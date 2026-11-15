# Перевірка безпеки перед запуском

Дата: 2026-11-15. Гілка `launch-1`. Перевірка локального коду й синтетичних тестових даних; production-ресурсів не створено. Жоден інструмент або цей огляд не доводить, що сайт неможливо зламати.

## Знахідки

| ID | Рівень | Доказ до виправлення | Виправлення | Регресійний тест і стан |
|---|---|---|---|---|
| L1 | medium | `config/jsonlog.py:23,30`: stdout передавав повідомлення й traceback без очищення. `config/errorlog.py:57,95`: маска охоплювала лише `/u/` і `/badge/`, а structured path міг містити IP або ім'я в `/follow/`, `/report/`, `/mod/act/user/` | Спільне очищення повідомлень, traceback і structured path; маска всіх маршрутів з іменем користувача | `config.test_launch_security.LogPrivacyTests`: до зміни 7 невдалих subtests; після — OK. Наявні JSON/exception/error-page тести збережено |
| C1 | medium | `config/settings/prod.py:13,22`: порожній, короткий або відомий dev SECRET_KEY, а також відомий dev BAN_HASH_KEY не зупиняли `check` | Додано перевірки під час імпорту production settings: SECRET_KEY ≥50 символів, ≥5 різних, без insecure-prefix; відомий dev BAN_HASH_KEY відхиляється поряд з наявними перевірками довжини/відмінності | `config.test_launch_secrets.ProductionSecretTests`: до зміни 4 + 1 невдалих subtests; після — OK |
| R1 | low | Django DatabaseCache не видаляє рядок лише через прострочення; негативний TTL залишав 3 рядки замість 2. У production ключ може містити солений IP-хеш | Щоденний `prune_support` фізично видаляє прострочені рядки всіх налаштованих DatabaseCache; чинні й безстрокові рядки зберігаються. Реалізовано в етапі 3, `267c27f` | `support.test_cache_retention.CacheRetentionTests`: спочатку FAIL (3 ≠ 2), після — OK; повтор команди безпечний |
| P1 | medium | Під час Heroku preparation: `support/antispam.py:56` брав першу адресу X-Forwarded-For. При моделі довіри «прямий router додає адресу в кінець» підставлений клієнтом prefix міняв IP-хеш і дозволяв обходити anonymous support/people limits | Лише для явно довіреного HTTP_X_FORWARDED_FOR беремо праву адресу; single-value X-Real-IP і REMOTE_ADDR збережено. Це політика прямого router без Cloudflare proxy; фактичний порядок/довіру треба перевірити після deploy | `support.test_proxy_ip.ProxyIpTests`: до зміни FAIL (підставлена адреса замість справжньої), після — OK; перевіряються support і people keys та ігнорування header без explicit trust |

Підсумок підтверджених знахідок: high 0, medium 3, low 1; усі чотири виправлено. Це кількість виявлених проблем, не оцінка ймовірності всіх можливих атак.

## Що перевірено

| Ділянка | Доказ / результат | Межа перевірки |
|---|---|---|
| Відомі вразливості залежностей | `pip-audit -r requirements/prod.txt`: 29 пакетів, 0 відомих вразливостей; dev: 47 пакетів, 0. JSON у локальних `logs/launch/audit-prod.json`, `audit-dev.json` | База advisory доступна на час запуску; це не аналіз невідомих вразливостей. Після додавання S3-залежностей повторено production audit: 36 пакетів, 0 відомих вразливостей |
| Production settings | `manage.py check --deploy` з production settings і синтетичними env: без зауважень. Справжніх ключів не потрібно й не використано | Не перевірено налаштування майбутнього Heroku app, DNS, TLS чи зовнішніх сервісів |
| CSRF | Middleware увімкнено, `csrf_exempt` у коді застосунків немає. `WriteCsrfTests` перевіряє 47 POST-маршрутів із `Client(enforce_csrf_checks=True)`: без token — 403 до дії, також для signed-in користувача | OAuth callback захищається state у allauth; зовнішню сторону flow не проходили |
| HTTPS, cookies, headers | SSL redirect, secure session/CSRF cookies, HttpOnly session, SameSite=Lax, proxy SSL header, DENY frame, same-origin referrer, nosniff. HSTS початково 3600 s; preload/subdomains лише заголовки, домен не реєструється у preload list. Sessions — Django default 14 днів, `clearsessions` треба запускати щоденно | Після налаштування хостингу перевірити реальні заголовки й довіру proxy |
| CSP | Звичайні сторінки: scripts тільки self, без unsafe-inline/eval; object-src none, frame-ancestors none. Inline script/style/handlers заборонені тестами `config.tests.SecurityHeadersTests` | Адмінка виключена з page CSP через inline код django-unfold; доступ тільки персоналу. Це наявний задокументований виняток; додаткові ресурси не дозволялися |
| Admin URL і вхід | Адреса з env, `/admin/` у production відхиляється. Login throttle перевіряється `AdminLoginThrottleTests`; ключ від truncated SHA-256 username, без IP | Це додатковий бар'єр, не заміна сильному паролю й обмеженню staff-доступу |
| IDOR: проєкти, screenshots, build log | `projects/views.py:50`: спільний owner guard; чужі об'єкти — 404. Вкладені об'єкти отримуються через relation власного проєкту. Регресії в `projects/tests.py`, `test_screenshots.py` | Перевірка коду й локальних запитів, без зовнішнього pentest |
| IDOR: спільнота, санкції, support | Thread/reply guards у views/services; moderator/superuser rules і Notice owner tests у moderation. Support attachment (`support/views.py:77`) — active staff з окремим permission, інакше 404; download no-store/nosniff/sandbox | Не змінювали моделі, міграції, hallmarks, grants чи moderation rules |
| XSS | `projects/rendering.py:38`: Markdown без raw HTML + nh3 allowlist, тільки дозволені tags/attributes/schemes, nofollow ugc noopener. Templates escape user text; inline SVG читається лише з довірених static шляхів | Власні sanitizer/dependency tests, без нового browser fuzzing corpus |
| Redirects | Login/Terms/social/language/error back-link перевіряють allowed host/scheme; відповідні malicious-next тести збережені | GitHub redirects усередині allauth окремо потребують зовнішнього огляду |
| SSRF | Всі user URL downloads через `verification/net.py::safe_fetch`: IP pinning після DNS, блок private/loopback/CGNAT/IPv6, перевірка redirect, ports 80/443, timeout/body/decompression caps. GitHub API client має фіксований origin, перевірені path parts, redirect off; довільної user URL там немає | Усі мережеві атаки в тестах замокані; live DNS rebinding чи мережу хостингу не тестували |
| Uploads | `projects/images.py:21`: content перевіряється Pillow, ≤5 MB, ≤25M pixels, re-encode WebP, metadata removed, random names. Support text перевіряється як текст з byte cap, не лише extension; download attachment замість inline HTML | S3 storage policy/IAM і фактична приватність об'єктів перевіряються вручну перед deploy |
| Rate limits | Код і тести sign-in/admin, support/session/user/IP-hash, uploads, reports, search, social writes, project/domain/repo та community limits. Production cache спільний між workers; query text не зберігається | Перевірки послідовні. DatabaseCache increments не дають гарантії атомарної квоти під паралельним навантаженням; support також перевіряє й рахує окремо. Обхід/похибка лімітів при конкуренції лишається ризиком для зовнішнього навантажувального огляду; ці ліміти не можна вважати жорсткими квотами |
| Enumeration | Профілі й зайняті username публічні за задумом. Email/password signup вимкнений; GitHub email не публікується. People search обмежений і не повертає private поля | Публічні username можна перевіряти по одному; rate limits лише зменшують масовий збір |
| Logs, errors, secrets | Немає print/TODO/DEBUG=True у security runtime code; знайдений print — лише текст інструкції генерації ключа. `.env`, DB, logs/media/staticfiles не tracked. Помилки production не показують технічні traceback; власні журнали scrubbed, raw IP/UA/query/POST не записуються | Heroku router містить IP за погодженою політикою до приблизно тижня; реальний доступ/retention власник перевіряє перед запуском. Sanitizer не є універсальним DLP для довільних майбутніх повідомлень |

## Перевірки

- `manage.py check`, `check --deploy` і `git diff --check` — без зауважень.
- Цільові logger/error regressions: 27 тестів OK; після перевірок ключів — 105 тестів `config support` OK.
- Повний набір: 1153 тести OK (70,7 с), включно з permission/XSS/SSRF/upload/redirect/rate-limit перевірками. Старий admin URL fixture отримав різноманітний синтетичний ключ; його assertions збережено.
- Статичний пошук виконано лише в tracked runtime-файлах без читання секретів `.env`; реальні credentials у звіт або коміти не потрапляють.

## Not covered

- Penetration testing проти live-сервера.
- Огляд GitHub OAuth flow незалежною людиною, реальний consent/callback та конфігурація production OAuth App.
- Юридичний огляд текстів і фактичних договорів/retention зовнішніх обробників.
- Load testing, зокрема конкурентні ліміти й кілька Heroku workers, виснаження DB/cache/storage та захист від DDoS.
- Реальна PostgreSQL, S3/IAM/bucket policy, SMTP, відновлення backup, DNS/TLS: ресурсів і credentials тут немає; вони не створювалися.

Перед широким публічним запуском рекомендовано незалежний security review і перевірку відкритого ризику конкурентних rate limits під навантаженням. Локальна підготовка не замінює ці роботи.
