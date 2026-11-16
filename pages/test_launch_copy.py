"""Завершені редакційні тексти та погоджена політика запуску всіма мовами."""

from django.conf import settings
from django.test import SimpleTestCase, TestCase

from config import branding
from pages.content import load_page


class LaunchCopyTests(SimpleTestCase):
    """У текстах немає редакційних заглушок, а контакти та основні факти збережені."""

    def test_content_is_finished_and_contacts_are_resolved(self):
        for code, _name in settings.LANGUAGES:
            for slug in ("about", "privacy", "terms", "cookies", "community-rules", "how-proof-works"):
                with self.subTest(language=code, slug=slug):
                    page = load_page(slug, code)
                    self.assertEqual(page["language"], code)
                    self.assertNotIn("{{", page["html"])
                    self.assertNotRegex(page["html"], r"\bTODO\b|\{#who\}|not been reviewed by a lawyer")
                    source = (settings.CONTENT_DIR / code / f"{slug}.md").read_text()
                    self.assertNotRegex(source.split("\n\n")[1], r"Draft|Чернетка|Wersja robocza|Entwurf|Borrador|Brouillon|Rascunho")
                    if slug == "about":
                        self.assertIn(f"mailto:{branding.CONTACT_EMAIL}", page["html"])
                        self.assertIn('href="/support/"', page["html"])
                        self.assertNotIn('id="who"', page["html"])

    def test_every_privacy_translation_keeps_the_operational_limits(self):
        for code, _name in settings.LANGUAGES:
            with self.subTest(language=code):
                source = (settings.CONTENT_DIR / code / "privacy.md").read_text()
                for fact in ("24", "12", "S3", "GitHub", "#support", "#recipients"):
                    self.assertIn(fact, source)
                self.assertNotIn("TODO", source)
                self.assertNotIn("/u/<username>/", source)
                self.assertNotRegex(source, r"(?i)\bsticker\b|вибраний стікер")


class NumberedLabelTests(TestCase):
    """Лендинг не має нумерованих ярликів на кшталт «01 / The standard» в жодній мові."""
    def test_landing_has_no_numbered_section_labels(self):
        for lang in ("en", "uk", "pl", "de", "es", "fr", "pt-br"):
            with self.subTest(lang=lang):
                html = self.client.get("/", headers={"Accept-Language": lang}).content.decode()
                self.assertNotRegex(html, r">\s*0\d\s*/\s*\S")
                self.assertNotIn('class="eyebrow numeric"', html)


class LandingUptimeExampleTests(TestCase):
    """Лендинг показує стовпчики лише як позначений приклад, а реальні проєкти не отримують вигаданих даних."""
    def test_landing_example_is_labelled_and_compact(self):
        html = self.client.get("/").content.decode()
        self.assertIn("data-uptime-bars", html)
        self.assertIn("Example data", html)
        self.assertIn("Illustrative project", html)
        self.assertIn("uptime-bars--compact", html)
        self.assertIn("js/uptime.js", html)

    def test_example_summary_is_not_a_real_project(self):
        from pages.views import example_uptime
        summary = example_uptime()
        self.assertEqual(len(summary.days), 30)
        self.assertTrue(all(day.date is None for day in summary.days))
