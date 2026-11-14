"""Is the support notice able to reach a mailbox? Plain checks of the email settings, shared by the system check
(support/checks.py), the admin inbox banner and `manage.py send_test_email`. Never reads out the password.
"""
from django.conf import settings

SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# Backends that never deliver to a real mailbox (print, keep in memory, write files, drop).
LOCAL_BACKENDS = {
    "django.core.mail.backends.console.EmailBackend": "prints emails in the terminal",
    "django.core.mail.backends.locmem.EmailBackend": "keeps emails in memory",
    "django.core.mail.backends.filebased.EmailBackend": "writes emails to files",
    "django.core.mail.backends.dummy.EmailBackend": "drops every email",
}


def email_problems(backend=None):
    """Plain-English reasons why the support notice would not arrive. Empty list: the settings look complete."""
    backend = backend or settings.EMAIL_BACKEND
    problems = []
    if not settings.SUPPORT_INBOX_EMAIL:
        problems.append("SUPPORT_INBOX_EMAIL is empty: no notice is sent, messages only wait in the admin inbox.")
    if backend in LOCAL_BACKENDS:
        problems.append(f"EMAIL_BACKEND {LOCAL_BACKENDS[backend]} ({backend.rsplit('.', 2)[-2]}): nothing reaches a mailbox.")
    elif backend == SMTP_BACKEND:
        if not settings.EMAIL_HOST or (settings.EMAIL_HOST == "localhost" and not settings.EMAIL_HOST_USER):
            problems.append("EMAIL_HOST is not set (localhost, no login): unless a mail server runs on this machine, "
                            "sending fails. Gmail: EMAIL_HOST=smtp.gmail.com.")
        if settings.EMAIL_HOST_USER and not settings.EMAIL_HOST_PASSWORD:
            problems.append("EMAIL_HOST_USER is set but EMAIL_HOST_PASSWORD is empty (Gmail: an app password).")
        if settings.EMAIL_HOST_PASSWORD and not settings.EMAIL_HOST_USER:
            problems.append("EMAIL_HOST_PASSWORD is set but EMAIL_HOST_USER is empty.")
    if settings.DEFAULT_FROM_EMAIL.endswith("@localhost"):
        problems.append("DEFAULT_FROM_EMAIL is not set (webmaster@localhost): mail servers refuse it. "
                        "Use the sending account's address.")
    return problems


def describe(backend=None):
    """The settings in use, safe to print: the password only as set / not set."""
    backend = backend or settings.EMAIL_BACKEND
    lines = [f"EMAIL_BACKEND        {backend}"]
    if backend == SMTP_BACKEND:
        lines += [
            f"EMAIL_HOST           {settings.EMAIL_HOST or '(empty)'}",
            f"EMAIL_PORT           {settings.EMAIL_PORT}",
            f"EMAIL_USE_TLS        {settings.EMAIL_USE_TLS}" + (" / EMAIL_USE_SSL True" if getattr(settings, "EMAIL_USE_SSL", False) else ""),
            f"EMAIL_HOST_USER      {settings.EMAIL_HOST_USER or '(empty)'}",
            f"EMAIL_HOST_PASSWORD  {'(set, hidden)' if settings.EMAIL_HOST_PASSWORD else '(empty)'}",
        ]
    lines += [
        f"DEFAULT_FROM_EMAIL   {settings.DEFAULT_FROM_EMAIL}",
        f"SUPPORT_INBOX_EMAIL  {settings.SUPPORT_INBOX_EMAIL or '(empty)'}",
    ]
    return lines
