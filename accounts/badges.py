"""Видача й зняття бейджів (official, moderator) з записом у AuditLog.

Granting and revoking badges. The admin and `manage.py grant_badge` both go through here, so every
change writes the same AuditLog entry ("badge.granted" / "badge.revoked")."""
from django.db import IntegrityError, transaction

from moderation import audit

from .models import UserBadge
from .roles import forget_badges


def grant(user, kind, actor=None, note="", via="admin"):
    """Видає бейдж; None, якщо він уже є.

    Returns the new badge, or None when the user already has it."""
    try:
        with transaction.atomic():
            badge = UserBadge.objects.create(user=user, kind=kind, granted_by=actor, note=note)
    except IntegrityError:
        return None
    forget_badges(user)
    audit.log("badge.granted", user, actor=actor, kind=kind, note=note, via=via)
    return badge


def revoke(user, kind, actor=None, via="admin"):
    """Знімає бейдж; True, якщо було що знімати.

    Returns True when a badge was removed."""
    deleted, _rows = UserBadge.objects.filter(user=user, kind=kind).delete()
    forget_badges(user)
    if deleted:
        audit.log("badge.revoked", user, actor=actor, kind=kind, via=via)
    return bool(deleted)


def log_saved(badge, actor, created, via="admin"):
    """Пише в AuditLog бейдж, який форма адмінки зберегла сама.

    For admin forms that save the row themselves."""
    forget_badges(badge.user)
    audit.log("badge.granted" if created else "badge.changed", badge.user, actor=actor,
              kind=badge.kind, note=badge.note, via=via)


def log_deleted(badge, actor, via="admin"):
    forget_badges(badge.user)
    audit.log("badge.revoked", badge.user, actor=actor, kind=badge.kind, via=via)
