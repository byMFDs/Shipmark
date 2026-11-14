"""Language support (CLAUDE.md section 8): every language is served via Accept-Language,
has a complete catalog, and has the same content pages as English."""
import re

from allauth.account.adapter import get_adapter
from django.conf import settings
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext, ngettext

from projects.tests import make_user

CODES = [code for code, _name in settings.LANGUAGES]
OTHER_CODES = [code for code in CODES if code != "en"]
# Languages that got their legal pages after the English one and say so ("Translation for convenience").
CONVENIENCE_CODES = ["pl", "de", "es", "fr", "pt-br"]
LEGAL_SLUGS = ("privacy", "terms", "cookies")
ALL_SLUGS = ("about", "how-proof-works", "privacy", "terms", "cookies")


class LanguageListTests(SimpleTestCase):
    """Список мов."""
    def test_expected_languages_and_never_russian(self):
        self.assertEqual(CODES, ["en", "uk", "pl", "de", "es", "fr", "pt-br"])
        self.assertNotIn("ru", CODES)


class AcceptLanguageTests(TestCase):
    """Мова з Accept-Language браузера.

    The browser's Accept-Language picks the language when there is no saved choice."""

    def get(self, header, path="/explore/"):
        return self.client.get(path, headers={"Accept-Language": header}).content.decode()

    def test_each_language_is_served(self):
        english = self.get("en")
        self.assertIn('<html lang="en">', english)
        for code in OTHER_CODES:
            with self.subTest(code=code):
                html = self.get(code)
                self.assertIn(f'<html lang="{code}">', html)
                with translation.override(code):
                    translated = gettext("Show projects")
                self.assertNotEqual(translated, "Show projects")
                self.assertIn(translated, html)
                self.assertNotIn(">Show projects<", html)

    def test_regional_variants_find_the_language(self):
        for header, code in [("pt-BR", "pt-br"), ("pt", "pt-br"), ("pt-PT,pt;q=0.8", "pt-br"),
                             ("de-AT", "de"), ("fr-CA", "fr"), ("es-MX", "es"), ("pl-PL", "pl"), ("uk-UA", "uk")]:
            with self.subTest(header=header):
                self.assertIn(f'<html lang="{code}">', self.get(header))

    def test_quality_values_choose_the_best_supported_language(self):
        self.assertIn('<html lang="de">', self.get("ja;q=0.9, de;q=0.8, en;q=0.5"))

    def test_russian_and_unsupported_fall_back_to_english(self):
        for header in ("ru", "ru-RU,ru;q=0.9", "ja", "zh-CN"):
            with self.subTest(header=header):
                self.assertIn('<html lang="en">', self.get(header))


class CatalogTests(SimpleTestCase):
    """Каталоги перекладів."""
    def test_every_catalog_translates_plural_forms(self):
        """Each language answers ngettext() for 0..30 with a non-empty text that is not the English one."""
        for code in OTHER_CODES:
            with translation.override(code):
                for n in range(31):
                    with self.subTest(code=code, n=n):
                        text = ngettext("%(n)s project", "%(n)s projects", n) % {"n": n}
                        self.assertNotIn("project", text.lower())
                        self.assertIn(str(n), text)

    def test_catalogs_are_complete(self):
        """No empty or fuzzy messages: msgfmt statistics would show them. Checked on the .po files."""
        for locale_dir in sorted(p for p in settings.LOCALE_PATHS[0].iterdir() if p.is_dir()):
            text = (locale_dir / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")
            with self.subTest(locale=locale_dir.name):
                self.assertNotIn("#, fuzzy\nmsgid", text.split('msgid ""\nmsgstr ""', 1)[1].split("\n\n", 1)[1])
                for entry in re.split(r"\n\n+", text.strip()):
                    if 'msgid ""\n' in entry and "Project-Id-Version" in entry:
                        continue
                    if re.search(r'^msgstr(?:\[\d+\])? ""\n(?!")', entry + "\n", re.MULTILINE):
                        self.fail(f"Empty translation in {locale_dir.name}: {entry[:120]!r}")


class ContentPagesTests(SimpleTestCase):
    """Кожна мова має кожну markdown-сторінку.

    content/<lang>/<slug>.md: every language has every page, with the same structure as English."""

    @staticmethod
    def read(lang, slug):
        return (settings.CONTENT_DIR / lang / f"{slug}.md").read_text(encoding="utf-8")

    def test_all_pages_exist_in_all_languages(self):
        for code in OTHER_CODES:
            for slug in ALL_SLUGS:
                with self.subTest(code=code, slug=slug):
                    self.assertTrue((settings.CONTENT_DIR / code / f"{slug}.md").is_file())

    def test_placeholders_anchors_and_links_match_english(self):
        """A translator cannot lose a {{ placeholder }}, a #section anchor or a link target."""
        for slug in ALL_SLUGS:
            english = self.read("en", slug)
            want = {
                "placeholders": sorted(re.findall(r"\{\{ \w+ \}\}", english)),
                "anchors": sorted(re.findall(r"\{#([\w-]+)\}", english)),
                "links": sorted(re.findall(r"\]\(((?:/|mailto:|https?:)[^)]*)\)", english)),
            }
            for code in OTHER_CODES:
                text = self.read(code, slug)
                got = {
                    "placeholders": sorted(re.findall(r"\{\{ \w+ \}\}", text)),
                    "anchors": sorted(re.findall(r"\{#([\w-]+)\}", text)),
                    "links": sorted(re.findall(r"\]\(((?:/|mailto:|https?:)[^)]*)\)", text)),
                }
                for key in want:
                    if slug == "about" and key == "links":
                        continue
                    with self.subTest(code=code, slug=slug, key=key):
                        self.assertEqual(got[key], want[key])

    def test_legal_pages_in_new_languages_say_the_english_version_prevails(self):
        for code in CONVENIENCE_CODES:
            for slug in LEGAL_SLUGS:
                with self.subTest(code=code, slug=slug):
                    html = self.client_html(code, slug)
                    quote = re.search(r"<blockquote>(.*?)</blockquote>", html, re.DOTALL)
                    self.assertIsNotNone(quote)
                    self.assertEqual(quote.group(1).count("<p>"), 2, "Draft note + translation note")

    def client_html(self, code, slug):
        from pages.content import load_page

        page = load_page(slug, code)
        self.assertEqual(page["language"], code)
        return page["html"]

    def test_pt_br_pages_load_for_the_pt_br_language_code(self):
        from pages.content import load_page

        self.assertEqual(load_page("terms", "pt-br")["language"], "pt-br")


class NewLanguagePagesTests(TestCase):
    """Сторінки нових мов."""
    def test_how_proof_works_is_translated_and_keeps_section_ids(self):
        for code in OTHER_CODES:
            with self.subTest(code=code):
                html = self.client.get("/how-proof-works/", headers={"Accept-Language": code}).content.decode()
                for anchor in ("authored", "live", "steady", "self-declared"):
                    self.assertIn(f'id="{anchor}"', html)
                self.assertIn('<article class="prose doc"', html)

    def test_legal_page_is_served_in_each_language(self):
        for code in CONVENIENCE_CODES:
            with self.subTest(code=code):
                response = self.client.get("/legal/privacy/", headers={"Accept-Language": code})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'<html lang="{code}">')
                self.assertNotContains(response, "Privacy policy")


class AboutPageTests(TestCase):
    """Сторінка «Про нас»."""
    def test_about_is_real_content_in_every_language(self):
        from config import branding

        for code in CODES:
            with self.subTest(code=code):
                html = self.client.get("/about/", headers={"Accept-Language": code}).content.decode()
                self.assertIn(f'href="mailto:{branding.CONTACT_EMAIL}"', html)  # contact comes from branding.py
                self.assertIn('href="/how-proof-works/"', html)
                self.assertTrue("Danylo Rudenko" in html or "Данило Руденко" in html)
                self.assertIn("TODO", html)  # things the developer must confirm stay visible until edited
                for anchor in ("problem", "proof", "not-verified", "builders", "who", "next", "contact"):
                    self.assertIn(f'id="{anchor}"', html)
                for leftover in ("This page is a placeholder", "Ta strona jest tymczasowa", "Це тимчасова сторінка", "{{"):
                    self.assertNotIn(leftover, html.split("<main", 1)[1])


class SignInLanguageTests(TestCase):
    """Повідомлення про вхід і вихід мовою сторінки.

    The "signed in" / "signed out" toasts are in the same language as the page that shows them."""

    def setUp(self):
        self.user = make_user("olena")
        self.user.preferred_language = "uk"
        self.user.save(update_fields=["preferred_language"])

    def test_signed_in_message_uses_the_saved_language(self):
        # The GitHub callback starts in the browser language (English here), not in the saved one.
        request = RequestFactory().get("/accounts/github/login/callback/", headers={"Accept-Language": "en"})
        SessionMiddleware(lambda r: None).process_request(request)
        MessageMiddleware(lambda r: None).process_request(request)
        request.user = self.user  # allauth calls post_login right after logging the person in
        with translation.override("en"):
            get_adapter(request).post_login(request, self.user, email_verification="none", signal_kwargs=None,
                                            email=None, signup=False, redirect_url=None)
            texts = [str(m) for m in get_messages(request)]
            self.assertEqual(translation.get_language(), "uk")
        with translation.override("uk"):
            expected = gettext("Signed in as %(name)s.") % {"name": self.user.display_name or self.user.username}
        self.assertEqual(texts, [expected])
        self.assertNotEqual(expected, "Signed in as olena.")
        self.assertEqual(request.saved_language, "uk")  # the middleware writes it to the language cookie

    def test_language_cookie_follows_the_saved_preference(self):
        self.client.force_login(self.user)
        response = self.client.get("/explore/", headers={"Accept-Language": "en"})
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "uk")
        again = self.client.get("/explore/")
        self.assertNotIn(settings.LANGUAGE_COOKIE_NAME, again.cookies)  # written only when it differs

    def test_signed_out_page_and_message_stay_in_the_saved_language(self):
        self.client.force_login(self.user)
        self.client.get("/explore/", headers={"Accept-Language": "en"})  # syncs the cookie
        response = self.client.post(reverse("account_logout"), follow=True, headers={"Accept-Language": "en"})
        html = response.content.decode()
        self.assertIn('<html lang="uk">', html)
        with translation.override("uk"):
            self.assertIn(gettext("You are signed out."), html)

    def test_anonymous_requests_never_get_a_language_cookie(self):
        response = self.client.get("/explore/", headers={"Accept-Language": "de"})
        self.assertNotIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)
