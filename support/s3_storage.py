"""Приватні S3-вкладення підтримки без адрес для браузера."""
from storages.backends.s3 import S3Storage


class PrivateS3Storage(S3Storage):
    """Вкладення відкриваються тільки через staff download view."""

    def url(self, name, *args, **kwargs):
        raise ValueError("Support attachments have no public URL; staff download them through the admin.")
