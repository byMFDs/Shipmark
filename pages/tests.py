from django.test import TestCase

from config import branding


class LandingTests(TestCase):
    def test_landing_returns_200_and_shows_site_name(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, branding.SITE_NAME)
        self.assertContains(response, f"{branding.SITE_NAME} is under construction")

    def test_viewport_meta(self):
        response = self.client.get("/")
        self.assertContains(response, "width=device-width, initial-scale=1, viewport-fit=cover")
