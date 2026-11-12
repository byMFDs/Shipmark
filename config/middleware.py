import hashlib
import re
import secrets

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.middleware.locale import LocaleMiddleware
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation
from django.utils.http import urlencode

from .errorlog import current_request
from .ratelimit import is_limited


BADGE_PREFIX = "/badge/"


class RequestIdMiddleware:
    """A short random id per request: `request.request_id`, the X-Request-ID response header, the
    "Reference" on the 500/403/CSRF pages and the `request_id` of every error log line (config/errorlog.py).

    Always made here, never taken from the client: a visitor cannot plant an id in our logs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = secrets.token_hex(4)
        token = current_request.set(request)
        try:
            response = self.get_response(request)
        finally:
            current_request.reset(token)
        response.headers["X-Request-ID"] = request.request_id
        return response


class LocalhostRedirectMiddleware:
    """Development only (listed in settings/dev.py): http://127.0.0.1:8000/x?y -> http://localhost:8000/x?y.

    A browser keeps its cache, localStorage (theme) and cookies (session, language) per origin, so the two
    addresses can show different things; and the GitHub OAuth app knows only the localhost callback.
    """

    HOST = re.compile(r"127\.0\.0\.1(:\d{1,5})?")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            # Raw header, not get_host(): nothing here is trusted, it only has to match exactly.
            match = self.HOST.fullmatch(request.META.get("HTTP_HOST", ""))
            if match:
                port = match.group(1) or ""
                return HttpResponseRedirect(f"{request.scheme}://localhost{port}{request.get_full_path()}")
        return self.get_response(request)


class UserLocaleMiddleware(LocaleMiddleware):
    """Language order (CLAUDE.md section 8): saved user preference, then language cookie,
    then the browser's Accept-Language, then English.

    Django's LocaleMiddleware already does the last three, in that order.
    We only put the signed-in user's saved preference in front.
    """

    def process_request(self, request):
        if request.path_info.startswith(BADGE_PREFIX):
            # Badges are English and identical for everyone. Not reading the user or the language
            # cookie keeps `Vary: Cookie` and `Vary: Accept-Language` off the response, so caches can share it.
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
            return
        user = getattr(request, "user", None)
        saved = user.preferred_language if user is not None and user.is_authenticated else ""
        if saved in dict(settings.LANGUAGES):
            translation.activate(saved)
            request.LANGUAGE_CODE = translation.get_language()
            request.saved_language = saved
            return
        super().process_request(request)

    def process_response(self, request, response):
        if request.path_info.startswith(BADGE_PREFIX):
            return response
        response = super().process_response(request, response)
        # Keep the language cookie equal to the saved preference (also set at sign-in, see AccountAdapter.post_login),
        # so pages and messages stay in the same language after signing out. Written only when it differs.
        saved = getattr(request, "saved_language", "")
        if saved and request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) != saved:
            set_language_cookie(response, saved)
        return response


def set_language_cookie(response, code):
    """The same cookie Django's set_language view writes."""
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME, code,
        max_age=settings.LANGUAGE_COOKIE_AGE, path=settings.LANGUAGE_COOKIE_PATH, domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE, httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )


class TermsAcceptanceMiddleware:
    """Signed-in users who accepted an older Terms version are sent to the "accept the new Terms" page.

    Bump settings.TERMS_VERSION to ask everyone again. Users with no accepted version at all were not
    created by the signup step (e.g. `createsuperuser` staff) and are not asked.
    A few paths stay open so the user can still read the texts, sign out, export or delete the account.
    """

    OPEN_URL_NAMES = ("accounts:accept_terms", "accounts:export", "accounts:delete", "account_logout", "set_language")
    OPEN_PREFIXES = ("/legal/", "/static/", "/media/", BADGE_PREFIX, "/accounts/")

    def __init__(self, get_response):
        self.get_response = get_response
        self._open_paths = None

    def __call__(self, request):
        # The path first: reading request.user touches the session and would add `Vary: Cookie` to badges.
        if self._is_open(request.path_info):
            return self.get_response(request)
        user = getattr(request, "user", None)
        if (
            user is not None and user.is_authenticated
            and user.terms_version_accepted
            and user.terms_version_accepted != settings.TERMS_VERSION
        ):
            url = reverse("accounts:accept_terms")
            if request.method in ("GET", "HEAD"):
                url += "?" + urlencode({"next": request.get_full_path()})
            return redirect(url)
        return self.get_response(request)

    def _is_open(self, path):
        if self._open_paths is None:  # reversed on first use: URLconf is not loaded when middleware is built
            self._open_paths = {reverse(name) for name in self.OPEN_URL_NAMES}
        return (
            path in self._open_paths
            or path.startswith(self.OPEN_PREFIXES)
            or path.startswith("/" + settings.ADMIN_URL)
        )


class SecurityHeadersMiddleware:
    """Adds Content-Security-Policy and Permissions-Policy to every page.

    The policy comes from settings.CONTENT_SECURITY_POLICY. The admin is skipped: django-unfold
    needs inline scripts and styles. A header a view already set (the SVG badges) is left alone.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path_info.startswith("/" + settings.ADMIN_URL):
            if settings.CONTENT_SECURITY_POLICY:
                response.headers.setdefault("Content-Security-Policy", settings.CONTENT_SECURITY_POLICY)
            response.headers.setdefault("Permissions-Policy", settings.PERMISSIONS_POLICY)
        return response


class AdminLoginThrottleMiddleware:
    """Slows down password guessing on the admin login: 10 attempts per username per 15 minutes.

    Counted per username (not per IP): behind the reverse proxy every request has the proxy's address.
    The cost is that someone can lock a known staff username out for 15 minutes; they still need the secret ADMIN_URL.
    """

    LIMIT, WINDOW = 10, 15 * 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path_info == f"/{settings.ADMIN_URL}login/":
            username = request.POST.get("username", "").strip().lower()
            key = hashlib.sha256(username.encode()).hexdigest()[:32]  # the cache never sees the name itself
            if is_limited("admin_login", key, limit=self.LIMIT, window=self.WINDOW):
                return HttpResponse("Too many sign-in attempts. Try again in a few minutes.", status=429,
                                    content_type="text/plain; charset=utf-8")
        return self.get_response(request)
