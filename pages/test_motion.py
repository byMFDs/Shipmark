"""Motion rules (POLISH3 stage 4, docs/DESIGN.md "Motion"), read from the real CSS files.

Keyframes move only transform and opacity; page transitions exist only when motion is welcome; an endless animation
runs only inside a [data-loop] block (which pauses offscreen and in hidden tabs) or as an answer to the person
(a hovered, focused or busy button). Reduced motion switches everything off in base.css.
"""
import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

CSS = Path(settings.BASE_DIR) / "static" / "css"

# Endless animations that are answers, not ambient loops: the halo while hovered / focused / busy, the busy spinner.
ANSWER_LOOPS = (":hover", ":focus-visible", "aria-busy", "data-busy-ring")


def css_files():
    return sorted([*CSS.glob("*.css"), *CSS.glob("pages/*.css")])


def without_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def keyframes(text):
    """(name, body) of every @keyframes block (bodies hold one level of nested braces)."""
    for match in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", text):
        depth, i = 1, match.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        yield match.group(1), text[match.end():i - 1]


def rules(text):
    """(selector, declarations) of every innermost rule."""
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
        yield " ".join(selector.split()), body


class MotionRuleTests(TestCase):
    """Правила анімацій у CSS."""
    def test_keyframes_move_only_transform_and_opacity(self):
        for path in css_files():
            for name, body in keyframes(without_comments(path.read_text())):
                properties = set(re.findall(r"([\w-]+)\s*:", body))
                with self.subTest(file=path.name, keyframes=name):
                    self.assertTrue(properties, "empty keyframes")
                    self.assertLessEqual(properties, {"transform", "opacity"})

    def test_page_transitions_only_when_motion_is_welcome(self):
        text = without_comments((CSS / "motion.css").read_text())
        self.assertEqual(text.count("@view-transition"), 1)
        self.assertRegex(text, r"@media \(prefers-reduced-motion: no-preference\) \{\s*@view-transition \{ navigation: auto; \}")
        # The tab-mark names live in the same kind of block, so reduced motion never morphs anything.
        start = text.index("view-transition-name: nav-mark")
        self.assertIn("prefers-reduced-motion: no-preference", text[text.rindex("@media", 0, start):start])
        for path in css_files():
            if path.name in ("motion.css", "components.css"):
                continue  # components.css names only the header (kept still); checked by the regex below
            self.assertNotIn("view-transition-name", path.read_text(), path.name)
        self.assertEqual(re.findall(r"view-transition-name:\s*([\w-]+)", (CSS / "components.css").read_text()), ["site-header"])

    def test_endless_animations_are_loops_or_answers(self):
        for path in css_files():
            for selector, body in rules(without_comments(path.read_text())):
                if not re.search(r"animation[\w-]*:[^;]*\binfinite\b", body):
                    continue
                with self.subTest(file=path.name, selector=selector):
                    for part in selector.split(","):
                        self.assertTrue("[data-loop]" in part or any(a in part for a in ANSWER_LOOPS), part)

    def test_reduced_motion_switches_everything_off(self):
        base = without_comments((CSS / "base.css").read_text())
        block = base[base.index("@media (prefers-reduced-motion: reduce)"):]
        self.assertIn("animation: none !important", block)
        self.assertIn("transition: none !important", block)

    def test_reading_progress_is_hidden_unless_supported(self):
        text = without_comments((CSS / "motion.css").read_text())
        self.assertIn(".read-progress { display: none; }", text)
        self.assertIn("@supports (animation-timeline: scroll())", text)


class TabMarkTests(TestCase):
    """Позначка поточної вкладки.

    The current tab carries one .tab-mark (the element a view transition slides); the others carry none."""

    def tab_row(self, html, nav_class):
        start = html.index(f'<nav class="tabs {nav_class}"')
        return html[start:html.index("</nav>", start)]

    def test_discover_tabs(self):
        for query, current in (("", "Projects"), ("?tab=people", "People")):
            row = self.tab_row(self.client.get(reverse("pages:explore") + query).content.decode(), "explore-tabs")
            self.assertEqual(row.count('class="tab-mark"'), 1)
            self.assertRegex(row, rf'aria-current="page">{current}<span class="tab-mark"')

    def test_only_the_first_tab_is_flush_left(self):
        """Each tab link is the only child of its <li>: `.tabs__link:first-child` matched every tab."""
        css = without_comments((CSS / "components.css").read_text())
        self.assertNotIn(".tabs__link:first-child", css)
        self.assertIn(".tabs__list > li:first-child .tabs__link { padding-left: 0; }", css)

    def test_header_nav_marks_the_current_page(self):
        html = self.client.get(reverse("pages:explore")).content.decode()
        self.assertRegex(html, r'class="site-nav__link"[^>]*aria-current="page">[^<]+<span class="tab-mark" aria-hidden="true">')
