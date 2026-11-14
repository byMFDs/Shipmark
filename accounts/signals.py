"""Сигнали accounts: прибирання файлів після видалення користувача."""
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .avatars import drop
from .models import User


@receiver(post_delete, sender=User)
def delete_picture_files(sender, instance, **kwargs):
    """Видаляє аватарку й обкладинку з диска разом з акаунтом.

    Deleting an account removes its uploaded avatar and cover files too (privacy: nothing stays on disk)."""
    drop(instance.avatar)
    drop(instance.cover)
