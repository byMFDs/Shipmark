"""Ban evasion: a keyed hash of the GitHub user id, kept only while the ban lasts (see BannedIdentity).

hash = HMAC-SHA256(key = settings.BAN_HASH_KEY, message = "<LABEL>:github:<id>"). The raw id is never stored.
LABEL is only a domain-separation prefix (this hash cannot be confused with any other HMAC); the secret is the key.
BAN_HASH_KEY is separate from SECRET_KEY on purpose: rotating SECRET_KEY must never free banned people, and
BAN_HASH_KEY must never be rotated while a ban is active (the hashes cannot be recomputed without the ids).

Older rows (hash_scheme "secret_key") were keyed from SECRET_KEY and its fallbacks. They are still looked up, but only
while such rows exist; `rehash_bans` converts the ones whose account still exists. Rows whose account was deleted
cannot be converted (the id is not stored): they keep matching through the old scheme until they expire.
"""
import hashlib
import hmac

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import BannedIdentity

LABEL = "shipmark.moderation.banned-identity"  # domain separation only
Scheme = BannedIdentity.HashScheme


def _hash(uid):
    key = settings.BAN_HASH_KEY.encode()
    return hmac.new(key, f"{LABEL}:github:{uid}".encode(), hashlib.sha256).hexdigest()


def _legacy_hashes(uid):
    """The pre-BAN_HASH_KEY scheme (django salted_hmac keyed from SECRET_KEY and its fallbacks). Lookup only."""
    secrets = [settings.SECRET_KEY, *getattr(settings, "SECRET_KEY_FALLBACKS", [])]
    return [salted_hmac(LABEL, f"github:{uid}", secret=secret, algorithm="sha256").hexdigest() for secret in secrets]


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
        identity_hash=_hash(uid), hash_scheme=Scheme.BAN_KEY, sanction=sanction, reason=sanction.reason,
        expires_at=sanction.expires_at,
    )


def sync(sanction):
    """After the end date or the reason of a ban changed, or it was revoked."""
    if sanction.revoked_at is not None:
        BannedIdentity.objects.filter(sanction=sanction).delete()
    else:
        BannedIdentity.objects.filter(sanction=sanction).update(reason=sanction.reason, expires_at=sanction.expires_at)


def _active(now):
    return BannedIdentity.objects.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))


def find(uid, now=None):
    """The active ban for this GitHub id, or None. Prunes ended bans first.

    The BAN_HASH_KEY hash is tried first; the old SECRET_KEY scheme only when old rows still exist."""
    if not uid:
        return None
    now = now or timezone.now()
    prune(now)
    active = _active(now)
    rows = list(active.filter(hash_scheme=Scheme.BAN_KEY, identity_hash=_hash(uid)))
    if not rows and active.filter(hash_scheme=Scheme.SECRET_KEY).exists():
        rows = list(active.filter(hash_scheme=Scheme.SECRET_KEY, identity_hash__in=_legacy_hashes(uid)))
    return max(rows, key=lambda r: (r.expires_at is None, r.expires_at), default=None)


def legacy_count(now=None):
    return _active(now or timezone.now()).filter(hash_scheme=Scheme.SECRET_KEY).count()


def rehash(now=None):
    """Converts active old-scheme rows to BAN_HASH_KEY. Returns (converted, left_over).

    Only possible while the banned account still exists (its GitHub id comes from the linked GitHub account); the
    old hash must match first, so a row is never changed on a guess. Left over = account deleted, nothing to do."""
    now = now or timezone.now()
    prune(now)
    converted = left_over = 0
    for row in _active(now).filter(hash_scheme=Scheme.SECRET_KEY).select_related("sanction__user"):
        uid = github_uid(row.sanction.user) if row.sanction_id else None
        if uid and row.identity_hash in _legacy_hashes(uid):
            row.identity_hash, row.hash_scheme = _hash(uid), Scheme.BAN_KEY
            row.save(update_fields=["identity_hash", "hash_scheme"])
            converted += 1
        else:
            left_over += 1
    return converted, left_over
