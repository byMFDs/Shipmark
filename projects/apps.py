"""Конфігурація застосунку projects; підключає сигнали."""
from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """Застосунок projects: проєкти, скриншоти, журнал збірки, марки."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'

    def ready(self):
        from . import signals  # noqa: F401
