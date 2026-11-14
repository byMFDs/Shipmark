"""Рішення персоналу щодо доказів: черга розгляду в адмінці.

Staff decisions on proof: the review queue in the admin. Every decision writes AuditLog.

The owner never sees an accusation: while a link waits, the project shows "waiting for a routine
manual review"; after a revoke or block the mark is simply not there, like any failed check.
"""
from django.db import IntegrityError, transaction
from django.utils import timezone

from moderation import audit

from .models import Block, DomainVerification, RepoLink
from .repo import remove_link


def review_queue():
    return RepoLink.objects.filter(review_state__in=(RepoLink.Review.NEEDS_REVIEW, RepoLink.Review.NEEDS_RECHECK))


def review_queue_badge(request):
    """Лічильник черги розгляду в бічній панелі адмінки.

    Sidebar badge in the admin (config/settings/base.py UNFOLD)."""
    return review_queue().count() or None


def approve(link, actor):
    """Схвалює посилання, що чекає розгляду.

    Staff looked at the review reasons and agrees the mark is fine. Only for "needs review"."""
    if link.review_state != RepoLink.Review.NEEDS_REVIEW:
        return False
    now = timezone.now()
    with transaction.atomic():
        link.review_state = RepoLink.Review.APPROVED
        link.reviewed_by, link.reviewed_at, link.earned_at = actor, now, now
        link.save(update_fields=["review_state", "reviewed_by", "reviewed_at", "earned_at"])
        audit.log("moderation.repo.approved", link.project, actor=actor, repo=link.repo_full_name,
                  reasons=link.review_reasons)
    return True


def revoke_repo(link, actor):
    """Знімає марку «Repo owner» зараз.

    Remove Repo owner now. A later check by the owner starts from the review again."""
    return remove_link(link.project, "revoked_by_staff", actor=actor)


def _block(kind, value, label, actor, reason=""):
    """Створює блокування й пише в журнал."""
    try:
        with transaction.atomic():
            block, created = Block.objects.get_or_create(
                kind=kind, value=str(value), defaults={"label": label, "created_by": actor, "reason": reason})
    except IntegrityError:  # a parallel block of the same thing
        return Block.objects.get(kind=kind, value=str(value)), False
    return block, created


def block_repo(link, actor, reason=""):
    """Блокує репозиторій для всіх проєктів.

    Block this repository (by repo id) for every project, and remove the mark."""
    block, created = _block(Block.Kind.REPO, link.github_repo_id, link.repo_full_name, actor, reason)
    if created:
        audit.log("moderation.repo.blocked", block, actor=actor, repo=link.repo_full_name, repo_id=link.github_repo_id)
    remove_link(link.project, "blocked", actor=actor)
    return block


def revoke_live(row, actor, reason="revoked_by_staff"):
    """Знімає марку Live зараз.

    Remove Live now (the row becomes failed, like a failed re-verification)."""
    if row.status != DomainVerification.Status.VERIFIED:
        return False
    with transaction.atomic():
        row.status = DomainVerification.Status.FAILED
        row.last_error = "blocked_domain" if reason == "blocked" else ""
        row.save(update_fields=["status", "last_error"])
        audit.log("hallmark.live.removed", row.project, actor=actor, domain=row.domain, reason=reason)
    return True


def block_domain(row, actor, reason=""):
    """Блокує домен для всіх проєктів.

    Block this domain (www ignored) for every project, and remove Live."""
    block, created = _block(Block.Kind.DOMAIN, row.domain_key, row.domain, actor, reason)
    if created:
        audit.log("moderation.domain.blocked", block, actor=actor, domain=row.domain_key)
    revoke_live(row, actor, reason="blocked")
    return block
