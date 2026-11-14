"""Адмінка підписок і вподобань (лише перегляд)."""
from django.contrib import admin

from moderation.adminbase import ReadOnlyModelAdmin

from .models import Follow, Like


@admin.register(Follow)
class FollowAdmin(ReadOnlyModelAdmin):
    """Підписки в адмінці."""
    list_display = ("follower", "following", "created_at")
    list_filter = ("created_at",)
    search_fields = ("follower__username", "following__username")
    list_select_related = ("follower", "following")


@admin.register(Like)
class LikeAdmin(ReadOnlyModelAdmin):
    """Вподобання в адмінці."""
    list_display = ("user", "project", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "project__name", "project__owner__username")
    list_select_related = ("user", "project", "project__owner")
