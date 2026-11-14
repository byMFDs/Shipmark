"""Видаляє закриті звернення, старші 12 місяців, з вкладеннями (cron).

Delete closed support messages older than 12 months, with their attachment files (cron, daily or weekly).

    python manage.py prune_support

Messages that are new, read or answered are kept until someone closes them. The privacy page promises this.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from support.models import SupportMessage

KEEP_CLOSED = timedelta(days=365)


def prune(now=None):
    """Видаляє старі закриті звернення; повертає кількість."""
    cutoff = (now or timezone.now()) - KEEP_CLOSED
    old = SupportMessage.objects.filter(status=SupportMessage.Status.CLOSED, created_at__lt=cutoff)
    count = old.count()
    for message in old:  # one by one: the attachment rows and files go with each message
        message.delete()
    return count


class Command(BaseCommand):
    """Команда prune_support."""
    help = "Delete closed support messages older than 12 months, with their attachments."

    def handle(self, *args, **options):
        self.stdout.write(f"Deleted {prune()} closed support messages older than 12 months.")
