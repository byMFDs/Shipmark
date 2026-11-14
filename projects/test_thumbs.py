"""Small list copies of screenshots (feed cards, profile rows, Explore): made on save, backfilled by make_thumbs."""
import io
import os
from io import StringIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from .images import THUMB_BOX
from .models import Project, Screenshot
from .tests import TEMP_MEDIA, ProjectTestCase, image_file, make_project, make_shot, make_user, urls_for


def noisy(size=(1200, 800)):
    """Random pixels: does not compress, so a big image is really big."""
    buffer = io.BytesIO()
    Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3)).save(buffer, format="PNG")
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile("noise.png", buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ThumbnailTests(ProjectTestCase):
    """Мініатюри скриншотів."""
    def setUp(self):
        super().setUp()
        self.project = make_project(self.owner)

    def make(self, upload):
        from .images import clean_screenshot
        return Screenshot.objects.create(project=self.project, image=clean_screenshot(upload), order=0)

    def test_made_on_save_small_webp_with_its_size_stored(self):
        shot = self.make(noisy())
        self.assertRegex(shot.thumb.name, r"^screenshots/thumbs/[0-9a-f]{32}\.webp$")
        with Image.open(shot.thumb.path) as thumb:
            self.assertEqual(thumb.format, "WEBP")
            self.assertLessEqual(max(thumb.size), max(THUMB_BOX))
            self.assertEqual((shot.thumb_width, shot.thumb_height), thumb.size)
            self.assertEqual(len(thumb.getexif()), 0)
        self.assertLess(shot.thumb.size, shot.image.size / 2)  # a fraction of the full image
        self.assertEqual(max(shot.width, shot.height), 1200)  # the full image is untouched

    def test_a_small_image_is_not_enlarged(self):
        shot = self.make(image_file(size=(40, 30)))
        self.assertEqual((shot.thumb_width, shot.thumb_height), (40, 30))

    def test_lists_use_the_thumbnail_and_fall_back_to_the_full_image(self):
        shot = self.make(noisy())
        self.assertEqual((shot.list_image.name, shot.list_width), (shot.thumb.name, shot.thumb_width))
        Screenshot.objects.filter(pk=shot.pk).update(thumb="", thumb_width=0, thumb_height=0)
        shot.refresh_from_db()
        self.assertEqual((shot.list_image.name, shot.list_width, shot.list_height), (shot.image.name, shot.width, shot.height))

    def test_the_project_page_still_shows_the_full_image(self):
        shot = self.make(noisy())
        html = self.client.get(self.project.get_absolute_url()).content.decode()
        self.assertIn(shot.image.url, html)
        self.assertNotIn(shot.thumb.url, html)

    def test_profile_rows_use_the_thumbnail(self):
        shot = self.make(noisy())
        html = self.client.get(reverse("accounts:profile", args=[self.owner.username])).content.decode()
        self.assertIn(f'src="{shot.thumb.url}"', html)
        self.assertNotIn(f'src="{shot.image.url}"', html)

    def test_uploading_in_the_editor_makes_one(self):
        self.client.force_login(self.owner)
        draft = make_project(self.owner, name="Draft", status=Project.Status.DRAFT)
        self.client.post(urls_for(draft)["edit"], {"name": "Draft", "tagline": "t", "description": "", "live_url": "",
                                                    "repo_full_name": "", "tags_text": "", "screenshots": [image_file(size=(900, 600))]})
        self.assertTrue(draft.screenshots.get().thumb)

    def test_reordering_does_not_rebuild_thumbnails(self):
        first, second = self.make(noisy((300, 200))), self.make(noisy((300, 200)))
        names = (first.thumb.name, second.thumb.name)
        self.client.force_login(self.owner)
        self.client.post(reverse("projects:screenshot_move", args=[self.owner.username, self.project.slug, second.pk]), {"direction": "up"})
        first.refresh_from_db(), second.refresh_from_db()
        self.assertEqual((first.thumb.name, second.thumb.name), names)

    def test_both_files_go_when_the_screenshot_or_the_project_goes(self):
        shot = self.make(noisy((300, 200)))
        image, thumb = Path(shot.image.path), Path(shot.thumb.path)
        self.assertTrue(image.exists() and thumb.exists())
        with self.captureOnCommitCallbacks(execute=True):
            shot.delete()
        self.assertFalse(image.exists() or thumb.exists())
        other = self.make(noisy((300, 200)))
        image, thumb = Path(other.image.path), Path(other.thumb.path)
        with self.captureOnCommitCallbacks(execute=True):
            self.project.delete()
        self.assertFalse(image.exists() or thumb.exists())


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class MakeThumbsCommandTests(ProjectTestCase):
    """Команда make_thumbs."""
    def setUp(self):
        super().setUp()
        self.project = make_project(self.owner)

    def old_row(self, n=0):
        """A screenshot from before thumbnails existed: an image, no thumb."""
        shot = make_shot(self.project, n)
        Screenshot.objects.filter(pk=shot.pk).update(thumb="", thumb_width=0, thumb_height=0)
        return Screenshot.objects.get(pk=shot.pk)

    def test_backfills_old_rows_and_is_safe_to_repeat(self):
        a, b = self.old_row(0), self.old_row(1)
        out = StringIO()
        call_command("make_thumbs", stdout=out)
        self.assertIn("Made 2 thumbnail(s), 0 skipped.", out.getvalue())
        a.refresh_from_db(), b.refresh_from_db()
        self.assertTrue(a.thumb and b.thumb)
        names = (a.thumb.name, b.thumb.name)
        out = StringIO()
        call_command("make_thumbs", stdout=out)
        self.assertIn("Made 0 thumbnail(s)", out.getvalue())
        a.refresh_from_db(), b.refresh_from_db()
        self.assertEqual((a.thumb.name, b.thumb.name), names)

    def test_an_unreadable_file_is_skipped_and_reported_and_the_rest_continue(self):
        broken, fine = self.old_row(0), self.old_row(1)
        Path(broken.image.path).write_bytes(b"not an image")
        out, err = StringIO(), StringIO()
        call_command("make_thumbs", stdout=out, stderr=err)
        self.assertIn("Made 1 thumbnail(s), 1 skipped.", out.getvalue())
        self.assertIn(f"screenshot {broken.pk}", err.getvalue())
        broken.refresh_from_db(), fine.refresh_from_db()
        self.assertFalse(broken.thumb)
        self.assertTrue(fine.thumb)
        self.assertEqual(broken.list_image.name, broken.image.name)  # still shown, as the full image

    def test_a_missing_file_is_skipped_too(self):
        gone = self.old_row()
        Path(gone.image.path).unlink()
        out = StringIO()
        call_command("make_thumbs", stdout=out, stderr=StringIO())
        self.assertIn("1 skipped", out.getvalue())
