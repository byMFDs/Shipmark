"""Конфігурація застосунку moderation."""
from django.apps import AppConfig


class ModerationConfig(AppConfig):
    """Застосунок moderation: скарги, санкції, повідомлення, журнал."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moderation'
