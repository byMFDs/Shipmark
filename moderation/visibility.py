"""Що бачить публіка: призупинені й забанені приховані однаково.

Who and what the public may see. A suspended user and a user with an active ban are hidden the same way:
their profile and projects are 404 and they are left out of every list. Removed, hidden and draft projects are
not "published", so they are never public. The active ban is checked inside the query (no extra query)."""
from django.db.models import Exists, OuterRef

from .models import Sanction


def banned(outer="owner"):
    """Підзапит: чи є в людини чинний бан.

    Exists() for an active ban of the user at OuterRef(outer). Use with ~ to keep the others."""
    return Exists(Sanction.objects.active().filter(kind=Sanction.Kind.BAN, user=OuterRef(outer)))


def visible_users(queryset):
    return queryset.filter(is_suspended=False).filter(~banned("pk"))


def visible_owner(queryset, owner="owner"):
    """Фільтрує записи, власник яких видимий.

    Filter any queryset by its owner field path ("owner", "project__owner", ...)."""
    return queryset.filter(**{f"{owner}__is_suspended": False}).filter(~banned(owner))


def is_hidden_user(user):
    from accounts.roles import active_ban

    return bool(user.is_suspended or active_ban(user))
