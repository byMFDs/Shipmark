from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation


class UserLocaleMiddleware(LocaleMiddleware):
    """Language order (CLAUDE.md section 8): saved user preference, then language cookie,
    then the browser's Accept-Language, then English.

    Django's LocaleMiddleware already does the last three, in that order.
    We only put the signed-in user's saved preference in front.
    """

    def process_request(self, request):
        user = getattr(request, "user", None)
        saved = user.preferred_language if user is not None and user.is_authenticated else ""
        if saved in dict(settings.LANGUAGES):
            translation.activate(saved)
            request.LANGUAGE_CODE = translation.get_language()
            return
        super().process_request(request)
