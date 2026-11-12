"""What the feed and the like/follow buttons read. Subqueries and prefetches only, so a list is a fixed number of queries."""
from collections import namedtuple

from django.db.models import BooleanField, Count, Exists, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce

from moderation.visibility import visible_owner
from projects.models import BuildLogEntry, Project
from verification.uptime import with_uptime

from .models import Follow, Like

PAGE_SIZE = 20
MAX_PAGE = 50  # bounds the work of the "Following" merge below (page * 20 rows from each source)

# kind is "project" or "entry"; at is the time the item is sorted by.
FeedItem = namedtuple("FeedItem", "kind obj at")


def published_projects():
    """The only projects other people may see: published, and the owner is not suspended or banned."""
    return visible_owner(Project.objects.filter(status=Project.Status.PUBLISHED))


def follower_count(person):
    return Follow.objects.filter(following=person, follower__is_suspended=False).count()


def is_following(user, person):
    return user.is_authenticated and Follow.objects.filter(follower=user, following=person).exists()


def like_state(project, user):
    """(number of likes, did `user` like it). Likes of suspended users do not count."""
    count = Like.objects.filter(project=project, user__is_suspended=False).count()
    liked = user.is_authenticated and Like.objects.filter(project=project, user=user).exists()
    return count, liked


def with_social(queryset, user):
    """Annotate `like_count` and `liked`. Subqueries, so other joins cannot inflate the count."""
    likes = Like.objects.filter(project=OuterRef("pk"), user__is_suspended=False).order_by().values("project")
    queryset = queryset.annotate(like_count=Coalesce(Subquery(likes.annotate(n=Count("pk")).values("n")), 0))
    if user.is_authenticated:
        return queryset.annotate(liked=Exists(Like.objects.filter(project=OuterRef("pk"), user=user)))
    return queryset.annotate(liked=Value(False, output_field=BooleanField()))


def _event_at():
    # Not every project has launched_at (admin-made ones); Coalesce works the same on SQLite and PostgreSQL.
    return Coalesce("launched_at", "created_at")


def project_rows(queryset, user):
    """Same loading as the profile list, so project.hallmarks needs no extra queries."""
    return with_social(with_uptime(
        queryset.prefetch_related("screenshots", "domain_verifications", "owner__badges").select_related("owner", "repo_link")
    ), user).annotate(event_at=_event_at())


def latest_launches(user, page):
    """Everyone's recently launched projects. Returns (items, has_next)."""
    start = (page - 1) * PAGE_SIZE
    rows = list(project_rows(published_projects(), user).order_by("-event_at", "-pk")[start:start + PAGE_SIZE + 1])
    items = [FeedItem("project", p, p.event_at) for p in rows[:PAGE_SIZE]]
    return items, len(rows) > PAGE_SIZE


def following_feed(user, page):
    """Projects and build log updates of the people `user` follows. Returns (items, has_next).

    Two sorted sources are merged, so for page N we take the newest N * PAGE_SIZE + 1 of each
    (that is why MAX_PAGE exists). The "launch" log entry is left out: its project is already an item.
    """
    wanted = page * PAGE_SIZE + 1
    followed = Follow.objects.filter(follower=user, follower__is_suspended=False).values("following")
    projects = project_rows(published_projects().filter(owner__in=followed), user).order_by("-event_at", "-pk")[:wanted]
    entries = (
        visible_owner(BuildLogEntry.objects.filter(
            project__status=Project.Status.PUBLISHED,
            project__owner__in=followed,
        ), "project__owner").exclude(kind=BuildLogEntry.Kind.LAUNCH)
        .select_related("project__owner").prefetch_related("project__owner__badges")
        .order_by("-created_at", "-pk")[:wanted]
    )
    merged = [FeedItem("project", p, p.event_at) for p in projects] + [FeedItem("entry", e, e.created_at) for e in entries]
    merged.sort(key=lambda item: (item.at, item.kind, item.obj.pk), reverse=True)
    start = (page - 1) * PAGE_SIZE
    return merged[start:start + PAGE_SIZE], len(merged) > page * PAGE_SIZE
