"""Сигнали підтримки: прибирання файлів вкладень."""
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import SupportAttachment


@receiver(post_delete, sender=SupportAttachment)
def delete_attachment_file(sender, instance, **kwargs):
    """Видаляє файл вкладення разом з його рядком.

    The file goes with its row (also by cascade: message, account), through the storage API, after the commit."""
    if instance.file:
        storage, name = instance.file.storage, instance.file.name
        transaction.on_commit(lambda: storage.delete(name))
