# План: features-1 (етап 0), 2026-11-12

Бриф: `docs/promts/features_master.md`. Гілка `features-1`. Міграції лише додають поля/таблиці, кожна з `reverse`.

## 1. Зміни моделей
**accounts**
- `UserBadge(user FK, kind official|moderator, granted_by FK null, granted_at, note)`, unique (user, kind).
  Пише/знімає лише superuser (inline на User; для staff inline read-only). Кожна зміна → AuditLog `badge.granted/revoked`.
- `User` + поля: `headline` (≤80), `about` (markdown ≤1000), `location` (≤60), `status` (none/open_to_work/
  open_to_collaborate/hiring/building_in_public), `avatar` (ImageField), `avatar_source` (none/upload/github),
  `cover` (ImageField), `skills` M2M → `projects.Tag` (≤10, перевірка у формі).
- `ProfileLink(user, kind website|github|x|linkedin|telegram|other, url, order)`, ≤6. `PinnedProject(user, project, order)`, ≤3,
  лише свої опубліковані.
- Дані: `bio` копіюється в `about`, `website` → `ProfileLink(website)`; старі поля лишаються до окремого прибирання.
- Міграція: системний акаунт `shipmark` (unusable password, `is_active=True`, але вхід блокує адаптер) + official badge.
- `usernames.py`: + shipmark, official, moderator, mod, team, staff, news. Display name "Shipmark", "Shipmark Team",
  "Shipmark Official" (без регістру, з нормалізацією пробілів) заборонено всім, крім власників official badge.

**news** (новий app): `NewsPost(title, slug unique, body markdown, published_at null=чернетка, pinned, created_by FK internal,
created_at, updated_at)`. Автор на сайті завжди "Shipmark" (системний акаунт), `created_by` видно лише в адмінці.

**moderation**
- `Report`: статуси open/in_review/resolved/dismissed (існуючі resolved лишаються), `resolution_note`, нова ціль
  `log_entry` FK (SET_NULL), `target_owner` FK (власник цілі на момент скарги, для історії), `source` user|moderator.
  CheckConstraint "рівно одна ціль" розширюється; unique "одна відкрита скарга" — для статусів open+in_review.
- `Sanction(user, kind mute|ban, reason, starts_at, expires_at null=назавжди, issued_by, revoked_at, revoked_by, report null)`.
  Активна = `starts_at <= now < expires_at` (або null) і `revoked_at` null. Рахується під час запиту, без cron.
- **projects** `Project.Status` + `removed`; поля `removed_reason`, `removed_at`, `removed_by`; + `published_at`
  (перша публікація; backfill з `launched_at`/`created_at`) для рейтингу.

Одне джерело прав: `accounts/roles.py`: `is_official(u)`, `can_moderate(u)` (= moderator badge або superuser),
`active_sanction(u)` (кеш на request), `can_write(u)` (не muted/banned/suspended). Усі views і шаблони беруть лише звідси.
`is_suspended` лишається як є (ручне призупинення superuser'ом = безстрокове, діє як ban).

## 2. URL map (нове)
| URL | Хто | Що |
|---|---|---|
| `/news/`, `/news/<slug>/` | усі | список (pinned зверху), стаття, OG |
| `/feed/?tab=foryou\|following\|news&tag=&tool=&mark=&range=&sort=&page=` | усі (following: signed in) | стрічка |
| `/mod/` (`?status=&kind=&reason=`) | can_moderate | черга, лічильник відкритих |
| `/mod/reports/<id>/` (GET + POST дія) | can_moderate | скарга, об'єкт, історія власника, дії |
| `/mod/act/<project\|user\|log>/<id>/` | can_moderate | "Moderate" під час перегляду: та сама форма, створює/знаходить Report |
| `/report/log/<user>/<slug>/<pk>/` | signed in, can_write | скарга на запис build log |
| `/settings/` (+ POST `/settings/avatar/`, `/settings/avatar/github/`, `/settings/avatar/remove/`, `/settings/cover/…`) | власник | профіль |
| `/u/<user>/?tab=projects\|log\|about` | усі | вкладки профілю (query, бо `/u/<user>/<slug>/` = проєкт; slug "log" зламав би шлях) |
| `/banned/` | забанений | причина, дата кінця, контакт, вихід |
Публічних write-ендпоїнтів для news немає.

## 3. Матриця прав
| Дія | Анонім | User | Muted | Banned | Moderator | Staff | Superuser |
|---|---|---|---|---|---|---|---|
| Читати публічне, news | так | так | так | ні (сторінка /banned/) | так | так | так |
| Свої налаштування, експорт, видалення акаунта | — | так | так | експорт/видалення так | так | так | так |
| Створити/редагувати/публікувати, лог, лайк, follow, скарга, upload | ні | так | **ні (403)** | ні | так | так | так |
| /mod/, дії модерації (з причиною, ліміти) | 404 | 404 | 404 | — | так | 404 без badge | так |
| Mute ≤7 дн, ban ≤14 дн (`MOD_MAX_*` у settings) | — | — | — | — | так | — | без ліміту |
| Діяти на superuser / official / moderator / себе | — | — | — | — | **ні (403)** | — | так (не на себе) |
| Безстрокові санкції, revoke, restore, purge | — | — | — | — | ні | ні | так |
| Видати/зняти badge | — | — | — | — | ні | ні (read-only) | так (адмінка, команда) |
| NewsPost у адмінці | — | — | — | — | ні | з permission `news.*` | так |
Чужі приватні об'єкти → 404; провал ролі → 403. Rate limit на дії модератора (наприклад 30/год).
Ban: middleware після auth; активна сесія → `/banned/` (дозволені лише legal, logout, export, delete). Вхід через GitHub
для забаненого → теж `/banned/`. Проєкти забаненого зникають зі списків/стрічки/explore/бейджів (mute не ховає).

## 4. Формула "For you" (SQL, SQLite + PostgreSQL)
`score = (2·likes + Least(owner_followers, 50)/5 + 3·marks) × decay`, де `decay` — Case/When за віком `published_at`:
≤24 год ×8, ≤3 дні ×4, ≤7 днів ×2, ≤30 днів ×1, старше ×0.5 (без `POWER`/`LN`: у SQLite вони не гарантовані).
`marks` = SQL-анотації Exists для Repo owner / Domain verified / Steady поруч із `compute_hallmarks` у `projects/proof.py`
(той самий принцип, що `with_uptime()`), + тест паритету "SQL = compute_hallmarks" на наборі фікстур. Сортування:
score, потім `published_at`, `id`. Popular / Newest перемикає `sort`. Документується в `docs/DESIGN.md` або `FEATURES_STATUS.md`.
Картка = проєкт; build-log оновлення в For you показується snippet'ом на картці (останнє за період), у Following —
окремими записами хронологічно, як зараз. Removed / banned / suspended / hidden виключено одним менеджером `Project.objects.public()`.

**Explore vs Feed (пропозиція):** фільтри (tag/tool/mark) — один спільний парсер у `pages/filters.py` для обох сторінок.
Feed = "що нового" з рейтингом, Explore = пошук за назвою + сітка. Не зливаю й не видаляю без твого рішення.

## 5. Ризики
- **N+1** на збагачених картках (обкладинка, бейджі власника, followers, like-стан, snippet): Prefetch з обмеженими
  queryset'ами + assertNumQueries для 1 і 20 карток.
- **Розходження SQL-оцінки marks з `compute_hallmarks`** → тест паритету; mark на сторінці завжди з `compute_hallmarks`.
- Перевірка санкції на кожен запит = +1 запит → кешую на `request` (і в `user` об'єкті); тести з assertNumQueries оновлюю свідомо.
- Старі Report з `resolved` і нові unique-обмеження: міграція перевіряється на копії `db.sqlite3`.
- Реальні акаунти з новими зарезервованими іменами: у dev-БД таких немає; у прод — міграція не перейменовує, лише
  забороняє нові (і пише попередження в лог).
- Системний акаунт `shipmark` не повинен з'являтися в "хто читає", follow, стрічці як автор проєктів, у видаленні.
- Обрізка аватарки/обкладинки: великі PNG → обмеження пікселів (`Image.MAX_IMAGE_PIXELS`) у тому ж Pillow-конвеєрі.
- GitHub-аватар через `safe_fetch`: ліміт 512 KB може бути замалим для деяких → беремо `?s=512` (JPEG, зазвичай <100 KB).
- Скриншоти (баг I): у формі редагування окрема форма "Upload screenshot" (`templates/projects/form.html:123`) — головний
  підозрюваний, але причину підтверджую тестом на етапі 1, не здогадкою.
- 7 мов: обсяг нових рядків великий (модерація, профілі, стрічка); переклади роблю в кожному етапі, не в кінці.
- Етап 5 (дизайн-прохід усіх сторінок) — найбільший; може знадобитись розбити на 5a/5b.
- Конфлікт із DESIGN.md: бриф вимагає radius 10px на кнопках і градієнтний бордер. Це свідома зміна правил
  "radius 0, no gradients" → оновлю DESIGN.md і CLAUDE.md §9 у етапі 5.

## 6. Відкриті питання до тебе
1. `is_suspended`: лишити як "безстроковий ban від superuser'а" (мій вибір) чи мігрувати в Sanction і прибрати?
2. `bio` (280) і нове `about` (1000): копіюю bio → about і показую лише about. Добре?
3. Skills: M2M до наявних `Tag` (спільний словник, можна фільтрувати) — чи окремий вільний список?
4. Ліміти модератора: mute ≤7 днів, ban ≤14 днів, 30 дій/год — підходять?
5. Explore: лишити окремою сторінкою пошуку зі спільними фільтрами (моя пропозиція) чи злити у Feed?
6. Скарга модератора "під час перегляду": видно reporter = модератор лише в /mod/ і адмінці (користувач не бачить). Ок?
7. "Purge" removed-проєкту: остаточне видалення + файли, лише superuser, AuditLog лишається. Ок?
8. Ban: дозволити забаненому експорт і видалення акаунта (GDPR-право). Я так і роблю, якщо не заперечиш.
9. `LEGAL_OWNER_NAME` і `CONTACT_EMAIL` (`config/branding.py`) усе ще заглушки — потрібні реальні значення до запуску.
10. H (repo cooldown): у git log окремого коміту не знайшов; перевірю код на етапі 6 і зроблю, якщо треба.
