"""Архів старого demo-корпусу для перевірки походження; створення вимкнено."""
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

PREFIX = "demo-"
DOMAIN = "@example.invalid"
PEOPLE = ["demo-iryna", "demo-mateo", "demo-sana", "demo-leo", "demo-noor", "demo-tomasz"]

# (board slug, author index, title, body, images [(w, h)], replies)
# A reply is (author index, text, images, [child replies]).
THREADS = [
    ("help", 0, "Domain verification stuck on \"pending\" after adding the TXT record",
     "I added the TXT record two hours ago. `dig TXT` shows it from my machine, but the check still says pending. "
     "Is there a cache on your side, or should I wait for the TTL?",
     [], [
         (1, "Your record probably has quotes inside the value. Copy the token without them.", [], [
             (0, "That was it. The registrar UI added quotes around my quotes. Verified now, thank you!", [], []),
         ]),
         (3, "Also check that the record is on the root domain, not on `www`.", [], []),
     ]),
    ("show", 2, "Shipped: a tiny invoice tool for freelancers, built in a weekend",
     "Built with Claude and plain Django. It makes a PDF invoice from a short form and remembers your clients. "
     "No accounts, data stays in your browser. Feedback on the landing page is very welcome.",
     [(1600, 900), (900, 1600)], [
         (4, "The landing is clear. I would move the price above the screenshot.", [], [
             (2, "Good point, moved it. Conversions are up a bit already.", [], [
                 (4, "Nice!", [], []),
             ]),
         ]),
         (5, "Thanks for sharing.", [], []),
         (1, "How do you handle VAT numbers for EU clients?", [], []),
     ]),
    ("collab", 3, "Looking for a designer for an open-source habit tracker",
     "The app works and has about 300 weekly users, but it looks like a developer made it (I did). "
     "Looking for someone who wants a portfolio piece. Everything stays MIT-licensed.",
     [], [
         (2, "I could help with the onboarding screens. What stack is the front end?", [], [
             (3, "Server-rendered templates and a little vanilla JS. No build step.", [], []),
         ]),
     ]),
    ("feedback", 4, "Idea: show the uptime history on the badge",
     "The Steady mark is great, but a tiny sparkline of the last 30 days on the embeddable badge would say more "
     "than a word. Would you put that on your README?",
     [], [
         (0, "Yes, as long as it stays readable in dark mode on GitHub.", [], []),
         (5, "I prefer the plain badge. Fewer pixels, fewer questions.", [], []),
     ]),
    ("off-topic", 5, "What are you listening to while you build?",
     "Long focus sessions need something without words. Share your playlists.",
     [], [
         (1, "Rain sounds and a lot of coffee.", [], []),
         (2, "Film soundtracks. Anything by the same composer for three hours.", [], []),
         (3, "That sounds good.", [], []),
     ]),
    ("help", 1, "How do you keep API keys out of the code the model writes?",
     "My assistant keeps putting keys straight into the source. I use a `.env` file and tell it so, "
     "but every new session starts again. What works for you?",
     [], [
         (2, "A project notes file the assistant reads at the start of every session. One line: secrets only from env.", [], []),
         (4, "Plus a pre-commit hook that refuses anything that looks like a key.", [], []),
     ]),
    ("show", 0, "My first project with all three hallmarks",
     "Repo owner, Domain verified and now Steady after 30 days without downtime. A small status page for my "
     "side projects. Here is what the dashboard looks like on a phone.",
     [(640, 1280)], [
         (3, "Congratulations, that Steady mark takes patience.", [], []),
     ]),
    ("feedback", 2, "Dark mode contrast on the project page",
     "The muted text on the build log looked a little faint to me on an older laptop screen. "
     "Maybe it is my display. Anyone else?",
     [(1600, 240)], []),
]


def refuse_in_production():
    """Зупиняє команду поза розробкою.

    Two independent checks: DEBUG must be on, and the settings must not be the production ones (production needs
    an https SITE_URL and the prod settings module). Either one failing is enough to refuse."""
    if not settings.DEBUG:
        raise CommandError("seed_community runs only with DEBUG on (development).")
    if os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith(".prod") or settings.SITE_URL.startswith("https://"):
        raise CommandError("seed_community refuses to run with production settings.")


class Command(BaseCommand):
    """Відмовляє у створенні та небезпечному старому очищенні demo-даних."""
    help = "Retired: use community_testdata; legacy-clean validates and backs up old demo data."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true")

    def handle(self, *args, **options):
        refuse_in_production()
        raise CommandError("seed_community is retired. Use community_testdata seed, or community_testdata legacy-clean --dry-run.")
