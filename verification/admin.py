from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from unfold.decorators import action

from moderation import audit
from moderation.adminbase import ReadOnlyModelAdmin

from moderation.adminbase import AuditedModelAdmin

from . import review
from .domain import reverify
from .models import Block, DomainVerification, RepoLink, RepoReview, UptimeCheck
from .repo import RepoCheckError, reverify_link

RERUN_LIMIT = 20  # each one is a network request; bigger batches belong to the cron command


class ModerateMixin:
    """Approve / revoke / block need the change permission (superusers have it), not only view."""

    def has_moderate_permission(self, request):
        return request.user.has_perm("verification.change_repolink")


@admin.register(RepoLink)
class RepoLinkAdmin(ModerateMixin, ReadOnlyModelAdmin):
    list_display = ("repo_full_name", "project", "is_owner", "review_state", "user_commit_count", "checked_at")
    list_filter = ("review_state", "is_owner", "checked_at")
    search_fields = ("repo_full_name", "project__name", "project__owner__username")
    list_select_related = ("project", "project__owner")
    actions = ["approve", "revoke", "block", "rerun"]

    @action(description=_("Approve (the review reasons are fine)"), permissions=["moderate"])
    def approve(self, request, queryset):
        done = sum(review.approve(link, request.user) for link in queryset.select_related("project"))
        messages.success(request, _("Approved %(count)s.") % {"count": done})

    @action(description=_("Revoke Repo owner"), permissions=["moderate"])
    def revoke(self, request, queryset):
        done = sum(review.revoke_repo(link, request.user) for link in list(queryset.select_related("project")))
        messages.success(request, _("Revoked %(count)s.") % {"count": done})

    @action(description=_("Block the repository and revoke Repo owner"), permissions=["moderate"])
    def block(self, request, queryset):
        links = list(queryset.select_related("project"))
        for link in links:
            review.block_repo(link, request.user)
        messages.success(request, _("Blocked %(count)s.") % {"count": len(links)})

    @action(description=_("Re-check on GitHub now"), permissions=["view"])
    def rerun(self, request, queryset):
        outcomes = {"confirmed": 0, "review": 0, "removed": 0, "kept": 0}
        for link in list(queryset.select_related("project", "project__owner")[:RERUN_LIMIT]):
            try:
                outcome = reverify_link(link, actor=request.user)
            except RepoCheckError as exc:
                messages.error(request, exc.message)
                break
            outcomes[outcome] += 1
        messages.success(request, _("Confirmed %(confirmed)s, needs review %(review)s, removed %(removed)s, "
                                    "retry later %(kept)s.") % outcomes)


@admin.register(RepoReview)
class RepoReviewAdmin(RepoLinkAdmin):
    """The review queue: only links waiting for staff (needs review) or for a re-check."""

    list_display = ("repo_full_name", "project", "review_state", "review_reasons", "repo_created_at",
                    "root_commit_at", "user_commit_count", "active_weeks", "checked_at")
    list_filter = ("review_state",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(pk__in=review.review_queue().values("pk"))


@admin.register(Block)
class BlockAdmin(AuditedModelAdmin):
    """Blocks are made by the actions above. Deleting one (logged) unblocks it."""

    list_display = ("kind", "label", "value", "created_by", "created_at")
    list_filter = ("kind",)
    search_fields = ("label", "value")
    readonly_fields = ("kind", "value", "label", "reason", "created_by", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(DomainVerification)
class DomainVerificationAdmin(ReadOnlyModelAdmin):
    list_display = ("domain", "project", "method", "status", "verified_at", "last_confirmed_at", "last_error")
    list_filter = ("status", "method", "last_confirmed_at")
    search_fields = ("domain", "project__name", "project__owner__username")
    list_select_related = ("project", "project__owner")
    exclude = ("token",)  # a secret per project: no need to show it
    actions = ["rerun", "revoke_live", "block_domain"]

    def has_moderate_permission(self, request):
        return request.user.has_perm("verification.change_domainverification")

    @action(description=_("Revoke Domain verified"), permissions=["moderate"])
    def revoke_live(self, request, queryset):
        done = sum(review.revoke_live(row, request.user) for row in queryset.select_related("project"))
        messages.success(request, _("Revoked %(count)s.") % {"count": done})

    @action(description=_("Block the domain and revoke Domain verified"), permissions=["moderate"])
    def block_domain(self, request, queryset):
        rows = list(queryset.select_related("project"))
        for row in rows:
            review.block_domain(row, request.user)
        messages.success(request, _("Blocked %(count)s.") % {"count": len(rows)})

    @action(description=_("Re-run verification now"), permissions=["view"])
    def rerun(self, request, queryset):
        rows = list(queryset.filter(status=DomainVerification.Status.VERIFIED)
                    .select_related("project", "project__owner")[:RERUN_LIMIT])
        skipped = queryset.count() - len(rows)
        outcomes = {"confirmed": 0, "kept": 0, "removed": 0}
        for row in rows:
            outcome = reverify(row)
            outcomes[outcome] += 1
            audit.log("moderation.verification.rerun", row.project, actor=request.user,
                      domain=row.domain, outcome=outcome)
        messages.success(request, _("Confirmed %(confirmed)s, retry later %(kept)s, removed %(removed)s.") % outcomes)
        if skipped:
            messages.warning(request, ngettext("%(count)s row skipped: not verified, or over the limit of %(limit)s.",
                                      "%(count)s rows skipped: not verified, or over the limit of %(limit)s.", skipped)
                             % {"count": skipped, "limit": RERUN_LIMIT})


@admin.register(UptimeCheck)
class UptimeCheckAdmin(ReadOnlyModelAdmin):
    list_display = ("project", "checked_at", "ok", "status_code", "response_ms", "error")
    list_filter = ("ok", "checked_at")
    search_fields = ("project__name", "project__owner__username")
    list_select_related = ("project", "project__owner")
    date_hierarchy = "checked_at"
