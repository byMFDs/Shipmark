from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render

from projects.models import Tool
from projects.proof import RULES
from social.queries import project_rows, published_projects

from .content import load_page
from .explore import HALLMARK_CHOICES, SORTS, ExploreForm, explore, tag_options

RECENT_ON_LANDING = 6


def landing(request):
    """Signed-out visitors only: people with an account go straight to their feed."""
    if request.user.is_authenticated:
        return redirect("social:feed")
    recent = list(project_rows(published_projects(), request.user).order_by("-event_at", "-pk")[:RECENT_ON_LANDING])
    proof = [{"kind": kind, "rule": RULES[kind]} for kind in ("authored", "live", "steady")]
    return render(request, "pages/landing.html", {
        "recent": recent, "proof": proof, "github_configured": settings.GITHUB_OAUTH_CONFIGURED,
    })


def explore_view(request):
    params = ExploreForm(request.GET).values()
    result = explore(params, request.user)
    if params["page"] > 1 and not result["projects"]:
        raise Http404  # past the last page
    return render(request, "pages/explore.html", {
        **result,
        "params": params,
        "prev_page": params["page"] - 1 if params["page"] > 2 else None,  # page 1 has no "page" parameter
        "next_page": params["page"] + 1,
        "filtered": any(params[k] for k in ("q", "tag", "tool", "hallmark")),
        "tags": tag_options(params["tag"]),
        "tools": Tool.objects.all(),
        "hallmarks": HALLMARK_CHOICES,
        "sorts": SORTS,
    })


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


LEGAL_PAGES = ("privacy", "terms", "cookies")


def legal_page(request, slug):
    """/legal/privacy/, /legal/terms/, /legal/cookies/. Only these: other content pages have their own URLs."""
    if slug not in LEGAL_PAGES:
        raise Http404
    return content_page(request, slug)
