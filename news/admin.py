from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from moderation import audit
from moderation.adminbase import AuditedModelAdmin

from .models import NewsPost


@admin.register(NewsPost)
class NewsPostAdmin(AuditedModelAdmin):
    """Django's own model permissions decide who may write: superusers, and staff given news.add/change/
    delete_newspost (for example through a "News editors" group). Every save and delete is in AuditLog."""

    list_display = ("title", "state", "pinned", "published_at", "created_by", "updated_at")
    list_filter = ("pinned", "published_at")
    search_fields = ("title", "body", "slug")
    list_select_related = ("created_by",)
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    fields = ("title", "slug", "body", "body_preview", "published_at", "pinned", "created_by", "created_at", "updated_at")
    readonly_fields = ("body_preview", "created_by", "created_at", "updated_at")

    @admin.display(description=_("State"))
    def state(self, obj):
        if obj.published_at is None:
            return _("Draft")
        return _("Published") if obj.is_published() else _("Scheduled")

    @admin.display(description=_("Preview"))
    def body_preview(self, obj):
        if not obj.pk:
            return _("Save to see the preview.")
        return format_html('<div class="prose">{}</div>', obj.body_html)  # body_html is sanitized by nh3

    def save_model(self, request, obj, form, change):
        was_published = bool(change and NewsPost.objects.filter(pk=obj.pk, published_at__isnull=False).exists())
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        audit.log("news.updated" if change else "news.created", obj, actor=request.user,
                  fields=sorted(form.changed_data), published=obj.published_at is not None)
        if obj.published_at is not None and not was_published:
            audit.log("news.published", obj, actor=request.user, published_at=obj.published_at.isoformat())
