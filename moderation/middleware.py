"""A ban ends the session at the next request and shows the ban page (reason, end date, contact).

Expiry is evaluated here, per request; there is no cron. The query result is cached on the user object, so
templates and views asking about mutes later in the same request add no query.
"""
from django.contrib.auth import logout

from accounts.roles import active_ban
from config.middleware import BADGE_PREFIX

from .pages import ban_response


class BanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(BADGE_PREFIX):  # badges never touch the session (no Vary: Cookie)
            return self.get_response(request)
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            ban = active_ban(user)
            if ban is not None:
                logout(request)
                return ban_response(request, ban.reason, ban.expires_at)
        return self.get_response(request)
