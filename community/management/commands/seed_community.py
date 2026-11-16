"""Демо-вміст спільноти для розробки (лише з DEBUG).

Demo content for the community, for looking at the pages in development. DEBUG only.

    python manage.py seed_community           # remove the previous demo content, then create it again
    python manage.py seed_community --clear   # only remove it

Demo people are accounts named `demo-…` with an `@example.invalid` address and an unusable password (nobody can
sign in as them). Their threads, replies, images and upvotes are made through community.services, the same code the
pages use, then spread over the last two weeks so Hot, New and Top differ. Images are drawn here with Pillow and go
through the normal image pipeline. Refuses to run unless DEBUG is on and the settings are not production ones (see `refuse_in_production`), so it
never touches a production database. Demo accounts are not counted in the "people joined" number and are not listed
in the sitemap or in people search.
"""
import io
import os
import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from community import services
from community.images import clean_upload
from community.models import Board, Reply, Thread

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


def picture(width, height, seed):
    """Проста абстрактна картинка для демо-дописів.

    A simple abstract picture: paper background, hairline frame, a few flat blocks in the brand colours."""
    rng = random.Random(seed)
    image = Image.new("RGB", (width, height), "#F4F3EE")
    draw = ImageDraw.Draw(image)
    colours = ["#BD4B27", "#2B5A3F", "#E3EBDA", "#20251F", "#D9D8D0"]
    for _ in range(6):
        x0, y0 = rng.randrange(0, width), rng.randrange(0, height)
        x1 = min(width, x0 + rng.randrange(width // 6 + 1, width // 2 + 2))
        y1 = min(height, y0 + rng.randrange(height // 6 + 1, height // 2 + 2))
        draw.rectangle([x0, y0, x1, y1], fill=rng.choice(colours))
    draw.rectangle([0, 0, width - 1, height - 1], outline="#868A80", width=max(1, min(width, height) // 200))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return clean_upload(SimpleUploadedFile(f"demo-{seed}.png", buffer.getvalue(), content_type="image/png"))


def clear():
    """Видаляє демо-людей і все, що вони написали.

    Removes the demo people and everything they wrote. Returns how many people were removed."""
    people = get_user_model().objects.filter(username__startswith=PREFIX, email__endswith=DOMAIN)
    Thread.objects.filter(author__in=people).delete()  # replies, votes and images go with them (files too)
    Reply.objects.filter(author__in=people).delete()
    count = people.count()
    people.delete()
    return count


def seed():
    """Створює демо-вміст; повертає кількість тем і відповідей.

    Creates the demo content. Returns (threads, replies)."""
    User = get_user_model()
    now = timezone.now()
    people = []
    for name in PEOPLE:
        user = User.objects.create_user(username=name, email=f"{name}{DOMAIN}", date_joined=now - timedelta(days=90))
        user.set_unusable_password()
        user.display_name = name.removeprefix(PREFIX).title()
        user.save()
        people.append(user)
    rng = random.Random(7)
    threads = replies = 0
    for index, (slug, author, title, body, sizes, answers) in enumerate(THREADS):
        board = Board.objects.get(slug=slug)
        images = [picture(w, h, f"{index}-{n}") for n, (w, h) in enumerate(sizes)]
        thread = services.create_thread(people[author], board, title, body, images)
        threads += 1
        started = now - timedelta(days=rng.randrange(0, 14), hours=rng.randrange(0, 23))
        made = [thread]

        def add(items, parent, at):
            nonlocal replies
            for who, text, shapes, children in items:
                at = at + timedelta(minutes=rng.randrange(5, 240))
                pictures = [picture(w, h, f"{index}-r{replies}-{n}") for n, (w, h) in enumerate(shapes)]
                reply = services.create_reply(people[who], thread, parent=parent, body=text, images=pictures)
                Reply.objects.filter(pk=reply.pk).update(created_at=min(at, now))
                replies += 1
                made.append(reply)
                at = add(children, reply, at)
            return at

        last = add(answers, None, started)
        Thread.objects.filter(pk=thread.pk).update(created_at=started, last_activity_at=min(last, now))
        for target in made:  # a few upvotes from the others, never on their own post
            voters = [p for p in people if p.pk != target.author_id]
            for voter in rng.sample(voters, rng.randrange(0, len(voters))):
                services.set_vote(voter, target, True)
    return threads, replies


def refuse_in_production():
    """Зупиняє команду поза розробкою.

    Two independent checks: DEBUG must be on, and the settings must not be the production ones (production needs
    an https SITE_URL and the prod settings module). Either one failing is enough to refuse."""
    if not settings.DEBUG:
        raise CommandError("seed_community runs only with DEBUG on (development).")
    if os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith(".prod") or settings.SITE_URL.startswith("https://"):
        raise CommandError("seed_community refuses to run with production settings.")


class Command(BaseCommand):
    """Команда seed_community."""
    help = "Create demo community content (DEBUG only). Removes the previous demo content first."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Only remove the demo content.")

    def handle(self, *args, **options):
        """Прибирає старий демо-вміст і створює новий (лише з DEBUG)."""
        refuse_in_production()
        with transaction.atomic():
            removed = clear()
            if options["clear"]:
                self.stdout.write(f"Removed {removed} demo people and their posts.")
                return
            threads, replies = seed()
        self.stdout.write(self.style.SUCCESS(
            f"Created {len(PEOPLE)} demo people, {threads} threads and {replies} replies. "
            "Run `python manage.py post_welcome` for the pinned welcome thread."))
