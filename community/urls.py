"""Маршрути спільноти."""
from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    path("community/", views.home, name="home"),
    path("community/b/<slug:slug>/", views.home, name="board"),
    path("community/new/", views.thread_new, name="new"),
    path("community/rules/", views.rules, name="rules"),
    path("community/notifications/", views.notifications_view, name="notifications"),
    path("community/t/<int:pk>/", views.thread_detail, name="thread_short"),
    path("community/t/<int:pk>-<slug:slug>/", views.thread_detail, name="thread"),
    path("community/t/<int:pk>/edit/", views.thread_edit, name="thread_edit"),
    path("community/t/<int:pk>/delete/", views.thread_delete, name="thread_delete"),
    path("community/t/<int:pk>/reply/", views.reply_create, name="reply"),
    path("community/t/<int:pk>/vote/", views.vote_thread, name="vote_thread"),
    path("community/r/<int:pk>/edit/", views.reply_edit, name="reply_edit"),
    path("community/r/<int:pk>/delete/", views.reply_delete, name="reply_delete"),
    path("community/r/<int:pk>/vote/", views.vote_reply, name="vote_reply"),
]
