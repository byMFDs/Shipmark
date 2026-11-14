from urllib.parse import parse_qs, urlparse

from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .models import ProfileLink
from .forms import SignupConfirmForm
from .usernames import RESERVED_USERNAMES, generate_username, validate_username

User = get_user_model()

GITHUB_DATA = {
    "id": 4242,
    "login": "Octo-Cat",
    "name": "Octo  Cat",
    "bio": "Builds things\nwith AI",
    "avatar_url": "https://avatars.githubusercontent.com/u/4242",
    "email": "octo@example.com",
}


FAKE_GITHUB_APP = {"github": {
    "SCOPE": ["read:user", "user:email"],
    "APPS": [{"client_id": "id", "secret": "secret"}],
}}


def make_user(username, **extra):
    return User.objects.create_user(username=username, password="x", **extra)


class UsernameRuleTests(TestCase):
    """Правила імені користувача."""
    def test_every_reserved_name_is_rejected(self):
        for name in RESERVED_USERNAMES:
            if len(name) < 3:  # "u" and "p" fail on length first; both are still rejected
                with self.assertRaises(ValidationError):
                    validate_username(name)
                continue
            with self.assertRaises(ValidationError) as ctx:
                validate_username(name)
            self.assertEqual(ctx.exception.code, "reserved", name)

    def test_bad_characters_and_case_rejected(self):
        for bad in ["Danylo", "a b c", "dan.ylo", "-danylo", "ab", "x" * 40, "дан-ило"]:
            with self.assertRaises(ValidationError, msg=bad):
                validate_username(bad)

    def test_good_names_pass(self):
        for good in ["danylo", "dan-ylo", "dan_ylo", "9lives", "abc"]:
            validate_username(good)

    def test_generated_name_is_never_reserved(self):
        self.assertNotIn(generate_username("admin"), RESERVED_USERNAMES)
        self.assertEqual(generate_username("admin"), "admin-2")
        self.assertEqual(generate_username("u"), "u-2")  # too short, gets a suffix to reach 3 chars

    def test_duplicate_login_gets_a_suffix(self):
        make_user("octocat")
        self.assertEqual(generate_username("octocat"), "octocat-2")
        make_user("octocat-2")
        self.assertEqual(generate_username("OctoCat"), "octocat-3")  # case-insensitive

    def test_suffix_keeps_name_within_max_length(self):
        long_name = "a" * 39
        make_user(long_name)
        result = generate_username(long_name)
        self.assertLessEqual(len(result), 39)
        self.assertTrue(result.endswith("-2"))


class GitHubSignupTests(TestCase):
    """Реєстрація через GitHub."""
    def setUp(self):
        self.factory = RequestFactory()

    def request(self):
        request = self.factory.post("/signup/")
        SessionMiddleware(lambda r: None).process_request(request)
        MessageMiddleware(lambda r: None).process_request(request)
        return request

    def sociallogin(self, request, data=None):
        provider = GitHubProvider(request, app=SocialApp(provider="github", client_id="id", secret="secret"))
        return provider.sociallogin_from_response(request, data or GITHUB_DATA)

    @override_settings(SOCIALACCOUNT_PROVIDERS=FAKE_GITHUB_APP)
    def test_oauth_redirect_asks_for_exactly_two_scopes(self):
        response = self.client.post(reverse("github_login"), {"process": "login"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://github.com/login/oauth/authorize"))
        query = parse_qs(urlparse(response["Location"]).query)
        self.assertEqual(sorted(query["scope"][0].split()), ["read:user", "user:email"])
        self.assertEqual(query["client_id"], ["id"])

    def test_oauth_cannot_start_with_get(self):
        # A GET only shows a confirmation page; it must not redirect to GitHub.
        with override_settings(SOCIALACCOUNT_PROVIDERS=FAKE_GITHUB_APP):
            response = self.client.get(reverse("github_login"))
        self.assertEqual(response.status_code, 200)

    def test_user_is_filled_from_github_data(self):
        request = self.request()
        sociallogin = self.sociallogin(request)
        user = sociallogin.user
        self.assertEqual(user.username, "octo-cat")
        self.assertEqual(user.github_login, "Octo-Cat")
        self.assertEqual(user.display_name, "Octo Cat")
        self.assertEqual(user.about, "Builds things with AI")
        self.assertEqual(user.avatar_url, GITHUB_DATA["avatar_url"])
        self.assertEqual(user.email, "octo@example.com")

    def test_long_bio_is_cut_to_1000(self):
        request = self.request()
        sociallogin = self.sociallogin(request, {**GITHUB_DATA, "bio": "x" * 1500})
        self.assertEqual(len(sociallogin.user.about), 1000)

    def test_terms_checkbox_is_required(self):
        request = self.request()
        form = SignupConfirmForm({"username": "octo-cat"}, sociallogin=self.sociallogin(request))
        self.assertFalse(form.is_valid())
        self.assertIn("terms", form.errors)

    def test_reserved_and_taken_usernames_rejected_in_form(self):
        make_user("taken")
        for name in ["admin", "settings", "Taken"]:
            form = SignupConfirmForm({"username": name, "terms": "on"}, sociallogin=self.sociallogin(self.request()))
            self.assertFalse(form.is_valid(), name)
            self.assertIn("username", form.errors)

    def test_form_has_no_email_field(self):
        form = SignupConfirmForm(sociallogin=self.sociallogin(self.request()))
        self.assertNotIn("email", form.fields)

    def test_saving_stores_terms_version_and_time(self):
        request = self.request()
        form = SignupConfirmForm({"username": "Octo-Cat", "terms": "on"}, sociallogin=self.sociallogin(request))
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save(request)
        user.refresh_from_db()
        self.assertEqual(user.username, "octo-cat")  # lowercased
        self.assertEqual(user.terms_version_accepted, settings.TERMS_VERSION)
        self.assertIsNotNone(user.terms_accepted_at)
        self.assertEqual(user.email, "octo@example.com")  # not wiped by the form
        self.assertFalse(user.has_usable_password())

    def test_only_two_github_scopes(self):
        self.assertEqual(settings.SOCIALACCOUNT_PROVIDERS["github"]["SCOPE"], ["read:user", "user:email"])


@override_settings(SOCIALACCOUNT_PROVIDERS=FAKE_GITHUB_APP)
class SignupViewTests(TestCase):
    """Сторінка підтвердження реєстрації.

    The real /signup/ page, with a pending GitHub login placed in the session."""

    def start(self, data=None):
        request = RequestFactory().get("/")
        SessionMiddleware(lambda r: None).process_request(request)
        provider = GitHubProvider(request, app=SocialApp(provider="github", client_id="id", secret="secret"))
        sociallogin = provider.sociallogin_from_response(request, data or GITHUB_DATA)
        session = self.client.session
        session["socialaccount_sociallogin"] = sociallogin.serialize()
        session.save()

    def test_without_pending_login_goes_to_sign_in(self):
        self.assertRedirects(self.client.get("/signup/"), reverse("account_login"), fetch_redirect_response=False)

    def test_page_prefills_username_and_asks_for_terms(self):
        self.start()
        response = self.client.get("/signup/")
        self.assertContains(response, 'value="octo-cat"')
        self.assertContains(response, 'name="terms"')
        self.assertNotContains(response, 'name="email"')

    def test_post_without_terms_creates_nothing(self):
        self.start()
        response = self.client.post("/signup/", {"username": "octo-cat"})
        self.assertContains(response, "accept the Terms")
        self.assertFalse(User.objects.filter(username="octo-cat").exists())

    def test_full_signup_creates_user_and_signs_in(self):
        self.start()
        response = self.client.post("/signup/", {"username": "octo-cat", "terms": "on"})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="octo-cat")
        self.assertEqual(user.github_login, "Octo-Cat")
        self.assertEqual(user.terms_version_accepted, settings.TERMS_VERSION)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_second_github_account_with_same_login_gets_suffix(self):
        make_user("octo-cat")
        self.start()
        self.assertContains(self.client.get("/signup/"), 'value="octo-cat-2"')


class AuthPageTests(TestCase):
    """Сторінки входу й виходу."""
    def test_login_page_starts_oauth_with_post(self):
        with self.settings(GITHUB_OAUTH_CONFIGURED=True):
            response = self.client.get(reverse("account_login"))
        self.assertContains(response, f'method="post" action="{reverse("github_login")}"')

    def test_login_page_without_credentials_does_not_crash(self):
        with self.settings(GITHUB_OAUTH_CONFIGURED=False):
            response = self.client.get(reverse("account_login"))
        self.assertContains(response, "not set up")
        self.assertNotContains(response, reverse("github_login"))

    def test_no_password_login_or_signup_routes(self):
        for path in ["/accounts/login/", "/accounts/signup/", "/accounts/password/reset/"]:
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_logout_needs_post(self):
        user = make_user("sam")
        self.client.force_login(user)
        self.assertContains(self.client.get(reverse("account_logout")), "Sign out?")
        self.assertIn("_auth_user_id", self.client.session)  # GET did not sign out
        self.client.post(reverse("account_logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_header_shows_account_menu_when_signed_in(self):
        self.client.force_login(make_user("sam", display_name="Sam Lee"))
        html = self.client.get("/explore/").content.decode()  # / redirects signed-in users to the feed
        self.assertIn(reverse("accounts:settings"), html)
        self.assertIn(reverse("account_logout"), html)
        self.assertIn("user-menu", html)

    def test_header_shows_sign_in_when_signed_out(self):
        self.assertContains(self.client.get("/"), reverse("account_login"))


class SettingsTests(TestCase):
    """Збереження налаштувань."""
    def setUp(self):
        cache.clear()
        self.alice = make_user("alice", display_name="Alice", about="old")
        self.bob = make_user("bob", display_name="Bob", about="bob bio")
        self.url = reverse("accounts:settings")

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.url}")
        response = self.client.post(self.url, {"display_name": "Hacked"})
        self.assertEqual(response.status_code, 302)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.display_name, "Alice")

    def test_user_can_edit_own_settings(self):
        self.client.force_login(self.alice)
        response = self.client.post(self.url, {
            "display_name": "  Alice   Liddell ", "headline": " Builds   things ", "about": "new **about**",
            "location": "Kyiv", "status": "hiring", "preferred_language": "uk",
        })
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.display_name, "Alice Liddell")
        self.assertEqual((self.alice.headline, self.alice.about), ("Builds things", "new **about**"))
        self.assertEqual((self.alice.location, self.alice.status), ("Kyiv", "hiring"))
        self.assertEqual(self.alice.preferred_language, "uk")

    def test_invalid_form_shows_error_summary_for_screen_readers(self):
        # The summary is role="alert", links to the bad field, and the field points at its error.
        self.client.force_login(self.alice)
        response = self.client.post(self.url, {"display_name": "Alice", "about": "x" * 1200, "preferred_language": "en"})
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("data-error-summary", html)
        self.assertIn('role="alert"', html)
        self.assertIn('href="#id_about"', html)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn("id_about_error", html)

    def test_cannot_edit_another_users_settings(self):
        self.client.force_login(self.alice)
        # Forged fields that try to point at Bob or to change protected fields.
        self.client.post(self.url, {
            "display_name": "Alice", "about": "x", "id": self.bob.pk, "pk": self.bob.pk,
            "username": "bob", "user": self.bob.pk, "is_staff": "on", "is_superuser": "on",
            "is_suspended": "on", "github_login": "someone-else",
        })
        self.bob.refresh_from_db()
        self.assertEqual((self.bob.display_name, self.bob.about, self.bob.username), ("Bob", "bob bio", "bob"))
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.username, "alice")
        self.assertFalse(self.alice.is_staff or self.alice.is_superuser or self.alice.is_suspended)
        self.assertEqual(self.alice.github_login, "")

    def test_settings_page_shows_only_own_data(self):
        self.client.force_login(self.alice)
        response = self.client.get(self.url)
        self.assertContains(response, "Alice")
        self.assertNotContains(response, "bob bio")

    def test_links_must_be_http_or_https(self):
        self.client.force_login(self.alice)
        for bad in ["javascript:alert(1)", "ftp://example.com/x", "https://user:pw@example.com/"]:
            response = self.client.post(self.url, {"display_name": "A", "link0_kind": "website", "link0_url": bad})
            self.assertEqual(response.status_code, 200, bad)
            self.assertFalse(self.alice.links.exists(), bad)

    def test_unknown_language_rejected(self):
        self.client.force_login(self.alice)
        self.client.post(self.url, {"display_name": "A", "preferred_language": "ru"})
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.preferred_language, "")

    def test_suspended_user_cannot_write(self):
        self.alice.is_suspended = True
        self.alice.save()
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(self.url, {"display_name": "New"}).status_code, 403)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.display_name, "Alice")

    def test_rate_limited(self):
        self.client.force_login(self.alice)
        for _ in range(30):
            self.client.post(self.url, {"display_name": "A"})
        response = self.client.post(self.url, {"display_name": "Changed"})
        self.assertContains(response, "Too many changes")
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.display_name, "A")


class PublicProfileTests(TestCase):
    """Публічний профіль і 404 для прихованих."""
    def setUp(self):
        self.alice = make_user(
            "alice", email="alice-private@example.com", display_name="Alice A", headline="I build things",
            github_login="alice-gh",
        )
        ProfileLink.objects.create(user=self.alice, kind="website", url="https://alice.example.org")

    def url(self, name="alice"):
        return reverse("accounts:profile", args=[name])

    def test_public_page_shows_profile_data(self):
        response = self.client.get(self.url())
        self.assertContains(response, "Alice A")
        self.assertContains(response, "I build things")
        self.assertContains(response, "https://github.com/alice-gh")
        self.assertContains(response, 'rel="nofollow ugc noopener"')
        self.assertContains(response, 'property="og:title"')
        self.assertContains(response, "og-default.png")

    def test_unknown_user_is_404(self):
        self.assertEqual(self.client.get(self.url("nobody")).status_code, 404)

    def test_suspended_user_is_404_for_everyone(self):
        self.alice.is_suspended = True
        self.alice.save()
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        # Same answer as for a name that never existed.
        self.assertEqual(self.client.get(self.url("nobody")).status_code, 404)

    def test_email_never_appears(self):
        for viewer in (None, self.alice, make_user("bob", email="bob-private@example.com")):
            if viewer:
                self.client.force_login(viewer)
            html = self.client.get(self.url()).content.decode()
            self.assertNotIn("alice-private@example.com", html)
            self.assertNotIn("bob-private@example.com", html)

    def test_non_http_link_is_not_shown(self):
        ProfileLink.objects.filter(user=self.alice).update(url="javascript:alert(1)")
        self.assertNotContains(self.client.get(self.url()), "javascript:")

    def test_uppercase_url_redirects_to_canonical(self):
        response = self.client.get(self.url("Alice"))
        self.assertRedirects(response, self.url(), status_code=301)

    def test_empty_state_differs_for_owner(self):
        self.assertNotContains(self.client.get(self.url()), "Add something you shipped")
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(self.url()), "Add something you shipped")

    def test_user_text_is_escaped(self):
        User.objects.filter(pk=self.alice.pk).update(display_name="<script>x</script>")
        response = self.client.get(self.url())
        self.assertNotContains(response, "<script>x</script>")
