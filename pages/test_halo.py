"""The halo ring on the main buttons (POLISH3 stage 2): visible on both themes, >= 3:1 against the page.

Reads the real colours from static/css/tokens.css, so a token change that makes the ring too faint fails here.
"""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

CSS = Path(settings.BASE_DIR) / "static" / "css"


def block(text, selector_start):
    """The declarations of the first rule whose selector list starts with `selector_start`."""
    start = text.index(selector_start)
    return text[text.index("{", start) + 1:text.index("}", start)]


def tokens(declarations):
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})\s*;", declarations))


def luminance(hex_colour):
    channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def mix(a, b, t):
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))


class HaloTests(SimpleTestCase):
    def setUp(self):
        text = (CSS / "tokens.css").read_text()
        self.themes = {
            "light": tokens(block(text, ":root,\n[data-theme=\"light\"]")),
            "dark": tokens(block(text, "[data-theme=\"dark\"],\n.band")),
        }
        self.components = (CSS / "components.css").read_text()

    def ring(self, t, kind):
        """The stops of the running light (components.css .btn--halo) and every 10% blend between them."""
        if kind == "primary":
            stops = [t["accent"], t["text"], t["accent-hover"], t["text"], t["accent"]]
        else:
            stops = [t["line-strong"], t["text"], t["accent"], t["text"], t["line-strong"]]
        return [mix(a, b, k / 10) for a, b in zip(stops, stops[1:]) for k in range(11)]

    def test_every_colour_on_the_ring_is_at_least_3_to_1_on_page_and_surface(self):
        for theme, t in self.themes.items():
            for kind in ("secondary", "primary"):
                for background in ("paper", "surface"):
                    with self.subTest(theme=theme, button=kind, background=background):
                        worst = min(contrast(c, t[background]) for c in self.ring(t, kind))
                        self.assertGreaterEqual(worst, 3.0)

    def test_the_light_stands_out_from_the_resting_ring(self):
        """The bug: on the light theme hover turned the whole ring ink, so the ink light could not be seen."""
        for theme, t in self.themes.items():
            with self.subTest(theme=theme):
                self.assertGreaterEqual(contrast(t["text"], t["line-strong"]), 3.0)

    def test_the_css_uses_these_colours_and_keeps_the_ring_on_hover(self):
        halo = block(self.components, ".btn--halo {")
        self.assertIn("background: var(--halo-base)", halo)
        self.assertIn("--halo-base: var(--line-strong)", halo)
        self.assertIn("--halo-light: var(--text)", halo)
        self.assertIn("--halo-spark: var(--accent)", halo)
        primary = block(self.components, ".btn--halo.btn--primary {")
        self.assertIn("--halo-base: var(--accent)", primary)
        self.assertIn("--halo-spark: var(--accent-hover)", primary)
        gradient = block(self.components, ".btn--halo::before {")
        self.assertNotIn("transparent", gradient)  # would show the page through the ring
        self.assertNotIn("--paper", gradient)  # paper on a paper page is invisible
