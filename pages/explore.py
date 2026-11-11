"""Explore: search, filters and sorting. Everything comes from GET parameters, so a URL is a shareable view.

Hallmarks are never stored (CLAUDE.md section 2), so the hallmark filter and the "Most proven"
sort use compute_hallmarks() itself instead of a second copy of the rules in SQL:
1. the database narrows the candidates (search, tag, tool, and a cheap superset check for the mark);
2. the exact marks are computed in Python for the candidates (a fixed number of queries);
3. only the requested page is loaded in full.
At MVP scale this is fast. If published projects grow into many thousands, cache a score column.
"""
from datetime import timedelta

from django import forms
from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from projects.models import Tag, Tool
from social.queries import project_rows, published_projects, with_social
from verification.domain import LIVE_MAX_AGE
from verification.models import DomainVerification
from verification.uptime import with_uptime

PAGE_SIZE = 24
MAX_PAGE = 200
TAG_OPTIONS = 40  # most used tags offered in the filter

SORTS = [("newest", _("Newest")), ("liked", _("Most liked")), ("proven", _("Most proven"))]
HALLMARK_CHOICES = [("", _("Any")), ("authored", _("Repo owner")), ("live", _("Live")), ("steady", _("Steady"))]


class ExploreForm(forms.Form):
    """Validates the query string. An invalid value is ignored (as if it were not given), never an error page."""

    q = forms.CharField(required=False, max_length=100, strip=True)
    tag = forms.CharField(required=False, max_length=40)
    tool = forms.CharField(required=False, max_length=40)
    hallmark = forms.ChoiceField(required=False, choices=HALLMARK_CHOICES)
    sort = forms.ChoiceField(required=False, choices=SORTS)
    page = forms.IntegerField(required=False, min_value=1, max_value=MAX_PAGE)

    def values(self):
        self.is_valid()
        data = self.cleaned_data
        return {
            "q": " ".join(data.get("q", "").split()),
            "tag": data.get("tag", ""),
            "tool": data.get("tool", ""),
            "hallmark": data.get("hallmark", ""),
            "sort": data.get("sort") or "newest",
            "page": data.get("page") or 1,
        }


def tag_options(selected=""):
    """Most used tags among visible projects, plus the selected one if it is not among them."""
    visible = Q(projects__status="published", projects__owner__is_suspended=False)
    tags = list(Tag.objects.filter(visible).annotate(n=Count("projects")).order_by("-n", "name")[:TAG_OPTIONS])
    if selected and selected not in {t.slug for t in tags}:
        tags += list(Tag.objects.filter(slug=selected))
    return sorted(tags, key=lambda t: t.name.lower())


def _may_have(queryset, kind, now):
    """A cheap superset of the projects that can hold `kind`. The exact check is compute_hallmarks()."""
    if kind == "authored":
        return queryset.exclude(repo_full_name="").filter(repo_link__isnull=False)
    verified = DomainVerification.objects.filter(
        project=OuterRef("pk"), status=DomainVerification.Status.VERIFIED,
        last_confirmed_at__gte=now - LIVE_MAX_AGE,
    )
    return queryset.exclude(live_url="").filter(Exists(verified))


def _event_time(project):
    return project.launched_at or project.created_at


def explore(params, user, now=None):
    """Return a dict for the template: projects (one page), total, has_next, and the cleaned params."""
    now = now or timezone.now()
    queryset = published_projects()
    if params["q"]:
        queryset = queryset.filter(Q(name__icontains=params["q"]) | Q(tagline__icontains=params["q"]))
    if params["tag"]:
        queryset = queryset.filter(tags__slug=params["tag"])
    if params["tool"]:
        queryset = queryset.filter(built_with__slug=params["tool"])

    start = (params["page"] - 1) * PAGE_SIZE
    kind = params["hallmark"]

    if kind or params["sort"] == "proven":
        if kind:
            queryset = _may_have(queryset, kind, now)
        # Only what compute_hallmarks and the sort read: no screenshots, no description.
        candidates = list(with_social(with_uptime(
            queryset.defer("description").select_related("repo_link").prefetch_related("domain_verifications"), now,
        ), user))
        if kind:
            candidates = [p for p in candidates if p.hallmarks[kind].earned]
        first = {
            "newest": lambda p: 0,
            "liked": lambda p: p.like_count,
            "proven": lambda p: p.hallmarks.earned_count,
        }[params["sort"]]
        candidates.sort(key=lambda p: (first(p), _event_time(p), p.pk), reverse=True)
        page_ids = [p.pk for p in candidates[start:start + PAGE_SIZE]]
        rows = {p.pk: p for p in project_rows(published_projects().filter(pk__in=page_ids), user)}
        projects = [rows[pk] for pk in page_ids if pk in rows]
        return {"projects": projects, "total": len(candidates), "has_next": len(candidates) > start + PAGE_SIZE}

    total = queryset.count()
    order = ["-event_at", "-pk"] if params["sort"] == "newest" else ["-like_count", "-event_at", "-pk"]
    projects = list(project_rows(queryset, user).order_by(*order)[start:start + PAGE_SIZE])
    return {"projects": projects, "total": total, "has_next": total > start + PAGE_SIZE}
