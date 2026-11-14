"""Конфігурація застосунку community; підключає сигнали."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommunityConfig(AppConfig):
    """Застосунок community: форум з дошками, темами, відповідями й голосами."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "community"
    verbose_name = _("Community")

    def ready(self):
        from . import signals  # noqa: F401
