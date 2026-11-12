import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone, translation
from django.utils.html import strip_tags
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from config.ratelimit import is_limited
from accounts.roles import can_write
from moderation.visibility import visible_users
from projects.badges import embed_snippets
from projects.rendering import render_user_markdown
from social.queries import is_following

from config import branding
from config.site import absolute_url

from .deletion import delete_account
from .export import build_export
from .forms import AcceptTermsForm, DeleteAccountForm, SettingsForm
from .models import User
from .links import safe_links
from .profile import (TABS, profile_built_with, profile_drafts, profile_log, profile_pinned, profile_projects,
                      profile_stats)


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
        form = SettingsForm(request.POST, request.FILES, instance=user, can_edit_profile=can_write(user))
        if is_limited("settings", user.pk, limit=30, window=600):
            form.add_error(None, _("Too many changes in a short time. Try again in a few minutes."))
        elif form.is_valid():
            user = form.save()
            # Write the message in the language the page will have after the redirect.
            with translation.override(user.preferred_language or translation.get_language()):
                messages.success(request, _("Settings saved."))
            return redirect("accounts:settings")
    else:
        form = SettingsForm(instance=user, can_edit_profile=can_write(user))
    return render(request, "accounts/settings.html", {"form": form, "can_edit_profile": can_write(user)})


@login_required
@require_http_methods(["GET", "POST"])
def accept_terms(request):
    """Asked after settings.TERMS_VERSION changes (see config.middleware.TermsAcceptanceMiddleware)."""
    user = request.user
    target = _safe_next(request) or settings.LOGIN_REDIRECT_URL
    if user.terms_version_accepted == settings.TERMS_VERSION:
        return redirect(target)
    form = AcceptTermsForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save(user)
        messages.success(request, _("Thank you. You accepted the updated Terms."))
        return redirect(target)
    return render(request, "accounts/accept_terms.html", {"form": form, "next": _safe_next(request)})


@login_required
@require_http_methods(["POST"])
def export_data(request):
    """JSON file with the signed-in user's data. POST, so a link preview or prefetch never triggers it."""
    user = request.user
    if is_limited("export", user.pk, limit=10, window=3600):
        messages.error(request, _("Too many downloads in a short time. Try again later."))
        return redirect("accounts:settings")
    data = build_export(user, absolute=absolute_url)
    filename = f"{branding.SITE_NAME.lower()}-{user.username}-{timezone.now():%Y-%m-%d}.json"
    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2), content_type="application/json; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "no-store"
    return response


@login_required
@require_http_methods(["GET", "POST"])
def delete_account_page(request):
    """Explains what happens, then deletes after the user types their username.

    Allowed for suspended users too: deleting your data is a right, not a write to the site.
    """
    user = request.user
    form = DeleteAccountForm(request.POST or None, user=user)
    if request.method == "POST":
        if is_limited("account_delete", user.pk, limit=10, window=3600):
            form.add_error(None, _("Too many attempts. Try again later."))
        elif form.is_valid():
            logout(request)
            delete_account(user)
            messages.success(request, _("Your account and everything in it were deleted."))
            return redirect("pages:landing")
    return render(request, "accounts/delete_account.html", {"form": form})


def profile(request, username):
    """Public profile. Unknown and suspended users give the same 404: no hint that the account exists."""
    try:
        person = visible_users(User.objects.all()).get(username__iexact=username)
    except User.DoesNotExist:
        raise Http404
    if person.username != username:  # /u/Danylo/ -> /u/danylo/
        return redirect("accounts:profile", username=person.username, permanent=True)
    is_me = request.user.pk == person.pk
    projects = profile_projects(person)
    about_html = render_user_markdown(person.about) if person.about else ""
    tab = request.GET.get("tab") if request.GET.get("tab") in TABS else "projects"
    context = {
        "person": person,
        "is_me": is_me,
        "tab": tab,
        "links": safe_links(person),  # only http(s), whatever is stored
        "stats": profile_stats(person, projects),
        "projects": projects,
        "pinned": profile_pinned(person, projects),
        "about_html": about_html,
        "about_text": " ".join(strip_tags(about_html).split())[:300],  # for the page description: no markup
        "following": is_following(request.user, person),
        "drafts": profile_drafts(person) if is_me and tab == "projects" else [],  # drafts are private to the owner
        "embed": embed_snippets(person) if is_me and tab == "projects" else None,
    }
    if tab == "log":
        context["log_entries"] = profile_log(person)
    elif tab == "about":
        context["skills"] = list(person.skills.all())
        context["built_with"] = profile_built_with(person)
    return render(request, "accounts/profile.html", context)
