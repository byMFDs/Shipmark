"""Screenshots upload with the project form, and the cover shows wherever the project is listed.

The bug this covers: the editor had a separate "Upload screenshot" form, so choosing a file and pressing
"Save" or "Publish" (other forms) never sent the file. No Screenshot row was created and every list showed
the placeholder letter.
"""
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from config.ratelimit import is_limited

from .models import MAX_SCREENSHOTS, Project
from .tests import TEMP_MEDIA, ProjectTestCase, image_file, make_project, make_shot, make_user, urls_for


def form_data(project=None, **extra):
    data = {
        "name": project.name if project else "Tallyhook",
        "tagline": project.tagline if project else "Replay webhooks",
        "description": "", "live_url": "", "repo_full_name": "", "tags_text": "",
    }
    data.update(extra)
    return data


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class OneFlowTests(ProjectTestCase):
    def setUp(self):
        super().setUp()
        self.project = make_project(self.owner, status=Project.Status.DRAFT)
        self.client.force_login(self.owner)
        self.edit_url = urls_for(self.project)["edit"]

    def test_file_input_and_publish_button_belong_to_the_main_form(self):
        html = self.client.get(self.edit_url).content.decode()
        self.assertIn('enctype="multipart/form-data" class="panel stack" id="project-form"', html)
        self.assertRegex(html, r'<input type="file" name="screenshots"[^>]*multiple')
        self.assertIn('form="project-form" name="publish"', html)
        self.assertNotIn(reverse("projects:screenshot_add", args=[self.owner.username, self.project.slug]), html)

    def test_save_uploads_several_files_and_shows_thumbnails(self):
        response = self.client.post(self.edit_url, form_data(self.project, screenshots=[image_file(), image_file()]))
        self.assertRedirects(response, self.edit_url + "#screenshots", fetch_redirect_response=False)
        shots = list(self.project.screenshots.all())
        self.assertEqual([s.order for s in shots], [0, 1])
        page = self.client.get(self.edit_url)
        for shot in shots:
            self.assertContains(page, shot.image.url)
        self.assertContains(page, f'form="shot-delete-{shots[0].pk}"')
        self.assertContains(page, f'id="shot-move-{shots[1].pk}"')

    def test_publish_from_the_form_saves_files_then_publishes(self):
        response = self.client.post(self.edit_url, form_data(self.project, screenshots=[image_file()], publish="1"))
        self.assertRedirects(response, self.project.get_absolute_url(), fetch_redirect_response=False)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.PUBLISHED)
        self.assertEqual(self.project.screenshots.count(), 1)

    def test_publish_endpoint_keeps_screenshots(self):
        make_shot(self.project)
        self.client.post(urls_for(self.project)["publish"])
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.PUBLISHED)
        self.assertEqual(self.project.screenshots.count(), 1)

    def test_new_project_with_screenshots(self):
        response = self.client.post(reverse("projects:new"), form_data(name="Lantern", screenshots=[image_file()]))
        project = Project.objects.get(owner=self.owner, name="Lantern")
        self.assertRedirects(response, urls_for(project)["edit"] + "#screenshots", fetch_redirect_response=False)
        self.assertEqual(project.screenshots.count(), 1)
        self.assertEqual(project.status, Project.Status.DRAFT)

    def test_invalid_file_shows_an_error_and_saves_nothing(self):
        bad = SimpleUploadedFile("notes.png", b"not an image", content_type="image/png")
        response = self.client.post(self.edit_url, form_data(self.project, tagline="Changed", screenshots=[image_file(), bad]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "notes.png: We could not open this file as an image.")
        self.assertContains(response, 'role="alert"')
        self.assertEqual(self.project.screenshots.count(), 0)
        self.project.refresh_from_db()
        self.assertEqual(self.project.tagline, "A tagline")

    def test_too_big_file_shows_an_error(self):
        header = image_file().read()
        big = SimpleUploadedFile("big.png", header + b"\0" * (5 * 1024 * 1024), content_type="image/png")
        response = self.client.post(self.edit_url, form_data(self.project, screenshots=[big]))
        self.assertContains(response, "larger than 5 MB")
        self.assertEqual(self.project.screenshots.count(), 0)

    def test_more_than_four_in_total_is_refused(self):
        for order in range(3):
            make_shot(self.project, order)
        response = self.client.post(self.edit_url, form_data(self.project, screenshots=[image_file(), image_file()]))
        self.assertContains(response, "You chose 2; you can add 1 more.")
        self.assertEqual(self.project.screenshots.count(), 3)
        self.client.post(self.edit_url, form_data(self.project, screenshots=[image_file()]))
        self.assertEqual(self.project.screenshots.count(), MAX_SCREENSHOTS)
        response = self.client.post(self.edit_url, form_data(self.project, screenshots=[image_file()]))
        self.assertContains(response, "at most 4 screenshots. Remove one first.")
        self.assertEqual(self.project.screenshots.count(), MAX_SCREENSHOTS)

    def test_other_errors_say_the_images_must_be_chosen_again(self):
        response = self.client.post(self.edit_url, form_data(self.project, name="", screenshots=[image_file()]))
        self.assertContains(response, "Choose them again, then save.")
        self.assertEqual(self.project.screenshots.count(), 0)

    def test_upload_rate_limit_counts_each_file(self):
        cache.clear()
        for _i in range(20):  # 20 uploads per hour per user, used up elsewhere
            is_limited("screenshot_add", self.owner.pk, limit=20, window=3600)
        response = self.client.post(self.edit_url, form_data(self.project, screenshots=[image_file()]))
        self.assertContains(response, "Too many changes")
        self.assertEqual(self.project.screenshots.count(), 0)

    def test_someone_else_cannot_upload_to_my_project(self):
        self.client.force_login(make_user("mallory"))
        response = self.client.post(self.edit_url, form_data(self.project, screenshots=[image_file()]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.project.screenshots.count(), 0)

    def test_suspended_owner_cannot_upload(self):
        self.owner.is_suspended = True
        self.owner.save()
        response = self.client.post(self.edit_url, form_data(self.project, screenshots=[image_file()]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.project.screenshots.count(), 0)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class CoverTests(ProjectTestCase):
    """After an upload through the editor the cover appears everywhere the project is shown."""

    def setUp(self):
        super().setUp()
        self.project = make_project(self.owner, status=Project.Status.DRAFT)
        self.client.force_login(self.owner)
        self.client.post(urls_for(self.project)["edit"], form_data(self.project, screenshots=[image_file(size=(64, 40))], publish="1"))
        self.cover = self.project.screenshots.get()
        self.client.logout()

    def test_detail_page_and_open_graph(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, f'src="{self.cover.image.url}" width="64" height="40"')
        self.assertRegex(response.content.decode(), rf'<meta property="og:image" content="https?://[^"]+{self.cover.image.url}">')

    def test_profile_row(self):
        response = self.client.get(reverse("accounts:profile", args=[self.owner.username]))
        # Lists show the small copy, not the full image.
        self.assertContains(response, f'class="project-thumb" src="{self.cover.thumb.url}" width="80" height="56"')
        self.assertNotContains(response, self.cover.image.url)
        self.assertNotContains(response, "project-thumb--empty")

    def test_feed_card_and_explore(self):
        for url in (reverse("social:feed") + "?tab=latest", reverse("pages:explore")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, self.cover.thumb.url)
                self.assertNotContains(response, self.cover.image.url)
                self.assertNotContains(response, "project-thumb--empty")

    def test_placeholder_only_without_an_image(self):
        other = make_project(self.owner, name="Plainly")
        response = self.client.get(reverse("accounts:profile", args=[self.owner.username]))
        self.assertContains(response, "project-thumb--empty", count=1)
        self.assertContains(response, self.cover.thumb.url)
        self.assertContains(response, other.name)
