"""Простий ліміт частоти на кеші.

Tiny cache-based rate limit (CLAUDE.md section 6).

    if is_limited("settings", request.user.pk, limit=30, window=600): ...

Counts per (name, key) in a fixed window. Uses Django's default cache. The default LocMemCache
is per process, so in production with several workers configure a shared cache.
"""
import math
import time

from django.core.cache import cache


def is_limited(name, key, limit, window):
    """Рахує виклик; True, коли ліміт за вікно перевищено.

    Counts this call and returns True once it goes over `limit` within `window` seconds."""
    cache_key = f"rl:{name}:{key}"
    cache.add(cache_key, 0, timeout=window)  # only sets the expiry for a new window
    try:
        count = cache.incr(cache_key)
    except ValueError:  # expired between add() and incr()
        cache.set(cache_key, 1, timeout=window)
        count = 1
    return count > limit


# ---------- Cooldowns and limits that can say how long to wait ----------

def _seconds_left(until):
    return max(1, math.ceil(until - time.time()))


def claim_cooldown(name, key, seconds):
    """Починає паузу або повертає, скільки секунд лишилось.

    Start a cooldown and return 0, or return the seconds left of the one already running.

    cache.add is atomic, so two requests at the same moment cannot both start (and both run) the action.
    """
    cache_key = f"cd:{name}:{key}"
    until = time.time() + seconds
    if cache.add(cache_key, until, timeout=seconds):
        return 0
    return _seconds_left(cache.get(cache_key) or until)


def cooldown_left(name, key):
    """Скільки секунд лишилось у паузі (лише читає).

    Seconds left of a running cooldown, or 0. Reads only, starts nothing."""
    until = cache.get(f"cd:{name}:{key}")
    return _seconds_left(until) if until else 0


def release_cooldown(name, key):
    cache.delete(f"cd:{name}:{key}")


def limited_for(name, key, limit, window):
    """Як is_limited, але повертає секунди до кінця вікна.

    Like is_limited (and counts the same way), but returns 0 when allowed, else the seconds until the window ends."""
    until_key = f"rl:{name}:{key}:until"
    cache.add(until_key, time.time() + window, timeout=window)
    if not is_limited(name, key, limit, window):
        return 0
    return _seconds_left(cache.get(until_key) or time.time() + window)
