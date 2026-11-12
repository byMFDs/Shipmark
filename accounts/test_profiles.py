"""Profiles: pictures, fields, links, skills, pinned projects, tabs, and the abuse cases around them."""
import io
from datetime import timedelta
from pathlib import Path
from unittest import mock

import httpx
from allauth.socialaccount.models import SocialAccount
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from PIL import Image

from moderation import decisions, sanctions
from moderation.models import AuditLog
from projects.models import BuildLogEntry, Project, Tool
from projects.tests import TEMP_MEDIA, image_file, make_project, make_user
from verification.net import FetchError, FetchResult

from .avatars import GITHUB_AVATAR_HOSTS
from .deletion import delete_account
from .export import build_export
from .links import clean_link
from .models import PinnedProject, ProfileLink, User

GITHUB_PICTURE = "https://avatars.githubusercontent.com/u/4242?v=4"


def png_bytes(size=(600, 300), color="blue"):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def fetch_result(content=None, status=200):
    return FetchResult(url=GITHUB_PICTURE, status_code=status, headers=httpx.Headers({"content-type": "image/png"}),
                       content=png_bytes() if content is None else content)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProfileTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = make_user("ana", display_name="Ana", github_login="ana-gh", avatar_url=GITHUB_PICTURE)
        SocialAccount.objects.create(user=self.ana, provider="github", uid="4242",
                                     extra_data={"login": "ana-gh", "avatar_url": GITHUB_PICTURE})
        self.url = reverse("accounts:settings")
        self.client.force_login(self.ana)

    def fresh(self, user=None):
        return User.objects.get(pk=(user or self.ana).pk)

    def post(self, files=None, **data):
        base = {"display_name": "Ana", "headline": "", "location": "", "status": "", "about": "",
                "skills_text": "", "preferred_language": ""}
        base.update(data)
        base.update(files or {})
        return self.client.post(self.url, base)

    def profile(self, user="ana", **params):
        return self.client.get(reverse("accounts:profile", args=[user]), params)


# ---------- Pictures ----------

class AvatarTests(ProfileTestCase):
    def test_upload_is_cropped_reencoded_and_shown_everywhere(self):
        buffer = io.BytesIO()
        exif = Image.Exif()
        exif[0x010F] = "SecretCameraMaker"
        Image.new("RGB", (900, 400), "red").save(buffer, format="JPEG", exif=exif)
        upload = SimpleUploadedFile("../../me.jpg", buffer.getvalue(), content_type="image/jpeg")
        response = self.post({"avatar_file": upload})
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        ana = self.fresh()
        self.assertRegex(ana.avatar.name, r"^avatars/[0-9a-f]{32}\.webp$")
        self.assertEqual(ana.avatar_source, "upload")
        with Image.open(ana.avatar.path) as stored:
            self.assertEqual((stored.format, stored.size), ("WEBP", (512, 512)))  # centre-cropped square
            self.assertEqual(len(stored.getexif()), 0)
        self.assertNotIn(b"SecretCameraMaker", Path(ana.avatar.path).read_bytes())
        self.client.logout()
        self.assertContains(self.profile(), f'src="{ana.avatar.url}"')
        make_project(ana, name="Quillbox")
        self.assertContains(self.client.get(Project.objects.get().get_absolute_url()), ana.avatar.url)

    def test_bad_files_are_refused_and_nothing_changes(self):
        header = image_file("PNG").read()
        bad = [
            image_file("GIF", name="a.gif"),
            SimpleUploadedFile("a.png", b"<svg xmlns='http://www.w3.org/2000/svg'><script>1</script></svg>", content_type="image/png"),
            SimpleUploadedFile("a.png", b"not an image", content_type="image/png"),
            SimpleUploadedFile("a.png", header + b"\0" * (5 * 1024 * 1024), content_type="image/png"),
            image_file("PNG", size=(6000, 5000)),
        ]
        for file in bad:
            response = self.post({"avatar_file": file}, display_name="Changed")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'role="alert"')
        ana = self.fresh()
        self.assertFalse(ana.avatar)
        self.assertEqual(ana.display_name, "Ana")  # the whole form is refused, nothing half-saved

    def test_replace_and_remove_delete_the_old_files(self):
        self.post({"avatar_file": image_file()})
        first = Path(self.fresh().avatar.path)
        self.assertTrue(first.exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.post({"avatar_file": image_file(size=(100, 100))})
        second = Path(self.fresh().avatar.path)
        self.assertNotEqual(first, second)
        self.assertFalse(first.exists())
        self.assertTrue(second.exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.post(remove_avatar="on")
        ana = self.fresh()
        self.assertEqual((ana.avatar.name, ana.avatar_source), ("", ""))
        self.assertFalse(second.exists())
        self.client.logout()
        self.assertContains(self.profile(), "avatar--initials")

    def test_upload_wins_over_github_and_remove(self):
        with mock.patch("accounts.avatars.safe_fetch") as fetch:
            self.post({"avatar_file": image_file()}, use_github_avatar="on", remove_avatar="on")
        fetch.assert_not_called()
        self.assertEqual(self.fresh().avatar_source, "upload")

    def test_cover_is_cropped_to_a_banner(self):
        self.post({"cover_file": image_file(size=(1000, 1000))})
        ana = self.fresh()
        self.assertRegex(ana.cover.name, r"^covers/[0-9a-f]{32}\.webp$")
        with Image.open(ana.cover.path) as stored:
            self.assertEqual(stored.size, (1500, 500))
        self.assertContains(self.profile(), ana.cover.url)
        path = Path(ana.cover.path)
        with self.captureOnCommitCallbacks(execute=True):
            self.post(remove_cover="on")
        self.assertFalse(self.fresh().cover)
        self.assertFalse(path.exists())

    def test_picture_is_the_social_preview_image(self):
        self.post({"avatar_file": image_file()})
        self.client.logout()
        self.assertRegex(self.profile().content.decode(), r'og:image" content="https?://[^"]+/avatars/[0-9a-f]{32}\.webp"')

    def test_upload_rate_limit(self):
        from config.ratelimit import is_limited
        for _i in range(20):
            is_limited("profile_image", self.ana.pk, limit=20, window=3600)
        response = self.post({"avatar_file": image_file()})
        self.assertContains(response, "Too many changes")
        self.assertFalse(self.fresh().avatar)


class GitHubAvatarTests(ProfileTestCase):
    def test_downloaded_once_through_safe_fetch_and_stored_locally(self):
        with mock.patch("accounts.avatars.safe_fetch", return_value=fetch_result()) as fetch:
            response = self.post(use_github_avatar="on")
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        fetch.assert_called_once()
        called = fetch.call_args.args[0]
        self.assertTrue(called.startswith("https://avatars.githubusercontent.com/u/4242"))
        self.assertIn("s=512", called)
        ana = self.fresh()
        self.assertEqual(ana.avatar_source, "github")
        with Image.open(ana.avatar.path) as stored:
            self.assertEqual((stored.format, stored.size), ("WEBP", (512, 512)))
        self.client.logout()
        html = self.profile().content.decode()
        self.assertIn(ana.avatar.url, html)
        self.assertNotIn("githubusercontent.com", html)  # never hotlinked

    def test_only_github_picture_hosts_are_fetched(self):
        self.assertEqual(GITHUB_AVATAR_HOSTS, ("avatars.githubusercontent.com",))
        for url in ("https://evil.example/a.png", "http://avatars.githubusercontent.com/u/1",
                    "https://avatars.githubusercontent.com.evil.example/u/1", "https://127.0.0.1/a.png", ""):
            SocialAccount.objects.filter(user=self.ana).update(extra_data={"avatar_url": url})
            User.objects.filter(pk=self.ana.pk).update(avatar_url=url)
            page = self.client.get(self.url)
            self.assertNotContains(page, "use_github_avatar", msg_prefix=url)  # no checkbox
            with mock.patch("accounts.avatars.safe_fetch") as fetch:
                self.post(use_github_avatar="on")  # a forged field is ignored
            fetch.assert_not_called()
            self.assertFalse(self.fresh().avatar, url)

    def test_fetch_failures_show_a_message_and_change_nothing(self):
        for outcome in (FetchError("timeout"), fetch_result(status=404), fetch_result(content=b"<html>nope</html>")):
            kwargs = {"side_effect": outcome} if isinstance(outcome, Exception) else {"return_value": outcome}
            with mock.patch("accounts.avatars.safe_fetch", **kwargs):
                response = self.post(use_github_avatar="on", display_name="Changed")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'role="alert"')
            self.assertFalse(self.fresh().avatar)
            self.assertEqual(self.fresh().display_name, "Ana")
            cache.clear()

    def test_rate_limit(self):
        with mock.patch("accounts.avatars.safe_fetch", return_value=fetch_result()) as fetch:
            for _i in range(5):
                self.post(use_github_avatar="on")
            response = self.post(use_github_avatar="on")
        self.assertEqual(fetch.call_count, 5)
        self.assertContains(response, "Too many changes")

    def test_only_safe_fetch_is_used(self):
        import accounts.avatars as module
        source = Path(module.__file__).read_text()
        self.assertNotIn("httpx", source)
        self.assertNotIn("requests", source)
        self.assertIn("safe_fetch", source)


class MuteTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        boss = User.objects.create_superuser("boss", "b@example.com", "pw")
        sanctions.issue(self.ana, "mute", "Spam avatar uploads, against the rules.", boss, length=timedelta(days=1))

    def test_muted_user_cannot_upload_pictures_but_can_edit_text(self):
        with mock.patch("accounts.avatars.safe_fetch") as fetch:
            for data in ({"files": {"avatar_file": image_file()}}, {"files": {"cover_file": image_file()}},
                         {"use_github_avatar": "on"}):
                files = data.pop("files", None)
                response = self.post(files, display_name="Changed", **data)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "muted")
        fetch.assert_not_called()
        ana = self.fresh()
        self.assertEqual((ana.display_name, bool(ana.avatar), bool(ana.cover)), ("Ana", False, False))
        response = self.post(headline="Still me")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.fresh().headline, "Still me")

    def test_the_page_says_pictures_are_locked(self):
        self.assertContains(self.client.get(self.url), "pictures cannot be changed")


# ---------- Fields ----------

class FieldTests(ProfileTestCase):
    def test_limits_and_choices(self):
        for data in ({"headline": "x" * 81}, {"about": "x" * 1001}, {"location": "x" * 61}, {"status": "king"},
                     {"display_name": "Shipmark Team"}):
            response = self.post(**data)
            self.assertEqual(response.status_code, 200, data)
        self.assertEqual((self.fresh().headline, self.fresh().status), ("", ""))
        self.post(headline="x" * 80, about="y" * 1000, location="Lviv", status="building_in_public")
        ana = self.fresh()
        self.assertEqual((len(ana.headline), len(ana.about), ana.location, ana.status),
                         (80, 1000, "Lviv", "building_in_public"))

    def test_everything_is_optional(self):
        self.post(headline="Hi", about="About", location="Kyiv", status="hiring")
        self.post()  # all empty
        ana = self.fresh()
        self.assertEqual((ana.headline, ana.about, ana.location, ana.status), ("", "", "", ""))

    def test_status_and_location_show_on_the_profile(self):
        self.post(headline="Builds tools", location="Kyiv", status="open_to_work")
        self.client.logout()
        html = self.profile().content.decode()
        self.assertIn("Builds tools", html)
        self.assertIn("Kyiv", html)
        self.assertIn("Open to work", html)

    def test_user_text_is_escaped(self):
        self.post(headline="<script>alert(1)</script>", location="<b>x</b>", display_name="<i>Ana</i>")
        self.client.logout()
        html = self.profile().content.decode()
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("<b>x</b>", html)


class LinkTests(ProfileTestCase):
    def test_kind_rules(self):
        good = [("github", "https://github.com/ana"), ("github", "https://www.github.com/ana"),
                ("x", "https://x.com/ana"), ("x", "https://twitter.com/ana"),
                ("linkedin", "https://uk.linkedin.com/in/ana"), ("telegram", "https://t.me/ana"),
                ("website", "https://ana.example/path?x=1"), ("other", "http://example.org")]
        for kind, url in good:
            self.assertEqual(clean_link(kind, url), url)
        bad = [("github", "https://evil.example/ana"), ("github", "https://github.com.evil.example/ana"),
               ("github", "https://notgithub.com/ana"), ("x", "https://x.com.evil.example/"),
               ("linkedin", "https://example.com/linkedin.com"), ("website", "javascript:alert(1)"),
               ("website", "ftp://example.com"), ("website", "https://user:pw@example.com"),
               ("website", "https://localhost"), ("website", "data:text/html,hi"), ("website", "https://a b.example")]
        for kind, url in bad:
            with self.assertRaises(Exception, msg=(kind, url)):
                clean_link(kind, url)

    def test_save_replace_order_and_dedupe(self):
        self.post(link0_kind="website", link0_url="https://ana.example", link1_kind="github",
                  link1_url="https://github.com/ana", link2_kind="other", link2_url="https://ANA.example",  # same as 0
                  link3_kind="other", link3_url="https://blog.example")
        links = list(self.ana.links.all())
        self.assertEqual([(l.kind, l.url) for l in links],
                         [("website", "https://ana.example"), ("github", "https://github.com/ana"),
                          ("other", "https://blog.example")])
        self.assertEqual([l.order for l in links], [0, 1, 2])
        self.post(link0_kind="github", link0_url="https://github.com/ana")
        self.assertEqual([l.url for l in self.ana.links.all()], ["https://github.com/ana"])
        self.post()
        self.assertFalse(self.ana.links.exists())

    def test_wrong_site_for_the_kind_is_an_error_on_that_row(self):
        response = self.post(link0_kind="github", link0_url="https://evil.example/ana")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not look like a GitHub address")
        self.assertContains(response, 'aria-invalid="true"')
        self.assertFalse(self.ana.links.exists())

    def test_links_are_nofollow_and_icons_are_inline(self):
        self.post(link0_kind="x", link0_url="https://x.com/ana", link1_kind="website", link1_url="https://ana.example")
        self.client.logout()
        html = self.profile().content.decode()
        self.assertEqual(html.count('rel="nofollow ugc noopener"'), 2)
        self.assertIn("ana.example", html)
        self.assertNotIn("<img src=\"https://", html)

    def test_settings_shows_only_my_links(self):
        bob = make_user("bob")
        ProfileLink.objects.create(user=bob, kind="website", url="https://bob-private.example")
        ProfileLink.objects.create(user=self.ana, kind="website", url="https://ana.example")
        page = self.client.get(self.url)
        self.assertContains(page, "https://ana.example")
        self.assertNotContains(page, "bob-private")


class SkillTests(ProfileTestCase):
    def test_skills_are_tags_with_a_limit(self):
        self.post(skills_text="Python, django , python, Design")
        self.assertEqual(sorted(t.slug for t in self.ana.skills.all()), ["design", "django", "python"])
        too_many = ", ".join(f"skill{n}" for n in range(11))
        self.assertContains(self.post(skills_text=too_many), "Use at most 10 skills.")
        self.assertContains(self.post(skills_text="bad<tag>"), "Tags use letters")
        self.assertEqual(self.ana.skills.count(), 3)
        self.post(skills_text="")
        self.assertEqual(self.ana.skills.count(), 0)

    def test_skills_show_on_the_about_tab(self):
        self.post(skills_text="python, design")
        self.client.logout()
        self.assertContains(self.profile(tab="about"), "python")
        self.assertNotContains(self.profile(), 'class="chip">python')


class PinnedTests(ProfileTestCase):
    def setUp(self):
        super().setUp()
        self.p = [make_project(self.ana, name=f"Thing {n}") for n in range(4)]
        self.draft = make_project(self.ana, name="Draft", status=Project.Status.DRAFT)
        self.bob = make_user("bob")
        self.others = make_project(self.bob, name="Bobs")

    def test_pin_up_to_three_own_published_projects(self):
        self.post(pinned=[self.p[1].pk, self.p[0].pk])
        self.assertEqual({pin.project_id for pin in self.ana.pins.all()}, {self.p[0].pk, self.p[1].pk})
        self.client.logout()
        html = self.profile().content.decode()
        self.assertIn('id="pinned-title"', html)
        self.assertContains(self.profile(), "Pinned")

    def test_cannot_pin_others_drafts_or_more_than_three(self):
        for pks in ([self.others.pk], [self.draft.pk], [p.pk for p in self.p]):
            response = self.post(pinned=pks)
            self.assertEqual(response.status_code, 200, pks)
            self.assertFalse(self.ana.pins.exists(), pks)
        self.assertFalse(PinnedProject.objects.filter(project=self.others).exists())

    def test_an_unpublished_or_removed_project_leaves_the_pinned_list(self):
        self.post(pinned=[self.p[0].pk, self.p[1].pk])
        self.client.logout()
        self.assertContains(self.profile(), 'id="pinned-title"')
        decisions.remove_project(self.p[0], User.objects.create_superuser("boss", "b@example.com", "pw"), "Rule broken, see terms.")
        Project.objects.filter(pk=self.p[1].pk).update(status=Project.Status.DRAFT)
        self.assertNotContains(self.profile(), 'id="pinned-title"')

    def test_pinned_choices_are_only_my_published_projects(self):
        page = self.client.get(self.url)
        self.assertContains(page, "Thing 0")
        self.assertNotContains(page, "Draft</span>")
        self.assertNotContains(page, "Bobs")


# ---------- Page ----------

class ProfilePageTests(ProfileTestCase):
    def test_tabs_and_unknown_tab(self):
        self.client.logout()
        for tab in ("projects", "log", "about", "nonsense", ""):
            self.assertEqual(self.profile(tab=tab).status_code, 200, tab)
        self.assertContains(self.profile(tab="log"), 'aria-current="page">Build log')
        self.assertContains(self.profile(tab="nonsense"), 'aria-current="page">Projects')

    def test_build_log_tab_lists_only_public_updates_of_this_person(self):
        public = make_project(self.ana, name="Public")
        draft = make_project(self.ana, name="Hidden draft", status=Project.Status.DRAFT)
        bob = make_user("bob")
        BuildLogEntry.objects.create(project=public, text="Shipped **v1**")
        BuildLogEntry.objects.create(project=draft, text="Secret draft note")
        BuildLogEntry.objects.create(project=make_project(bob, name="Bobs"), text="Bob note")
        self.client.logout()
        page = self.profile(tab="log")
        self.assertContains(page, "<strong>v1</strong>")
        self.assertNotContains(page, "Secret draft note")
        self.assertNotContains(page, "Bob note")

    def test_log_and_about_tabs_have_inviting_empty_states(self):
        self.assertContains(self.profile(tab="log"), "Write short updates on a project page")
        self.assertContains(self.profile(tab="about"), "Tell people what you build")
        self.client.logout()
        self.assertContains(self.profile(tab="about"), "has not written anything here yet")
        self.assertNotContains(self.profile(tab="about"), "Tell people what you build")

    def test_about_is_markdown_and_sanitized(self):
        self.post(about="Hello **world**\n\n<script>alert(1)</script>\n\n[bad](javascript:alert(1)) [ok](https://example.com)")
        self.client.logout()
        html = self.profile(tab="about").content.decode()
        self.assertIn("<strong>world</strong>", html)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("javascript:", html)
        self.assertIn('rel="nofollow ugc noopener"', html)
        self.assertNotIn("**world**", html)

    def test_built_with_summary_is_labelled_self_declared(self):
        tool = Tool.objects.get(slug="claude-code")
        for n in range(2):
            make_project(self.ana, name=f"P{n}").built_with.add(tool)
        make_project(self.ana, name="Draft", status=Project.Status.DRAFT).built_with.add(Tool.objects.get(slug="cursor"))
        self.client.logout()
        page = self.profile(tab="about")
        self.assertContains(page, "Built with (self-declared)")
        self.assertContains(page, "Claude Code")
        self.assertContains(page, "×2")
        self.assertNotContains(page, "Cursor")

    def test_edit_button_only_for_the_owner(self):
        self.assertContains(self.profile(), reverse("accounts:settings"))
        self.client.logout()
        self.assertNotContains(self.profile(), "Edit profile")

    def test_queries_do_not_grow_with_links_or_log_entries(self):
        public = make_project(self.ana, name="Public")
        self.client.logout()

        def count(**params):
            with CaptureQueriesContext(connection) as ctx:
                self.assertEqual(self.profile(**params).status_code, 200)
            return len(ctx)

        few = {tab: count(tab=tab) for tab in ("projects", "log", "about")}
        for n in range(6):
            ProfileLink.objects.create(user=self.ana, kind="other", url=f"https://example.com/{n}")
            BuildLogEntry.objects.create(project=public, text=f"update {n}")
        self.assertEqual({tab: count(tab=tab) for tab in ("projects", "log", "about")}, few)


class SettingsPageTests(ProfileTestCase):
    def test_has_live_preview_and_one_form_for_everything(self):
        page = self.client.get(self.url)
        html = page.content.decode()
        self.assertContains(page, "data-profile-preview")
        self.assertContains(page, "profile-preview.js")
        self.assertEqual(html.count('enctype="multipart/form-data"'), 1)
        for name in ("avatar_file", "cover_file", "headline", "location", "status", "about", "skills_text",
                     "link0_url", "link5_url", "preferred_language"):
            self.assertIn(f'name="{name}"', html)
        self.assertIn('name="use_github_avatar"', html)

    def test_preview_shows_saved_values_without_js(self):
        self.post(headline="Builds tools", location="Kyiv", status="hiring")
        page = self.client.get(self.url)
        self.assertContains(page, 'data-pv="headline">Builds tools')
        self.assertContains(page, "Hiring")

    def test_forged_fields_cannot_reach_other_people(self):
        bob = make_user("bob", display_name="Bob")
        self.post(user=bob.pk, id=bob.pk, username="bob", skills_text="x")
        bob.refresh_from_db()
        self.assertEqual(bob.display_name, "Bob")
        self.assertFalse(bob.skills.exists())


# ---------- Data rights ----------

class DataRightsTests(ProfileTestCase):
    def test_export_has_the_new_fields_and_only_mine(self):
        bob = make_user("bob", headline="bob secret headline")
        ProfileLink.objects.create(user=bob, kind="website", url="https://bob-private.example")
        make_project(self.ana, name="Pinned one")
        self.post({"avatar_file": image_file()}, headline="Builds tools", about="About me", location="Kyiv",
                  status="hiring", skills_text="python", link0_kind="website", link0_url="https://ana.example",
                  pinned=[Project.objects.get(owner=self.ana).pk])
        data = build_export(self.fresh(), absolute=lambda url: f"https://shipmark.me{url}")
        profile = data["profile"]
        self.assertEqual((profile["headline"], profile["about"], profile["location"], profile["status"]),
                         ("Builds tools", "About me", "Kyiv", "hiring"))
        self.assertEqual(profile["skills"], ["python"])
        self.assertEqual(profile["links"], [{"kind": "website", "url": "https://ana.example"}])
        self.assertEqual(profile["pinned_projects"], ["pinned-one"])
        self.assertTrue(profile["avatar"].startswith("https://shipmark.me/media/avatars/"))
        text = str(data)
        self.assertNotIn("bob secret headline", text)
        self.assertNotIn("bob-private", text)

    def test_deleting_the_account_removes_the_picture_files(self):
        self.post({"avatar_file": image_file(), "cover_file": image_file()})
        ana = self.fresh()
        avatar, cover = Path(ana.avatar.path), Path(ana.cover.path)
        self.assertTrue(avatar.exists() and cover.exists())
        with self.captureOnCommitCallbacks(execute=True):
            delete_account(ana)
        self.assertFalse(avatar.exists() or cover.exists())
        self.assertFalse(ProfileLink.objects.filter(user_id=ana.pk).exists())

    def test_moderators_clearing_the_picture_removes_files_and_the_github_address(self):
        self.post({"avatar_file": image_file(), "cover_file": image_file()}, headline="Spam", about="Spam",
                  link0_kind="website", link0_url="https://spam.example")
        ana = self.fresh()
        avatar, cover = Path(ana.avatar.path), Path(ana.cover.path)
        boss = User.objects.create_superuser("boss", "b@example.com", "pw")
        with self.captureOnCommitCallbacks(execute=True):
            changed = decisions.clear_profile(ana, ["avatar", "bio", "links"], boss, "Spam in every field, see the terms.")
        self.assertEqual(sorted(changed), ["avatar", "bio", "links"])
        ana = self.fresh()
        self.assertEqual((ana.avatar.name, ana.cover.name, ana.avatar_url, ana.headline, ana.about), ("", "", "", "", ""))
        self.assertFalse(ana.links.exists())
        self.assertFalse(avatar.exists() or cover.exists())
        self.assertTrue(AuditLog.objects.filter(action="moderation.profile.cleared").exists())
