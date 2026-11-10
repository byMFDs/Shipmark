import django.utils.timezone
from django.db import migrations, models
from django.db.models import F


def copy_checked_at(apps, schema_editor):
    # Existing links: the first check is not known, the latest one is the closest honest value.
    apps.get_model("verification", "RepoLink").objects.update(earned_at=F("checked_at"))


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0003_uptimecheck"),
    ]

    operations = [
        migrations.AddField(
            model_name="repolink",
            name="earned_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.RunPython(copy_checked_at, migrations.RunPython.noop),
    ]
