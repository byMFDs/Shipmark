from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config import views

urlpatterns = [
    path("i18n/set-language/", views.set_language, name="set_language"),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    # Uploaded files in development only. In production media is served by the web server.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
