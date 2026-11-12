from django.urls import path

from . import mod_views, views

app_name = "moderation"

urlpatterns = [
    path("report/project/<str:username>/<slug:slug>/", views.report_project, name="report_project"),
    path("report/user/<str:username>/", views.report_user, name="report_user"),
    path("report/log/<str:username>/<slug:slug>/<int:pk>/", views.report_log_entry, name="report_log_entry"),
    path("notices/<int:pk>/dismiss/", mod_views.dismiss_notice, name="dismiss_notice"),
    # /mod/: moderator badge or superuser only (404 for everyone else).
    path("mod/", mod_views.queue, name="queue"),
    path("mod/reports/<int:pk>/", mod_views.report_detail, name="report_detail"),
    path("mod/act/project/<int:pk>/", mod_views.act_project, name="act_project"),
    path("mod/act/user/<str:username>/", mod_views.act_user, name="act_user"),
    path("mod/act/log/<int:pk>/", mod_views.act_log_entry, name="act_log_entry"),
]
