import re
from pathlib import Path

from django.conf import settings
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings

from config import branding

# Tags that make the browser download something from another site. Plain <a href> links are fine.
EXTERNAL_RESOURCE = re.compile(
    r"<(?:link|script|img|source|iframe|video|audio|embed|object|use|image)\b[^>]*"
    r"\b(?:src|href|srcset|data|xlink:href)=[\"']?(?:https?:)?//",
    re.IGNORECASE,
)
EXTERNAL_CSS = re.compile(r"url\(\s*[\"']?(?:https?:)?//|@import", re.IGNORECASE)


class LandingTests(TestCase):
    def test_landing_returns_200_and_shows_site_name(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, branding.SITE_NAME)
        self.assertContains(response, f"{branding.SITE_NAME} is under construction")

    def test_viewport_meta(self):
        response = self.client.get("/")
        self.assertContains(response, "width=device-width, initial-scale=1, viewport-fit=cover")

    def test_saved_theme_is_applied_before_stylesheets(self):
        # Prevents a flash of the wrong theme: the inline script must run before CSS paints.
        html = self.client.get("/").content.decode()
        self.assertLess(html.index('localStorage.getItem("theme")'), html.index('rel="stylesheet"'))


class StyleguideTests(TestCase):
    def test_hidden_when_debug_is_off(self):
        self.assertEqual(self.client.get("/styleguide/").status_code, 404)

    @override_settings(DEBUG=True)
    def test_shown_when_debug_is_on(self):
        self.assertEqual(self.client.get("/styleguide/").status_code, 200)


class NoExternalResourcesTests(TestCase):
    """No third-party requests: fonts, styles, scripts and images are all self-hosted."""

    @override_settings(DEBUG=True)
    def test_pages_load_nothing_from_other_sites(self):
        for url in ("/", "/styleguide/"):
            html = self.client.get(url).content.decode()
            self.assertIsNone(EXTERNAL_RESOURCE.search(html), url)
            self.assertIsNone(EXTERNAL_CSS.search(html), url)

    def test_static_files_load_nothing_from_other_sites(self):
        static = Path(settings.BASE_DIR) / "static"
        for path in static.rglob("*"):
            if path.suffix == ".css":
                self.assertIsNone(EXTERNAL_CSS.search(path.read_text()), path)
            elif path.suffix == ".js":
                self.assertNotRegex(path.read_text(), r"https?://", path)
            elif path.suffix == ".svg":
                self.assertNotRegex(path.read_text(), r"href=[\"']?(?:https?:)?//", path)


class HallmarkTagTests(SimpleTestCase):
    def render(self, snippet):
        return Template("{% load ui %}" + snippet).render(Context())

    def test_earned_and_not_earned_say_so_in_text(self):
        earned = self.render('{% hallmark "authored" "m" True %}')
        self.assertIn("is-earned", earned)
        self.assertIn("Authored", earned)
        self.assertNotIn("Not yet", earned)

        unearned = self.render('{% hallmark "live" "m" False %}')
        self.assertIn("is-unearned", unearned)
        self.assertIn("Not yet", unearned)

    def test_small_mark_keeps_label_for_screen_readers(self):
        html = self.render('{% hallmark "steady" "s" %}')
        self.assertIn("visually-hidden", html)
        self.assertIn("Steady", html)

    def test_unknown_kind_is_an_error(self):
        with self.assertRaises(ValueError):
            self.render('{% hallmark "used" "m" %}')


class InlineSvgTests(SimpleTestCase):
    def test_strips_comments_and_marks_decorative(self):
        html = Template('{% load ui %}{% icon "github" %}').render(Context())
        self.assertTrue(html.startswith("<svg"))
        self.assertNotIn("<!--", html)
        self.assertIn('aria-hidden="true"', html)
        self.assertIn('class="icon"', html)

    def test_label_makes_it_an_image(self):
        html = Template('{% load ui %}{% icon "close" label="Close" %}').render(Context())
        self.assertIn('role="img" aria-label="Close"', html)
        self.assertNotIn("aria-hidden", html)
