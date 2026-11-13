# Privacy policy

> **Draft**, last updated 14 November 2026. This text has not been reviewed by a lawyer yet.

This page explains what {{ site_name }} stores about you, why, for how long, and what you can do about it. It describes what the site actually does.

## Who is responsible {#controller}

{{ site_name }} is run by {{ legal_owner_name }}, who is responsible for your data (the "controller").
Questions or requests: [{{ contact_email }}](mailto:{{ contact_email }}).

## What we store and why {#data}

**When you sign in with GitHub.** GitHub sends us:

- your account id, login, name, bio, avatar link and the other public fields of your GitHub profile;
- the email addresses on your GitHub account.

We ask GitHub for only two permissions, `read:user` and `user:email`. Through your account we never get access to your repositories, private or public. We do not keep your GitHub access token after sign-in. We need this data to create your account and to recognise you next time (performance of our agreement with you). Your GitHub login is refreshed at every sign-in, so your profile always links to your current GitHub account.

**Your profile.** Username, display name, headline, About, location, a status (for example "open to work"), up to 10 skills, up to 6 links, up to 3 pinned projects and your language. Everything except the username is optional. The display name and About start as your GitHub name and bio; you can change or remove them in Settings. We also store the address of your GitHub picture, only so that "Use my GitHub picture" can copy it; it is never shown. Your username, display name, headline, About, location, status, skills, links, pinned projects, GitHub login and the month you joined are **public**.

**Profile picture and cover.** You can upload a picture and a wide cover image, or copy your GitHub picture once with "Use my GitHub picture". Every image is re-encoded (the picture to 512×512, the cover to 1500×500), which removes hidden metadata such as GPS location, gets a random file name and is stored on our own server: pages never load your picture from GitHub. Both are **public**. When you remove or replace one, or delete your account, the file is deleted; copies stay in backups for up to 14 days. Without a picture, your initials are shown.

**Your email address.** Stored with your account and visible only to our staff. It is never shown on the site. The site does not send you email (the only email it sends is a notice to our own team about a support message); we would use the address only to contact you about your account, a report or a support message.

**Your projects.** Everything you enter: name, tagline, description, links, tags, the AI tools you say you used (shown as self-declared), screenshots and build log entries. Published projects are public; drafts are visible only to you and staff. Screenshots are re-encoded when you upload them, which removes hidden metadata such as camera details or GPS location.

**Proof checks.** To award hallmarks we check facts ourselves (our legitimate interest in showing proof that can be trusted):

- *Repo owner:* we ask GitHub's public API about the repository you link, and check it again every week. GitHub's list of other contributors is read during the check and not stored. We store:
    - its id, its owner's account id, whether you own it, its creation date and its Website field;
    - the first commit of its history (id and date);
    - your commit count, your first and last commit dates, and the number of weeks with your commits;
    - the state of a manual review, when one is needed;
    - whether the verification file was found, if you use it for an organisation repository.
- *Domain verified:* we look up the DNS records of your project's domain or fetch its page to find your verification token.
- *Steady:* we request your project's address up to every few hours and store whether it answered and how fast. These checks are kept for **90 days**.

The results are shown on your public project page.

**Follows and likes.** We store whom you follow and which projects you like. Others see only the counts, not the lists.

**Reports and moderation.**

- If you report a project, a profile or a build-log update, we store the reason and the details you write.
- Reports are seen by moderators (people with the moderator badge) and staff. To decide, they also see the reported content and the reported person's history on {{ site_name }}: when they joined, earlier sanctions, other reports about them and removed projects. The moderation pages do not show email addresses.
- The person you report is never told who reported them.
- When moderators act, we store the decision and its reason. A removed project keeps its content and the reason (only you, moderators and staff see it). Cleared profile fields (picture and cover, headline and About, or links) are deleted. Mutes and bans are stored with their reason, start and end.
- You see the reason in a notice on the site, which we keep until you delete your account. Decisions about you and these notices are included in "Download my data".
- To appeal a decision, write to [{{ contact_email }}](mailto:{{ contact_email }}).

**Community.** When you post in the community we store:

- your threads: board, title, text, dates, and whether a thread was edited, pinned, locked or removed;
- your replies: text, the sticker you picked, and which post they answer;
- the images you attach. They are re-encoded like screenshots: hidden metadata such as GPS location is removed, file names are random, and we keep a copy up to 1600 px and a 640 px thumbnail on our own server.

Posts, their images, their upvote counts and your username on them are **public**. We also store your upvotes; nobody sees who upvoted what, not on the site and not in the admin.

When you delete a post, its text, sticker and images are deleted at once. A thread's title stays while replies of others are under it, shown as "[deleted]". When moderators remove a post, its images are deleted at once, and its text is kept with the reason, visible only to you, moderators and staff. Moderators see reported posts together with the author's history, as for other reports.

**Reply notifications.** When someone replies to your thread or to your reply, we store a notification for you (which reply, when, and when you opened the list), plus the time of your newest unread one so that the menu can show a mark. Only you see them. They are deleted after **90 days**, or with your account. We never send them by email.

**Ban evasion.** When an account is banned, we store a salted one-way hash of its GitHub user id (never the id itself), with the reason and the end date. It only lets us recognise the same GitHub account if it signs up again during the ban. It is deleted when the ban ends or is lifted, also when the banned account was deleted in the meantime.

**Terms acceptance.** We store which version of the Terms you accepted and when.

**Audit log.** We keep an internal record of hallmark changes, moderation actions and account deletions, so that decisions can be checked later. Only staff can see it.

**IP addresses and logs.** The application does not store your IP address, and its own logs do not contain it. For each page request the logs record only the method, the page address (without anything after a `?`), the response status, size and time taken, plus errors. They hold no browser details. Page addresses include usernames (`/u/<username>/`), so a log line can show which profile was opened, but not by whom.

**Error log.** When something fails, the application writes a short record to an error file on our server. The record holds:

- the time and a random reference number (the one shown on the error page);
- the request method, and the page address without anything after a `?` and with usernames replaced by `[user]`;
- the response status and which part of the code failed;
- the technical error message, with email addresses, IP addresses and anything that looks like a password or key removed.

Pages that were not found are written to a separate file, each address at most once a minute. These files never contain your IP address, browser details, cookies, what you typed into a form, your email address or your username. Each file is limited to 5 MB plus 5 older copies; the oldest is deleted when the limit is reached.

> **TODO before launch:** the web server in front of the application keeps its own access log, which by default includes IP addresses. What it records and how long it keeps it (and how long the application logs are kept) has not been decided yet. Fill this in, or switch IP logging off, before this page goes public.

**Abuse protection.** To limit abuse we count some actions (for example, likes per hour) in the site's database. Each counter is a number tied to your account or to a project, without any IP address, and applies for at most 24 hours. After that it is no longer used, but the row may stay in the database until it is cleaned up. One exception: when you search for people without being signed in, the counter is tied to a salted one-way hash of your IP address (never the address itself) for 10 minutes. What you search for is never stored.

**Analytics and tracking.** There are none: no analytics, no advertising and no tracking scripts. Fonts are served from our own server.

**Backups.** Every day we back up the database and the uploaded images (screenshots, profile pictures and covers) and keep each backup for 14 days. If you delete your account, your data stays in those backups until the last one that contains it is replaced, up to 14 days later.

## Messages to support {#support}

When you write to us through the [support form](/support/), we store the topic, the subject, your message, the email address you give (or your account's), the account you were signed in with, the reference number of an error page if you came from one, and up to 3 attachments. Images are re-encoded like other pictures (hidden metadata such as GPS location is removed); text files are kept as text. Attachments are stored in a private folder on our server that has no public address: only staff with access to the support inbox can download them. We use your email address only to reply.

We do not store your IP address or browser details with the message. To stop spam, a salted one-way fingerprint of your IP address is kept in the server's cache for at most 24 hours, never in the database or the logs.

When a message arrives, our server sends a short plain-text notice with your message and your email address to the team's mailbox, through our email provider (see "Who else receives data"). Staff can add internal notes and set a status (new, read, answered, closed). We read every message but cannot promise to reply to all. Closed messages are deleted 12 months after they were sent; the others stay until they are closed. "Download my data" includes the messages you sent while signed in, and deleting your account deletes them, also the ones sent while signed out from your account's email address.

## How long we keep it {#retention}

- Your account, profile, projects, follows and likes: until you delete them or your account.
- Support messages and their attachments: closed ones 12 months after they were sent, the others until they are closed; with your account.
- Community threads, replies and images: until you delete them or your account (see "Community" above for what stays). Upvotes: until you take them back or delete your account.
- Reply notifications: 90 days.
- Profile picture and cover: until you remove or replace them, or delete your account.
- Uptime checks: 90 days.
- Moderation decisions about you (mutes, bans, removed projects) and notices: while your account exists; they are deleted with it. Reports about you stay without a link to your account, with only the name shown at the time.
- Ban hash of a GitHub id: only until the ban ends or is lifted.
- Sign-in sessions: 2 weeks, or until you sign out.
- Reports you made: kept after they are handled. If you delete your account, they stay without your name.
- Audit log: kept. Entries about a deleted account do not contain the username or email.
- Abuse-protection counters: at most 24 hours.
- Backups: 14 days. A deleted account disappears from them within 14 days.
- Error log files: until they are full (5 MB, plus 5 older copies of 5 MB each), then the oldest entries are deleted.
- Web server and application logs: **TODO**, not decided yet.

## Who else receives data {#recipients}

- **GitHub, Inc.** You sign in on github.com, and our server reads your profile and public repository data from GitHub's API. GitHub's own privacy statement applies to your use of GitHub.
- **Our email provider** (for example Google, if the team's mailbox is a Gmail account) carries the notice about each support message, with its text and your email address, to the team's mailbox.
- **The servers of your project.** For the Domain verified and Steady checks our server contacts your domain's DNS and your project's address. They see our server, not you.
- **Our hosting provider**, which runs the server and the database for us.

We do not sell your data and do not share it for advertising.

## Your rights {#rights}

- **See and download your data:** Settings → "Download my data" gives you a JSON file with your profile (with your links, skills, pinned projects and the addresses of your picture and cover), GitHub details, projects, build log, likes, follows, reports you made, and moderation decisions and notices about you.
- **Correct it:** edit your profile in Settings and your projects on their pages.
- **Delete it:** Settings → "Delete account". This removes your profile, your picture and cover, and all your projects, likes and follows at once and cannot be undone. Your username becomes free.
- **Community:** "Download my data" also contains your threads, replies, the addresses of your images, your upvotes and your reply notifications. Deleting your account deletes your community images, upvotes and notifications, and your threads without replies from others; your other posts stay without your name, picture or link. Community images are in the daily backups like other uploads (14 days).
- **Object or complain:** write to [{{ contact_email }}](mailto:{{ contact_email }}). If you live in the EU, UK or Ukraine, you can also complain to your data protection authority.

## Cookies {#cookies}

We use only the cookies the site needs to work. See the [cookie policy](/legal/cookies/).

## Changes {#changes}

If this policy changes, we update the date at the top. If the change is important, we will ask you to accept the updated Terms on your next visit.
