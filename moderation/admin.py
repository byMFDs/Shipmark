from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.decorators import action

from . import actions
from .adminbase import AuditedModelAdmin, ReadOnlyModelAdmin
from .models import AuditLog, Report


@admin.register(Report)
class ReportAdmin(AuditedModelAdmin):
    list_display = ("target_repr", "kind", "reason", "status", "reporter", "created_at", "handled_by")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("target_repr", "details", "reporter__username")
    list_select_related = ("reporter", "handled_by", "project", "target_user")
    date_hierarchy = "created_at"
    actions = ["resolve"]
    # Reports are written by the site and changed only through the actions, so every change is logged.
    readonly_fields = ("reporter", "target_link", "target_repr", "reason", "details", "status",
                       "handled_by", "handled_at", "created_at")
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    @admin.display(description=_("Type"))
    def kind(self, obj):
        return _("Project") if obj.project_id else _("Profile")

    @admin.display(description=_("Target"))
    def target_link(self, obj):
        if obj.project_id:
            url = reverse("admin:projects_project_change", args=[obj.project_id])
        elif obj.target_user_id:
            url = reverse("admin:accounts_user_change", args=[obj.target_user_id])
        else:
            return _("%(name)s (deleted)") % {"name": obj.target_repr}
        return format_html('<a href="{}">{}</a>', url, obj.target_repr)

    @action(description=_("Resolve selected reports"), permissions=["change"])
    def resolve(self, request, queryset):
        done = sum(actions.resolve_report(r, request.user) for r in queryset)
        messages.success(request, _("Resolved %(count)s report(s).") % {"count": done})


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyModelAdmin):
    """Append-only: nobody edits or deletes history, not even in the admin."""

    list_display = ("created_at", "action", "target_repr", "actor")
    list_filter = ("action", "created_at")
    search_fields = ("action", "target_repr", "target_id", "actor__username")
    list_select_related = ("actor",)
    date_hierarchy = "created_at"

    def has_delete_permission(self, request, obj=None):
        return False
