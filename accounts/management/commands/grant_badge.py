"""Команда grant_badge: видати або зняти бейдж official чи moderator.

python manage.py grant_badge <username> <official|moderator> [--note "..."] [--revoke]

The same as the badge admin (superusers only there); the change is written to AuditLog with no actor
and via="command".
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts import badges
from accounts.models import UserBadge


class Command(BaseCommand):
    """Видає або знімає бейдж користувачу з консолі."""
    help = "Grant or revoke the official or moderator badge."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("kind", choices=UserBadge.Kind.values)
        parser.add_argument("--note", default="", help="Why (kept with the badge and in the audit log).")
        parser.add_argument("--revoke", action="store_true", help="Remove the badge instead.")

    def handle(self, username, kind, note, revoke, **options):
        try:
            user = get_user_model().objects.get(username=username.strip().lower())
        except get_user_model().DoesNotExist:
            raise CommandError(f"No user named {username!r}.") from None
        if revoke:
            done = badges.revoke(user, kind, via="command")
            self.stdout.write(f"Revoked {kind} from {user}." if done else f"{user} did not have the {kind} badge.")
        else:
            done = badges.grant(user, kind, note=note[:200], via="command")
            self.stdout.write(f"Granted {kind} to {user}." if done else f"{user} already has the {kind} badge.")
