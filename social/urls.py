"""Маршрути стрічки, підписок і вподобань."""
from django.urls import path

from . import views

app_name = "social"

# Action URLs live outside /u/<username>/..., where a project slug such as "follow" would clash.
urlpatterns = [
    path("feed/", views.feed, name="feed"),
    path("follow/<str:username>/", views.follow, name="follow"),
    path("unfollow/<str:username>/", views.unfollow, name="unfollow"),
    path("like/<str:username>/<slug:slug>/", views.like, name="like"),
    path("unlike/<str:username>/<slug:slug>/", views.unlike, name="unlike"),
]
