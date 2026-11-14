"""Хуки django-allauth: заповнюють нашого User даними з GitHub і лишають вхід лише через GitHub.

django-allauth hooks: fill our User from GitHub data and keep sign-in GitHub-only."""
import re

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.db import transaction
from django.utils import translation
from django.utils.translation import gettext as _

from . import github
from .roles import active_ban
from .usernames import generate_username, looks_official


def _one_line(text, limit):
    return re.sub(r"\s+", " ", text or "").strip()[:limit]


class AccountAdapter(DefaultAccountAdapter):
    """Адаптер акаунтів allauth: збереження користувача, мова після входу, наші тексти повідомлень."""
    def is_open_for_signup(self, request):
        return False  # no email/password signup, only GitHub (see SocialAccountAdapter)

    def save_user(self, request, user, form, commit=True):
        """Зберігає нового користувача, не втрачаючи email, який дав GitHub."""
        # allauth would overwrite the email with an empty value (our form has no email field).
        email = user.email
        user = super().save_user(request, user, form, commit=False)
        if not user.email:
            user.email = email
        if commit:
            user.save()
        return user

    def post_login(self, request, user, **kwargs):
        """Перемикає запит на збережену мову людини до повідомлення «ви увійшли».

        Switch this request to the person's saved language before the "signed in" message is written.

        The GitHub callback starts anonymous, so it runs in the cookie or browser language, while the next page
        uses the saved preference (CLAUDE.md section 8). Without this the toast and the page could differ.
        UserLocaleMiddleware also stores the language in the language cookie, so it stays after signing out.
        """
        saved = user.preferred_language
        if saved in dict(settings.LANGUAGES):
            translation.activate(saved)
            request.LANGUAGE_CODE = saved
            request.saved_language = saved
        return super().post_login(request, user, **kwargs)

    def add_message(self, request, level, message_template=None, message_context=None, extra_tags="", message=None):
        """Підміняє повідомлення allauth про вхід і вихід нашими перекладеними текстами.

        Our own short texts for sign-in and sign-out (in our translations), written in the active language."""
        if message_template == "account/messages/logged_in.txt":
            user = (message_context or {}).get("user") or request.user
            message = _("Signed in as %(name)s.") % {"name": user.display_name or user.username}
        elif message_template == "account/messages/logged_out.txt":
            message = _("You are signed out.")
        return super().add_message(request, level, message_template, message_context, extra_tags, message)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Адаптер входу через GitHub: бани, перейменовані логіни, перше заповнення профілю."""
    def is_open_for_signup(self, request, sociallogin):
        return True  # GitHub sign-up is open

    def pre_social_login(self, request, sociallogin):
        """Кожен вхід через GitHub: перевірка бану й оновлення збереженого логіна.

        Every GitHub sign-in. allauth has already refreshed `extra_data` from GET /user by now.

        A banned person sees the ban page instead of being signed in: an existing account by its active ban,
        a new signup by the salted hash of the GitHub id (moderation/bans.py), so deleting the account and
        signing up again does not end a ban.
        """
        from moderation import bans
        from moderation.pages import ban_response

        if sociallogin.is_existing:
            ban = active_ban(sociallogin.user)
            if ban is not None:
                raise ImmediateHttpResponse(ban_response(request, ban.reason, ban.expires_at))
            github.refresh_login(sociallogin.user, sociallogin.account.extra_data)
            return
        identity = bans.find(sociallogin.account.uid)
        if identity is not None:
            raise ImmediateHttpResponse(ban_response(request, identity.reason, identity.expires_at))

    def save_user(self, request, sociallogin, form=None):
        """Перший вхід: звільняє логін у старого локального акаунта, якщо власник перейменувався на GitHub.

        First sign-in: an old local account may still hold this login (its owner renamed on GitHub)."""
        with transaction.atomic():
            github.release_login(sociallogin.user.github_login, keep=sociallogin.user)
            return super().save_user(request, sociallogin, form)

    def populate_user(self, request, sociallogin, data):
        """Заповнює нового користувача з даних GitHub (ім'я, логін) до кроку підтвердження.

        Runs on first login, before the confirmation step. Everything here can be edited later."""
        user = super().populate_user(request, sociallogin, data)
        extra = sociallogin.account.extra_data
        login = extra.get("login") or data.get("username") or ""
        user.github_login = login
        user.username = generate_username(login)  # suggestion; the user confirms it on the next page
        user.display_name = _one_line(data.get("name"), 80) or login
        if looks_official(user.display_name):  # a GitHub name like "Shipmark Team" is not carried over
            user.display_name = ""
        user.about = _one_line(extra.get("bio"), 1000)
        user.avatar_url = extra.get("avatar_url") or ""
        # Not used: allauth's first/last name. We keep one display name.
        user.first_name = user.last_name = ""
        return user
