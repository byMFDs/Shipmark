"""Команда make_thumbs: створює мініатюри для скриншотів без них.

python manage.py make_thumbs: build the small list copies for screenshots that have none (once after deploy).

New screenshots get one when they are saved. Safe to repeat: only rows without a thumbnail are touched, and a file
that cannot be read is reported and skipped (lists keep using its full image)."""
from django.core.management.base import BaseCommand

from projects.models import Screenshot


class Command(BaseCommand):
    """Команда make_thumbs."""
    help = "Create thumbnails for screenshots that do not have one."

    def handle(self, *args, **options):
        """Створює відсутні мініатюри й рахує успіхи та збої."""
        made = failed = 0
        for shot in Screenshot.objects.filter(thumb="").iterator():
            if shot.make_thumb():
                made += 1
            else:
                failed += 1
                self.stderr.write(f"Could not read the image of screenshot {shot.pk}; skipped.")
        self.stdout.write(f"Made {made} thumbnail(s), {failed} skipped.")
