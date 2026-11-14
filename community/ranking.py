"""Порядок тем: Hot, New, Top, обчислений у SQL.

Thread order: Hot, New, Top. Computed in SQL (SQLite and PostgreSQL), no new dependency.

    hot = (10 * score + 4 * min(reply_count, 50) + 10) * decay

- score        upvotes (there are no downvotes)
- reply_count  capped at 50, so one long argument cannot hold the top for days
- +10          a new thread without votes still sorts by age instead of tying at zero
- decay        by the age of the thread: 32 under 6 hours, 16 under a day, 8 under 3 days, 4 under a week,
               2 under 30 days, 1 older. Steps, not a curve: LOG/POWER are not portable between the two databases
               (the same choice as social/ranking.py).

Whole numbers only. Ties: the thread with newer activity first, then the higher id, so the order is stable and
pages never repeat or skip a thread. Pinned threads are not ranked: the pages show them in their own row.

New = newest first. Top = most upvotes among threads created in the window (week, month, all time).
Replies: Best = most upvotes, then older first; New = newest first; applied on every level of the tree.
"""
from datetime import timedelta

from django.db.models import Case, F, IntegerField, Value, When
from django.db.models.functions import Least

SCORE_POINTS, REPLY_POINTS, REPLY_CAP, BASE_POINTS = 10, 4, 50, 10
DECAY_STEPS = (
    (timedelta(hours=6), 32), (timedelta(days=1), 16), (timedelta(days=3), 8), (timedelta(days=7), 4),
    (timedelta(days=30), 2),
)
DECAY_OLDEST = 1

SORTS = ("hot", "new", "top")
TOP_WINDOWS = {"week": timedelta(days=7), "month": timedelta(days=30), "all": None}
REPLY_SORTS = ("best", "new")


def with_hot(queryset, now):
    """Додає до тем бал «гарячості» з урахуванням віку."""
    decay = Case(
        *[When(created_at__gte=now - age, then=Value(factor)) for age, factor in DECAY_STEPS],
        default=Value(DECAY_OLDEST), output_field=IntegerField(),
    )
    points = F("score") * SCORE_POINTS + Least(F("reply_count"), Value(REPLY_CAP)) * REPLY_POINTS + BASE_POINTS
    return queryset.annotate(hot=points * decay)


def ordered(queryset, sort, window, now):
    """Сортує теми за обраним порядком і вікном.

    `sort` in SORTS, `window` a key of TOP_WINDOWS (used by "top" only)."""
    if sort == "new":
        return queryset.order_by("-created_at", "-pk")
    if sort == "top":
        age = TOP_WINDOWS.get(window)
        if age is not None:
            queryset = queryset.filter(created_at__gte=now - age)
        return queryset.order_by("-score", "-reply_count", "-pk")
    return with_hot(queryset, now).order_by("-hot", "-last_activity_at", "-pk")


def sort_replies(replies, sort):
    if sort == "new":
        return sorted(replies, key=lambda r: (r.created_at, r.pk), reverse=True)
    return sorted(replies, key=lambda r: (-r.score, r.created_at, r.pk))
