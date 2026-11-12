from django import forms
from django.core.exceptions import ValidationError
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


ACTION_LABELS = {
    "dismiss": _("Dismiss: no action"),
    "remove_project": _("Remove the project"),
    "clear_profile": _("Clear profile fields"),
    "mute": _("Mute"),
    "ban": _("Ban"),
}


class ActionForm(StyledFormMixin, forms.Form):
    """One form for every moderator decision. The reason is required: the affected person sees it.

    Limits (settings.MODERATION_MAX_*) and the superuser-only permanent option are checked here and again in
    moderation.sanctions, so a forged POST cannot get around them.
    """

    action = forms.ChoiceField(label=_("Decision"), widget=forms.RadioSelect)
    reason = forms.CharField(
        label=_("Reason (the person sees this)"), min_length=10, max_length=MAX_DETAILS,
        widget=forms.Textarea(attrs={"rows": 4, "maxlength": MAX_DETAILS}),
        help_text=_("Plain and specific: what was wrong and which rule it breaks. Never name the reporter."),
        error_messages={"required": _("Write the reason. The person will see it."),
                        "min_length": _("Write at least a short sentence (10 characters).")},
    )
    category = forms.ChoiceField(label=_("Report reason"), choices=Report.Reason.choices, required=False)
    fields = forms.MultipleChoiceField(
        label=_("Fields to clear"), required=False, widget=forms.CheckboxSelectMultiple,
        choices=[("avatar", _("Avatar")), ("bio", _("Bio")), ("links", _("Links"))],
    )
    length = forms.IntegerField(label=_("Length"), min_value=1, max_value=100000, required=False)
    unit = forms.ChoiceField(label=_("Unit"), choices=[("hours", _("hours")), ("days", _("days"))],
                             initial="days", required=False)
    permanent = forms.BooleanField(label=_("Permanent (superusers only)"), required=False)

    def __init__(self, *args, actions, actor, with_category=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields["action"].choices = [(a, ACTION_LABELS[a]) for a in actions]
        self.fields["action"].widget.attrs["class"] = "radio"
        self.fields["fields"].widget.attrs["class"] = "checkbox"
        self.fields["permanent"].widget.attrs["class"] = "checkbox"
        if not with_category:
            del self.fields["category"]
        else:
            self.fields["category"].required = True
        if "clear_profile" not in actions:
            del self.fields["fields"]
        if not {"mute", "ban"} & set(actions):
            for name in ("length", "unit", "permanent"):
                del self.fields[name]
        elif not getattr(actor, "is_superuser", False):
            del self.fields["permanent"]  # a moderator never sees it, and a posted value is ignored

    def clean(self):
        from datetime import timedelta

        from .sanctions import check_length

        data = super().clean()
        action = data.get("action")
        if action in ("mute", "ban"):
            if data.get("permanent"):
                data["timedelta"] = None
            elif not data.get("length"):
                self.add_error("length", _("Say how long."))
                return data
            else:
                hours = data["length"] * (24 if data.get("unit") != "hours" else 1)
                data["timedelta"] = timedelta(hours=hours)
            try:
                check_length(action, data["timedelta"], self.actor)
            except ValidationError as error:
                self.add_error("length", error)
        if action == "clear_profile" and not data.get("fields"):
            self.add_error("fields", _("Choose at least one field."))
        return data
