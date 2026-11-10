from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation
from django.utils.http import urlencode


BADGE_PREFIX = "/badge/"


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
            return
        super().process_request(request)

    def process_response(self, request, response):
        if request.path_info.startswith(BADGE_PREFIX):
            return response
        return super().process_response(request, response)


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
