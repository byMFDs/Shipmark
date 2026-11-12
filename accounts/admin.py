from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from moderation import actions, audit
from moderation.adminbase import AuditedModelAdmin

from . import badges
from .models import User, UserBadge
from .roles import can_manage_badges


class BadgePermissions:
    """Badges: superusers grant, change and revoke; other staff only look (CLAUDE: one source, accounts.roles)."""

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request, obj=None):
        return can_manage_badges(request.user)

    def has_change_permission(self, request, obj=None):
        return can_manage_badges(request.user)

    def has_delete_permission(self, request, obj=None):
        return can_manage_badges(request.user)


class UserBadgeInline(BadgePermissions, TabularInline):
    model = UserBadge
    fk_name = "user"
    extra = 0
    fields = ("kind", "note", "granted_by", "granted_at")
    readonly_fields = ("granted_by", "granted_at")
    verbose_name = _("badge")
    verbose_name_plural = _("Badges (only superusers can change these)")


@admin.register(UserBadge)
class UserBadgeAdmin(BadgePermissions, ModelAdmin):
    list_display = ("user", "kind", "granted_by", "granted_at", "note")
    list_filter = ("kind",)
    search_fields = ("user__username", "user__display_name", "note")
    list_select_related = ("user", "granted_by")
    autocomplete_fields = ("user",)
    fields = ("user", "kind", "note", "granted_by", "granted_at")
    readonly_fields = ("granted_by", "granted_at")

    def get_readonly_fields(self, request, obj=None):
        # An existing badge keeps its person and kind; revoke it and grant a new one instead.
        return self.readonly_fields + (("user", "kind") if obj else ())

    def save_model(self, request, obj, form, change):
        if not change:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)
        badges.log_saved(obj, request.user, created=not change)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        badges.log_deleted(obj, request.user)

    def delete_queryset(self, request, queryset):
        for badge in queryset.select_related("user"):
            self.delete_model(request, badge)


class UserAddForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)


class UserEditForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


@admin.register(User)
class UserAdmin(AuditedModelAdmin, BaseUserAdmin):
    form = UserEditForm
    add_form = UserAddForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("username", "display_name", "github_login", "is_suspended", "is_staff", "project_count", "date_joined")
    list_filter = ("is_suspended", "is_staff", "is_superuser", "preferred_language", "date_joined")
    search_fields = ("username", "display_name", "github_login", "email")
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"
    actions = ["suspend", "unsuspend"]
    inlines = [UserBadgeInline]
    readonly_fields = ("last_login", "date_joined", "terms_version_accepted", "terms_accepted_at")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Profile"), {"fields": ("display_name", "bio", "website", "github_login", "avatar_url", "preferred_language", "email")}),
        (_("Moderation"), {"fields": ("is_suspended",)}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Terms and dates"), {"fields": ("terms_version_accepted", "terms_accepted_at", "last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("username", "password1", "password2")}),)

    def get_readonly_fields(self, request, obj=None):
        # Only superusers change roles. Otherwise staff with "change user" could make themselves superuser
        # and so reach everything that is superuser-only (badges, permanent sanctions).
        fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            fields = tuple(fields) + ("is_staff", "is_superuser", "groups", "user_permissions")
        return fields

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _projects=Count("projects", filter=Q(projects__status="published"), distinct=True),
        )

    @admin.display(description=_("Published projects"), ordering="_projects")
    def project_count(self, obj):
        return obj._projects

    def save_formset(self, request, form, formset, change):
        """Badge rows from the inline: set who granted them and write AuditLog, like the badge admin does."""
        if formset.model is not UserBadge:
            return super().save_formset(request, form, formset, change)
        if not can_manage_badges(request.user):  # read-only inline; never save posted rows
            return None
        instances = formset.save(commit=False)
        for badge in formset.deleted_objects:
            badge.delete()
            badges.log_deleted(badge, request.user)
        for badge in instances:
            created = badge.pk is None
            if created:
                badge.granted_by = request.user
            badge.save()
            badges.log_saved(badge, request.user, created=created)
        return None

    def save_model(self, request, obj, form, change):
        # Editing the checkbox in the form is a moderation step too: log it like the actions do.
        super().save_model(request, obj, form, change)
        if change and "is_suspended" in form.changed_data:
            audit.log("moderation.user.suspended" if obj.is_suspended else "moderation.user.unsuspended",
                      obj, actor=request.user, via="form")

    @action(description=_("Suspend selected users"), permissions=["change"])
    def suspend(self, request, queryset):
        done = 0
        for user in queryset:
            if user.pk == request.user.pk or user.is_superuser:
                messages.warning(request, _("Skipped %(name)s: staff cannot suspend themselves or a superuser.") % {"name": user})
                continue
            done += actions.suspend_user(user, request.user)
        messages.success(request, _("Suspended %(count)s user(s). Their projects are hidden everywhere.") % {"count": done})

    @action(description=_("Unsuspend selected users"), permissions=["change"])
    def unsuspend(self, request, queryset):
        done = sum(actions.unsuspend_user(user, request.user) for user in queryset)
        messages.success(request, _("Unsuspended %(count)s user(s).") % {"count": done})
