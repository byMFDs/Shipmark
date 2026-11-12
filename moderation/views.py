"""Report a project, a profile or a build-log entry. Signed-in users who can write; moderators handle them in /mod/."""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from accounts.roles import can_write
from config.ratelimit import is_limited
from projects.models import BuildLogEntry, Project

from .forms import ReportForm
from .models import OPEN_STATES, Report
from .pages import write_blocked_message
from .visibility import visible_owner, visible_users

User = get_user_model()

# Per signed-in user. A person rarely reports more than a couple of things an hour.
REPORT_LIMIT = (5, 3600)


def _handle(request, *, target_kwargs, target_owner, target_repr, title, back_url):
    """Shared by the report views. The target was already checked: it is public and not the reporter's own."""
    user = request.user
    form = ReportForm(request.POST or None)
    if request.method == "POST":
        if not can_write(user):
            return HttpResponseForbidden(write_blocked_message(user))
        if is_limited("report", user.pk, *REPORT_LIMIT):
            form.add_error(None, _("Too many reports in a short time. Try again later."))
        elif form.is_valid():
            if Report.objects.filter(reporter=user, status__in=OPEN_STATES, **target_kwargs).exists():
                messages.info(request, _("You already reported this. We will look at it."))
                return redirect(back_url)
            try:
                with transaction.atomic():  # the unique constraints also stop a double click
                    Report.objects.create(
                        reporter=user, target_owner=target_owner, target_repr=target_repr[:200],
                        reason=form.cleaned_data["reason"], details=form.cleaned_data["details"].strip(),
                        **target_kwargs,
                    )
            except IntegrityError:
                pass
            messages.success(request, _("Thank you. We will review your report."))
            return redirect(back_url)
    return render(request, "moderation/report.html", {"form": form, "title": title, "back_url": back_url})


def _public_project(username, slug):
    # Published, and the owner is not suspended or banned, like every public page: anything else is a 404.
    return get_object_or_404(
        visible_owner(Project.objects.filter(status=Project.Status.PUBLISHED)).select_related("owner"),
        owner__username__iexact=username, slug=slug,
    )


@login_required
@require_http_methods(["GET", "POST"])
def report_project(request, username, slug):
    project = _public_project(username, slug)
    if project.owner_id == request.user.pk:
        messages.error(request, _("You cannot report your own project."))
        return redirect(project)
    return _handle(
        request, target_kwargs={"project": project}, target_owner=project.owner, target_repr=str(project),
        title=_("Report %(name)s") % {"name": project.name}, back_url=project.get_absolute_url(),
    )


@login_required
@require_http_methods(["GET", "POST"])
def report_user(request, username):
    """A profile: name, avatar, bio, links."""
    person = get_object_or_404(visible_users(User.objects.all()), username__iexact=username)
    back = reverse("accounts:profile", args=[person.username])
    if person.pk == request.user.pk:
        messages.error(request, _("You cannot report yourself."))
        return redirect(back)
    return _handle(
        request, target_kwargs={"target_user": person}, target_owner=person, target_repr=str(person),
        title=_("Report @%(username)s") % {"username": person.username}, back_url=back,
    )


@login_required
@require_http_methods(["GET", "POST"])
def report_log_entry(request, username, slug, pk):
    project = _public_project(username, slug)
    entry = get_object_or_404(BuildLogEntry, pk=pk, project=project)
    back = f"{project.get_absolute_url()}#log-{entry.pk}"
    if project.owner_id == request.user.pk:
        messages.error(request, _("You cannot report your own project."))
        return redirect(back)
    return _handle(
        request, target_kwargs={"log_entry": entry}, target_owner=project.owner,
        target_repr=f"{project} · {entry.text[:80]}",
        title=_("Report an update on %(name)s") % {"name": project.name}, back_url=back,
    )
