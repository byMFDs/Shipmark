"""Ban evasion: a salted hash of the GitHub user id, kept only while the ban lasts (see BannedIdentity).

hash = HMAC-SHA256(key derived from SECRET_KEY and a fixed salt, "github:<id>"). The raw id is never stored.
Keys in SECRET_KEY_FALLBACKS are tried too, so rotating SECRET_KEY does not free banned accounts.
"""
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import BannedIdentity

SALT = "shipmark.moderation.banned-identity"


def _hash(uid, secret=None):
    return salted_hmac(SALT, f"github:{uid}", secret=secret, algorithm="sha256").hexdigest()


def identity_hashes(uid):
    secrets = [settings.SECRET_KEY, *getattr(settings, "SECRET_KEY_FALLBACKS", [])]
    return [_hash(uid, secret) for secret in secrets]


def github_uid(user):
    from allauth.socialaccount.models import SocialAccount

    return SocialAccount.objects.filter(user=user, provider="github").values_list("uid", flat=True).first()


def prune(now=None):
    """Deletes rows of bans that have ended. Returns how many."""
    deleted, _rows = BannedIdentity.objects.filter(expires_at__lte=now or timezone.now()).delete()
    return deleted


def remember(sanction):
    """Called when a ban is issued. No GitHub account (admin-made users): nothing to remember."""
    uid = github_uid(sanction.user)
    if not uid:
        return None
    return BannedIdentity.objects.create(
        identity_hash=_hash(uid), sanction=sanction, reason=sanction.reason, expires_at=sanction.expires_at,
    )


def sync(sanction):
    """After the end date or the reason of a ban changed, or it was revoked."""
    if sanction.revoked_at is not None:
        BannedIdentity.objects.filter(sanction=sanction).delete()
    else:
        BannedIdentity.objects.filter(sanction=sanction).update(reason=sanction.reason, expires_at=sanction.expires_at)


def find(uid, now=None):
    """The active ban for this GitHub id, or None. Prunes ended bans first."""
    if not uid:
        return None
    now = now or timezone.now()
    prune(now)
    rows = BannedIdentity.objects.filter(identity_hash__in=identity_hashes(uid)).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now))
    return max(rows, key=lambda r: (r.expires_at is None, r.expires_at), default=None)
