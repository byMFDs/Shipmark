"""A page of a thread's replies as a tree, in a fixed number of queries whatever the size of the thread."""
from django.db.models import prefetch_related_objects

from moderation.visibility import banned

from . import limits
from .models import Reply
from .ranking import sort_replies


class Node:
    """One reply in the tree. `stub` is "" for a normal reply, or why only a placeholder is shown:
    "deleted" (by the author) or "removed" (by moderators, or the author is suspended or banned)."""

    def __init__(self, reply):
        self.reply = reply
        self.children = []
        author = reply.author
        if reply.is_removed or (author is not None and (author.is_suspended or reply.author_banned)):
            self.stub = "removed"
        elif reply.is_deleted:
            self.stub = "deleted"
        else:
            self.stub = ""

    @property
    def below(self):
        """How many replies hang under this one (all levels): the "Hide replies (N)" button."""
        return sum(1 + child.below for child in self.children)


def _rows(queryset):
    return queryset.select_related("author").annotate(author_banned=banned("author"))


def load_page(thread, sort, page):
    """(nodes, has_next): top-level replies of this page with their branches, sorted on every level.
    A placeholder is kept only while something readable hangs under it."""
    top = _rows(Reply.objects.filter(thread=thread, parent__isnull=True))
    order = ("-created_at", "-pk") if sort == "new" else ("-score", "created_at", "pk")
    start = (page - 1) * limits.REPLIES_PER_PAGE
    tops = list(top.order_by(*order)[start:start + limits.REPLIES_PER_PAGE + 1])
    has_next = len(tops) > limits.REPLIES_PER_PAGE
    tops = tops[:limits.REPLIES_PER_PAGE]
    below = list(_rows(Reply.objects.filter(thread=thread, root__in=[r.pk for r in tops]))) if tops else []
    rows = tops + below
    prefetch_related_objects(rows, "author__badges", "images")

    nodes = {row.pk: Node(row) for row in rows}
    for row in below:
        parent = nodes.get(row.parent_id)
        if parent is not None:
            parent.children.append(nodes[row.pk])

    def prune(node):
        node.children = [child for child in node.children if prune(child)]
        ordered = sort_replies([child.reply for child in node.children], sort)
        node.children = [nodes[reply.pk] for reply in ordered]
        return not node.stub or bool(node.children)

    return [nodes[row.pk] for row in tops if prune(nodes[row.pk])], has_next


def reply_ids(nodes):
    out = []
    for node in nodes:
        out.append(node.reply.pk)
        out.extend(reply_ids(node.children))
    return out
