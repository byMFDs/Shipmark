# Data inventory

Every piece of personal data the code stores or processes. The privacy, terms and cookies pages
(`content/<lang>/{privacy,terms,cookies}.md`) are written from this file.
**When a model gets a new personal field, or data goes somewhere new, update this file, the legal
pages and `accounts/export.py`.**

Last checked against the code: 2026-11-10.

"Public" means anyone on the internet, signed in or not. "Staff" means people with admin access
(`is_staff`) at `ADMIN_URL`. Every record below is in the export unless the "Export" column says no.

## 1. Account (`accounts.User`)

| Field | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `username` | Suggested from GitHub login, confirmed by the user at signup | Profile URL `/u/<username>/`, identity on the site | Until account deletion; then free for anyone | Public | yes |
| `display_name` | GitHub `name` at first sign-in, then edited by the user | Shown on profile, projects, feed | Until deletion | Public | yes |
| `bio` (≤280) | GitHub `bio` at first sign-in, then the user | Profile | Until deletion | Public | yes |
| `website` | The user | Profile link | Until deletion | Public (only http/https shown as a link) | yes |
| `email` | GitHub (primary email) | Account record; staff can contact the person about their account or a report. **No email is sent by the site** | Until deletion | Staff only. Never shown publicly | yes |
| `github_login` | GitHub at first sign-in | Profile link to GitHub; one account per GitHub login | Until deletion | Public | yes |
| `avatar_url` | GitHub at first sign-in | Stored for later use. **Not shown** (initials are shown; remote images would leak visitors' IPs to GitHub) | Until deletion | Staff | yes |
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
| `Screenshot` image files | Upload by the user. Re-encoded to WebP (metadata such as EXIF/GPS removed), random file name | Project page | Until removed; the file is deleted with the row | Same as the project (files under `/media/` are reachable by URL) | yes (URLs) |
| `BuildLogEntry` text, kind, date | The user | Timeline on the project page and feed | Until deleted | Same as the project | yes |

## 4. Verification (`verification`)

| Data | Source | Purpose | Retention | Who can see it | Export |
|---|---|---|---|---|---|
| `RepoLink` (repo name, GitHub repo id, is owner, the user's commit count, first/last commit dates, check dates) | GitHub public API (`api.github.com`) | Authored hallmark | Until the check fails, the repo is unlinked, or deletion | Hallmark and its facts: public on published projects | yes |
| Contributor lists of repositories | GitHub public API | Find the user's commit count | **Not stored**: other contributors' logins and counts are read in memory and dropped | n/a | n/a |
| `DomainVerification` (domain, method, token, status, dates, last error code) | The user's live URL; our DNS lookups and HTTP requests | Live hallmark | With the project (one row per project + domain) | Status/dates: public via the hallmark. Token: owner and staff | yes (no token) |
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
| `Report` (reporter, target, target name, reason, details, status, handled by, dates) | A signed-in user | Moderation | Kept after it is resolved (no automatic deletion). When the reporter deletes their account, `reporter` becomes empty. When the target is deleted, the target link becomes empty; the readable name (`target_repr`, e.g. "alice/my-app") stays | Staff only. The reported person is not told who reported them | yes (reports you made) |
| `AuditLog` (actor, action, target type/id, target name, metadata, date) | System and staff | Record of hallmark changes, moderation actions, account deletions | Kept (no automatic deletion). Actor becomes empty when that account is deleted. The account-deletion entry has no username or email ("deleted user #<id>") | Staff only, read-only | no (internal record) |

## 7. Cookies and browser storage

Only strictly necessary ones. No analytics, no ads, no third-party scripts or fonts.

| Name | Set by | Purpose | Lifetime |
|---|---|---|---|
| `sessionid` | Django sessions | Keeps you signed in; holds sign-in state during the GitHub redirect | 2 weeks (Django default), removed at sign-out |
| `csrftoken` | Django CSRF | Protects forms against cross-site requests | 1 year (Django default) |
| `django_language` | Language switcher | Remembers the language you chose | 1 year (`LANGUAGE_COOKIE_AGE`) |
| `messages` | Django messages | One-time notices ("Settings saved") when there is no session (e.g. right after sign-out) | Until shown, at most the browser session |
| `theme` (localStorage, not a cookie) | `static/js/theme.js` | Light/dark choice | Until cleared in the browser. **Never sent to the server** |

## 8. Server-side, not in models

| Data | Where | Purpose | Retention |
|---|---|---|---|
| Session rows (user id, auth hash, allauth state, messages) | `django_session` table | Sign-in | Expire after 2 weeks. Expired rows stay until `manage.py clearsessions` runs (not scheduled yet, see `docs/DEPLOY_NOTES.md`) |
| Rate-limit counters `rl:<action>:<user id or project id>` | Django cache (memory) | Abuse protection | At most 1 hour. **No IP addresses** |
| IP addresses | The app does not store them | n/a | n/a |
| Web server / proxy access logs | Hosting, outside this code | Depends on the host | **To decide at deploy**, then add to the privacy page |
| Backups | Hosting, outside this code | Depends on the host | **To decide at deploy**, then add to the privacy page |

## 9. Third parties

| Who | What they get | Why |
|---|---|---|
| GitHub, Inc. | The sign-in redirect (you sign in on github.com). Our server calls `api.github.com` for your profile, emails, and public repository data | Sign-in, Authored hallmark |
| DNS resolvers and the project's own server | DNS queries for the project domain; HTTP requests to the project URL | Live and Steady hallmarks |
| Hosting provider | Everything above, as it runs the server and database | Hosting (processor). Name it in the privacy page before launch |

Nothing is sold or shared for advertising. No email provider (the site sends no email).

## 10. Rights, as implemented

- **Export:** Settings → "Download my data" (`accounts/export.py`): JSON of everything marked "yes" above.
- **Deletion:** Settings → "Delete account" (`accounts/deletion.py`): type the username to confirm. Deletes the
  user and cascades to everything in sections 1–5. Reports they made are kept with `reporter` emptied.
  Writes `AuditLog` action `account.deleted`. The username is free again.
- **Correction:** profile fields in Settings; project content on the project pages.
- **Terms re-acceptance:** bump `TERMS_VERSION` in `config/settings/base.py`; signed-in users are asked on their next visit.
