"""Сповіщення в застосунку про відповіді.

In-app reply notifications: "someone replied to your thread / to your reply". No email, no push.

The header shows a mark while `User.community_notified_at` is set (no query: the user row is loaded anyway).
Opening /community/notifications/ lists them, marks them read and clears the mark.
"""
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from . import limits
from .models import ReplyNotification


def recipient_for(thread, answered):
    """Кому сповіщати про відповідь.

    Who hears about a reply: the author of the reply being answered, else the thread's author.
    `answered` is the reply the person clicked "Reply" on (before the depth limit moves it up a level)."""
    if answered is not None:
        return answered.author, ReplyNotification.Kind.REPLY
    return thread.author, ReplyNotification.Kind.THREAD


def notify(reply, recipient, kind):
    """Створює сповіщення (не собі й не видаленим акаунтам).

    Nobody is told about their own reply, and a deleted or deactivated account is told nothing."""
    if recipient is None or recipient.pk == reply.author_id or not recipient.is_active:
        return None
    now = timezone.now()
    try:
        with transaction.atomic():
            notification = ReplyNotification.objects.create(recipient=recipient, reply=reply, kind=kind, created_at=now)
    except IntegrityError:
        return None
    get_user_model().objects.filter(pk=recipient.pk).update(community_notified_at=now)
    return notification


def inbox(user):
    """Сповіщення людини, нові спершу."""
    return (
        ReplyNotification.objects.visible().filter(recipient=user)
        .select_related("reply__author", "reply__thread").order_by("-created_at", "-pk")
    )


def mark_all_read(user):
    """Позначає всі сповіщення прочитаними."""
    now = timezone.now()
    ReplyNotification.objects.filter(recipient=user, read_at__isnull=True).update(read_at=now)
    if user.community_notified_at is not None:
        get_user_model().objects.filter(pk=user.pk).update(community_notified_at=None)
        user.community_notified_at = None


def prune(now=None):
    """Видаляє сповіщення, старші за термін зберігання.

    Delete notifications older than the retention period. Returns how many."""
    cutoff = (now or timezone.now()) - limits.NOTIFICATION_RETENTION
    deleted, _rows = ReplyNotification.objects.filter(created_at__lt=cutoff).delete()
    return deleted
