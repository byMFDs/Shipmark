"""Profile links: what is accepted, and how a link is shown.

Only http(s) links without a password in them. GitHub, X, LinkedIn and Telegram must point to their own
site, so a "GitHub" icon cannot lead to a look-alike page. "Website" and "Other" accept any public address.
"""
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import ProfileLink

MAX_LINKS = 6
HOSTS = {
    ProfileLink.Kind.GITHUB: ("github.com",),
    ProfileLink.Kind.X: ("x.com", "twitter.com"),
    ProfileLink.Kind.LINKEDIN: ("linkedin.com",),
    ProfileLink.Kind.TELEGRAM: ("t.me", "telegram.me", "telegram.dog"),
}
ICONS = {  # static/icons/<name>.svg
    ProfileLink.Kind.WEBSITE: "globe",
    ProfileLink.Kind.GITHUB: "github",
    ProfileLink.Kind.X: "x",
    ProfileLink.Kind.LINKEDIN: "linkedin",
    ProfileLink.Kind.TELEGRAM: "telegram",
    ProfileLink.Kind.OTHER: "link",
}


def _host_matches(host, allowed):
    return any(host == name or host.endswith("." + name) for name in allowed)


def clean_link(kind, url):
    """Returns the cleaned URL or raises ValidationError."""
    url = (url or "").strip()
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    # A backslash is read as "/" by browsers, so "https://evil.example\\.github.com" would pass a suffix check on the
    # host but open evil.example. Whitespace and control characters are refused for the same reason.
    if (parts.scheme not in ("http", "https") or "." not in host or parts.username or parts.password
            or "\\" in url or any(ord(ch) <= 32 or ord(ch) == 127 for ch in url)):
        raise ValidationError(_("Enter a public web address that starts with http:// or https://."), code="invalid")
    allowed = HOSTS.get(kind)
    if allowed and not _host_matches(host, allowed):
        raise ValidationError(
            _("This does not look like a %(kind)s address. Use the kind “Other” for any other site."),
            code="wrong_host", params={"kind": ProfileLink.Kind(kind).label},
        )
    if len(url) > 200:
        raise ValidationError(_("The address is too long (200 characters at most)."), code="too_long")
    return url


def safe_links(user):
    """The user's links, only those that are still valid http(s) (whatever is stored). For display."""
    out = []
    for link in user.links.all():
        if link.url.lower().startswith(("http://", "https://")):
            out.append(link)
    return out


def display_url(url):
    """"example.com/path" for the link text."""
    parts = urlsplit(url)
    host = (parts.hostname or "").removeprefix("www.")
    text = host + (parts.path.rstrip("/") if parts.path != "/" else "")
    return text[:40] + ("…" if len(text) > 40 else "")
