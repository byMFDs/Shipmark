"""Адмінка користувачів і бейджів: ролі, призупинення, журнал змін."""
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from moderation import actions, audit
from moderation.adminbase import AuditedModelAdmin

from projects.images import clean_avatar, clean_cover

from . import avatars, badges
from .models import ProfileLink, User, UserBadge
from .roles import can_manage_badges, can_set_official_pictures
from .usernames import RESERVED_USERNAMES

PICTURE_FIELDS = ("avatar_upload", "remove_avatar", "cover_upload", "remove_cover")
RAW_PICTURE_FIELDS = ("avatar", "avatar_source", "cover", "avatar_url")  # never edited as raw values: see UserAdmin


class BadgePermissions:
    """Права на бейджі в адмінці: змінює лише суперкористувач, інші лише дивляться.

    Badges: superusers grant, change and revoke; other staff only look (CLAUDE: one source, accounts.roles)."""

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request, obj=None):
        return can_manage_badges(request.user)

    def has_change_permission(self, request, obj=None):
        return can_manage_badges(request.user)

    def has_delete_permission(self, request, obj=None):
        return can_manage_badges(request.user)


class UserBadgeInline(BadgePermissions, TabularInline):
    """Бейджі користувача прямо на його сторінці в адмінці."""
    model = UserBadge
    fk_name = "user"
    extra = 0
    fields = ("kind", "note", "granted_by", "granted_at")
    readonly_fields = ("granted_by", "granted_at")
    verbose_name = _("badge")
    verbose_name_plural = _("Badges (only superusers can change these)")


class ProfileLinkInline(TabularInline):
    """Посилання профілю на сторінці користувача в адмінці."""
    model = ProfileLink
    fk_name = "user"
    extra = 0
    fields = ("kind", "url", "order")


@admin.register(UserBadge)
class UserBadgeAdmin(BadgePermissions, ModelAdmin):
    """Окремий список бейджів в адмінці."""
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
        """Запам'ятовує, хто видав бейдж, і пише це в AuditLog."""
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
    """Форма створення користувача в адмінці."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)


class UserEditForm(UserChangeForm):
    """Форма редагування користувача в адмінці.

    Besides the usual fields: picture uploads for official and system accounts. UserAdmin.get_form removes them
    for everyone who may not use them; the pictures pass through the same pipeline as Settings uploads."""
    avatar_upload = forms.FileField(
        required=False, label=_("Upload a picture"),
        widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}),
        help_text=_("PNG, JPEG or WebP, up to 5 MB. It is cropped to a square."),
    )
    remove_avatar = forms.BooleanField(required=False, label=_("Remove the avatar (show initials)"))
    cover_upload = forms.FileField(
        required=False, label=_("Cover image"),
        widget=forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}),
        help_text=_("Optional. PNG, JPEG or WebP, up to 5 MB. It is cropped to a wide banner (3:1)."),
    )
    remove_cover = forms.BooleanField(required=False, label=_("Remove the cover image"))

    class Meta(UserChangeForm.Meta):
        model = User

    def _picture(self, field, cleaner):
        upload = self.cleaned_data.get(field)
        if not upload:
            return None
        try:
            return cleaner(upload)
        except ValidationError as error:
            self.add_error(field, error)
        return None

    def clean(self):
        """Прогоняє завантажені картинки через спільний конвеєр зображень."""
        data = super().clean()
        self.avatar_content = self._picture("avatar_upload", clean_avatar) if "avatar_upload" in self.fields else None
        self.cover_content = self._picture("cover_upload", clean_cover) if "cover_upload" in self.fields else None
        return data


@admin.register(User)
class UserAdmin(AuditedModelAdmin, BaseUserAdmin):
    """Користувачі в адмінці: пошук, бейджі, призупинення з записом у AuditLog."""
    form = UserEditForm
    add_form = UserAddForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("username", "display_name", "github_login", "is_suspended", "is_staff", "project_count", "date_joined")
    list_filter = ("is_suspended", "is_staff", "is_superuser", "preferred_language", "date_joined")
    search_fields = ("username", "display_name", "github_login", "email")
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"
    actions = ["suspend", "unsuspend"]
    inlines = [UserBadgeInline, ProfileLinkInline]
    readonly_fields = ("last_login", "date_joined", "terms_version_accepted", "terms_accepted_at")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Profile"), {"fields": ("display_name", "headline", "about", "location", "status", "github_login", "preferred_language", "email")}),
        (_("Pictures"), {"fields": ("avatar", "avatar_source", "cover", "avatar_url", *PICTURE_FIELDS)}),
        (_("Moderation"), {"fields": ("is_suspended",)}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Terms and dates"), {"fields": ("terms_version_accepted", "terms_accepted_at", "last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("username", "password1", "password2")}),)

    def get_readonly_fields(self, request, obj=None):
        """Не-суперкористувач не може змінювати ролі й права персоналу."""
        # Only superusers change roles. Otherwise staff with "change user" could make themselves superuser
        # and so reach everything that is superuser-only (badges, permanent sanctions).
        # The stored picture values are read-only for everyone: they change only through the upload fields below
        # (the image pipeline), never as raw text.
        fields = tuple(super().get_readonly_fields(request, obj)) + RAW_PICTURE_FIELDS
        if obj is not None and obj.username in RESERVED_USERNAMES:
            # The system account ("shipmark") has a reserved name that the username validator refuses, so its
            # form could never be saved; the name of a reserved account is not editable anyway.
            fields += ("username",)
        if not request.user.is_superuser:
            fields = tuple(fields) + ("is_staff", "is_superuser", "groups", "user_permissions")
        return fields

    def get_fieldsets(self, request, obj=None):
        """Поля завантаження картинок показуються лише суперкористувачу на офіційному чи системному акаунті."""
        fieldsets = super().get_fieldsets(request, obj)
        if obj is not None and can_set_official_pictures(request.user, obj):
            return fieldsets
        return [(name, {**options, "fields": tuple(f for f in options["fields"] if f not in PICTURE_FIELDS)})
                for name, options in fieldsets]

    def get_form(self, request, obj=None, **kwargs):
        """Прибирає поля завантаження картинок, якщо їх не можна використовувати.

        Removing them from the class means a hand-made POST cannot use them either."""
        form = super().get_form(request, obj, **kwargs)
        if obj is None or not can_set_official_pictures(request.user, obj):
            for name in PICTURE_FIELDS:
                form.base_fields.pop(name, None)
        return form

    def has_change_permission(self, request, obj=None):
        """Системний акаунт змінює лише суперкористувач.

        The system account (official author of news and notices) is changed by superusers only; other staff see it
        read-only, whatever their model permissions say."""
        if obj is not None and obj.is_system_account and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Системний акаунт не видаляє ніхто."""
        # Nobody deletes the system account: news and community notices keep their author.
        if obj is not None and obj.is_system_account:
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        # "Delete selected" checks the permission without an object; keep the system account out of it too.
        super().delete_queryset(request, queryset.exclude(is_system_account=True))

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _projects=Count("projects", filter=Q(projects__status="published"), distinct=True),
        )

    @admin.display(description=_("Published projects"), ordering="_projects")
    def project_count(self, obj):
        return obj._projects

    def save_formset(self, request, form, formset, change):
        """Рядки бейджів з inline: хто видав і запис у AuditLog.

        Badge rows from the inline: set who granted them and write AuditLog, like the badge admin does."""
        if formset.model is not UserBadge:
            return super().save_formset(request, form, formset, change)
        if not can_manage_badges(request.user):  # read-only inline; never save posted rows
            # The admin reads these lists to write its change message; without them every save by staff 500s.
            formset.new_objects, formset.changed_objects, formset.deleted_objects = [], [], []
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
        """Зберігає користувача; зміна «призупинено» йде в AuditLog."""
        # Editing the checkbox in the form is a moderation step too: log it like the actions do.
        changed = []
        if change and can_set_official_pictures(request.user, obj):
            changed = self._save_pictures(obj, form)
        super().save_model(request, obj, form, change)
        if changed:
            audit.log("accounts.official_pictures", obj, actor=request.user, via="admin", changed=changed)
        if change and "is_suspended" in form.changed_data:
            audit.log("moderation.user.suspended" if obj.is_suspended else "moderation.user.unsuspended",
                      obj, actor=request.user, via="form")

    def _save_pictures(self, obj, form):
        """Застосовує завантажену чи видалену картинку; повертає, що змінено.

        Same storage code as Settings (accounts.avatars): random file name, old file removed after commit."""
        changed = []
        if form.avatar_content is not None:
            avatars.set_avatar(obj, form.avatar_content, User.AvatarSource.UPLOAD)
            changed.append("avatar")
        elif form.cleaned_data.get("remove_avatar") and obj.avatar:
            avatars.remove_avatar(obj)
            changed.append("avatar_removed")
        if form.cover_content is not None:
            avatars.set_cover(obj, form.cover_content)
            changed.append("cover")
        elif form.cleaned_data.get("remove_cover") and obj.cover:
            avatars.remove_cover(obj)
            changed.append("cover_removed")
        return changed

    @action(description=_("Suspend selected users"), permissions=["change"])
    def suspend(self, request, queryset):
        """Дія адмінки: призупинити вибраних (крім себе й суперкористувачів)."""
        done = 0
        for user in queryset:
            if user.pk == request.user.pk or user.is_superuser or user.is_system_account:
                messages.warning(request, _("Skipped %(name)s: staff cannot suspend themselves or a superuser.") % {"name": user})
                continue
            done += actions.suspend_user(user, request.user)
        message = ngettext("Suspended %(count)s user. Their projects are hidden everywhere.",
                           "Suspended %(count)s users. Their projects are hidden everywhere.", done)
        messages.success(request, message % {"count": done})

    @action(description=_("Unsuspend selected users"), permissions=["change"])
    def unsuspend(self, request, queryset):
        """Дія адмінки: зняти призупинення з вибраних."""
        done = sum(actions.unsuspend_user(user, request.user) for user in queryset)
        message = ngettext("Unsuspended %(count)s user.",
                           "Unsuspended %(count)s users.", done)
        messages.success(request, message % {"count": done})
