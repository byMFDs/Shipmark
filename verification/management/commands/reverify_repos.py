"""Check linked repositories again. Run daily by cron; each link is re-checked weekly (docs/DEPLOY_NOTES.md).

    python manage.py reverify_repos              # links due (7 days, needs re-check, pending statistics)
    python manage.py reverify_repos --all        # every link, e.g. after changing the rules
    python manage.py reverify_repos --project 12 # one project

By repo id: ownership (owner id), public visibility, then the facts. Only definite answers change
anything (gone, private, another repository or owner, fork, blocked: the mark is removed; new
review facts: "needs review"); each change is written to AuditLog. GitHub errors keep the state and
are retried next run. A rate limit stops the run. Needs GITHUB_API_TOKEN in production (5000 requests
an hour instead of 60; one link costs up to about 10).
"""
import logging

from django.core.management.base import BaseCommand

from verification.models import RepoLink
from verification.repo import RepoCheckError, due_links, reverify_link

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-check linked GitHub repositories by id; remove or review marks on definite changes."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Every link, not only the ones due.")
        parser.add_argument("--project", type=int, help="Only this project id.")

    def handle(self, *args, **options):
        links = RepoLink.objects.select_related("project", "project__owner").order_by("checked_at")
        if options["project"]:
            links = links.filter(project_id=options["project"])
        elif not options["all"]:
            links = due_links()
        ids = list(links.values_list("pk", flat=True))  # ids first: rows change while we work
        counts = {"confirmed": 0, "review": 0, "removed": 0, "kept": 0, "errors": 0}
        for pk in ids:
            link = RepoLink.objects.select_related("project", "project__owner").filter(pk=pk).first()
            if link is None:
                continue  # removed meanwhile (the owner changed the repository, a parallel check)
            try:
                outcome = reverify_link(link)
            except RepoCheckError as exc:  # only a rate limit gets here
                self.stdout.write(f"Rate limited, stopped. {exc.message}")
                break
            except Exception:  # one broken answer or bug must never stop the run
                logger.exception("Repo re-check failed for link %s", pk)
                outcome = "errors"
            counts[outcome] += 1
            if outcome not in ("confirmed", "kept") and options["verbosity"] > 1:
                self.stdout.write(f"{link.repo_full_name}: {outcome}")
        self.stdout.write(
            f"Confirmed {counts['confirmed']}, needs review {counts['review']}, removed {counts['removed']}, "
            f"retry later {counts['kept']}, errors {counts['errors']}."
        )
