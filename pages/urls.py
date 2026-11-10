from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("about/", views.content_page, {"slug": "about"}, name="about"),
    path("styleguide/", views.styleguide, name="styleguide"),  # 404 unless DEBUG
]
