# About {{ site_name }}

{{ site_name }} is a public place where people who build with AI tools show the work they actually shipped. Instead of claims, each project carries proof marks that we check ourselves.

## The problem {#problem}

Saying "I shipped it" costs nothing. A screenshot, a launch post or a line in a CV can describe anything, and from the outside nobody can tell whether the product exists, who controls it, or whether it still runs a month later.

GitHub shows code. LinkedIn shows claims. {{ site_name }} tries to show outcomes: a project, the facts we could check about it, and what its builder did next. The project is the main thing here; a profile is just the collection of someone's projects.

## How proof works {#proof}

A project can earn three hallmarks. Each one is a fact our server checks, and each one disappears when the fact stops being true.

- **Repo owner.** The project links a public GitHub repository. We ask GitHub's public API whether it belongs to the author's personal GitHub account and is not a fork; for organisation and team repositories, the author adds a file with this project's token instead. We check it again every week.
- **Domain verified.** The author proves control of the project's domain with a token we generate: a DNS TXT record or a meta tag on the homepage. We re-check it regularly, and the mark holds only while the domain was confirmed in the last 35 days.
- **Steady.** Once a project has Domain verified, we open its address about every 3 hours. Steady needs at least 40 checks in the last 30 days, and at least 95% of them must get an answer without an error within 5 seconds.

The full rules, including how each mark can be lost, are on [How proof works](/how-proof-works/).

## What we do not verify {#not-verified}

- **Who wrote the code.** {{ site_name }} checks facts it can prove: who owns the linked GitHub repository, who controls the domain, and whether the site answers. It does not and cannot check who wrote the code, or how much of it an AI tool wrote. Commit history and dates are written by the repository owner and can be changed. If you think a project is copied, report it.
- **Whether the project is good.** Hallmarks are not reviews. A Steady project can still be a weak idea, and a great project can have no marks yet.
- **What the author writes.** Name, description, screenshots, tags, launch date and the AI tools under "Built with" come from the author. "Built with" is always labeled self-declared.

## What builders get {#builders}

- A public profile that collects your projects. You sign in with GitHub; we ask only for your public profile and your email addresses, never for access to your repositories.
- A page for each project with its hallmarks, screenshots, a 30-day uptime strip once it has Domain verified, and a build log: short updates and launch notes, in order.
- A badge for your GitHub README or website that shows the hallmarks the project has right now. The project page gives you the code to paste.
- Follows, likes, a feed of new launches and of the people you follow, and an Explore page to find projects by tag, tool or hallmark.
- Control over your data: download all of it as a file, or delete your account, from Settings. No ads, no analytics, no tracking scripts.

## Who is behind it {#who}

{{ site_name }} is built and run by one person, Danylo Rudenko, a solo builder. It is made the way many projects here are made: with AI tools, mostly Claude Code, with one person deciding what gets built and checking the result.

**TODO (Danylo):** confirm this paragraph, and add a sentence about yourself if you want (where you are, why you started).

## What is next {#next}

Planned after the first version, in no fixed order:

- one feed page with a filter, instead of separate tabs;
- avatars and more ways to shape a profile;
- achievements;
- better repository checks, for example for forks, and linking a repository to its domain;
- what "Domain verified" should mean for projects that are not websites: command-line tools, libraries, mobile apps.

**TODO (Danylo):** check that this list still matches your plans before publishing.

## Contact {#contact}

Questions, ideas, a bug, or a project that should not be here: write to [{{ contact_email }}](mailto:{{ contact_email }}). You can also use the "Report" link on any project or profile.

**TODO before launch:** this address comes from `CONTACT_EMAIL` in `config/branding.py` and is still a placeholder.
