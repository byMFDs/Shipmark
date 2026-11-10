from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase

from config.context_processors import brand


class SettingsTests(SimpleTestCase):
    def test_settings_load(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")
        self.assertEqual(settings.ROOT_URLCONF, "config.urls")
        self.assertEqual(settings.LANGUAGE_CODE, "en")
        self.assertNotIn("ru", [code for code, _ in settings.LANGUAGES])

    def test_all_local_apps_registered(self):
        for app in ("accounts", "projects", "verification", "social", "pages", "moderation"):
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_brand_context_processor(self):
        context = brand(RequestFactory().get("/"))
        self.assertEqual(context["brand"].SITE_NAME, "Shipmark")
        self.assertTrue(hasattr(context["brand"], "CONTACT_EMAIL"))


class UserModelTests(TestCase):
    def test_custom_user_has_profile_fields(self):
        user = get_user_model().objects.create_user("danylo", password="x" * 12)
        self.assertFalse(user.is_suspended)
        self.assertEqual(user.github_login, "")

    def test_github_login_unique_only_when_set(self):
        User = get_user_model()
        User.objects.create_user("a")
        User.objects.create_user("b")  # both empty: allowed
        User.objects.create_user("c", github_login="octocat")
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user("d", github_login="octocat")
