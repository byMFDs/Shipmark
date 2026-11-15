"""Перевірки S-логотипа, растрових експортів і знака модератора."""
import re
import hashlib
import io
import xml.etree.ElementTree as ET

from PIL import Image

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import SimpleTestCase, TestCase

from config import branding
from pages.brand_icons import apple_touch_icon, favicon_ico, favicon_png, mark_path, path_mask

S_PATH_SHA256 = "182eb40cf6529d541be5f055d69e8d7907500b44e86d65511fb6a20ab24f84fb"


def read(path, mode="r"):
    with open(finders.find(path), mode, **({} if "b" in mode else {"encoding": "utf-8"})) as fh:
        return fh.read()


class BrandFilesTests(SimpleTestCase):
    """Файли бренду на місці й узгоджені."""
    def test_every_svg_uses_the_traced_s(self):
        self.assertEqual(hashlib.sha256(mark_path().encode()).hexdigest(), S_PATH_SHA256)
        for path in (branding.LOGO, branding.LOGO_MARK, branding.LOGO_DARK, branding.LOGO_MARK_DARK, branding.FAVICON):
            with self.subTest(path=path):
                self.assertIn(f'd="{mark_path()}"', read(path))

    def test_raster_icons_are_drawn_from_the_current_mark(self):
        """Fails when logo-mark.svg changed but `python manage.py make_icons` was not run."""
        self.assertEqual(read(branding.FAVICON_ICO, "rb"), favicon_ico())
        self.assertEqual(read(branding.APPLE_TOUCH_ICON, "rb"), apple_touch_icon())
        self.assertEqual(read("brand/favicon.png", "rb"), favicon_png())

    def test_favicon_svg_follows_the_browser_theme(self):
        svg = read(branding.FAVICON)
        self.assertIn("prefers-color-scheme:dark", svg.replace(" ", ""))

    def test_raster_sizes_and_paper_colour(self):
        for name, expected in (("brand/favicon.png", (32, 32)), (branding.APPLE_TOUCH_ICON, (180, 180)),
                               (branding.OG_DEFAULT_IMAGE, (1200, 630))):
            with self.subTest(name=name):
                image = Image.open(io.BytesIO(read(name, "rb")))
                self.assertEqual(image.size, expected)
                if name != "brand/favicon.png":
                    self.assertEqual(image.convert("RGB").getpixel((0, 0)), (244, 243, 238))

    def test_overlapping_outlined_letters_use_nonzero_fill(self):
        # Two overlapping contours with the same winding stay filled (e.g. the h stem and shoulder).
        mask = path_mask("M0 0H8V8H0ZM4 0H12V8H4Z", (12, 8), 1)
        self.assertEqual(mask.getpixel((6, 4)), 255)
        self.assertEqual(mask.getpixel((2, 4)), 255)

    def test_moderator_is_the_red_shield_and_official_stays_blue(self):
        moderator = ET.fromstring(read("icons/badge-moderator.svg"))
        official = ET.fromstring(read("icons/badge-official.svg"))
        shield, bar = list(moderator)
        self.assertEqual(shield.tag.rsplit("}", 1)[-1], "path")
        self.assertEqual(shield.get("fill"), "#FF3131")
        self.assertEqual(bar.tag.rsplit("}", 1)[-1], "rect")
        self.assertEqual(bar.get("fill"), "#FFFFFF")
        self.assertEqual(bar.get("rx"), "10")
        self.assertEqual(official.get("color"), "#0096FF")
        self.assertEqual(next(iter(official)).get("href"), "#account-rosette")


class IconLinksTests(TestCase):
    """Посилання на іконки в head."""
    def test_pages_link_icons_with_a_content_version(self):
        html = self.client.get("/").content.decode()
        for path in (branding.FAVICON, branding.FAVICON_ICO, branding.APPLE_TOUCH_ICON, "brand/favicon.png"):
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


class BrandMarkupTests(TestCase):
    """Нові знаки присутні в хедері, футері й бейджі без зміни поповера."""
    def test_header_and_footer_inline_the_current_s_mark(self):
        html = self.client.get("/").content.decode()
        for tag in ("header", "footer"):
            with self.subTest(tag=tag):
                part = re.search(rf"<{tag}\b.*?</{tag}>", html, re.S).group()
                self.assertIn(f'd="{mark_path()}"', part)
                self.assertIn('class="logo-word"', part)

    def test_moderator_button_uses_the_new_svg_and_keeps_popover_hooks(self):
        from accounts import badges
        from projects.tests import make_user
        user = make_user("mark-review")
        badges.grant(user, "moderator")
        html = self.client.get("/u/mark-review/").content.decode()
        button = re.search(r'<button[^>]*data-badge="moderator".*?</button>', html, re.S).group()
        self.assertIn('fill="#FF3131"', button)
        self.assertIn('fill="#FFFFFF"', button)
        self.assertNotIn('<use', button)
        self.assertIn('aria-haspopup="dialog"', button)
        self.assertIn('id="badge-tpl-moderator"', html)
        self.assertIn("Moderators can review reports.", html)
