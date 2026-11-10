from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from .content import load_page


def landing(request):
    return render(request, "pages/landing.html")


# Shown on the styleguide. Values must match static/css/tokens.css.
STYLEGUIDE_TOKENS = [
    ("paper", "#F1F2EF", "#15171A", "Page background"),
    ("plate", "#FAFAF8", "#1F2226", "Raised surfaces, fields"),
    ("text", "#1E2126", "#E6E7E9", "Text"),
    ("steel", "#666C74", "#9AA0A8", "Secondary text"),
    ("line", "#D5D8DB", "#2E3237", "Dividers"),
    ("line-strong", "#868C93", "#6B7179", "Borders of controls"),
    ("ink", "#2A3FCF", "#8EA8F1", "Proof marks, links, focus, primary action"),
    ("danger", "#A8322D", "#F08A80", "Errors, destructive actions"),
]


def styleguide(request):
    """Every component in both themes. Development only: 404 when DEBUG is off."""
    if not settings.DEBUG:
        raise Http404
    tokens = [{"name": n, "light": light, "dark": dark, "use": use} for n, light, dark, use in STYLEGUIDE_TOKENS]
    return render(request, "pages/styleguide.html", {"themes": ["light", "dark"], "tokens": tokens})


def content_page(request, slug):
    page = load_page(slug)
    if page is None:
        raise Http404
    return render(request, "pages/content_page.html", {"page": page})
