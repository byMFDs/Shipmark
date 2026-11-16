"""Загальні сторінки: лендинг, Discover, styleguide, контент і юридичні сторінки."""
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render

from accounts import people
from projects.models import Tool
from projects.proof import RULES
from social.queries import project_rows, published_projects
from verification.uptime import Day, Summary

from .content import load_page
from .explore import HALLMARK_CHOICES, SORTS, ExploreForm, explore, tag_options

RECENT_ON_LANDING = 6


def example_uptime():
    """Вигадані дані аптайму для прикладу на лендингу.

    Example data for the illustrative project on the landing page only (it is labelled "Example data" there).
    Never used for a real project: real pages read UptimeCheck rows through uptime_summary()."""
    days = [Day(None, total=8, ok=8) for _ in range(30)]
    days[0], days[1] = Day(None), Day(None)   # no data yet: shows the empty bar
    days[18] = Day(None, total=8, ok=7)       # one day with a failed check
    return Summary(ok=sum(d.ok for d in days), total=sum(d.total for d in days), last_checked_at=None, days=days)


def landing(request):
    """Лендинг для гостей; з акаунтом — одразу в стрічку.

    Signed-out visitors only: people with an account go straight to their feed."""
    if request.user.is_authenticated:
        return redirect("social:feed")
    recent = list(project_rows(published_projects(), request.user).order_by("-event_at", "-pk")[:RECENT_ON_LANDING])
    proof = [{"kind": kind, "rule": RULES[kind]} for kind in ("authored", "live", "steady")]
    return render(request, "pages/landing.html", {
        "recent": recent, "proof": proof, "github_configured": settings.GITHUB_OAUTH_CONFIGURED,
        "example_uptime": example_uptime(),
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
    ("paper", "#F3F6F7", "#071C1E", "Page background"),
    ("surface", "#F3F6F7", "#15292B", "Records, cards, panels"),
    ("raised", "#F3F6F7", "#233638", "Fields, menus, popovers, toasts"),
    ("text", "#071C1E", "#F3F6F7", "Text, focus ring"),
    ("muted", "#20383A", "#B1B9BA", "Secondary text"),
    ("line", "#20383A", "#4E6264", "Hairlines, frames"),
    ("line-strong", "#6A7A7C", "#7F8E8F", "Borders of controls (3:1)"),
    ("accent", "#C7F36B", "#C7F36B", "The one primary action (dark: dark text on it)"),
    ("accent-text", "#20383A", "#79D9D2", "Eyebrows, numbers"),
    ("proof-bg", "#C7F36B", "#C7F36B", "Earned marks, proof notes"),
    ("proof", "#071C1E", "#071C1E", "Text on proof"),
    ("band-bg", "#071C1E", "#071C1E", "Dark statement strips"),
    ("danger", "#20383A", "#79D9D2", "Errors, destructive actions"),
]


def styleguide(request):
    """Усі компоненти в обох темах (лише з DEBUG).

    Every component in both themes. Development only: 404 when DEBUG is off."""
    if not settings.DEBUG:
        raise Http404

    tokens = [{"name": n, "light": light, "dark": dark, "use": use} for n, light, dark, use in STYLEGUIDE_TOKENS]
    return render(request, "pages/styleguide.html", {"themes": ["light", "dark"], "tokens": tokens,
                                                          "example_uptime": example_uptime()})


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
