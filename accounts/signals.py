"""Сигнали accounts: прибирання файлів після видалення користувача, свіжий лічильник людей."""
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .avatars import drop
from .models import User


@receiver(post_delete, sender=User)
def delete_picture_files(sender, instance, **kwargs):
    """Видаляє аватарку й обкладинку з диска разом з акаунтом.

    Deleting an account removes its uploaded avatar and cover files too (privacy: nothing stays on disk)."""
    drop(instance.avatar)
    drop(instance.cover)


def _forget_people_count():
    from pages.stats import CACHE_KEY  # here: pages imports accounts

    cache.delete(CACHE_KEY)


@receiver(post_save)
def people_count_on_save(sender, instance, created, update_fields=None, **kwargs):
    """Нове або змінене (активність) акаунта скидає кеш лічильника.

    A new account, or a save that may change is_active, drops the cached "<n> people joined" after the commit, so
    the header shows the real number at once instead of after the 60-second cache. Logins (last_login only) do not.
    Listens to every sender and keeps users only: proxies of User (the admin's test accounts) send their own class."""
    if not issubclass(sender, User):
        return
    if created or update_fields is None or "is_active" in update_fields:
        transaction.on_commit(_forget_people_count, robust=True)


@receiver(post_delete)
def people_count_on_delete(sender, instance, **kwargs):
    """Видалений акаунт скидає кеш лічильника після commit."""
    if not issubclass(sender, User):
        return
    transaction.on_commit(_forget_people_count, robust=True)
