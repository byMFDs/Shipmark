from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config import views

urlpatterns = [
    path("i18n/set-language/", views.set_language, name="set_language"),
    path("", include("accounts.auth_urls")),
    # Only GitHub's OAuth routes (not allauth.urls: that would add email/password pages).
    # Callback: /accounts/github/login/callback/
    path("accounts/", include("allauth.socialaccount.providers.github.urls")),
    path("", include("accounts.urls")),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    # Uploaded files in development only. In production media is served by the web server.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
