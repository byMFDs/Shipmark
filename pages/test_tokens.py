"""Colour tokens (static/css/tokens.css): both dark blocks stay in sync, every pair the design relies on stays
WCAG AA in both themes, and the styleguide's table shows the real values. Polish-3 stage 3b (dark theme)."""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from pages.test_halo import contrast, tokens
from pages.views import STYLEGUIDE_TOKENS

TOKENS = (Path(settings.BASE_DIR) / "static" / "css" / "tokens.css").read_text()


def rule(selector_start):
    start = TOKENS.index(selector_start)
    return TOKENS[TOKENS.index("{", start) + 1:TOKENS.index("}", start)]


def os_dark():
    """The dark values chosen by the operating system (inside @media prefers-color-scheme: dark)."""
    media = TOKENS.index("@media (prefers-color-scheme: dark)")
    start = TOKENS.index(':root:not([data-theme="light"])', media)
    return TOKENS[TOKENS.index("{", start) + 1:TOKENS.index("}", start)]


LIGHT = tokens(rule(':root,\n[data-theme="light"]'))
DARK = tokens(rule('[data-theme="dark"],\n.band'))
THEMES = {"light": LIGHT, "dark": DARK}


class TokenTests(SimpleTestCase):
    def test_the_two_dark_blocks_are_the_same(self):
        self.assertEqual(DARK, tokens(os_dark()))

    def test_text_pairs_are_at_least_4_5_to_1(self):
        for theme, t in THEMES.items():
            for fg in ("text", "muted", "accent-text", "danger"):
                for bg in ("paper", "surface", "raised"):
                    with self.subTest(theme=theme, pair=f"{fg} on {bg}"):
                        self.assertGreaterEqual(contrast(t[fg], t[bg]), 4.5)
            with self.subTest(theme=theme, pair="proof on proof-bg"):
                self.assertGreaterEqual(contrast(t["proof"], t["proof-bg"]), 4.5)
            with self.subTest(theme=theme, pair="on-accent on accent"):
                self.assertGreaterEqual(contrast(t["on-accent"], t["accent"]), 4.5)
            with self.subTest(theme=theme, pair="on-danger on danger"):
                self.assertGreaterEqual(contrast(t["on-danger"], t["danger"]), 4.5)

    def test_control_edges_and_focus_are_at_least_3_to_1(self):
        for theme, t in THEMES.items():
            for bg in ("paper", "surface", "raised"):
                for fg in ("line-strong", "focus", "accent"):
                    with self.subTest(theme=theme, pair=f"{fg} on {bg}"):
                        self.assertGreaterEqual(contrast(t[fg], t[bg]), 3.0)

    def test_dark_levels_stand_apart(self):
        """The old dark surface sat at 1.10:1 on the page and its hairlines at 1.27:1: cards melted into the page."""
        self.assertGreaterEqual(contrast(DARK["surface"], DARK["paper"]), 1.12)
        self.assertGreaterEqual(contrast(DARK["raised"], DARK["surface"]), 1.1)
        self.assertGreaterEqual(contrast(DARK["line"], DARK["surface"]), 1.4)

    def test_the_styleguide_table_shows_the_real_values(self):
        for name, light, dark, _use in STYLEGUIDE_TOKENS:
            if name == "band-bg":
                continue  # a single value per theme, outside the two theme blocks
            with self.subTest(token=name):
                self.assertEqual(LIGHT[name].upper(), light.upper())
                self.assertEqual(DARK[name].upper(), dark.upper())

    def test_no_old_dark_value_is_left_in_the_css(self):
        old = ("#141A17", "#1B231F", "#EFEDE4", "#2B3530", "#6D7771", "#F5803F")
        for path in (Path(settings.BASE_DIR) / "static" / "css").rglob("*.css"):
            if path.name == "styleguide.css":
                continue  # the before/after comparison keeps them on purpose
            text = path.read_text().upper()
            for value in old:
                with self.subTest(file=path.name, value=value):
                    self.assertNotIn(value, text)
