"""Account deletion (CLAUDE.md section 12). Irreversible.

Deleting the User row cascades to: projects (with screenshots and their files, build log,
repository link, domain verifications, uptime checks, likes on them), the user's likes and follows,
the GitHub account link and stored email addresses. The username is free again afterwards.

Kept, without the person: reports they made (reporter emptied), reports about them or their
projects (the target becomes empty; the readable name stays for moderation), AuditLog entries.
"""
from django.db import transaction

from moderation.models import AuditLog, Report


def delete_account(user):
    """Delete `user` and everything they own. Returns the AuditLog entry."""
    with transaction.atomic():
        user_id = user.pk
        project_count = user.projects.count()
        anonymized = Report.objects.filter(reporter=user).update(reporter=None)
        # No username or email in the entry: the account is gone, only the fact that it was deleted stays.
        entry = AuditLog.objects.create(
            actor=None,
            action="account.deleted",
            target_type=user._meta.label_lower,
            target_id=str(user_id),
            target_repr=f"deleted user #{user_id}",
            metadata={"projects_deleted": project_count, "reports_anonymized": anonymized},
        )
        user.delete()
    return entry
