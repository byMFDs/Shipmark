"""Щоденне обслуговування спільноти (cron): перерахунок голосів і відповідей, чистка сповіщень.

Daily community upkeep (cron), safe to run at any time:

1. Recompute the denormalized counters: `score` of threads and replies, `reply_count` of threads. They move with
   every vote and reply, so this repairs drift and is where the votes of suspended and banned people stop counting.
2. Delete reply notifications older than 90 days (community/limits.py NOTIFICATION_RETENTION).

    python manage.py community_daily
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from community import notifications
from community.models import Reply, Thread, Vote
from moderation.visibility import banned


def _votes(field):
    """Підзапит: кількість голосів від видимих людей."""
    counted = (
        Vote.objects.filter(**{field: OuterRef("pk")}, user__is_suspended=False).filter(~banned("user"))
        .order_by().values(field).annotate(n=Count("pk")).values("n")
    )
    return Coalesce(Subquery(counted, output_field=IntegerField()), 0)


def _replies():
    """Підзапит: кількість живих відповідей у темі."""
    counted = (
        Reply.objects.filter(thread=OuterRef("pk"), status=Reply.Status.PUBLISHED, deleted_at__isnull=True)
        .order_by().values("thread").annotate(n=Count("pk")).values("n")
    )
    return Coalesce(Subquery(counted, output_field=IntegerField()), 0)


def recount():
    """Перераховує лічильники тем і відповідей; повертає кількість змінених рядків.

    Returns (threads, replies) rows touched."""
    threads = Thread.objects.update(score=_votes("thread"), reply_count=_replies())
    replies = Reply.objects.update(score=_votes("reply"))
    return threads, replies


class Command(BaseCommand):
    """Команда community_daily."""
    help = "Recompute community scores and reply counts, and delete reply notifications older than 90 days."

    def handle(self, *args, **options):
        threads, replies = recount()
        pruned = notifications.prune()
        self.stdout.write(f"Recounted {threads} threads and {replies} replies. Deleted {pruned} old notifications.")
