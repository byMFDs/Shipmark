"""Ручні тестові акаунти й дописи з адмінки: доступ, реєстр, серверні перевірки.

Hand-made test data from the admin section "Test data" (community/admin_testdata.py).

- Who: active superusers only, and only where the test-data generator itself may run (local development SQLite,
  `testdata.require_local`), or explicitly enabled with TEST_DATA_ADMIN_ENABLED.
- What counts as a test account: a user row in the test-data registry (TestDataObject, exact id) that still
  passes `testdata.protect_user` (no staff, superuser, badge, group, permission, GitHub identity, usable
  password, and an @example.invalid address). Names never decide it. Real people and the system account are
  never listed, never chosen as authors and never saved through these tools: every save checks again on the
  server, inside the transaction, whatever the form or the URL said.
- Everything made here is registered at once, so `community_testdata clean` (and `list`) see it: new accounts and
  posts in the dataset ADMIN_DATASET; profile rows (links, skills) and picture files in the run of the person
  they belong to, with their SHA256 like the generator's files.
- Posts go through community.services (the same code as the site: counters, notifications, image pipeline).
"""
import hashlib

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts.models import ProfileLink, User
from accounts.roles import can_write

from . import services, testdata
from .models import (CommunityImage, Reply, ReplyNotification, TestDataFile, TestDataObject, TestDataRun,
                     TestDataSet, Thread)
from .permissions import can_reply

ADMIN_DATASET = "admin-manual"
ADMIN_MODE = "admin"
TEST_EMAIL_DOMAIN = "@example.invalid"
USER_LABEL = User._meta.label_lower
SKILL_ROWS = User.skills.through


def tools_enabled():
    """Explicit admin opt-in, or the existing local development guard. CLI remains local-only."""
    if getattr(settings, "TEST_DATA_ADMIN_ENABLED", False):
        return True
    try:
        testdata.require_local()
    except CommandError:
        return False
    return True


def can_use(user):
    """Доступ до розділу: лише активний суперкористувач і лише з увімкненими інструментами."""
    return bool(getattr(user, "is_authenticated", False) and user.is_active and user.is_superuser and tools_enabled())


def sidebar_permission(request):
    return can_use(request.user)


# ---------- Registry ----------

def label(model_or_obj):
    """Мітка конкретної моделі (не проксі): так її читає testdata.dataset_objects."""
    model = model_or_obj if isinstance(model_or_obj, type) else type(model_or_obj)
    return model._meta.concrete_model._meta.label_lower


def registered_ids(model):
    return TestDataObject.objects.filter(model_label=label(model)).values("object_id")


def admin_run():
    """Запуск, у якому реєструється все створене в адмінці."""
    dataset, _created = TestDataSet.objects.get_or_create(name=ADMIN_DATASET, defaults={"seed": 0})
    run = dataset.runs.filter(mode=ADMIN_MODE).order_by("created_at").first()
    return run or TestDataRun.objects.create(dataset=dataset, mode=ADMIN_MODE)


def run_of(user):
    """Запуск, у якому зареєстрована тестова людина (її профіль і файли йдуть туди ж)."""
    row = TestDataObject.objects.filter(model_label=USER_LABEL, object_id=user.pk).select_related("run").first()
    return row.run if row else None


def register(obj, run):
    TestDataObject.objects.get_or_create(model_label=label(obj), object_id=obj.pk, defaults={"run": run})
    return obj


def register_file(name, run, storage=default_storage):
    """Реєструє файл із контрольною сумою, як це робить генератор."""
    with storage.open(name, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    TestDataFile.objects.update_or_create(name=name, defaults={"run": run, "sha256": digest, "pending_delete": False})


def forget_file(name):
    if name:
        TestDataFile.objects.filter(name=name).delete()


# ---------- Who is a test account ----------

def test_users():
    """Лише зареєстровані тестові акаунти, які досі синтетичні.

    Registered accounts that still look synthetic (the same marks protect_user checks). Real people, staff,
    badge holders and the system account can never be in this list, whatever the registry says."""
    return (
        User.objects.filter(pk__in=registered_ids(User), is_staff=False, is_superuser=False, is_system_account=False,
                            github_login="", email__endswith=TEST_EMAIL_DOMAIN, password__startswith="!")
        .exclude(badges__isnull=False).exclude(groups__isnull=False).exclude(user_permissions__isnull=False)
        .exclude(socialaccount__isnull=False)
    )


def require_test_user(user):
    """Серверна перевірка автора чи профілю; помилка — ValidationError.

    Raises ValidationError unless `user` is a registered test account that is still synthetic. Reads the row
    from the database again, so a value changed in the form or the URL cannot get through."""
    pk = getattr(user, "pk", None)
    fresh = User.objects.filter(pk=pk).first() if pk else None
    if fresh is None or run_of(fresh) is None:
        raise ValidationError(_("Only registered test accounts can be used here."), code="not_test")
    try:
        testdata.protect_user(fresh)
    except CommandError:
        raise ValidationError(_("This account is protected and cannot be used as a test account."),
                              code="protected") from None
    return fresh


def test_threads():
    return Thread.objects.filter(pk__in=registered_ids(Thread))


def test_replies():
    return Reply.objects.filter(pk__in=registered_ids(Reply))


def require_test_post(post):
    """Тема чи відповідь має бути зареєстрованою й від тестового автора."""
    model = Thread if isinstance(post, Thread) else Reply
    if not post.pk or not TestDataObject.objects.filter(model_label=label(model), object_id=post.pk).exists():
        raise ValidationError(_("Only test posts can be changed here."), code="not_test")
    require_test_user(post.author)
    if isinstance(post, Thread) and post.pinned:
        raise ValidationError(_("Pinned threads are protected."))


# ---------- Accounts ----------

def prepare_new_user(user):
    """Поля нового тестового акаунта, яких немає у формі.

    No password (nobody can sign in), a reserved example address, no roles. Terms are recorded as accepted
    so the account behaves like a normal signed-up one on the site."""
    user.email = f"{user.username}{TEST_EMAIL_DOMAIN}"
    user.set_unusable_password()
    user.is_active, user.is_staff, user.is_superuser = True, False, False
    user.terms_version_accepted = settings.TERMS_VERSION
    user.terms_accepted_at = timezone.now()


def sync_profile(user, old_files=()):
    """Після збереження профілю: реєструє посилання, навички й нові файли, забуває замінені.

    Links and skills are replaced as a whole by the settings form, so their registry rows are rebuilt; picture
    files keep a checksum, and the replaced file's row goes (the file itself is deleted after commit)."""
    run = run_of(user)
    for model, ids in ((ProfileLink, ProfileLink.objects.filter(user=user).values_list("pk", flat=True)),
                       (SKILL_ROWS, SKILL_ROWS.objects.filter(user=user).values_list("pk", flat=True))):
        known = TestDataObject.objects.filter(model_label=label(model))
        alive = set(model.objects.filter(pk__in=known.values("object_id")).values_list("pk", flat=True))
        known.exclude(object_id__in=alive).delete()  # rows of this kind that no longer exist
        for pk in ids:
            TestDataObject.objects.get_or_create(model_label=label(model), object_id=pk, defaults={"run": run})
    current = {field.name for field in (user.avatar, user.cover) if field}
    for name in set(old_files) - current:
        forget_file(name)
    for name in current:
        register_file(name, run)


# ---------- Posts ----------

def _register_images(post, run):
    """Реєструє картинки допису та обидва їхні файли."""
    field = "thread" if isinstance(post, Thread) else "reply"
    for image in CommunityImage.objects.filter(**{field: post}):
        register(image, run)
        register_file(image.image.name, run)
        register_file(image.thumb.name, run)


def create_thread(author, board, title, body, images=()):
    """Тема від тестового автора через звичайний сервіс сайту."""
    with transaction.atomic():
        testdata.lock_database()
        author = require_test_user(author)
        if not can_write(author):
            raise ValidationError(_("This test account cannot write (suspended, muted or banned)."))
        if not board.is_active:
            raise ValidationError(_("Choose a board."))
        run = admin_run()
        thread = register(services.create_thread(author, board, title, body, images), run)
        _register_images(thread, run)
    return thread


def create_reply(author, thread, parent=None, body="", images=()):
    """Відповідь від тестового автора; лише в тестовій темі й під тестовою відповіддю.

    Through community.services.create_reply: depth limit, reply_count, last activity and the notification are the
    site's own. The thread and the parent must be test posts, so a test reply never lands under a real
    person's words and the cleanup never meets one."""
    with transaction.atomic():
        testdata.lock_database()
        author = require_test_user(author)
        thread = Thread.objects.select_related("board", "author").get(pk=thread.pk)
        require_test_post(thread)
        if not can_write(author):
            raise ValidationError(_("This test account cannot write (suspended, muted or banned)."))
        if thread.is_deleted or not thread.board.is_active or not can_reply(author, thread):
            raise ValidationError(_("This thread does not accept replies."))
        if parent is not None:
            parent = Reply.objects.select_related("author", "parent", "root").get(pk=parent.pk)
            require_test_post(parent)
            if parent.thread_id != thread.pk or not parent.is_alive:
                raise ValidationError(_("The reply you are answering is gone."))
        run = admin_run()
        reply = register(services.create_reply(author, thread, parent, body, images=images), run)
        _register_images(reply, run)
        for notice in ReplyNotification.objects.filter(reply=reply):
            register(notice, run)
    return reply


def edit_thread(thread, title, body):
    """Змінює текст (і заголовок у дозволений час) лише тестової теми."""
    with transaction.atomic():
        testdata.lock_database()
        thread = Thread.objects.select_related("author").get(pk=thread.pk)
        require_test_post(thread)
        return services.edit_thread(thread, body, title)


def edit_reply(reply, body):
    """Змінює текст лише тестової відповіді."""
    with transaction.atomic():
        testdata.lock_database()
        reply = Reply.objects.select_related("author").get(pk=reply.pk)
        require_test_post(reply)
        return services.edit_reply(reply, body)
