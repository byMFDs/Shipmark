"""Видача й зняття санкцій з однаковими правилами в /mod/ і адмінці.

Issuing and revoking sanctions: the rules and the AuditLog entries are the same in /mod/ and the admin.

Who may act on whom (check_target) and for how long (check_length) is decided here, never in a template.
"""
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts.roles import can_moderate, forget_sanctions, is_protected
from accounts.system import is_system

from . import audit, bans
from .models import Sanction


def check_target(target, actor):
    """Чи може модератор діяти щодо цієї людини.

    Raises PermissionDenied when `actor` may not act on `target` (sanction, remove, clear).

    Nobody acts on themselves or the system account. A moderator who is not a superuser never acts on a
    superuser, an official account or another moderator.
    """
    if not getattr(actor, "is_superuser", False) and not can_moderate(actor):
        raise PermissionDenied(_("You cannot moderate."))
    if target.pk == getattr(actor, "pk", None):
        raise PermissionDenied(_("You cannot sanction yourself."))
    if is_system(target):
        raise PermissionDenied(_("The system account cannot be sanctioned."))
    if getattr(actor, "is_superuser", False):
        return
    if target.is_superuser:
        raise PermissionDenied(_("Only a superuser can sanction a superuser."))
    if is_protected(target):
        raise PermissionDenied(_("Only a superuser can act on an official account or a moderator."))


def check_length(kind, length, actor):
    """Чи тривалість санкції в межах дозволеного.

    `length` is a timedelta, or None for permanent. Raises ValidationError outside the limits."""
    if length is None:
        if not getattr(actor, "is_superuser", False):
            raise ValidationError(_("Only a superuser can issue a permanent sanction."), code="permanent")
        return
    if length.total_seconds() <= 0:
        raise ValidationError(_("Choose a length above zero."), code="length")
    if getattr(actor, "is_superuser", False):
        return
    limit = settings.MODERATION_MAX_BAN if kind == Sanction.Kind.BAN else settings.MODERATION_MAX_MUTE
    if length > limit:
        days = int(limit.total_seconds() // 86400)
        if kind == Sanction.Kind.BAN:
            message = _("Moderators can ban for at most %(days)s days.") % {"days": days}
        else:
            message = _("Moderators can mute for at most %(days)s days.") % {"days": days}
        raise ValidationError(message, code="too_long")


def issue(user, kind, reason, actor, length=None, report=None, via="mod"):
    """Видає санкцію, запам'ятовує хеш бану, пише в журнал.

    Checks the rules, creates the sanction, remembers a ban's GitHub hash, logs. Returns the Sanction."""
    check_target(user, actor)
    check_length(kind, length, actor)
    now = timezone.now()
    with transaction.atomic():
        sanction = Sanction.objects.create(
            user=user, kind=kind, reason=reason, starts_at=now, expires_at=now + length if length else None,
            issued_by=actor, report=report,
        )
        on_issued(sanction, actor, via=via)
    return sanction


def on_issued(sanction, actor, via="admin"):
    """Що робиться після видачі санкції (також з адмінки).

    Also used by the admin, which saves the row itself."""
    if sanction.kind == Sanction.Kind.BAN:
        bans.remember(sanction)
    forget_sanctions(sanction.user)
    log_issued(sanction, actor, via=via)


def log_issued(sanction, actor, via="admin"):
    """Пише видачу санкції в AuditLog."""
    audit.log(f"moderation.{sanction.kind}.issued", sanction.user, actor=actor, via=via,
              sanction=sanction.pk, reason=sanction.reason,
              starts_at=sanction.starts_at.isoformat(),
              expires_at=sanction.expires_at.isoformat() if sanction.expires_at else None,
              report=sanction.report_id)


def log_changed(sanction, actor, fields, via="admin"):
    """Пише зміну санкції в AuditLog."""
    bans.sync(sanction)
    forget_sanctions(sanction.user)
    audit.log(f"moderation.{sanction.kind}.changed", sanction.user, actor=actor, via=via,
              sanction=sanction.pk, fields=sorted(fields),
              expires_at=sanction.expires_at.isoformat() if sanction.expires_at else None)


def revoke(sanction, actor, via="admin"):
    """Знімає санкцію (лише суперкористувач).

    Superusers only (the admin checks). Returns True when it changed. Revoked sanctions stay as history."""
    if sanction.revoked_at is not None:
        return False
    sanction.revoked_at = timezone.now()
    sanction.revoked_by = actor
    sanction.save(update_fields=["revoked_at", "revoked_by"])
    bans.sync(sanction)
    forget_sanctions(sanction.user)
    audit.log(f"moderation.{sanction.kind}.revoked", sanction.user, actor=actor, via=via, sanction=sanction.pk)
    return True
