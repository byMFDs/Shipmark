"""UI template tags: inline SVG, icons, avatars, hallmarks, site header and footer.

Load with {% load ui %}.
"""
import math
import re
from functools import lru_cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince
from django.utils.translation import get_language, gettext
from django.utils.translation import gettext_lazy as _

register = template.Library()


# ---------- Inline SVG ----------

# Removed when inlining: XML prolog, comments, <title>, and <style> (inline SVG styles
# would apply to the whole page).
_SVG_JUNK = re.compile(r"<\?xml.*?\?>|<!--.*?-->|<title\b.*?</title>|<style\b.*?</style>", re.S)
_ROOT_ATTRS = re.compile(r'\s(?:role|aria-label|aria-hidden|class)="[^"]*"')


def _read_svg(path):
    full_path = finders.find(path)
    if not full_path:
        raise ValueError(f"Static SVG not found: {path}")
    with open(full_path, encoding="utf-8") as fh:
        return _SVG_JUNK.sub("", fh.read()).strip()


_read_svg_cached = lru_cache(maxsize=128)(_read_svg)


@register.simple_tag
def inline_svg(path, css_class="", label=""):
    """Paste a static SVG file into the page so CSS can color it (e.g. the logo in the header).

    Paths come from templates and branding.py only, never from users.
    """
    svg = _read_svg(path) if settings.DEBUG else _read_svg_cached(path)
    head, sep, rest = svg.partition(">")
    head = _ROOT_ATTRS.sub("", head)
    if css_class:
        head += f' class="{escape(css_class)}"'
    if label:
        head += f' role="img" aria-label="{escape(label)}"'
    else:
        head += ' aria-hidden="true" focusable="false"'
    return mark_safe(head + sep + rest)


@register.simple_tag
def icon(name, css_class="", label=""):
    """An icon from static/icons/<name>.svg. Decorative unless a label is given."""
    return inline_svg(f"icons/{name}.svg", f"icon {css_class}".strip(), label)


# ---------- Relative dates ----------

@register.filter
def ago(value):
    """ "3 days ago", "just now": one unit only, localized. For <time> elements with the exact date nearby."""
    if not value:
        return ""
    now = timezone.now()
    if (now - value).total_seconds() < 60:  # also covers small clock differences into the future
        return gettext("just now")
    return gettext("%(time)s ago") % {"time": timesince(value, now, depth=1)}


# ---------- Avatar ----------

def initials(name):
    parts = [p for p in re.split(r"[\s_.-]+", str(name)) if p]
    letters = "".join(p[0] for p in parts[:2]) or "?"
    return letters.upper()


@register.simple_tag
def avatar(name, size=32, src=""):
    """A round avatar. Without `src` it shows initials.

    `src` must be a local URL: remote images would send visitors' IPs to another site.
    """
    size = int(size)
    if src:
        return format_html(
            '<img class="avatar avatar--{0}" src="{1}" alt="{2}" width="{0}" height="{0}" loading="lazy">',
            size, src, name,
        )
    return format_html(
        '<span class="avatar avatar--{0} avatar--initials" role="img" aria-label="{1}">{2}</span>',
        size, name, initials(name),
    )


# ---------- Hallmark ----------

HALLMARK_LABELS = {
    "authored": _("Authored"),
    "live": _("Live"),
    "steady": _("Steady"),
}

# Sizes of the {% hallmark %} chip (s: lists, m: default, l: project page with a fact).
# The cartouche geometry below is still used by the SVG badges (projects/badges.py).
HALLMARK_HEIGHTS = {"s": 16, "m": 24, "l": 40}
GLYPH_STROKE = {"s": 1.5, "m": 1.5, "l": 2}


def _n(value):
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _toward(x, y, tx, ty, dist):
    length = math.hypot(tx - x, ty - y)
    return x + (tx - x) * dist / length, y + (ty - y) * dist / length


def _cartouche(w, h, cut, soft, inset=0.0):
    """Rectangle with cut corners; every joint softened by a short curve."""
    a, b = inset, inset
    w, h = w - 2 * inset, h - 2 * inset
    pts = [(cut, 0), (w - cut, 0), (w, cut), (w, h - cut), (w - cut, h), (cut, h), (0, h - cut), (0, cut)]
    pts = [(x + a, y + b) for x, y in pts]
    out = []
    for i, (x, y) in enumerate(pts):
        start = _toward(x, y, *pts[i - 1], soft)
        end = _toward(x, y, *pts[(i + 1) % len(pts)], soft)
        out.append(f"{'L' if out else 'M'}{_n(start[0])} {_n(start[1])}Q{_n(x)} {_n(y)} {_n(end[0])} {_n(end[1])}")
    return "".join(out) + "Z"


def _circle(cx, cy, r):
    return f"M{_n(cx - r)} {_n(cy)}a{_n(r)} {_n(r)} 0 1 0 {_n(2 * r)} 0a{_n(r)} {_n(r)} 0 1 0 {_n(-2 * r)} 0Z"


def _rect(x0, y0, x1, y1):
    return f"M{_n(x0)} {_n(y0)}H{_n(x1)}V{_n(y1)}H{_n(x0)}Z"


def _glyph(kind, cx, cy, g, sw):
    """Glyph as filled outlines, so it can be cut out of the ink with fill-rule evenodd."""
    u, hs = g / 12, sw / 2
    if kind == "authored":  # commit node: a ring on a line
        r = 2.5 * u
        return (
            _circle(cx, cy, r + hs) + _circle(cx, cy, r - hs)
            + _rect(cx - 6 * u, cy - hs, cx - r - hs, cy + hs)
            + _rect(cx + r + hs, cy - hs, cx + 6 * u, cy + hs)
        )
    if kind == "live":  # a dot inside a ring
        r = 4.25 * u
        return _circle(cx, cy, r + hs) + _circle(cx, cy, r - hs) + _circle(cx, cy, 1.6 * u)
    # steady: three equal bars
    return "".join(_rect(cx + dx - hs, cy - 4 * u, cx + dx + hs, cy + 4 * u) for dx in (-3.5 * u, 0, 3.5 * u))


@lru_cache(maxsize=16)
def hallmark_geometry(kind, size):
    h = HALLMARK_HEIGHTS[size]
    w = h * 5 / 4
    cut = h / 5
    soft = min(2.0, cut * 0.3)
    shape = _cartouche(w, h, cut, soft)
    glyph = _glyph(kind, w / 2, h / 2, h * 0.6, GLYPH_STROKE[size])
    return {
        "w": _n(w),
        "vh": _n(h + 1),
        "solid": shape + glyph,
        "glyph": glyph,
        "outline": _cartouche(w, h, cut - 0.2, soft, inset=0.5),
        # Deboss: shadow along the inner top edge, light along the outer bottom edge.
        "shade": f"M0.6 {_n(cut + 0.4)}L{_n(cut + 0.4)} 0.6H{_n(w - cut - 0.4)}L{_n(w - 0.6)} {_n(cut + 0.4)}",
        "lip": f"M0.2 {_n(h - cut + 0.7)}L{_n(cut - 0.2)} {_n(h + 0.5)}H{_n(w - cut + 0.2)}L{_n(w - 0.2)} {_n(h - cut + 0.7)}",
    }


@register.inclusion_tag("includes/hallmark.html")
def hallmark(kind, size="m", earned=True, fact=""):
    """{% hallmark "authored" size="l" earned=True fact="Owner of org/repo" %}"""
    if kind not in HALLMARK_LABELS or size not in HALLMARK_HEIGHTS:
        raise ValueError(f"Unknown hallmark {kind!r} or size {size!r}")
    return {
        "kind": kind,
        "size": size,
        "earned": bool(earned),
        "label": HALLMARK_LABELS[kind],
        "fact": fact,
    }


# ---------- Site header and footer ----------

def _url(name, *args):
    """URL for a named route, or "" if the page does not exist yet."""
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return ""


@register.simple_tag(takes_context=True)
def absolute_url(context, url):
    """{% absolute_url cover.image.url %}: full URL for Open Graph. Already absolute URLs (a CDN) stay as they are."""
    request = context.get("request")
    return request.build_absolute_uri(url) if request else url


@register.simple_tag
def maybe_url(name, *args):
    """{% maybe_url "pages:legal" "terms" as terms_url %}: the URL, or "" if the page does not exist yet."""
    return _url(name, *args)


# Links appear by themselves once these URL names exist.
NAV_LINKS = [("social:feed", (), _("Feed")), ("pages:explore", (), _("Explore"))]
FOOTER_LINKS = [
    ("pages:about", (), _("About")),
    ("pages:how_proof_works", (), _("How proof works")),
    ("pages:legal", ("privacy",), _("Privacy")),
    ("pages:legal", ("terms",), _("Terms")),
    ("pages:legal", ("cookies",), _("Cookies")),
]

DEMO_USER = {"name": "Olena Marchenko", "username": "olena"}


@register.inclusion_tag("includes/site_header.html", takes_context=True)
def site_header(context, demo="", compact=False):
    """Header. `demo` ("signed-in" or "signed-out") fills every slot with sample links for the styleguide."""
    request = context.get("request")
    path = request.path if request else ""
    links = []
    for name, args, label in NAV_LINKS:
        url = "#" if demo else _url(name, *args)
        if url:
            links.append({"url": url, "label": label, "current": url != "#" and path.startswith(url)})
    if demo and links:
        links[0]["current"] = True

    user = context.get("user")
    if demo:
        signed_in = demo == "signed-in"
        me = DEMO_USER if signed_in else None
        profile_url = new_url = login_url = settings_url = logout_url = "#"
    else:
        signed_in = bool(user and user.is_authenticated)
        me = {"name": user.display_name or user.username, "username": user.username} if signed_in else None
        profile_url = _url("accounts:profile", user.username) if signed_in else ""
        new_url = _url("projects:new")
        login_url = _url("account_login")
        settings_url = _url("accounts:settings")
        logout_url = _url("account_logout")

    return {
        "brand": context.get("brand"),
        "home_url": reverse("pages:landing"),
        "links": links,
        "signed_in": signed_in,
        "me": me,
        "profile_url": profile_url,
        "new_url": new_url,
        "login_url": login_url,
        "settings_url": settings_url,
        "logout_url": logout_url,
        "has_menu": bool(links or signed_in or login_url),
        "compact": compact,
        "demo": bool(demo),
    }


@register.inclusion_tag("includes/site_footer.html", takes_context=True)
def site_footer(context, demo=False):
    request = context.get("request")
    links = []
    for name, args, label in FOOTER_LINKS:
        url = "#" if demo else _url(name, *args)
        if url:
            links.append({"url": url, "label": label})
    brand = context.get("brand")
    return {
        "brand": brand,
        "home_url": "#" if demo else reverse("pages:landing"),
        "links": links,
        "social_links": getattr(brand, "SOCIAL_LINKS", {}),
        "set_language_url": "#" if demo else _url("set_language"),
        "languages": settings.LANGUAGES,
        "current_language": get_language(),
        "next_url": request.get_full_path() if request else "/",
        "csrf_token": context.get("csrf_token"),
        "year": timezone.now().year,
        "demo": demo,
    }
