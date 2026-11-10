from django.urls import path

from . import views

app_name = "moderation"

urlpatterns = [
    path("report/project/<str:username>/<slug:slug>/", views.report_project, name="report_project"),
    path("report/user/<str:username>/", views.report_user, name="report_user"),
]
