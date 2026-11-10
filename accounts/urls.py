from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("settings/", views.settings_page, name="settings"),
    path("settings/export/", views.export_data, name="export"),
    path("settings/delete/", views.delete_account_page, name="delete"),
    path("terms/accept/", views.accept_terms, name="accept_terms"),
    path("u/<str:username>/", views.profile, name="profile"),
]
