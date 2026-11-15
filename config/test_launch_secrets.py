"""Не дозволяє запуск production зі слабкими або відомими dev-ключами."""
from django.test import SimpleTestCase


class ProductionSecretTests(SimpleTestCase):
    """Production відмовляється працювати з порожнім або dev-ключем сесій чи банів."""

    def test_production_refuses_empty_short_or_known_development_secret(self):
        from config.tests import ProductionSettingsTests

        for secret in ("", "short", "dev-insecure-key-do-not-use-in-production", "django-insecure-" + "a1" * 40):
            with self.subTest(secret_type="empty" if not secret else "invalid"):
                result = ProductionSettingsTests._manage(self, "check", SECRET_KEY=secret)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("SECRET_KEY", result.stderr)

    def test_production_refuses_the_known_development_ban_key(self):
        from config.tests import ProductionSettingsTests

        result = ProductionSettingsTests._manage(
            self, "check", BAN_HASH_KEY="dev-insecure-ban-hash-key-do-not-use-in-production",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BAN_HASH_KEY", result.stderr)
