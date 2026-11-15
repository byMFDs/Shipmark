"""Every language is complete: catalogs hold every string in the code, are compiled, and the main pages show
no English UI text in another language.

Why these exist: during the redesign `makemessages` was run only for `uk`, so pl/de/es/fr/pt-br never got the new
strings. The old check looked only for empty entries in the .po files, and a string that is missing altogether
is not empty, so it passed while half of the site fell back to English.
"""
import gettext as gnu_gettext
import os
import re
import shutil
import tempfile
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import translation

from projects.models import BuildLogEntry, Project
from projects.tests import make_project, make_user

LOCALE_DIR = Path(settings.LOCALE_PATHS[0])
CODES = [code for code, _name in settings.LANGUAGES if code != "en"]


def po_entries(path):
    """{msgid: [msgstr, ...]} of a .po file (plural forms as several strings). Header and obsolete entries skipped."""
    entries = {}
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
        fields, current = {}, None
        for line in block.splitlines():
            match = re.match(r'^(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?) "(.*)"$', line)
            if match:
                current = match.group(1)
                fields[current] = match.group(2)
            elif line.startswith('"') and current:
                fields[current] += line[1:-1]
        if fields.get("msgid"):
            key = fields["msgid"].encode("latin-1", "backslashreplace").decode("unicode_escape")
            if "msgctxt" in fields:
                key = f"{fields['msgctxt']}\x04{key}"
            entries[key] = [v for k, v in fields.items() if k.startswith("msgstr")]
    return entries


def catalog_dirs():
    return sorted(p for p in LOCALE_DIR.iterdir() if (p / "LC_MESSAGES" / "django.po").is_file())


class CatalogTests(SimpleTestCase):
    """Повнота каталогів перекладів."""
    def test_no_empty_or_fuzzy_translations(self):
        for locale_dir in catalog_dirs():
            text = (locale_dir / "LC_MESSAGES" / "django.po").read_text(encoding="utf-8")
            body = text.split("\n\n", 1)[1]  # after the header
            with self.subTest(locale=locale_dir.name):
                self.assertNotRegex(body, r"#,.*\bfuzzy\b", "fuzzy entries are not used by Django")
                for msgid, strings in po_entries(locale_dir / "LC_MESSAGES" / "django.po").items():
                    self.assertTrue(all(strings), f"empty translation: {msgid!r}")

    def test_every_catalog_has_the_same_strings(self):
        """A language that missed a makemessages run has fewer strings than the others."""
        sets = {d.name: set(po_entries(d / "LC_MESSAGES" / "django.po")) for d in catalog_dirs()}
        reference = set().union(*sets.values())
        for name, ids in sets.items():
            with self.subTest(locale=name):
                self.assertEqual(sorted(reference - ids), [], "missing: run makemessages for every language")

    def test_compiled_catalogs_match_the_po_files(self):
        """django.mo is what Django reads; a .po edit without compilemessages changes nothing on the site."""
        for locale_dir in catalog_dirs():
            mo_path = locale_dir / "LC_MESSAGES" / "django.mo"
            with self.subTest(locale=locale_dir.name):
                self.assertTrue(mo_path.is_file(), "run compilemessages")
                with mo_path.open("rb") as fh:
                    mo = gnu_gettext.GNUTranslations(fh)
                for msgid, strings in po_entries(locale_dir / "LC_MESSAGES" / "django.po").items():
                    if "\x04" in msgid or len(strings) != 1:
                        continue
                    want = strings[0].encode("latin-1", "backslashreplace").decode("unicode_escape")
                    self.assertEqual(mo.gettext(msgid), want, f"stale .mo for {msgid!r}: run compilemessages")

    def test_every_string_in_the_code_is_in_the_catalogs(self):
        """Extract the strings from the code into a temporary folder and compare (needs GNU gettext)."""
        if not shutil.which("xgettext"):
            self.skipTest("GNU gettext is not installed")
        # makemessages writes next to the code it scans, so it runs in a temporary folder of links to the code:
        # the real locale/ folder is never touched.
        tmp = Path(tempfile.mkdtemp())
        cwd = os.getcwd()
        try:
            for item in Path(settings.BASE_DIR).iterdir():
                if item.is_dir() and (item.name == "templates" or (item / "apps.py").is_file() or item.name == "config"):
                    (tmp / item.name).symlink_to(item, target_is_directory=True)
            (tmp / "locale").mkdir()
            os.chdir(tmp)
            with override_settings(LOCALE_PATHS=[tmp / "locale"]):
                call_command("makemessages", locale=["xx"], symlinks=True, verbosity=0, no_obsolete=True)
            extracted = set(po_entries(tmp / "locale" / "xx" / "LC_MESSAGES" / "django.po"))
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertGreater(len(extracted), 100)
        for locale_dir in catalog_dirs():
            with self.subTest(locale=locale_dir.name):
                missing = extracted - set(po_entries(locale_dir / "LC_MESSAGES" / "django.po"))
                self.assertEqual(sorted(missing), [], "run makemessages for every language and translate")


# ---------- Rendered pages ----------

class _Text(HTMLParser):
    """Видимий текст сторінки для перевірки перекладу.

    Visible text nodes and text attributes, without scripts, styles, code and inline SVG."""

    SKIP = {"script", "style", "code", "pre", "svg", "textarea", "template"}
    ATTRS = {"aria-label", "title", "alt", "placeholder", "data-copied", "data-error", "data-busy-label",
             "data-label-on", "data-label-off"}

    def __init__(self):
        super().__init__()
        self.depth, self.out = 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.depth += 1
        for name, value in attrs:
            if value and (name in self.ATTRS or (name == "value" and tag in ("button", "input") and dict(attrs).get("type") in ("submit", "button"))):
                self.out.append(value)

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if not self.depth and data.strip():
            self.out.append(data)


def texts(html):
    # Long pages from content/<lang>/*.md are checked by test_languages.py, not here.
    html = re.sub(r'<article class="prose doc".*?</article>', " ", html, flags=re.S)
    parser = _Text()
    parser.feed(html)
    return {re.sub(r"\s+", " ", t).strip() for t in parser.out}


def english_ui_strings(code):
    """Patterns for every English UI string, except those this language deliberately keeps (Live, GitHub, ...).

    Read from the .po files, not from gettext(): a string missing from a stale .mo would look "the same in both".
    """
    folder = translation.to_locale(code)
    own = po_entries(LOCALE_DIR / folder / "LC_MESSAGES" / "django.po")
    patterns = []
    for po in catalog_dirs():
        for msgid in po_entries(po / "LC_MESSAGES" / "django.po"):
            if "\x04" in msgid or "<" in msgid or not re.search(r"[A-Za-z]{3}", msgid):
                continue
            if own.get(msgid, [""])[0] == msgid:
                continue  # kept in English on purpose (hallmark names, GitHub, Markdown...)
            text = re.sub(r"\s+", " ", msgid.replace("%%", "%")).strip()
            regex = re.escape(text)
            regex = re.sub(r"%\\\(\w+\\\)[sd]", ".+?", regex)
            patterns.append((msgid, re.compile(f"^{regex}$")))
    return list({m: (m, rx) for m, rx in patterns}.values())


@override_settings(DEBUG=True)  # for the /_dev/errors/ previews
class RenderedPagesTests(TestCase):
    """На сторінках кожною мовою не лишилось англійського тексту.

    The main pages, signed out and signed in, in every language: no English UI text left."""

    @classmethod
    def setUpTestData(cls):
        cls.ann = make_user("ann", display_name="Ann", terms_version_accepted=settings.TERMS_VERSION)
        cls.bob = make_user("bob", terms_version_accepted=settings.TERMS_VERSION)
        cls.project = make_project(cls.ann, name="Tallyhook", live_url="https://tallyhook.test")
        make_project(cls.ann, name="Draftbox", status=Project.Status.DRAFT)
        BuildLogEntry.objects.create(project=cls.project, text="v2 out", kind=BuildLogEntry.Kind.UPDATE)
        from datetime import timedelta

        from django.utils import timezone

        from community import services
        from community.models import Board, Thread

        User = type(cls.ann)
        User.objects.filter(pk__in=[cls.ann.pk, cls.bob.pk]).update(date_joined=timezone.now() - timedelta(days=30))
        cls.thread = Thread.objects.create(board=Board.objects.get(slug="help"), author=cls.ann, title="Tallyhook DNS",
                                           body="TXT record", pinned=True)
        services.create_reply(cls.bob, cls.thread, body="TTL")

    def pages(self):
        p = self.project
        public = ["/", "/explore/", "/feed/", "/u/ann/", p.get_absolute_url(), "/about/", "/how-proof-works/",
                  "/legal/privacy/", "/login/"] + [f"/_dev/errors/{c}/" for c in ("400", "403", "404", "500", "csrf")]
        owner = ["/feed/", "/u/ann/", p.get_absolute_url(), "/new/", f"{p.get_absolute_url()}edit/",
                 f"{p.get_absolute_url()}delete/", "/settings/", "/settings/delete/"]
        t = self.thread
        public += ["/community/", "/community/b/help/", t.get_absolute_url()]
        owner += [t.get_absolute_url(), "/community/new/", f"/community/t/{t.pk}/edit/", f"/community/t/{t.pk}/delete/",
                  "/community/notifications/"]
        other = [f"/report/project/ann/{p.slug}/", t.get_absolute_url(), f"/report/thread/{t.pk}/"]
        return [(None, url) for url in public] + [(self.ann, url) for url in owner] + [(self.bob, url) for url in other]

    def test_no_english_ui_text_in_other_languages(self):
        for code in CODES:
            patterns = english_ui_strings(code)
            for user, url in self.pages():
                with self.subTest(code=code, url=url, user=user and user.username):
                    if user:
                        self.client.force_login(user)
                    else:
                        self.client.logout()
                    response = self.client.get(url, headers={"Accept-Language": code})
                    self.assertIn(response.status_code, (200, 404), url)
                    html = response.content.decode()
                    self.assertIn(f'<html lang="{code}"', html)
                    leftovers = sorted({msgid for text in texts(html) for msgid, rx in patterns if rx.match(text)})
                    self.assertEqual(leftovers, [], f"English UI text on {url} in {code}")

    def test_form_labels_are_translated(self):
        """A form field without an explicit label gets Django's English name for it ("Live url"), which is not in any
        catalog, so the check above cannot see it. Ukrainian is the canary: a Latin-only label that reads the same as
        in English was never translated (except names we keep on purpose: GitHub, Markdown, ...)."""
        kept = {msgid for msgid, strings in po_entries(LOCALE_DIR / "uk" / "LC_MESSAGES" / "django.po").items()
                if strings[0] == msgid}
        from projects.models import Tool
        kept |= set(Tool.objects.values_list("name", flat=True))  # data (built-with choices), not UI text
        kept |= set(Project.objects.values_list("name", flat=True))  # pinned-project choices

        def labels(html):
            found = set()
            for body in re.findall(r"<label\b[^>]*>(.*?)</label>", html, re.S):
                text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
                if text:
                    found.add(text)
            return found

        for user, url in self.pages() + [(None, "/support/"), (self.ann, "/support/")]:
            with self.subTest(url=url, user=user and user.username):
                if user:
                    self.client.force_login(user)
                else:
                    self.client.logout()
                english = labels(self.client.get(url, headers={"Accept-Language": "en"}).content.decode())
                ukrainian = labels(self.client.get(url, headers={"Accept-Language": "uk"}).content.decode())
                same = sorted(text for text in english & ukrainian
                              if re.search(r"[A-Za-z]{3}", text) and text not in kept)
                self.assertEqual(same, [], f"labels not translated on {url}")
