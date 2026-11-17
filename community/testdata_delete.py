"""Selective admin cleanup: exact provenance, closed dependency graph, atomic deletion."""
from collections import Counter

from django.apps import apps
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.core.management.base import CommandError
from django.db import models, transaction

from accounts.models import User
from moderation import audit
from pages.stats import CACHE_KEY
from . import testdata, testdata_tools as tools
from .management.commands.community_daily import _replies, _votes
from .models import Reply, ReplyNotification, TestDataFile, TestDataObject, TestDataSet, Thread, Vote


def _plan(selection):
    known = set(TestDataObject.objects.values_list("model_label", "object_id"))
    selected = known.copy() if selection is None else set(selection)
    if selected - known:
        raise CommandError("Вибір містить незареєстровані об’єкти; видалення заборонено.")
    objects = {}
    frontier = selected
    while frontier:
        for label, pk in frontier:
            obj = apps.get_model(label)._base_manager.filter(pk=pk).first()
            if obj is not None:
                objects[(label, pk)] = obj
        found = set()
        for model in apps.get_models(include_auto_created=True):
            for field in model._meta.local_fields:
                if not isinstance(field, (models.ForeignKey, models.OneToOneField)):
                    continue
                label = field.remote_field.model._meta.label_lower
                ids = [pk for target, pk in frontier if target == label]
                if not ids:
                    continue
                for pk in model._base_manager.filter(**{f"{field.attname}__in": ids}).values_list("pk", flat=True):
                    item = (model._meta.label_lower, pk)
                    if item not in known:
                        raise CommandError(f"Нетестова залежність: {item[0]} #{pk} через {field.name}. Нічого не видалено.")
                    found.add(item)
        frontier = found - selected
        selected |= found
    # Context permits keeping authors and parent threads when deleting just one post.
    # Validate every referenced author independently: registry membership alone is insufficient.
    for obj in objects.values():
        for field in obj._meta.local_fields:
            if isinstance(field, models.ForeignKey) and field.remote_field.model is User:
                pk = getattr(obj, field.attname)
                if pk:
                    tools.require_test_user(User(pk=pk))
    names = {getattr(obj, f.name).name for obj in objects.values()
             for f in obj._meta.local_fields if isinstance(f, models.FileField) and getattr(obj, f.name)}
    files = TestDataFile.objects.filter(name__in=names)
    if selection is None:
        files = TestDataFile.objects.all()  # also retry pending files from an earlier committed delete
    file_rows = list(files)
    collector, storage_files, ids = testdata.deletion_plan(list(objects.values()), file_rows, context=known)
    return objects, collector, storage_files, file_rows, ids


def remove(actor, selection=None, *, execute=False):
    """None selects all registered test data; otherwise exact (concrete label, pk) pairs."""
    if not tools.can_use(actor):
        raise PermissionDenied
    with transaction.atomic():
        testdata.lock_database()
        # Permissions may have changed since the request was authenticated.
        actor = User.objects.get(pk=actor.pk)
        if not tools.can_use(actor):
            raise PermissionDenied
        objects, collector, files, file_rows, ids = _plan(selection)
        result = {"objects": [{"model": label, "id": pk, "text": str(obj)}
                              for (label, pk), obj in sorted(objects.items())],
                  "counts": dict(Counter(label for label, pk in objects)),
                  "files": list(files), "file_failures": []}
        if not execute:
            return result
        thread_ids = {obj.thread_id for obj in objects.values() if isinstance(obj, (Reply, Vote)) and obj.thread_id}
        reply_ids = {obj.reply_id for obj in objects.values() if isinstance(obj, Vote) and obj.reply_id}
        recipients = {obj.recipient_id for obj in objects.values() if isinstance(obj, ReplyNotification)}
        # Disable existing file signals; deletion is handled by the durable queue after commit.
        for rows in collector.data.values():
            for obj in rows:
                for field in obj._meta.local_fields:
                    if isinstance(field, models.FileField):
                        setattr(obj, field.name, "")
        collector.delete()
        for label, pks in ids.items():
            TestDataObject.objects.filter(model_label=label, object_id__in=pks).delete()
        if selection is None:
            TestDataObject.objects.all().delete()  # includes stale registry entries of already absent rows
            TestDataSet.objects.update(profile_cursor=0, thread_cursor=0)
        file_ids = [row.pk for row in file_rows]
        TestDataFile.objects.filter(pk__in=file_ids).update(pending_delete=True)
        Thread.objects.filter(pk__in=thread_ids).update(score=_votes("thread"), reply_count=_replies())
        Reply.objects.filter(pk__in=reply_ids).update(score=_votes("reply"))
        for thread in Thread.objects.filter(pk__in=thread_ids):
            newest = thread.replies.filter(status=Reply.Status.PUBLISHED, deleted_at__isnull=True).order_by("-created_at").first()
            Thread.objects.filter(pk=thread.pk).update(last_activity_at=newest.created_at if newest else thread.created_at)
        for pk in recipients:
            newest = ReplyNotification.objects.filter(recipient_id=pk, read_at__isnull=True).order_by("-created_at").first()
            User.objects.filter(pk=pk).update(community_notified_at=newest.created_at if newest else None)
        audit.log("testdata.deleted", actor, actor=actor, counts=result["counts"], ids=ids)
        transaction.on_commit(lambda: cache.delete(CACHE_KEY), robust=True)

        def finish():
            for row in file_rows:
                storage = files.get(row.name, default_storage)
                try:
                    storage.delete(row.name)
                except Exception:
                    result["file_failures"].append(row.name)
                else:
                    TestDataFile.objects.filter(pk=row.pk).delete()
        transaction.on_commit(finish)
        return result
