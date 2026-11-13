from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("support/", views.support_form, name="form"),
    path("support/sent/", views.sent, name="sent"),
    path("support/attachment/<int:pk>/", views.attachment, name="attachment"),
]
