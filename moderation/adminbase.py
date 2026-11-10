"""Shared admin pieces: every destructive or moderating step writes an AuditLog entry."""
from unfold.admin import ModelAdmin

from . import audit


class AuditedModelAdmin(ModelAdmin):
    """Logs deletes made in the admin. Subclasses log their own status changes."""

    def delete_model(self, request, obj):
        audit.log("admin.deleted", obj, actor=request.user, model=obj._meta.label_lower)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            audit.log("admin.deleted", obj, actor=request.user, model=obj._meta.label_lower)
        super().delete_queryset(request, queryset)


class ReadOnlyModelAdmin(ModelAdmin):
    """List and view only: for facts the system writes (checks, logs)."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
