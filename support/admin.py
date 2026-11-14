"""Скринька підтримки в адмінці (лише для персоналу з правами).

Support inbox in the admin. Visible only to superusers and staff who were given the support permissions
(support.view_supportmessage to read, support.change_supportmessage to set status and notes). Every status change
and note is in the AuditLog; what the person wrote cannot be edited."""
from urllib.parse import quote

from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from unfold.admin import ModelAdmin
from unfold.decorators import action

from config import branding
from moderation import audit

from .mailcheck import email_problems
from .models import SupportMessage


def can_view_inbox(request):
    return request.user.has_perm("support.view_supportmessage")


def unread_badge(request):
    if not can_view_inbox(request):
        return None
    return SupportMessage.objects.filter(status=SupportMessage.Status.NEW).count() or None


def unread_count():
    return SupportMessage.objects.filter(status=SupportMessage.Status.NEW).count()


@admin.register(SupportMessage)
class SupportMessageAdmin(ModelAdmin):
    """Звернення в підтримку в адмінці: статуси, нотатки, вкладення."""
    list_display = ("created_at", "category", "status", "short_subject", "email", "who", "files")
    list_filter = ("status", "category", "created_at")
    search_fields = ("email", "subject", "body", "reference", "user__username")
    list_select_related = ("user",)
    date_hierarchy = "created_at"
    actions = ["mark_read", "mark_answered", "mark_closed"]
    readonly_fields = ("created_at", "category", "email", "who", "subject", "body", "reference", "attachment_links",
                       "reply_link")
    fieldsets = (
        (None, {"fields": ("created_at", "category", "who", "email", "reply_link", "subject", "body", "reference",
                           "attachment_links")}),
        (_("Handling"), {"fields": ("status", "internal_note")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(file_count=Count("attachments"))

    def changelist_view(self, request, extra_context=None):
        """Список звернень з банером, якщо пошта не налаштована."""
        # A visible note when new messages cannot reach the support mailbox (support/mailcheck.py). The reasons are
        # setting names, so they stay in English.
        problems = email_problems()
        if problems and request.method == "GET":
            messages.warning(request, format_html(
                "{} {}", _("New messages do not reach the support mailbox. Run “python manage.py send_test_email” on the "
                           "server for details."), " ".join(problems)))
        return super().changelist_view(request, extra_context)

    def has_add_permission(self, request):
        return False

    @admin.display(description=_("Subject"))
    def short_subject(self, obj):
        return (obj.subject or obj.body)[:60]

    @admin.display(description=_("Account"))
    def who(self, obj):
        """Хто написав: посилання на акаунт або «не увійшов»."""
        if not obj.user_id:
            return _("Not signed in")
        return format_html('<a href="{}">@{}</a>', reverse("admin:accounts_user_change", args=[obj.user_id]),
                           obj.user.username)

    @admin.display(description=_("Files"))
    def files(self, obj):
        return obj.file_count or ""

    @admin.display(description=_("Attachments"))
    def attachment_links(self, obj):
        """Посилання на завантаження вкладень."""
        items = list(obj.attachments.all())
        if not items:
            return "-"
        return format_html_join(
            format_html("<br>"), '<a href="{}">{}</a> ({} KB, {})',
            ((reverse("support:attachment", args=[a.pk]), a.download_name, max(1, a.size // 1024),
              a.get_kind_display()) for a in items),
        )

    @admin.display(description=_("Reply"))
    def reply_link(self, obj):
        subject = f"Re: {obj.subject or branding.SITE_NAME + ' support'}"
        return format_html('<a href="mailto:{}?subject={}">{}</a>', obj.email, quote(subject), _("Reply by email"))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Відкриття нового звернення позначає його прочитаним.

        Opening a new message marks it read (logged like any status change)."""
        message = self.get_object(request, object_id)
        if (message is not None and message.status == SupportMessage.Status.NEW and request.method == "GET"
                and self.has_change_permission(request, message)):
            self._set_status(request, message, SupportMessage.Status.READ)
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        """Зберігає статус і нотатку з записом в AuditLog."""
        changed = [name for name in ("status", "internal_note") if name in form.changed_data]
        super().save_model(request, obj, form, change)
        if changed:
            audit.log("support.updated", obj, actor=request.user, fields=changed, status=obj.status)

    def delete_model(self, request, obj):
        audit.log("admin.deleted", obj, actor=request.user, model=obj._meta.label_lower)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            audit.log("admin.deleted", obj, actor=request.user, model=obj._meta.label_lower)
        super().delete_queryset(request, queryset)

    def _set_status(self, request, message, status):
        """Змінює статус звернення з записом в AuditLog."""
        if message.status == status:
            return False
        message.status = status
        message.save(update_fields=["status", "updated_at"])
        audit.log("support.status", message, actor=request.user, status=status)
        return True

    def _bulk(self, request, queryset, status):
        done = sum(self._set_status(request, message, status) for message in queryset)
        messages.success(request, ngettext("Updated %(count)d message.", "Updated %(count)d messages.", done)
                         % {"count": done})

    @action(description=_("Mark as read"), permissions=["change"])
    def mark_read(self, request, queryset):
        self._bulk(request, queryset, SupportMessage.Status.READ)

    @action(description=_("Mark as answered"), permissions=["change"])
    def mark_answered(self, request, queryset):
        self._bulk(request, queryset, SupportMessage.Status.ANSWERED)

    @action(description=_("Close"), permissions=["change"])
    def mark_closed(self, request, queryset):
        self._bulk(request, queryset, SupportMessage.Status.CLOSED)
