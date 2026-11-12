"""The boards every install starts with (created by migration 0001). Admins can add, rename and hide boards.

The names and descriptions are stored in English and marked for translation here; `Board.display_name` looks the
stored text up in the catalogs, so a default board is shown in the reader's language and an admin-made one as typed.
"""
from django.utils.translation import gettext_noop

# (slug, name, description)
DEFAULT_BOARDS = [
    ("help", gettext_noop("Help and questions"), gettext_noop("Stuck on something? Ask here.")),
    ("show", gettext_noop("Show your project"), gettext_noop("Share what you shipped and how it went.")),
    ("collab", gettext_noop("Looking for collaborators"), gettext_noop("Find people to build with.")),
    ("feedback", gettext_noop("Feedback and ideas"), gettext_noop("Ask for honest feedback or suggest an idea.")),
    ("off-topic", gettext_noop("Off-topic"), gettext_noop("Everything else.")),
]
