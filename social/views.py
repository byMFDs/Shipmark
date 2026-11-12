from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from accounts.roles import can_write
from config.ratelimit import is_limited
from moderation.pages import write_blocked_message
from moderation.visibility import visible_users
from projects.models import Project

from . import queries
from .models import Follow, Like

User = get_user_model()

# Per signed-in user. Generous for a person, tight for a script.
FOLLOW_LIMIT = (60, 3600)
LIKE_LIMIT = (120, 3600)


def _wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def _safe_next(request, default):
    """Where a plain POST goes back to. Only addresses on this site are accepted."""
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return default


def _fail(request, message, status, back):
    if _wants_json(request):
        return JsonResponse({"ok": False, "message": message}, status=status)
    messages.error(request, message)
    return redirect(back)


def _done(request, data, message, back):
    if _wants_json(request):
        return JsonResponse({"ok": True, **data})
    messages.success(request, message)
    return redirect(back)


def social_action(name, limit, window):
    """POST only; signed in; not suspended; rate limited. Checked before the target is even looked up."""
    def decorator(view):
        @wraps(view)
        @require_POST
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if _wants_json(request):
                    return JsonResponse({"ok": False, "message": _("Sign in to do this.")}, status=401)
                return redirect_to_login(_safe_next(request, "/"))
            back = _safe_next(request, "/")
            if not can_write(request.user):
                return _fail(request, write_blocked_message(request.user), 403, back)
            if is_limited(name, request.user.pk, limit=limit, window=window):
                return _fail(request, _("Too many changes in a short time. Try again in a few minutes."), 429, back)
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


# ---------- Follow ----------

def _person(username):
    # Suspended and banned users look the same as missing ones.
    return get_object_or_404(visible_users(User.objects.all()), username__iexact=username)


def _follow_change(request, username, follow):
    person = _person(username)
    back = _safe_next(request, reverse("accounts:profile", args=[person.username]))
    if person.pk == request.user.pk:
        return _fail(request, _("You cannot follow yourself."), 400, back)
    if follow:
        Follow.objects.get_or_create(follower=request.user, following=person)  # idempotent; the unique pair also guards races
        message = _("Following @%(username)s.") % {"username": person.username}
    else:
        Follow.objects.filter(follower=request.user, following=person).delete()
        message = _("Unfollowed @%(username)s.") % {"username": person.username}
    return _done(request, {"pressed": follow, "count": queries.follower_count(person)}, message, back)


@social_action("follow", *FOLLOW_LIMIT)
def follow(request, username):
    return _follow_change(request, username, True)


@social_action("follow", *FOLLOW_LIMIT)
def unfollow(request, username):
    return _follow_change(request, username, False)


# ---------- Like ----------

def _likeable(username, slug):
    """Published and not suspended: anything else is a 404, drafts of other people included."""
    return get_object_or_404(
        queries.published_projects().select_related("owner"), owner__username__iexact=username, slug=slug,
    )


def _like_change(request, username, slug, like):
    project = _likeable(username, slug)
    back = _safe_next(request, project.get_absolute_url())
    # Decision: no likes on your own project. A like is a signal from someone else, and
    # self-likes would only pad the number.
    if project.owner_id == request.user.pk:
        return _fail(request, _("You cannot like your own project."), 400, back)
    if like:
        Like.objects.get_or_create(user=request.user, project=project)
        message = _("Liked.")
    else:
        Like.objects.filter(user=request.user, project=project).delete()
        message = _("Like removed.")
    count, _liked = queries.like_state(project, request.user)
    return _done(request, {"pressed": like, "count": count}, message, back)


@social_action("like", *LIKE_LIMIT)
def like(request, username, slug):
    return _like_change(request, username, slug, True)


@social_action("like", *LIKE_LIMIT)
def unlike(request, username, slug):
    return _like_change(request, username, slug, False)


# ---------- Feed ----------

TABS = ("following", "latest")


def _page_number(request):
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        return 1
    if page > queries.MAX_PAGE:
        raise Http404
    return max(page, 1)


def _page_url(tab, page):
    return f"{reverse('social:feed')}?{urlencode({'tab': tab, 'page': page})}"


@require_GET
def feed(request):
    """Tab "following" needs an account; a signed-out visitor always gets "latest"."""
    user = request.user
    tab = request.GET.get("tab")
    if tab not in TABS or not user.is_authenticated:
        tab = "following" if user.is_authenticated else "latest"
    page = _page_number(request)
    items, has_next = (queries.following_feed if tab == "following" else queries.latest_launches)(user, page)
    next_url = _page_url(tab, page + 1) if has_next else ""

    if _wants_json(request):  # "Load more"
        return JsonResponse({
            "html": render_to_string("social/_items.html", {"items": items}, request=request),
            "next_url": next_url,
        })
    return render(request, "social/feed.html", {
        "tab": tab,
        "items": items,
        "page": page,
        "next_url": next_url,
        "prev_url": _page_url(tab, page - 1) if page > 1 else "",
        "latest_url": _page_url("latest", 1),
        "following_url": _page_url("following", 1),
    })
