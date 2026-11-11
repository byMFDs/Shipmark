"""Read the error log files written by config/errorlog.py.

    python manage.py show_errors                 # the last 20 errors, grouped by exception
    python manage.py show_errors --last 50       # more
    python manage.py show_errors --summary       # one line per exception: count, first and last time, paths
    python manage.py show_errors --full          # with the traceback of each error
    python manage.py show_errors --notfound      # 404s (notfound.jsonl) instead: the most requested paths

Files: settings.LOG_DIR / errors.jsonl and notfound.jsonl, plus their rotated copies (.1 ... .5).
In production set DJANGO_SETTINGS_MODULE=config.settings.prod, so LOG_DIR is the server's folder.
"""
import json
from collections import Counter, OrderedDict

from django.conf import settings
from django.core.management.base import BaseCommand

from config.errorlog import BACKUP_COUNT, ERRORS_FILE, NOTFOUND_FILE


def read_lines(name):
    """All records of a log file, oldest first (rotated copies first). Broken lines are skipped."""
    base = settings.LOG_DIR / name
    paths = [base.with_name(f"{name}.{i}") for i in range(BACKUP_COUNT, 0, -1)] + [base]
    records = []
    for path in paths:
        if not path.is_file():
            continue
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict):
                    records.append(record)
    return records


def group_key(record):
    if record.get("exception"):
        return record["exception"]
    status = record.get("status")
    return f"HTTP {status}" if status else record.get("level", "ERROR")


class Command(BaseCommand):
    help = "Show recent errors from the JSON error log, grouped by exception."

    def add_arguments(self, parser):
        parser.add_argument("--last", type=int, default=20, help="How many recent records to read (default 20).")
        parser.add_argument("--summary", action="store_true", help="One line per exception type.")
        parser.add_argument("--full", action="store_true", help="Print each traceback too.")
        parser.add_argument("--notfound", action="store_true", help="Show 404s (notfound.jsonl) by path.")

    def handle(self, *args, **options):
        last = max(1, options["last"])
        if options["notfound"]:
            return self.show_notfound(last)
        records = read_lines(ERRORS_FILE)
        if not records:
            self.stdout.write(f"No errors logged in {settings.LOG_DIR / ERRORS_FILE}.")
            return
        if options["summary"]:
            return self.show_summary(records)
        self.show_recent(records[-last:], options["full"])

    def show_recent(self, records, with_traceback):
        groups = OrderedDict()
        for record in reversed(records):  # newest group first
            groups.setdefault(group_key(record), []).append(record)
        self.stdout.write(f"Last {len(records)} errors, newest first, grouped by exception:\n")
        for key, items in groups.items():
            self.stdout.write(self.style.ERROR(f"{key}  ×{len(items)}"))
            for r in items:
                where = " ".join(x for x in (r.get("method", ""), r.get("path", "")) if x) or "(no request)"
                status = r.get("status") or "-"
                view = f"  view={r['view']}" if r.get("view") else ""
                ref = f"  ref={r['request_id']}" if r.get("request_id") else ""
                self.stdout.write(f"  {r.get('timestamp', '?')[:19]}  {status}  {where}{view}{ref}")
                if r.get("message"):
                    self.stdout.write(f"      {r['message']}")
                if with_traceback and r.get("traceback"):
                    for line in r["traceback"].rstrip().splitlines():
                        self.stdout.write(f"      | {line}")
            self.stdout.write("")

    def show_summary(self, records):
        groups = OrderedDict()
        for record in records:
            groups.setdefault(group_key(record), []).append(record)
        rows = sorted(groups.items(), key=lambda kv: kv[1][-1].get("timestamp", ""), reverse=True)
        self.stdout.write(f"{len(records)} errors, {len(rows)} kinds, most recent first:\n")
        for key, items in rows:
            paths = Counter(r.get("path") or "(no request)" for r in items).most_common(3)
            self.stdout.write(self.style.ERROR(f"{len(items):>5}  {key}"))
            self.stdout.write(f"       first {items[0].get('timestamp', '?')[:19]}   last {items[-1].get('timestamp', '?')[:19]}")
            self.stdout.write("       " + ", ".join(f"{path} ×{n}" for path, n in paths))

    def show_notfound(self, last):
        records = read_lines(NOTFOUND_FILE)
        if not records:
            self.stdout.write(f"No 404s logged in {settings.LOG_DIR / NOTFOUND_FILE}.")
            return
        counts = Counter(r.get("path", "") for r in records)
        latest = {r.get("path", ""): r.get("timestamp", "") for r in records}
        self.stdout.write(f"{len(records)} logged 404s (each path at most once a minute), top {last}:\n")
        for path, n in counts.most_common(last):
            self.stdout.write(f"{n:>5}  {path}   last {latest[path][:19]}")
