"""GitHub identity through the real allauth sign-in flow (OAuth start, callback, signup page).

Only the two HTTP calls to GitHub are faked (token exchange and GET /user, /user/emails); everything else
is allauth and our adapter as in production.
"""
import json
from contextlib import contextmanager
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from moderation.models import AuditLog

from .system import SYSTEM_USERNAME
from .tests import FAKE_GITHUB_APP, make_user

User = get_user_model()


def _response(status, body):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.headers["content-type"] = "application/json"
    return response


class FakeGitHub:
    """Stands in for requests.Session: answers the token URL and the two API endpoints."""

    def __init__(self, profile):
        self.profile = profile

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def request(self, method, url, **kwargs):
        assert url == "https://github.com/login/oauth/access_token", url
        return _response(200, {"access_token": "t0ken", "token_type": "bearer", "scope": "read:user,user:email"})

    def get(self, url, **kwargs):
        if url == "https://api.github.com/user":
            return _response(200, self.profile)
        if url == "https://api.github.com/user/emails":
            return _response(200, [{"email": f"{self.profile['login']}@example.com", "primary": True, "verified": True}])
        raise AssertionError(url)


@override_settings(SOCIALACCOUNT_PROVIDERS=FAKE_GITHUB_APP)
class GitHubLoginFlowTests(TestCase):
    @contextmanager
    def github(self, uid, login):
        fake = FakeGitHub({"id": uid, "login": login, "name": login, "bio": "", "avatar_url": ""})
        with patch("accounts.adapters.SocialAccountAdapter.get_requests_session", return_value=fake):
            yield

    def sign_in(self, uid, login, username=None):
        """POST to start OAuth, then GitHub's callback; for a new account also the signup step."""
        self.client.logout()
        with self.github(uid, login):
            start = self.client.post(reverse("github_login"), {"process": "login"})
            state = parse_qs(urlparse(start["Location"]).query)["state"][0]
            response = self.client.get(reverse("github_callback"), {"code": "c0de", "state": state})
            if response.status_code == 302 and response["Location"].endswith(reverse("socialaccount_signup")):
                response = self.client.post(reverse("socialaccount_signup"),
                                            {"username": username or login.lower(), "terms": "on"})
        self.assertLess(response.status_code, 500)
        return response

    def existing(self, username, uid, login):
        user = make_user(username, github_login=login)
        SocialAccount.objects.create(user=user, provider="github", uid=str(uid), extra_data={"login": login})
        return user

    def test_new_account_stores_login(self):
        self.sign_in(10, "Ann-GH", username="ann")
        user = User.objects.get(username="ann")
        self.assertEqual(user.github_login, "Ann-GH")
        self.assertEqual(SocialAccount.objects.get(user=user).uid, "10")

    def test_login_is_refreshed_at_every_sign_in(self):
        ann = self.existing("ann", 10, "ann-old")
        self.sign_in(10, "ann-new")
        ann.refresh_from_db()
        self.assertEqual(ann.github_login, "ann-new")
        self.assertEqual(self.client.session["_auth_user_id"], str(ann.pk))
        self.assertTrue(AuditLog.objects.filter(action="account.github_login.renamed", target_id=str(ann.pk)).exists())
        # The profile links to the current login.
        self.assertContains(self.client.get("/u/ann/"), "https://github.com/ann-new")

    def test_renamed_login_taken_by_a_new_account_does_not_crash(self):
        ann = self.existing("ann", 10, "shared")  # Ann renamed on GitHub; she has not signed in since
        response = self.sign_in(20, "shared", username="newcomer")
        self.assertEqual(response.status_code, 302)
        newcomer = User.objects.get(username="newcomer")
        ann.refresh_from_db()
        self.assertEqual(newcomer.github_login, "shared")
        self.assertEqual(ann.github_login, "")  # stale value cleared, not duplicated
        self.assertEqual(User.objects.filter(github_login__iexact="shared").count(), 1)
        self.assertTrue(AuditLog.objects.filter(action="account.github_login.released", target_id=str(ann.pk)).exists())
        # Ann comes back: she gets her current login, the newcomer keeps "shared".
        self.sign_in(10, "ann-renamed")
        ann.refresh_from_db()
        self.assertEqual(ann.github_login, "ann-renamed")
        self.assertEqual(User.objects.filter(username="ann").count(), 1)

    def test_existing_user_takes_a_login_held_stale_by_another(self):
        bob = self.existing("bob", 30, "bob")
        carol = self.existing("carol", 40, "Carol")  # stale: GitHub id 40 renamed away from "Carol"
        self.sign_in(30, "carol")  # case differs: GitHub logins are case-insensitive
        bob.refresh_from_db()
        carol.refresh_from_db()
        self.assertEqual(bob.github_login, "carol")
        self.assertEqual(carol.github_login, "")
        self.assertEqual(User.objects.exclude(username=SYSTEM_USERNAME).count(), 2)  # the system account is not a person

    def test_same_login_twice_changes_nothing(self):
        ann = self.existing("ann", 10, "ann")
        self.sign_in(10, "ann")
        ann.refresh_from_db()
        self.assertEqual(ann.github_login, "ann")
        self.assertFalse(AuditLog.objects.filter(action__startswith="account.github_login").exists())
