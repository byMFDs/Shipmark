"""Загальні сторінки: лендинг, Discover, styleguide, контент і юридичні сторінки."""
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render

from accounts import people
from projects.models import Tool
from projects.proof import RULES
from social.queries import project_rows, published_projects

from .content import load_page
from .explore import HALLMARK_CHOICES, SORTS, ExploreForm, explore, tag_options

RECENT_ON_LANDING = 6


def landing(request):
    """Лендинг для гостей; з акаунтом — одразу в стрічку.

    Signed-out visitors only: people with an account go straight to their feed."""
    if request.user.is_authenticated:
        return redirect("social:feed")
    recent = list(project_rows(published_projects(), request.user).order_by("-event_at", "-pk")[:RECENT_ON_LANDING])
    proof = [{"kind": kind, "rule": RULES[kind]} for kind in ("authored", "live", "steady")]
    return render(request, "pages/landing.html", {
        "recent": recent, "proof": proof, "github_configured": settings.GITHUB_OAUTH_CONFIGURED,
    })


def explore_view(request):
    """Discover з вкладками Projects і People.

    Discover: two tabs on one page. Projects (default, unchanged) and People (?tab=people)."""
    if request.GET.get("tab") == "people":
        return people_view(request)
    params = ExploreForm(request.GET).values()
    result = explore(params, request.user)
    if params["page"] > 1 and not result["projects"]:
        raise Http404  # past the last page
    return render(request, "pages/explore.html", {
        **result,
        "tab": "projects",
        "params": params,
        "prev_page": params["page"] - 1 if params["page"] > 2 else None,  # page 1 has no "page" parameter
        "next_page": params["page"] + 1,
        "filtered": any(params[k] for k in ("q", "tag", "tool", "hallmark")),
        "tags": tag_options(params["tag"]),
        "tools": Tool.objects.all(),
        "hallmarks": HALLMARK_CHOICES,
        "sorts": SORTS,
    })


MAX_PEOPLE_PAGE = 50


def people_view(request):
    """Discover → People: пошук за іменем користувача.

    Discover → People: username search (accounts/people.py has the rules)."""
    raw = request.GET.get("q", "")
    query = people.clean_query(raw)
    try:
        page = min(max(int(request.GET.get("page", 1)), 1), MAX_PEOPLE_PAGE)
    except ValueError:
        page = 1
    context = {"tab": "people", "q": raw.strip()[:100], "query": query, "page": page, "results": [],
               "has_next": False, "problem": people.query_problem(query) if query else "", "limited": False,
               "min_length": people.MIN_LENGTH}
    status = 200
    if query and not context["problem"]:
        if people.search_limited(request):
            context["limited"], status = True, 429
        else:
            results, has_next = people.search(query, page)
            if page > 1 and not results:
                raise Http404  # past the last page
            context.update(results=people.attach_counts(results, request.user), has_next=has_next,
                           prev_page=page - 1 if page > 2 else None, next_page=page + 1)
    return render(request, "pages/explore.html", context, status=status)


# Shown on the styleguide. Values must match static/css/tokens.css.
STYLEGUIDE_TOKENS = [
    ("paper", "#F4F3EE", "#121815", "Page background"),
    ("surface", "#FFFEFA", "#1C2521", "Records, cards, panels"),
    ("raised", "#FFFEFA", "#242E29", "Fields, menus, popovers, toasts"),
    ("text", "#20251F", "#ECEAE1", "Text, focus ring"),
    ("muted", "#5C635B", "#A7AFA6", "Secondary text"),
    ("line", "#D9D8D0", "#35413B", "Hairlines, frames"),
    ("line-strong", "#868A80", "#76817A", "Borders of controls (3:1)"),
    ("accent", "#BD4B27", "#EE7A3B", "The one primary action (dark: dark text on it)"),
    ("accent-text", "#AE411D", "#EE936E", "Eyebrows, numbers"),
    ("proof-bg", "#E3EBDA", "#233A2C", "Earned marks, proof notes"),
    ("proof", "#2B5A3F", "#ADD5B8", "Text on proof"),
    ("band-bg", "#212721", "#0D1310", "Dark statement strips"),
    ("danger", "#A8322D", "#F2918A", "Errors, destructive actions"),
]


def styleguide(request):
    """Усі компоненти в обох темах (лише з DEBUG).

    Every component in both themes. Development only: 404 when DEBUG is off."""
    if not settings.DEBUG:
        raise Http404
    from community.stickers import STICKERS

    tokens = [{"name": n, "light": light, "dark": dark, "use": use} for n, light, dark, use in STYLEGUIDE_TOKENS]
    stickers = [{"key": key, "label": label, "file": f"stickers/{key}.svg"} for key, label in STICKERS.items()]
    return render(request, "pages/styleguide.html", {"themes": ["light", "dark"], "tokens": tokens, "stickers": stickers})


def content_page(request, slug):
    """Markdown-сторінка за slug або 404."""
    page = load_page(slug)
    if page is None:
        raise Http404
    return render(request, "pages/content_page.html", {"page": page})


LEGAL_PAGES = ("privacy", "terms", "cookies")


def legal_page(request, slug):
    """Юридичні сторінки: privacy, terms, cookies.

    /legal/privacy/, /legal/terms/, /legal/cookies/. Only these: other content pages have their own URLs."""
    if slug not in LEGAL_PAGES:
        raise Http404
    return content_page(request, slug)
