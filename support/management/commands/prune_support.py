"""Видаляє закриті звернення, старші 12 місяців, з вкладеннями (cron).

Delete closed support messages older than 12 months, with their attachment files (cron, daily or weekly).

    python manage.py prune_support

Messages that are new, read or answered are kept until someone closes them. The privacy page promises this.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.core.cache.backends.db import DatabaseCache
from django.db import connections, router
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


def prune_cache():
    """Фізично видаляє прострочені рядки всіх налаштованих кешів БД."""
    count = 0
    visited = set()
    for alias in caches:
        backend = caches[alias]
        if not isinstance(backend, DatabaseCache):
            continue
        model = backend.cache_model_class
        database = router.db_for_write(model)
        table = model._meta.db_table
        if (database, table) in visited:
            continue
        visited.add((database, table))
        connection = connections[database]
        quote = connection.ops.quote_name
        cutoff = connection.ops.adapt_datetimefield_value(timezone.now())
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {quote(table)} WHERE {quote('expires')} < %s", [cutoff])
            count += cursor.rowcount
    return count


class Command(BaseCommand):
    """Команда prune_support."""
    help = "Delete closed support messages older than 12 months, with their attachments."

    def handle(self, *args, **options):
        self.stdout.write(f"Deleted {prune()} closed support messages older than 12 months.")
        self.stdout.write(f"Deleted {prune_cache()} expired database cache rows.")
