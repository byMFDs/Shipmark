"""python manage.py prune_bans: delete the GitHub-id hashes of bans that have ended (daily cron).

They are also pruned whenever a sign-up is checked; this catches the quiet days. Nothing else to clean:
sanction expiry itself is evaluated per request.
"""
from django.core.management.base import BaseCommand

from moderation.bans import prune


class Command(BaseCommand):
    help = "Delete the stored hashes of bans that have ended."

    def handle(self, *args, **options):
        self.stdout.write(f"Deleted {prune()} ended ban hash(es).")
