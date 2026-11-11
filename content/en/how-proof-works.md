# How proof works

A project here can earn three hallmarks. Each one is a fact we check ourselves, not something the author types in. Hallmarks are worked out again every time a page is shown, from the latest checks, so a mark that no longer holds disappears.

## Repo owner {#authored}

**What it means:** the GitHub repository linked to the project belongs to the personal GitHub account of the person who posted it, or (for organisation and team repositories) holds this project's verification file, which needs write access. It does not prove who wrote the code.

**How it is checked:** the author links a public GitHub repository and presses "Check repository". We ask GitHub's public API about it. The mark is earned when the repository belongs to the author's personal GitHub account and is not a fork.

**Organisation and team repositories:** the edit page gives each project its own random token. Add a file named `.shipmark-verify` with only that token in it to the root of the default branch, then check again. Only people who can push to the repository can add it, so it proves write access, not who wrote the code. Forks never count, on either path. The file is checked again every week; if it is gone, the mark is removed.

Accounts and repositories are compared by GitHub's numeric ids, not by names: renaming an account or a repository changes nothing, and a deleted repository that someone recreates under the same name is a different repository. We only read public data: signing in never gives us access to private repositories.

**What else we record:** when the repository was created, its first commit, how many commits the author has and when the first and latest were made, and in how many weeks the author's commits changed code (from GitHub's statistics; bots do not count). The project page lists these facts under "What was checked". The mark waits for a short manual review in three cases: the first commit is much older than the repository, the same first commit belongs to a repository linked to another project here, or GitHub shows no commits by the author. Commit dates are written by whoever makes the commit, so they describe the history; they do not prove it.

**How it is re-checked:** every week we look the repository up again by its id.

**How it can be lost:** the repository is deleted, made private or transferred to another account, or the author links a different repository. One repository can be linked to only one project.

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

The bare address of a hosting service shared by many sites (such as `github.io` or `vercel.app`) cannot be verified. Your own address on it (`yourname.github.io`) can.

## Steady {#steady}

**What it means:** the project stays up, not just on launch day.

**How it is checked:** while a project has Live, we request its live URL about every 3 hours. A check succeeds when the site answers with an HTTP status below 400 within 5 seconds. The mark is earned when, over the last 30 days:

- there were at least 40 checks, and
- at least 95% of them succeeded.

The project page shows the uptime percentage and a 30-day strip. Results are kept for 90 days.

**How it can be lost:** uptime falls below 95%, or the project loses Live. Steady always requires Live.

A check also fails when the site answers only after redirecting to another domain: the answer has to come from the domain that was verified.

## What is self-declared {#self-declared}

These parts of a project are written by the author and **not** checked by us:

- name, tagline, description and screenshots;
- tags and the launch date;
- "Built with", the AI tools the author says they used. It is always labeled "self-declared".

Hallmarks only say what they say. Repo owner is about the repository, Live about the domain, Steady about uptime. None of them is a review of the product.

## What we cannot check {#limits}

{{ site_name }} checks facts it can prove: who owns the linked GitHub repository, who controls the domain, and whether the site answers. It does not and cannot check who wrote the code. Commit history and dates are written by the repository owner and can be changed. If you think a project is copied, report it.
