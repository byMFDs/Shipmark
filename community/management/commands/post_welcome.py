"""Публікує закріплену тему «Вітання й правила» від системного акаунта.

Post the pinned "Welcome and rules" thread from the official system account "shipmark".

    python manage.py post_welcome                 # on the first active board
    python manage.py post_welcome --board help
    python manage.py post_welcome --force         # post a fresh one and unpin the old one

Safe to run again: while a welcome thread from the system account exists (and was not removed), nothing happens.
Works with COMMUNITY_ENABLED off, so it can be prepared before the community is switched on. The text is English,
like every post (user content is never translated); it links to /community/rules/, which is in the reader's
language. Logged in the AuditLog as `community.welcome_posted`.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.system import system_user
from config import branding
from community import services
from community.models import Board, Thread
from moderation import audit

TITLE = "Welcome and rules"


def welcome_body():
    """Текст вітальної теми."""
    return f"""Welcome to the {branding.SITE_NAME} community: ask for help, show what you shipped, find people to build with, and talk shop with people who build with AI.

**The rules in short**

1. Be kind and specific. Criticise work, never people.
2. Stay on the board's topic. Everything else goes to Off-topic.
3. No spam or advertising, no harassment, nothing illegal or sexual.
4. Only post what you may share, and respect other people's privacy.
5. Do not pretend: no impersonation, no fake proof, no claims that you wrote code you did not write.

The full text: [Community rules](/community/rules/).

**How it works**

- Upvotes only. You cannot upvote your own post.
- Replies go three levels deep.
- Every thread and reply has a Report link. Moderators always give a reason, and the author sees it.
- When someone answers you, it shows under "Replies to you". We never send email.

Questions or appeals: {branding.CONTACT_EMAIL}. Have fun, and ship things."""


def existing_welcome():
    return Thread.objects.filter(author=system_user(), title=TITLE).exclude(status=Thread.Status.REMOVED).first()


def post_welcome(board=None, force=False):
    """Створює вітальну тему; повертає (тема, чи створено).

    Returns (thread, created)."""
    author = system_user()
    old = existing_welcome()
    if old is not None and not force:
        return old, False
    board = board or Board.objects.filter(is_active=True).order_by("order", "pk").first()
    if board is None:
        raise CommandError("There is no active board.")
    with transaction.atomic():
        if old is not None:
            Thread.objects.filter(pk=old.pk).update(pinned=False)
        thread = services.create_thread(author, board, TITLE, welcome_body())
        thread.pinned = True
        thread.save(update_fields=["pinned"])
        audit.log("community.welcome_posted", thread, board=board.slug, replaced=old.pk if old else None)
    return thread, True


class Command(BaseCommand):
    """Команда post_welcome."""
    help = 'Post the pinned "Welcome and rules" thread from the system account (once; --force for a new one).'

    def add_arguments(self, parser):
        parser.add_argument("--board", help="Board slug (default: the first active board).")
        parser.add_argument("--force", action="store_true", help="Post a new welcome thread and unpin the old one.")

    def handle(self, *args, board=None, force=False, **options):
        target = None
        if board:
            target = Board.objects.filter(slug=board, is_active=True).first()
            if target is None:
                raise CommandError(f"No active board with the slug {board!r}.")
        thread, created = post_welcome(target, force=force)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Posted and pinned: {thread.get_absolute_url()}"))
        else:
            self.stdout.write(f"A welcome thread already exists: {thread.get_absolute_url()} (use --force for a new one).")
