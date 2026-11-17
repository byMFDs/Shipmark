"""Команда керування приватним тестовим набором спільноти."""
import json

from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_slug
from django.core.exceptions import ValidationError

from community import testdata
from community.models import TestDataSet


class Command(BaseCommand):
    """Створює, показує та безпечно видаляє зареєстровані тестові дані."""
    help = "Manage private synthetic community data (local development SQLite only)."

    def add_arguments(self, parser):
        """Явні режими замість неявного наповнення під час запуску сайту."""
        parser.add_argument("mode", choices=["users", "seed", "activity", "list", "clean", "legacy-clean"])
        parser.add_argument("--dataset", default="local-preview")
        parser.add_argument("--users", type=int, default=25)
        parser.add_argument("--threads", type=int, default=8)
        parser.add_argument("--seed", type=int, default=7)
        parser.add_argument("--append", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--all", action="store_true", dest="all_datasets", help="Clean every registered test dataset.")
        parser.add_argument("--backup-dir", help="Private directory for mandatory cleanup backups.")

    def handle(self, *args, **options):
        """Виконує рівно один режим, виводить машинозчитуваний звіт з ID."""
        mode, name = options["mode"], options["dataset"]
        try:
            validate_slug(name)
        except ValidationError:
            raise CommandError("--dataset must be a nonempty slug.") from None
        if len(name) > 60 or options["users"] < 0 or options["threads"] < 0:
            raise CommandError("Use nonnegative counts and a dataset name of at most 60 characters.")
        if options["dry_run"] and mode not in {"clean", "legacy-clean"}:
            raise CommandError("--dry-run applies to clean and legacy-clean only.")
        if options["append"] and mode not in {"users", "seed", "activity"}:
            raise CommandError("--append applies to creation modes only.")
        if options["all_datasets"] and mode != "clean":
            raise CommandError("--all applies to clean only.")
        if mode == "list":
            datasets = TestDataSet.objects.all().order_by("name")
            result = [testdata.report(dataset) for dataset in datasets]
        elif mode in {"clean", "legacy-clean"}:
            result = testdata.clean(None if options["all_datasets"] else name,
                                    dry_run=options["dry_run"], legacy=mode == "legacy-clean",
                                    backup_dir=options["backup_dir"])
        else:
            result = testdata.generate(name, mode, user_count=options["users"], thread_count=options["threads"],
                                       seed=options["seed"], append=options["append"])
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
        if isinstance(result, dict) and result.get("blocked"):
            raise CommandError(result["blocked"])
        if isinstance(result, dict) and result.get("file_delete_failures"):
            raise CommandError("Database cleaned; some files need retry. See file_delete_failures and backup.")
