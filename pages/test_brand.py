"""Logo C everywhere: every icon file is drawn from the same mark, and icon URLs change when the files change."""
import re

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import SimpleTestCase, TestCase

from config import branding
from pages.brand_icons import apple_touch_icon, favicon_ico, mark_path

LOGO_C = "M0 0H32V32H0ZM4 26H12L22 6H14ZM20 18H28V26H20Z"


def read(path, mode="r"):
    with open(finders.find(path), mode, **({} if "b" in mode else {"encoding": "utf-8"})) as fh:
        return fh.read()


class BrandFilesTests(SimpleTestCase):
    def test_every_svg_uses_logo_c(self):
        self.assertEqual(mark_path(), LOGO_C)
        for path in (branding.LOGO, branding.LOGO_MARK, branding.LOGO_DARK, branding.LOGO_MARK_DARK, branding.FAVICON):
            with self.subTest(path=path):
                self.assertIn(f'd="{LOGO_C}"', read(path))

    def test_raster_icons_are_drawn_from_the_current_mark(self):
        """Fails when logo-mark.svg changed but `python manage.py make_icons` was not run."""
        self.assertEqual(read(branding.FAVICON_ICO, "rb"), favicon_ico())
        self.assertEqual(read(branding.APPLE_TOUCH_ICON, "rb"), apple_touch_icon())

    def test_favicon_svg_follows_the_browser_theme(self):
        svg = read(branding.FAVICON)
        self.assertIn("prefers-color-scheme:dark", svg.replace(" ", ""))


class IconLinksTests(TestCase):
    def test_pages_link_icons_with_a_content_version(self):
        html = self.client.get("/").content.decode()
        for path in (branding.FAVICON, branding.FAVICON_ICO, branding.APPLE_TOUCH_ICON):
            with self.subTest(path=path):
                self.assertRegex(html, re.escape(f"/static/{path}?v=") + r"[0-9a-f]{10}\"")
        self.assertNotIn("corner", html)

    def test_favicon_ico_redirects_to_the_static_file(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"/static/{branding.FAVICON_ICO}")

    def test_site_url_defaults(self):
        self.assertEqual(settings.SITE_URL, "http://localhost:8000")
        from config.tests import ProductionSettingsTests

        result = ProductionSettingsTests._manage(self, "shell", "-c", "from django.conf import settings as s; print(s.SITE_URL)")
        self.assertIn("https://shipmark.me", result.stdout, result.stderr)
        result = ProductionSettingsTests._manage(self, "check", SITE_URL="http://shipmark.me")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SITE_URL must start with https://", result.stderr)
