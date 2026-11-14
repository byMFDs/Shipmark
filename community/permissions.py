"""Хто може писати і скільки; views питають тут.

Who may post, and how much. Views ask here; the numbers are in community/limits.py.

Roles come from accounts.roles (muted, suspended and banned people cannot write; moderators are the moderator
badge or a superuser). The account-age rules do not apply to moderators.
"""
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts.roles import can_moderate, can_write
from moderation.pages import write_blocked_message
from moderation.visibility import is_hidden_user

from . import limits


def account_age(user):
    return timezone.now() - user.date_joined


def is_too_new(user):
    """Акаунт молодший 10 хвилин: ще не пише й не голосує.

    Under 10 minutes old: cannot post or vote yet."""
    return not can_moderate(user) and account_age(user) < limits.MIN_ACCOUNT_AGE


def is_young(user):
    """Акаунт молодший 24 годин: одне посилання, без картинок.

    Under 24 hours old: one link per post, no images."""
    return not can_moderate(user) and account_age(user) < limits.YOUNG_ACCOUNT_AGE


def post_block(user):
    """Чому людина зараз не може писати, або "".

    Why `user` cannot post or vote right now, or "" when they can."""
    if not can_write(user):
        return write_blocked_message(user)
    if is_too_new(user):
        return _("Your account is a few minutes old. You can post and vote 10 minutes after signing up.")
    return ""


def author_hidden(author):
    """Автор призупинений або забанений.

    Suspended or banned (a deleted account, None, is not hidden: its posts stay as "[deleted]")."""
    return author is not None and is_hidden_user(author)


def can_see_thread(user, thread):
    """Хто бачить тему залежно від її статусу.

    Public threads for everyone; a removed thread for its author and moderators; anything for moderators."""
    if can_moderate(user):
        return True
    if not thread.board.is_active or author_hidden(thread.author):
        return False
    if thread.is_removed:
        return bool(getattr(user, "pk", None)) and thread.author_id == user.pk
    return not (thread.is_deleted and thread.reply_count == 0)


def can_reply(user, thread):
    """Хто може відповідати в темі залежно від її статусу.

    A published thread accepts replies; a locked one only from moderators; a removed one from nobody."""
    if thread.is_removed:
        return False
    return not thread.is_locked or can_moderate(user)
