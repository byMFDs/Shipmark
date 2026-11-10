# Shipmark: MVP, розбитий на промпти для Claude Code

Цей файл для тебе, не для Claude. Поклади його в `docs/PROMPTS.md`.
Claude Code сам його не читає, тому він не з'їдає ліміти.
`CLAUDE.md` кладеш у корінь проєкту: його Claude Code читає автоматично щоразу.

Промпти написані англійською навмисно: англійський текст займає помітно менше токенів,
ніж український, а ти кидаєш їх десятки разів. Відповідати тобі Claude буде українською
(це прописано в `CLAUDE.md`). Над кожним промптом є пояснення українською, що він робить.

---

## Частина A. Підготовка (робиш руками, один раз)

1. Встанови Python 3.12+ і git (на Pop!_OS/Ubuntu: `sudo apt install python3 python3-venv git`).
2. Встанови Claude Code за офіційною інструкцією:
   https://docs.claude.com/en/docs/claude-code/overview
   Він входить у твою Pro-підписку, окремо платити не треба.
3. Створи папку і репозиторій:
   ```bash
   mkdir shipmark && cd shipmark
   git init
   mkdir docs
   ```
4. Поклади `CLAUDE.md` у корінь `shipmark/`, а цей файл у `shipmark/docs/PROMPTS.md`.
5. Створи **приватний** репозиторій на GitHub і підключи його (`git remote add origin ...`).
6. Перший коміт: `git add . && git commit -m "Add project memory and prompt plan"`.
7. Запусти `claude` у папці `shipmark/`.

---

## Частина B. Ритуал кожного промпту (найважливіше)

1. **Новий промпт = чиста сесія.** Перед кожним промптом пиши `/clear`.
   `CLAUDE.md` підтягнеться сам, а сміття з минулої задачі зникне. Це головна економія лімітів.
2. Для промптів з позначкою **[PLAN]** спершу увімкни plan mode (Shift+Tab, поки не з'явиться
   режим плану), встав промпт, прочитай план, поправ, якщо щось не так, і тільки тоді дозволь писати код.
   Для звичайних промптів plan mode не треба: він додає зайвий крок.
3. Коли Claude закінчив: запусти `python manage.py runserver`, пройди список
   «Що перевірити вручну», потім **сам прочитай змінені файли**. Не все, але так, щоб розуміти,
   що де лежить. Це і є твоє навчання.
4. Якщо все працює: `git add . && git commit -m "<повідомлення від Claude>"` і `git push`.
5. Якщо зламалось і два виправлення не допомогли: **не борися**. `git checkout .` (або `git reset --hard`)
   повертає останній робочий коміт, `/clear`, і кидаєш промпт заново з уточненням.
   Це дешевше, ніж десять повідомлень «виправ ще раз».

### Як економити ліміти
- Ліміти Pro спільні для чату на claude.ai і для Claude Code. Довгі розмови в чаті теж їх з'їдають.
- Є вікно на 5 годин і тижневий ліміт. Перевіряти залишок: `/usage` у Claude Code.
- Основна модель для коду: Sonnet. Важчі моделі (Opus) витрачають ліміт швидше: вмикай через `/model`
  тільки для промптів **[PLAN]**, які зазначені як складні, і то лише на етап плану.
- Коли сесія стала довгою посеред задачі: `/compact Keep: current task, changed files, failing tests`.
- Помилку вставляй **тільки трейсбеком** (останні 20-30 рядків), а не цілими файлами.
- Не проси «переглянь весь проєкт» без причини. Це найдорожче, що можна попросити.
- Не роби два промпти в одній сесії, навіть якщо обидва маленькі.
- Скріншоти: якщо щось виглядає не так, встав скрін у Claude Code. Картинка пояснює краще за абзац тексту.

---

## Частина C. Універсальні промпти (використовуй будь-коли)

**Помилка:**
```
Bug: <what I did> → <what happened> → <what I expected>.
Traceback:
<paste last 20-30 lines>
Fix only this. Explain the cause in 2 sentences.
```

**Хочу зрозуміти код (для навчання, дуже рекомендую):**
```
Explain <file or function> to me like I know basic Django and am learning JS.
What does each part do, why is it built this way, and what would break if I removed it?
Do not change any code.
```

**Маленька зміна:**
```
Small change: <what exactly>. Touch only the files needed. No other changes.
```

**Перед тим як закінчити день посеред задачі:**
```
Write docs/HANDOFF.md: current goal, files changed, decisions made, what is unfinished,
exact next step. Max 20 lines.
```
Наступного разу: `/clear` → `Read docs/HANDOFF.md and continue.`

**Безпека після великої фічі:**
```
Security review of the changes in the last commit only. Check: ownership checks,
CSRF, input validation, SSRF (safe_fetch usage), XSS in templates and markdown,
rate limits. List problems by severity. Do not fix yet.
```
Також у Claude Code є вбудована команда `/security-review`.

---

## Частина D. Промпти MVP (по порядку)

Кожен промпт закінчується тим, що Claude дає тобі список «Що перевірити вручну».
Нижче я додав, на що звернути увагу **тобі** і що варто зрозуміти в коді.

### 1. Фундамент проєкту [PLAN]
Скелет Django: налаштування для dev/prod, змінні середовища, свій User одразу
(потім змінити дуже боляче), структура папок, branding.py.

```
Task 1: project foundation. Follow CLAUDE.md.

- Create a venv-based Django 5.2 LTS project in the current folder: package `config`
  with settings/base.py, dev.py, prod.py. Read settings from env via django-environ.
  DATABASE_URL defaults to SQLite in dev.
- requirements/base.txt, dev.txt, prod.txt with pinned versions (only allowed deps
  needed so far). .env.example documenting every variable. .gitignore for Python,
  .env, media, SQLite db, .venv.
- Create apps from CLAUDE.md section 4 as empty stubs registered in settings.
- Custom User model in accounts (AbstractUser + fields from section 5) BEFORE the first
  migration. AUTH_USER_MODEL set.
- config/branding.py with the fields from section 7 and a context processor `brand`.
- templates/base.html: minimal semantic skeleton (header, main, footer), viewport meta
  from section 10, blocks for title/meta/content/scripts. No styling yet.
- A landing view at / that renders "Shipmark is under construction" from brand.SITE_NAME.
- docs/PROGRESS.md (empty log), README.md with exact Linux commands to set up and run.
- Tests: settings load, / returns 200 and shows SITE_NAME.
Do not build design, auth or any features yet.
```
**Тобі:** запусти за інструкцією з README сам, без Claude. Відкрий `config/settings/`
і зрозумій, чому налаштувань три файли. Спробуй змінити SITE_NAME у `branding.py` і подивись,
що змінилось на сторінці.

---

### 2. Дизайн-система і логотип [PLAN] (тут можна Opus на етап плану)
Найважливіший промпт для того, щоб сайт виглядав дорого, а не як шаблон.
Спершу Claude пише план дизайну і сам перевіряє його на шаблонність, потім код.

```
Task 2: design system and logo. Follow CLAUDE.md section 9 exactly.

Step 1 (plan, show me before coding): write docs/DESIGN.md (max 80 lines): tokens
(colors with light/dark values, type scale, spacing scale, radii, shadows/bevel recipe),
the hallmark mark design, the hero "plate being stamped" moment, layout grid.
Then review your plan against the "Avoid" list in section 9 and against generic AI
landing pages. Revise anything that reads as a default and say what you changed.

Step 2 (after I approve):
- Download IBM Plex Sans, Plex Sans Condensed, Plex Mono (woff2, Latin + Cyrillic
  subsets, needed weights only) into static/fonts with the OFL license. @font-face with
  font-display: swap and a size-adjusted fallback.
- static/css/tokens.css, base.css, components.css. Components: buttons (primary,
  secondary, quiet, danger), inputs/textarea/select/checkbox with errors, plate
  (featured and compact), hallmark (earned/not earned, sizes S/M/L), tag chip,
  avatar, nav header (desktop + mobile menu), footer, toast, empty state, tabs.
- Light/dark: prefers-color-scheme by default plus a toggle (static/js/theme.js,
  remembers choice in localStorage, no flash on load).
- Logo: static/brand/logo.svg (wordmark + mark), logo-mark.svg, favicon.svg,
  apple-touch-icon.png (180px), og-default.png (1200x630). The mark is a hallmark
  cartouche with a simple glyph. It must read well at 16px.
- A /styleguide/ page (DEBUG only) showing every component in both themes.
Mobile-first. Check the quality bar in section 10.
```
**Тобі:** відкрий `/styleguide/` на компʼютері й на телефоні (той самий Wi-Fi,
`runserver 0.0.0.0:8000`, у `ALLOWED_HOSTS` для dev має бути твоя локальна IP).
Якщо щось не подобається, роби скріншот і пиши конкретно: «кнопка виглядає дешево, бо...».
Цей промпт нормально повторити 2-3 рази з правками. Дизайн, який тобі не подобається,
потім переробляти дорожче.

---

### 3. Мови: англійська й українська
```
Task 3: i18n foundation. Follow CLAUDE.md section 8.

- LANGUAGES = en, uk. LocaleMiddleware. Detection order exactly as in section 8.
  No URL prefixes. No IP geolocation.
- Language switcher in the footer (and later the account menu): POST to set_language,
  works without JS, keeps the current page.
- Wrap every existing UI string in translate/gettext. makemessages, write the
  Ukrainian translations (natural Ukrainian, not word-by-word), compilemessages.
- content/<lang>/<slug>.md loader with fallback to en, rendered through markdown + nh3.
  Add content/en/about.md and content/uk/about.md as placeholders, route /about/.
- docs/EDITING.md in Ukrainian: how to change UI text, translations, long pages,
  site name, logo. Plain words, with exact file paths and commands.
- Tests: Accept-Language uk → Ukrainian page; cookie overrides header; unknown → English.
```
**Тобі:** перемкни мову браузера на англійську й назад. Відкрий сайт у приватному вікні.
Прочитай `docs/EDITING.md` і сам зміни один текст українською через `.po` файл.

---

### 4. Вхід через GitHub [PLAN]
```
Task 4: GitHub sign-in with django-allauth. Follow CLAUDE.md.

- GitHub is the only login method. Scopes read:user and user:email only.
- On first login create the User from GitHub data: username (from GitHub login,
  de-duplicated, not reserved), display_name, avatar_url, bio, github_login.
- Signup step: user confirms username and accepts Terms (checkbox, required); store
  terms_version_accepted (from settings) and terms_accepted_at.
- Styled pages: sign in, signup confirmation, sign out confirmation, errors.
- /settings/: edit display name, bio, website, preferred language, theme.
- Header shows avatar menu when signed in.
- Give me exact steps (in Ukrainian) to create a GitHub OAuth App for local dev,
  which callback URL to use, and which env variables to fill.
- Tests: reserved usernames rejected, duplicate login gets a suffix, settings require login,
  a user cannot edit another user's settings.
```
**Тобі:** створи GitHub OAuth App за інструкцією. Зрозумій різницю між Client ID і Client Secret
і чому секрет лежить у `.env`, а не в коді. Перевір, що `.env` справді не потрапив у git:
`git status`.

---

### 5. Профілі
```
Task 5: public profiles. Follow CLAUDE.md.

- /u/<username>/: avatar, display name, bio, website, GitHub link, join date,
  counts (projects, hallmarks earned, followers), list of published projects
  (empty state for now, inviting to add the first project if it's your own profile).
- 404 for unknown or suspended users.
- Meta tags: title, description, Open Graph (uses og-default.png for now).
- Mobile layout first.
- Tests: suspended user → 404; email never appears in the HTML.
```
**Тобі:** подивись свій профіль з телефона. Перевір через «Переглянути код сторінки»,
що твого email там справді нема.

---

### 6. Проєкти: створення і редагування [PLAN]
```
Task 6: projects CRUD. Follow CLAUDE.md sections 5 and 6.

- Models: Project, Tag, Tool (seed a list of common AI coding tools), Screenshot.
- /new/: create project (name, tagline, description markdown with preview, live_url,
  repo full name, tags, built-with tools). Starts as draft.
- Owner pages: edit, publish/unpublish, delete (with confirmation), upload up to 4
  screenshots (rules from section 6), reorder screenshots.
- /u/<username>/<slug>/: project page with plate layout, screenshots, description,
  tags, "Built with (self-declared)" label, owner controls when it's yours.
  Hallmark row shows all hallmarks as not earned for now.
- Profile now lists published projects as plates.
- Tests (important): other users get 404 on drafts and on every edit/delete URL
  (IDOR); markdown with <script> and javascript: links is sanitized; image size and
  type limits enforced; 5th screenshot rejected.
```
**Тобі:** це перший промпт, де найбільше безпеки. Спробуй сам: створи проєкт від одного
акаунта, скопіюй URL редагування, зайди з іншого акаунта (другий GitHub або приватне вікно
з іншим юзером) і встав URL. Має бути 404. Напиши в описі `<script>alert(1)</script>`.
Не має бути алерту.

---

### 7. Перевірка авторства репозиторію
```
Task 7: repo authorship check (Authored hallmark). Follow CLAUDE.md section 2.

- verification/repo.py: given a project and its owner's GitHub token (from allauth),
  call the GitHub REST API for the public repo: confirm it exists and is public,
  whether the owner account owns it, the user's commit count (contributors endpoint),
  first and last commit dates. Store in RepoLink. One repo → one project.
- "Check repository" button on the project edit page, rate-limited (1 per 10 min per
  project). Clear messages for: not found, private, not yours, too few commits,
  GitHub rate limit.
- Handle GitHub API errors and rate limits without crashing.
- Tests with mocked HTTP: owner → authored; contributor ≥10 commits → authored;
  9 commits → not; private repo → not; repo already linked to another project → rejected.
```
**Тобі:** перевір на своєму реальному репозиторії і на чужому публічному.
Розберись, що таке API rate limit і чому запит іде з токеном користувача.

---

### 8. Безпечні запити і перевірка домену [PLAN] (складний, можна Opus на план)
Тут найважливіша для безпеки річ у всьому проєкті: сервер ходить за адресами,
які вводить користувач. Без захисту так зламують сервери (SSRF).

```
Task 8: safe_fetch and domain verification (Live hallmark). Follow CLAUDE.md
sections 2 and 6.

Part 1: verification/net.py::safe_fetch with every rule from section 6. Tests first:
blocks 127.0.0.1, localhost, 10.x, 172.16.x, 192.168.x, 169.254.169.254, ::1,
fc00::/7, 100.64.x, a public URL that redirects to a private IP, ports other than
80/443, non-http schemes, bodies over 512 KB, slow responses. Allows a normal public URL
(mock DNS and HTTP in tests).

Part 2: domain verification.
- Domain is taken from live_url (normalize, strip www for comparison, keep exact host).
- Two methods: DNS TXT record `shipmark-verify=<token>` (dnspython) or
  <meta name="shipmark-verify" content="<token>"> on the homepage (via safe_fetch).
- UI on project edit page: choose method, copyable instructions (Plex Mono, copy
  button in JS), "Verify now" (rate-limited), status display, help for common
  DNS mistakes.
- One verified domain → one project. Store verified_at, last_confirmed_at.
- Management command `reverify_domains`: re-check verified domains older than 30 days;
  on failure remove the hallmark and write AuditLog.
- Tests for both methods, uniqueness, re-verification failure.
```
**Тобі:** прочитай `net.py` повністю, рядок за рядком, з промптом «Explain...» з частини C.
Це найцінніший шматок коду для твого розуміння безпеки. Потім перевір на своєму сайті
horizonnect.dev через meta-тег.

---

### 9. Перевірка, що сайт живий (uptime)
```
Task 9: uptime checks (Steady hallmark). Follow CLAUDE.md sections 2 and 6.

- Management command `check_uptime`: for projects with a verified domain, request
  the live_url via safe_fetch (HEAD, fall back to GET), store UptimeCheck
  (ok = status < 400), at most one check per project per 3 hours, delete checks
  older than 90 days. Process in small batches; one failing site never stops the run.
- Project page: uptime % for 30 days, last check time, a small 30-day strip
  (one cell per day, accessible text alternative).
- docs/DEPLOY_NOTES.md: the cron lines for check_uptime and reverify_domains.
- Tests: 3-hour throttle, pruning, percentage math, Steady rules from section 2.
```
**Тобі:** запусти `python manage.py check_uptime` кілька разів руками і подивись, як
з'являються записи в базі. Зрозумій, що таке cron і навіщо він тут.

---

### 10. Відзнаки (hallmarks) і сторінка «Як працює доказ»
```
Task 10: hallmarks. Follow CLAUDE.md section 2.

- projects/proof.py::compute_hallmarks(project) → list of hallmarks with earned flag,
  earned_at and a one-line reason. Pure function, cached per request.
- Use it everywhere: project page (large hallmarks with tooltips/explanations that also
  work on touch), plates (small), profile counts.
- /how-proof-works/ from content/<lang>/how-proof-works.md (en + uk): what each hallmark
  means, how it's checked, what is self-declared, how it can be lost.
- Tests: every row of the table in section 2, including losing Live after failed
  re-verification and Steady requiring Live.
```
**Тобі:** це момент, коли продукт уперше «оживає». Додай свій реальний проєкт і дотягни
його до трьох відзнак. Якщо тобі самому нецікаво на це дивитись, це важливий сигнал.

---

### 11. Журнал будівництва (build log)
```
Task 11: build log. Follow CLAUDE.md.

- BuildLogEntry: owner adds short updates (≤500 chars, limited markdown: bold,
  italic, links, inline code) and marks one "Launched" milestone (sets launched_at).
- Timeline on the project page, newest first, with relative dates (localized).
- Add/delete entries inline with JS (fetch + CSRF), plain POST fallback without JS.
- Rate limit: 10 entries per day per project.
- Tests: only owner can add/delete; limits; sanitized output.
```
**Тобі:** відкрий DevTools → Network і подивись, який запит іде, коли додаєш запис.
Знайди в JS, де береться CSRF-токен. Це твій перший живий приклад «JS без перезавантаження».

---

### 12. Підписки, лайки і стрічка [PLAN]
```
Task 12: follows, likes, feed. Follow CLAUDE.md.

- Follow/unfollow users, like/unlike projects. static/js/social.js: optimistic UI
  (update instantly, roll back on error), CSRF header, buttons disabled while pending,
  plain POST fallback without JS. Rate limited.
- /feed/: tabs "Following" (projects and build log entries from people you follow)
  and "Latest launches" (recently published or launched projects, everyone).
  Pagination with a "Load more" button (JS) and normal page links (no JS).
- Signed-out visitors see "Latest launches" only.
- No N+1 queries: show me the query count for /feed/ in a test (assertNumQueries).
- Tests: cannot like own project? (decide and explain), unique constraints,
  suspended users' content excluded, rate limits.
```
**Тобі:** постав лайк, вимкни інтернет у DevTools (Offline) і постав ще один.
Кнопка має повернутись назад і показати помилку. Це і є «оптимістичний UI з відкатом».

---

### 13. Бейджі для вставки (головний двигун росту)
```
Task 13: embeddable SVG badges. Follow CLAUDE.md.

- /badge/<username>/<slug>.svg: compact badge with the site mark, project name and
  earned hallmarks. /badge/<username>.svg: profile badge with hallmark count.
- Pure SVG, no external fonts (use system font stack inside SVG), crisp at 1x and 2x,
  readable on light and dark GitHub READMEs.
- Cache-Control: public, max-age=3600. No cookies set on badge responses.
  Unknown/hidden → a neutral "not found" badge (still 200, so READMEs don't break).
- "Embed badge" panel on project and profile pages: Markdown and HTML snippets with
  copy buttons, live preview.
- Tests: hidden project returns neutral badge; no Set-Cookie header; content type.
```
**Тобі:** встав бейдж у README свого реального репозиторію на GitHub і подивись,
як він виглядає у світлій і темній темі GitHub. Кожен такий бейдж буде безплатною рекламою.

---

### 14. Головна сторінка і «Огляд» [PLAN] (можна Opus на план)
```
Task 14: landing and explore. Follow CLAUDE.md section 9.

- Landing (/): the hero is the one bold moment from section 9: a large example plate
  getting its hallmarks struck in sequence; reduced-motion shows final state.
  Then: what Shipmark is in two sentences, how proof works (three hallmarks, short),
  a strip of real recently launched projects (falls back gracefully when empty),
  a clear "Sign in with GitHub" action. Real, specific copy; no filler.
  Signed-in users visiting / are redirected to /feed/.
- /explore/: search by name/tagline (icontains, works on SQLite and Postgres),
  filters by tag, tool and hallmark, sort by newest / most liked / most proven.
  Filters reflected in the URL (shareable), work without JS.
- Open Graph tags for landing, explore, profiles, projects (project uses its first
  screenshot if present).
- Check every width from section 10 and both themes.
```
**Тобі:** покажи головну трьом людям з телефона без пояснень і спитай: «Що це за сайт?»
Якщо не можуть сказати за 10 секунд, перепиши тексти. Це дешевше за будь-який код.

---

### 15. Модерація і красива адмінка [PLAN]
```
Task 15: moderation and admin. Follow CLAUDE.md sections 6 and 11.

- Report model and a "Report" action on projects and profiles (reason select +
  optional details, rate limited, signed-in only).
- django-unfold admin, branded from config/branding.py (logo, name, colors from tokens).
  Sidebar and dashboard exactly as in section 11. Useful list_display, filters, search
  on every model. Admin actions write AuditLog.
- ADMIN_URL from env. In production refuse to start if ADMIN_URL is "admin/".
- Suspending a user hides their projects everywhere (feed, explore, badges, profile).
- Tell me in Ukrainian how to create the superuser and open the admin.
- Tests: non-staff cannot reach admin; suspend hides content; actions are logged.
```
**Тобі:** зайди в адмінку і зроби весь цикл: поскаржся на проєкт з другого акаунта,
знайди скаргу, сховай проєкт, перевір, що він зник зі стрічки і що бейдж став нейтральним.

---

### 16. Юридичні сторінки, видалення акаунта, експорт даних
```
Task 16: legal pages and account rights. Follow CLAUDE.md section 12.

- First, list in docs/DATA_INVENTORY.md every piece of personal data the code stores
  or processes: field, source, purpose, retention, who can see it, third parties (GitHub).
- Then write content/en and content/uk: privacy.md, terms.md, cookies.md based strictly
  on that inventory. Contact = brand.CONTACT_EMAIL, owner = brand.LEGAL_OWNER_NAME.
  Add a visible note at the top of each: "Draft, last updated <date>".
- Footer links to all three. Terms version constant in settings; bumping it asks
  users to accept again on next visit.
- /settings/: "Download my data" (JSON of profile, projects, build log, likes, follows)
  and "Delete account" (type username to confirm, explains what happens, irreversible,
  writes AuditLog, anonymizes reports made by the user).
- Tests: export contains only the user's own data; deletion removes projects and
  frees the username; terms version bump forces re-acceptance.
```
**Тобі:** прочитай `DATA_INVENTORY.md` уважно. Якщо там є щось, що ти не хочеш збирати,
прибери з коду, а не з тексту. Перед публічним запуском покажи ці сторінки юристу
або хоча б у юридичній спільноті: це чернетка, а не юридичний документ.

---

### 17. Ще мови
```
Task 17: more languages. Follow CLAUDE.md section 8.

- Add pl, de, es, fr, pt-br. Never Russian.
- Translate all .po files and content/*.md (about, how-proof-works, legal pages)
  naturally for each language. Keep product terms consistent (glossary at the top of
  docs/EDITING.md: hallmark, plate, build log, project, verify).
- Mark legal pages in new languages: "Translation for convenience; the English version
  prevails."
- Check that nothing overflows with longer German words at 360px.
- Tests: each language served via Accept-Language.
```
**Тобі:** попроси знайомого поляка чи німця глянути хоч одну сторінку. Машинний переклад
часто граматично правильний, але звучить неприродно.

---

### 18. Перевірка на всіх пристроях і доступність
```
Task 18: cross-device, accessibility and performance pass. Follow CLAUDE.md section 10.

- Go through every page at 360, 390, 768, 1024, 1280, 1440 widths, both themes.
  List problems first, then fix them.
- Check: iOS rules from section 10, keyboard-only navigation, focus order, contrast,
  form errors read by screen readers, reduced motion, no horizontal scroll anywhere,
  images with width/height, no layout shift from fonts.
- Give me a manual checklist in Ukrainian for my own testing on a real Android phone,
  an iPhone (borrowed), Firefox and Chrome on Linux, and Windows.
I will paste screenshots of problems after this.
```
**Тобі:** iPhone у тебе може не бути. На Linux можна поставити GNOME Web (Epiphany):
він працює на WebKit, тому показує багато тих самих проблем, що й Safari. Але на справжньому
iPhone все одно перевір хоч раз перед запуском: позич у друга на 10 хвилин.

---

### 19. Аудит безпеки
```
Task 19: security audit before launch. Follow CLAUDE.md section 6.

- Run python manage.py check --deploy with prod settings and fix everything.
- Run pip-audit and report vulnerable packages.
- Review every view: auth required where needed, ownership checks, rate limits,
  CSRF, safe_fetch is the only outbound HTTP, nh3 on every user markdown,
  no user data in logs, no email in HTML, suspended users blocked.
- Production settings: secure cookies, HSTS, SECURE_PROXY_SSL_HEADER, CSP-friendly
  templates (no inline event handlers), X-Frame-Options, Referrer-Policy.
- Output a table: issue, severity, file, fix applied or not. Fix high and medium.
```
Після цього також запусти вбудовану `/security-review` у Claude Code.
**Тобі:** пройди таблицю сам. Для кожного пункту, який не розумієш, використай промпт
«Explain...». Ти казав, що хочеш сам відповідати за безпеку: ось тут це і відбувається.

---

### 20. Готовність до продакшну (без деплою)
```
Task 20: production readiness. Follow CLAUDE.md.

- prod settings: PostgreSQL via DATABASE_URL, whitenoise for static files with
  compressed manifest storage, media storage on disk with a clear note on moving to
  S3-compatible storage later, gunicorn config, structured logging to stdout.
- Verify migrations work on PostgreSQL: give me exact commands to install Postgres
  locally on Pop!_OS, create a db, and run the project against it.
- docs/DEPLOY_NOTES.md: env variables list, collectstatic, migrate, cron lines,
  backups (pg_dump daily), how to rotate SECRET_KEY, a pre-launch checklist.
Do not choose a hosting provider and do not deploy. We will do that together later.
```
**Тобі:** запусти проєкт на локальному Postgres. Якщо щось працювало на SQLite і зламалось
на Postgres, краще дізнатись це зараз, а не після запуску.

---

## Частина E. Після MVP (не промпти, а план)

1. **Деплой.** Вибір хостингу, домен, HTTPS, Postgres, cron. Окрема розмова.
2. **Перші 50 будівельників.** Не реклама, а ручна робота: пишеш людям, які публічно будують
   з ШІ (X, Reddit, Indie Hackers, українські Telegram-спільноти), пропонуєш додати проєкт
   і поставити бейдж. Твій власний профіль на сайті і пости про те, як ти його будуєш, це
   теж маркетинг.
3. **Метрика, яка вирішує все:** скільки людей повертаються в стрічку через тиждень після
   реєстрації. Якщо майже ніхто, нові фічі не допоможуть, треба лагодити причину повертатися.
4. **Тільки потім:** відзнака «Used» (реальні користувачі через інтеграції), челенджі,
   сторінка для компаній, які шукають людей.
