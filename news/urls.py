from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("news/", views.post_list, name="list"),
    path("news/<slug:slug>/", views.post_detail, name="detail"),
]
