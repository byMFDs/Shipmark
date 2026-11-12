"""Recompute the denormalized counters: `score` of threads and replies, `reply_count` of threads.

They move with every vote and reply, so this is a repair tool and the place where the votes of suspended and
banned people stop counting. Safe to run at any time; daily from cron is enough.

    python manage.py community_recount
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from community.models import Reply, Thread, Vote
from moderation.visibility import banned


def _votes(field):
    counted = (
        Vote.objects.filter(**{field: OuterRef("pk")}, user__is_suspended=False).filter(~banned("user"))
        .order_by().values(field).annotate(n=Count("pk")).values("n")
    )
    return Coalesce(Subquery(counted, output_field=IntegerField()), 0)


def _replies():
    counted = (
        Reply.objects.filter(thread=OuterRef("pk"), status=Reply.Status.PUBLISHED, deleted_at__isnull=True)
        .order_by().values("thread").annotate(n=Count("pk")).values("n")
    )
    return Coalesce(Subquery(counted, output_field=IntegerField()), 0)


def recount():
    """Returns (threads, replies) rows touched."""
    threads = Thread.objects.update(score=_votes("thread"), reply_count=_replies())
    replies = Reply.objects.update(score=_votes("reply"))
    return threads, replies


class Command(BaseCommand):
    help = "Recompute community scores and reply counts (votes of suspended and banned accounts are left out)."

    def handle(self, *args, **options):
        threads, replies = recount()
        self.stdout.write(f"Recounted {threads} threads and {replies} replies.")
