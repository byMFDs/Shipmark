# Запуск на Heroku: ручна інструкція

Підготовлено локально 2026-11-15. Ця сесія не створювала ресурсів, не надсилала код і не виконувала deploy. Нижче — наступні дії власника після окремого рішення про запуск. Команди виконуй із кореня проєкту; `APP_NAME` заміни власною назвою app.

## 1. Перед створенням ресурсів

- Переглянь `docs/SECURITY_REPORT.md` і `docs/LAUNCH_LEGAL_CHANGES.md`; перед широким запуском замов незалежний огляд безпеки й юридичний огляд.
- Вибери S3-сумісного провайдера та регіон. Створи приватний bucket; заборони anonymous/public read і listing, включно з префіксом `support/`. Сайт використовує `media/` для зображень і `support/` для приватних вкладень.
- Обидва префікси приватні. Зображення на публічних сторінках мають підписані URL зі строком 3600 секунд. Вкладення підтримки не мають URL: застосунок читає їх із S3 й віддає через staff view після перевірки permission.
- Створи окремі credentials лише для цього bucket: list/read/write/delete потрібних префіксів, без керування акаунтом. Не вмикай public website hosting або access-log archive. Перед зміною політики журналів онови Privacy.
- Використай HTTPS endpoint без path/query/userinfo. Застосунок використовує path-style addressing і S3 v4 signatures; перевір сумісність обраного провайдера. Не додавай wildcard/CDN у CSP: точний endpoint origin додається до img-src автоматично.
- Якщо переносиш наявні файли: збережи відносні імена, додавши `media/` перед screenshots/avatars/covers/community, а приватні файли перенеси під `support/`. Нічого не видаляй зі старого сховища до перевіреного перенесення й backup.

## 2. Heroku app і add-ons

1. Створи app в обраному регіоні через Dashboard або `heroku create APP_NAME`.
2. Додай **Heroku Postgres** і **Heroku Scheduler**. Тариф, доступність і вартість вибери в акаунті; їх тут не перевіряли. PostgreSQL add-on надає `DATABASE_URL` автоматично.
3. Увімкни maintenance mode до першого відкриття для відвідувачів: `heroku maintenance:on -a APP_NAME`.
4. Використай Python buildpack. Кореневий `requirements.txt` включає `requirements/prod.txt`; `.python-version` фіксує Python 3.12. Buildpack має виконати Django `collectstatic`: **не** встановлюй `DISABLE_COLLECTSTATIC`.
5. Усі змінні нижче налаштуй **до першого build**: production settings вимагають S3 і секрети також під час collectstatic/release. `Procfile` запускає web через Gunicorn і release через `python manage.py migrate --noinput`. Коли є Heroku `PORT`, Gunicorn слухає `0.0.0.0` на цьому порту; локально без PORT — `127.0.0.1:8000`.

## 3. Змінні середовища

Це перелік імен із порожніми місцями, а не готові значення для копіювання. Порожні обов'язкові значення зупинять запуск. Не записуй secrets у git, issue, screenshot або log.

```dotenv
DJANGO_SETTINGS_MODULE=
SECRET_KEY=
BAN_HASH_KEY=
ADMIN_URL=
ALLOWED_HOSTS=
CSRF_TRUSTED_ORIGINS=
SITE_URL=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_API_TOKEN=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=
AWS_S3_ENDPOINT_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
SUPPORT_INBOX_EMAIL=
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=
DEFAULT_FROM_EMAIL=
CLIENT_IP_HEADER=
COMMUNITY_ENABLED=
SECURE_HSTS_SECONDS=
SECURE_HSTS_INCLUDE_SUBDOMAINS=
SECURE_HSTS_PRELOAD=
WEB_CONCURRENCY=
LOG_LEVEL=
```

- `DJANGO_SETTINGS_MODULE`: `config.settings.prod`. `SITE_URL`: `https://shipmark.me`.
- `SECRET_KEY`: власний випадковий production key, мінімум 50 символів, не dev key. `BAN_HASH_KEY`: інший випадковий ключ, мінімум 32 символи. Зберігай їх у захищеному сховищі; BAN_HASH_KEY не обертай, поки діють бани. Startup відхиляє слабкий SECRET_KEY, відомі dev keys та відсутній S3.
- `ADMIN_URL`: власний непублічний шлях; `admin/` відхиляється. Це додатковий бар'єр, а не пароль.
- `ALLOWED_HOSTS`: `shipmark.me`, `www.shipmark.me` і **точний фактичний** Heroku app hostname зі сторінки app, через кому, без схем. Не використовуй `*` або всі `herokuapp.com`. `CSRF_TRUSTED_ORIGINS`: ті самі три адреси зі схемою `https://`. Canonical домени є також у production defaults; hostname app потрібно додати вручну.
- П'ять `AWS_*` змінних із переліку — обов'язкові; default disk fallback у production відсутній. `AWS_S3_REGION_NAME` — значення, яке вимагає обраний провайдер. Endpoint, bucket і credentials мають належати одному сховищу.
- `DATABASE_URL` і `PORT` задає Heroku; не замінюй їх порожніми ручними значеннями. Схема `postgres://` підтримується.
- `GITHUB_API_TOKEN`: для публічних repo checks, без доступу до приватних репозиторіїв. OAuth scopes — лише `read:user` і `user:email`; токен OAuth користувача не зберігається.
- SMTP потрібен для сповіщень команді про support messages. Налаштуй TLS/порт за документацією свого поштового провайдера. Звернення зберігається й при помилці SMTP; перед запуском перевір доставку.
- Для Heroku використовуй `CLIENT_IP_HEADER` = `HTTP_X_FORWARDED_FOR` тільки за прямого трафіку через довірений Heroku router. Cloudflare при запуску — DNS-only. Перевір фактичний порядок адрес і неможливість підмінити адресу в заголовку; не довіряй такому заголовку при прямому доступі до Gunicorn.
- `COMMUNITY_ENABLED` залиш unset або false: production default false перевірено тестом. Не вмикай спільноту до її ручного checklist у DEPLOY_NOTES.
- Початковий `SECURE_HSTS_SECONDS` — 3600; після перевіреного HTTPS можна збільшити. Не подавай домен у preload list до окремого рішення. HTTPS за router визначає `SECURE_PROXY_SSL_HEADER`; власний proxy не додавай.
- `LOG_LEVEL` — INFO; stdout JSON очищено від IP/email/секретів та імен у маршрутах. Heroku routing logs містять IP за погодженою політикою: короткий потік приблизно до тижня, доступ власника, без drain/add-on. Перевір фактичні retention і доступ у своєму акаунті до запуску. Не вмикай довгострокове журналювання без оновлення Privacy.

## 4. Production GitHub OAuth App

1. У своєму GitHub акаунті створи окремий production OAuth App.
2. Homepage — `https://shipmark.me`; callback **точно** `https://shipmark.me/accounts/github/login/callback/`.
3. Client id і client secret встанови в Heroku config vars. Не використовуй production secret у локальних fixture.
4. Перший реальний sign-in перевір після HTTPS і DNS. Локальні тести не замінюють перевірку consent/state/callback незалежною людиною.

## 5. Домени й DNS

1. Додай обидва домени до Heroku app: `heroku domains:add shipmark.me -a APP_NAME` і `heroku domains:add www.shipmark.me -a APP_NAME`.
2. Через `heroku domains -a APP_NAME` скопіюй **Heroku DNS target** для кожного домену. Це ціль для DNS, а не IP і не звичайна адреса app.
3. У DNS-провайдера створи CNAME для `www` на його target. Для кореня `shipmark.me` використовуй CNAME flattening / ALIAS / ANAME за можливостями провайдера; не вигадуй A record із мінливим Heroku IP. У Cloudflare apex CNAME працює через flattening.
4. У Cloudflare обидва записи залиш **DNS-only**, без proxy. Збережи MX/TXT записи пошти й перевірок.
5. Налаштуй сертифікат/керований HTTPS для обох доменів у Heroku. Перевір сертифікат, canonical links і HTTPS redirect, перш ніж відкривати сайт.

## 6. Перший build і release

1. Локально встанови production і dev requirements та виконай tests, `check --deploy`, pip-audit. Поточний код уже перевірено на SQLite; PostgreSQL перед launch потребує окремого тестового прогону.
2. Після окремого рішення про deploy підключи Heroku remote: `heroku git:remote -a APP_NAME`.
3. Надішли погоджений commit: `git push heroku launch-1:main`. **Ця команда в підготовчій сесії не виконувалася.**
4. У build log перевір успішний `collectstatic`; у release log — успішний migrate. WhiteNoise використовує compressed manifest і hashed URLs; пропущений static файл має бути виправлений, а не прихований.
5. До вимкнення maintenance: `heroku run "python manage.py createcachetable" -a APP_NAME`. Database cache потрібен усім workers; release виконує тільки migrate.
6. Виконай `heroku run "python manage.py check --deploy" -a APP_NAME`, створи власного superuser через `createsuperuser`, перевір приватний admin URL. За потреби даних з попереднього запуску виконай one-time кроки DEPLOY_NOTES; dev/demo DB у production не переносити.
7. `heroku run "python manage.py send_test_email" -a APP_NAME`: перевір командний support inbox. Не надсилай пароль або ключ у форму підтримки.
8. Переконайся, що Scheduler і backup налаштовані, потім `heroku maintenance:off -a APP_NAME` і пройди список нижче.

## 7. Heroku Scheduler

Scheduler має лише кожні 10 хвилин, щогодини та щодня. Усі команди використовують production env із app; час вибери в UTC, рознеси щоденні роботи. Не став weekly schedule: його немає.

| Команда | Частота | Що робить |
|---|---|---|
| `python manage.py check_uptime` | кожні 10 хвилин | Перевіряє лише проєкти, для яких настав час (внутрішнє вікно близько 3 годин), видаляє checks старші 90 днів |
| `python manage.py reverify_domains` | щодня | Перевіряє домени, яким настав строк |
| `python manage.py reverify_repos` | щодня | Наявна `due_links` пропускає звичайний повтор до 7 днів; pending/needs-recheck обробляються раніше. Цю логіку вже реалізовано, не змінювали |
| `python manage.py prune_bans` | щодня | Прибирає прострочені ban hashes |
| `python manage.py prune_support` | щодня | Прибирає закриті звернення старші 12 місяців із файлами та фізично видаляє прострочені database-cache rows, зокрема IP-хеші |
| `python manage.py clearsessions` | щодня | Фізично прибирає прострочені sign-in sessions |
| `python manage.py community_daily` | щодня | Прибирає reply notifications після 90 днів і перераховує community counters; безпечно з flag off |

Запусти кожну команду один раз вручну й перевір результат. Scheduler не гарантує точний час: стеж за невдалими/пропущеними jobs та не запускай дублікати довгої перевірки паралельно.

## 8. Backup і перевірка запуску

- Налаштуй щоденні копії PostgreSQL, медіа й приватних support attachments; усі копії, зовнішні архіви та noncurrent object versions — не довше погоджених **14 днів**. Lifecycle для backup не має видаляти чинні зображення після 14 днів. Перевір правила й план провайдера, можливість видалення старих копій та один справжній restore. Локальний код не забезпечує retention зовнішніх backup.
- Перевір sign-in із GitHub, створення й публікацію проєкту, завантаження та заміну зображення. Зображення має пережити перезапуск dyno; signed S3 URL має відкриватися, unsigned object URL — відхилятися.
- Надішли support message з attachment. Персонал з permission може завантажити його; signed-out, звичайний користувач і прямий unsigned S3 URL доступу не мають. Перевір видалення файлу після видалення звернення.
- Відкрий About, Privacy, Terms, Cookies і Proof сімома мовами; перевір контакт, логотип у header/footer, favicon і кастомну 404.
- Перевір власні/чужі drafts і edit URLs, export/delete test account, logout, CSRF, language/theme, console без CSP errors.
- На справжніх iPhone та Android перевір меню, форми, upload, клавіатуру, safe area й sticky елементи у світлій/темній темах. Firefox screenshots не перевіряють Safari.
- Підтвердь, що community недоступна при false, `/admin/` не відкривається, власні logs очищені, а Heroku router retention/access відповідають Privacy.

Не перевірено в цій сесії: фактичні Heroku/PostgreSQL/S3/SMTP/OAuth/DNS/TLS, backup restore, провайдерські тарифи й дозволи. Зовнішніх ресурсів не створено.
