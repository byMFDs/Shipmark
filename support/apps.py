"""Конфігурація застосунку support; підключає перевірки й сигнали."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SupportConfig(AppConfig):
    """Застосунок support: форма підтримки й скринька в адмінці."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "support"
    verbose_name = _("Support")

    def ready(self):
        from . import checks, signals  # noqa: F401
