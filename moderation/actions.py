"""Moderation decisions, in one place. The admin actions, the admin forms and the tests all use these.

Each function changes the state and writes an AuditLog entry (CLAUDE.md section 11). They return True
when something changed, so a repeated click does not log twice.
"""
from django.utils import timezone

from projects.models import Project

from . import audit
from .models import Report


def hide_project(project, actor):
    if project.status == Project.Status.HIDDEN:
        return False
    previous = project.status
    project.status = Project.Status.HIDDEN
    project.save(update_fields=["status", "updated_at"])
    audit.log("moderation.project.hidden", project, actor=actor, previous_status=previous)
    return True


def unhide_project(project, actor):
    """Back to published when the project was ever launched, otherwise back to a draft."""
    if project.status != Project.Status.HIDDEN:
        return False
    project.status = Project.Status.PUBLISHED if project.launched_at else Project.Status.DRAFT
    project.save(update_fields=["status", "updated_at"])
    audit.log("moderation.project.unhidden", project, actor=actor, new_status=project.status)
    return True


def suspend_user(user, actor):
    if user.is_suspended:
        return False
    user.is_suspended = True
    user.save(update_fields=["is_suspended"])
    audit.log("moderation.user.suspended", user, actor=actor)
    return True


def unsuspend_user(user, actor):
    if not user.is_suspended:
        return False
    user.is_suspended = False
    user.save(update_fields=["is_suspended"])
    audit.log("moderation.user.unsuspended", user, actor=actor)
    return True


def resolve_report(report, actor):
    if report.status == Report.Status.RESOLVED:
        return False
    report.status = Report.Status.RESOLVED
    report.handled_by = actor
    report.handled_at = timezone.now()
    report.save(update_fields=["status", "handled_by", "handled_at"])
    audit.log("moderation.report.resolved", report, actor=actor, reason=report.reason, reported=report.target_repr)
    return True
