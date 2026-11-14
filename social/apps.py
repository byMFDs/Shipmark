"""Конфігурація застосунку social."""
from django.apps import AppConfig


class SocialConfig(AppConfig):
    """Застосунок social: підписки, вподобання, стрічка."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'social'
