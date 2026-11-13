"""Site footer: one grid of link columns, a bottom bar with the copyright and the controls."""
import re
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from config import context_processors


def columns(html):
    """{heading: [link labels]} from the footer."""
    footer = html[html.index('<footer class="site-footer'):]
    found = {}
    for block in re.findall(r'<nav class="site-footer__col".*?</nav>', footer, re.S):
        heading = re.search(r'<h2 class="site-footer__heading label"[^>]*>([^<]+)</h2>', block).group(1)
        found[heading] = re.findall(r'<li><a href="[^"]+">([^<]+)</a></li>', block)
    return found


class FooterTests(TestCase):
    def page(self, url="/explore/"):
        return self.client.get(url).content.decode()

    def test_three_columns_in_order(self):
        found = columns(self.page())
        self.assertEqual(list(found), ["Product", "Company", "Legal"])
        self.assertEqual(found["Product"][:3], ["Feed", "Explore", "News"])
        self.assertEqual(found["Company"][:2], ["About", "How proof works"])
        self.assertEqual(found["Legal"], ["Privacy", "Terms", "Cookies"])

    def test_community_link_follows_the_flag(self):
        with override_settings(COMMUNITY_ENABLED=True):
            self.assertIn("Community", columns(self.page())["Product"])
        with override_settings(COMMUNITY_ENABLED=False):
            self.assertNotIn("Community", columns(self.page())["Product"])

    def test_brand_block_has_logo_domain_and_tagline(self):
        html = self.page()
        brand = context_processors._BRAND
        self.assertIn('class="site-footer__home"', html)
        self.assertIn(f'<p class="site-footer__domain mono">{brand.SITE_DOMAIN}</p>', html)
        self.assertIn(f'<p class="site-footer__tagline">{brand.TAGLINE}</p>', html)

    def test_copyright_comes_from_legal_owner_name_in_sentence_case(self):
        with mock.patch.object(context_processors._BRAND, "LEGAL_OWNER_NAME", "Example Studio"):
            html = self.page()
        copy = re.search(r'<p class="site-footer__copy">(.*?)</p>', html).group(1)
        self.assertRegex(copy, r"^&copy; \d{4} Example Studio$")
        self.assertNotIn("label", re.search(r'<p class="site-footer__copy"', html).group(0))  # not mono caps

    def test_language_form_works_without_js_and_submits_on_change_with_js(self):
        html = self.page()
        form = re.search(r'<form class="lang-form".*?</form>', html, re.S).group(0)
        self.assertIn(f'action="{reverse("set_language")}"', form)
        self.assertIn('method="post"', form)
        self.assertIn("csrfmiddlewaretoken", form)
        self.assertIn("data-autosubmit", form)
        self.assertIn('<button class="btn btn--secondary lang-form__submit" type="submit">', form)
        self.assertIn('<label class="visually-hidden" for="footer-language">', form)
        self.assertEqual(form.count("<option"), len(settings.LANGUAGES))
        self.assertIn("js/language.js", html)

    def test_theme_switch_has_three_pressed_state_buttons(self):
        html = self.page()
        switch = re.search(r'<div class="theme-switch needs-js" role="group".*?</div>', html, re.S).group(0)
        self.assertEqual(len(re.findall(r"data-theme-choice=", switch)), 3)
        self.assertEqual(switch.count('aria-pressed="true"'), 1)

    def test_every_language_renders_the_footer(self):
        for code, _name in settings.LANGUAGES:
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = code
            with self.subTest(language=code):
                found = columns(self.page())
                self.assertEqual(len(found), 3)
                self.assertTrue(all(found.values()))

    def test_landing_footer_is_flush(self):
        self.assertIn('class="site-footer site-footer--flush"', self.page("/"))
