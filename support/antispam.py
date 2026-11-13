"""Spam protection for /support/ without outside services.

- Honeypot: a field people never see. A filled one is a bot; it gets the "sent" page and nothing is stored.
- Fill-time token: the form carries a signed timestamp; a POST less than 3 seconds after the page was made, or
  with a broken or old token, is refused.
- Rate limits: 3 messages an hour and 10 a day per session, per signed-in account and per salted hash of the
  IP address. The hash lives only in the cache (never in the database or logs) and expires with the window.
- Duplicates: the same address and text within 24 hours count as one message.
"""
import hashlib
import hmac
import re
import time

from django.conf import settings
from django.core import signing
from django.core.cache import cache

MIN_FILL_SECONDS = 3
TOKEN_MAX_AGE = 2 * 60 * 60
TOKEN_SALT = "support.form.started"
LIMITS = (("hour", 3, 60 * 60), ("day", 10, 24 * 60 * 60))
DUPLICATE_WINDOW = 24 * 60 * 60


# ---------- Fill-time token ----------

def issue_token(now=None):
    return signing.dumps({"t": round(now if now is not None else time.time(), 3)}, salt=TOKEN_SALT)


def token_problem(token, now=None):
    """'' when the form was filled in a human way, else 'fast' or 'expired' (a broken token counts as expired)."""
    try:
        started = signing.loads(token or "", salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)["t"]
    except (signing.BadSignature, KeyError, TypeError):
        return "expired"
    elapsed = (now if now is not None else time.time()) - float(started)
    return "fast" if elapsed < MIN_FILL_SECONDS else ""


# ---------- Rate limits ----------

def client_ip(request):
    """The visitor's address as the trusted proxy reports it (settings.CLIENT_IP_HEADER), else REMOTE_ADDR."""
    header = getattr(settings, "CLIENT_IP_HEADER", "") or "REMOTE_ADDR"
    return (request.META.get(header) or request.META.get("REMOTE_ADDR") or "").split(",")[0].strip()


def ip_key(ip):
    """A salted one-way hash of the address. Used only as a cache key; the address itself is never kept."""
    return hmac.new(settings.SECRET_KEY.encode(), f"support-ip:{ip}".encode(), hashlib.sha256).hexdigest()[:32]


def client_keys(request):
    """Who is sending: the session, the account (when signed in) and the hashed address."""
    if not request.session.session_key:
        request.session.save()  # a session cookie only after a POST to this form (strictly necessary)
    keys = [f"s:{request.session.session_key}", f"ip:{ip_key(client_ip(request))}"]
    if request.user.is_authenticated:
        keys.append(f"u:{request.user.pk}")
    return keys


def _count_key(window, key):
    return f"support:rl:{window}:{key}"


def is_limited(keys):
    """True when any key already sent the most messages allowed in an hour or a day. Counts nothing."""
    return any((cache.get(_count_key(window, key)) or 0) >= limit for key in keys for window, limit, _s in LIMITS)


def count(keys):
    """Counts one accepted message for every key."""
    for key in keys:
        for window, _limit, seconds in LIMITS:
            cache_key = _count_key(window, key)
            cache.add(cache_key, 0, timeout=seconds)  # the window starts with the first message
            try:
                cache.incr(cache_key)
            except ValueError:  # expired between add() and incr()
                cache.set(cache_key, 1, timeout=seconds)


# ---------- Duplicates ----------

def _normalized(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def claim_first(email, body):
    """True for the first copy of this text from this address within 24 hours (cache.add is atomic)."""
    digest = hashlib.sha256(f"{email.strip().lower()}\n{_normalized(body)}".encode()).hexdigest()
    return cache.add(f"support:dup:{digest}", 1, timeout=DUPLICATE_WINDOW)
