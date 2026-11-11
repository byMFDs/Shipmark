"""Fill new fields of existing repo links from GitHub. Run once after deploying, then it is a no-op.

    python manage.py backfill_repo_facts            # links with missing facts
    python manage.py backfill_repo_facts --dry-run  # only say what would change

It never removes a hallmark. A repository that looks different now (gone, private, another owner)
is only reported here; `reverify_repos` decides about it with the same rules as every week.
On a rate limit the run stops; run it again later, it continues where it stopped.
"""
from django.core.management.base import BaseCommand

from accounts.github import github_id
from verification.models import RepoLink
from verification.repo import RepoCheckError, _Api, repo_by_id


class Command(BaseCommand):
    help = "Fill missing GitHub ids of existing repo links. Never removes a hallmark."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        counts = {"filled": 0, "changed": 0, "unavailable": 0}
        links = (RepoLink.objects.filter(github_owner_id__isnull=True)
                 .select_related("project", "project__owner").order_by("pk"))
        for link in links.iterator(chunk_size=100):
            try:
                with _Api() as api:  # a fresh client per link: each gets the full per-check deadline
                    repo = repo_by_id(api, link.github_repo_id)
            except RepoCheckError as exc:
                if exc.code == "rate_limited":
                    self.stdout.write(f"Rate limited, stopped. {exc.message}")
                    break
                counts["changed" if exc.code == "not_found" else "unavailable"] += 1
                self.stdout.write(f"{link.repo_full_name}: {exc.code}, left for reverify_repos")
                continue
            owner_id = repo["owner"]["id"]
            user_id = github_id(link.project.owner)
            if link.is_owner and owner_id != user_id:
                # Filling the new owner's id would hide the transfer from every later check.
                counts["changed"] += 1
                self.stdout.write(f"{link.repo_full_name}: owner changed on GitHub, left for reverify_repos")
                continue
            counts["filled"] += 1
            if not options["dry_run"]:
                link.github_owner_id = owner_id
                link.save(update_fields=["github_owner_id"])
        self.stdout.write(
            f"Filled {counts['filled']}, changed on GitHub {counts['changed']}, "
            f"GitHub unavailable {counts['unavailable']}." + (" (dry run)" if options["dry_run"] else "")
        )
