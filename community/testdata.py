"""Створення й безпечне очищення приватних тестових даних із точним реєстром."""
import hashlib
import io
import json
import os
import random
import sqlite3
import tarfile
import uuid
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import CommandError
from django.db import connection, models, transaction
from django.db.models import Q
from django.db.models.deletion import Collector
from django.utils import timezone
from PIL import Image, ImageDraw

from accounts.models import User
from accounts.system import system_user
from pages.stats import CACHE_KEY
from projects.images import clean_avatar

from . import services
from .models import (Board, CommunityImage, Reply, ReplyNotification, TestDataFile,
                     TestDataObject, TestDataRun, TestDataSet, Thread, Vote)
from .testdata_corpus import ABOUT, CONVERSATIONS, PROFILES
from .testdata_legacy import REPLY_VARIANTS


def require_local():
    """Дозволяє зміни лише у локальній SQLite з явними dev-налаштуваннями."""
    site = urlsplit(settings.SITE_URL)
    settings_module = settings.SETTINGS_MODULE or os.environ.get("DJANGO_SETTINGS_MODULE", "")
    if not settings.DEBUG:
        raise CommandError("Test data runs only with DEBUG on (development).")
    if (settings_module != "config.settings.dev"
            or site.scheme != "http" or site.hostname not in {"localhost", "127.0.0.1", "::1"}):
        raise CommandError("Test data refuses production settings; use config.settings.dev and a localhost SITE_URL. "
                           f"Current module={settings_module}, scheme={site.scheme}, host={site.hostname}")
    if connection.vendor != "sqlite":
        raise CommandError("Test data requires an isolated local SQLite database; remote databases are refused.")
    if not isinstance(default_storage, FileSystemStorage):
        raise CommandError("Test data requires local media storage; external integrations are refused.")


def lock_database():
    """Серіалізує зміни SQLite, включно зі звичайними записами сайту."""
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            # Rare administrative operation: prevent concurrent inserts/updates from introducing
            # an untracked dependency between validation and deletion (including SET_NULL links).
            tables = sorted({m._meta.db_table for m in apps.get_models(include_auto_created=True)
                             if m._meta.managed and not m._meta.proxy})
            cursor.execute("LOCK TABLE " + ", ".join(connection.ops.quote_name(t) for t in tables)
                           + " IN SHARE ROW EXCLUSIVE MODE")
        elif connection.vendor == "sqlite":
            cursor.execute("UPDATE django_migrations SET name = name WHERE 0")
        else:
            raise CommandError("Test data mutations support SQLite and PostgreSQL only.")


def key(obj):
    return obj._meta.label_lower, obj.pk


def register(run, obj):
    TestDataObject.objects.create(run=run, model_label=obj._meta.label_lower, object_id=obj.pk)
    return obj


def dataset_objects(dataset):
    """Завантажує лише існуючі об'єкти з технічного реєстру."""
    grouped = defaultdict(list)
    for label, pk in TestDataObject.objects.filter(run__dataset=dataset).values_list("model_label", "object_id"):
        grouped[label].append(pk)
    return [obj for label, ids in grouped.items()
            for obj in apps.get_model(label)._base_manager.filter(pk__in=ids)]


def avatar_content(index, seed):
    """Малює різні локальні ілюстрації: пейзаж, абстракцію чи рослину."""
    rng = random.Random(f"{seed}:avatar:{index}")
    colors = [tuple(rng.randrange(45, 220) for _ in range(3)) for _ in range(4)]
    image = Image.new("RGB", (256, 256), colors[0])
    draw = ImageDraw.Draw(image)
    if index % 3 == 0:
        draw.ellipse((155, 25, 220, 90), fill=colors[1])
        draw.polygon([(0, 220), (85, 85), (180, 256)], fill=colors[2])
        draw.polygon([(80, 256), (185, 120), (256, 200), (256, 256)], fill=colors[3])
    elif index % 3 == 1:
        for n in range(6):
            x, y = rng.randrange(190), rng.randrange(190)
            draw.ellipse((x, y, x + 65, y + 65), fill=colors[n % 4])
        draw.line((20, 235, 230, 20), fill=colors[2], width=15)
    else:
        draw.line((128, 235, 128, 35), fill=colors[1], width=9)
        for y in (65, 105, 145, 185):
            draw.ellipse((65, y - 25, 128, y + 12), fill=colors[2])
            draw.ellipse((128, y - 10, 195, y + 25), fill=colors[3])
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return clean_avatar(ContentFile(buffer.getvalue()))


def generate(name, mode, user_count=25, thread_count=8, seed=7, append=False):
    """Створює тільки явно запитаний обсяг без дублів і сторонніх інтеграцій."""
    require_local()
    stored = []
    try:
        with transaction.atomic():
            lock_database()
            dataset, _ = TestDataSet.objects.get_or_create(name=name, defaults={"seed": seed})
            if dataset.seed != seed:
                raise CommandError(f"Dataset seed is {dataset.seed}; use that seed or another --dataset.")
            existing = dataset_objects(dataset)
            people = sorted((o for o in existing if isinstance(o, User)), key=lambda u: u.pk)
            for person in people:
                protect_user(person)
            n_users = (user_count if append else max(0, user_count - len(people))) if mode != "activity" else 0
            n_threads = (thread_count if append else max(0, thread_count - sum(isinstance(o, Thread) for o in existing))) if mode != "users" else 0
            if dataset.profile_cursor + n_users > len(PROFILES) or dataset.thread_cursor + n_threads > len(CONVERSATIONS):
                raise CommandError(f"Local corpus exhausted (maximum {len(PROFILES)} profiles, {len(CONVERSATIONS)} conversations). No changes made.")
            if n_threads and len(people) + n_users < 9:
                raise CommandError("At least 9 registered test users are needed for the conversation corpus.")
            profiles = PROFILES[dataset.profile_cursor:dataset.profile_cursor + n_users]
            taken = list(User.objects.filter(username__in=[p[0] for p in profiles]).values_list("id", "username"))
            if taken:
                raise CommandError(f"Username collision; no accounts overwritten: {taken}")
            conversations = CONVERSATIONS[dataset.thread_cursor:dataset.thread_cursor + n_threads]
            boards = {b.slug: b for b in Board.objects.filter(is_active=True)}
            missing = {c[0] for c in conversations} - boards.keys()
            if missing:
                raise CommandError(f"Missing active boards: {sorted(missing)}. No boards are created by this tool.")
            if not n_users and not n_threads:
                result = report(dataset)
                result["created"] = {}
                result["skipped"] = {"users": user_count if mode != "activity" else 0,
                                     "threads": thread_count if mode != "users" else 0}
                return result
            run = TestDataRun.objects.create(dataset=dataset, mode=mode)
            now = timezone.now()
            rng = random.Random(f"{seed}:{dataset.profile_cursor}:{dataset.thread_cursor}")
            for offset, (username, display, city) in enumerate(profiles):
                index = dataset.profile_cursor + offset
                joined = now - timedelta(days=7, minutes=rng.randrange(0, 7 * 24 * 60))
                person = User.objects.create_user(
                    username=username, email=f"{username}@example.invalid", password=None,
                    display_name=display, location=city if index % 4 else "",
                    about=ABOUT[index % len(ABOUT)] if index % 3 else "",
                    headline=["Вчуся робити сайти", "", "Будую у вільний час", ""][index % 4],
                    preferred_language="uk", date_joined=joined,
                    terms_version_accepted=settings.TERMS_VERSION, terms_accepted_at=joined,
                )
                register(run, person)
                content = avatar_content(index, seed)
                # The site's ImageField chooses a random path; remember the file before the DB write.
                person.avatar.save("avatar.webp", content, save=False)
                stored.append(person.avatar.name)
                with person.avatar.open("rb") as handle:
                    digest = hashlib.sha256(handle.read()).hexdigest()
                TestDataFile.objects.create(run=run, name=person.avatar.name, sha256=digest)
                person.avatar_source = User.AvatarSource.UPLOAD
                person.save(update_fields=["avatar", "avatar_source"])
                people.append(person)
            active = rng.sample(people, 9) if n_threads else []
            for index, (slug, who, title, body, answers) in enumerate(conversations):
                started = max(now - timedelta(days=6 - index % 6, hours=rng.randrange(8)),
                              max(p.date_joined for p in active) + timedelta(hours=1))
                if started > now - timedelta(hours=12):
                    raise CommandError("Test participants registered too recently; retry activity after 12 hours.")
                thread = register(run, services.create_thread(active[who], boards[slug], title, body))
                Thread.objects.filter(pk=thread.pk).update(created_at=started, last_activity_at=started)
                made, last = [], started
                for reply_who, text, parent_index in answers:
                    last += timedelta(minutes=rng.randrange(15, 130))
                    parent = made[parent_index] if parent_index is not None else None
                    reply = register(run, services.create_reply(active[reply_who], thread, parent=parent, body=text))
                    Reply.objects.filter(pk=reply.pk).update(created_at=last)
                    for notice in ReplyNotification.objects.filter(reply=reply):
                        notice.created_at = last
                        notice.save(update_fields=["created_at"])
                        register(run, notice)
                    made.append(reply)
                Thread.objects.filter(pk=thread.pk).update(last_activity_at=last)
                if index % 3:  # Some threads and almost all replies have no votes.
                    voter = rng.choice([p for p in active if p.pk != thread.author_id])
                    services.set_vote(voter, thread, True)
                    vote = Vote.objects.get(user=voter, thread=thread)
                    Vote.objects.filter(pk=vote.pk).update(created_at=last + timedelta(minutes=5))
                    register(run, vote)
                if made and index % 3 == 1:
                    target = made[0]
                    voter = rng.choice([p for p in active if p.pk != target.author_id])
                    services.set_vote(voter, target, True)
                    vote = Vote.objects.get(user=voter, reply=target)
                    Vote.objects.filter(pk=vote.pk).update(created_at=last + timedelta(minutes=9))
                    register(run, vote)
            # services.notify also changes the user's cached timestamp; keep it historical and consistent.
            for person in people:
                newest = ReplyNotification.objects.filter(recipient=person).order_by("-created_at").first()
                User.objects.filter(pk=person.pk).update(community_notified_at=newest.created_at if newest else None)
            dataset.profile_cursor += n_users
            dataset.thread_cursor += n_threads
            dataset.save(update_fields=["profile_cursor", "thread_cursor"])
            transaction.on_commit(lambda: cache.delete(CACHE_KEY), robust=True)
            result = report(dataset)
            result["created"] = dict(Counter(
                run.records.values_list("model_label", flat=True)))
            result["skipped"] = {"users": max(0, user_count - n_users) if mode != "activity" else 0,
                                 "threads": max(0, thread_count - n_threads) if mode != "users" else 0}
            return result
    except Exception:
        # A rolled-back database cannot reference these newly allocated random names.
        for file_name in stored:
            if User.objects.filter(avatar=file_name).exists():
                continue
            try:
                default_storage.delete(file_name)
            except OSError:
                # Keep a concrete recovery list if the storage itself is unavailable.
                recovery = Path(settings.BASE_DIR) / ".test-data-backups"
                recovery.mkdir(mode=0o700, exist_ok=True)
                with (recovery / "orphan-files.jsonl").open("a") as handle:
                    handle.write(json.dumps({"name": file_name}) + "\n")
        raise


def protect_user(person):
    """Окремо захищає системного користувача, ролі й реальні ідентичності."""
    if (person.is_system_account or person.pk == system_user().pk or person.is_staff or person.is_superuser or person.badges.exists()
            or person.github_login or person.socialaccount_set.exists() or person.has_usable_password()
            or person.groups.exists() or person.user_permissions.exists()
            or not person.email.endswith("@example.invalid")):
        raise CommandError(f"Protected or no longer synthetic: accounts.user #{person.pk} @{person.username}")


def report(dataset):
    """Повний звіт з ID об'єктів, користувачами й запусками набору."""
    objects = dataset_objects(dataset)
    ids = defaultdict(list)
    for obj in objects:
        ids[obj._meta.label_lower].append(obj.pk)
    return {"dataset": dataset.name, "seed": dataset.seed,
            "runs": [str(pk) for pk in dataset.runs.values_list("pk", flat=True)],
            "counts": {label: len(rows) for label, rows in sorted(ids.items())},
            "ids": {label: sorted(rows) for label, rows in sorted(ids.items())},
            "users": [{"id": o.pk, "username": o.username} for o in objects if isinstance(o, User)],
            "files": list(TestDataFile.objects.filter(run__dataset=dataset).values("name", "pending_delete")),
            "corpus_remaining": {"profiles": len(PROFILES) - dataset.profile_cursor,
                                 "conversations": len(CONVERSATIONS) - dataset.thread_cursor}}


def legacy_objects():
    """Визначає старі об'єкти за точним корпусом seed_community та підписом акаунтів."""
    from .management.commands.seed_community import PEOPLE, THREADS
    people, ignored = [], []
    for person in User.objects.filter(Q(username__istartswith="demo") | Q(email__endswith="@example.invalid")):
        if TestDataObject.objects.filter(model_label="accounts.user", object_id=person.pk).exists():
            continue
        if (person.username not in PEOPLE or person.email != f"{person.username}@example.invalid"
                or person.display_name != person.username.removeprefix("demo-").title()):
            ignored.append({"id": person.pk, "username": person.username})
            continue
        protect_user(person)
        if person.avatar or person.cover:
            raise CommandError(f"Unproven legacy profile files: accounts.user #{person.pk}")
        people.append(person)
    people_ids = {p.pk for p in people}
    by_username = {p.username: p for p in people}
    threads = list(Thread.objects.filter(author_id__in=people_ids))
    replies = list(Reply.objects.filter(author_id__in=people_ids))
    proven_replies = set()
    for thread in threads:
        match = next((row for row in THREADS if row[2] == thread.title and row[3] == thread.body
                      and PEOPLE[row[1]] == thread.author.username and row[0] == thread.board.slug), None)
        if match is None or thread.pinned:
            raise CommandError(f"Unproven legacy content: community.thread #{thread.pk}")

        def prove_answers(answers, parent=None):
            """Зіставляє авторів, текст і вкладеність зі старим локальним корпусом."""
            for who, text, _images, children in answers:
                author = by_username.get(PEOPLE[who])
                signatures = {(text, ""), REPLY_VARIANTS.get((thread.title, who, text), (text, ""))}
                rows = [r for r in replies if author and r.author_id == author.pk and r.thread_id == thread.pk
                        and (r.body, r.sticker_key) in signatures and r.parent_id == (parent.pk if parent else None)]
                if len(rows) != 1:
                    raise CommandError(f"Legacy reply signature mismatch in thread #{thread.pk}: {text[:60]}")
                proven_replies.add(rows[0].pk)
                prove_answers(children, rows[0])
        prove_answers(match[5])
    if proven_replies != {r.pk for r in replies}:
        raise CommandError(f"Unproven legacy replies: {sorted({r.pk for r in replies} - proven_replies)}")
    tids, rids = {t.pk for t in threads}, {r.pk for r in replies}
    images = list(CommunityImage.objects.filter(Q(thread_id__in=tids) | Q(reply_id__in=rids), uploader_id__in=people_ids))
    votes = list(Vote.objects.filter(Q(thread_id__in=tids) | Q(reply_id__in=rids), user_id__in=people_ids))
    notices = list(ReplyNotification.objects.filter(reply_id__in=rids, recipient_id__in=people_ids))
    return people + threads + replies + images + votes + notices, ignored


# Rows that are part of one person's profile (registered by the admin's test-user form): they may go only together
# with their own registered test account.
PROFILE_ROWS = {"accounts.profilelink", "accounts.user_skills"}


def deletion_plan(objects, file_rows=None, context=None):
    """Перевіряє каскади, SET_NULL, права, файли та всі нетестові залежності."""
    allowed = {key(o) for o in objects}
    provenance = allowed if context is None else context
    grouped = defaultdict(set)
    for label, pk in allowed:
        grouped[label].add(pk)
    for obj in objects:
        if isinstance(obj, User):
            protect_user(obj)
        if obj._meta.label_lower in PROFILE_ROWS and ("accounts.user", obj.user_id) not in provenance:
            raise CommandError(f"Profile row outside the test set: {obj._meta.label_lower} #{obj.pk}")
        if isinstance(obj, (Thread, Reply)):
            if ("accounts.user", obj.author_id) not in provenance or (isinstance(obj, Thread) and obj.pinned):
                raise CommandError(f"Protected post: {obj._meta.label_lower} #{obj.pk}")
        if isinstance(obj, Reply) and ("community.thread", obj.thread_id) not in provenance:
            raise CommandError(f"Reply #{obj.pk} belongs to an untracked thread #{obj.thread_id}")
        if isinstance(obj, (Vote, CommunityImage)):
            actor_id = obj.user_id if isinstance(obj, Vote) else obj.uploader_id
            target = ("community.thread", obj.thread_id) if obj.thread_id else ("community.reply", obj.reply_id)
            if ("accounts.user", actor_id) not in provenance or target not in provenance:
                raise CommandError(f"Interaction outside the test set: {obj._meta.label_lower} #{obj.pk}")
        if isinstance(obj, ReplyNotification):
            if ("accounts.user", obj.recipient_id) not in provenance or ("community.reply", obj.reply_id) not in provenance:
                raise CommandError(f"Notification outside the test set: #{obj.pk}")
    conflicts = []
    # Include hidden reverse relations, SET_NULL and M2M through rows, not only CASCADE.
    for model in apps.get_models(include_auto_created=True):
        for field in model._meta.local_fields:
            if not isinstance(field, (models.ForeignKey, models.OneToOneField)):
                continue
            target_ids = grouped.get(field.remote_field.model._meta.label_lower)
            if not target_ids:
                continue
            for pk in model._base_manager.filter(**{f"{field.attname}__in": target_ids}).values_list("pk", flat=True):
                if (model._meta.label_lower, pk) not in allowed:
                    conflicts.append(f"{model._meta.label_lower} #{pk} via {field.name}")
    if conflicts:
        raise CommandError("Cleanup blocked by untracked dependencies; no changes made: " + "; ".join(conflicts))
    collector = Collector(using=connection.alias)
    for label, ids in grouped.items():
        collector.collect(apps.get_model(label)._base_manager.filter(pk__in=ids))
    cascaded = {key(o) for items in collector.data.values() for o in items}
    for queryset in collector.fast_deletes:
        cascaded.update(key(o) for o in queryset)
    if cascaded - allowed:
        raise CommandError(f"Unexpected cascade: {sorted(cascaded - allowed)}")
    files = {}
    for obj in objects:
        for field in obj._meta.local_fields:
            if isinstance(field, models.FileField):
                value = getattr(obj, field.name)
                if value:
                    files[value.name] = value.storage
    expected = {row.name: row.sha256 for row in file_rows or ()}
    if file_rows is not None and set(files) - expected.keys():
        raise CommandError(f"Unregistered files: {sorted(set(files) - expected.keys())}")
    for name in expected:
        files.setdefault(name, default_storage)
    for model in apps.get_models():
        for field in model._meta.local_fields:
            if isinstance(field, models.FileField):
                for pk, name in model._base_manager.filter(**{f"{field.name}__in": files}).values_list("pk", field.name):
                    if (model._meta.label_lower, pk) not in allowed:
                        raise CommandError(f"Shared file {name}: {model._meta.label_lower} #{pk}")
    for name, storage in list(files.items()):
        if not storage.exists(name):
            if any(row.name == name and row.pending_delete for row in file_rows or ()):
                del files[name]
                continue
            raise CommandError(f"Cannot back up missing file: {name}")
        if name in expected:
            with storage.open(name, "rb") as handle:
                if hashlib.sha256(handle.read()).hexdigest() != expected[name]:
                    raise CommandError(f"File changed since generation: {name}")
    return collector, files, {label: sorted(ids) for label, ids in sorted(grouped.items())}


def backup(files, destination=None):
    """Зберігає узгоджений SQLite snapshot і точні файли, перевіряє ізольоване відновлення."""
    if connection.savepoint_ids:
        raise CommandError("Cleanup must run as a standalone command, outside any enclosing transaction.")
    root = Path(destination or Path(settings.BASE_DIR) / ".test-data-backups").resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = root / f"{timezone.now():%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}"
    target.mkdir(mode=0o700)
    db_name = str(connection.settings_dict["NAME"])
    if db_name == ":memory:" or "mode=memory" in db_name:
        raise CommandError("A file-backed SQLite database is required for verified backups.")
    source = sqlite3.connect(f"file:{db_name}?mode=ro", uri=True)
    out = sqlite3.connect(target / "db.sqlite3")
    try:
        source.backup(out)
        if out.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise CommandError("Database backup failed integrity_check; cleanup cancelled.")
        restored = sqlite3.connect(":memory:")
        out.backup(restored)
        if restored.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise CommandError("Isolated database restore failed; cleanup cancelled.")
        restored.close()
    finally:
        source.close()
        out.close()
    manifest = {}
    with tarfile.open(target / "media.tar.gz", "w:gz") as archive:
        for index, (name, storage) in enumerate(sorted(files.items())):
            with storage.open(name, "rb") as handle:
                data = handle.read()
            member = tarfile.TarInfo(f"files/{index}")
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
            manifest[name] = {"member": member.name, "sha256": hashlib.sha256(data).hexdigest()}
    with tarfile.open(target / "media.tar.gz") as archive:
        for info in manifest.values():
            if hashlib.sha256(archive.extractfile(info["member"]).read()).hexdigest() != info["sha256"]:
                raise CommandError("File backup verification failed; cleanup cancelled.")
    (target / "files.json").write_text(json.dumps(manifest, indent=2))
    for path in target.iterdir():
        path.chmod(0o600)
    return str(target)


def clean(name, dry_run=False, legacy=False, backup_dir=None):
    """Очищує весь набір лише після перевірки залежностей і резервної копії."""
    require_local()
    with transaction.atomic():
        if not dry_run:
            lock_database()
        datasets = list(TestDataSet.objects.all() if name is None else TestDataSet.objects.filter(name=name)) if not legacy else []
        file_rows = list(TestDataFile.objects.filter(run__dataset__in=datasets)) if not legacy else None
        objects, ignored = legacy_objects() if legacy else ([obj for dataset in datasets for obj in dataset_objects(dataset)], [])
        # Return exact candidate IDs even when safety validation blocks cleanup.
        candidates = defaultdict(list)
        for obj in objects:
            candidates[obj._meta.label_lower].append(obj.pk)
        result = {"ids": {k: sorted(v) for k, v in candidates.items()},
                  "counts": {k: len(v) for k, v in candidates.items()}, "ignored": ignored,
                  "dry_run": dry_run, "blocked": None}
        try:
            collector, files, _ = deletion_plan(objects, file_rows)
        except CommandError as error:
            result["blocked"] = str(error)
            return result
        result["files"] = sorted(files)
        if dry_run or not objects and not files and not file_rows:
            return result
        result["backup"] = backup(files, backup_dir)
        # Existing post_delete signals remove files on_commit. Clear file fields on the instances collected
        # for deletion so we can use our durable file queue and handle failed storage deletes explicitly.
        for items in collector.data.values():
            for obj in items:
                for field in obj._meta.local_fields:
                    if isinstance(field, models.FileField):
                        setattr(obj, field.name, "")
        collector.delete()
        if datasets:
            TestDataObject.objects.filter(run__dataset__in=datasets).delete()
            TestDataFile.objects.filter(run__dataset__in=datasets).update(pending_delete=True)
            TestDataSet.objects.filter(pk__in=[d.pk for d in datasets]).update(profile_cursor=0, thread_cursor=0)
            TestDataFile.objects.filter(run__dataset__in=datasets).exclude(name__in=files).delete()
        transaction.on_commit(lambda: cache.delete(CACHE_KEY), robust=True)
        result["file_delete_failures"] = []

        def finish_files():
            """Видаляє файли тільки після зовнішнього commit; помилки лишають чергу для повтору."""
            for file_name, storage in files.items():
                try:
                    storage.delete(file_name)
                except OSError as error:
                    result["file_delete_failures"].append({"name": file_name, "error": str(error)})
                else:
                    if datasets:
                        TestDataFile.objects.filter(run__dataset__in=datasets, name=file_name).delete()

        transaction.on_commit(finish_files)
    return result
