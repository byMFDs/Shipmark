from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Screenshot


@receiver(post_delete, sender=Screenshot)
def delete_screenshot_file(sender, instance, **kwargs):
    """Remove the file when a screenshot row goes away (also when a project is deleted)."""
    for field in (instance.image, instance.thumb):
        if field:
            storage, name = field.storage, field.name
            transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))
