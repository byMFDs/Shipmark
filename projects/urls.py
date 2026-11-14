"""Маршрути проєктів і бейджів."""
from django.urls import path

from . import badge_views, views

app_name = "projects"

# Owner-only URLs sit under the project URL. Anyone else gets a 404 from `owner_project`.
urlpatterns = [
    path("badge/<str:username>.svg", badge_views.profile_badge, name="badge_profile"),
    path("badge/<str:username>/<slug:slug>.svg", badge_views.project_badge, name="badge_project"),
    path("new/", views.new, name="new"),
    path("new/preview/", views.preview, name="preview"),
    path("u/<str:username>/<slug:slug>/", views.detail, name="detail"),
    path("u/<str:username>/<slug:slug>/edit/", views.edit, name="edit"),
    path("u/<str:username>/<slug:slug>/publish/", views.publish, name="publish"),
    path("u/<str:username>/<slug:slug>/unpublish/", views.unpublish, name="unpublish"),
    path("u/<str:username>/<slug:slug>/delete/", views.delete, name="delete"),
    path("u/<str:username>/<slug:slug>/repo/check/", views.repo_check, name="repo_check"),
    path("u/<str:username>/<slug:slug>/domain/verify/", views.domain_verify, name="domain_verify"),
    path("u/<str:username>/<slug:slug>/screenshots/add/", views.screenshot_add, name="screenshot_add"),
    path("u/<str:username>/<slug:slug>/screenshots/<int:pk>/delete/", views.screenshot_delete, name="screenshot_delete"),
    path("u/<str:username>/<slug:slug>/screenshots/<int:pk>/move/", views.screenshot_move, name="screenshot_move"),
    path("u/<str:username>/<slug:slug>/log/add/", views.log_add, name="log_add"),
    path("u/<str:username>/<slug:slug>/log/<int:pk>/delete/", views.log_delete, name="log_delete"),
]
