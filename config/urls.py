from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path

from config import errors, views

# Error pages (config/errors.py). Django uses these instead of its own when DEBUG is off.
handler400 = "config.errors.bad_request"
handler403 = "config.errors.permission_denied"
handler404 = "config.errors.page_not_found"
handler500 = "config.errors.server_error"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("i18n/set-language/", views.set_language, name="set_language"),
    path("favicon.ico", views.favicon, name="favicon"),
    path("", include("accounts.auth_urls")),
    # Only GitHub's OAuth routes (not allauth.urls: that would add email/password pages).
    # Callback: /accounts/github/login/callback/
    path("accounts/", include("allauth.socialaccount.providers.github.urls")),
    path("", include("accounts.urls")),
    path("", include("projects.urls")),
    path("", include("social.urls")),
    path("", include("moderation.urls")),
    path("", include("pages.urls")),
    # Previews of every error page, linked from /styleguide/. 404 unless DEBUG.
    path("_dev/errors/<str:code>/", errors.preview, name="error_preview"),
]

if settings.DEBUG:
    # Uploaded files in development only. In production media is served by the web server.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
