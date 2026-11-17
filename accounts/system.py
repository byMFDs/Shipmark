"""Системний акаунт «shipmark», автор офіційних новин.

The system account "shipmark": the public author of official news.

Created by migration accounts/0005 with an unusable password and is_active=False, so nobody can sign in
as it (no password, no GitHub account linked, and Django refuses inactive users). It carries the
official badge.

The account is found by its stable mark `User.is_system_account` (set by migration 0008), never by the
username: SYSTEM_USERNAME is only the name migration 0005 gave it.
"""
from django.contrib.auth import get_user_model

SYSTEM_USERNAME = "shipmark"


def system_user():
    return get_user_model().objects.get(is_system_account=True)


def is_system(user):
    return bool(getattr(user, "is_system_account", False))
