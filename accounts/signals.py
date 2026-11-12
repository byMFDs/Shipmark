from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import User


@receiver(post_delete, sender=User)
def delete_picture_files(sender, instance, **kwargs):
    """Deleting an account removes its uploaded avatar and cover files too (privacy: nothing stays on disk)."""
    for field in (instance.avatar, instance.cover):
        if field:
            storage, name = field.storage, field.name
            transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))
