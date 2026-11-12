"""Moderator decisions from /mod/: dismiss, remove a project, clear profile fields, mute, ban.

Every decision needs a reason that the affected person sees (notice, banner or ban page), checks who may act
on whom (sanctions.check_target), resolves the linked report and writes AuditLog. The reporter is never named
to the reported person. Restore and purge are superuser-only.
"""
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from projects.models import Project

from . import audit, sanctions
from .models import OPEN_STATES, Notice, Report, Sanction

DISMISS, REMOVE_PROJECT, CLEAR_PROFILE, MUTE, BAN = "dismiss", "remove_project", "clear_profile", "mute", "ban"
PROFILE_FIELDS = ("avatar", "bio", "links")


def notify(user, kind, target_repr, reason=""):
    if user is None or not user.pk:
        return None
    return Notice.objects.create(user=user, kind=kind, target_repr=str(target_repr)[:200], reason=reason)


def _close(report, actor, status, note):
    report.status = status
    report.resolution_note = note
    report.handled_by = actor
    report.handled_at = timezone.now()
    report.save(update_fields=["status", "resolution_note", "handled_by", "handled_at"])
    audit.log(f"moderation.report.{status}", report, actor=actor, reason=report.reason, note=note,
              reported=report.target_repr)


def _close_open_reports(report, actor, note, **target):
    """The linked report, and every other open report about the same thing, are resolved together."""
    if report is not None and report.is_open:
        _close(report, actor, Report.Status.RESOLVED, note)
        notify(report.reporter, Notice.Kind.REPORT_ACTIONED, report.target_repr)
    if target:
        for other in Report.objects.filter(status__in=OPEN_STATES, **target).select_related("reporter"):
            _close(other, actor, Report.Status.RESOLVED, note)
            notify(other.reporter, Notice.Kind.REPORT_ACTIONED, other.target_repr)


def dismiss(report, actor, reason):
    if not report.is_open:
        return False
    with transaction.atomic():
        _close(report, actor, Report.Status.DISMISSED, reason)
        notify(report.reporter, Notice.Kind.REPORT_DISMISSED, report.target_repr, reason)
    return True


def remove_project(project, actor, reason, report=None):
    sanctions.check_target(project.owner, actor)
    if project.status == Project.Status.REMOVED:
        return False
    with transaction.atomic():
        previous = project.status
        project.status = Project.Status.REMOVED
        project.removed_reason = reason
        project.removed_at = timezone.now()
        project.removed_by = actor
        project.save(update_fields=["status", "removed_reason", "removed_at", "removed_by", "updated_at"])
        audit.log("moderation.project.removed", project, actor=actor, reason=reason, previous_status=previous,
                  report=getattr(report, "pk", None))
        notify(project.owner, Notice.Kind.PROJECT_REMOVED, project.name, reason)
        _close_open_reports(report, actor, reason, project=project)
    return True


def restore_project(project, actor):
    """Superuser only: back to published when it was ever launched, otherwise to a draft."""
    if not actor.is_superuser:
        raise PermissionDenied
    if project.status != Project.Status.REMOVED:
        return False
    project.status = Project.Status.PUBLISHED if project.launched_at else Project.Status.DRAFT
    project.save(update_fields=["status", "updated_at"])  # removed_* stay as history
    audit.log("moderation.project.restored", project, actor=actor, new_status=project.status)
    notify(project.owner, Notice.Kind.PROJECT_RESTORED, project.name)
    return True


def purge_project(project, actor):
    """Superuser only, removed projects only: deletes the project and its files for good."""
    if not actor.is_superuser:
        raise PermissionDenied
    if project.status != Project.Status.REMOVED:
        return False
    audit.log("moderation.project.purged", project, actor=actor, owner=project.owner.username,
              name=project.name, reason=project.removed_reason)
    project.delete()
    return True


def clear_profile(person, fields, actor, reason, report=None):
    """`fields`: some of "avatar" (picture and cover), "bio" (headline and About) and "links" (all links).
    Returns the list of fields that were not empty. Picture files are deleted from disk."""
    from accounts import avatars

    sanctions.check_target(person, actor)
    changed = []
    with transaction.atomic():
        if "avatar" in fields and (person.avatar or person.cover or person.avatar_url):
            had_file = bool(person.avatar or person.cover)
            avatars.remove_avatar(person)
            avatars.remove_cover(person)
            person.avatar_url = ""  # the GitHub address too, so "use my GitHub picture" cannot bring it back
            person.save(update_fields=["avatar", "avatar_source", "cover", "avatar_url"])
            if had_file:
                changed.append("avatar")
        if "bio" in fields and (person.headline or person.about):
            person.headline = person.about = ""
            person.save(update_fields=["headline", "about"])
            changed.append("bio")
        if "links" in fields and person.links.exists():
            person.links.all().delete()
            changed.append("links")
        audit.log("moderation.profile.cleared", person, actor=actor, reason=reason, fields=sorted(fields),
                  changed=changed, report=getattr(report, "pk", None))
        notify(person, Notice.Kind.PROFILE_CLEARED, ", ".join(str(_field_label(f)) for f in fields), reason)
        _close_open_reports(report, actor, reason, target_user=person)
    return changed


def _field_label(field):
    return {"avatar": _("picture and cover"), "bio": _("headline and About"), "links": _("links")}[field]


def sanction(person, kind, actor, reason, length, report=None):
    """Mute or ban. `length` is a timedelta or None (permanent, superusers only)."""
    with transaction.atomic():
        issued = sanctions.issue(person, kind, reason, actor, length=length, report=report, via="mod")
        _close_open_reports(report, actor, reason)
    return issued


KINDS = {MUTE: Sanction.Kind.MUTE, BAN: Sanction.Kind.BAN}
