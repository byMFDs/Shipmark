# Privacy policy

> **Draft**, last updated 11 November 2026. This text has not been reviewed by a lawyer yet.

This page explains what {{ site_name }} stores about you, why, for how long, and what you can do about it. It describes what the site actually does.

## Who is responsible {#controller}

{{ site_name }} is run by {{ legal_owner_name }}, who is responsible for your data (the "controller").
Questions or requests: [{{ contact_email }}](mailto:{{ contact_email }}).

## What we store and why {#data}

**When you sign in with GitHub.** We receive from GitHub your account id, login, name, bio, avatar link and the other public fields of your GitHub profile, plus the email addresses on your GitHub account. We ask GitHub only for `read:user` and `user:email`: we never get access to your repositories, private or public, through your account. We do not keep your GitHub access token after sign-in. We need this to create your account and to recognise you next time (performance of our agreement with you). Your GitHub login is refreshed at every sign-in, so your profile always links to your current GitHub account.

**Your profile.** Username, display name, bio, website and language. The name and bio start as your GitHub values; you can change them in Settings. Your username, display name, bio, website, GitHub login and the month you joined are **public**.

**Your email address.** Stored with your account and visible only to our staff. It is never shown on the site. The site does not send email; we would use the address only to contact you about your account or a report.

**Your projects.** Everything you enter: name, tagline, description, links, tags, the AI tools you say you used (shown as self-declared), screenshots and build log entries. Published projects are public; drafts are visible only to you and staff. Screenshots are re-encoded when you upload them, which removes hidden metadata such as camera details or GPS location.

**Proof checks.** To award hallmarks we check facts ourselves (our legitimate interest in showing proof that can be trusted):

- *Repo owner:* we ask GitHub's public API about the repository you link and store its id, its owner's account id, whether you own it, its creation date and its Website field, the first commit of its history (id and date), your commit count, your first and last commit dates, the number of weeks with your commits, and the state of a manual review when one is needed. We check it again every week. GitHub's list of other contributors is read during the check and not stored. If you use the verification file for an organisation repository, we also store whether it was found.
- *Live:* we look up the DNS records of your project's domain or fetch its page to find your verification token.
- *Steady:* we request your project's address up to every few hours and store whether it answered and how fast. These checks are kept for **90 days**.

The results are shown on your public project page.

**Follows and likes.** We store whom you follow and which projects you like. Others see only the counts, not the lists.

**Reports.** If you report a project or a profile, we store the reason and the details you write. Only staff see reports. The person you report is not told who reported them.

**Terms acceptance.** We store which version of the Terms you accepted and when.

**Audit log.** We keep an internal record of hallmark changes, moderation actions and account deletions, so that decisions can be checked later. Only staff can see it.

**IP addresses and logs.** The application does not store your IP address, and its own logs do not contain it. For each page request the logs record only the method, the page address (without anything after a `?`), the response status, size and time taken, plus errors. They hold no browser details. Page addresses include usernames (`/u/<username>/`), so a log line can show which profile was opened, but not by whom.

**Error log.** When something fails, the application writes a short record to an error file on our server: the time, a random reference number (the one shown on the error page), the request method, the page address without anything after a `?` and with usernames replaced by `[user]`, the response status, which part of the code failed, and the technical error message with email addresses, IP addresses and anything that looks like a password or key removed. Pages that were not found are written to a separate file, each address at most once a minute. These files never contain your IP address, browser details, cookies, what you typed into a form, your email address or your username. Each file is limited to 5 MB plus 5 older copies; the oldest is deleted when the limit is reached.

> **TODO before launch:** the web server in front of the application keeps its own access log, which by default includes IP addresses. What it records and how long it keeps it (and how long the application logs are kept) has not been decided yet. Fill this in, or switch IP logging off, before this page goes public.

**Abuse protection.** To limit abuse we count some actions (for example, likes per hour) in the site's database. Each counter is a number tied to your account or to a project, without any IP address, and applies for at most 24 hours. After that it is no longer used, but the row may stay in the database until it is cleaned up.

**Analytics and tracking.** There are none: no analytics, no advertising and no tracking scripts. Fonts are served from our own server.

**Backups.** Every day we back up the database and the uploaded screenshots and keep each backup for 14 days. If you delete your account, your data stays in those backups until the last one that contains it is replaced, up to 14 days later.

## How long we keep it {#retention}

- Your account, profile, projects, follows and likes: until you delete them or your account.
- Uptime checks: 90 days.
- Sign-in sessions: 2 weeks, or until you sign out.
- Reports you made: kept after they are handled. If you delete your account, they stay without your name.
- Audit log: kept. Entries about a deleted account do not contain the username or email.
- Abuse-protection counters: at most 24 hours.
- Backups: 14 days. A deleted account disappears from them within 14 days.
- Error log files: until they are full (5 MB, plus 5 older copies of 5 MB each), then the oldest entries are deleted.
- Web server and application logs: **TODO**, not decided yet.

## Who else receives data {#recipients}

- **GitHub, Inc.** You sign in on github.com, and our server reads your profile and public repository data from GitHub's API. GitHub's own privacy statement applies to your use of GitHub.
- **The servers of your project.** For the Live and Steady checks our server contacts your domain's DNS and your project's address. They see our server, not you.
- **Our hosting provider**, which runs the server and the database for us.

We do not sell your data and do not share it for advertising.

## Your rights {#rights}

- **See and download your data:** Settings → "Download my data" gives you a JSON file with your profile, GitHub details, projects, build log, likes, follows and reports you made.
- **Correct it:** edit your profile in Settings and your projects on their pages.
- **Delete it:** Settings → "Delete account". This removes your profile and all your projects, likes and follows at once and cannot be undone. Your username becomes free.
- **Object or complain:** write to [{{ contact_email }}](mailto:{{ contact_email }}). If you live in the EU, UK or Ukraine, you can also complain to your data protection authority.

## Cookies {#cookies}

We use only the cookies the site needs to work. See the [cookie policy](/legal/cookies/).

## Changes {#changes}

If this policy changes, we update the date at the top. If the change is important, we will ask you to accept the updated Terms on your next visit.
