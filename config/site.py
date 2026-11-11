"""Canonical absolute URLs for anything shared outside the site.

Badge embed snippets, Open Graph tags, canonical links and the data export use settings.SITE_URL
(http://localhost:8000 in development, https://shipmark.me in production), never the Host of the request:
a snippet copied from a local or preview server must still point to the real site.
"""
from django.conf import settings


def absolute_url(path):
    """"/u/ann/" -> "https://shipmark.me/u/ann/". URLs that are already absolute (a CDN) stay as they are."""
    path = str(path or "")
    if path.startswith(("http://", "https://")):
        return path
    return settings.SITE_URL.rstrip("/") + "/" + path.lstrip("/")
