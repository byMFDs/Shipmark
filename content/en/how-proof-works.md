# How proof works

A project here can earn three hallmarks. Each one is a fact we check ourselves, not something the author types in. Hallmarks are worked out again every time a page is shown, from the latest checks, so a mark that no longer holds disappears.

## Authored {#authored}

**What it means:** the person who posted the project wrote the code, or a real part of it.

**How it is checked:** the author links a public GitHub repository and presses "Check repository". We ask GitHub's public API about it. The mark is earned when either:

- the repository belongs to the author's personal GitHub account and is not a fork, or
- GitHub counts at least 10 commits from the author's account in the repository's contributor list.

Accounts are compared by GitHub's numeric account id, so renaming a GitHub account does not matter. We only read public data: signing in never gives us access to private repositories.

**How it can be lost:** a later check finds the repository deleted, private, moved or no longer authored by the account, or the author links a different repository to the project. One repository can be linked to only one project.

## Live {#live}

**What it means:** the author controls the domain the project runs on.

**How it is checked:** the author adds a token that we generate for this project and this domain, in one of two ways:

- a DNS TXT record on the domain, or
- a meta tag on the homepage, which must load publicly (no login), answer 200 OK and stay under 512 KB.

`www.example.com` and `example.com` count as the same domain. A domain can be verified for only one project at a time. Tokens are random and never reused.

**How it is re-checked:** once a day we re-check every domain that has not been confirmed in the last 30 days. The mark holds only while the domain was confirmed in the last 35 days.

**How it can be lost:**

- the token is gone from DNS or from the homepage: the mark is removed at once;
- the site or DNS does not answer: we try again on the next run, but after 35 days without a confirmation the mark is gone;
- the author changes the live URL to another domain.

Every time Live is earned or removed, the change is recorded in our internal log.

## Steady {#steady}

**What it means:** the project stays up, not just on launch day.

**How it is checked:** while a project has Live, we request its live URL about every 3 hours. A check succeeds when the site answers with an HTTP status below 400 within 5 seconds. The mark is earned when, over the last 30 days:

- there were at least 40 checks, and
- at least 95% of them succeeded.

The project page shows the uptime percentage and a 30-day strip. Results are kept for 90 days.

**How it can be lost:** uptime falls below 95%, or the project loses Live. Steady always requires Live.

## What is self-declared {#self-declared}

These parts of a project are written by the author and **not** checked by us:

- name, tagline, description and screenshots;
- tags and the launch date;
- "Built with", the AI tools the author says they used. It is always labeled "self-declared".

Hallmarks only say what they say. Authored is about the code, Live about the domain, Steady about uptime. None of them is a review of the product.
