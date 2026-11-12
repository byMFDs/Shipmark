"""The COMMUNITY_ENABLED switch (env). Off: every community route is a 404 and nothing links to it."""
from functools import wraps

from django.conf import settings
from django.http import Http404


def enabled():
    return bool(getattr(settings, "COMMUNITY_ENABLED", False))


def community_view(view):
    """First decorator of every community view (also the report and /mod/ routes for threads and replies)."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not enabled():
            raise Http404
        return view(request, *args, **kwargs)
    return wrapper
