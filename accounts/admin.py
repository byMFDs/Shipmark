from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from unfold.decorators import action
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from moderation import actions, audit
from moderation.adminbase import AuditedModelAdmin

from .models import User


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
    readonly_fields = ("last_login", "date_joined", "terms_version_accepted", "terms_accepted_at")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Profile"), {"fields": ("display_name", "bio", "website", "github_login", "avatar_url", "preferred_language", "email")}),
        (_("Moderation"), {"fields": ("is_suspended",)}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Terms and dates"), {"fields": ("terms_version_accepted", "terms_accepted_at", "last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("username", "password1", "password2")}),)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _projects=Count("projects", filter=Q(projects__status="published"), distinct=True),
        )

    @admin.display(description=_("Published projects"), ordering="_projects")
    def project_count(self, obj):
        return obj._projects

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
