"""The system account "shipmark": the public author of official news.

Created by migration accounts/0005 with an unusable password and is_active=False, so nobody can sign in
as it (no password, no GitHub account linked, and Django refuses inactive users). It carries the
official badge.
"""
from django.contrib.auth import get_user_model

SYSTEM_USERNAME = "shipmark"


def system_user():
    return get_user_model().objects.get(username=SYSTEM_USERNAME)


def is_system(user):
    return getattr(user, "username", None) == SYSTEM_USERNAME
