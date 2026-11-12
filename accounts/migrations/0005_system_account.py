"""The system account "shipmark" with the official badge (see accounts/system.py).

Unusable password and is_active=False: nobody can sign in as it. If a real person already has the
username "shipmark", the migration stops with a clear message instead of taking over their account.
"""
from django.contrib.auth.hashers import make_password
from django.db import migrations

from config import branding

USERNAME = "shipmark"


def create(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    UserBadge = apps.get_model("accounts", "UserBadge")
    existing = User.objects.filter(username__iexact=USERNAME).first()
    if existing is not None:
        if existing.is_active or not existing.password.startswith("!"):  # "!" = unusable password
            raise RuntimeError(
                'A user named "shipmark" already exists. Rename that account in the admin first; '
                "the name is reserved for the system account."
            )
        user = existing
    else:
        user = User.objects.create(
            username=USERNAME,
            display_name=branding.SITE_NAME,
            password=make_password(None),  # unusable
            is_active=False,
        )
    UserBadge.objects.get_or_create(user=user, kind="official", defaults={"note": "System account"})


def remove(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(username=USERNAME, is_active=False, password__startswith="!").delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_userbadge")]
    operations = [migrations.RunPython(create, remove)]
