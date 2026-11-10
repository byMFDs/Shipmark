"""Username rules: validation and generation from a GitHub login.

Usernames appear in URLs (/u/<username>/), so they are lowercase and URL-safe.
"""
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# CLAUDE.md section 4. Also blocks names that look like official accounts.
RESERVED_USERNAMES = frozenset({
    "admin", "api", "static", "media", "badge", "legal", "settings", "new", "feed",
    "explore", "login", "logout", "signup", "u", "p", "help", "about", "support",
    "root", "system",
})

MIN_LENGTH = 3
MAX_LENGTH = 39  # same as GitHub
_ALLOWED = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def validate_username(value):
    """Model/form validator. Does not check uniqueness (the database does)."""
    if not (MIN_LENGTH <= len(value) <= MAX_LENGTH):
        raise ValidationError(
            _("Use %(min)d to %(max)d characters."), code="length",
            params={"min": MIN_LENGTH, "max": MAX_LENGTH},
        )
    if not _ALLOWED.match(value):
        raise ValidationError(
            _("Use only lowercase letters, digits, hyphens and underscores, starting with a letter or digit."),
            code="invalid",
        )
    if value in RESERVED_USERNAMES:
        raise ValidationError(_("This username is reserved. Please choose another."), code="reserved")


def is_taken(username, exclude_pk=None):
    from django.contrib.auth import get_user_model

    qs = get_user_model().objects.filter(username__iexact=username)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def _is_free(candidate):
    try:
        validate_username(candidate)
    except ValidationError:
        return False
    return not is_taken(candidate)


def generate_username(github_login):
    """A valid, free username based on a GitHub login: `name`, then `name-2`, `name-3`, ..."""
    base = re.sub(r"[^a-z0-9_-]", "-", (github_login or "").lower()).strip("-_")[:MAX_LENGTH] or "user"
    candidate, n = base, 1
    while not _is_free(candidate):
        n += 1
        suffix = f"-{n}"
        candidate = base[: MAX_LENGTH - len(suffix)] + suffix
    return candidate
