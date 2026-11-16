"""Аватарка й обкладинка офіційних акаунтів: лише суперкористувач, лише через конвеєр зображень."""
import io
import re
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from moderation.models import AuditLog
from news.models import NewsPost
from projects.tests import make_user

from . import badges
from .models import UserBadge
from .roles import can_set_official_pictures
from .system import system_user

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix="shipmark-test-official-")


def image(size=(800, 600), fmt="PNG", color="#c7f36b"):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, fmt)
    return buffer.getvalue()


def upload(name="a.png", data=None, content_type="image/png"):
    return SimpleUploadedFile(name, data if data is not None else image(), content_type=content_type)


@override_settings(MEDIA_ROOT=MEDIA)
class OfficialPicturesTests(TestCase):
    """Один суперкористувач, один персонал без суперправ, системний акаунт «shipmark» і звичайна людина."""
    def setUp(self):
        self.boss = User.objects.create_superuser("boss", "boss@example.com", "pw")
        self.staff = User.objects.create_user("staff", "staff@example.com", "pw", is_staff=True)
        from django.contrib.auth.models import Permission
        self.staff.user_permissions.add(*Permission.objects.filter(content_type__app_label="accounts", content_type__model="user"))
        self.system = system_user()
        self.ana = make_user("ana")
        self.official = make_user("brand")
        badges.grant(self.official, UserBadge.Kind.OFFICIAL)

    def url(self, user):
        return reverse("admin:accounts_user_change", args=[user.pk])

    def form_data(self, user, **extra):
        """Мінімальний валідний POST форми користувача: поточні значення форми плюс додаткові."""
        self.client.force_login(self.boss if extra.pop("as_boss", True) else self.staff)
        form = self.client.get(self.url(user)).context["adminform"].form
        data = {}
        for name, field in form.fields.items():
            value = form.initial.get(name)
            if value in (None, ""):
                continue
            if isinstance(value, bool):
                if value:
                    data[name] = "on"
            elif isinstance(value, (list, tuple)):
                data[name] = [getattr(v, "pk", v) for v in value]
            else:
                data[name] = value
        data.update(extra)
        # the inline formsets need their management forms
        for prefix in ("badges", "links"):
            data.setdefault(f"{prefix}-TOTAL_FORMS", 0)
            data.setdefault(f"{prefix}-INITIAL_FORMS", 0)
        return data

    def post(self, user, as_boss=True, **extra):
        data = self.form_data(user, as_boss=as_boss, **extra)
        return self.client.post(self.url(user), data)

    def fresh(self, user):
        return User.objects.get(pk=user.pk)

    # ----- who may -----
    def test_role_check(self):
        self.assertTrue(can_set_official_pictures(self.boss, self.system))
        self.assertTrue(can_set_official_pictures(self.boss, self.official))
        self.assertFalse(can_set_official_pictures(self.boss, self.ana))
        self.assertFalse(can_set_official_pictures(self.staff, self.system))
        self.assertFalse(can_set_official_pictures(self.official, self.official))

    def test_form_has_upload_fields_only_for_superuser_on_official_accounts(self):
        self.client.force_login(self.boss)
        for target, expected in ((self.system, True), (self.official, True), (self.ana, False)):
            with self.subTest(target=target.username):
                fields = self.client.get(self.url(target)).context["adminform"].form.fields
                self.assertEqual("avatar_upload" in fields, expected)
                self.assertEqual("cover_upload" in fields, expected)
        self.client.force_login(self.staff)
        fields = self.client.get(self.url(self.system)).context["adminform"].form.fields
        self.assertNotIn("avatar_upload", fields)
        self.assertNotIn("cover_upload", fields)

    # ----- upload -----
    def test_superuser_uploads_avatar_and_cover_for_the_system_account(self):
        response = self.post(self.system, avatar_upload=upload(), cover_upload=upload("c.png", image((1800, 700))))
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["adminform"].form.errors)
        system = self.fresh(self.system)
        self.assertTrue(re.fullmatch(r"avatars/[0-9a-f]{32}\.webp", system.avatar.name), system.avatar.name)
        self.assertTrue(re.fullmatch(r"covers/[0-9a-f]{32}\.webp", system.cover.name), system.cover.name)
        self.assertEqual(system.avatar_source, "upload")
        with Image.open(system.avatar.path) as stored:
            self.assertEqual((stored.format, stored.size), ("WEBP", (512, 512)))
            self.assertFalse(stored.info.get("exif"))
        log = AuditLog.objects.filter(action="accounts.official_pictures").get()
        self.assertEqual((log.actor, log.target_id, log.metadata["changed"]), (self.boss, str(self.system.pk), ["avatar", "cover"]))

    def test_replacing_removes_the_old_file_and_names_are_random(self):
        self.post(self.official, avatar_upload=upload())
        first = self.fresh(self.official).avatar
        first_path = first.path
        with self.captureOnCommitCallbacks(execute=True):  # the old file is removed after the commit
            self.post(self.official, avatar_upload=upload("b.png", image((600, 600), color="#071c1e")))
        second = self.fresh(self.official).avatar
        self.assertNotEqual(first.name, second.name)
        import os
        self.assertFalse(os.path.exists(first_path))

    def test_remove_avatar(self):
        self.post(self.official, avatar_upload=upload())
        self.post(self.official, remove_avatar="on")
        official = self.fresh(self.official)
        self.assertFalse(official.avatar)
        self.assertEqual(official.avatar_source, "")

    # ----- refused -----
    def test_not_an_image_too_big_or_too_many_pixels_are_refused(self):
        bomb = io.BytesIO()
        Image.new("L", (6000, 5000)).save(bomb, "PNG")  # 30 million pixels, tiny file
        cases = {
            "text": upload("a.png", b"not an image at all"),
            "huge": upload("a.png", b"\x89PNG" + b"0" * (5 * 1024 * 1024 + 10)),
            "bomb": upload("b.png", bomb.getvalue()),
        }
        for name, bad in cases.items():
            with self.subTest(case=name):
                response = self.post(self.system, avatar_upload=bad)
                self.assertEqual(response.status_code, 200)  # the form is shown again with an error
                self.assertIn("avatar_upload", response.context["adminform"].form.errors)
                self.assertFalse(self.fresh(self.system).avatar)

    def test_staff_without_superuser_cannot_set_pictures_even_by_a_hand_made_post(self):
        response = self.post(self.system, as_boss=False, avatar_upload=upload(), cover_upload=upload(),
                             avatar="avatars/evil.webp")
        self.assertIn(response.status_code, (200, 302))
        system = self.fresh(self.system)
        self.assertFalse(system.avatar)
        self.assertFalse(system.cover)
        self.assertFalse(AuditLog.objects.filter(action="accounts.official_pictures").exists())

    def test_superuser_cannot_set_pictures_of_an_ordinary_account_here(self):
        self.post(self.ana, avatar_upload=upload())
        self.assertFalse(self.fresh(self.ana).avatar)

    def test_raw_picture_values_are_read_only_for_everyone(self):
        self.post(self.official, avatar="avatars/raw.webp", avatar_source="github", avatar_url="https://x.example/a.png")
        official = self.fresh(self.official)
        self.assertEqual((official.avatar.name, official.avatar_source, official.avatar_url), ("", "", ""))

    # ----- where it shows -----
    def test_picture_shows_on_profile_og_and_news_byline(self):
        self.post(self.system, avatar_upload=upload())
        system = self.fresh(self.system)
        profile = self.client.get(reverse("accounts:profile", args=[system.username])).content.decode()
        self.assertIn(system.avatar.url, profile)
        self.assertRegex(profile, r'<meta property="og:image" content="[^"]*' + re.escape(system.avatar.url))
        post = NewsPost.objects.create(title="Hello", slug="hello", body="Body", published_at=timezone.now())
        news = self.client.get(post.get_absolute_url()).content.decode()
        self.assertIn(system.avatar.url, news)
