from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from unfold.decorators import action

from moderation import audit
from moderation.adminbase import ReadOnlyModelAdmin

from .domain import reverify
from .models import DomainVerification, RepoLink, UptimeCheck

RERUN_LIMIT = 20  # each one is a network request; bigger batches belong to the cron command


@admin.register(RepoLink)
class RepoLinkAdmin(ReadOnlyModelAdmin):
    list_display = ("repo_full_name", "project", "is_owner", "user_commit_count", "checked_at")
    list_filter = ("is_owner", "checked_at")
    search_fields = ("repo_full_name", "project__name", "project__owner__username")
    list_select_related = ("project", "project__owner")


@admin.register(DomainVerification)
class DomainVerificationAdmin(ReadOnlyModelAdmin):
    list_display = ("domain", "project", "method", "status", "verified_at", "last_confirmed_at", "last_error")
    list_filter = ("status", "method", "last_confirmed_at")
    search_fields = ("domain", "project__name", "project__owner__username")
    list_select_related = ("project", "project__owner")
    exclude = ("token",)  # a secret per project: no need to show it
    actions = ["rerun"]

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
            messages.warning(request, _("%(count)s row(s) skipped: not verified, or over the limit of %(limit)s.")
                             % {"count": skipped, "limit": RERUN_LIMIT})


@admin.register(UptimeCheck)
class UptimeCheckAdmin(ReadOnlyModelAdmin):
    list_display = ("project", "checked_at", "ok", "status_code", "response_ms", "error")
    list_filter = ("ok", "checked_at")
    search_fields = ("project__name", "project__owner__username")
    list_select_related = ("project", "project__owner")
    date_hierarchy = "checked_at"
