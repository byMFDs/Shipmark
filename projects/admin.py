"""Адмінка проєктів: приховати, повернути, відновити, видалити назавжди; теги й інструменти."""
from django.contrib import admin, messages
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from moderation import actions, audit, decisions
from moderation.models import OPEN_STATES
from moderation.adminbase import AuditedModelAdmin

from .models import BuildLogEntry, Project, Screenshot, Tag, Tool


class ScreenshotInline(TabularInline):
    """Скриншоти проєкту на його сторінці в адмінці."""
    model = Screenshot
    extra = 0
    fields = ("image", "order")


@admin.register(Project)
class ProjectAdmin(AuditedModelAdmin):
    """Проєкти в адмінці з діями модерації."""
    list_display = ("name", "owner", "status", "launched_at", "likes", "open_reports", "created_at")
    list_filter = ("status", "owner__is_suspended", "tags", "built_with", "created_at")
    search_fields = ("name", "slug", "tagline", "owner__username", "repo_full_name", "live_url")
    list_select_related = ("owner",)
    raw_id_fields = ("owner",)
    filter_horizontal = ("tags", "built_with")
    date_hierarchy = "created_at"
    actions = ["hide", "unhide", "restore", "purge"]
    inlines = [ScreenshotInline]
    readonly_fields = ("hallmark_summary", "created_at", "updated_at", "removed_reason", "removed_at", "removed_by")
    fieldsets = (
        (None, {"fields": ("owner", "name", "slug", "tagline", "status")}),
        (_("Removed by a moderator"), {"fields": ("removed_reason", "removed_at", "removed_by")}),
        (_("Content"), {"fields": ("description", "live_url", "repo_full_name", "tags", "built_with")}),
        (_("Proof"), {"fields": ("hallmark_summary",)}),
        (_("Dates"), {"fields": ("launched_at", "created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        """Проєкти з кількістю скриншотів і записів журналу."""
        return super().get_queryset(request).annotate(
            _likes=Count("likes", distinct=True),
            _open_reports=Count("reports", filter=Q(reports__status__in=OPEN_STATES), distinct=True),
        )

    @admin.display(description=_("Likes"), ordering="_likes")
    def likes(self, obj):
        return obj._likes

    @admin.display(description=_("Open reports"), ordering="_open_reports")
    def open_reports(self, obj):
        return obj._open_reports

    @admin.display(description=_("Hallmarks (computed now)"))
    def hallmark_summary(self, obj):
        if not obj.pk:
            return "-"
        return ", ".join(f"{h.kind}: {'yes' if h.earned else 'no'}" for h in obj.hallmarks)

    def save_model(self, request, obj, form, change):
        """Зберігає проєкт; зміна статусу йде в AuditLog."""
        super().save_model(request, obj, form, change)
        if change and "status" in form.changed_data:
            old = form.initial.get("status")
            audit.log("moderation.project.status_changed", obj, actor=request.user,
                      previous_status=old, new_status=obj.status, via="form")

    @action(description=_("Hide selected projects"), permissions=["change"])
    def hide(self, request, queryset):
        """Дія адмінки: приховати вибрані проєкти."""
        done = sum(actions.hide_project(p, request.user) for p in queryset.select_related("owner"))
        message = ngettext("Hid %(count)s project.",
                           "Hid %(count)s projects.", done)
        messages.success(request, message % {"count": done})

    @action(description=_("Unhide selected projects"), permissions=["change"])
    def unhide(self, request, queryset):
        """Дія адмінки: повернути приховані проєкти."""
        done = sum(actions.unhide_project(p, request.user) for p in queryset.select_related("owner"))
        message = ngettext("Made %(count)s project visible again.",
                           "Made %(count)s projects visible again.", done)
        messages.success(request, message % {"count": done})

    @action(description=_("Restore selected removed projects"), permissions=["superuser"])
    def restore(self, request, queryset):
        """Дія адмінки: відновити прибрані проєкти (лише суперкористувач)."""
        done = sum(decisions.restore_project(p, request.user) for p in queryset.select_related("owner"))
        message = ngettext("Restored %(count)s project.",
                           "Restored %(count)s projects.", done)
        messages.success(request, message % {"count": done})

    @action(description=_("Purge selected removed projects (deletes them for good)"), permissions=["superuser"])
    def purge(self, request, queryset):
        """Дія адмінки: видалити прибрані проєкти назавжди (лише суперкористувач)."""
        done = sum(decisions.purge_project(p, request.user) for p in queryset.select_related("owner"))
        message = ngettext("Deleted %(count)s removed project for good.",
                           "Deleted %(count)s removed projects for good.", done)
        messages.success(request, message % {"count": done})

    def has_superuser_permission(self, request):
        """Відновлення й остаточне видалення лише для суперкористувача.

        Restore and purge: superusers only (moderators never reach the admin's actions)."""
        return request.user.is_active and request.user.is_superuser


@admin.register(BuildLogEntry)
class BuildLogEntryAdmin(AuditedModelAdmin):
    """Записи журналу збірки в адмінці."""
    list_display = ("project", "kind", "short_text", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("text", "project__name", "project__owner__username")
    list_select_related = ("project", "project__owner")
    raw_id_fields = ("project",)

    @admin.display(description=_("Text"))
    def short_text(self, obj):
        return obj.text[:80]


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """Теги в адмінці."""
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tool)
class ToolAdmin(ModelAdmin):
    """AI-інструменти в адмінці."""
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
