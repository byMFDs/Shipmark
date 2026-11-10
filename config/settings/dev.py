from .base import *  # noqa: F403

DEBUG = env.bool("DEBUG", default=True)  # noqa: F405

# Insecure on purpose, for local work only.
SECRET_KEY = SECRET_KEY or "dev-insecure-key-do-not-use-in-production"  # noqa: F405

if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
