"""Команда check_uptime: перевіряє, чи відповідають Live-проєкти (cron кожні 15 хвилин).

Check that Live projects answer. Run by cron every 15 minutes (docs/DEPLOY_NOTES.md).

    python manage.py check_uptime

Each project is checked at most once per 3 hours, so a frequent cron only spreads the work.
Projects are loaded in small batches; an error on one site is logged and the run goes on.
Checks older than 90 days are deleted at the end.
"""
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from projects.models import Project
from verification.domain import is_live
from verification.uptime import check_project, due_projects, prune

logger = logging.getLogger(__name__)
BATCH_SIZE = 50


class Command(BaseCommand):
    """Команда check_uptime."""
    help = "Check live URLs of projects with a verified domain (max once per 3 hours each); prune old checks."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)

    def handle(self, *args, **options):
        size = max(1, options["batch_size"])
        # Ids first: the list does not shift while checks are being written.
        ids = list(due_projects(timezone.now()).values_list("pk", flat=True))
        counts = {"up": 0, "down": 0, "skipped": 0, "errors": 0}
        for start in range(0, len(ids), size):
            batch = (Project.objects.filter(pk__in=ids[start:start + size])
                     .prefetch_related("domain_verifications").order_by("pk"))
            for project in batch:
                counts[self._check(project, options["verbosity"])] += 1
        deleted = prune()
        self.stdout.write(
            f"Up {counts['up']}, down {counts['down']}, skipped {counts['skipped']}, "
            f"errors {counts['errors']}. Deleted {deleted} old checks."
        )

    def _check(self, project, verbosity):
        """Перевіряє один проєкт."""
        now = timezone.now()
        if not is_live(project, now=now):  # verified domain is not the one in live_url any more
            return "skipped"
        try:
            check = check_project(project, now=now)
        except Exception:  # one broken site or bug must never stop the run
            logger.exception("Uptime check failed for project %s", project.pk)
            return "errors"
        if check is None:
            return "skipped"
        if not check.ok and verbosity > 1:
            self.stdout.write(f"{project.live_url}: down ({check.status_code or check.error})")
        return "up" if check.ok else "down"
