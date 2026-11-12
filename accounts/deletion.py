"""Account deletion (CLAUDE.md section 12). Irreversible.

Deleting the User row cascades to: projects (with screenshots and their files, build log,
repository link, domain verifications, uptime checks, likes on them), the user's likes and follows,
the GitHub account link and stored email addresses. The username is free again afterwards.

Kept, without the person: reports they made (reporter emptied), reports about them or their
projects (the target becomes empty; the readable name stays for moderation), AuditLog entries.

Community (runs whether or not COMMUNITY_ENABLED is on): the person's images are deleted from storage, their
votes are taken back, their threads that nobody else replied to are deleted. Threads other people replied to and
all of the person's replies stay with their text and no author (shown as "[deleted]", no picture, no link).
"""
from django.db import transaction
from django.db.models import Exists, F, OuterRef

from community.images import delete_images
from community.models import Reply, Thread, Vote
from moderation.models import AuditLog, Report


def _clear_community(user):
    """Returns the numbers for the AuditLog entry. The rows that stay lose their author when the user row goes
    (SET_NULL)."""
    images = delete_images(uploader=user)
    Thread.objects.filter(pk__in=Vote.objects.filter(user=user, thread__isnull=False).values("thread")).update(score=F("score") - 1)
    Reply.objects.filter(pk__in=Vote.objects.filter(user=user, reply__isnull=False).values("reply")).update(score=F("score") - 1)
    others = Reply.objects.filter(thread=OuterRef("pk")).exclude(author=user)
    lonely = Thread.objects.filter(author=user).filter(~Exists(others))
    deleted_threads = lonely.count()
    for thread in lonely:  # one by one: the rows cascade to their own replies, votes and images
        thread.delete()
    return {
        "community_images_deleted": images,
        "community_threads_deleted": deleted_threads,
        "community_threads_anonymized": Thread.objects.filter(author=user).count(),
        "community_replies_anonymized": Reply.objects.filter(author=user).count(),
    }


def delete_account(user):
    """Delete `user` and everything they own. Returns the AuditLog entry."""
    with transaction.atomic():
        user_id = user.pk
        project_count = user.projects.count()
        anonymized = Report.objects.filter(reporter=user).update(reporter=None)
        community = _clear_community(user)
        # No username or email in the entry: the account is gone, only the fact that it was deleted stays.
        entry = AuditLog.objects.create(
            actor=None,
            action="account.deleted",
            target_type=user._meta.label_lower,
            target_id=str(user_id),
            target_repr=f"deleted user #{user_id}",
            metadata={"projects_deleted": project_count, "reports_anonymized": anonymized, **community},
        )
        user.delete()
    return entry
