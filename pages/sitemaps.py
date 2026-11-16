"""Мапа сайту sitemap.xml: лише публічні сторінки, адреси з SITE_URL.

sitemap.xml for search engines (django.contrib.sitemaps). Only pages anyone may open and that are worth indexing.

Included: home, about, how proof works, legal pages, news (index and articles), published projects of visible
owners, profiles of visible people who have at least one published project (a profile without one is noindex, so
it is not listed), and community threads only while COMMUNITY_ENABLED.
Never listed: drafts, hidden or removed projects, suspended or banned people, the system account, inactive
accounts, demo accounts of seed_community, settings, sign-in, search results, error pages.
URLs always use SITE_URL (config/site.py), never the Host of the request.
"""
from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Max, Q
from django.urls import reverse

from accounts.models import User
from accounts.people import DEMO_DOMAIN, DEMO_PREFIX
from accounts.system import SYSTEM_USERNAME
from moderation.visibility import visible_users
from news.models import NewsPost
from social.queries import published_projects


def not_demo(prefix=""):
    """Q для рядків, чий автор не демо-акаунт seed_community. prefix — шлях до користувача ("owner__")."""
    return ~Q(**{f"{prefix}username__startswith": DEMO_PREFIX, f"{prefix}email__endswith": DEMO_DOMAIN})


def real_people(queryset):
    """Люди, яких можна показувати публічно: активні, не призупинені, не забанені, не системні й не демо."""
    return (visible_users(queryset.filter(is_active=True)).exclude(username=SYSTEM_USERNAME)
            .filter(not_demo()))


class CanonicalSitemap(Sitemap):
    """Базовий клас: адреси з SITE_URL, а не з Host запиту."""
    protocol = None  # taken from SITE_URL

    def get_urls(self, page=1, site=None, protocol=None):
        parts = urlsplit(settings.SITE_URL)
        return super().get_urls(page=page, site=SimpleNamespace(domain=parts.netloc), protocol=parts.scheme)


class StaticSitemap(CanonicalSitemap):
    """Головна, про сайт, як працюють докази, юридичні сторінки й список новин."""
    changefreq = "monthly"

    def items(self):
        names = [("pages:landing", None, 1.0), ("pages:about", None, 0.5), ("pages:how_proof_works", None, 0.7)]
        names += [("pages:legal", [slug], 0.3) for slug in ("privacy", "terms", "cookies")]
        if NewsPost.objects.published().exists():
            names.append(("news:list", None, 0.5))
        return names

    def location(self, item):
        name, args, _priority = item
        return reverse(name, args=args)

    def priority(self, item):
        return item[2]


class NewsSitemap(CanonicalSitemap):
    """Опубліковані новини."""
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return NewsPost.objects.published().order_by("-published_at")

    def lastmod(self, item):
        return item.updated_at


class ProjectSitemap(CanonicalSitemap):
    """Опубліковані проєкти видимих власників."""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return (published_projects().filter(owner__is_active=True).exclude(owner__username=SYSTEM_USERNAME)
                .filter(not_demo("owner__")).select_related("owner").order_by("-updated_at", "-pk"))

    def lastmod(self, item):
        return item.updated_at


class ProfileSitemap(CanonicalSitemap):
    """Профілі людей, які мають хоча б один опублікований проєкт."""
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        published = Q(projects__status="published")
        return (real_people(User.objects.all()).filter(published)
                .annotate(latest=Max("projects__updated_at", filter=published))
                .order_by("-latest", "pk"))

    def location(self, item):
        return reverse("accounts:profile", args=[item.username])

    def lastmod(self, item):
        return item.latest


class ThreadSitemap(CanonicalSitemap):
    """Публічні гілки спільноти; порожній, поки COMMUNITY_ENABLED вимкнено."""
    changefreq = "daily"
    priority = 0.4

    def items(self):
        if not settings.COMMUNITY_ENABLED:
            return []
        from community.models import Thread
        return (Thread.objects.public().filter(author__isnull=False).filter(not_demo("author__"))
                .select_related("board").order_by("-last_activity_at", "-pk"))

    def lastmod(self, item):
        return item.last_activity_at


SITEMAPS = {
    "pages": StaticSitemap,
    "news": NewsSitemap,
    "projects": ProjectSitemap,
    "profiles": ProfileSitemap,
    "threads": ThreadSitemap,
}
