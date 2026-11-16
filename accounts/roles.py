"""Хто що може: єдине джерело ролей для views, шаблонів і адмінки.

Who may do what. The single source of truth for roles: views, templates and the admin ask here.

Badges (UserBadge) are read once per user object: from a prefetch (`prefetch_related("badges")`,
or "owner__badges" on lists) when there is one, otherwise with one query that is then cached on the object.
"""
from .models import UserBadge

OFFICIAL = UserBadge.Kind.OFFICIAL
MODERATOR = UserBadge.Kind.MODERATOR


def badge_dates(user):
    """Дати видачі бейджів користувача.

    {kind: granted_at} of the user's badges (the real dates, shown as "Official since ..."). Empty for anonymous
    users. Same single read as badge_kinds."""
    if user is None or not getattr(user, "pk", None):
        return {}
    cached = getattr(user, "_badge_dates", None)
    if cached is None:
        prefetched = getattr(user, "_prefetched_objects_cache", {}).get("badges")
        rows = prefetched if prefetched is not None else user.badges.all()
        cached = {badge.kind: badge.granted_at for badge in rows}
        user._badge_dates = cached
    return cached


def badge_kinds(user):
    """Набір типів бейджів користувача.

    frozenset of badge kinds ("official", "moderator"). Empty for anonymous users."""
    return frozenset(badge_dates(user))


def forget_badges(user):
    """Скидає кеш бейджів після видачі чи зняття.

    Call after granting or revoking, so the same object reads the new state."""
    user.__dict__.pop("_badge_dates", None)
    getattr(user, "_prefetched_objects_cache", {}).pop("badges", None)


def is_official(user):
    return OFFICIAL in badge_kinds(user)


def has_moderator_badge(user):
    return MODERATOR in badge_kinds(user)


def can_moderate(user):
    """Бейдж модератора або суперкористувач.

    The moderator badge, or a superuser. Plain staff (is_staff) cannot moderate on the site."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return False
    return user.is_superuser or has_moderator_badge(user)


def can_manage_badges(user):
    """Видавати бейджі може лише суперкористувач.

    Only superusers grant or revoke badges, in the admin or with `grant_badge`."""
    return bool(getattr(user, "is_authenticated", False) and user.is_active and user.is_superuser)


def can_set_official_pictures(actor, target):
    """Змінювати аватарку й обкладинку офіційного чи системного акаунта може лише суперкористувач.

    Only a superuser sets the avatar and cover of an official or system account (the "shipmark" account has no
    sign-in, so its picture cannot be changed any other way). Ordinary accounts change theirs in Settings."""
    from .system import is_system
    return bool(can_manage_badges(actor) and getattr(target, "pk", None) and (is_system(target) or is_official(target)))


# ---------- Sanctions (moderation.Sanction), evaluated per request ----------

def active_sanctions(user):
    """Чинні mute і ban користувача, закешовані на об'єкті.

    Mutes and bans in force now, cached on the user object (one query per request)."""
    if user is None or not getattr(user, "pk", None):
        return ()
    cached = getattr(user, "_active_sanctions", None)
    if cached is None:
        from moderation.models import Sanction  # here: moderation imports accounts

        cached = tuple(Sanction.objects.active().filter(user_id=user.pk).order_by("-starts_at", "-pk"))
        user._active_sanctions = cached
    return cached


def forget_sanctions(user):
    user.__dict__.pop("_active_sanctions", None)


def _longest(sanctions):
    """Санкція, яка закінчується найпізніше.

    The one that ends last (a permanent one wins)."""
    if not sanctions:
        return None
    return max(sanctions, key=lambda s: (s.expires_at is None, s.expires_at or s.starts_at))


def active_ban(user):
    return _longest([s for s in active_sanctions(user) if s.kind == "ban"])


def active_mute(user):
    return _longest([s for s in active_sanctions(user) if s.kind == "mute"])


def can_write(user):
    """Чи може людина щось створювати (не призупинена, не приглушена, не забанена).

    Create, edit, publish, log, like, follow, report, upload. Not: suspended, muted or banned users.
    Reading, own settings, export and account deletion stay open to muted users."""
    if not getattr(user, "is_authenticated", False) or not user.is_active or user.is_suspended:
        return False
    return not active_sanctions(user)


def is_protected(target):
    """Акаунти, на які модератор без прав суперкористувача не може діяти.

    Accounts a moderator (who is not a superuser) may never act on."""
    return bool(target.is_superuser or is_official(target) or has_moderator_badge(target))
