from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.forms import StyledFormMixin

from .models import MAX_DETAILS, Report


class ReportForm(StyledFormMixin, forms.Form):
    reason = forms.ChoiceField(
        label=_("Reason"),
        choices=[("", _("Choose a reason")), *Report.Reason.choices],
        error_messages={"required": _("Choose a reason.")},
    )
    details = forms.CharField(
        label=_("Details (optional)"),
        required=False,
        max_length=MAX_DETAILS,
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": MAX_DETAILS}),
        help_text=_("What is wrong, and where? Do not include passwords or private data."),
    )

    def clean(self):
        data = super().clean()
        # "Something else" is useless without words.
        if data.get("reason") == Report.Reason.OTHER and not (data.get("details") or "").strip():
            self.add_error("details", _("Tell us what is wrong."))
        return data
