"""Перевірки домену shipmark.org і єдиної контактної адреси."""
import re
import subprocess
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from config import branding
from pages.content import load_page

ROOT = Path(settings.BASE_DIR)
OLD = ("shipmark.me", "shipmark@gmail.com")
SCANNED = ("templates", "content", "locale", "config", "accounts", "projects", "pages", "social", "community",
           "moderation", "news", "support", "verification", "static/js", "static/css", "scripts", ".env.example")
EXCLUDED = {"config/test_domain.py"}
LANGS = ("en", "uk", "pl", "de", "es", "fr", "pt-br")


def tracked():
    out = subprocess.run(["git", "ls-files", *SCANNED], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p not in EXCLUDED and not p.endswith((".png", ".ico", ".woff2", ".mo", ".svg"))]


class OldDomainTests(SimpleTestCase):
    """Старий домен і старі адреси не лишились у tracked коді, шаблонах, контенті й перекладах."""
    def test_no_old_domain_or_address_in_tracked_files(self):
        found = []
        for rel in tracked():
            text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore").lower()
            found += [f"{rel}: {old}" for old in OLD if old in text]
        self.assertEqual(found, [])

    def test_branding_values(self):
        self.assertEqual(branding.SITE_DOMAIN, "shipmark.org")
        self.assertEqual(branding.CONTACT_EMAIL, "shipmark.org@gmail.com")


class ContactLinkTests(SimpleTestCase):
    """Кожен mailto у контентних сторінках дорівнює CONTACT_EMAIL, текст і href однакові."""
    def test_every_mailto_matches_contact_email(self):
        pages = ("about", "privacy", "terms", "cookies", "community-rules", "how-proof-works")
        for lang in LANGS:
            for slug in pages:
                with self.subTest(lang=lang, slug=slug):
                    html = load_page(slug, lang)["html"]
                    for href, text in re.findall(r'href="mailto:([^"?]+)[^"]*"[^>]*>([^<]*)<', html):
                        self.assertEqual(href, branding.CONTACT_EMAIL)
                        self.assertEqual(text.strip(), branding.CONTACT_EMAIL)

    def test_legal_pages_do_link_the_contact(self):
        for lang in LANGS:
            self.assertIn(f"mailto:{branding.CONTACT_EMAIL}", load_page("privacy", lang)["html"])
