"""Конфігурація застосунку pages."""
from django.apps import AppConfig


class PagesConfig(AppConfig):
    """Застосунок pages: лендинг, Discover, контентні сторінки, теги шаблонів."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
