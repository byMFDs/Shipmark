import re
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings

from config import branding

from .content import load_page, render_markdown

# Tags that make the browser download something from another site. Plain <a href> links are fine.
EXTERNAL_RESOURCE = re.compile(
    r"<(?:link|script|img|source|iframe|video|audio|embed|object|use|image)\b[^>]*"
    r"\b(?:src|href|srcset|data|xlink:href)=[\"']?(?:https?:)?//",
    re.IGNORECASE,
)
EXTERNAL_CSS = re.compile(r"url\(\s*[\"']?(?:https?:)?//|@import", re.IGNORECASE)


class LandingTests(TestCase):
    """Лендинг."""
    def test_landing_returns_200_and_shows_site_name(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, branding.SITE_NAME)

    def test_viewport_meta(self):
        response = self.client.get("/")
        self.assertContains(response, "width=device-width, initial-scale=1, viewport-fit=cover")

    def test_saved_theme_is_applied_before_stylesheets(self):
        # Prevents a flash of the wrong theme: the (blocking, non-module) script must come before the CSS.
        html = self.client.get("/").content.decode()
        script = html.index('js/theme-init')
        self.assertLess(script, html.index('rel="stylesheet"'))
        self.assertNotIn("type=\"module\"", html[html.rindex("<script", 0, script):script + 60])


class StyleguideTests(TestCase):
    """Styleguide лише в розробці."""
    def test_hidden_when_debug_is_off(self):
        self.assertEqual(self.client.get("/styleguide/").status_code, 404)

    @override_settings(DEBUG=True)
    def test_shown_when_debug_is_on(self):
        self.assertEqual(self.client.get("/styleguide/").status_code, 200)


class NoExternalResourcesTests(TestCase):
    """Жодних сторонніх ресурсів.

    No third-party requests: fonts, styles, scripts and images are all self-hosted."""

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
    """Тег марки."""
    def render(self, snippet):
        return Template("{% load ui %}" + snippet).render(Context())

    def test_earned_and_not_earned_say_so_in_text(self):
        earned = self.render('{% hallmark "authored" "m" True %}')
        self.assertIn("is-earned", earned)
        self.assertIn("Repo owner", earned)
        self.assertNotIn("Not yet", earned)

        unearned = self.render('{% hallmark "live" "m" False %}')
        self.assertIn("is-unearned", unearned)
        self.assertIn("Not yet", unearned)

    def test_small_mark_shows_label_and_hides_only_the_state(self):
        # Chips show the name at every size; small unearned marks keep "Not yet" for screen readers only.
        earned = self.render('{% hallmark "steady" "s" %}')
        self.assertIn('<span class="hallmark__label">Steady</span>', earned)
        self.assertIn('aria-hidden="true"', earned)  # the check glyph is decorative

        unearned = self.render('{% hallmark "steady" "s" False %}')
        self.assertIn('hallmark__state visually-hidden">Not yet', unearned)

    def test_unknown_kind_is_an_error(self):
        with self.assertRaises(ValueError):
            self.render('{% hallmark "used" "m" %}')


class InlineSvgTests(SimpleTestCase):
    """Вставка SVG."""
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


class LanguageDetectionTests(TestCase):
    """Порядок вибору мови.

    CLAUDE.md section 8: saved preference, then cookie, then Accept-Language, then English."""

    # /explore/: the same page for everyone (signed-in visitors of / are redirected to the feed).
    UK_TEXT = "Показати проєкти"
    EN_TEXT = "Show projects"

    def get(self, **extra):
        return self.client.get("/explore/", **extra).content.decode()

    def test_accept_language_uk_gives_ukrainian(self):
        html = self.get(headers={"Accept-Language": "uk"})
        self.assertIn(self.UK_TEXT, html)
        self.assertIn('<html lang="uk">', html)

    def test_unknown_language_falls_back_to_english(self):
        for header in ("ru", "ja-JP,ar;q=0.8", "zz"):
            html = self.get(headers={"Accept-Language": header})
            self.assertIn(self.EN_TEXT, html, header)
            self.assertIn('<html lang="en">', html)

    def test_no_header_gives_english(self):
        self.assertIn(self.EN_TEXT, self.get())

    def test_cookie_overrides_header(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        self.assertIn(self.EN_TEXT, self.get(headers={"Accept-Language": "uk"}))
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "uk"
        self.assertIn(self.UK_TEXT, self.get(headers={"Accept-Language": "en"}))

    def test_saved_user_preference_overrides_cookie_and_header(self):
        user = get_user_model().objects.create_user("danylo", preferred_language="uk")
        self.client.force_login(user)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        self.assertIn(self.UK_TEXT, self.get(headers={"Accept-Language": "en"}))

    def test_switcher_sets_cookie_and_returns_to_same_page(self):
        response = self.client.post("/i18n/set-language/", {"language": "uk", "next": "/about/"})
        self.assertRedirects(response, "/about/", fetch_redirect_response=False)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "uk")
        self.assertIn("Про проєкт", self.client.get("/about/").content.decode())

    def test_switcher_ignores_unsafe_redirect_and_unknown_language(self):
        response = self.client.post("/i18n/set-language/", {"language": "ru", "next": "https://evil.example/"})
        self.assertEqual(response["Location"], "/")
        self.assertNotIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)

    def test_switcher_saves_choice_on_signed_in_account(self):
        user = get_user_model().objects.create_user("danylo", preferred_language="uk")
        self.client.force_login(user)
        self.client.post("/i18n/set-language/", {"language": "en"})
        user.refresh_from_db()
        self.assertEqual(user.preferred_language, "en")
        self.assertIn(self.EN_TEXT, self.get(headers={"Accept-Language": "uk"}))

    def test_switcher_requires_post(self):
        self.assertEqual(self.client.get("/i18n/set-language/").status_code, 405)

    def test_footer_has_switcher_form(self):
        html = self.get()
        self.assertIn('action="/i18n/set-language/"', html)
        self.assertIn('name="language"', html)


class ContentPageTests(TestCase):
    """Контентні сторінки."""
    def test_about_in_each_language(self):
        self.assertContains(self.client.get("/about/"), "<h1>About Shipmark</h1>")
        uk = self.client.get("/about/", headers={"Accept-Language": "uk"})
        self.assertContains(uk, "<h1>Про Shipmark</h1>")

    def test_falls_back_to_english_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "en").mkdir()
            (Path(tmp) / "en" / "only-en.md").write_text("# Hello\n\nText")
            with override_settings(CONTENT_DIR=Path(tmp)):
                page = load_page("only-en", "uk")
        self.assertEqual(page["language"], "en")
        self.assertEqual(page["title"], "Hello")

    def test_missing_page_and_bad_slugs_are_404_or_none(self):
        self.assertIsNone(load_page("nope", "en"))
        for slug in ("../CLAUDE", "a/b", "A", ""):
            self.assertIsNone(load_page(slug, "en"), slug)

    def test_output_is_sanitized(self):
        html = render_markdown(
            "# T\n\n<script>alert(1)</script>\n\n[x](javascript:alert(1)) [ok](https://example.com)\n\n"
            "<img src=x onerror=alert(1)>"
        )
        self.assertNotIn("<script", html)
        self.assertNotIn("javascript:", html)
        self.assertNotIn("onerror", html)
        self.assertNotIn("<img", html)
        self.assertIn('href="https://example.com"', html)
        self.assertIn('rel="noopener"', html)
