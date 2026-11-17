"""Стабільна ознака системного акаунта замість перевірки за username."""
from django.db import migrations, models
from django.db.models import Q


def mark_system_account(apps, schema_editor):
    """Позначає акаунт, створений міграцією 0005 (username "shipmark", без пароля, неактивний)."""
    User = apps.get_model("accounts", "User")
    User.objects.filter(username="shipmark", is_active=False).update(is_system_account=True)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_user_community_notified_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_system_account",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=Q(is_system_account=True), fields=("is_system_account",), name="one_system_account",
            ),
        ),
        migrations.RunPython(mark_system_account, migrations.RunPython.noop),
    ]
