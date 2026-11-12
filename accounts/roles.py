"""Who may do what. The single source of truth for roles: views, templates and the admin ask here.

Badges (UserBadge) are read once per user object: from a prefetch (`prefetch_related("badges")`,
or "owner__badges" on lists) when there is one, otherwise with one query that is then cached on the object.
"""
from .models import UserBadge

OFFICIAL = UserBadge.Kind.OFFICIAL
MODERATOR = UserBadge.Kind.MODERATOR


def badge_kinds(user):
    """frozenset of badge kinds ("official", "moderator"). Empty for anonymous users."""
    if user is None or not getattr(user, "pk", None):
        return frozenset()
    cached = getattr(user, "_badge_kinds", None)
    if cached is None:
        prefetched = getattr(user, "_prefetched_objects_cache", {}).get("badges")
        rows = prefetched if prefetched is not None else user.badges.all()
        cached = frozenset(badge.kind for badge in rows)
        user._badge_kinds = cached
    return cached


def forget_badges(user):
    """Call after granting or revoking, so the same object reads the new state."""
    user.__dict__.pop("_badge_kinds", None)
    getattr(user, "_prefetched_objects_cache", {}).pop("badges", None)


def is_official(user):
    return OFFICIAL in badge_kinds(user)


def has_moderator_badge(user):
    return MODERATOR in badge_kinds(user)


def can_moderate(user):
    """The moderator badge, or a superuser. Plain staff (is_staff) cannot moderate on the site."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return False
    return user.is_superuser or has_moderator_badge(user)


def can_manage_badges(user):
    """Only superusers grant or revoke badges, in the admin or with `grant_badge`."""
    return bool(getattr(user, "is_authenticated", False) and user.is_active and user.is_superuser)
