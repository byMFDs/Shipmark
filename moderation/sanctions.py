"""Issuing and revoking sanctions. The admin uses this now; /mod/ (stage 2) will use the same functions,
so the rules and the AuditLog entries are the same everywhere."""
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts.roles import is_official
from accounts.system import is_system

from . import audit
from .models import Sanction


def check_target(target, actor):
    """Nobody sanctions themselves or the system account. Superusers are checked here too (stage 2 adds
    the moderator limits: no superusers, officials, other moderators)."""
    if target.pk == getattr(actor, "pk", None):
        raise PermissionDenied(_("You cannot sanction yourself."))
    if is_system(target):
        raise PermissionDenied(_("The system account cannot be sanctioned."))
    if target.is_superuser and not getattr(actor, "is_superuser", False):
        raise PermissionDenied(_("Only a superuser can sanction a superuser."))
    if is_official(target) and not getattr(actor, "is_superuser", False):
        raise PermissionDenied(_("Only a superuser can sanction an official account."))


def log_issued(sanction, actor, via="admin"):
    audit.log(f"moderation.{sanction.kind}.issued", sanction.user, actor=actor, via=via,
              sanction=sanction.pk, reason=sanction.reason,
              starts_at=sanction.starts_at.isoformat(),
              expires_at=sanction.expires_at.isoformat() if sanction.expires_at else None,
              report=sanction.report_id)


def log_changed(sanction, actor, fields, via="admin"):
    audit.log(f"moderation.{sanction.kind}.changed", sanction.user, actor=actor, via=via,
              sanction=sanction.pk, fields=sorted(fields),
              expires_at=sanction.expires_at.isoformat() if sanction.expires_at else None)


def revoke(sanction, actor, via="admin"):
    """Returns True when it changed. Revoked sanctions stay in the list (history)."""
    if sanction.revoked_at is not None:
        return False
    sanction.revoked_at = timezone.now()
    sanction.revoked_by = actor
    sanction.save(update_fields=["revoked_at", "revoked_by"])
    audit.log(f"moderation.{sanction.kind}.revoked", sanction.user, actor=actor, via=via, sanction=sanction.pk)
    return True


def active_for(user, now=None):
    """Active sanctions of `user`, newest first (stage 2 caches this on the request)."""
    return list(Sanction.objects.active(now).filter(user=user).order_by("-starts_at"))
