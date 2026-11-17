"""Superuser test-data admin: explicit production opt-in and reviewed selective cleanup.

All object mutations recheck registry membership and synthetic identity on the server.
Deletion uses a dependency preview and repeats validation atomically on confirmation.
"""
from django import forms
from django.contrib import admin, messages
from django.core import signing
from django.core.management.base import CommandError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from urllib.parse import urlencode
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.widgets import (UnfoldAdminSelectWidget, UnfoldAdminTextareaWidget, UnfoldAdminTextInputWidget,
                            UnfoldBooleanWidget)

from accounts.forms import SettingsForm
from accounts.models import User
from accounts.usernames import is_taken, validate_username
from moderation import audit

from . import limits, services, testdata, testdata_tools as tools
from .forms import BoardChoiceField, _body, _images
from .images import clean_upload
from .models import Board, TestAccount, TestReply, TestThread


def unfold_widgets(form):
    """Віджети unfold замість стилів сайту, щоб поля виглядали як решта адмінки."""
    for field in form.fields.values():
        old = field.widget
        if isinstance(old, forms.CheckboxInput):
            new = UnfoldBooleanWidget()
        elif isinstance(old, forms.Textarea):
            new = UnfoldAdminTextareaWidget()
        elif isinstance(old, forms.Select) and not isinstance(old, forms.SelectMultiple):
            new = UnfoldAdminSelectWidget()
            new.choices = old.choices
        elif isinstance(old, (forms.TextInput, forms.URLInput)):
            new = UnfoldAdminTextInputWidget()
        else:
            continue  # file inputs stay plain, as on the other admin pages
        new.attrs.update({k: v for k, v in old.attrs.items() if k not in {"class", "aria-describedby"}})
        new.is_required = field.required
        field.widget = new


class TestAdmin(ModelAdmin):
    """Спільні права: усе лише для активного суперкористувача в локальній розробці; видалення немає."""
    def has_module_permission(self, request):
        return tools.can_use(request.user)

    def has_view_permission(self, request, obj=None):
        return tools.can_use(request.user)

    def has_add_permission(self, request):
        return tools.can_use(request.user)

    def has_change_permission(self, request, obj=None):
        return tools.can_use(request.user)

    change_list_template = "admin/community/testdata_change_list.html"
    actions = ["remove_selected_test_data"]

    def has_delete_permission(self, request, obj=None):
        return tools.can_use(request.user)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def get_urls(self):
        name = self.model._meta.model_name
        return [path("cleanup/", self.admin_site.admin_view(self.cleanup_view),
                     name=f"community_{name}_cleanup")] + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, {**(extra_context or {}), "testdata_cleanup_url":
            reverse(f"admin:community_{self.model._meta.model_name}_cleanup")})

    @admin.action(description="Видалити вибрані тестові об’єкти…", permissions=["delete"])
    def remove_selected_test_data(self, request, queryset):
        token = signing.dumps(list(queryset.values_list("pk", flat=True)), salt=self.model._meta.label_lower)
        return HttpResponseRedirect(reverse(f"admin:community_{self.model._meta.model_name}_cleanup")
                                    + "?" + urlencode({"selection": token}))

    def delete_view(self, request, object_id, extra_context=None):
        return self.cleanup_view(request, object_id=object_id)

    def cleanup_view(self, request, object_id=None):
        from .testdata_delete import remove
        if not tools.can_use(request.user):
            raise PermissionDenied
        token = request.POST.get("selection", request.GET.get("selection", ""))
        selection = None
        if object_id is not None:
            try:
                selection = [(tools.label(self.model), int(object_id))]
            except ValueError:
                raise PermissionDenied from None
        elif token:
            try:
                ids = signing.loads(token, salt=self.model._meta.label_lower, max_age=3600)
                selection = [(tools.label(self.model), int(pk)) for pk in ids]
            except (signing.BadSignature, ValueError, TypeError):
                raise PermissionDenied from None
        error, result = None, None
        try:
            result = remove(request.user, selection, execute=request.method == "POST" and request.POST.get("confirm") == "yes")
        except (CommandError, ValidationError, OSError) as exc:
            error = str(exc)
        else:
            if request.method == "POST" and request.POST.get("confirm") == "yes":
                if result["file_failures"]:
                    self.message_user(request, "Записи видалено. Частина файлів залишилася в черзі; повторіть очищення всього набору.", messages.WARNING)
                else:
                    self.message_user(request, "Тестові об’єкти видалено. Лічильники оновлено.", messages.SUCCESS)
                return HttpResponseRedirect(reverse(f"admin:community_{self.model._meta.model_name}_changelist"))
        return TemplateResponse(request, "admin/community/testdata_confirm_delete.html", {
            **self.admin_site.each_context(request), "opts": self.model._meta,
            "title": "Видалення тестових даних", "result": result, "error": error,
            "selection": token, "all_test_data": selection is None,
        })

    def delete_model(self, request, obj):
        # No default Django cascade path may bypass the reviewed deletion service.
        from .testdata_delete import remove
        remove(request.user, [(tools.label(obj), obj.pk)], execute=True)

    def delete_queryset(self, request, queryset):
        from .testdata_delete import remove
        remove(request.user, [(tools.label(self.model), pk) for pk in queryset.values_list("pk", flat=True)], execute=True)

    def get_form(self, request, obj=None, change=False, **kwargs):
        # The form class is used as it is: its fields are not model fields (the admin's factory would refuse them).
        return self.form

    def save_form(self, request, form, change):
        return form.instance  # saved in save_model, through the tools, in the admin's transaction

    def save_related(self, request, form, formsets, change):
        pass  # everything is written by save_model

    def save_model(self, request, obj, form, change):
        """Запис через інструменти; відмова сервера скасовує все."""
        if not tools.can_use(request.user):  # the admin checked already; a second look costs nothing
            raise PermissionDenied
        try:
            testdata.lock_database()
            self.write(request, obj, form, change)
        except ValidationError as error:
            # The checks run again on the server; a refused save leaves the database as it was (the admin's
            # transaction rolls back) and shows a plain error page instead of a half-done change.
            raise PermissionDenied("; ".join(error.messages)) from None


# ---------- Test users ----------

class TestUserForm(SettingsForm):
    """Профіль тестового акаунта: ті самі поля й перевірки, що в Налаштуваннях, плюс ім'я користувача.

    The Settings form (name, headline, location, status, About, language, picture, cover, skills, links) with the
    username added. Pictures go through the same pipeline; the per-person upload limit is not applied (the
    superuser edits many test accounts in a row). Email, password, roles and GitHub are not fields here."""

    username = forms.CharField(
        label=_("Username"), max_length=User._meta.get_field("username").max_length,
        help_text=_("The profile will be at /u/username/. Use small letters, numbers, - and _."),
    )

    class Meta(SettingsForm.Meta):
        model = TestAccount  # so the admin's links after a save stay in this section
        fields = ["username", *SettingsForm.Meta.fields]

    def __init__(self, *args, **kwargs):
        """Форма налаштувань без закріплених проєктів і GitHub, у стилі адмінки."""
        super().__init__(*args, can_edit_profile=True, **kwargs)
        for name in ("pinned", "use_github_avatar"):
            self.fields.pop(name, None)  # test accounts have no projects and no GitHub
        unfold_widgets(self)

    def clean_username(self):
        """Ті самі правила імені, що при реєстрації; зайнятість без урахування регістру."""
        value = self.cleaned_data["username"].strip().lower()
        validate_username(value)
        if is_taken(value, exclude_pk=self.instance.pk):
            raise ValidationError(User._meta.get_field("username").error_messages["unique"], code="unique")
        return value

    def clean(self):
        data = super().clean()
        data["pinned"] = []  # no field here; Settings' save replaces the pins with this (empty) list
        return data

    def _image(self, field, cleaner, limit_name):
        """Картинка через спільний конвеєр, без ліміту частоти для суперкористувача."""
        upload = self.cleaned_data.get(field)
        if not upload:
            return None
        try:
            return cleaner(upload)
        except ValidationError as error:
            self.add_error(field, error)
        return None


@admin.register(TestAccount)
class TestAccountAdmin(TestAdmin):
    """Тестові акаунти: створення, профіль, аватар, перехід на публічний профіль."""
    form = TestUserForm
    list_display = ("username", "display_name", "location", "date_joined", "profile_link")
    search_fields = ("username", "display_name")
    ordering = ("-date_joined", "-pk")
    fieldsets = (
        (None, {"fields": ("username", "display_name", "headline", "location", "status", "about", "preferred_language")}),
        (_("Pictures"), {"fields": ("avatar_file", "remove_avatar", "cover_file", "remove_cover")}),
        (_("Skills and links"), {"fields": ("skills_text", *[f"link{i}_{part}" for i in range(6) for part in ("kind", "url")])}),
    )

    def get_queryset(self, request):
        # Only registered, still synthetic accounts: a real person's id in the URL finds nothing.
        return super().get_queryset(request).filter(pk__in=tools.test_users().values("pk"))

    @admin.display(description=_("Public profile"))
    def profile_link(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener">/u/{}/</a>', self.view_on_site(obj), obj.username)

    def view_on_site(self, obj):
        return reverse("accounts:profile", args=[obj.username])

    def write(self, request, obj, form, change):
        """Створює чи змінює тестовий акаунт і синхронізує реєстр."""
        if change:
            stored = tools.require_test_user(obj)  # the row in the database, checked again
            old_files = [name for name in (stored.avatar.name, stored.cover.name) if name]
        else:
            tools.prepare_new_user(obj)
            old_files = []
        form.save()
        if not change:
            tools.register(obj, tools.admin_run())
        tools.require_test_user(obj)  # still synthetic after the save
        tools.sync_profile(obj, old_files)
        audit.log("testdata.user.saved", obj, actor=request.user, created=not change)

    def response_add(self, request, obj, post_url_continue=None):
        """Після створення відкриває акаунт для подальшого редагування."""
        # Like Django's own user admin: after "Save" a new account opens for more editing.
        if "_addanother" not in request.POST and "_continue" not in request.POST:
            request.POST = request.POST.copy()
            request.POST["_continue"] = 1
        return super().response_add(request, obj, post_url_continue)


# ---------- Test threads ----------

class TestThreadForm(forms.ModelForm):
    """Нова тема: тестовий автор, дошка, заголовок, текст, картинки; зміна — лише текст і заголовок (за правилами)."""
    author = forms.ModelChoiceField(label=_("Author (test account)"), queryset=User.objects.none())
    board = BoardChoiceField(label=_("Board"), queryset=Board.objects.none())
    title = forms.CharField(label=_("Title"), min_length=limits.MIN_TITLE, max_length=limits.MAX_TITLE, strip=True)
    body = _body(10, limits.MAX_THREAD_BODY)
    images = _images(limits.MAX_THREAD_IMAGES)

    class Meta:
        model = TestThread
        fields = []

    def _post_clean(self):
        pass  # the row is written by community.services, not from this form's instance (nothing to validate there)

    def __init__(self, *args, **kwargs):
        """Поля нової теми або (для збереженої) лише текст і заголовок."""
        super().__init__(*args, **kwargs)
        thread = self.instance
        if thread.pk:
            for name in ("author", "board", "images"):
                del self.fields[name]
            self.fields["body"].initial = thread.body
            if services.title_editable(thread):
                self.fields["title"].initial = thread.title
            else:
                del self.fields["title"]  # the site's rule: the title is fixed after 15 minutes
        else:
            self.fields["author"].queryset = tools.test_users().order_by("username")
            self.fields["author"].label_from_instance = lambda u: f"@{u.username} · {u.display_name}" if u.display_name else f"@{u.username}"
            self.fields["board"].queryset = Board.objects.filter(is_active=True)
        unfold_widgets(self)

    def clean_images(self):
        """Перевіряє кількість і кожен файл через конвеєр зображень."""
        files = self.cleaned_data.get("images") or []
        if len(files) > limits.MAX_THREAD_IMAGES:
            raise ValidationError(_("Too many images."))
        return [clean_upload(upload) for upload in files]

    def clean(self):
        """Текст чи картинка обов'язкові; автор — лише тестовий акаунт."""
        data = super().clean()
        has_images = bool(self.instance.pk) and self.instance.images.exists()
        if not data.get("body") and not data.get("images") and not has_images and "images" not in self.errors:
            self.add_error("body", _("Write something or add an image."))
        if data.get("author") is not None:
            try:
                tools.require_test_user(data["author"])
            except ValidationError as error:
                self.add_error("author", error)
        return data


@admin.register(TestThread)
class TestThreadAdmin(TestAdmin):
    """Теми тестових акаунтів."""
    form = TestThreadForm
    list_display = ("title", "board", "author", "reply_count", "status", "created_at")
    list_select_related = ("board", "author")
    search_fields = ("title", "body", "author__username")
    ordering = ("-created_at", "-pk")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(pk__in=tools.registered_ids(TestThread))

    def get_fieldsets(self, request, obj=None):
        return ((None, {"fields": tuple(self.form(instance=obj or TestThread()).fields)}),)

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def write(self, request, obj, form, change):
        """Нова тема через інструменти або зміна тексту наявної."""
        data = form.cleaned_data
        if change:
            tools.edit_thread(obj, data.get("title"), data["body"])
        else:
            created = tools.create_thread(data["author"], data["board"], data["title"], data["body"], data["images"])
            obj.pk = created.pk
        obj.refresh_from_db()
        audit.log("testdata.thread.saved", obj, actor=request.user, created=not change)


# ---------- Test replies ----------

class TestReplyForm(forms.ModelForm):
    """Нова відповідь у тестовій темі (за потреби — на тестову відповідь); зміна — лише текст."""
    author = forms.ModelChoiceField(label=_("Author (test account)"), queryset=User.objects.none())
    thread = forms.ModelChoiceField(label=_("Thread (test thread)"), queryset=TestThread.objects.none())
    parent = forms.ModelChoiceField(
        label=_("Answer to (test reply, optional)"), queryset=TestReply.objects.none(), required=False,
        help_text=_("Leave empty to answer the thread. Replies nest up to three levels; deeper answers attach one level up."),
    )
    body = _body(4, limits.MAX_REPLY_BODY)
    images = _images(limits.MAX_REPLY_IMAGES)

    class Meta:
        model = TestReply
        fields = []

    def _post_clean(self):
        pass  # the row is written by community.services, not from this form's instance (nothing to validate there)

    def __init__(self, *args, **kwargs):
        """Поля нової відповіді або (для збереженої) лише текст."""
        super().__init__(*args, **kwargs)
        reply = self.instance
        if reply.pk:
            for name in ("author", "thread", "parent", "images"):
                del self.fields[name]
            self.fields["body"].initial = reply.body
        else:
            self.fields["author"].queryset = tools.test_users().order_by("username")
            self.fields["author"].label_from_instance = lambda u: f"@{u.username}"
            self.fields["thread"].queryset = (
                TestThread.objects.filter(pk__in=tools.registered_ids(TestThread), deleted_at__isnull=True,
                                          status=TestThread.Status.PUBLISHED, board__is_active=True)
                .order_by("-created_at"))
            self.fields["thread"].label_from_instance = lambda t: f"#{t.pk} · {t.title}"
            self.fields["parent"].queryset = (
                TestReply.objects.filter(pk__in=tools.registered_ids(TestReply), deleted_at__isnull=True,
                                         status=TestReply.Status.PUBLISHED)
                .select_related("thread", "author").order_by("thread_id", "created_at"))
            self.fields["parent"].label_from_instance = lambda r: (
                f"#{r.pk} · {r.thread.title[:40]} · @{getattr(r.author, 'username', '?')}: {r.body[:40]}")
        unfold_widgets(self)

    def clean_images(self):
        """Перевіряє кількість і кожен файл через конвеєр зображень."""
        files = self.cleaned_data.get("images") or []
        if len(files) > limits.MAX_REPLY_IMAGES:
            raise ValidationError(_("Too many images."))
        return [clean_upload(upload) for upload in files]

    def clean(self):
        """Текст чи картинка; батько з тієї ж теми; автор лише тестовий."""
        data = super().clean()
        if not self.instance.pk and not self.errors and not (data.get("body") or data.get("images")):
            self.add_error("body", _("Write something or add an image."))
        if self.instance.pk and not data.get("body") and not self.instance.images.exists():
            self.add_error("body", _("Write something or add an image."))
        parent, thread = data.get("parent"), data.get("thread")
        if parent is not None and thread is not None and parent.thread_id != thread.pk:
            self.add_error("parent", _("Choose a reply from the same thread."))
        if data.get("author") is not None:
            try:
                tools.require_test_user(data["author"])
            except ValidationError as error:
                self.add_error("author", error)
        return data


@admin.register(TestReply)
class TestReplyAdmin(TestAdmin):
    """Відповіді тестових акаунтів."""
    form = TestReplyForm
    list_display = ("__str__", "author", "depth", "status", "created_at")
    list_select_related = ("thread", "author")
    search_fields = ("body", "author__username", "thread__title")
    ordering = ("-created_at", "-pk")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(pk__in=tools.registered_ids(TestReply))

    def get_fieldsets(self, request, obj=None):
        return ((None, {"fields": tuple(self.form(instance=obj or TestReply()).fields)}),)

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def write(self, request, obj, form, change):
        """Нова відповідь через інструменти або зміна тексту наявної."""
        data = form.cleaned_data
        if change:
            tools.edit_reply(obj, data["body"])
        else:
            created = tools.create_reply(data["author"], data["thread"], data.get("parent"), data["body"],
                                         images=data["images"])
            obj.pk = created.pk
        obj.refresh_from_db()
        audit.log("testdata.reply.saved", obj, actor=request.user, created=not change)
