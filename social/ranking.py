"""The "For you" ranking: one score per project, computed in SQL (SQLite and PostgreSQL, no new dependency).

    score = (2 * likes + followers / 5 + 3 * marks + 1) * decay

- likes     likes from accounts that are not suspended (social.queries.with_social)
- followers the owner's followers (not suspended), capped at 50 so one famous account cannot bury everyone else
- marks     how many of Repo owner / Live / Steady the project has (0 to 3), see below
- +1        so a brand-new project with no signals still sorts by recency instead of all tying at zero
- decay     by the age of the launch (`event_at`): 8 under a day, 4 under 3 days, 2 under a week, 1 under 30 days,
            0.5 older. Steps, not a curve: POWER/LOG are not portable between SQLite and PostgreSQL

The database works in whole numbers, so everything is multiplied by 10 (likes 20, followers 2 per follower up to 100,
marks 30, base 10) and by 2 for the decay (16 / 8 / 4 / 2 / 1). Ordering is unchanged; only the numbers are bigger.
Ties break by newest launch, then by id, so the order is stable and "Load more" never repeats or skips a project.

MARKS IN SQL ARE FOR RANKING ONLY. The one definition of a hallmark is projects.proof.compute_hallmarks. The SQL here
mirrors it closely (same review states, 35-day confirmation, 40 checks and 95%), but it does not compare the verified
domain with the live URL's host (that needs Python). It can therefore only rank a project a little too high, never
decide what a card shows: cards and the hallmark filter use compute_hallmarks. A test compares both on many cases.
"""
from datetime import timedelta

from django.db.models import Case, Count, Exists, F, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Coalesce, Least, Lower

from projects.models import BuildLogEntry
from verification.domain import LIVE_MAX_AGE
from verification.models import DomainVerification, RepoLink
from verification.uptime import STEADY_MIN_CHECKS, STEADY_MIN_PERCENT

from .models import Follow

# Human weights x 10 (see the module docstring).
LIKE_POINTS, FOLLOWER_POINTS, FOLLOWER_CAP, MARK_POINTS, BASE_POINTS = 20, 2, 50, 30, 10
# Decay x 2: (age limit, factor). Older than the last limit: 1.
DECAY_STEPS = ((timedelta(days=1), 16), (timedelta(days=3), 8), (timedelta(days=7), 4), (timedelta(days=30), 2))
DECAY_OLDEST = 1


def _int(condition):
    return Case(When(condition, then=Value(1)), default=Value(0), output_field=IntegerField())


def has_repo_mark():
    """SQL twin of proof._authored: a checked link for the project's current repository name."""
    link = (
        RepoLink.objects.annotate(_name=Lower("repo_full_name"))
        .filter(project=OuterRef("pk"), _name=Lower(OuterRef("repo_full_name")),
                review_state__in=[RepoLink.Review.CLEAR, RepoLink.Review.APPROVED])
        .filter(Q(is_owner=True) | Q(token_file_found=True))
    )
    return ~Q(repo_full_name="") & Exists(link)


def has_live_mark(now):
    """SQL twin of proof._live, without the host comparison (see the docstring)."""
    verified = DomainVerification.objects.filter(
        project=OuterRef("pk"), status=DomainVerification.Status.VERIFIED, last_confirmed_at__gte=now - LIVE_MAX_AGE,
    )
    return ~Q(live_url="") & Exists(verified)


def with_marks(queryset, now):
    """Annotate `marks` (0-3). Needs the with_uptime() annotations (uptime_total, uptime_ok) on the queryset."""
    queryset = queryset.annotate(_ok100=F("uptime_ok") * 100, _need=F("uptime_total") * STEADY_MIN_PERCENT)
    steady = has_live_mark(now) & Q(uptime_total__gte=STEADY_MIN_CHECKS) & Q(_ok100__gte=F("_need"))
    return queryset.annotate(
        marks=_int(has_repo_mark()) + _int(has_live_mark(now)) + _int(steady),
    )


def with_score(queryset, now):
    """Annotate `score`. Needs `event_at`, `like_count` and the with_uptime() annotations (project_rows gives all)."""
    followers = Follow.objects.filter(following=OuterRef("owner"), follower__is_suspended=False).order_by().values("following")
    queryset = with_marks(queryset, now).annotate(
        owner_followers=Coalesce(Subquery(followers.annotate(n=Count("pk")).values("n")), 0),
    )
    decay = Case(
        *[When(event_at__gte=now - age, then=Value(factor)) for age, factor in DECAY_STEPS],
        default=Value(DECAY_OLDEST), output_field=IntegerField(),
    )
    return queryset.annotate(
        score=(
            LIKE_POINTS * F("like_count")
            + FOLLOWER_POINTS * Least(F("owner_followers"), Value(FOLLOWER_CAP))
            + MARK_POINTS * F("marks")
            + BASE_POINTS
        ) * decay,
    )


def with_latest_update(queryset):
    """Annotate the newest build-log update (not the launch entry): `update_text`, `update_at`, `update_id`."""
    newest = BuildLogEntry.objects.filter(project=OuterRef("pk")).exclude(kind=BuildLogEntry.Kind.LAUNCH).order_by("-created_at", "-pk")
    return queryset.annotate(
        update_text=Subquery(newest.values("text")[:1]),
        update_at=Subquery(newest.values("created_at")[:1]),
        update_id=Subquery(newest.values("pk")[:1]),
    )
