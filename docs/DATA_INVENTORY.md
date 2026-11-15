# Data inventory

Every piece of personal data the code stores or processes. The privacy, terms and cookies pages
(`content/<lang>/{privacy,terms,cookies}.md`) are written from this file.
**When a model gets a new personal field, or data goes somewhere new, update this file, the legal
pages and `accounts/export.py`.**

Last checked against the code: 2026-11-13 (community; support messages and attachments).

"Public" means anyone on the internet, signed in or not. "Staff" means people with admin access
(`is_staff`) at `ADMIN_URL`. Every record below is in the export unless the "Export" column says no.

## 1. Account (`accounts.User`)

| Field | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `username` | Suggested from GitHub login, confirmed by the user at signup | Profile URL `/u/<username>/`, identity on the site | Until account deletion; then free for anyone | Public | yes |
| `display_name` | GitHub `name` at first sign-in, then edited by the user | Shown on profile, projects, feed | Until deletion | Public | yes |
| `about` (≤1000, limited markdown) | GitHub `bio` at first sign-in, then the user (settings). Replaces `bio` | Profile "About" tab; the first 160 characters (markup removed) are the page description | Until deletion | Public (rendered and sanitized) | yes |
| `headline` (≤80), `location` (≤60), `status` (open to work / open to collaborate / hiring / building in public) | The user, all optional | Profile card | Until deletion | Public. Free text: the person decides what to write; moderators can clear headline and About | yes |
| `skills` (≤10 tags, shared `Tag` table) | The user, optional | "About" tab | Until deletion (the tag row stays, it is a shared word list) | Public | yes |
| `ProfileLink` (≤6: kind, https/http address, order) | The user, optional | Links on the profile (website, GitHub, X, LinkedIn, Telegram, other). GitHub, X, LinkedIn and Telegram must point to their own sites | Until deletion | Public, with `rel="nofollow ugc noopener"` | yes |
| `PinnedProject` (≤3: own published projects) | The user, optional | Shown first on the profile | Until deletion or until the project is unpublished or removed (then it is not shown) | Public | yes |
| `avatar`, `avatar_source` (upload / GitHub), `cover` | The user: an uploaded file, or "use my GitHub picture" (downloaded **once** through `safe_fetch` from `avatars.githubusercontent.com`, stored on our disk, never hotlinked). Files are re-encoded to WebP (512×512 and 1500×500), metadata removed, random names, in `MEDIA_ROOT` (`avatars/`, `covers/`) | Profile picture and banner | Until the person removes or replaces them, or deletes the account (the files are deleted from disk; copies stay in backups for up to 14 days) | Public (the image URL is public) | yes (links to the files) |
| `bio`, `website` | **Deprecated.** The old fields; copied to `about` and a website link by migration 0006. Nothing reads or writes them. A later migration drops the columns | none | Until the cleanup migration | Staff (admin hides them) | no |
| `email` | GitHub (primary email) | Account record; staff can contact the person about their account or a report. **No email is sent by the site** | Until deletion | Staff only. Never shown publicly | yes |
| `github_login` | GitHub, refreshed at **every** sign-in (`accounts/github.py`). If another local account still holds the same login (its owner renamed on GitHub), that stale copy is cleared and logged | Profile link to GitHub; one account per GitHub login | Until deletion | Public | yes |
| `avatar_url` | GitHub at first sign-in (the address of the GitHub picture) | Used only for "use my GitHub picture" (see `avatar` above). **Never shown or hotlinked**: remote images would leak visitors' IPs to GitHub | Until deletion (moderators clearing the picture also clear it) | Staff | yes |
| `preferred_language` | The user (settings or language switcher) | UI language | Until deletion | Staff | yes |
| `terms_version_accepted`, `terms_accepted_at` | Signup step and "accept updated Terms" page | Proof of which Terms the user accepted, and when | Until deletion | Staff | yes |
| `date_joined` | Automatic | Profile shows "Joined <month year>" | Until deletion | Public (month and year) | yes |
| `last_login` | Automatic (Django) | Admin information | Until deletion | Staff | yes |
| `is_suspended`, `is_staff`, `is_superuser`, `is_active` | Staff / system | Moderation and permissions | Until deletion | Staff | `is_suspended` yes |
| `password` | None: GitHub users get an unusable password. Only staff accounts made with `createsuperuser` have one (hashed) | Admin sign-in | Until deletion | Nobody (hash only) | no |
| `first_name`, `last_name` | Always empty (cleared in `accounts/adapters.py`) | Not used | n/a | n/a | no |

## 2. GitHub sign-in (django-allauth)

| Data | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `SocialAccount.uid` | GitHub numeric account id | Links the GitHub account; the repository check compares owners by this id | Until deletion | Staff | yes |
| `SocialAccount.extra_data` | The full JSON GitHub returns for `GET /user` (login, id, name, bio, avatar, company, blog, location, public email, twitter username, public counts, account dates…). Refreshed by allauth at each sign-in | Kept as allauth stores it; the app reads only `login`, `name`, `bio`, `avatar_url` | Until deletion | Staff | yes |
| `SocialAccount.date_joined`, `last_login` | Automatic | Admin information | Until deletion | Staff | yes |
| `EmailAddress` rows | GitHub `GET /user/emails`: **every** address on the GitHub account, with primary/verified flags (scope `user:email`) | Required by allauth; one becomes `User.email` | Until deletion | Staff | yes |
| GitHub access token | OAuth | Used once during sign-in to read the two endpoints above | **Not stored** (`SOCIALACCOUNT_STORE_TOKENS = False`) | n/a | n/a |

OAuth scopes: `read:user`, `user:email` only. No access to private repositories.

## 3. Projects and content (`projects`)

| Data | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `Project` name, slug, tagline, description, live URL, repo name, tags, status, dates | The user | The project page | Until the project or account is deleted | Published: public. Draft and hidden: owner and staff | yes |
| `built_with` (AI tools) | The user, **self-declared** | Shown as "Built with (self-declared)" | Same | Same as the project | yes |
| `Screenshot` image files, and their thumbnails (`thumb`, a derived WebP copy up to 640 px) | Upload by the user. Re-encoded to WebP (metadata such as EXIF/GPS removed), random file name; the thumbnail is made from the stored image | Project page (full image); feed, profile rows, Explore and landing cards (thumbnail) | Until removed; both files are deleted with the row | Same as the project (files under `/media/` are reachable by URL) | yes (URLs) |
| `BuildLogEntry` text, kind, date | The user | Timeline on the project page and feed | Until deleted | Same as the project | yes |

## 4. Verification (`verification`)

| Data | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `RepoLink`: repo name, GitHub repo id, owner account id, is owner, verification file found, repo created date, the repo's Website field, first commit of the history (sha, date), the user's commit count, first/last commit dates, active weeks, review state and reasons, reviewed by/at, check dates | GitHub public API (`api.github.com`), re-read weekly by `reverify_repos` | Repo owner hallmark (id `authored`) and the "What was checked" panel | Until the check fails, the repo is unlinked, or deletion | Facts with dates: public on published projects. Review reasons and reviewer: owner (export) and staff only; the page shows only "waiting for a routine manual review" | yes (without reviewer) |
| Contributor lists of repositories | GitHub public API | Find the user's commit count | **Not stored**: other contributors' logins and counts are read in memory and dropped | n/a | n/a |
| `DomainVerification` (domain, method, token, status, dates, last error code) | The user's live URL; our DNS lookups and HTTP requests | Live hallmark | With the project (one row per project + domain) | Status/dates: public via the hallmark. Token: owner and staff | yes (no token) |
| `Project.repo_token` | Random, made when the edit page first shows the repository section (`verification/repo.py::repo_token_for`); unique, never reused | The content of the `.shipmark-verify` file that proves write access to an organisation or team repository | With the project | Owner (edit page) and staff | no (a secret for the check, like the domain token) |
| `Block` (kind repo/domain, repo id or domain, readable name, internal note, staff member, date) | Staff, from the review queue | Stops a repository or domain from earning a mark again | Until staff delete it (logged) | Staff only | no (a moderation record about a repository or domain, not about the person) |
| `UptimeCheck` (time, ok, status code, response time, error code) | Our requests to the project URL | Steady hallmark | **90 days** (pruned by `check_uptime`) | Public summary on the project page | no (technical data about the site, not the person; shown on the project page) |

Requests to users' sites go through `verification/net.py::safe_fetch` with a fixed User-Agent
(`<SITE_NAME>-verify/1.0`). The project's server sees our server's IP address, never a visitor's.

## 5. Social (`social`)

| Data | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `Follow` (follower, following, date) | The user | Feed | Until unfollow or deletion of either account | Public: follower count only. The list of who follows whom is not shown | yes (people you follow) |
| `Like` (user, project, date) | The user | Like counts, "most liked" sort | Until unlike, or deletion of the user or project | Public: count only | yes |

## 6. Moderation (`moderation`)

| Data | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `Report` (reporter, target: project / profile / build-log entry / thread / reply, target owner, target name, source user/moderator, reason, details, status open/in review/resolved/dismissed, resolution note, handled by, dates) | A signed-in user, or a moderator acting while browsing | Moderation | Kept after it is handled (no automatic deletion). When the reporter deletes their account, `reporter` becomes empty. When the target or its owner is deleted, those links become empty; the readable name (`target_repr`, e.g. "alice/my-app") stays | Moderators (moderator badge) and staff. The reported person never sees who reported them | yes (reports you made) |
| `Sanction` (user, mute/ban, reason, start, end or none = permanent, issued by, report, revoked at/by) | A moderator (mute ≤ 7 days, ban ≤ 14 days) or a superuser (any length, permanent, revoke) | Enforce the terms: a mute blocks posting; a ban signs the person out, blocks sign-in and hides the profile and projects | While the account exists (never deleted, only revoked); deleted with the account | The person (reason and end date: banner or ban page), moderators, staff | yes |
| `Notice` (user, kind, about, reason, created, dismissed) | System, from a moderator decision | Tell the person what was decided and why (removed project, cleared profile fields, outcome of their report). Never names a reporter | While the account exists; deleted with it | The person, staff | yes |
| `BannedIdentity` (HMAC-SHA256 of the GitHub user id under `BAN_HASH_KEY`, hash scheme, reason, end date, sanction link) | System, when a ban is issued for an account with GitHub sign-in | Stop a banned person from deleting the account and signing up again during the ban. The GitHub id itself is never stored. The key is its own secret (env `BAN_HASH_KEY`, not in the database, not `SECRET_KEY`); the hash is useless without it. Hashes made before this key existed (scheme `secret_key`) are converted by `rehash_bans` when their account still exists, otherwise they expire on their own | Only until the ban ends or is revoked: deleted on revoke, when sign-ups are checked, and by the daily `prune_bans`. Survives account deletion until then | Superusers (hash only) | no (not linked to an account) |
| `Project.removed_reason`, `removed_at`, `removed_by` | A moderator | Why a project was removed (owner sees it on the project page) | With the project; superusers restore or purge | Owner, moderators, staff | yes (with the project) |
| `AuditLog` (actor, action, target type/id, target name, metadata, date) | System and staff | Record of hallmark changes (earned, removed, needs review, needs re-check, repo renamed), GitHub login changes (`account.github_login.renamed` / `.released`, with old and new login), moderation actions (approve, revoke, block), account deletions | Kept (no automatic deletion). Actor becomes empty when that account is deleted. The account-deletion entry has no username or email ("deleted user #<id>") | Staff only, read-only | no (internal record) |

## 6a. Community (`community`, behind `COMMUNITY_ENABLED`)

Export and deletion cover these rows also while the flag is off.

| Data | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `Thread` (board, author, title ≤120, body ≤8000 limited markdown, slug, status published/locked/removed, pinned, created, edited, last activity, score, reply count, `deleted_at`, removed reason/at/by, lock reason) | The user; moderators set status, pin, lock and the reasons | Community threads | Author delete: body and images deleted at once; the row (title, "[deleted]") stays only while others replied. Account deletion: threads without others' replies are deleted, the rest lose their author (`SET_NULL`) | Published/locked on an active board with a visible author: public. Removed: author, moderators, staff. Reasons: author, moderators, staff | yes (with removed reason) |
| `Reply` (thread, parent, root, depth 1-3, author, body ≤4000, sticker key, status, score, created, edited, `deleted_at`, removed reason/at/by) | The user; moderators remove | Answers | Author delete: body, sticker and images deleted at once, the row stays for the answers under it. Account deletion: author emptied | Like the thread; removed text: author, moderators, staff | yes |
| `CommunityImage` (display copy ≤1600 px and 640 px thumbnail, WebP, width/height, alt, order, uploader, date) in `MEDIA_ROOT/community/<year>/<month>/` (thumbnails in `t/`) | Upload; re-encoded by `projects/images.py` (metadata such as EXIF/GPS removed), random names, through the storage API | Pictures in posts | Deleted with the row and its files (`community/signals.py`) when the author deletes the post, a moderator removes it, or the uploader deletes the account. Then only in backups (14 days) | Same as the post | yes (addresses, sizes) |
| `Vote` (user, thread or reply, date) | The user | Scores, Hot/Top | Until taken back, or deletion of the user or the post. `community_daily` stops counting votes of suspended or banned accounts | Nobody: only the score is public. Not registered in the admin | yes |
| `ReplyNotification` (recipient, reply, kind thread/reply, created, read) | System, when someone answers the person's thread or reply (never for their own reply, deleted or inactive accounts) | "Replies to you" list (in-app only, no email) | **90 days** (`community_daily`), or with the account or the reply | The recipient | yes (kind, address, dates; not the other person's name or text) |
| `User.community_notified_at` | System | The mark in the account menu without a query | Cleared when the list is opened; with the account | The user (as a mark) | no (a cache of the row above) |
| Duplicate-post keys `community:dup:<kind>:<user id>:<SHA-256 of board/parent + normalized text>` | Django cache (`community/services.py`) | Refuse the same text twice in a row | 10 minutes (reply) or 24 hours (thread) | Nobody | no |

Moderators (moderator badge) see reported posts in `/mod/` with the author's history, like other reports, and removed
posts with their text. The AuditLog records remove, lock, pin, restore and `community.welcome_posted`.
The demo accounts of `seed_community` (`demo-*`, `@example.invalid`) exist only in development (the command refuses
to run without `DEBUG`).

## 6b. Support (`support`)

| Data | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `SupportMessage` (user or none, email, category, subject ≤120, body 10-4000, reference = request id from an error page, status new/read/answered/closed, internal note, created, updated) | The visitor (form at `/support/`); staff set status and note | Answer questions, fix bugs | Closed: deleted 12 months after sending (`prune_support`, cron). Others: until closed. With the account (also messages sent signed out from the account's email) | Staff with `support.view_supportmessage` (and superusers) in the admin. The internal note: staff only | yes (not the internal note) |
| `SupportAttachment` (kind image/text, file, cleaned original name, size, date) in `SUPPORT_ROOT` (default `private/support/`, **outside** `MEDIA_ROOT`, no URL; `STORAGES["support"]`) | Upload: images re-encoded to WebP by `projects/images.py` (metadata removed), .txt/.log stored as UTF-8 text (≤200 KB, binary refused); random names | Screenshots and logs for a bug | With the message (files deleted by `support/signals.py`), then only in backups (14 days) | Staff with the permission, through `/support/attachment/<id>/` (download, `nosniff`, sandbox CSP) | yes (kind, name, size) |
| Notification email (plain text: category, email, account name, subject, body, reference, number of attachments, admin link; no attachments) | `support/notify.py`, after the commit, to `SUPPORT_INBOX_EMAIL` with Reply-To = the visitor | Tell the team | In the team mailbox and at the email provider (e.g. Gmail) under their terms | The team | no |
| Rate-limit keys `support:rl:<hour/day>:<s:session / u:user id / ip:HMAC-SHA256(SECRET_KEY, IP)[:32]>` and duplicate keys `support:dup:<SHA-256 of email + text>` | Django cache | 3 messages/hour and 10/day; same text once per 24 h | Counters apply for 1 hour / 24 hours; expired database-cache rows physically removed by daily `prune_support` | Nobody | no |

No IP address or user agent is stored with a message. The salted IP hash exists only as a cache key (above). The
client address comes from `CLIENT_IP_HEADER` (set by the reverse proxy) or `REMOTE_ADDR`.

## 7. Cookies and browser storage

Only strictly necessary ones. No analytics, no ads, no third-party scripts or fonts.

| Name | Set by | Purpose | Lifetime |
|---|---|---|---|
| `sessionid` | Django sessions | Keeps you signed in; holds sign-in state during the GitHub redirect | 2 weeks (Django default), removed at sign-out |
| `csrftoken` | Django CSRF | Protects forms against cross-site requests | 1 year (Django default) |
| `django_language` | Language switcher; also written from the saved `preferred_language` at sign-in and on signed-in pages when it differs (`UserLocaleMiddleware`, `AccountAdapter.post_login`) | Remembers the language you chose, so pages and the "signed in / signed out" notices stay in one language, also after signing out | 1 year (`LANGUAGE_COOKIE_AGE`) |
| `messages` | Django messages | One-time notices ("Settings saved") when there is no session (e.g. right after sign-out) | Until shown, at most the browser session |
| `theme` (localStorage, not a cookie) | `static/js/theme.js` | Light/dark choice | Until cleared in the browser. **Never sent to the server** |

## 8. Server-side, not in models

| Data | Where | Purpose | Retention |
|---|---|---|---|
| Session rows (user id, auth hash, allauth state, messages) | `django_session` table | Sign-in | Expire after 2 weeks. Expired rows stay until `manage.py clearsessions` runs (not scheduled yet, see `docs/DEPLOY_NOTES.md`) |
| Rate-limit counters: key `rl:<action>:<user id or project id>`, value = a number (plus `rl:…:until`, the end of the window, and cooldowns `cd:<action>:<key>` = an end time; the repo-check cooldown key is `<project id>:<repository name>`). Admin login: `rl:admin_login:<truncated SHA-256 of the username>` | Django cache (`config/ratelimit.py`). **Production: database cache, table `django_cache`** (`createcachetable`). Dev: process memory | Abuse protection | Each counter counts for its window: 10 minutes, 1 hour, or 24 hours (`buildlog_add`); the admin-login counter 15 minutes. Expired rows may remain until read or cache culling. Daily `prune_support` physically removes expired rows; the counter lifetime and deletion are separate. **No IP addresses** |
| People search rate limit (`accounts/people.py`, Discover → People) | Django cache (same table as above): key `rl:people_search:u:<user id>` when signed in, `rl:people_search:ip:<salted HMAC-SHA256 of the IP address, label "people-ip", truncated to 32 hex>` when not; value = a number | Stops scripts from walking the user list | The 10-minute window (expired rows: see the row above). **The search text is not stored anywhere**: not in the key, not in a model, not in logs (the access log drops the query string) |
| Public account count | Django cache, key `stats:public_user_count` (`pages/stats.py`): one number, no personal data | The header's "<n> people joined" | 60 seconds |
| IP addresses | The app does not store them: not in models, not in the app logs or error files. The only traces are two rate limits: people search by anonymous visitors (10 minutes, row above) and the support form's: a salted HMAC of the address as a cache key for at most 24 hours (section 6b) | Spam protection | 1 hour / 24 hours |
| Application logs (JSON on stdout, `config/jsonlog.py`, `gunicorn.conf.py`) | gunicorn access line: method, path without query string, status, bytes, milliseconds. Django `django.request` for 4xx/5xx, and exceptions | Operations, debugging | **No IP address, no user agent, no query string.** Launch policy: routes must be redacted and log messages sanitized so stdout contains no personal data (implemented and regression-tested). Heroku log stream: up to approximately one week, readable only by the hosting account holder. No long-term drain or logging add-on at launch; update Privacy before enabling one. |
| Error log files (`LOG_DIR`/`errors.jsonl`, `notfound.jsonl`; `config/errorlog.py`) | errors.jsonl: unhandled exceptions, 5xx, 403 and CSRF failures. Fields: timestamp, level, request id (random, per request), method, path **without query string, `/u/<name>` and `/badge/<name>` masked as `[user]`**, status, view name, exception class, message and traceback **scrubbed** (emails, IPs, tokens, `password=`/`secret=`/`token=`… values, long random strings removed). notfound.jsonl: timestamp, level, request id, method, masked path, status; each path at most once a minute per worker | Debugging (`manage.py show_errors`) | Rotating: 5 MB per file + 5 old copies, the oldest is deleted. **No IP address, user agent, cookies, headers, query string, POST body, email, username or token** |
| Hosting routing log | Heroku routing layer, outside application code; includes the visitor IP | Routing and operations | Heroku log stream, up to approximately one week, account holder only. No long-term drain/add-on at launch. Cloudflare is DNS-only; update Privacy before enabling its proxy |
| Backups | Cron lines in `docs/DEPLOY_NOTES.md`: `pg_dump` of the database (03:15) and `tar` of `MEDIA_ROOT` (03:30), daily | Recovery | **14 days** on the server (`find … -mtime +14 -delete`). A deleted account stays in them until the last backup containing it is rotated out. All backup copies, including off-server copies and object versions, follow the existing 14-day retention policy. Configure and verify this before launch; local code does not enforce provider backup retention. |

## 9. Third parties

| Who | What they get | Why |
|---|---|---|
| GitHub, Inc. | The sign-in redirect (you sign in on github.com). Our server calls `api.github.com` for your profile, emails, and public repository data | Sign-in, Repo owner hallmark (id `authored`) |
| DNS resolvers and the project's own server | DNS queries for the project domain; HTTP requests to the project URL | Live and Steady hallmarks |
| Email provider (SMTP, e.g. Google for Gmail) | The plain-text notice about each support message: its text, the sender's email and account name | Deliver the notice to the team mailbox (processor) |
| Web hosting and managed database | Application records and routing information | Hosting and database processing. Heroku at launch; Privacy names processor categories generically |
| S3-compatible object storage | Uploaded images and private support attachments | Store files on our behalf; provider/bucket chosen before deployment |

Nothing is sold or shared for advertising. Email provider: only for the notice about each support message to the team's mailbox (`SUPPORT_INBOX_EMAIL`, SMTP from `.env`, e.g. Gmail); the site sends no email to users.

## 10. Rights, as implemented

- **Export:** Settings → "Download my data" (`accounts/export.py`): JSON of everything marked "yes" above.
- **Deletion:** Settings → "Delete account" (`accounts/deletion.py`): type the username to confirm. Deletes the
  user and cascades to everything in sections 1–5; community content as described in section 6a. Reports they made are kept with `reporter` emptied.
  Writes `AuditLog` action `account.deleted`. The username is free again.
- **Correction:** profile fields in Settings; project content on the project pages.
- **Terms re-acceptance:** bump `TERMS_VERSION` in `config/settings/base.py`; signed-in users are asked on their next visit.

## Launch decisions (developer-approved)

Heroku hosts the application and managed PostgreSQL. Cloudflare is DNS-only at launch. No long-term log drain or logging add-on is enabled. Application logs contain no raw IP or personal data; the application stores only salted IP hashes for rate limits in the database-backed cache. Heroku routing logs contain visitor IPs; routing and stdout share the short-lived log stream (up to approximately one week), accessible only to the account holder. Privacy must be updated before adding a drain, logging add-on or traffic proxy. Closed support messages and attachments are removed 12 months after sending by daily `prune_support`. Daily `prune_support` cache cleanup is implemented and regression-tested; stdout redaction is implemented and regression-tested.

## Production file storage (launch stage 7)

Production requires a private S3-compatible bucket and explicit credentials. Re-encoded project/profile/community images are stored under `media/` and delivered by signed URLs (3600 seconds). Support attachments are stored under `support/`; the storage backend refuses browser URLs and only the existing permission-checked download view streams their bytes. Both prefixes deny anonymous access; the account holder must verify bucket policy/IAM and deletion/backup retention before launch. Local development retains MEDIA_ROOT and private SUPPORT_ROOT. No provider resources or credentials were created here. All backup copies and noncurrent versions follow the existing 14-day policy; never expire current live images merely because they are 14 days old.
