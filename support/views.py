"""Форма підтримки, підтвердження й завантаження вкладень для персоналу.

/support/ (the form), /support/sent/ (the confirmation) and the staff-only attachment download."""
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext
from django.views.decorators.http import require_GET, require_http_methods

from . import antispam
from .forms import REFERENCE_RE, SupportForm
from .models import SupportAttachment, SupportMessage
from .notify import notify_inbox


def _sent(state=""):
    url = reverse("support:sent")
    return redirect(f"{url}?{state}" if state else url)


@require_http_methods(["GET", "POST"])
def support_form(request):
    """Форма звернення з антиспамом і сповіщенням після коміту."""
    user = request.user
    if request.method == "POST":
        form = SupportForm(request.POST, request.FILES, user=user)
        if form.is_bot:
            return _sent()  # looks like success; nothing is stored or sent
        if form.is_valid():
            keys = antispam.client_keys(request)
            data = form.cleaned_data
            if antispam.is_limited(keys):
                form.add_error(None, gettext("You have sent several messages already. Please wait an hour and try again."))
            elif not antispam.claim_first(data["email"], data["body"]):
                return _sent("again=1")
            else:
                message = _save(form, user)
                antispam.count(keys)
                transaction.on_commit(lambda: notify_inbox(message.pk))
                return _sent()
    else:
        initial = {}
        category = request.GET.get("category", "")
        if category in SupportMessage.Category.values:
            initial["category"] = category
        reference = request.GET.get("ref", "")
        if REFERENCE_RE.match(reference):
            initial.update(reference=reference, category=initial.get("category", SupportMessage.Category.BUG))
        form = SupportForm(initial=initial, user=user)
    return render(request, "support/form.html", {
        "form": form, "categories": SupportMessage.Category.choices,
    }, status=400 if form.errors else 200)


def _save(form, user):
    """Зберігає звернення й вкладення в одній транзакції."""
    data = form.cleaned_data
    with transaction.atomic():
        message = SupportMessage.objects.create(
            user=user if user.is_authenticated else None, email=data["email"], category=data["category"],
            subject=data["subject"].strip(), body=data["body"].strip(), reference=data["reference"],
        )
        for item in data["attachments"]:
            attachment = SupportAttachment(message=message, kind=item["kind"], name=item["name"], size=item["size"])
            attachment.file.save("attachment", item["content"], save=False)
            attachment.save()
    return message


@require_GET
def sent(request):
    return render(request, "support/sent.html", {"again": request.GET.get("again") == "1"})


@require_GET
def attachment(request, pk):
    """Завантаження вкладення (лише персонал з правом).

    Staff with the permission only; everyone else gets a 404 (not even "it exists"). Always a download."""
    user = request.user
    if not (user.is_authenticated and user.is_active and user.is_staff and user.has_perm("support.view_supportmessage")):
        raise Http404
    item = get_object_or_404(SupportAttachment, pk=pk)
    content_type = "text/plain; charset=utf-8" if item.kind == SupportAttachment.Kind.TEXT else "image/webp"
    response = FileResponse(item.file.open("rb"), as_attachment=True, filename=item.download_name,
                            content_type=content_type)
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "default-src 'none'; sandbox"
    response["Cache-Control"] = "private, no-store"
    return response
