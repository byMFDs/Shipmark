import io
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .forms import ProjectForm
from .images import clean_screenshot
from .models import MAX_SCREENSHOTS, Project, Screenshot, Tool
from .rendering import render_user_markdown

User = get_user_model()
TEMP_MEDIA = tempfile.mkdtemp(prefix="shipmark-test-media-")


def make_user(username, **extra):
    return User.objects.create_user(username=username, password="x", **extra)


def make_project(owner, name="Tallyhook", status=Project.Status.PUBLISHED, **extra):
    from .models import unique_slug
    project = Project.objects.create(
        owner=owner, name=name, slug=unique_slug(owner, name), tagline="A tagline", status=status,
        launched_at=timezone.now() if status == Project.Status.PUBLISHED else None, **extra,
    )
    return project


def image_file(fmt="PNG", size=(40, 30), name="shot.png", mode="RGB", **save_args):
    buffer = io.BytesIO()
    Image.new(mode, size, "red").save(buffer, format=fmt, **save_args)
    content_type = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp", "GIF": "image/gif"}[fmt]
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


def make_shot(project, order=0):
    """A real stored screenshot (the model reads the image size from the file)."""
    return Screenshot.objects.create(project=project, image=clean_screenshot(image_file()), order=order)


def urls_for(project):
    u, s = project.owner.username, project.slug
    return {
        "edit": reverse("projects:edit", args=[u, s]),
        "publish": reverse("projects:publish", args=[u, s]),
        "unpublish": reverse("projects:unpublish", args=[u, s]),
        "delete": reverse("projects:delete", args=[u, s]),
        "add": reverse("projects:screenshot_add", args=[u, s]),
    }


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProjectTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()  # rate limits live in the cache
        self.owner = make_user("owner")
        self.other = make_user("other")


class OwnershipTests(ProjectTestCase):
    """IDOR: every owner-only URL gives 404 to other users, and drafts are invisible to them."""

    def setUp(self):
        super().setUp()
        self.draft = make_project(self.owner, "Secret draft", Project.Status.DRAFT)
        self.shot = make_shot(self.draft)

    def owner_urls(self, project):
        u, s = project.owner.username, project.slug
        return {
            "GET": [urls_for(project)["edit"], urls_for(project)["delete"]],
            "POST": [
                urls_for(project)["edit"], urls_for(project)["publish"], urls_for(project)["unpublish"],
                urls_for(project)["delete"], urls_for(project)["add"],
                reverse("projects:screenshot_delete", args=[u, s, self.shot.pk]),
                reverse("projects:screenshot_move", args=[u, s, self.shot.pk]),
            ],
        }

    def test_other_user_gets_404_everywhere(self):
        self.client.force_login(self.other)
        urls = self.owner_urls(self.draft)
        for url in urls["GET"]:
            self.assertEqual(self.client.get(url).status_code, 404, url)
        for url in urls["POST"]:
            self.assertEqual(self.client.post(url, {"direction": "up"}).status_code, 404, url)
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)
        # Nothing changed.
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Project.Status.DRAFT)
        self.assertTrue(Project.objects.filter(pk=self.draft.pk).exists())
        self.assertTrue(Screenshot.objects.filter(pk=self.shot.pk).exists())

    def test_other_user_cannot_delete_published_project(self):
        project = make_project(self.owner, "Public")
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(urls_for(project)["delete"]).status_code, 404)
        self.assertEqual(self.client.post(urls_for(project)["unpublish"]).status_code, 404)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_anonymous_is_sent_to_login_and_sees_no_draft(self):
        for url in self.owner_urls(self.draft)["GET"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("/login/", response["Location"])
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)

    def test_screenshot_of_another_project_is_not_reachable_through_my_project(self):
        mine = make_project(self.other, "Mine")
        self.client.force_login(self.other)
        url = reverse("projects:screenshot_delete", args=[self.other.username, mine.slug, self.shot.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(Screenshot.objects.filter(pk=self.shot.pk).exists())

    def test_owner_sees_own_draft(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(urls_for(self.draft)["edit"]).status_code, 200)

    def test_hidden_project_is_404_for_others_but_owner_cannot_republish_it(self):
        hidden = make_project(self.owner, "Hidden", Project.Status.HIDDEN)
        self.assertEqual(self.client.get(hidden.get_absolute_url()).status_code, 404)
        self.client.force_login(self.owner)
        self.client.post(urls_for(hidden)["publish"])
        hidden.refresh_from_db()
        self.assertEqual(hidden.status, Project.Status.HIDDEN)

    def test_projects_of_suspended_user_are_hidden(self):
        project = make_project(self.owner)
        self.owner.is_suspended = True
        self.owner.save()
        self.assertEqual(self.client.get(project.get_absolute_url()).status_code, 404)

    def test_suspended_user_cannot_write(self):
        project = make_project(self.owner, "P", Project.Status.DRAFT)
        self.owner.is_suspended = True
        self.owner.save()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(reverse("projects:new"), {"name": "X", "tagline": "Y"}).status_code, 403)
        self.assertEqual(self.client.post(urls_for(project)["publish"]).status_code, 403)
        self.assertEqual(self.client.post(urls_for(project)["delete"]).status_code, 403)
        self.assertEqual(Project.objects.filter(owner=self.owner).count(), 2)  # draft from setUp + P; nothing new

    def test_csrf_is_enforced(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(urls_for(self.draft)["publish"]).status_code, 403)
        self.assertEqual(client.post(reverse("projects:preview"), {"text": "x"}).status_code, 403)


class PublicPageTests(ProjectTestCase):
    def test_published_page_is_public_and_labels_declared_tools(self):
        project = make_project(self.owner, description="Hello **world**")
        project.built_with.add(Tool.objects.get(name="Claude Code"))
        response = self.client.get(project.get_absolute_url())
        self.assertContains(response, "<strong>world</strong>", html=True)
        self.assertContains(response, "Built with (self-declared)")
        self.assertContains(response, "Claude Code")
        self.assertNotContains(response, "Edit project")  # no owner controls for visitors
        for kind in ("Repo owner", "Live", "Steady"):
            self.assertContains(response, kind)
        self.assertEqual(response.content.decode().count("Not yet"), 3)

    def test_owner_sees_controls(self):
        project = make_project(self.owner)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(project.get_absolute_url()), "Edit project")

    def test_uppercase_username_redirects(self):
        project = make_project(self.owner)
        url = reverse("projects:detail", args=["OWNER", project.slug])
        response = self.client.get(url)
        self.assertRedirects(response, project.get_absolute_url(), status_code=301)

    def test_javascript_url_stored_in_db_is_not_rendered_as_link(self):
        project = make_project(self.owner, live_url="javascript:alert(1)")
        self.assertNotContains(self.client.get(project.get_absolute_url()), "javascript:")


class MarkdownSanitizingTests(ProjectTestCase):
    def test_script_and_event_handlers_are_neutralized(self):
        html = render_user_markdown('hi <script>alert(1)</script> <img src=x onerror=alert(1)> <b onclick="x()">b</b>')
        self.assertNotIn("<script", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("<b ", html)

    def test_javascript_and_data_links_are_dropped(self):
        for source in (
            "[x](javascript:alert(1))", "[x](JaVaScRiPt:alert(1))", "[x](java&#115;cript:alert(1))",
            "[x]( javascript:alert(1))", "[x](data:text/html;base64,AAAA)", "[x](vbscript:msgbox)",
        ):
            html = render_user_markdown(source)
            self.assertNotIn("javascript", html.lower(), source)
            self.assertNotIn("data:", html, source)
            self.assertNotIn("vbscript", html, source)
            self.assertNotIn("href", html, source)

    def test_external_links_get_rel(self):
        html = render_user_markdown("[ok](https://example.com)")
        self.assertIn('href="https://example.com"', html)
        self.assertIn('rel="nofollow ugc noopener"', html)

    def test_images_are_not_allowed(self):
        self.assertNotIn("<img", render_user_markdown("![a](https://example.com/a.png)"))

    def test_headings_start_at_h3(self):
        html = render_user_markdown("# Big")
        self.assertIn("<h3>", html)
        self.assertNotIn("<h1", html)

    def test_page_and_preview_endpoint_are_sanitized(self):
        project = make_project(self.owner, description="<script>alert(1)</script>[x](javascript:alert(1))")
        response = self.client.get(project.get_absolute_url())
        self.assertNotContains(response, "<script>alert")
        self.assertNotContains(response, "javascript:alert")
        self.client.force_login(self.owner)
        data = self.client.post(reverse("projects:preview"), {"text": "<script>x</script>[a](javascript:1)"}).json()
        self.assertNotIn("<script", data["html"])
        self.assertNotIn("javascript", data["html"])

    def test_preview_needs_login_and_post(self):
        self.assertEqual(self.client.post(reverse("projects:preview"), {"text": "x"}).status_code, 302)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("projects:preview")).status_code, 405)
        self.assertEqual(self.client.post(reverse("projects:preview"), {"text": "x" * 5001}).status_code, 400)


class ScreenshotTests(ProjectTestCase):
    def setUp(self):
        super().setUp()
        self.project = make_project(self.owner, status=Project.Status.DRAFT)
        self.client.force_login(self.owner)
        self.add_url = urls_for(self.project)["add"]

    def upload(self, file):
        return self.client.post(self.add_url, {"image": file}, follow=True)

    def test_valid_image_is_reencoded_to_webp_with_random_name(self):
        self.upload(image_file("PNG", name="../../evil name.png"))
        shot = self.project.screenshots.get()
        self.assertRegex(shot.image.name, r"^screenshots/[0-9a-f]{32}\.webp$")
        with Image.open(shot.image.path) as stored:
            self.assertEqual(stored.format, "WEBP")
        self.assertEqual((shot.width, shot.height), (40, 30))

    def test_metadata_is_stripped(self):
        buffer = io.BytesIO()
        exif = Image.Exif()
        exif[0x010F] = "SecretCameraMaker"
        Image.new("RGB", (30, 30), "blue").save(buffer, format="JPEG", exif=exif)
        self.upload(SimpleUploadedFile("a.jpg", buffer.getvalue(), content_type="image/jpeg"))
        shot = self.project.screenshots.get()
        self.assertNotIn(b"SecretCameraMaker", Path(shot.image.path).read_bytes())
        with Image.open(shot.image.path) as stored:
            self.assertEqual(len(stored.getexif()), 0)

    def test_big_images_are_scaled_down(self):
        self.upload(image_file("PNG", size=(3000, 1000)))
        shot = self.project.screenshots.get()
        self.assertEqual(max(shot.width, shot.height), 1600)

    def test_wrong_types_are_rejected(self):
        bad = [
            image_file("GIF", name="a.gif"),
            SimpleUploadedFile("a.png", b"<svg xmlns='http://www.w3.org/2000/svg'><script>1</script></svg>", content_type="image/png"),
            SimpleUploadedFile("a.png", b"not an image at all", content_type="image/png"),
            SimpleUploadedFile("a.php", b"<?php echo 1;", content_type="image/png"),
            SimpleUploadedFile("a.png", b"", content_type="image/png"),
        ]
        for file in bad:
            self.upload(file)
        self.assertEqual(self.project.screenshots.count(), 0)

    def test_file_over_5_mb_is_rejected(self):
        header = image_file("PNG").read()
        too_big = SimpleUploadedFile("big.png", header + b"\0" * (5 * 1024 * 1024), content_type="image/png")
        response = self.upload(too_big)
        self.assertEqual(self.project.screenshots.count(), 0)
        self.assertContains(response, "larger than 5 MB")

    def test_too_many_pixels_are_rejected(self):
        response = self.upload(image_file("PNG", size=(6000, 5000)))  # 30 MP, tiny file
        self.assertEqual(self.project.screenshots.count(), 0)
        self.assertContains(response, "too many pixels")

    def test_missing_file(self):
        response = self.client.post(self.add_url, {}, follow=True)
        self.assertContains(response, "Choose an image first.")

    def test_fifth_screenshot_is_rejected(self):
        for _i in range(MAX_SCREENSHOTS):
            self.upload(image_file("PNG"))
        self.assertEqual(self.project.screenshots.count(), 4)
        response = self.upload(image_file("PNG"))
        self.assertEqual(self.project.screenshots.count(), 4)
        self.assertContains(response, "at most 4 screenshots")

    def test_reorder_and_delete_keep_order_continuous(self):
        for _i in range(3):
            self.upload(image_file("PNG"))
        first, second, third = list(self.project.screenshots.all())
        u, s = self.owner.username, self.project.slug
        self.client.post(reverse("projects:screenshot_move", args=[u, s, third.pk]), {"direction": "up"})
        self.assertEqual([x.pk for x in self.project.screenshots.all()], [first.pk, third.pk, second.pk])
        self.client.post(reverse("projects:screenshot_move", args=[u, s, first.pk]), {"direction": "up"})  # already first
        self.assertEqual(self.project.screenshots.first().pk, first.pk)
        self.client.post(reverse("projects:screenshot_move", args=[u, s, first.pk]), {"direction": "sideways"})
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("projects:screenshot_delete", args=[u, s, first.pk]))
        self.assertEqual([x.order for x in self.project.screenshots.all()], [0, 1])

    def test_files_are_removed_with_screenshot_and_with_project(self):
        self.upload(image_file("PNG"))
        path = Path(self.project.screenshots.get().image.path)
        self.assertTrue(path.exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(urls_for(self.project)["delete"])
        self.assertFalse(path.exists())
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())


class FormAndLifecycleTests(ProjectTestCase):
    def valid(self, **extra):
        data = {"name": "Tallyhook", "tagline": "Replay webhooks", "description": "", "live_url": "", "repo_full_name": "", "tags_text": ""}
        data.update(extra)
        return data

    def test_create_makes_a_draft_even_if_status_is_posted(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("projects:new"), self.valid(status="published", slug="hacked", owner=self.other.pk))
        project = Project.objects.get()
        self.assertEqual((project.status, project.slug, project.owner), ("draft", "tallyhook", self.owner))
        self.assertRedirects(response, urls_for(project)["edit"])

    def test_same_name_gets_a_new_slug_and_edit_keeps_slug(self):
        self.client.force_login(self.owner)
        for _i in range(2):
            self.client.post(reverse("projects:new"), self.valid())
        slugs = sorted(Project.objects.values_list("slug", flat=True))
        self.assertEqual(slugs, ["tallyhook", "tallyhook-2"])
        project = Project.objects.get(slug="tallyhook")
        self.client.post(urls_for(project)["edit"], self.valid(name="Renamed", slug="x"))
        project.refresh_from_db()
        self.assertEqual((project.name, project.slug), ("Renamed", "tallyhook"))

    def test_two_owners_can_use_the_same_slug(self):
        a = make_project(self.owner, "Same")
        b = make_project(self.other, "Same")
        self.assertEqual(a.slug, b.slug)

    def test_name_without_latin_letters_still_gets_a_slug(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("projects:new"), self.valid(name="Розклад"))
        self.assertEqual(Project.objects.get().slug, "project")

    def test_publish_and_unpublish(self):
        project = make_project(self.owner, status=Project.Status.DRAFT)
        self.client.force_login(self.owner)
        self.client.post(urls_for(project)["publish"])
        project.refresh_from_db()
        self.assertEqual(project.status, "published")
        self.assertIsNotNone(project.launched_at)
        first_launch = project.launched_at
        self.client.post(urls_for(project)["unpublish"])
        self.client.post(urls_for(project)["publish"])
        project.refresh_from_db()
        self.assertEqual(project.launched_at, first_launch)
        self.client.logout()
        self.assertEqual(self.client.get(project.get_absolute_url()).status_code, 200)

    def test_publish_and_delete_do_not_work_with_get(self):
        project = make_project(self.owner, status=Project.Status.DRAFT)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(urls_for(project)["publish"]).status_code, 405)
        self.assertContains(self.client.get(urls_for(project)["delete"]), "cannot be undone")
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_delete_with_post(self):
        project = make_project(self.owner)
        self.client.force_login(self.owner)
        response = self.client.post(urls_for(project)["delete"])
        self.assertRedirects(response, reverse("accounts:profile", args=["owner"]))
        self.assertFalse(Project.objects.exists())

    def form(self, **extra):
        return ProjectForm(self.valid(**extra))

    def valid_data(self, **extra):
        return self.valid(**extra)

    def test_repo_name_is_normalized_and_validated(self):
        for raw, expected in [
            ("octocat/hello", "octocat/hello"),
            ("https://github.com/octocat/hello-world/", "octocat/hello-world"),
            ("github.com/octocat/hello.git", "octocat/hello"),
        ]:
            form = self.form(repo_full_name=raw)
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data["repo_full_name"], expected)
        for bad in ["octocat", "a/b/c", "https://evil.com/a/b", "a b/c", "../x/y"]:
            self.assertIn("repo_full_name", self.form(repo_full_name=bad).errors, bad)

    def test_live_url_must_be_public_http(self):
        for bad in ["javascript:alert(1)", "ftp://example.com", "http://localhost", "https://user:pw@example.com", "data:text/html,x"]:
            self.assertIn("live_url", self.form(live_url=bad).errors, bad)
        form = self.form(live_url="example.com")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["live_url"], "https://example.com")

    def test_tags_are_limited_and_deduplicated(self):
        self.assertIn("tags_text", self.form(tags_text="a1,b1,c1,d1,e1,f1").errors)
        self.assertIn("tags_text", self.form(tags_text="<script>").errors)
        self.assertIn("tags_text", self.form(tags_text="x" * 31).errors)
        self.client.force_login(self.owner)
        self.client.post(reverse("projects:new"), self.valid(tags_text="DevTools, devtools,  Open  Source"))
        self.assertEqual(sorted(Project.objects.get().tags.values_list("name", flat=True)), ["devtools", "open source"])

    def test_only_listed_tools_can_be_chosen(self):
        self.assertIn("built_with", self.form(built_with=[99999]).errors)
        tool = Tool.objects.get(name="Cursor")
        form = self.form(built_with=[tool.pk])
        self.assertTrue(form.is_valid(), form.errors)

    def test_seeded_tools(self):
        self.assertTrue(Tool.objects.filter(name="Claude Code").exists())
        self.assertGreaterEqual(Tool.objects.count(), 10)

    def test_description_length_limit(self):
        self.assertIn("description", self.form(description="x" * 5001).errors)

    def test_new_requires_login(self):
        response = self.client.get(reverse("projects:new"))
        self.assertEqual(response.status_code, 302)

    def test_creating_is_rate_limited(self):
        self.client.force_login(self.owner)
        for _i in range(11):
            self.client.post(reverse("projects:new"), self.valid())
        self.assertEqual(Project.objects.count(), 10)


class ProfileListTests(ProjectTestCase):
    def test_profile_lists_only_published_and_drafts_only_for_owner(self):
        make_project(self.owner, "Public one")
        make_project(self.owner, "Private draft", Project.Status.DRAFT)
        make_project(self.owner, "Moderated", Project.Status.HIDDEN)
        url = reverse("accounts:profile", args=["owner"])
        anon = self.client.get(url)
        self.assertContains(anon, "Public one")
        self.assertNotContains(anon, "Private draft")
        self.assertNotContains(anon, "Moderated")
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(url), "Private draft")
        self.client.force_login(self.owner)
        mine = self.client.get(url)
        self.assertContains(mine, "Private draft")
        self.assertContains(mine, "Your drafts")
        self.assertEqual(mine.context["stats"]["projects"], 1)

    def test_profile_does_not_run_a_query_per_project(self):
        url = reverse("accounts:profile", args=["owner"])
        make_project(self.owner, "One")
        # user, projects (+repo link), screenshots, domain verifications, follower count: the same for 1 or 4 projects
        with self.assertNumQueries(5):
            self.client.get(url)
        for name in ("Two", "Three", "Four"):
            project = make_project(self.owner, name)
            make_shot(project)
        with self.assertNumQueries(5):
            self.client.get(url)
