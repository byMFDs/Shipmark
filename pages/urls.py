"""Маршрути загальних сторінок."""
from django.urls import path

from . import seo, views

app_name = "pages"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("robots.txt", seo.robots_txt, name="robots"),
    path("sitemap.xml", seo.sitemap_xml, name="sitemap"),
    path("explore/", views.explore_view, name="explore"),
    path("about/", views.content_page, {"slug": "about"}, name="about"),
    path("legal/<slug:slug>/", views.legal_page, name="legal"),
    path("how-proof-works/", views.content_page, {"slug": "how-proof-works"}, name="how_proof_works"),
    path("styleguide/", views.styleguide, name="styleguide"),  # 404 unless DEBUG
]
