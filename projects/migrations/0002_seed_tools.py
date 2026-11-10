from django.db import migrations
from django.utils.text import slugify

# Brand names, not translated. More can be added in the admin.
TOOLS = [
    "Claude Code", "Claude", "ChatGPT", "Codex", "Cursor", "GitHub Copilot", "Windsurf",
    "Gemini CLI", "Gemini", "Lovable", "Bolt", "v0", "Replit Agent", "Aider", "Cline",
    "Devin", "Kiro", "Zed", "Warp",
]


def seed(apps, schema_editor):
    Tool = apps.get_model("projects", "Tool")
    for name in TOOLS:
        Tool.objects.get_or_create(slug=slugify(name), defaults={"name": name})


class Migration(migrations.Migration):
    dependencies = [("projects", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
