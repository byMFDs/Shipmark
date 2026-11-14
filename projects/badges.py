"""SVG-бейджі для README і сайтів.

Embeddable SVG badges (README / site badges).

Pure functions that return an SVG string. Nothing here touches the request, the session or
the database: the views load the data and pass it in.

Rules for the SVG:
- No external fonts. The system font stack is set on the root element.
- Fixed colors (a badge sits on any page, so it cannot use the site's CSS variables). It has its
  own dark and light halves and a border, so it reads on light and dark READMEs alike.
- Text widths are estimated (no font is available on the server), then `textLength` forces the
  estimate, so the layout never overlaps, whatever font the viewer's system picks.
"""
import re
import unicodedata
from functools import lru_cache

from django.contrib.staticfiles import finders
from django.utils.html import escape

from config import branding
from pages.templatetags.ui import hallmark_geometry

HEIGHT = 28
PAD = 10
GAP = 8
MARK_SIZE = 14
FONT_SIZE = 12
MAX_NAME_WIDTH = 170  # px; longer names are cut with an ellipsis
FONT_STACK = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"

# Design tokens from static/css/tokens.css (light values, the badge is the same everywhere).
# Green is proof only, so it is the color of the stamps; the badge has no accent.
GRAPHITE = "#20251F"
PLATE = "#FFFEFA"
STEEL = "#5C635B"
LINE = "#868A80"
INK = "#2B5A3F"

HALLMARK_ORDER = ("authored", "live", "steady")
HALLMARK_LABELS = {"authored": "Repo owner", "live": "Domain verified", "steady": "Steady"}  # English only, see docs

# Control characters break XML; bidi controls and zero-width characters could fake the text.
_UNSAFE = re.compile("[\x00-\x1f\x7f-\x9f​-‏‪-‮⁦-⁩﻿￾￿]")


def _n(value):
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def clean_text(text):
    text = unicodedata.normalize("NFC", _UNSAFE.sub("", str(text))).strip()
    return re.sub(r"\s+", " ", text)


# ---------- Text width ----------

_NARROW = set("il.,:;|'!1jIft()[]-/\\` ")
_WIDE = set("mwMW@%")


def _char_em(ch):
    """Ширина символу в em для оцінки довжини тексту."""
    if ch in _NARROW:
        return 0.32
    if ch in _WIDE:
        return 0.92
    if ord(ch) >= 0x2E80:  # CJK and friends
        return 1.0
    if ch.isdigit():
        return 0.6
    if ch.isupper():
        return 0.68
    return 0.57


def text_width(text, size=FONT_SIZE, bold=False):
    return sum(_char_em(ch) for ch in text) * size * (1.06 if bold else 1.0)


def fit_text(text, max_width, bold=False):
    """Обрізає текст з трикрапкою, якщо він задовгий.

    Cut `text` with an ellipsis when it would be wider than `max_width`."""
    if text_width(text, bold=bold) <= max_width:
        return text
    room = max_width - text_width("…", bold=bold)
    out = ""
    for ch in text:
        if text_width(out + ch, bold=bold) > room:
            break
        out += ch
    return out.rstrip() + "…"


# ---------- Site mark ----------

@lru_cache(maxsize=1)
def _site_mark():
    """Знак сайту з файлу logo-mark для бейджа.

    (viewBox size, path data) read from the logo-mark file, so replacing the file rebrands the badge."""
    try:
        with open(finders.find(branding.LOGO_MARK), encoding="utf-8") as fh:
            source = fh.read()
        box = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', source)
        paths = re.findall(r'<path\b[^>]*?\bd="([^"]+)"', source)
        if box and paths and box.group(1) == box.group(2):
            return float(box.group(1)), " ".join(paths)
    except (TypeError, OSError):
        pass
    return 16.0, "M0 0H16V16H0Z"  # plain square: a missing or odd logo must not break badges


# ---------- Layout ----------

class _Badge:
    """Збирає частини SVG зліва направо.

    Collects SVG pieces left to right. Call `finish()` for the document."""

    def __init__(self, title):
        self.title = title
        self.parts = []
        self.x = 0.0
        self.halves = []  # (x, width, fill): backgrounds, drawn first

    def background(self, width, fill):
        self.halves.append((self.x, width, fill))

    def text(self, x, text, fill, bold=False):
        """Додає текстовий блок."""
        width = text_width(text, bold=bold)
        self.parts.append(
            f'<text x="{_n(x)}" y="18" fill="{fill}" font-weight="{600 if bold else 500}" '
            f'textLength="{_n(width)}" lengthAdjust="spacingAndGlyphs">{escape(text)}</text>'
        )
        return width

    def site_half(self):
        """Темна ліва половина: знак і назва сайту.

        Dark left half: site mark and the site name."""
        size, path = _site_mark()
        name = clean_text(branding.SITE_NAME)
        scale = MARK_SIZE / size
        self.parts.append(f'<path transform="translate({PAD} {_n((HEIGHT - MARK_SIZE) / 2)}) scale({_n(scale)})" '
                          f'fill="{PLATE}" fill-rule="evenodd" d="{escape(path)}"/>')
        text_x = PAD + MARK_SIZE + 6
        width = text_width(name, bold=True)
        self.background(text_x + width + PAD, GRAPHITE)
        self.text(text_x, name, PLATE, bold=True)
        self.x = text_x + width + PAD

    def finish(self):
        """Готовий SVG-документ."""
        total = _n(self.x)
        backgrounds = "".join(
            f'<rect x="{_n(x)}" width="{_n(w)}" height="{HEIGHT}" fill="{fill}"/>' for x, w, fill in self.halves
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{HEIGHT}" viewBox="0 0 {total} {HEIGHT}" '
            f'role="img" aria-label="{escape(self.title)}" font-family="{FONT_STACK}" font-size="{FONT_SIZE}">'
            f'<title>{escape(self.title)}</title>'
            f'<clipPath id="r"><rect width="{total}" height="{HEIGHT}"/></clipPath>'
            f'<g clip-path="url(#r)"><rect width="{total}" height="{HEIGHT}" fill="{PLATE}"/>{backgrounds}{"".join(self.parts)}</g>'
            f'<rect x=".5" y=".5" width="{_n(self.x - 1)}" height="{HEIGHT - 1}" fill="none" stroke="{LINE}"/>'
            '</svg>\n'
        )


def _plural(count, one, many):
    return f"{count} {one if count == 1 else many}"


def project_badge(name, earned_kinds):
    """Бейдж проєкту: назва й зароблені марки.

    Badge for one project: site mark, project name, one stamp per earned hallmark."""
    name = clean_text(name) or "Project"
    earned = [kind for kind in HALLMARK_ORDER if kind in earned_kinds]
    site = clean_text(branding.SITE_NAME)
    if earned:
        title = f"{site}: {name}, " + ", ".join(HALLMARK_LABELS[k] for k in earned)
    else:
        title = f"{site}: {name}, no hallmarks yet"
    badge = _Badge(title)
    badge.site_half()
    x = badge.x + PAD
    shown = fit_text(name, MAX_NAME_WIDTH, bold=True)
    x += badge.text(x, shown, GRAPHITE, bold=True) + GAP
    if earned:
        for kind in earned:
            geo = hallmark_geometry(kind, "s")
            badge.parts.append(
                f'<path transform="translate({_n(x)} {_n((HEIGHT - 16) / 2)})" fill="{INK}" fill-rule="evenodd" d="{geo["solid"]}"/>'
            )
            x += float(geo["w"]) + 4
        x -= 4
    else:
        x += badge.text(x, "no hallmarks yet", STEEL)
    badge.x = x + PAD
    return badge.finish()


def profile_badge(username, hallmark_count):
    """Бейдж профілю: @ім'я й кількість марок.

    Badge for a profile: site mark, @username, number of hallmarks over published projects."""
    username = clean_text(username)
    site = clean_text(branding.SITE_NAME)
    count_text = _plural(hallmark_count, "hallmark", "hallmarks")
    badge = _Badge(f"{site}: @{username}, {count_text}")
    badge.site_half()
    x = badge.x + PAD
    x += badge.text(x, fit_text(f"@{username}", MAX_NAME_WIDTH, bold=True), GRAPHITE, bold=True) + PAD
    width = text_width(count_text, bold=True)
    badge.halves.append((x, width + 2 * PAD, INK))
    badge.text(x + PAD, count_text, "#FFFFFF", bold=True)
    badge.x = x + width + 2 * PAD
    return badge.finish()


def not_found_badge():
    """Нейтральний бейдж, який не каже, чому проєкту не видно.

    Neutral badge for unknown, draft, hidden and suspended alike: it says nothing about which."""
    badge = _Badge(f"{clean_text(branding.SITE_NAME)}: not found")
    badge.site_half()
    x = badge.x + PAD
    x += badge.text(x, "not found", STEEL)
    badge.x = x + PAD
    return badge.finish()


# ---------- Embed snippets ----------

def embed_snippets(person, project=None):
    """Markdown і HTML для вставки бейджа.

    Markdown and HTML snippets plus the badge URL, for the "Embed badge" panel.

    Absolute URLs come from settings.SITE_URL (config/site.py), never from the request's host, so a snippet copied
    on localhost or a preview server still points to the real site. `badge_path` is for the preview on our own page.
    """
    from django.urls import reverse

    from config.site import absolute_url
    site = clean_text(branding.SITE_NAME)
    if project is None:
        badge_path = reverse("projects:badge_profile", args=[person.username])
        page_path = reverse("accounts:profile", args=[person.username])
        alt = f"{site}: @{person.username}"
    else:
        badge_path = reverse("projects:badge_project", args=[person.username, project.slug])
        page_path = project.get_absolute_url()
        alt = f"{site}: {clean_text(project.name)}"
    badge_url = absolute_url(badge_path)
    page_url = absolute_url(page_path)
    md_alt = re.sub(r"[\[\]\\]", "", alt)  # brackets would end the Markdown image text early
    return {
        "badge_url": badge_url,
        "badge_path": badge_path,
        "alt": alt,
        "markdown": f"[![{md_alt}]({badge_url})]({page_url})",
        "html": f'<a href="{escape(page_url)}"><img src="{escape(badge_url)}" alt="{escape(alt)}" height="{HEIGHT}"></a>',
    }
