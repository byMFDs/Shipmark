"""Конфігурація застосунку verification."""
from django.apps import AppConfig


class VerificationConfig(AppConfig):
    """Застосунок verification: репозиторії, домени, аптайм, safe_fetch."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'verification'
