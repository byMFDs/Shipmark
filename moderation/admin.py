"""Адмінка модерації: скарги, санкції, повідомлення, журнал, хеші банів."""
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from unfold.admin import ModelAdmin
from unfold.decorators import action

from . import actions, sanctions
from .adminbase import AuditedModelAdmin, ReadOnlyModelAdmin
from .models import AuditLog, BannedIdentity, Notice, Report, Sanction


@admin.register(Report)
class ReportAdmin(AuditedModelAdmin):
    """Скарги в адмінці."""
    list_display = ("target_repr", "kind", "reason", "status", "reporter", "created_at", "handled_by")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("target_repr", "details", "reporter__username")
    list_select_related = ("reporter", "handled_by", "project", "target_user", "log_entry")
    date_hierarchy = "created_at"
    actions = ["resolve"]
    # Reports are written by the site and changed only through the actions, so every change is logged.
    readonly_fields = ("reporter", "source", "target_link", "target_owner", "target_repr", "reason", "details",
                       "status", "resolution_note", "handled_by", "handled_at", "created_at")
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    @admin.display(description=_("Type"))
    def kind(self, obj):
        return {"project": _("Project"), "profile": _("Profile"), "entry": _("Build-log entry")}.get(obj.kind, "-")

    @admin.display(description=_("Target"))
    def target_link(self, obj):
        """Посилання на предмет скарги в адмінці."""
        if obj.project_id:
            url = reverse("admin:projects_project_change", args=[obj.project_id])
        elif obj.log_entry_id:
            url = reverse("admin:projects_buildlogentry_change", args=[obj.log_entry_id])
        elif obj.target_user_id:
            url = reverse("admin:accounts_user_change", args=[obj.target_user_id])
        else:
            return _("%(name)s (deleted)") % {"name": obj.target_repr}
        return format_html('<a href="{}">{}</a>', url, obj.target_repr)

    @action(description=_("Resolve selected reports"), permissions=["change"])
    def resolve(self, request, queryset):
        """Дія адмінки: закрити вибрані скарги."""
        done = sum(actions.resolve_report(r, request.user) for r in queryset)
        message = ngettext("Resolved %(count)s report.",
                           "Resolved %(count)s reports.", done)
        messages.success(request, message % {"count": done})


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyModelAdmin):
    """Журнал змін лише для читання.

    Append-only: nobody edits or deletes history, not even in the admin."""

    list_display = ("created_at", "action", "target_repr", "actor")
    list_filter = ("action", "created_at")
    search_fields = ("action", "target_repr", "target_id", "actor__username")
    list_select_related = ("actor",)
    date_hierarchy = "created_at"

    def has_delete_permission(self, request, obj=None):
        return False


class SanctionForm(forms.ModelForm):
    """Форма санкції в адмінці з перевіркою правил.

    Admin form. `actor` is set by SanctionAdmin.get_form; the target rules live in moderation.sanctions."""

    actor = None

    class Meta:
        model = Sanction
        fields = ("user", "kind", "reason", "starts_at", "expires_at", "report")

    def clean(self):
        """Перевіряє, чи можна накласти санкцію на цю людину."""
        data = super().clean()
        user = data.get("user") or getattr(self.instance, "user", None)
        if user is not None and not self.instance.pk:
            try:
                sanctions.check_target(user, self.actor)
            except PermissionDenied as error:
                raise ValidationError(str(error)) from None
        starts, expires = data.get("starts_at"), data.get("expires_at")
        if starts and expires and expires <= starts:
            self.add_error("expires_at", _("The end must be after the start."))
        return data


class SanctionStateFilter(admin.SimpleListFilter):
    """Фільтр санкцій за станом."""
    title = _("state")
    parameter_name = "state"

    def lookups(self, request, model_admin):
        return [("active", _("Active")), ("scheduled", _("Scheduled")), ("expired", _("Expired")),
                ("revoked", _("Revoked"))]

    def queryset(self, request, queryset):
        """Санкції в обраному стані."""
        now = timezone.now()
        value = self.value()
        if value == "active":
            return queryset.active(now)
        if value == "scheduled":
            return queryset.filter(revoked_at__isnull=True, starts_at__gt=now)
        if value == "expired":
            return queryset.filter(revoked_at__isnull=True, expires_at__lte=now)
        if value == "revoked":
            return queryset.filter(revoked_at__isnull=False)
        return queryset


@admin.register(Sanction)
class SanctionAdmin(ModelAdmin):
    """Санкції в адмінці: видає й знімає суперкористувач.

    Superusers issue, change and revoke here (any length, also permanent). Other staff only look.
    Sanctions are never deleted, only revoked, so the history stays."""

    form = SanctionForm
    list_display = ("user", "kind", "state_label", "starts_at", "expires_at", "issued_by", "report")
    list_filter = (SanctionStateFilter, "kind", "starts_at")
    search_fields = ("user__username", "reason")
    list_select_related = ("user", "issued_by", "revoked_by", "report")
    autocomplete_fields = ("user",)
    raw_id_fields = ("report",)
    date_hierarchy = "starts_at"
    actions = ["revoke"]
    readonly_fields = ("issued_by", "created_at", "revoked_at", "revoked_by")

    def get_fields(self, request, obj=None):
        fields = ["user", "kind", "reason", "starts_at", "expires_at", "report"]
        return fields + list(self.readonly_fields) if obj else fields

    def get_readonly_fields(self, request, obj=None):
        # The person and the kind never change; revoke and issue a new one instead.
        return self.readonly_fields + (("user", "kind") if obj else ())

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        form.actor = request.user
        return form

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("State"))
    def state_label(self, obj):
        return {"active": _("Active"), "scheduled": _("Scheduled"), "expired": _("Expired"),
                "revoked": _("Revoked")}[obj.state()]

    def save_model(self, request, obj, form, change):
        """Зберігає санкцію, хеш бану й запис в AuditLog."""
        if not change:
            obj.issued_by = request.user
        super().save_model(request, obj, form, change)
        if change:
            if form.changed_data:
                sanctions.log_changed(obj, request.user, form.changed_data)
        else:
            sanctions.on_issued(obj, request.user)

    @action(description=_("Revoke selected sanctions"), permissions=["change"])
    def revoke(self, request, queryset):
        """Дія адмінки: зняти вибрані санкції."""
        done = sum(sanctions.revoke(s, request.user) for s in queryset.select_related("user"))
        message = ngettext("Revoked %(count)s sanction.",
                           "Revoked %(count)s sanctions.", done)
        messages.success(request, message % {"count": done})


@admin.register(Notice)
class NoticeAdmin(ReadOnlyModelAdmin):
    """Повідомлення людям про рішення (лише читання).

    What affected people were told. Written by moderation.decisions only."""

    list_display = ("created_at", "user", "kind", "target_repr", "dismissed_at")
    list_filter = ("kind", "created_at")
    search_fields = ("user__username", "target_repr", "reason")
    list_select_related = ("user",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BannedIdentity)
class BannedIdentityAdmin(ReadOnlyModelAdmin):
    """Солені хеші забанених GitHub id (лише читання).

    Salted hashes of banned GitHub ids (never the id). Deleted when the ban ends or is revoked."""

    list_display = ("created_at", "__str__", "hash_scheme", "expires_at", "sanction")
    list_filter = ("hash_scheme",)
    list_select_related = ("sanction",)

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
