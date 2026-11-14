#!/usr/bin/env python
"""Командний рядок Django (типово dev-налаштування).

Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Запускає команду manage.py."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
