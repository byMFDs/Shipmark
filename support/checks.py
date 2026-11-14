"""System check: in production (DEBUG off), warn when the support notice cannot reach a mailbox.

Shows on `manage.py check`, `migrate` and every other management command, so a missing SMTP setup is visible at deploy.
Dev (DEBUG on) prints emails in the terminal on purpose and the test runner keeps them in memory: no warning; `send_test_email` explains it there.
"""
from django.conf import settings
from django.core.checks import Tags, Warning, register

from .mailcheck import email_problems


@register(Tags.compatibility)
def support_email_check(app_configs, **kwargs):
    if settings.DEBUG or settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend":
        return []  # dev prints on purpose; locmem is the test runner's backend
    return [
        Warning(problem, hint="See docs/DEPLOY_NOTES.md, 'Support inbox', and run `python manage.py send_test_email`.",
                id=f"support.W00{index}")
        for index, problem in enumerate(email_problems(), start=1)
    ]
