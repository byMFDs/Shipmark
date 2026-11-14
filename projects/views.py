"""Сторінки й дії проєкту: створення, редагування, публікація, перевірки, скриншоти, журнал."""
import math
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_http_methods, require_POST

from accounts.github import github_id as github_user_id
from accounts.roles import can_write
from moderation.pages import write_blocked_message
from moderation.visibility import banned

from config.ratelimit import claim_cooldown, cooldown_left, is_limited, limited_for, release_cooldown
from verification import domain as domains
from verification.models import DomainVerification
from social.queries import like_state
from verification.repo import AUTHORED, FORK, TOKEN_FILE, RepoCheckError, repo_token_for, run_check
from verification.uptime import uptime_summary, with_uptime

from .forms import BuildLogForm, ProjectForm
from .badges import embed_snippets
from .images import clean_screenshot
from .models import LOG_ENTRIES_PER_DAY, MAX_SCREENSHOTS, BuildLogEntry, Project, Screenshot
from .proof import checked_facts
from .rendering import MAX_LENGTH, render_user_markdown

LOG_SHOWN = 50  # entries on the project page

TOO_MANY = _("Too many changes in a short time. Try again in a few minutes.")


def _locked(request):
    """Відповідь для тих, хто не може писати.

    Suspended and muted users can read but not write (accounts.roles.can_write)."""
    return HttpResponseForbidden(write_blocked_message(request.user))


def owner_project(view=None, *, cleanup=False):
    """Декоратор: проєкт з адреси, лише власний (інакше 404).

    Loads the project from the URL and makes sure it is the signed-in user's.

    Anyone else gets a 404, the same as for a project that does not exist, so URLs
    cannot be used to find out which drafts exist. Used on every owner-only view.
    POST needs `can_write`; a project removed by moderators accepts no changes. `cleanup=True` (delete,
    unpublish) stays open to muted owners and for removed projects: taking your own work down is allowed.
    Suspended owners (an admin decision) change nothing.
    """
    if view is None:
        return lambda v: owner_project(v, cleanup=cleanup)

    @wraps(view)
    @login_required
    def wrapper(request, username, slug, *args, **kwargs):
        project = get_object_or_404(Project.objects.select_related("owner"), owner__username=username, slug=slug)
        if project.owner_id != request.user.pk:
            raise Http404
        if request.method == "POST":
            if request.user.is_suspended or (not cleanup and not can_write(request.user)):
                return _locked(request)
            if not cleanup and project.status == Project.Status.REMOVED:
                return HttpResponseForbidden(_("Moderators removed this project. It cannot be changed."))
        return view(request, project, *args, **kwargs)
    return wrapper


# ---------- Create, edit ----------

def _edit_url(project, anchor=""):
    return reverse("projects:edit", args=[project.owner.username, project.slug]) + anchor


def _uploads_limited(request, images):
    """Ліміт завантажень: кожна картинка рахується окремо.

    One rate-limit hit per image (20 per hour per user), so several files count like several uploads."""
    return any([is_limited("screenshot_add", request.user.pk, limit=20, window=3600) for _image in images])


def store_screenshots(project, images):
    """Додає перевірені картинки після наявних.

    Saves already validated images after the existing ones. Returns how many were stored.

    The project row is locked, so two parallel saves cannot both pass the limit (PostgreSQL; SQLite
    serializes writes anyway). Extra images over the limit are dropped, never stored.
    """
    if not images:
        return 0
    with transaction.atomic():
        Project.objects.select_for_update().get(pk=project.pk)
        count = project.screenshots.count()
        room = max(MAX_SCREENSHOTS - count, 0)
        for offset, content in enumerate(images[:room]):
            Screenshot.objects.create(project=project, image=content, order=count + offset)
    return min(len(images), room)


def _publish(project):
    """Публікує чернетку (прихований проєкт власник не повертає).

    Only drafts can be published. A hidden project is a moderation decision; the owner cannot undo it."""
    if project.status != Project.Status.DRAFT:
        return False
    project.status = Project.Status.PUBLISHED
    project.launched_at = project.launched_at or timezone.now()
    project.save(update_fields=["status", "launched_at", "updated_at"])
    return True


@login_required
@require_http_methods(["GET", "POST"])
def new(request):
    """Створення проєкту."""
    form = ProjectForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if not can_write(request.user):
            return _locked(request)
        if is_limited("project_create", request.user.pk, limit=10, window=3600):
            form.add_error(None, TOO_MANY)
        elif form.is_valid() and _uploads_limited(request, form.cleaned_data["screenshots"]):
            form.add_error("screenshots", TOO_MANY)
        elif form.is_valid():
            project = form.save(owner=request.user)
            stored = store_screenshots(project, form.cleaned_data["screenshots"])
            messages.success(request, _("Draft saved.") if stored else _("Draft saved. Add screenshots, then publish."))
            return redirect(_edit_url(project, "#screenshots" if stored else ""))
    return render(request, "projects/form.html", {"form": form, "project": None, "max_screenshots": MAX_SCREENSHOTS})


@owner_project
@require_http_methods(["GET", "POST"])
def edit(request, project):
    """Редагування проєкту зі скриншотами й публікацією.

    Saves the fields and the chosen screenshots together. "Publish project" in the same form saves, then publishes."""
    screenshots = list(project.screenshots.all())
    form = ProjectForm(request.POST or None, request.FILES or None, instance=project,
                       existing_screenshots=len(screenshots))
    if request.method == "POST":
        if is_limited("project_edit", request.user.pk, limit=60, window=600):
            form.add_error(None, TOO_MANY)
        elif form.is_valid() and _uploads_limited(request, form.cleaned_data["screenshots"]):
            form.add_error("screenshots", TOO_MANY)
        elif form.is_valid():
            form.save()
            stored = store_screenshots(project, form.cleaned_data["screenshots"])
            if "publish" in request.POST and _publish(project):
                messages.success(request, _("Published."))
                return redirect(project)
            if stored:
                messages.success(request, ngettext(
                    "Changes saved. %(count)d screenshot added.", "Changes saved. %(count)d screenshots added.", stored,
                ) % {"count": stored})
                return redirect(_edit_url(project, "#screenshots"))
            messages.success(request, _("Changes saved."))
            return redirect(_edit_url(project))
    return render(request, "projects/form.html", {
        "form": form,
        "project": project,
        "screenshots": screenshots,
        "max_screenshots": MAX_SCREENSHOTS,
        "repo_link": _current_repo_link(project),
        "repo_wait": (_repo_wait_text(project, wait)
                      if project.repo_full_name and (wait := cooldown_left("repo_check", _repo_key(project))) else ""),
        "repo_token": repo_token_for(project) if project.repo_full_name else "",
        "repo_token_file": TOKEN_FILE,
        **_domain_context(project, domains.verification_for(project, create=True)),
    })


@login_required
@require_POST
def preview(request):
    """Прев'ю markdown для редактора.

    Markdown preview for the editor (JS). Same renderer as the project page."""
    if not can_write(request.user):
        return _locked(request)
    if is_limited("project_preview", request.user.pk, limit=120, window=600):
        return JsonResponse({"error": TOO_MANY}, status=429)
    text = request.POST.get("text", "")
    if len(text) > MAX_LENGTH:
        return HttpResponseBadRequest(_("The description is too long."))
    return JsonResponse({"html": render_user_markdown(text)})


# ---------- Repository check ----------

REPO_CHECK_COOLDOWN = 600       # seconds between checks of the same repository for one project
REPO_CHECKS_PER_HOUR = 6        # per project, any repository (typos, switching repositories)
REPO_CHECKS_PER_USER_HOUR = 20  # per person, all projects together: each check is several GitHub API calls


def _repo_key(project):
    return f"{project.pk}:{project.repo_full_name.lower()}"


def _repo_wait_text(project, seconds):
    """Текст «перевірте знову через N хвилин»."""
    minutes = math.ceil(seconds / 60)
    return ngettext(
        "%(repo)s was checked a moment ago. You can check it again in %(count)d minute.",
        "%(repo)s was checked a moment ago. You can check it again in %(count)d minutes.", minutes,
    ) % {"repo": project.repo_full_name, "count": minutes}


def _current_repo_link(project):
    """Результат перевірки для поточної назви репозиторію.

    The check result for the repository saved now. A result for an older name is stale: show nothing."""
    link = getattr(project, "repo_link", None)
    if link is None or not project.repo_full_name or link.repo_full_name.lower() != project.repo_full_name.lower():
        return None
    return link


@owner_project
@require_POST
def repo_check(request, project):
    """Перевірка репозиторію для марки «Repo owner»."""
    back = redirect("projects:edit", username=project.owner.username, slug=project.slug)
    github_id = github_user_id(request.user)
    if not project.repo_full_name:
        messages.error(request, _("Add a GitHub repository and save the project first."))
    elif github_id is None:
        messages.error(request, _("Sign in with GitHub to check a repository."))
    # After the cheap checks, so they do not use anything up. The cooldown belongs to this project AND this
    # repository: after fixing a typo or linking another repository the owner can check it at once.
    elif wait := claim_cooldown("repo_check", _repo_key(project), REPO_CHECK_COOLDOWN):
        messages.info(request, _repo_wait_text(project, wait))
    elif wait := max(limited_for("repo_check_hour", project.pk, REPO_CHECKS_PER_HOUR, 3600),
                     limited_for("repo_check_user", request.user.pk, REPO_CHECKS_PER_USER_HOUR, 3600)):
        release_cooldown("repo_check", _repo_key(project))  # nothing was checked, so no cooldown either
        minutes = math.ceil(wait / 60)
        messages.info(request, ngettext(
            "That is enough checks for this hour. You can check again in %(count)d minute.",
            "That is enough checks for this hour. You can check again in %(count)d minutes.", minutes,
        ) % {"count": minutes})
    else:
        try:
            result = run_check(project, github_id, actor=request.user)
        except RepoCheckError as exc:
            messages.error(request, exc.message)
        else:
            if result.outcome == AUTHORED and result.link.is_verified:
                messages.success(request, _("Repository checked. You earned Repo owner."))
            elif result.outcome == AUTHORED:
                messages.success(request, _("Repository checked. Repo owner will appear after a short manual review."))
            elif result.outcome == FORK:
                messages.error(request, _("This repository is a fork. Forks cannot earn Repo owner; link the original repository."))
            else:
                messages.error(request, _("This repository is not owned by your personal GitHub account, "
                                          "and its verification file was not found."))
    return back


# ---------- Domain verification ----------

def _domain_context(project, row):
    """Дані для блоку перевірки домену.

    Everything the domain section and its status block need. `row` is None without a usable domain."""
    live = domains.is_live(project)
    return {
        "domain_row": row,
        "domain_live": live,
        "domain_needs_confirm": bool(row and row.status == DomainVerification.Status.VERIFIED and not live),
        "domain_error": domains.error_message(row.last_error) if row else "",
        "domain_shared": domains.error_message("shared_host") if row and domains.is_shared_host(row.domain) else "",
        "domain_record": domains.record_value(row.token) if row else "",
        "domain_meta": domains.meta_tag(row.token) if row else "",
        "domain_home": domains.homepage_url(project, row.domain) if row else "",
        "domain_token_name": domains.TOKEN_NAME,
    }


@owner_project
@require_POST
def domain_verify(request, project):
    """«Перевірити зараз» для домену (POST або JSON).

     "Verify now". Plain POST redirects back; fetch() with Accept: application/json gets JSON."""
    wants_json = "application/json" in request.headers.get("Accept", "")
    row = domains.verification_for(project, create=True)
    ok, status = False, 200
    if not project.live_url:
        message = domains.error_message("no_url")
    elif row is None:
        message = domains.error_message("bad_host")
    elif domains.is_shared_host(row.domain):  # before the rate limit: no request is made for it
        message = domains.error_message("shared_host")
    elif (is_limited("domain_verify", project.pk, limit=5, window=600)
          or is_limited("domain_verify_user", request.user.pk, limit=30, window=3600)):
        message, status = _("Too many checks. Wait a few minutes, then verify again."), 429
    else:
        was_verified = row.status == DomainVerification.Status.VERIFIED
        try:
            domains.verify(row, request.POST.get("method", ""), actor=request.user)
        except domains.DomainCheckError as exc:
            message = exc.message
        else:
            ok = True
            message = _("Verified. Your domain is confirmed again.") if was_verified else _("Verified. You earned Domain verified.")

    if wants_json:
        html = render_to_string("projects/_domain_status.html", {"project": project, **_domain_context(project, row)},
                                request=request)
        return JsonResponse({"ok": ok, "message": message, "html": html}, status=status)
    (messages.success if ok else messages.error)(request, message)
    return redirect(reverse("projects:edit", args=[project.owner.username, project.slug]) + "#domain-title")


# ---------- Publish, delete ----------

@owner_project
@require_POST
def publish(request, project):
    if _publish(project):
        messages.success(request, _("Published."))
    return redirect(project)


@owner_project(cleanup=True)
@require_POST
def unpublish(request, project):
    """Знімає проєкт з публікації в чернетку."""
    if project.status == Project.Status.PUBLISHED:
        project.status = Project.Status.DRAFT
        project.save(update_fields=["status", "updated_at"])
        messages.success(request, _("Moved back to drafts."))
    return redirect("projects:edit", username=project.owner.username, slug=project.slug)


@owner_project(cleanup=True)
@require_http_methods(["GET", "POST"])
def delete(request, project):
    """Видалення проєкту з підтвердженням.

    GET asks for confirmation, POST deletes."""
    if request.method == "POST":
        project.delete()  # screenshots go with it; signals remove the files
        messages.success(request, _("Project deleted."))
        return redirect("accounts:profile", username=request.user.username)
    return render(request, "projects/delete.html", {"project": project})


# ---------- Screenshots ----------

@owner_project
@require_POST
def screenshot_add(request, project):
    """Завантаження одного скриншота окремо від форми.

    Upload without the rest of the form (one file, field "image"). The editor uses the main form."""
    edit_url = redirect(_edit_url(project, "#screenshots"))
    upload = request.FILES.get("image")
    if not upload:
        messages.error(request, _("Choose an image first."))
        return edit_url
    if is_limited("screenshot_add", request.user.pk, limit=20, window=3600):
        messages.error(request, TOO_MANY)
        return edit_url
    try:
        content = clean_screenshot(upload)
    except ValidationError as error:
        messages.error(request, error.messages[0])
        return edit_url
    if not store_screenshots(project, [content]):
        messages.error(request, _("A project can have at most 4 screenshots. Remove one first."))
        return edit_url
    messages.success(request, _("Screenshot added."))
    return edit_url


def _renumber(project):
    """Перенумеровує порядок скриншотів."""
    shots = list(project.screenshots.all())
    for index, shot in enumerate(shots):
        shot.order = index
    Screenshot.objects.bulk_update(shots, ["order"])
    return shots


@owner_project
@require_POST
def screenshot_delete(request, project, pk):
    """Видаляє скриншот."""
    shot = get_object_or_404(project.screenshots, pk=pk)  # only this project's screenshots
    shot.delete()
    _renumber(project)
    messages.success(request, _("Screenshot removed."))
    return redirect(_edit_url(project, "#screenshots"))


@owner_project
@require_POST
def screenshot_move(request, project, pk):
    """Переміщує скриншот вгору чи вниз."""
    shot = get_object_or_404(project.screenshots, pk=pk)
    direction = request.POST.get("direction")
    if direction not in ("up", "down"):
        return HttpResponseBadRequest()
    shots = _renumber(project)
    index = next(i for i, s in enumerate(shots) if s.pk == shot.pk)
    target = index - 1 if direction == "up" else index + 1
    if 0 <= target < len(shots):
        shots[index], shots[target] = shots[target], shots[index]
        for i, s in enumerate(shots):
            s.order = i
        Screenshot.objects.bulk_update(shots, ["order"])
    return redirect(_edit_url(project, "#screenshots"))


# ---------- Build log ----------

def _wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def _has_launch(project):
    return project.log_entries.filter(kind=BuildLogEntry.Kind.LAUNCH).exists()


def _log_limit_reached(project):
    """Ліміт записів журналу на день.

    10 entries a day per project. The DB count survives cache restarts; the cache counter
    also counts entries that were deleted again, so add + delete cannot get around the limit."""
    recent = project.log_entries.filter(created_at__gte=timezone.now() - timedelta(days=1)).count()
    return recent >= LOG_ENTRIES_PER_DAY or is_limited(
        "buildlog_add", project.pk, limit=LOG_ENTRIES_PER_DAY, window=24 * 3600)


@owner_project
@require_POST
def log_add(request, project):
    """Додає запис журналу (POST або JSON).

    Plain POST redirects back to the project page; fetch() with Accept: application/json gets JSON."""
    form = BuildLogForm(request.POST, project=project)
    status, entry = 400, None
    if form.is_valid():
        if _log_limit_reached(project):
            form.add_error(None, _("A project can get at most %(n)s build log entries a day. Try again tomorrow.")
                           % {"n": LOG_ENTRIES_PER_DAY})
            status = 429
        else:
            entry = form.save()

    if entry is None:
        if _wants_json(request):
            errors = [str(e) for field_errors in form.errors.values() for e in field_errors]
            return JsonResponse({"ok": False, "message": errors[0]}, status=status)
        # Without JS: show the page again with the errors and the text kept.
        return _render_detail(request, _detail_queryset().get(pk=project.pk), log_form=form, status=status)

    message = _("Posted. Launch date set to today.") if entry.is_launch else _("Posted.")
    if _wants_json(request):
        context = {"entry": entry, "project": project, "is_owner": True}
        return JsonResponse({
            "ok": True,
            "message": message,
            "html": render_to_string("projects/_log_entry.html", context, request=request),
            "launched_html": render_to_string("projects/_launched.html", {"project": project}, request=request),
            "can_launch": not _has_launch(project),
        })
    messages.success(request, message)
    return redirect(project.get_absolute_url() + "#build-log")


@owner_project
@require_POST
def log_delete(request, project, pk):
    """Видаляє запис журналу.

    Deleting the launch entry keeps launched_at: the project did launch on that date."""
    entry = get_object_or_404(project.log_entries, pk=pk)  # only this project's entries
    if is_limited("buildlog_delete", request.user.pk, limit=60, window=3600):
        if _wants_json(request):
            return JsonResponse({"ok": False, "message": TOO_MANY}, status=429)
        messages.error(request, TOO_MANY)
    else:
        entry.delete()
        if _wants_json(request):
            return JsonResponse({"ok": True, "message": _("Entry deleted."), "can_launch": not _has_launch(project)})
        messages.success(request, _("Entry deleted."))
    return redirect(project.get_absolute_url() + "#build-log")


# ---------- Public page ----------

def _detail_queryset():
    return with_uptime(Project.objects.select_related("owner", "repo_link")
                       .prefetch_related("tags", "built_with", "screenshots", "domain_verifications", "owner__badges")
                       .annotate(owner_banned=banned("owner")))


def detail(request, username, slug):
    """Сторінка проєкту."""
    project = get_object_or_404(_detail_queryset(), owner__username__iexact=username, slug=slug)
    is_owner = request.user.is_authenticated and request.user.pk == project.owner_id
    # Drafts, hidden and removed projects, and everything of a suspended or banned user: 404 for everyone
    # but the owner (who sees why a removed project is not public).
    if not is_owner and (project.status != Project.Status.PUBLISHED or project.owner.is_suspended
                         or project.owner_banned):
        raise Http404
    if project.owner.username != username:  # /u/Name/slug/ -> /u/name/slug/
        return redirect(project, permanent=True)
    return _render_detail(request, project)


def _render_detail(request, project, log_form=None, status=200):
    """Збирає сторінку проєкту: скриншоти, марки, аптайм, журнал."""
    is_owner = request.user.is_authenticated and request.user.pk == project.owner_id
    screenshots = list(project.screenshots.all())
    hallmarks = project.hallmarks
    uptime = uptime_summary(project)
    entries = list(project.log_entries.all()[:LOG_SHOWN + 1])  # one extra tells whether there are more
    like_count, liked = like_state(project, request.user)
    return render(request, "projects/detail.html", {
        "project": project,
        "person": project.owner,
        "is_owner": is_owner,
        "screenshots": screenshots,
        "hallmarks": hallmarks,
        "checked": checked_facts(project),
        # Shown while the project is Live, and afterwards as long as there is a check history.
        "uptime": uptime if hallmarks["live"].earned or uptime.last_checked_at else None,
        "tools": list(project.built_with.all()),
        "project_tags": list(project.tags.all()),
        "log_entries": entries[:LOG_SHOWN],
        "log_has_more": len(entries) > LOG_SHOWN,
        "log_form": (log_form or BuildLogForm(project=project)) if is_owner else None,
        "can_launch": is_owner and not _has_launch(project),
        "like_count": like_count,
        "liked": liked,
        # The badge panel is for the author, and only once there is a public page to link to.
        "embed": embed_snippets(project.owner, project) if is_owner and project.status == Project.Status.PUBLISHED else None,
    }, status=status)
