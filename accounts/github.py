"""GitHub-ідентичність користувача: числовий id і поточний логін.

The user's GitHub identity.

The numeric GitHub account id (allauth's `SocialAccount.uid`) is the identity: it never changes.
The login is only a name. It can be renamed, and the old name can then be taken by another account,
so `User.github_login` is refreshed from GitHub at every sign-in (`accounts/adapters.py`).
"""
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.db import transaction

from moderation import audit

PROVIDER = "github"


def github_id(user):
    """Числовий id GitHub-акаунта або None.

    GitHub's numeric account id from the sign-in, or None (staff accounts made with createsuperuser)."""
    if not getattr(user, "pk", None):
        return None
    uid = SocialAccount.objects.filter(user=user, provider=PROVIDER).values_list("uid", flat=True).first()
    return int(uid) if uid and str(uid).isdigit() else None


def release_login(login, keep=None):
    """Знімає логін з інших локальних акаунтів, у яких він застарів.

    Clear `login` from every other local user: their value is stale (they renamed on GitHub).

    GitHub logins are case-insensitive. Each cleared account gets an AuditLog entry; it gets its
    current login back at its own next sign-in.
    """
    if not login:
        return 0
    User = get_user_model()
    stale = User.objects.filter(github_login__iexact=login)
    if keep is not None and keep.pk:
        stale = stale.exclude(pk=keep.pk)
    count = 0
    for other in stale:
        audit.log("account.github_login.released", other, login=other.github_login)
        other.github_login = ""
        other.save(update_fields=["github_login"])
        count += 1
    return count


def refresh_login(user, extra_data):
    """Зберігає логін, який GitHub повідомив зараз.

    Store the login GitHub reports now. Called at every sign-in of an existing account."""
    login = str((extra_data or {}).get("login") or "")[:39]
    if not login or login == user.github_login:
        return False
    with transaction.atomic():
        release_login(login, keep=user)
        old = user.github_login
        user.github_login = login
        user.save(update_fields=["github_login"])
        audit.log("account.github_login.renamed", user, old=old, new=login)
    return True
