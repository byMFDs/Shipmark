"""Стартові теми спільноти від офіційного акаунта shipmark (без вигаданих людей).

Genuine discussion starters for the launch, written by the team from the official system account "shipmark".

    python manage.py seed_launch_content            # create the threads that do not exist yet
    python manage.py seed_launch_content --dry-run  # only list what would be created

Safe in production and safe to run again:
- Only the system account writes. No other account is created or used, no replies, no votes, no notifications.
- A thread is identified by its title: if the system account already has a thread with that title (in any state,
  also one a moderator removed), it is left alone, so a deliberate removal is never undone.
- Works with COMMUNITY_ENABLED off, so it can be prepared before the community is switched on.
- Text is English, the site's default language (user content is never translated), plain and short.
Each created thread is logged in the AuditLog as `community.launch_thread_posted`.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import User
from accounts.system import SYSTEM_USERNAME, system_user
from community import services
from community.models import Board, Thread
from config import branding
from moderation import audit

SIGNATURE = f"\n\n\u2014 The {branding.SITE_NAME} team"

# (board slug, title, body, pinned)
THREADS = [
    ("show", "What are you building this week?",
     "Tell us what you are working on right now, in a sentence or two. It can be tiny, half-finished or still just "
     "an idea. If it has a link, add it. We read every answer, and so will the people who build next to you.",
     True),
    ("off-topic", "Which AI tools do you use, and for what?",
     "We are curious about your real setup: which tools you use, what each one is good for, and what you stopped "
     "using. Short answers are fine, for example \"Claude Code for refactors, Cursor for quick edits\". "
     "No ranking, no wrong answers.",
     False),
    ("show", "Share the first thing you shipped",
     "Everyone remembers the first thing that went live, however small. What was it, how long did it take, and "
     "what did you learn? If it is still online, link it.",
     False),
    ("help", "Questions about how proof works? Ask here",
     "Marks are earned from facts we check: repository ownership, domain control and uptime. If something about "
     "that is unclear, or a check did not do what you expected, ask here and we will answer. The short version "
     "is on the \"How proof works\" page.",
     False),
    ("feedback", "Ideas for Shipmark",
     "What would make this place more useful to you? A missing check, a confusing page, something you wish "
     "you could show on your profile. One idea per reply makes it easier to discuss. We read all of them, "
     "but we cannot promise to build all of them.",
     False),
]


def plan():
    """Теми, яких ще немає: список (дошка, назва, текст, закріплена)."""
    author = system_user()
    existing = set(Thread.objects.filter(author=author).values_list("title", flat=True))
    return [row for row in THREADS if row[1] not in existing]


def seed():
    """Створює відсутні теми від системного акаунта; повертає (створені, пропущені дошки)."""
    author = system_user()
    created, skipped = [], []
    for slug, title, body, pinned in plan():
        board = Board.objects.filter(slug=slug, is_active=True).first()
        if board is None:
            skipped.append(slug)
            continue
        with transaction.atomic():
            thread = services.create_thread(author, board, title, body + SIGNATURE)
            if pinned:
                thread.pinned = True
                thread.save(update_fields=["pinned"])
            audit.log("community.launch_thread_posted", thread, board=board.slug, pinned=pinned)
        created.append(thread)
    return created, skipped


class Command(BaseCommand):
    """Команда seed_launch_content."""
    help = 'Post the launch discussion starters from the official "shipmark" account (idempotent, no fake people).'

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only list what would be created.")

    def handle(self, *args, dry_run=False, **options):
        """Створює стартові теми або лише показує їх."""
        if not User.objects.filter(is_system_account=True).exists():
            raise CommandError(f"The system account {SYSTEM_USERNAME!r} does not exist (run migrate first).")
        if dry_run:
            rows = plan()
            for slug, title, _body, pinned in rows:
                self.stdout.write(f"Would post in {slug}: {title}{' (pinned)' if pinned else ''}")
            self.stdout.write(f"{len(rows)} thread(s) to create, {len(THREADS) - len(rows)} already there.")
            return
        created, skipped = seed()
        for thread in created:
            self.stdout.write(self.style.SUCCESS(f"Posted: {thread.get_absolute_url()}"))
        for slug in skipped:
            self.stdout.write(self.style.WARNING(f"Skipped: the board {slug!r} is missing or inactive."))
        if not created:
            self.stdout.write("Nothing to do: all launch threads already exist.")
