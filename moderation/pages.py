"""Сторінка бану й тексти «чому не можна писати».

The ban page, shared by the middleware (active session) and the GitHub sign-in (existing or new account)."""
from django.shortcuts import render

from config import branding


def ban_response(request, reason, expires_at):
    return render(request, "moderation/banned.html", {
        "reason": reason, "expires_at": expires_at, "contact_email": branding.CONTACT_EMAIL,
    }, status=403)


def write_blocked_message(user):
    """Чому людина зараз не може писати.

    Why `user` cannot post right now (403 bodies, toasts)."""
    from django.utils import formats, timezone
    from django.utils.translation import gettext as _

    from accounts.roles import active_mute

    mute = active_mute(user) if getattr(user, "is_authenticated", False) else None
    if mute is not None:
        if mute.expires_at is None:
            return _("Your account is muted. You can read and use your settings, but not post.")
        return _("Your account is muted until %(date)s. You can read and use your settings, but not post.") % {
            "date": formats.date_format(timezone.localtime(mute.expires_at), "DATETIME_FORMAT")}
    return _("Your account is suspended.")
