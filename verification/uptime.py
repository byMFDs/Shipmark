"""Uptime checks and the Steady hallmark (CLAUDE.md section 2).

    probe(url)                 -> Probe, one HEAD (or GET) through safe_fetch
    check_project(project)     -> stored UptimeCheck, or None when checked less than 3 h ago
    due_projects(now)          -> projects with a Live domain and no check in the last 3 h
    prune(now)                 -> delete checks older than 90 days
    uptime_summary(project)    -> numbers and the 30-day strip for the project page
    with_uptime(queryset)      -> adds 30-day counts, so lists can compute Steady without N+1
    is_steady(project)         -> the Steady rule (Live is checked by proof.py)
"""
import time
from dataclasses import dataclass, field
from datetime import timedelta

from django.db.models import Count, Exists, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone

from .domain import LIVE_MAX_AGE, domain_key, host_from_url
from .models import DomainVerification, UptimeCheck
from .net import BlockedURL, FetchError, safe_fetch

CHECK_EVERY = timedelta(hours=3)
KEEP_FOR = timedelta(days=90)
WINDOW = timedelta(days=30)
WINDOW_DAYS = 30
STEADY_MIN_CHECKS = 40
STEADY_MIN_PERCENT = 95
NO_GET_RETRY = ("timeout",)  # a site that timed out on HEAD will time out on GET too; do not wait twice


# ---------- One check ----------

@dataclass
class Probe:
    ok: bool
    status_code: int | None
    response_ms: int | None
    error: str = ""


OTHER_HOST = "other_host"  # Probe.error: the site answered, but only after redirecting to another domain


def _request(url, method):
    start = time.monotonic()
    try:
        result = safe_fetch(url, method=method, read_body=False)
    except FetchError as exc:
        return None, None, None, exc
    return result.status_code, result.url, round((time.monotonic() - start) * 1000), None


def probe(url, expected_key=None):
    """HEAD first; GET when HEAD gets status >= 400 or fails (many servers refuse HEAD but serve GET).

    expected_key: the verified domain (domain_key). A site that ends up on another domain after its
    redirects is down for Steady: the answer is not from the domain that was proven.
    """
    status, final_url, ms, error = _request(url, "HEAD")
    retry = (status is not None and status >= 400) or (
        error is not None and not isinstance(error, BlockedURL) and error.code not in NO_GET_RETRY
    )
    if retry:
        status, final_url, ms, error = _request(url, "GET")
    if status is None:
        return Probe(ok=False, status_code=None, response_ms=None, error=error.code)
    if expected_key and domain_key(host_from_url(final_url)) != expected_key:
        return Probe(ok=False, status_code=status, response_ms=ms, error=OTHER_HOST)
    return Probe(ok=status < 400, status_code=status, response_ms=ms)


def recently_checked(project, now):
    return UptimeCheck.objects.filter(project=project, checked_at__gt=now - CHECK_EVERY).exists()


def check_project(project, now=None):
    """Check `project.live_url` once and store the result. None when checked less than 3 hours ago.

    The caller decides the project is Live. The 3-hour guard is repeated here, so two overlapping
    cron runs cannot store two checks.
    """
    now = now or timezone.now()
    if recently_checked(project, now):
        return None
    result = probe(project.live_url, expected_key=domain_key(host_from_url(project.live_url)))
    return UptimeCheck.objects.create(
        project=project, checked_at=now, ok=result.ok, status_code=result.status_code,
        response_ms=result.response_ms, error=result.error,
    )


def due_projects(now):
    """Projects with a verified domain confirmed in the last 35 days and no check in the last 3 hours.

    The exact "current domain" match is done by is_live() in the command, per project.
    Suspended users' projects are hidden, so they are not checked.
    """
    from projects.models import Project  # here, not at the top: projects.proof imports this module

    verified = DomainVerification.objects.filter(
        project=OuterRef("pk"), status=DomainVerification.Status.VERIFIED,
        last_confirmed_at__gte=now - LIVE_MAX_AGE,
    )
    recent = UptimeCheck.objects.filter(project=OuterRef("pk"), checked_at__gt=now - CHECK_EVERY)
    return (Project.objects.filter(Exists(verified)).filter(~Exists(recent))
            .exclude(live_url="").exclude(owner__is_suspended=True)
            .order_by("pk"))


def prune(now=None):
    """Delete checks older than 90 days. Returns how many were deleted."""
    cutoff = (now or timezone.now()) - KEEP_FOR
    deleted, _per_model = UptimeCheck.objects.filter(checked_at__lt=cutoff).delete()
    return deleted


# ---------- Numbers ----------

def percent(ok, total):
    """Share of successful checks, rounded down to one decimal: 39 of 40 -> 97.5, 2 of 3 -> 66.6.

    Rounded down, so 100 means every check succeeded. None when there are no checks.
    """
    if not total:
        return None
    return (ok * 1000 // total) / 10


def steady_rule(ok, total):
    """≥40 checks and ≥95% successful. Integer math: no float edge cases at exactly 95%."""
    return total >= STEADY_MIN_CHECKS and ok * 100 >= STEADY_MIN_PERCENT * total


def with_uptime(queryset, now=None):
    """Annotate `uptime_total` and `uptime_ok` (last 30 days). Subqueries, so other joins cannot inflate them."""
    since = (now or timezone.now()) - WINDOW
    checks = UptimeCheck.objects.filter(project=OuterRef("pk"), checked_at__gte=since).order_by().values("project")
    return queryset.annotate(
        uptime_total=Coalesce(Subquery(checks.annotate(n=Count("pk")).values("n")), 0),
        uptime_ok=Coalesce(Subquery(checks.filter(ok=True).annotate(n=Count("pk")).values("n")), 0),
    )


def window_counts(project, now=None):
    """(ok, total) over the last 30 days. Uses the with_uptime() annotation when the project has it."""
    if hasattr(project, "uptime_total"):
        return project.uptime_ok, project.uptime_total
    if not project.pk:
        return 0, 0
    since = (now or timezone.now()) - WINDOW
    rows = UptimeCheck.objects.filter(project=project, checked_at__gte=since)
    return rows.filter(ok=True).count(), rows.count()


def is_steady(project, now=None):
    """The uptime half of Steady. proof.py adds "and Live"."""
    return steady_rule(*window_counts(project, now))


# ---------- Project page ----------

@dataclass
class Day:
    date: object
    total: int = 0
    ok: int = 0

    @property
    def state(self):
        if not self.total:
            return "none"
        if self.ok == self.total:
            return "up"
        return "down" if self.ok == 0 else "partial"


@dataclass
class Summary:
    ok: int
    total: int
    last_checked_at: object
    days: list = field(default_factory=list)  # 30 Day objects, oldest first, the last one is today

    @property
    def percent(self):
        return percent(self.ok, self.total)


def uptime_summary(project, now=None):
    """Everything the uptime block on the project page shows. One or two queries."""
    now = now or timezone.now()
    rows = list(UptimeCheck.objects.filter(project=project, checked_at__gte=now - WINDOW)
                .order_by("checked_at").values_list("checked_at", "ok"))
    today = timezone.localdate(now)
    days = [Day(today - timedelta(days=WINDOW_DAYS - 1 - i)) for i in range(WINDOW_DAYS)]
    by_date = {day.date: day for day in days}
    for checked_at, ok in rows:
        day = by_date.get(timezone.localdate(checked_at))
        if day is not None:  # the first hours of the 30-day window fall on day 31; they count in the %
            day.total += 1
            day.ok += ok
    if rows:
        last = rows[-1][0]
    else:
        last = (UptimeCheck.objects.filter(project=project).order_by("-checked_at")
                .values_list("checked_at", flat=True).first())
    return Summary(ok=sum(ok for _t, ok in rows), total=len(rows), last_checked_at=last, days=days)
