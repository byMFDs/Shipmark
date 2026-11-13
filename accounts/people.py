"""People search on Discover (/explore/?tab=people): find a person by username, open the profile, follow.

Rules (POLISH3 stage 7):
- Username only, case-insensitive. Prefix matches first, then the ones that contain the text; inside each group
  alphabetical. At least MIN_LENGTH characters; an empty or too short query lists nobody, so there is no way to
  page through every account.
- A query with any character a username cannot have (%, *, spaces, regex signs ...) matches nobody. The lookups
  are Django's istartswith/icontains, which escape the LIKE wildcards % and _ on SQLite and PostgreSQL, so "_" is
  a literal underscore (usernames may contain it).
- Only people the public may see: active, not suspended, not banned (moderation.visibility), not the system
  account, not the demo accounts of seed_community. Deleted accounts no longer exist as rows.
- Only public fields reach the page: avatar, display name, username, badges, headline, counts. Never the email,
  GitHub id or login.
- A fixed number of queries per page whatever the number of results (test: assertNumQueries).
- Rate limited per account, or for anonymous visitors per salted hash of the IP address (a cache key only, for
  RATE_WINDOW seconds; the address itself is never kept). The query text is never stored or logged: request logs
  drop everything after "?" (config/jsonlog.py).
"""
import hashlib
import hmac
import re
from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Case, IntegerField, Value, When

from config.ratelimit import is_limited
from moderation.visibility import visible_users
from projects.models import Project
from social.models import Follow
from support.antispam import client_ip
from verification.uptime import with_uptime

from .system import SYSTEM_USERNAME
from .usernames import MAX_LENGTH

MIN_LENGTH = 2
PER_PAGE = 20
# Demo people of `seed_community` (DEBUG only): both marks, as that command defines them.
DEMO_PREFIX, DEMO_DOMAIN = "demo-", "@example.invalid"
# Searches per visitor and window. Generous for a person, tight for a script that walks the alphabet.
RATE_LIMIT_USER = 60
RATE_LIMIT_ANON = 30
RATE_WINDOW = 600

USERNAME_CHARS = re.compile(r"^[a-z0-9_-]+$")


def clean_query(raw):
    """What the visitor typed, trimmed, without a leading @, lowercased, at most a username long."""
    text = (raw or "").strip()
    if text.startswith("@"):
        text = text[1:]
    return text.lower()[:MAX_LENGTH + 1]


def query_problem(query):
    """'' when the query can be searched, else 'short' (fewer than MIN_LENGTH) or 'chars' (not a username)."""
    if len(query) < MIN_LENGTH:
        return "short"
    if len(query) > MAX_LENGTH or not USERNAME_CHARS.match(query):
        return "chars"
    return ""


def searchable_people():
    User = get_user_model()
    people = visible_users(User.objects.filter(is_active=True)).exclude(username=SYSTEM_USERNAME)
    return people.exclude(username__startswith=DEMO_PREFIX, email__endswith=DEMO_DOMAIN)


def search(query, page=1):
    """(people on this page, has_next). Call only when query_problem(query) is ''."""
    start = (page - 1) * PER_PAGE
    people = list(
        searchable_people()
        .filter(username__icontains=query)
        .annotate(rank=Case(When(username__istartswith=query, then=Value(0)), default=Value(1),
                            output_field=IntegerField()))
        .order_by("rank", "username", "pk")
        .only("pk", "username", "display_name", "headline", "avatar")
        .prefetch_related("badges")[start:start + PER_PAGE + 1]
    )
    return people[:PER_PAGE], len(people) > PER_PAGE


def attach_counts(people, viewer):
    """Sets person.project_count, person.hallmark_count and person.followed (by the viewer) on each person.

    Two queries for any number of people (projects with their proof data, then the viewer's follows), plus the
    prefetch of verified domains. Hallmarks come from compute_hallmarks, the one definition, like on the profile.
    """
    ids = [p.pk for p in people]
    projects, hallmarks = defaultdict(int), defaultdict(int)
    if ids:
        rows = with_uptime(
            Project.objects.filter(owner_id__in=ids, status=Project.Status.PUBLISHED)
            .select_related("repo_link").prefetch_related("domain_verifications")
        )
        for project in rows:
            projects[project.owner_id] += 1
            hallmarks[project.owner_id] += project.hallmarks.earned_count
    followed = set()
    if ids and getattr(viewer, "is_authenticated", False):
        followed = set(Follow.objects.filter(follower=viewer, following_id__in=ids).values_list("following_id", flat=True))
    for person in people:
        person.project_count = projects[person.pk]
        person.hallmark_count = hallmarks[person.pk]
        person.followed = person.pk in followed
    return people


def visitor_key(request):
    """The account id, or a salted one-way hash of the address for anonymous visitors (a cache key only)."""
    if request.user.is_authenticated:
        return f"u:{request.user.pk}"
    digest = hmac.new(settings.SECRET_KEY.encode(), f"people-ip:{client_ip(request)}".encode(), hashlib.sha256)
    return f"ip:{digest.hexdigest()[:32]}"


def search_limited(request):
    """Counts this search; True once the visitor is over the limit for the window."""
    limit = RATE_LIMIT_USER if request.user.is_authenticated else RATE_LIMIT_ANON
    return is_limited("people_search", visitor_key(request), limit=limit, window=RATE_WINDOW)
