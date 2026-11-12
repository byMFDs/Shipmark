from django.db import migrations

# A copy of community.boards.DEFAULT_BOARDS as it was when this migration was written (migrations do not import
# application code that may change later).
BOARDS = [
    ("help", "Help and questions", "Stuck on something? Ask here."),
    ("show", "Show your project", "Share what you shipped and how it went."),
    ("collab", "Looking for collaborators", "Find people to build with."),
    ("feedback", "Feedback and ideas", "Ask for honest feedback or suggest an idea."),
    ("off-topic", "Off-topic", "Everything else."),
]


def create_boards(apps, schema_editor):
    Board = apps.get_model("community", "Board")
    for order, (slug, name, description) in enumerate(BOARDS):
        Board.objects.get_or_create(slug=slug, defaults={"name": name, "description": description, "order": order})


def remove_boards(apps, schema_editor):
    """Only boards that hold no threads (a board with threads is protected)."""
    Board = apps.get_model("community", "Board")
    Board.objects.filter(slug__in=[slug for slug, _name, _description in BOARDS], threads__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("community", "0001_initial")]
    operations = [migrations.RunPython(create_boards, remove_boards)]
