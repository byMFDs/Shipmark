from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from config.ratelimit import is_limited

from .forms import SettingsForm


def _safe_next(request):
    target = request.POST.get("next") or request.GET.get("next") or ""
    ok = url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure())
    return target if ok else ""


def login_page(request):
    """Sign-in page. The button POSTs to allauth's GitHub login (CSRF-protected)."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    return render(request, "accounts/login.html", {
        "next": _safe_next(request),
        "configured": settings.GITHUB_OAUTH_CONFIGURED,
    })


@require_http_methods(["GET", "POST"])
def logout_page(request):
    """GET asks "Sign out?", POST signs out. A plain link must never log anyone out."""
    if not request.user.is_authenticated:
        return redirect(settings.LOGOUT_REDIRECT_URL)
    if request.method == "POST":
        logout(request)
        messages.success(request, _("You are signed out."))
        return redirect(settings.LOGOUT_REDIRECT_URL)
    return render(request, "accounts/logout.html")


@login_required
@require_http_methods(["GET", "POST"])
def settings_page(request):
    """Edit your own settings. There is no user id in the URL, so only request.user can be edited."""
    user = request.user
    if request.method == "POST":
        if user.is_suspended:
            return HttpResponseForbidden(_("Your account is suspended."))
        form = SettingsForm(request.POST, instance=user)
        if is_limited("settings", user.pk, limit=30, window=600):
            form.add_error(None, _("Too many changes in a short time. Try again in a few minutes."))
        elif form.is_valid():
            user = form.save()
            # Write the message in the language the page will have after the redirect.
            with translation.override(user.preferred_language or translation.get_language()):
                messages.success(request, _("Settings saved."))
            return redirect("accounts:settings")
    else:
        form = SettingsForm(instance=user)
    return render(request, "accounts/settings.html", {"form": form})
