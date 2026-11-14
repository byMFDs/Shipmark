"""Дрібні службові view: favicon і перемикання мови."""
from django.conf import settings
from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.views.decorators.http import require_POST
from django.views.i18n import set_language as django_set_language


def favicon(request):
    """/favicon.ico: тимчасове перенаправлення на SVG-іконку.

    /favicon.ico: browsers and feed readers ask for it without reading the page. Temporary redirect to the
    hashed static file, so a new logo is picked up (a permanent redirect would be cached forever)."""
    from config import branding

    response = HttpResponseRedirect(static(branding.FAVICON_ICO))
    response["Cache-Control"] = "public, max-age=86400"
    return response


@require_POST
def set_language(request):
    """Перемикає мову й запам'ятовує її в акаунті.

    Django's set_language (sets the cookie, redirects back safely) + remember it on the account.

    Without the account part a signed-in user's saved preference would override the cookie,
    and the switcher would appear to do nothing.
    Django accepts any language it has files for (e.g. "ru"); we accept only settings.LANGUAGES.
    """
    code = request.POST.get("language", "")
    if code not in dict(settings.LANGUAGES):
        request.POST = request.POST.copy()
        request.POST.pop("language", None)
        return django_set_language(request)
    response = django_set_language(request)
    if request.user.is_authenticated:
        request.user.preferred_language = code
        request.user.save(update_fields=["preferred_language"])
    return response
