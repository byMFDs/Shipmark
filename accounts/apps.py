"""Конфігурація застосунку accounts; підключає сигнали."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Застосунок accounts: користувачі, профілі, бейджі, налаштування."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from . import signals  # noqa: F401
