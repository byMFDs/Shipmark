"""Community UI layer: what the pages render (shell, lists, grids, lightbox, picker, forms) and who sees what.

The rules themselves (limits, mute/ban, protected accounts, depth) are tested in tests.py; here the question is
whether the templates show the right thing to the right person, and stay safe and stable with odd data."""
import re
from unittest import mock

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import override_settings
from django.urls import reverse
from django.utils import translation

from moderation.models import Sanction

from . import limits, services
from .models import Thread
from .stickers import STICKERS
from .tests import REASON, CommunityTestCase, _clean, make_thread


def tile_attrs(html):
    """[(data-width, data-height, classes)] of the image tiles in a page."""
    return [(int(w), int(h), c) for c, w, h in re.findall(
        r'<a class="(media-grid__tile[^"]*)" href="[^"]+" data-full="[^"]+" data-width="(\d+)" data-height="(\d+)"', html)
    ]


class ShellTests(CommunityTestCase):
    def test_every_page_uses_the_three_column_shell_with_boards_and_rules(self):
        self.client.force_login(self.bob)
        reply = services.create_reply(self.ann, self.thread, body="Try the TXT record again.")
        for url in (reverse("community:home"), reverse("community:board", args=["help"]), self.thread.get_absolute_url(),
                    reverse("community:new"), reverse("community:notifications"), reverse("community:rules")):
            with self.subTest(url=url):
                page = self.client.get(url)
                self.assertEqual(page.status_code, 200)
                for marker in ('class="feed-nav community-nav"', 'class="feed-side community-side"', "community-boards__list",
                               "data-lightbox", "css/pages/community.css"):
                    self.assertContains(page, marker)
        self.assertEqual(reply.thread_id, self.thread.pk)

    def test_boards_column_counts_public_threads_and_marks_the_current_board(self):
        make_thread(self.bob, title="Second help thread")
        make_thread(self.bob, title="Removed one", status=Thread.Status.REMOVED)
        page = self.client.get(reverse("community:board", args=["help"]))
        current = re.findall(r'<a class="community-boards__link" href="/community/b/help/" aria-current="page"', page.content.decode())
        self.assertEqual(len(current), 2)  # the desktop and the phone copy of the list
        counts = {board.slug: board.thread_count for board in page.context["boards"]}
        self.assertEqual(counts["help"], 2)
        self.assertEqual(counts["off-topic"], 0)

    def test_new_thread_button_depends_on_who_looks(self):
        anonymous = self.client.get(reverse("community:home"))
        self.assertNotContains(anonymous, reverse("community:new"))
        self.assertContains(anonymous, reverse("account_login"))
        self.client.force_login(self.bob)
        self.assertContains(self.client.get(reverse("community:board", args=["help"])), reverse("community:new") + "?board=help")

    def test_rules_page_renders_the_markdown_and_falls_back_to_english(self):
        page = self.client.get(reverse("community:rules"))
        self.assertContains(page, "<h1")
        self.assertContains(page, "Be kind and specific")
        self.assertNotContains(page, "{{ contact_email }}")
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "uk"
        uk = self.client.get(reverse("community:rules"))
        self.assertEqual(uk.status_code, 200)
        self.assertContains(uk, "Be kind and specific")  # no Ukrainian file yet: the English text, labelled as such
        self.assertContains(uk, 'lang="en"')

    def test_rules_page_is_a_404_while_the_flag_is_off(self):
        with override_settings(COMMUNITY_ENABLED=False):
            self.assertEqual(self.client.get(reverse("community:rules")).status_code, 404)

    def test_sort_tabs_search_and_period_links_keep_the_right_parameters(self):
        page = self.client.get(reverse("community:home"), {"sort": "top", "t": "month", "q": "domain"})
        self.assertEqual(page.context["sort_urls"]["new"], "/community/?q=domain&sort=new")
        self.assertEqual(page.context["window_urls"]["all"], "/community/?q=domain&sort=top&t=all")
        self.assertContains(page, 'name="t" value="month"')
        self.assertContains(page, "noindex")  # filtered lists stay out of search engines

    def test_search_text_is_escaped(self):
        page = self.client.get(reverse("community:home"), {"q": "<script>alert(1)</script>"})
        self.assertNotContains(page, "<script>alert(1)")
        self.assertContains(page, "No threads match this search")

    def test_titles_and_names_are_escaped_in_cards(self):
        make_thread(self.bob, title='<img src=x onerror=alert(1)> "quoted"')
        page = self.client.get(reverse("community:home"))
        self.assertNotContains(page, "<img src=x")
        self.assertContains(page, "&lt;img src=x onerror=alert(1)&gt;")

    def test_empty_states_are_designed_and_offer_the_next_step(self):
        Thread.objects.all().delete()
        anonymous = self.client.get(reverse("community:home"))
        self.assertContains(anonymous, "community-empty")
        self.assertContains(anonymous, "stickers/coffee.svg")
        self.assertContains(anonymous, reverse("account_login"))
        self.client.force_login(self.bob)
        self.assertContains(self.client.get(reverse("community:home")), reverse("community:new"))
        self.assertContains(self.client.get(reverse("community:notifications")), "stickers/sleepy.svg")
        searched = self.client.get(reverse("community:home"), {"q": "nothing"})
        self.assertContains(searched, "stickers/eyes.svg")


class LoadMoreTests(CommunityTestCase):
    def test_threads_load_more_returns_html_and_the_next_url(self):
        for n in range(5):
            make_thread(self.bob, title=f"Thread number {n}")
        with mock.patch.object(limits, "THREADS_PER_PAGE", 2):
            page = self.client.get(reverse("community:home"), {"sort": "new"})
            self.assertContains(page, "data-load-more")
            first = self.client.get(reverse("community:home"), {"sort": "new"}, headers={"Accept": "application/json"})
            self.assertEqual(first.status_code, 200)
            data = first.json()
            self.assertEqual(data["html"].count('data-feed-item'), 2)
            self.assertEqual(data["next_url"], "/community/?sort=new&page=2")
            last = self.client.get(reverse("community:home"), {"sort": "new", "page": 3}, headers={"Accept": "application/json"})
            self.assertEqual(last.json()["next_url"], "")
            self.assertEqual(last.json()["html"].count("data-feed-item"), 2)  # 6 threads (one from setUp), pages of 2

    def test_json_page_contains_no_page_chrome(self):
        data = self.client.get(reverse("community:home"), headers={"Accept": "application/json"}).json()
        self.assertNotIn("<html", data["html"])
        self.assertNotIn("community-nav", data["html"])

    def test_reply_load_more_returns_branches_with_their_replies(self):
        with mock.patch.object(limits, "REPLIES_PER_PAGE", 2):
            tops = [services.create_reply(self.bob, self.thread, body=f"Top {n}") for n in range(3)]
            services.create_reply(self.ann, self.thread, parent=tops[0], body="Child of the first.")
            page = self.client.get(self.thread.get_absolute_url(), {"sort": "new"})
            self.assertTrue(page.context["has_next"])
            self.assertEqual(page.context["next_url"], f"{self.thread.get_absolute_url()}?sort=new&page=2")
            data = self.client.get(self.thread.get_absolute_url(), {"sort": "new", "page": 2},
                                   headers={"Accept": "application/json"}).json()
            self.assertIn("Top 0", data["html"])
            self.assertIn("Child of the first.", data["html"])
            self.assertEqual(data["next_url"], "")

    def test_hidden_threads_and_replies_never_appear_in_json(self):
        mira_thread = make_thread(self.mira, title="Removed by a moderator", status=Thread.Status.REMOVED)
        reply = services.create_reply(self.bob, self.thread, body="Quietly removed text.")
        self.assertEqual(self.act(self.mira, reply, "remove_reply").status_code, 302)
        home = self.client.get(reverse("community:home"), headers={"Accept": "application/json"}).json()
        self.assertNotIn(mira_thread.title, home["html"])
        replies = self.client.get(self.thread.get_absolute_url(), headers={"Accept": "application/json"}).json()
        self.assertNotIn("Quietly removed text.", replies["html"])


class ImageGridTests(CommunityTestCase):
    def thread_with(self, *sizes):
        images = [_clean(size=size, name=f"{n}.png") for n, size in enumerate(sizes)]
        return services.create_thread(self.bob, self.board, "A thread with pictures", "See the pictures.", images)

    def test_grid_class_follows_the_number_of_images(self):
        for count in (1, 2, 3, 4):
            thread = self.thread_with(*[(300 + n, 200) for n in range(count)])
            page = self.client.get(thread.get_absolute_url())
            with self.subTest(count=count):
                self.assertContains(page, f"media-grid media-grid--{count}", count=1)
                self.assertEqual(len(tile_attrs(page.content.decode())), count)

    def test_every_tile_has_dimensions_lazy_loading_and_alt_text(self):
        thread = self.thread_with((1200, 800), (800, 1200))
        html = self.client.get(thread.get_absolute_url()).content.decode()
        tiles = re.findall(r'<a class="media-grid__tile.*?</a>', html, re.S)
        self.assertEqual(len(tiles), 2)
        for index, tile in enumerate(tiles, 1):
            with self.subTest(tile=index):
                self.assertRegex(tile, r'<img [^>]*width="\d+" height="\d+"')
                self.assertNotIn('width="0"', tile)
                self.assertIn('loading="lazy"', tile)
                self.assertIn(f"Image {index} of 2", tile)
                self.assertRegex(tile, r'srcset="[^"]+ \d+w, [^"]+ \d+w"')

    def test_unusual_shapes_keep_dimensions_and_get_their_classes(self):
        wide = self.thread_with((3000, 120))
        tall = self.thread_with((90, 2800))
        tiny = self.thread_with((8, 8))
        wide_tile, = tile_attrs(self.client.get(wide.get_absolute_url()).content.decode())
        tall_tile, = tile_attrs(self.client.get(tall.get_absolute_url()).content.decode())
        tiny_tile, = tile_attrs(self.client.get(tiny.get_absolute_url()).content.decode())
        self.assertEqual(wide_tile[:2], (1600, 64))  # the display copy is capped at 1600 on the long side
        self.assertNotIn("--tall", wide_tile[2])
        self.assertIn("media-grid__tile--tall", tall_tile[2])
        self.assertIn(tall_tile[0], (51, 52))  # 90 x 2800 scaled to 1600 on the long side
        self.assertEqual(tall_tile[1], 1600)
        self.assertIn("media-grid__tile--small", tiny_tile[2])
        self.assertEqual(tiny_tile[:2], (8, 8))

    def test_list_card_shows_one_thumbnail_and_a_count_for_the_rest(self):
        self.thread_with((600, 400), (600, 400), (600, 400))
        page = self.client.get(reverse("community:home"))
        self.assertContains(page, "thread-card__thumb")
        self.assertContains(page, "+2")
        self.assertContains(page, 'loading="lazy"')

    def test_replies_show_their_own_grid(self):
        reply = services.create_reply(self.ann, self.thread, body="", images=[_clean(), _clean(name="b.png")])
        page = self.client.get(self.thread.get_absolute_url())
        self.assertContains(page, "media-grid--2")
        self.assertContains(page, f'id="r{reply.pk}"')

    def test_removed_images_are_not_linked(self):
        thread = self.thread_with((300, 200))
        url = thread.images.get().image.url
        self.assertContains(self.client.get(thread.get_absolute_url()), url)
        self.assertEqual(self.act(self.mira, thread, "remove_thread").status_code, 302)
        self.client.logout()
        self.assertEqual(self.client.get(thread.get_absolute_url()).status_code, 404)


class LightboxMarkupTests(CommunityTestCase):
    def test_one_dialog_with_controls_and_scripts_on_every_page(self):
        page = self.client.get(self.thread.get_absolute_url())
        html = page.content.decode()
        self.assertEqual(html.count("<dialog"), 1)
        for hook in ("data-lightbox-img", "data-lightbox-prev", "data-lightbox-next", "data-lightbox-close",
                     "data-lightbox-count"):
            self.assertIn(hook, html)
        for script in ("js/lightbox.js", "js/composer.js", "js/community.js"):
            self.assertIn(script, html)
            self.assertTrue(finders.find(script), script)
        self.assertRegex(html, r'<dialog class="lightbox" data-lightbox aria-label="[^"]+"')

    def test_tiles_are_plain_links_to_the_display_copy_so_it_works_without_js(self):
        thread = services.create_thread(self.bob, self.board, "Pictures", "x", [_clean(), _clean(name="b.png")])
        html = self.client.get(thread.get_absolute_url()).content.decode()
        for image in thread.images.all():
            self.assertIn(f'href="{image.image.url}" data-full="{image.image.url}"', html)

    def test_buttons_have_labels_in_the_page_language(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "de"
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        self.assertIn("Vorheriges Bild", html)
        self.assertIn("Nächstes Bild", html)


class StickerUITests(CommunityTestCase):
    def test_picker_lists_every_sticker_for_people_who_can_reply(self):
        self.client.force_login(self.bob)
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        self.assertEqual(len(re.findall(r'<button class="sticker-picker__item"', html)), len(STICKERS))
        self.assertIn("data-picker-search", html)
        self.assertIn("data-picker-recent", html)
        for key in STICKERS:
            self.assertIn(f'data-sticker="{key}"', html)
            self.assertTrue(finders.find(f"stickers/{key}.svg"), key)

    def test_picker_labels_are_searchable_and_translated(self):
        self.client.force_login(self.bob)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "uk"
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        label = re.search(r'data-sticker="rocket" data-label="([^"]+)"', html).group(1)
        self.assertIn("rocket", label)  # the key stays searchable in every language
        with translation.override("uk"):
            self.assertIn(str(STICKERS["rocket"]).lower(), label)

    def test_without_js_a_select_offers_the_same_stickers(self):
        self.client.force_login(self.bob)
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        select = re.search(r'<select name="sticker".*?</select>', html, re.S).group(0)
        self.assertEqual(select.count("<option"), len(STICKERS) + 1)  # + "No sticker"
        self.assertIn("composer__sticker-select", html)

    def test_visitors_and_blocked_people_get_no_composer(self):
        visitor = self.client.get(self.thread.get_absolute_url())
        self.assertNotContains(visitor, "data-picker")
        self.assertContains(visitor, "Sign in to reply and vote.")
        self.ban(self.bob, kind=Sanction.Kind.MUTE)
        self.client.force_login(self.bob)
        muted = self.client.get(self.thread.get_absolute_url())
        self.assertNotContains(muted, "data-picker")
        self.assertNotContains(muted, "data-reply-form")

    def test_sticker_in_a_reply_is_an_image_with_the_translated_label_as_alt(self):
        reply = services.create_reply(self.bob, self.thread, sticker_key="rocket")
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        self.assertRegex(html, rf'(?s)id="r{reply.pk}".*?<img src="[^"]*stickers/rocket\.svg" width="96" height="96" alt="Rocket"')
        # a key that left the manifest renders nothing instead of a broken image
        type(reply).objects.filter(pk=reply.pk).update(sticker_key="not-a-sticker")
        self.assertNotContains(self.client.get(self.thread.get_absolute_url()), "not-a-sticker")

    def test_a_forged_sticker_value_is_refused_by_the_form(self):
        before = self.thread.replies.count()
        for value in ("../../etc/passwd", "rocket.svg", "<svg onload=alert(1)>", "ROCKET"):
            response = self.reply(self.bob, body="x", sticker=value)
            with self.subTest(value=value):
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.thread.replies.count(), before)


class PostFormTests(CommunityTestCase):
    def img_src(self, response):
        policy = response.headers.get("Content-Security-Policy", "")
        return re.search(r"img-src ([^;]*)", policy).group(1)

    def test_only_pages_with_a_composer_allow_blob_previews(self):
        self.client.force_login(self.bob)
        for url in (self.thread.get_absolute_url(), reverse("community:new")):
            with self.subTest(url=url):
                self.assertIn("blob:", self.img_src(self.client.get(url)))
        for url in (reverse("community:home"), reverse("community:notifications"), reverse("community:rules"),
                    "/explore/", reverse("community:thread_edit", args=[self.thread.pk])):
            with self.subTest(url=url):
                response = self.client.get(url)
                if response.status_code == 200:
                    self.assertNotIn("blob:", self.img_src(response))
        self.client.logout()
        self.assertNotIn("blob:", self.img_src(self.client.get(self.thread.get_absolute_url())))

    def test_blob_does_not_widen_any_other_directive(self):
        self.client.force_login(self.bob)
        policy = self.client.get(reverse("community:new")).headers["Content-Security-Policy"]
        self.assertEqual(policy.replace(" blob:", ""), settings.CONTENT_SECURITY_POLICY)
        self.assertNotIn("'unsafe-inline'", policy)

    def test_a_failed_reply_keeps_the_text_and_the_blob_policy(self):
        self.client.force_login(self.bob)
        response = self.client.post(reverse("community:reply", args=[self.thread.pk]), {"body": "x" * (limits.MAX_REPLY_BODY + 1)})
        self.assertEqual(response.status_code, 400)
        self.assertIn("blob:", self.img_src(response))
        self.assertContains(response, "data-composer", status_code=400)

    def test_new_thread_form_has_the_composer_with_four_images_and_a_board_preselect(self):
        self.client.force_login(self.bob)
        page = self.client.get(reverse("community:new"), {"board": "feedback"})
        self.assertContains(page, 'data-max="4"')
        self.assertContains(page, 'enctype="multipart/form-data"')
        self.assertContains(page, "Before you post")
        self.assertNotContains(page, "data-picker-open")  # stickers are for replies only

    def test_reply_form_allows_two_images_and_the_picker(self):
        self.client.force_login(self.bob)
        page = self.client.get(self.thread.get_absolute_url())
        self.assertContains(page, 'data-max="2"')
        self.assertContains(page, "data-picker-open")

    def test_reply_to_query_moves_the_form_without_js(self):
        reply = services.create_reply(self.ann, self.thread, body="Which record exactly?")
        self.client.force_login(self.bob)
        page = self.client.get(self.thread.get_absolute_url(), {"reply_to": reply.pk})
        self.assertContains(page, f'name="parent" value="{reply.pk}"')
        self.assertContains(page, "Reply to @ann")
        other = make_thread(self.ann, title="Another thread")
        stranger = services.create_reply(self.ann, other, body="Elsewhere.")
        forged = self.client.get(self.thread.get_absolute_url(), {"reply_to": stranger.pk})
        self.assertContains(forged, 'name="parent" value=""')  # a reply from another thread is ignored


class VisibilityTests(CommunityTestCase):
    def test_vote_control_is_a_form_for_others_and_static_for_the_author(self):
        reply = services.create_reply(self.bob, self.thread, body="Mine.")
        self.client.force_login(self.bob)
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        self.assertIn(f'action="{reverse("community:vote_thread", args=[self.thread.pk])}"', html)
        self.assertNotIn(f'action="{reverse("community:vote_reply", args=[reply.pk])}"', html)  # not on your own reply
        self.client.force_login(self.ann)
        own = self.client.get(self.thread.get_absolute_url()).content.decode()
        self.assertNotIn(f'action="{reverse("community:vote_thread", args=[self.thread.pk])}"', own)
        self.assertIn("vote--static", own)

    def test_voted_state_is_pressed_in_lists_and_threads(self):
        self.client.force_login(self.bob)
        self.assertEqual(self.vote(self.bob, self.thread).status_code, 302)
        for url in (reverse("community:home"), self.thread.get_absolute_url()):
            self.assertContains(self.client.get(url), 'aria-pressed="true"')

    def test_anonymous_sees_scores_but_no_buttons(self):
        page = self.client.get(self.thread.get_absolute_url())
        self.assertNotContains(page, "data-vote-form")
        self.assertContains(page, "vote--static")

    def test_report_and_edit_links_follow_ownership(self):
        reply = services.create_reply(self.bob, self.thread, body="A reply.")
        self.client.force_login(self.ann)
        page = self.client.get(self.thread.get_absolute_url())
        self.assertContains(page, reverse("community:thread_edit", args=[self.thread.pk]))
        self.assertNotContains(page, reverse("moderation:report_thread", args=[self.thread.pk]))
        self.assertContains(page, reverse("moderation:report_reply", args=[reply.pk]))
        self.assertNotContains(page, reverse("community:reply_edit", args=[reply.pk]))
        self.client.force_login(self.bob)
        page = self.client.get(self.thread.get_absolute_url())
        self.assertContains(page, reverse("moderation:report_thread", args=[self.thread.pk]))
        self.assertNotContains(page, reverse("community:thread_edit", args=[self.thread.pk]))

    def test_moderate_menu_only_for_moderators(self):
        self.client.force_login(self.bob)
        self.assertNotContains(self.client.get(self.thread.get_absolute_url()), reverse("moderation:act_thread", args=[self.thread.pk]))
        self.client.force_login(self.mira)
        self.assertContains(self.client.get(self.thread.get_absolute_url()), reverse("moderation:act_thread", args=[self.thread.pk]))

    def test_locked_thread_shows_the_reason_and_the_form_only_to_moderators(self):
        self.assertEqual(self.act(self.mira, self.thread, "lock_thread").status_code, 302)
        self.client.force_login(self.bob)
        page = self.client.get(self.thread.get_absolute_url())
        self.assertContains(page, "This thread is locked.")
        self.assertContains(page, REASON)
        self.assertNotContains(page, "data-reply-form")
        self.client.force_login(self.mira)
        self.assertContains(self.client.get(self.thread.get_absolute_url()), "data-reply-form")

    def test_removed_thread_is_a_404_for_others_and_shows_the_reason_to_the_author(self):
        self.assertEqual(self.act(self.mira, self.thread, "remove_thread").status_code, 302)
        self.client.logout()
        self.assertEqual(self.client.get(self.thread.get_absolute_url()).status_code, 404)
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(self.thread.get_absolute_url()).status_code, 404)
        self.client.force_login(self.ann)
        page = self.client.get(self.thread.get_absolute_url())
        self.assertContains(page, REASON)
        self.assertContains(page, "noindex")

    def test_deleted_account_has_no_name_picture_or_link(self):
        reply = services.create_reply(self.bob, self.thread, body="Bob was here.")
        self.bob.delete()
        page = self.client.get(self.thread.get_absolute_url())
        self.assertContains(page, "[deleted]")
        self.assertNotContains(page, "@bob")
        self.assertNotContains(page, "/u/bob/")
        self.assertContains(page, f'id="r{reply.pk}"')

    def test_thread_author_is_marked_in_replies(self):
        services.create_reply(self.ann, self.thread, body="Update from the author.")
        services.create_reply(self.bob, self.thread, body="From someone else.")
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        self.assertEqual(html.count("thread-chip\">Author"), 1)

    def test_page_meta_for_search_engines(self):
        self.assertNotContains(self.client.get(reverse("community:home")), "noindex")
        self.assertContains(self.client.get(reverse("community:home"), {"sort": "new"}), "noindex")
        self.assertNotContains(self.client.get(self.thread.get_absolute_url()), "noindex")
        self.assertContains(self.client.get(self.thread.get_absolute_url(), {"sort": "new"}), "noindex")


class ReplyTreeMarkupTests(CommunityTestCase):
    def test_node_counts_every_level_below_it(self):
        top = services.create_reply(self.bob, self.thread, body="Top.")
        child = services.create_reply(self.ann, self.thread, parent=top, body="Child.")
        services.create_reply(self.bob, self.thread, parent=child, body="Grandchild.")
        services.create_reply(self.mira, self.thread, parent=top, body="Second child.")
        nodes = self.client.get(self.thread.get_absolute_url()).context["nodes"]
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].below, 3)

    def test_collapse_button_points_at_an_existing_branch_and_is_hidden_until_js(self):
        top = services.create_reply(self.bob, self.thread, body="Top.")
        services.create_reply(self.ann, self.thread, parent=top, body="Child.")
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        button = re.search(r'<button class="reply__collapse" type="button" hidden data-collapse aria-expanded="true" aria-controls="([^"]+)"', html)
        self.assertIsNotNone(button)
        self.assertIn(f'id="{button.group(1)}"', html)
        self.assertIn("Hide 1 reply", html)

    def test_permalink_ids_exist_for_every_reply(self):
        top = services.create_reply(self.bob, self.thread, body="Top.")
        child = services.create_reply(self.ann, self.thread, parent=top, body="Child.")
        html = self.client.get(self.thread.get_absolute_url()).content.decode()
        for reply in (top, child):
            self.assertIn(f'id="r{reply.pk}"', html)
            self.assertIn(f'href="#r{reply.pk}"', html)
        self.assertEqual(child.get_absolute_url(), f"{self.thread.get_absolute_url()}#r{child.pk}")

    def test_plain_post_reply_still_works_and_redirects_to_the_reply(self):
        response = self.reply(self.bob, body="Plain form, no JS.")
        self.assertEqual(response.status_code, 302)
        self.assertIn("#r", response["Location"])


class CommunityTranslationTests(CommunityTestCase):
    def test_pages_render_in_every_language_without_untranslated_markers(self):
        self.client.force_login(self.bob)
        services.create_reply(self.ann, self.thread, body="A reply.")
        for code, _name in settings.LANGUAGES:
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = code
            for url in (reverse("community:home"), self.thread.get_absolute_url(), reverse("community:new")):
                with self.subTest(language=code, url=url):
                    html = self.client.get(url).content.decode()
                    html = re.sub(r'data-to="[^"]*"', "", html)  # the one placeholder the script fills on purpose
                    self.assertNotIn("%(", html)  # a placeholder that was never filled
                    self.assertNotIn("%%(", html)

    def test_reply_to_template_keeps_its_placeholder_for_the_script(self):
        self.client.force_login(self.bob)
        for code in ("en", "uk", "de", "pl", "es", "fr", "pt-br"):
            self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = code
            html = self.client.get(self.thread.get_absolute_url()).content.decode()
            with self.subTest(language=code):
                self.assertRegex(html, r'data-to="[^"]*%\(name\)s[^"]*"')
