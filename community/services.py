"""What changes community data: post, edit, delete, vote. Views, commands and tests call these.

Counters (`score`, `reply_count`) move with F() inside the same transaction as the row they count.
"""
import hashlib

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from . import limits, notifications, stickers
from .images import delete_images, store_images
from .models import Reply, Thread, Vote


# ---------- Duplicates ----------

def _normalized(text):
    return " ".join((text or "").lower().split())


def claim_text(user, kind, text, window, scope=""):
    """True when this text is new for the user; False when they posted the same within `window` seconds.
    cache.add is atomic, so a double submit cannot pass twice."""
    digest = hashlib.sha256(f"{scope}\n{_normalized(text)}".encode()).hexdigest()
    return cache.add(f"community:dup:{kind}:{user.pk}:{digest}", 1, timeout=window)


def claim_thread_text(user, title, body):
    return claim_text(user, "thread", f"{title}\n{body}", limits.DUPLICATE_THREAD_WINDOW)


def claim_reply_text(user, thread, parent, body):
    """Empty text (a sticker or an image alone) is never a duplicate. A short text only under the same parent."""
    text = _normalized(body)
    if not text:
        return True
    scope = f"{thread.pk}:{getattr(parent, 'pk', '')}" if len(text) < limits.DUPLICATE_SHORT else ""
    return claim_text(user, "reply", text, limits.DUPLICATE_REPLY_WINDOW, scope=scope)


# ---------- Threads ----------

def create_thread(author, board, title, body, images=()):
    with transaction.atomic():
        thread = Thread.objects.create(board=board, author=author, title=title, body=body)
        store_images(images, author, thread=thread)
    return thread


def _edited_stamp(created_at, now):
    """None inside the silent window, else the time to show next to "edited"."""
    return now if now - created_at > limits.EDIT_SILENT_WINDOW else None


def title_editable(thread, now=None):
    return (now or timezone.now()) - thread.created_at <= limits.EDIT_SILENT_WINDOW


def edit_thread(thread, body, title=None):
    now = timezone.now()
    fields = ["body"]
    thread.body = body
    if title is not None and title_editable(thread, now) and title != thread.title:
        thread.title = title
        thread.slug = ""  # Thread.save makes a new one; the old address redirects (the id finds the thread)
        fields += ["title", "slug"]
    stamp = _edited_stamp(thread.created_at, now)
    if stamp:
        thread.edited_at = stamp
        fields.append("edited_at")
    thread.save(update_fields=fields)
    return thread


def delete_thread(thread):
    """By the author: the text and the images are gone for good. The row stays ("[deleted]") while it has
    replies; without replies nobody can open it any more (ThreadQuerySet.public)."""
    if thread.is_deleted:
        return False
    with transaction.atomic():
        delete_images(thread=thread)
        thread.body = ""
        thread.deleted_at = timezone.now()
        thread.save(update_fields=["body", "deleted_at"])
    return True


# ---------- Replies ----------

def place_reply(parent):
    """(parent, root, depth) for an answer to `parent` (None = top level). Depth never passes MAX_DEPTH:
    an answer to a reply on the last level becomes its sibling."""
    if parent is None:
        return None, None, 1
    if parent.depth >= limits.MAX_DEPTH:
        parent = parent.parent
    return parent, (parent.root or parent), parent.depth + 1


def create_reply(author, thread, parent=None, body="", sticker_key="", images=()):
    """`parent` is the reply being answered (None: the thread). Its author is notified, also when the depth
    limit attaches the new reply one level higher."""
    if sticker_key and not stickers.is_sticker(sticker_key):
        raise ValueError("unknown sticker")  # forms check this first; never store a key outside the manifest
    recipient, kind = notifications.recipient_for(thread, parent)
    parent, root, depth = place_reply(parent)
    now = timezone.now()
    with transaction.atomic():
        reply = Reply.objects.create(
            thread=thread, parent=parent, root=root, depth=depth, author=author, body=body, sticker_key=sticker_key,
            created_at=now,
        )
        store_images(images, author, reply=reply)
        Thread.objects.filter(pk=thread.pk).update(reply_count=F("reply_count") + 1, last_activity_at=now)
        notifications.notify(reply, recipient, kind)
    return reply


def edit_reply(reply, body):
    fields = ["body"]
    reply.body = body
    stamp = _edited_stamp(reply.created_at, timezone.now())
    if stamp:
        reply.edited_at = stamp
        fields.append("edited_at")
    reply.save(update_fields=fields)
    return reply


def uncount_reply(reply):
    Thread.objects.filter(pk=reply.thread_id, reply_count__gt=0).update(reply_count=F("reply_count") - 1)


def delete_reply(reply):
    """By the author: text, sticker and images are gone; the row stays so the answers under it keep their place."""
    if reply.is_deleted:
        return False
    with transaction.atomic():
        counted = reply.is_alive
        delete_images(reply=reply)
        reply.body = ""
        reply.sticker_key = ""
        reply.deleted_at = timezone.now()
        reply.save(update_fields=["body", "sticker_key", "deleted_at"])
        if counted:
            uncount_reply(reply)
    return True


# ---------- Votes ----------

def set_vote(user, target, on):
    """Upvote (`on=True`) or take it back. Idempotent. Returns the new score."""
    model = type(target)
    field = "thread" if model is Thread else "reply"
    with transaction.atomic():
        if on:
            try:
                with transaction.atomic():
                    Vote.objects.create(user=user, **{field: target})
            except IntegrityError:
                changed = 0
            else:
                changed = 1
        else:
            deleted, _rows = Vote.objects.filter(user=user, **{field: target}).delete()
            changed = -1 if deleted else 0
        if changed:
            model.objects.filter(pk=target.pk).update(score=F("score") + changed)
    return model.objects.values_list("score", flat=True).get(pk=target.pk)
