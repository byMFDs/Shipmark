"""python manage.py rehash_bans: move ban hashes made with the old SECRET_KEY scheme to BAN_HASH_KEY.

Run once after deploying BAN_HASH_KEY (safe to repeat). Only bans whose account still exists can be converted: the
GitHub id is not stored anywhere else. The rest keep matching through the old scheme until they expire; the old scheme
is only used while such rows exist.
"""
from django.core.management.base import BaseCommand

from moderation import bans


class Command(BaseCommand):
    help = "Rehash active ban hashes with BAN_HASH_KEY."

    def handle(self, *args, **options):
        converted, left_over = bans.rehash()
        self.stdout.write(f"Rehashed {converted} ban hash(es) with BAN_HASH_KEY.")
        if left_over:
            self.stdout.write(
                f"{left_over} old-scheme hash(es) cannot be converted (their account was deleted). They still match "
                "through SECRET_KEY / SECRET_KEY_FALLBACKS until they expire: keep those keys until then."
            )
        else:
            self.stdout.write("No old-scheme hashes left: SECRET_KEY no longer has anything to do with bans.")
