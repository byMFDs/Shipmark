"""Аватарки: єдине місце, яке зберігає й видаляє картинки профілю.

Profile pictures: the only code that stores or removes them.

Uploads and the GitHub picture both go through projects.images (Pillow: checked, centre-cropped, re-encoded to
WebP, metadata dropped, random file name). The GitHub picture is downloaded once, through verification.net.safe_fetch
(the only way the server may fetch a URL), from a GitHub host only, and then stored here: visitors are never sent
to GitHub, so their IP addresses stay with us.
"""
from urllib.parse import urlsplit

from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from projects.images import clean_avatar
from verification.net import FetchError, safe_fetch

GITHUB_AVATAR_HOSTS = ("avatars.githubusercontent.com",)  # exact hosts, https only
GITHUB_AVATAR_SIZE = 512


def github_avatar_url(user):
    """Адреса аватарки з GitHub з останнього входу або порожній рядок.

    The picture URL GitHub reported at the last sign-in (falls back to the one saved at sign-up), or ""."""
    account = SocialAccount.objects.filter(user=user, provider="github").first()
    url = ((account.extra_data or {}).get("avatar_url") if account else "") or user.avatar_url
    parts = urlsplit(url or "")
    if parts.scheme != "https" or (parts.hostname or "").lower() not in GITHUB_AVATAR_HOSTS:
        return ""
    return url


def download_github_avatar(user):
    """Завантажує аватарку GitHub через safe_fetch і повертає обрізаний WebP.

    Returns the cropped WebP ContentFile, or raises ValidationError with a message for the person."""
    url = github_avatar_url(user)
    if not url:
        raise ValidationError(_("No GitHub picture is available for this account."), code="no_avatar")
    separator = "&" if "?" in url else "?"
    try:
        result = safe_fetch(f"{url}{separator}s={GITHUB_AVATAR_SIZE}")
    except FetchError:
        raise ValidationError(_("Could not download your GitHub picture right now. Try again later."), code="fetch") from None
    if result.status_code != 200 or not result.content:
        raise ValidationError(_("Could not download your GitHub picture right now. Try again later."), code="fetch")
    return clean_avatar(ContentFile(result.content))


def drop(file_field):
    """Видаляє збережений файл після коміту транзакції.

    Delete the stored file after the transaction commits (never before: a rollback must keep it).

    Only through the field's storage (Django's storage API), so media can move to S3 by settings alone."""
    if file_field:
        storage, name = file_field.storage, file_field.name
        transaction.on_commit(lambda: storage.delete(name))


def set_avatar(user, content, source):
    drop(user.avatar)
    user.avatar.save("avatar.webp", content, save=False)
    user.avatar_source = source


def remove_avatar(user):
    drop(user.avatar)
    user.avatar = ""
    user.avatar_source = ""


def set_cover(user, content):
    drop(user.cover)
    user.cover.save("cover.webp", content, save=False)


def remove_cover(user):
    drop(user.cover)
    user.cover = ""
