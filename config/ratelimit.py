"""Tiny cache-based rate limit (CLAUDE.md section 6).

    if is_limited("settings", request.user.pk, limit=30, window=600): ...

Counts per (name, key) in a fixed window. Uses Django's default cache. The default LocMemCache
is per process, so in production with several workers configure a shared cache.
"""
from django.core.cache import cache


def is_limited(name, key, limit, window):
    """Counts this call and returns True once it goes over `limit` within `window` seconds."""
    cache_key = f"rl:{name}:{key}"
    cache.add(cache_key, 0, timeout=window)  # only sets the expiry for a new window
    try:
        count = cache.incr(cache_key)
    except ValueError:  # expired between add() and incr()
        cache.set(cache_key, 1, timeout=window)
        count = 1
    return count > limit
