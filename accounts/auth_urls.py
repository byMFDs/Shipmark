"""Sign-in routes. Names are global (no namespace) because allauth looks them up by name."""
from allauth.socialaccount import views as social_views
from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("login/", views.login_page, name="account_login"),
    path("logout/", views.logout_page, name="account_logout"),
    # Step after the first GitHub login: confirm username + accept Terms.
    path("signup/", social_views.signup, name="socialaccount_signup"),
    path("login/cancelled/", social_views.login_cancelled, name="socialaccount_login_cancelled"),
    path("login/error/", social_views.login_error, name="socialaccount_login_error"),
    # allauth redirects here in a few cases; we have no "connected accounts" page.
    path("accounts/connections/", RedirectView.as_view(pattern_name="accounts:settings"), name="socialaccount_connections"),
]
