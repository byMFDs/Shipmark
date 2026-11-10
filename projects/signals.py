from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Screenshot


@receiver(post_delete, sender=Screenshot)
def delete_screenshot_file(sender, instance, **kwargs):
    """Remove the file when a screenshot row goes away (also when a project is deleted)."""
    if instance.image:
        storage, name = instance.image.storage, instance.image.name
        transaction.on_commit(lambda: storage.delete(name))
