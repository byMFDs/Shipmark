"""Змінна viewer у шаблонах: приглушення, непрочитані повідомлення, відкриті скарги.

`viewer` in every template (not "account": allauth uses that name): the signed-in user's mute, unread notices and moderator state.

Everything is lazy: a page that does not show it runs no query. Mutes come from the same per-request cache
as the ban check (accounts.roles.active_sanctions).
"""
from functools import cached_property

from accounts import roles

from .models import OPEN_STATES, Notice, Report


class AccountState:
    """Стан акаунта переглядача, обчислений ліниво."""
    def __init__(self, user):
        self.user = user
        self.signed_in = bool(user and user.is_authenticated)

    @cached_property
    def mute(self):
        return roles.active_mute(self.user) if self.signed_in else None

    @cached_property
    def can_write(self):
        return roles.can_write(self.user) if self.signed_in else False

    @cached_property
    def can_moderate(self):
        return roles.can_moderate(self.user) if self.signed_in else False

    @cached_property
    def notices(self):
        if not self.signed_in:
            return []
        return list(Notice.objects.filter(user=self.user, dismissed_at__isnull=True)[:5])

    @cached_property
    def open_reports(self):
        """Кількість відкритих скарг (лише для модераторів).

        Only computed for moderators (the account menu shows it)."""
        if not self.can_moderate:
            return 0
        return Report.objects.filter(status__in=OPEN_STATES).count()


def account(request):
    return {"viewer": AccountState(getattr(request, "user", None))}
