from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.i18n import set_language as django_set_language


@require_POST
def set_language(request):
    """Django's set_language (sets the cookie, redirects back safely) + remember it on the account.

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
