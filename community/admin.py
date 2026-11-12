"""Admin for the community. Boards are managed here. Threads and replies are read-only: removing, locking and
pinning need a reason the author sees, so they happen in /mod/. Superusers can restore removed posts and delete
rows for good; both are written to the AuditLog. Votes are not registered on purpose (nobody browses who voted)."""
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from unfold.decorators import action

from moderation import decisions
from moderation.adminbase import AuditedModelAdmin, ReadOnlyModelAdmin

from .models import Board, CommunityImage, Reply, Thread


@admin.register(Board)
class BoardAdmin(AuditedModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    def has_delete_permission(self, request, obj=None):
        # A board with threads cannot be deleted anyway (PROTECT); hide it with is_active instead.
        return request.user.is_superuser


class PostAdmin(AuditedModelAdmin):
    """Read-only, with "Restore" and delete for superusers."""

    actions = ["restore"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Thread)
class ThreadAdmin(PostAdmin):
    list_display = ("title", "board", "author", "status", "pinned", "score", "reply_count", "created_at")
    list_filter = ("status", "pinned", "board", "created_at")
    search_fields = ("title", "body", "author__username")
    list_select_related = ("board", "author")
    date_hierarchy = "created_at"

    @action(description=_("Restore selected threads (superusers)"), permissions=["delete"])
    def restore(self, request, queryset):
        done = sum(decisions.restore_thread(thread, request.user) for thread in queryset.select_related("author"))
        messages.success(request, _("Restored: %(count)s.") % {"count": done})


@admin.register(Reply)
class ReplyAdmin(PostAdmin):
    list_display = ("__str__", "author", "status", "depth", "score", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("body", "author__username", "thread__title")
    list_select_related = ("thread", "author")
    date_hierarchy = "created_at"

    @action(description=_("Restore selected replies (superusers)"), permissions=["delete"])
    def restore(self, request, queryset):
        done = sum(decisions.restore_reply(reply, request.user) for reply in queryset.select_related("author", "thread"))
        messages.success(request, _("Restored: %(count)s.") % {"count": done})


@admin.register(CommunityImage)
class CommunityImageAdmin(ReadOnlyModelAdmin):
    list_display = ("image", "uploader", "thread", "reply", "width", "height", "created_at")
    list_select_related = ("uploader", "thread", "reply__thread")
    date_hierarchy = "created_at"

    def has_delete_permission(self, request, obj=None):
        return False
