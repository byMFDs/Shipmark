"""Приватне сховище вкладень: поза MEDIA_ROOT, без URL.

Private storage for support attachments: never under MEDIA_ROOT, never served by URL.

STORAGES["support"] (config/settings) selects the backend. On one server it is this class, a folder outside the
public media folder (settings.SUPPORT_ROOT, read on every use so tests and settings can change it). To move it to
S3-compatible storage, point STORAGES["support"] at a private bucket or prefix (docs/DEPLOY_NOTES.md); the code
only opens, saves and deletes files through `storages["support"]` and never asks for a URL.
"""
import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage, storages


class PrivateStorage(FileSystemStorage):
    """Файлове сховище без публічної адреси."""
    @property
    def base_location(self):
        return self._value_or_setting(self._location, settings.SUPPORT_ROOT)

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise ValueError("Support attachments have no public URL; staff download them through the admin.")


def private_storage():
    """Сховище для поля вкладення.

    The storage of the FileField. A function, so the migration does not freeze a backend into it."""
    return storages["support"]
