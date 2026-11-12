"""The /feed/ page: which tab, which filters, which items. Ranking lives in social/ranking.py.

Everything comes from GET parameters, so every view of the feed is a link that works without JavaScript:
  tab    foryou (default) | following | news      ("latest" is the old name: For you, newest first)
  tag, tool, mark (authored | live | steady), range (24h | 7d | 30d | all), sort (popular | newest), page
Filters and sort belong to "For you". Following is chronological (projects and updates of people you follow) and
News lists official posts, so both ignore them.
"""
from datetime import timedelta
from urllib.parse import urlencode

from django import forms
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from news.models import NewsPost
from projects.models import Tag, Tool

from . import ranking
from .queries import FeedItem, MAX_PAGE, PAGE_SIZE, _event_at, project_cards, project_rows, published_projects, with_social
from verification.uptime import with_uptime

TABS = ("foryou", "following", "news")
RANGES = [("all", _("All time")), ("24h", _("Last 24 hours")), ("7d", _("Last 7 days")), ("30d", _("Last 30 days"))]
RANGE_DELTAS = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}
SORTS = [("popular", _("Popular")), ("newest", _("Newest"))]
MARKS = [("", _("Any")), ("authored", _("Repo owner")), ("live", _("Domain verified")), ("steady", _("Steady"))]
TAG_OPTIONS = 40


class FeedForm(forms.Form):
    """Validates the query string. A bad value is ignored (as if absent), never an error page."""

    tab = forms.CharField(required=False, max_length=10)
    tag = forms.CharField(required=False, max_length=40)
    tool = forms.CharField(required=False, max_length=40)
    mark = forms.ChoiceField(required=False, choices=MARKS)
    range = forms.ChoiceField(required=False, choices=RANGES)
    sort = forms.ChoiceField(required=False, choices=SORTS)
    page = forms.IntegerField(required=False, min_value=1)

    def values(self, user):
        self.is_valid()
        data = self.cleaned_data
        tab = data.get("tab") or "foryou"
        sort = data.get("sort") or ""
        if tab == "latest":  # the old name of the public list
            tab, sort = "foryou", sort or "newest"
        if tab not in TABS or (tab == "following" and not user.is_authenticated):
            tab = "foryou"
        return {
            "tab": tab, "tag": data.get("tag", ""), "tool": data.get("tool", ""), "mark": data.get("mark", ""),
            "range": data.get("range") or "all", "sort": sort or "popular", "page": data.get("page") or 1,
        }


def has_filters(params):
    return bool(params["tag"] or params["tool"] or params["mark"] or params["range"] != "all" or params["sort"] != "popular")


def feed_url(params, **changes):
    """/feed/?... with only the non-default parameters (so the plain feed is just /feed/)."""
    merged = {**params, **changes}
    query = {}
    if merged["tab"] != "foryou":
        query["tab"] = merged["tab"]
    if merged["tab"] == "foryou":
        for key, default in (("tag", ""), ("tool", ""), ("mark", ""), ("range", "all"), ("sort", "popular")):
            if merged[key] != default:
                query[key] = merged[key]
    if merged["page"] > 1:
        query["page"] = merged["page"]
    return reverse("social:feed") + (f"?{urlencode(query)}" if query else "")


def _since(params, now):
    delta = RANGE_DELTAS.get(params["range"])
    return now - delta if delta else None


def for_you(user, params, now=None):
    """(items, has_next) for the "For you" tab."""
    now = now or timezone.now()
    base = published_projects()
    if params["tag"]:
        base = base.filter(tags__slug=params["tag"])
    if params["tool"]:
        base = base.filter(built_with__slug=params["tool"])
    since = _since(params, now)
    newest = params["sort"] == "newest"
    order = ["-event_at", "-pk"] if newest else ["-score", "-event_at", "-pk"]
    start = (params["page"] - 1) * PAGE_SIZE
    kind = params["mark"]

    if kind:
        # Exact filter, as in Explore: the database narrows, compute_hallmarks decides. Only what it reads is loaded.
        light = with_social(with_uptime(
            base.defer("description").select_related("repo_link").prefetch_related("domain_verifications"), now,
        ), user).annotate(event_at=_event_at())
        if since:
            light = light.filter(event_at__gte=since)
        light = ranking.with_score(light, now)
        # Live and Steady both need a verified domain; the exact test below also checks the uptime and the host.
        light = light.filter(ranking.has_repo_mark() if kind == "authored" else ranking.has_live_mark(now))
        candidates = [p for p in light.order_by(*order) if p.hallmarks[kind].earned]
        ids = [p.pk for p in candidates[start:start + PAGE_SIZE]]
        rows = {p.pk: p for p in project_cards(published_projects().filter(pk__in=ids), user)}
        page = [rows[pk] for pk in ids if pk in rows]
        has_next = len(candidates) > start + PAGE_SIZE
    else:
        cards = project_cards(base, user)
        if since:
            cards = cards.filter(event_at__gte=since)
        if not newest:
            cards = ranking.with_score(cards, now)
        rows = list(cards.order_by(*order)[start:start + PAGE_SIZE + 1])
        page, has_next = rows[:PAGE_SIZE], len(rows) > PAGE_SIZE
    return [FeedItem("project", p, p.event_at) for p in page], has_next


def news_items(page):
    start = (page - 1) * PAGE_SIZE
    posts = list(NewsPost.objects.published().order_by("-pinned", "-published_at", "-pk")[start:start + PAGE_SIZE + 1])
    return [FeedItem("news", post, post.published_at) for post in posts[:PAGE_SIZE]], len(posts) > PAGE_SIZE


def latest_news(limit=3):
    return list(NewsPost.objects.published().order_by("-published_at", "-pk")[:limit])


def tag_options(selected=""):
    """Most used tags among visible projects (not suspended, not banned), plus the selected one."""
    tags = list(
        Tag.objects.filter(projects__in=published_projects().values("pk"))
        .annotate(n=Count("projects")).order_by("-n", "name")[:TAG_OPTIONS]
    )
    if selected and selected not in {t.slug for t in tags}:
        tags += list(Tag.objects.filter(slug=selected))
    return sorted(tags, key=lambda t: t.name.lower())


def tool_options():
    return list(Tool.objects.order_by("name"))
