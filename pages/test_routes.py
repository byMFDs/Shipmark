"""Every route, every role (POLISH3 stage 5b): GET each URL as anonymous, an ordinary member, the owner, a muted
member, a banned member, a moderator and a superuser, and compare the status code with what the rules say.

Others' drafts and hidden items are 404, write views answer GET with 405 (or a confirmation page), private pages send
anonymous visitors to sign in (302), /mod/ is 404 for anyone without the moderator badge, a ban shows the ban page
(403) and signs the person out (they browse on as anonymous; badges never touch the session). No route gives a 500.
"""
from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import badges
from accounts.models import User
from community.models import Board, Reply, Thread
from moderation import sanctions
from moderation.models import Report, Sanction
from news.models import NewsPost
from projects.models import BuildLogEntry, Project
from projects.tests import TEMP_MEDIA, make_project, make_shot, make_user
from support.models import SupportMessage

ROLES = ("anon", "user", "owner", "muted", "banned", "mod", "admin")
REASON = "Spam in every post, against the rules."


def expect(anon, user, owner=None, muted=None, banned=403, mod=None, admin=None):
    """Expected status per role; owner/muted/mod/admin default to the ordinary member's."""
    owner = user if owner is None else owner
    return {"anon": anon, "user": user, "owner": owner, "muted": user if muted is None else muted,
            "banned": banned, "mod": user if mod is None else mod, "admin": (user if mod is None else mod) if admin is None else admin}


@override_settings(MEDIA_ROOT=TEMP_MEDIA, COMMUNITY_ENABLED=True)
class RouteMatrixTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        old = timezone.now() - timedelta(days=60)
        cls.ann = make_user("ann", date_joined=old)
        cls.bob = make_user("bob", date_joined=old)
        cls.mute = make_user("mutey", date_joined=old)
        cls.banned = make_user("banny", date_joined=old)
        cls.mira = make_user("mira", date_joined=old)
        badges.grant(cls.mira, "moderator")
        cls.boss = User.objects.create_superuser("boss", "boss@example.com", "pw", date_joined=old)
        sanctions.issue(cls.mute, Sanction.Kind.MUTE, REASON, cls.boss, length=timedelta(days=1))
        sanctions.issue(cls.banned, Sanction.Kind.BAN, REASON, cls.boss, length=timedelta(days=1))

        cls.project = make_project(cls.ann)
        cls.draft = make_project(cls.ann, name="Drafty", status=Project.Status.DRAFT)
        cls.hidden = make_project(cls.ann, name="Hidden one", status=Project.Status.HIDDEN)
        cls.entry = BuildLogEntry.objects.create(project=cls.project, text="Shipped the badge.")
        cls.board = Board.objects.get(slug="help")
        cls.thread = Thread.objects.create(board=cls.board, author=cls.ann, title="How do I verify?", body="TXT record.")
        cls.reply = Reply.objects.create(thread=cls.thread, author=cls.bob, body="Check the TTL.")
        cls.news = NewsPost.objects.create(title="Hello", slug="hello", body="First post.", published_at=timezone.now())
        cls.news_draft = NewsPost.objects.create(title="Soon", slug="soon", body="Not yet.")
        cls.report = Report.objects.create(reporter=cls.bob, project=cls.project, target_owner=cls.ann,
                                           target_repr="Tallyhook", reason="spam")
        cls.support = SupportMessage.objects.create(email="ann@example.com", category="bug", body="Broken badge.")

    def setUp(self):
        cache.clear()
        self.shot = make_shot(self.project)

    def as_role(self, role):
        self.client.logout()
        user = {"anon": None, "user": self.bob, "owner": self.ann, "muted": self.mute, "banned": self.banned,
                "mod": self.mira, "admin": self.boss}[role]
        if user:
            self.client.force_login(user)
        return self.client

    def routes(self):
        """(url, expected statuses). 405: the route takes POST only."""
        a, p, d, h = "ann", self.project.slug, self.draft.slug, self.hidden.slug
        post_any = expect(405, 405)  # POST-only, no sign-in check before the method check
        post_login = expect(302, 405)  # POST-only behind sign-in
        post_owner = expect(302, 404, 405, mod=404, admin=404)  # someone else's project is 404 before the method
        post_mod = expect(302, 404, 404, mod=200, admin=200)  # GET shows the moderator's action form
        owner_only = expect(302, 404, 200, banned=403, mod=404, admin=404)
        signed_in = expect(302, 200, banned=403)
        public = expect(200, 200, banned=403)
        return [
            ("/", expect(200, 302, banned=403)),  # signed-in members go to the feed
            (reverse("pages:explore"), public),
            (reverse("pages:explore") + "?tab=people&q=an", public),
            (reverse("pages:about"), public),
            (reverse("pages:legal", args=["privacy"]), public),
            (reverse("pages:legal", args=["nope"]), expect(404, 404, banned=403)),
            (reverse("pages:how_proof_works"), public),
            (reverse("social:feed"), public),
            (reverse("social:feed") + "?tab=following", public),  # anonymous visitors get the default tab
            (reverse("news:list"), public),
            (reverse("news:detail", args=["hello"]), public),
            (reverse("news:detail", args=["soon"]), expect(404, 404, banned=403, mod=404, admin=404)),
            (reverse("support:form"), public),
            (reverse("support:sent"), public),
            (reverse("support:attachment", args=[999999]), expect(404, 404, banned=403, mod=404, admin=404)),
            (reverse("accounts:profile", args=[a]), public),
            (reverse("accounts:profile", args=["nobody"]), expect(404, 404, banned=403)),
            (reverse("accounts:settings"), signed_in),
            (reverse("accounts:delete"), signed_in),
            (reverse("accounts:export"), post_login),
            (reverse("projects:new"), expect(302, 200)),  # a muted member sees the form; the POST is refused
            (reverse("projects:badge_profile", args=[a]), expect(200, 200, banned=200)),
            (reverse("projects:badge_project", args=[a, p]), expect(200, 200, banned=200)),
            (reverse("projects:badge_project", args=[a, d]), expect(200, 200, banned=200)),  # neutral "not found" badge, by design
            (reverse("projects:detail", args=[a, p]), public),
            (reverse("projects:detail", args=[a, d]), expect(404, 404, 200, banned=403)),
            (reverse("projects:detail", args=[a, h]), expect(404, 404, 200, banned=403)),
            (reverse("projects:edit", args=[a, p]), owner_only),
            (reverse("projects:edit", args=[a, d]), owner_only),
            (reverse("projects:delete", args=[a, p]), owner_only),
            (reverse("projects:publish", args=[a, d]), post_owner),
            (reverse("projects:unpublish", args=[a, p]), post_owner),
            (reverse("projects:repo_check", args=[a, p]), post_owner),
            (reverse("projects:domain_verify", args=[a, p]), post_owner),
            (reverse("projects:screenshot_add", args=[a, p]), post_owner),
            (reverse("projects:screenshot_delete", args=[a, p, self.shot.pk]), post_owner),
            (reverse("projects:screenshot_move", args=[a, p, self.shot.pk]), post_owner),
            (reverse("projects:log_add", args=[a, p]), post_owner),
            (reverse("projects:log_delete", args=[a, p, self.entry.pk]), post_owner),
            (reverse("projects:preview"), post_login),
            (reverse("social:follow", args=[a]), post_any),
            (reverse("social:unfollow", args=[a]), post_any),
            (reverse("social:like", args=[a, p]), post_any),
            (reverse("social:unlike", args=[a, p]), post_any),
            (reverse("moderation:report_project", args=[a, p]), expect(302, 200, 302)),  # own item: back with a message
            (reverse("moderation:report_user", args=[a]), expect(302, 200, 302)),
            (reverse("moderation:report_log_entry", args=[a, p, self.entry.pk]), expect(302, 200, 302)),
            (reverse("moderation:report_thread", args=[self.thread.pk]), expect(302, 200, 302)),
            (reverse("moderation:report_reply", args=[self.reply.pk]), expect(302, 302, 200, muted=200, mod=200)),  # bob wrote the reply
            (reverse("moderation:queue"), expect(302, 404, banned=403, mod=200, admin=200)),
            (reverse("moderation:report_detail", args=[self.report.pk]), expect(302, 404, banned=403, mod=200, admin=200)),
            (reverse("moderation:act_project", args=[self.project.pk]), post_mod),
            (reverse("moderation:act_user", args=[a]), post_mod),
            (reverse("moderation:act_log_entry", args=[self.entry.pk]), post_mod),
            (reverse("moderation:act_thread", args=[self.thread.pk]), post_mod),
            (reverse("moderation:act_reply", args=[self.reply.pk]), post_mod),
            (reverse("moderation:dismiss_notice", args=[1]), post_login),
            (reverse("community:home"), public),
            (reverse("community:board", args=["help"]), public),
            (reverse("community:board", args=["nope"]), expect(404, 404, banned=403)),
            (reverse("community:rules"), public),
            (reverse("community:new"), expect(302, 200, banned=403)),
            (reverse("community:notifications"), signed_in),
            (reverse("community:thread_short", args=[self.thread.pk]), expect(301, 301, banned=403)),
            (self.thread.get_absolute_url(), public),
            (reverse("community:thread_edit", args=[self.thread.pk]), expect(302, 404, 200, banned=403)),
            (reverse("community:thread_delete", args=[self.thread.pk]), expect(302, 404, 200, banned=403)),
            (reverse("community:reply_edit", args=[self.reply.pk]), expect(302, 200, 404, muted=404, mod=404)),
            (reverse("community:reply_delete", args=[self.reply.pk]), expect(302, 200, 404, muted=404, mod=404)),
            (reverse("community:reply", args=[self.thread.pk]), post_login),
            (reverse("community:vote_thread", args=[self.thread.pk]), post_any),
            (reverse("community:vote_reply", args=[self.reply.pk]), post_any),
            (reverse("pages:styleguide"), expect(404, 404)),  # DEBUG only
        ]

    def test_matrix(self):
        problems = []
        for url, wanted in self.routes():
            for role in ROLES:
                got = self.as_role(role).get(url).status_code
                if got != wanted[role]:
                    problems.append(f"{url:55} {role:7} expected {wanted[role]} got {got}")
        self.assertEqual(problems, [], "\n" + "\n".join(problems))
