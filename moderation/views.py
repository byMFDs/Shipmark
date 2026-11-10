"""Report a project or a profile. Signed-in users only; the admin handles the reports."""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from config.ratelimit import is_limited
from projects.models import Project

from .forms import ReportForm
from .models import Report

User = get_user_model()

# Per signed-in user. A person rarely reports more than a couple of things an hour.
REPORT_LIMIT = (5, 3600)


def _handle(request, *, target_kwargs, target_repr, title, back_url):
    """Shared by both views. The target was already checked: it is public and not the reporter's own."""
    user = request.user
    form = ReportForm(request.POST or None)
    if request.method == "POST":
        if user.is_suspended:
            return HttpResponseForbidden(_("Your account is suspended."))
        if is_limited("report", user.pk, *REPORT_LIMIT):
            form.add_error(None, _("Too many reports in a short time. Try again later."))
        elif form.is_valid():
            if Report.objects.filter(reporter=user, status=Report.Status.OPEN, **target_kwargs).exists():
                messages.info(request, _("You already reported this. We will look at it."))
                return redirect(back_url)
            try:
                with transaction.atomic():  # the unique constraints also stop a double click
                    Report.objects.create(
                        reporter=user, target_repr=target_repr,
                        reason=form.cleaned_data["reason"], details=form.cleaned_data["details"].strip(),
                        **target_kwargs,
                    )
            except IntegrityError:
                pass
            messages.success(request, _("Thank you. We will review your report."))
            return redirect(back_url)
    return render(request, "moderation/report.html", {"form": form, "title": title, "back_url": back_url})


@login_required
@require_http_methods(["GET", "POST"])
def report_project(request, username, slug):
    # Published and not suspended, like every public page: anything else is a 404.
    project = get_object_or_404(
        Project.objects.select_related("owner"),
        owner__username__iexact=username, slug=slug,
        status=Project.Status.PUBLISHED, owner__is_suspended=False,
    )
    if project.owner_id == request.user.pk:
        messages.error(request, _("You cannot report your own project."))
        return redirect(project)
    return _handle(
        request, target_kwargs={"project": project}, target_repr=str(project),
        title=_("Report %(name)s") % {"name": project.name}, back_url=project.get_absolute_url(),
    )


@login_required
@require_http_methods(["GET", "POST"])
def report_user(request, username):
    person = get_object_or_404(User, username__iexact=username, is_suspended=False)
    back = reverse("accounts:profile", args=[person.username])
    if person.pk == request.user.pk:
        messages.error(request, _("You cannot report yourself."))
        return redirect(back)
    return _handle(
        request, target_kwargs={"target_user": person}, target_repr=str(person),
        title=_("Report @%(username)s") % {"username": person.username}, back_url=back,
    )
