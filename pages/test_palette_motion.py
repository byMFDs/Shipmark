"""Palette/motion contracts checked against the shipped styles, without a browser."""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from pages.test_halo import contrast
from pages.test_motion import css_files, keyframes, rules, without_comments


def media_blocks(text, condition):
    """Read complete nested media blocks, rather than stopping at the first rule."""
    for match in re.finditer(r"@media\s*\(" + re.escape(condition) + r"\)\s*\{", text):
        depth, end = 1, match.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(text[end], 0)
            end += 1
        yield text[match.end():end - 1]


class PaletteMotionTests(SimpleTestCase):
    def test_every_animation_selector_has_a_reduced_motion_override(self):
        css = Path(settings.BASE_DIR) / "static/css"
        base = without_comments((css / "base.css").read_text())
        reduced = list(media_blocks(base, "prefers-reduced-motion: reduce"))
        self.assertTrue(reduced)
        resets = dict(rules("\n".join(reduced)))
        universal = next(body for selector, body in resets.items()
                         if set(selector.split(", ")) == {"*", "*::before", "*::after"})
        # This selector covers each class, state and pseudo-element using animation.
        for path in css_files():
            for selector, body in rules(without_comments(path.read_text())):
                if re.search(r"\banimation\s*:\s*(?!none\b)", body):
                    with self.subTest(file=path.name, selector=selector):
                        self.assertIn("animation: none !important", universal)
                        self.assertIn("transition: none !important", universal)

    def test_new_animation_classes_explicitly_define_the_static_state(self):
        css = Path(settings.BASE_DIR) / "static/css"
        expected = {
            "motion.css": (".strike .hallmark__chip", ".tick-strip__cell", ".uptime-strip__day",
                           ".motion-reveal", ".motion-child", "html.motion-arrival body::before",
                           "html.motion-arrival .site-main", ".log-entry--launch.motion-node-seen::before"),
            "components.css": (".motion-shimmer::before", ".btn--halo::before",
                               ".btn[data-busy-ring]::after"),
        }
        for file, selectors in expected.items():
            blocks = "\n".join(media_blocks(without_comments((css / file).read_text()),
                                            "prefers-reduced-motion: reduce"))
            for selector in selectors:
                with self.subTest(file=file, selector=selector):
                    matching = [body for group, body in rules(blocks) if selector in group.split(", ")]
                    self.assertTrue(matching, "missing class-specific reduced-motion fallback")
                    self.assertIn("animation: none !important", " ".join(matching))

    def test_keyframes_and_transitions_use_only_compositor_properties(self):
        allowed = {"transform", "opacity", "clip-path"}
        for path in css_files():
            text = without_comments(path.read_text())
            for name, body in keyframes(text):
                with self.subTest(file=path.name, animation=name):
                    self.assertLessEqual(set(re.findall(r"([\w-]+)\s*:", body)), allowed)
            for body in re.findall(r"\btransition(?:-property)?\s*:\s*([^;{}]+);", text):
                parts = re.split(r",\s*(?![^()]*\))", body)
                with self.subTest(file=path.name, transition=body):
                    self.assertLessEqual({part.strip().split()[0] for part in parts}, allowed | {"none"})

    def test_documented_text_pairs_match_the_measured_aa_ratios(self):
        report = (Path(settings.BASE_DIR) / "docs/PALETTE.md").read_text()
        pairs = re.findall(
            r"\| (light|dark) \| [^|]+ \| (#[0-9A-F]{6}) \| [^|]+ \| (#[0-9A-F]{6}) \| (\d+\.\d+):1 \|",
            report,
        )
        self.assertGreaterEqual(len(pairs), 82)
        for theme, foreground, background, measured in pairs:
            with self.subTest(theme=theme, foreground=foreground, background=background):
                actual = contrast(foreground, background)
                self.assertGreaterEqual(actual, 4.5)
                self.assertAlmostEqual(actual, float(measured), delta=0.005)
