"""django-allauth hooks: fill our User from GitHub data and keep sign-in GitHub-only."""
import re

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.db import transaction

from . import github
from .usernames import generate_username


def _one_line(text, limit):
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False  # no email/password signup, only GitHub (see SocialAccountAdapter)

    def save_user(self, request, user, form, commit=True):
        # allauth would overwrite the email with an empty value (our form has no email field).
        email = user.email
        user = super().save_user(request, user, form, commit=False)
        if not user.email:
            user.email = email
        if commit:
            user.save()
        return user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True  # GitHub sign-up is open

    def pre_social_login(self, request, sociallogin):
        """Every GitHub sign-in. allauth has already refreshed `extra_data` from GET /user by now."""
        if sociallogin.is_existing:
            github.refresh_login(sociallogin.user, sociallogin.account.extra_data)

    def save_user(self, request, sociallogin, form=None):
        """First sign-in: an old local account may still hold this login (its owner renamed on GitHub)."""
        with transaction.atomic():
            github.release_login(sociallogin.user.github_login, keep=sociallogin.user)
            return super().save_user(request, sociallogin, form)

    def populate_user(self, request, sociallogin, data):
        """Runs on first login, before the confirmation step. Everything here can be edited later."""
        user = super().populate_user(request, sociallogin, data)
        extra = sociallogin.account.extra_data
        login = extra.get("login") or data.get("username") or ""
        user.github_login = login
        user.username = generate_username(login)  # suggestion; the user confirms it on the next page
        user.display_name = _one_line(data.get("name"), 80) or login
        user.bio = _one_line(extra.get("bio"), 280)
        user.avatar_url = extra.get("avatar_url") or ""
        # Not used: allauth's first/last name. We keep one display name.
        user.first_name = user.last_name = ""
        return user
