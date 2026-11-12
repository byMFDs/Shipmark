from .base import *  # noqa: F403

DEBUG = env.bool("DEBUG", default=True)  # noqa: F405

# Insecure on purpose, for local work only.
SECRET_KEY = SECRET_KEY or "dev-insecure-key-do-not-use-in-production"  # noqa: F405

BAN_HASH_KEY = BAN_HASH_KEY or "dev-insecure-ban-hash-key-do-not-use-in-production"  # noqa: F405

SITE_URL = SITE_URL or "http://localhost:8000"  # noqa: F405

if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

if DEBUG:
    # Local work uses one address: 127.0.0.1 is redirected to localhost (see the middleware).
    MIDDLEWARE = ["config.middleware.LocalhostRedirectMiddleware", *MIDDLEWARE]  # noqa: F405

    # Static files are served by WhiteNoise here too (not by runserver's own handler), so they can carry
    # "Cache-Control: no-cache": the browser re-checks every file on each load and a CSS edit shows at once.
    INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]  # noqa: F405

    def _no_cache(headers, path, url):
        headers["Cache-Control"] = "no-cache"

    WHITENOISE_ADD_HEADERS_FUNCTION = _no_cache
