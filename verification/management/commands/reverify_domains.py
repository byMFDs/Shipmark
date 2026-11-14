"""Команда reverify_domains: повторна перевірка доменів (cron щодня).

Re-check verified domains not confirmed in the last 30 days. Run daily by cron.

    python manage.py reverify_domains

A definite failure (token gone, domain gone) removes Live and writes AuditLog.
A temporary one (DNS timeout, site down) is retried on the next run, for up to 35 days in total.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from verification.domain import REVERIFY_AFTER, reverify
from verification.models import DomainVerification


class Command(BaseCommand):
    """Команда reverify_domains."""
    help = "Re-check verified domains older than 30 days; remove Live when the proof is gone."

    def handle(self, *args, **options):
        """Перевіряє домени, не підтверджені 30 днів, і рахує результати."""
        now = timezone.now()
        due = (DomainVerification.objects
               .filter(status=DomainVerification.Status.VERIFIED, last_confirmed_at__lt=now - REVERIFY_AFTER)
               .select_related("project", "project__owner")
               .order_by("last_confirmed_at"))
        counts = {"confirmed": 0, "kept": 0, "removed": 0}
        for row in due.iterator(chunk_size=200):
            outcome = reverify(row, now=now)
            counts[outcome] += 1
            if outcome != "confirmed" and options["verbosity"] > 1:
                self.stdout.write(f"{row.domain}: {outcome} ({row.last_error})")
        self.stdout.write(
            f"Confirmed {counts['confirmed']}, retry later {counts['kept']}, removed {counts['removed']}."
        )
