"""Правила імені користувача: перевірка й генерація з логіна GitHub.

Username rules: validation and generation from a GitHub login.

Usernames appear in URLs (/u/<username>/), so they are lowercase and URL-safe.
"""
import re
import unicodedata

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from config import branding

# CLAUDE.md section 4. Also blocks names that look like official accounts ("shipmark" is the system account).
RESERVED_USERNAMES = frozenset({
    "admin", "api", "static", "media", "badge", "legal", "settings", "new", "feed",
    "explore", "login", "logout", "signup", "u", "p", "help", "about", "support",
    "root", "system",
    "shipmark", "official", "moderator", "mod", "team", "staff", "news",
})

# Display names only official accounts may use: the site name alone or with one of these words.
# Compared after case folding, Unicode normalization (NFKC) and dropping everything but letters and digits,
# so "SHIPMARK", "Shipmark  Team", "shipmark-official", "Official Shipmark" and "Ｓｈｉｐｍａｒｋ" are all caught.
OFFICIAL_NAME_WORDS = ("", "team", "official", "staff", "support", "news", "moderator", "moderation", "hq")

MIN_LENGTH = 3
MAX_LENGTH = 39  # same as GitHub
_ALLOWED = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def validate_username(value):
    """Валідатор імені користувача (без перевірки зайнятості).

    Model/form validator. Does not check uniqueness (the database does)."""
    if not (MIN_LENGTH <= len(value) <= MAX_LENGTH):
        raise ValidationError(
            _("Use %(min)d to %(max)d characters."), code="length",
            params={"min": MIN_LENGTH, "max": MAX_LENGTH},
        )
    if not _ALLOWED.match(value):
        raise ValidationError(
            _("Use only small letters, numbers, - and _, and start with a letter or a number."),
            code="invalid",
        )
    if value in RESERVED_USERNAMES:
        raise ValidationError(_("This username is not available. Choose another one."), code="reserved")


def is_taken(username, exclude_pk=None):
    """Чи зайняте ім'я (без урахування регістру)."""
    from django.contrib.auth import get_user_model

    qs = get_user_model().objects.filter(username__iexact=username)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def _is_free(candidate):
    """Чи ім'я коректне й вільне."""
    try:
        validate_username(candidate)
    except ValidationError:
        return False
    return not is_taken(candidate)


def generate_username(github_login):
    """Вільне ім'я на основі логіна GitHub: name, name-2, name-3...

    A valid, free username based on a GitHub login: `name`, then `name-2`, `name-3`, ..."""
    base = re.sub(r"[^a-z0-9_-]", "-", (github_login or "").lower()).strip("-_")[:MAX_LENGTH] or "user"
    candidate, n = base, 1
    while not _is_free(candidate):
        n += 1
        suffix = f"-{n}"
        candidate = base[: MAX_LENGTH - len(suffix)] + suffix
    return candidate


def _name_key(value):
    folded = unicodedata.normalize("NFKC", value or "").casefold()
    return "".join(ch for ch in folded if ch.isalnum())


def looks_official(display_name):
    """Чи схоже відображуване ім'я на офіційний акаунт.

    True when the display name would pass for the site's own account."""
    site = _name_key(branding.SITE_NAME)
    key = _name_key(display_name)
    return bool(key) and any(key in (site + word, word + site) for word in OFFICIAL_NAME_WORDS)


def validate_display_name(value, user=None):
    """Офіційні імена дозволено лише акаунтам з бейджем official.

    Only accounts with the official badge may be called "Shipmark", "Shipmark Team" and so on."""
    from .roles import is_official

    if looks_official(value) and not (user is not None and is_official(user)):
        raise ValidationError(_("This name is reserved for official %(site)s accounts."), code="reserved_name",
                              params={"site": branding.SITE_NAME})
