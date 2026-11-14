"""Команда backfill_repo_facts: дозаповнює нові факти наявних посилань з GitHub.

Fill new facts of existing repo links from GitHub. Run once after deploying; later runs skip done links.

    python manage.py backfill_repo_facts            # links with missing facts
    python manage.py backfill_repo_facts --dry-run  # only say what would change

Fills: owner id, repository creation date, oldest commit (sha, date), active weeks, commit dates.
It never removes a hallmark:
- facts that need a review (imported or duplicate history, no commits by the owner) -> "needs review";
- a repository that is different now (gone, private, fork, another owner or id) -> "needs re-check";
both logged in AuditLog. `reverify_repos` and the review queue in the admin decide after that.
GitHub errors and rate limits change nothing: run the command again later, it continues.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from accounts.github import github_id
from verification.models import RepoLink
from verification.repo import RepoCheckError, fetch_facts, follow_rename, identity_change, mark_recheck, store_link

DEFINITE = ("not_found", "private", "moved", "invalid", "taken")


class Command(BaseCommand):
    """Команда backfill_repo_facts."""
    help = "Fill missing facts of existing repo links from GitHub. Never removes a hallmark."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        counts = {"filled": 0, "review": 0, "recheck": 0, "unavailable": 0}
        links = (RepoLink.objects.filter(Q(github_owner_id__isnull=True) | Q(repo_created_at__isnull=True))
                 .exclude(review_state=RepoLink.Review.NEEDS_RECHECK)
                 .select_related("project", "project__owner").order_by("pk"))
        for link in links.iterator(chunk_size=100):
            outcome = self._one(link, dry)
            if outcome == "stop":
                break
            counts[outcome] += 1
        self.stdout.write(
            f"Filled {counts['filled']}, needs review {counts['review']}, needs re-check {counts['recheck']}, "
            f"GitHub unavailable {counts['unavailable']}." + (" (dry run)" if dry else "")
        )

    def _one(self, link, dry):
        """Дозаповнює одне посилання."""
        name = link.repo_full_name
        try:
            facts = fetch_facts(name, github_id(link.project.owner), link.project)
        except RepoCheckError as exc:
            if exc.code == "rate_limited":
                self.stdout.write(f"Rate limited, stopped. {exc.message}")
                return "stop"
            if exc.code not in DEFINITE:
                self.stdout.write(f"{name}: {exc.code}, try again later")
                return "unavailable"
            reason = exc.code
        else:
            change = identity_change(link, facts.repo_id, facts.owner_id, facts.full_name)
            reason = (change if change in ("recreated", "transferred")
                      else "fork" if facts.is_fork else None if facts.is_owner or facts.token_file else "not_owner")
            if reason is None:
                if not dry:
                    follow_rename(link.project, link, facts, None)
                    link = store_link(link.project, facts, link)
                    self.stdout.write(f"{name}: filled" + (f", needs review ({', '.join(link.review_reasons)})"
                                                            if link.review_state == RepoLink.Review.NEEDS_REVIEW else ""))
                return "review" if not dry and link.review_state == RepoLink.Review.NEEDS_REVIEW else "filled"
        self.stdout.write(f"{name}: {reason}, needs re-check")
        if not dry:
            mark_recheck(link, reason, source="backfill")
        return "recheck"
