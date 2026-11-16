"""Що не індексувати: заголовок X-Robots-Tag і правила robots.txt.

What search engines must not index. Kept free of model imports, so the middleware can use it.

The real admin path is deliberately NOT listed in robots.txt: that file is public and ADMIN_URL is a private path.
Its responses get `X-Robots-Tag: noindex` instead (and nothing links to it).
"""
from django.conf import settings

# Paths whose responses always carry X-Robots-Tag: noindex (on top of the meta tag in their templates).
NOINDEX_PREFIXES = (
    "/mod/", "/settings/", "/login/", "/logout/", "/signup/", "/accounts/", "/new/", "/terms/accept/",
    "/support/sent/", "/i18n/", "/_dev/", "/styleguide/", "/feed/", "/community/new/", "/community/notifications/",
)

# robots.txt: what crawlers should not fetch. Search result pages are the ones with a query string.
ROBOTS_DISALLOW = (
    "/admin/",  # the usual decoy: the real admin path is secret and is not listed here
    "/mod/", "/settings/", "/login/", "/logout/", "/signup/", "/accounts/", "/new/", "/terms/accept/",
    "/support/sent/", "/i18n/", "/_dev/", "/styleguide/", "/community/new/", "/community/notifications/",
    "/*?q=", "/*&q=", "/*?tab=people", "/*?page=", "/*&page=",
)


def noindex_header_applies(request, response):
    """Чи треба додати X-Robots-Tag: noindex до відповіді."""
    path = request.path
    if response.status_code >= 400:
        return True
    admin = "/" + settings.ADMIN_URL.strip("/") + "/"
    return path.startswith(NOINDEX_PREFIXES) or path.startswith(admin)


class RobotsHeaderMiddleware:
    """Додає X-Robots-Tag: noindex приватним, службовим сторінкам і відповідям з помилкою.

    Adds `X-Robots-Tag: noindex` to private and utility pages and to every error response, so no error page
    or settings page is indexed even if its template forgot the meta tag."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if noindex_header_applies(request, response):
            response.headers.setdefault("X-Robots-Tag", "noindex")
        return response
