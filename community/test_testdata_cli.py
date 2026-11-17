"""Exercise real commits and verified cleanup backups on disposable SQLite and media."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from django.conf import settings
from django.test import SimpleTestCase


class StandaloneCleanupTests(SimpleTestCase):
    def test_committed_cleanup_backup_and_conflict(self):
        with tempfile.TemporaryDirectory(prefix="shipmark-testdata-") as root:
            env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings.dev",
                   "DATABASE_URL": f"sqlite:///{root}/db.sqlite3", "DEBUG": "true",
                   "SITE_URL": "http://localhost:8000", "LOG_DIR": f"{root}/logs",
                   "TESTDATA_SCRATCH": root}
            script = '''
import os, json, sqlite3
from pathlib import Path
from io import StringIO
import django
django.setup()
from django.conf import settings
from django.core.management import call_command, CommandError
from accounts.models import User
from community.models import Board, Thread, TestDataObject, TestDataFile
from community import services
from pages.stats import public_user_count
root = Path(os.environ["TESTDATA_SCRATCH"])
settings.MEDIA_ROOT = root / "media"
call_command("migrate", verbosity=0)
def run(mode, *args):
    out = StringIO()
    call_command("community_testdata", mode, *args, stdout=out)
    return json.loads(out.getvalue())
control = User.objects.create_user("control", password=None)
real_thread = services.create_thread(control, Board.objects.get(slug="help"), "Real", "Keep")
before = public_user_count()
seeded = run("seed")
assert public_user_count() == before + 25
assert run("seed")["created"] == {}
assert run("activity", "--append")["counts"]["accounts.user"] == 25
thread = Thread.objects.get(pk=seeded["ids"]["community.thread"][0])
reply = services.create_reply(control, thread, body="Real reply")
try:
    run("clean", "--all", "--backup-dir", str(root / "backups"))
except CommandError as error:
    assert "untracked dependencies" in str(error)
else:
    raise AssertionError("Real reply was not protected")
assert User.objects.count() == before + 26  # includes system account
# Remove only the control reply deliberately created by this test.
reply.delete()
preview = run("clean", "--all", "--dry-run")
assert preview["counts"]["community.thread"] == 16
cleaned = run("clean", "--all", "--backup-dir", str(root / "backups"))
assert cleaned["blocked"] is None
assert not cleaned["file_delete_failures"]
assert not TestDataObject.objects.exists() and not TestDataFile.objects.exists()
assert User.objects.filter(pk=control.pk).exists()
assert Thread.objects.filter(pk=real_thread.pk, body="Keep").exists()
assert public_user_count() == before
assert not list((root / "media").rglob("*.webp"))
with sqlite3.connect(Path(cleaned["backup"]) / "db.sqlite3") as saved:
    assert saved.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    assert saved.execute("SELECT COUNT(*) FROM community_testdataobject").fetchone()[0] > 0
assert run("clean", "--all")["counts"] == {}
print("Standalone SQLite lifecycle and verified backup passed")
'''
            result = subprocess.run([sys.executable, "-c", script], cwd=settings.BASE_DIR,
                                    env=env, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
