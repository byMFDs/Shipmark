# Polish-3: legal text changes (for review)

**For the developer and the lawyer.** Stage 1c made the legal pages easier to read: dense paragraphs became
lists and shorter sentences. **No meaning, right, obligation, retention period or scope was changed, and no fact
was added.** Wherever a sentence changed, the facts are the same as before; the column "What changed" says how.

- Pages changed: Privacy (5 passages), Terms (3 passages). Cookies and Community rules were already short and
  plain: unchanged.
- "Last updated" moved to 14 November 2026 on Privacy and Terms. `TERMS_VERSION` was **not** changed: the meaning
  is the same, so nobody has to accept the Terms again. If the lawyer sees a change of meaning anywhere, bump
  `TERMS_VERSION` in `config/settings/base.py` (people are then asked to accept again).
- **Non-English texts (uk, pl, de, es, fr, pt-br) are machine translations from the new English text and need a
  native speaker's review**, like the rest of the legal drafts.
- Exact diff: `git show <commit> -- content/` (commit "Legal: easier to read").

## English, sentence by sentence

### Privacy: "When you sign in with GitHub"

| Before | After | What changed |
|---|---|---|
| We receive from GitHub your account id, login, name, bio, avatar link and the other public fields of your GitHub profile, plus the email addresses on your GitHub account. | GitHub sends us: · your account id, login, name, bio, avatar link and the other public fields of your GitHub profile; · the email addresses on your GitHub account. | one sentence → a two-item list, same items |
| We ask GitHub only for `read:user` and `user:email`: we never get access to your repositories, private or public, through your account. | We ask GitHub for only two permissions, `read:user` and `user:email`. Through your account we never get access to your repositories, private or public. | split in two; "permissions" names what the two words are |
| We need this to create your account … | We need this data to create your account … | "this" → "this data" |
| (other sentences of the paragraph) | unchanged | |

### Privacy: "Proof checks", Repo owner item

| Before | After | What changed |
|---|---|---|
| we ask GitHub's public API about the repository you link and store its id, its owner's account id, whether you own it, its creation date and its Website field, the first commit of its history (id and date), your commit count, your first and last commit dates, the number of weeks with your commits, and the state of a manual review when one is needed. | we ask GitHub's public API about the repository you link, and check it again every week. … We store: · its id, its owner's account id, whether you own it, its creation date and its Website field; · the first commit of its history (id and date); · your commit count, your first and last commit dates, and the number of weeks with your commits; · the state of a manual review, when one is needed; · whether the verification file was found, if you use it for an organisation repository. | one long sentence → list of the same stored items |
| We check it again every week. | (moved into the first sentence: "…, and check it again every week.") | moved |
| GitHub's list of other contributors is read during the check and not stored. | unchanged (moved before the list) | moved |
| If you use the verification file for an organisation repository, we also store whether it was found. | (last list item) whether the verification file was found, if you use it for an organisation repository. | moved into the list |

### Privacy: "Reports and moderation"

The paragraph became a list of six items; every sentence is kept word for word except these:

| Before | After | What changed |
|---|---|---|
| When moderators act, we store the decision and its reason: a removed project keeps its content and the reason (only you, moderators and staff see it), cleared profile fields (picture and cover, headline and About, or links) are deleted, and mutes and bans are stored with their reason, start and end. | When moderators act, we store the decision and its reason. A removed project keeps its content and the reason (only you, moderators and staff see it). Cleared profile fields (picture and cover, headline and About, or links) are deleted. Mutes and bans are stored with their reason, start and end. | one sentence → four |

### Privacy: "Community"

| Before | After | What changed |
|---|---|---|
| When you post in the community we store your threads (board, title, text, dates, and whether a thread was edited, pinned, locked or removed), your replies (text, the sticker you picked, which post they answer) and the images you attach. | When you post in the community we store: · your threads: board, title, text, dates, and whether a thread was edited, pinned, locked or removed; · your replies: text, the sticker you picked, and which post they answer; · the images you attach. | brackets → list |
| Images are re-encoded like screenshots: … | They are re-encoded like screenshots: … (same sentence, now in the third list item) | moved |
| When you delete a post, its text, sticker and images are deleted at once (a thread's title stays while replies of others are under it, shown as "[deleted]"). | When you delete a post, its text, sticker and images are deleted at once. A thread's title stays while replies of others are under it, shown as "[deleted]". | bracket → own sentence |
| When moderators remove a post, its images are deleted at once and its text is kept … | When moderators remove a post, its images are deleted at once, and its text is kept … | comma |
| (other sentences) | unchanged, split into two paragraphs | |

### Privacy: "Error log"

| Before | After | What changed |
|---|---|---|
| When something fails, the application writes a short record to an error file on our server: the time, a random reference number (the one shown on the error page), the request method, the page address without anything after a `?` and with usernames replaced by `[user]`, the response status, which part of the code failed, and the technical error message with email addresses, IP addresses and anything that looks like a password or key removed. | When something fails, the application writes a short record to an error file on our server. The record holds: · the time and a random reference number (the one shown on the error page); · the request method, and the page address without anything after a `?` and with usernames replaced by `[user]`; · the response status and which part of the code failed; · the technical error message, with email addresses, IP addresses and anything that looks like a password or key removed. | one sentence → list, same items |
| (other sentences) | unchanged | |

### Terms: "Your content"

| Before | After | What changed |
|---|---|---|
| … on {{ site_name }} (project pages, profiles, feed, search and badges) … | … on {{ site_name }} (project pages, profiles, the For You Page, search and badges) … | the feed page is now called "For You Page" (stage 1a); same page, same URL |

### Terms: "Community", reports item

| Before | After | What changed |
|---|---|---|
| Anyone signed in can report a thread or a reply. Moderators can remove a post …, or pin it. Every removal and lock comes with a reason that the author sees. A removed post stays visible to its author and to moderators so that it can be reviewed; administrators can restore its text. | three list items: (1) Anyone signed in can report a thread or a reply. (2) Moderators can remove a post …, or pin it. Every removal and lock comes with a reason that the author sees. (3) A removed post stays visible to its author and to moderators so that it can be reviewed. Administrators can restore its text. | one item → three; ";" → "." |

### Terms: "Moderation"

| Before | After | What changed |
|---|---|---|
| Moderators can dismiss a report, remove a project, clear profile fields (picture and cover, headline and About, links), mute an account for up to 7 days (you can still read, change your settings, download or delete your data, but not post), or ban it for up to 14 days (you are signed out, cannot sign in, and your profile and projects are not public). | Moderators can: · dismiss a report; · remove a project; · clear profile fields (picture and cover, headline and About, links); · mute an account for up to 7 days: you can still read, change your settings, download or delete your data, but not post; · ban an account for up to 14 days: you are signed out, cannot sign in, and your profile and projects are not public. | one sentence → list; brackets → colons; "ban it" → "ban an account" |
| (other sentences) | unchanged | |

## Translations: old and new passages

Generated from git. Each pair is one passage (a paragraph or a list item) before and after.

### uk

**privacy, before:**

> **Коли ви входите через GitHub.** GitHub передає нам id і логін вашого акаунта, імʼя, біо, посилання на аватар та інші публічні поля профілю, а також адреси пошти з вашого акаунта GitHub. Ми просимо в GitHub лише `read:user` і `user:email`: через ваш акаунт ми не отримуємо доступу до жодних репозиторіїв, ні приватних, ні публічних. Токен доступу GitHub ми після входу не зберігаємо. Це потрібно, щоб створити акаунт і впізнавати вас наступного разу (виконання нашої з вами угоди). Ваш логін GitHub оновлюється при кожному вході, тож профіль завжди веде на ваш поточний акаунт GitHub.

**privacy, after:**

> **Коли ви входите через GitHub.** GitHub передає нам:
>
> - id і логін вашого акаунта, імʼя, біо, посилання на аватар та інші публічні поля профілю GitHub;
> - адреси пошти з вашого акаунта GitHub.
>
> Ми просимо в GitHub лише два дозволи: `read:user` і `user:email`. Через ваш акаунт ми ніколи не отримуємо доступу до ваших репозиторіїв, ні приватних, ні публічних. Токен доступу GitHub ми після входу не зберігаємо. Ці дані потрібні, щоб створити акаунт і впізнавати вас наступного разу (виконання нашої з вами угоди). Ваш логін GitHub оновлюється при кожному вході, тож профіль завжди веде на ваш поточний акаунт GitHub.

**privacy, before:**

> - *Власник репозиторію:* ми питаємо публічний API GitHub про репозиторій, який ви вказали, і зберігаємо його id, id акаунта власника, чи він ваш, дату створення і поле Website, перший коміт його історії (id і дату), кількість ваших комітів, дати першого й останнього, кількість тижнів з вашими комітами, а також стан ручної перевірки, якщо вона потрібна. Щотижня ми перевіряємо це знову. Список інших учасників ми читаємо під час перевірки й не зберігаємо. Якщо ви використовуєте файл підтвердження для репозиторію організації, ми також зберігаємо, чи його знайдено.

**privacy, after:**

> - *Власник репозиторію:* ми питаємо публічний API GitHub про репозиторій, який ви вказали, і щотижня перевіряємо його знову. Список інших учасників GitHub ми читаємо під час перевірки й не зберігаємо. Ми зберігаємо:
>     - його id, id акаунта власника, чи він ваш, дату створення і поле Website;
>     - перший коміт його історії (id і дату);
>     - кількість ваших комітів, дати першого й останнього, кількість тижнів з вашими комітами;
>     - стан ручної перевірки, якщо вона потрібна;
>     - чи знайдено файл підтвердження, якщо ви використовуєте його для репозиторію організації.

**privacy, before:**

> **Скарги і модерація.** Якщо ви скаржитеся на проєкт, профіль або запис build log, ми зберігаємо причину і подробиці, які ви написали. Скарги бачать модератори (люди з бейджем модератора) і команда. Щоб ухвалити рішення, вони також бачать вміст, на який поскаржилися, та історію цієї людини на {{ site_name }}: дату реєстрації, попередні санкції, інші скарги на неї і вилучені проєкти. Сторінки модерації не показують адрес пошти. Людині, на яку поскаржилися, ніколи не повідомляють, хто це зробив. Коли модератори ухвалюють рішення, ми зберігаємо його і причину: вилучений проєкт зберігає вміст і причину (бачите лише ви, модератори і команда), очищені поля профілю (фото й обкладинка, короткий опис і «Про себе» або посилання) видаляються, а обмеження і блокування зберігаються з причиною, початком і кінцем. Причину ви бачите в повідомленні на сайті, яке ми зберігаємо, доки ви не видалите акаунт. Рішення щодо вас і ці повідомлення є у «Завантажити мої дані». Щоб оскаржити рішення, напишіть на [{{ contact_email }}](mailto:{{ contact_email }}).

**privacy, after:**

> **Скарги і модерація.**
>
> - Якщо ви скаржитеся на проєкт, профіль або запис журналу розробки, ми зберігаємо причину і подробиці, які ви написали.
> - Скарги бачать модератори (люди з бейджем модератора) і команда. Щоб ухвалити рішення, вони також бачать вміст, на який поскаржилися, та історію цієї людини на {{ site_name }}: дату реєстрації, попередні санкції, інші скарги на неї і вилучені проєкти. Сторінки модерації не показують адрес пошти.
> - Людині, на яку поскаржилися, ніколи не повідомляють, хто це зробив.
> - Коли модератори ухвалюють рішення, ми зберігаємо його і причину. Вилучений проєкт зберігає вміст і причину (бачите лише ви, модератори і команда). Очищені поля профілю (фото й обкладинка, короткий опис і «Про себе» або посилання) видаляються. Обмеження і блокування зберігаються з причиною, початком і кінцем.
> - Причину ви бачите в повідомленні на сайті, яке ми зберігаємо, доки ви не видалите акаунт. Рішення щодо вас і ці повідомлення є у «Завантажити мої дані».
> - Щоб оскаржити рішення, напишіть на [{{ contact_email }}](mailto:{{ contact_email }}).
>
> **Спільнота.** Коли ви пишете у спільноті, ми зберігаємо:

**privacy, before:**

> **Спільнота.** Коли ви пишете у спільноті, ми зберігаємо ваші треди (розділ, назва, текст, дати, а також чи тред змінювали, закріпили, закрили чи вилучили), ваші відповіді (текст, вибраний стікер, на який допис вони відповідають) і прикріплені зображення. Зображення перекодовуються так само, як знімки екрана: приховані метадані, як-от GPS-координати, видаляються, назви файлів випадкові, а на нашому сервері зберігаються копія до 1600 px і мініатюра 640 px. Дописи, їхні зображення, кількість голосів і ваше імʼя користувача на них **публічні**. Ми також зберігаємо ваші голоси; ніхто не бачить, хто за що проголосував, ні на сайті, ні в адмінці. Коли ви видаляєте допис, його текст, стікер і зображення видаляються одразу (назва треду лишається, поки під ним є чужі відповіді, і показується як «[видалено]»). Коли допис вилучають модератори, його зображення видаляються одразу, а текст зберігається разом із причиною, і бачать його лише ви, модератори й персонал. Модератори бачать допис, на який поскаржилися, разом з історією автора, як і для інших скарг.

**privacy, after:**

> - ваші треди: розділ, назва, текст, дати, а також чи тред змінювали, закріпили, закрили чи вилучили;
> - ваші відповіді: текст, вибраний стікер і на який допис вони відповідають;
> - прикріплені зображення. Вони перекодовуються так само, як знімки екрана: приховані метадані, як-от GPS-координати, видаляються, назви файлів випадкові, а на нашому сервері зберігаються копія до 1600 px і мініатюра 640 px.
>
> Дописи, їхні зображення, кількість голосів і ваше імʼя користувача на них **публічні**. Ми також зберігаємо ваші голоси; ніхто не бачить, хто за що проголосував, ні на сайті, ні в адмінці.
>
> Коли ви видаляєте допис, його текст, стікер і зображення видаляються одразу. Назва треду лишається, поки під ним є чужі відповіді, і показується як «[видалено]». Коли допис вилучають модератори, його зображення видаляються одразу, а текст зберігається разом із причиною, і бачать його лише ви, модератори й команда. Модератори бачать допис, на який поскаржилися, разом з історією автора, як і для інших скарг.

**privacy, before:**

> **Журнал помилок.** Коли щось ламається, застосунок записує короткий запис у файл помилок на нашому сервері: час, випадковий код помилки (той, що показано на сторінці помилки), метод запиту, адресу сторінки без того, що йде після `?`, і з іменами користувачів, заміненими на `[user]`, статус відповіді, частину коду, де сталася помилка, і технічне повідомлення, з якого прибрано адреси пошти, IP-адреси та все, що схоже на пароль чи ключ. Сторінки, яких не знайдено, записуються в окремий файл, кожна адреса не частіше разу на хвилину. Ці файли ніколи не містять вашої IP-адреси, даних про браузер, cookies, того, що ви вводили у форми, вашої пошти чи імені користувача. Кожен файл обмежено 5 МБ плюс 5 старіших копій; коли ліміт досягнуто, найстаріша видаляється.

**privacy, after:**

> **Журнал помилок.** Коли щось ламається, застосунок записує короткий запис у файл помилок на нашому сервері. У записі є:
>
> - час і випадковий код помилки (той, що показано на сторінці помилки);
> - метод запиту й адреса сторінки без того, що йде після `?`, з іменами користувачів, заміненими на `[user]`;
> - статус відповіді й частина коду, де сталася помилка;
> - технічне повідомлення, з якого прибрано адреси пошти, IP-адреси та все, що схоже на пароль чи ключ.
>
> Сторінки, яких не знайдено, записуються в окремий файл, кожна адреса не частіше разу на хвилину. Ці файли ніколи не містять вашої IP-адреси, даних про браузер, cookies, того, що ви вводили у форми, вашої пошти чи імені користувача. Кожен файл обмежено 5 МБ плюс 5 старіших копій; коли ліміт досягнуто, найстаріша видаляється.

**terms, before:**

> - Ви дозволяєте нам зберігати, показувати й поширювати їх на {{ site_name }} (сторінки проєктів, профілі, стрічка, пошук і бейджі), доки вони опубліковані. Дозвіл припиняється, коли ви їх видаляєте, крім копій, які інші вже вбудували чи зберегли.

**terms, after:**

> - Ви дозволяєте нам зберігати, показувати й поширювати їх на {{ site_name }} (сторінки проєктів, профілі, сторінка «Для вас», пошук і бейджі), доки вони опубліковані. Дозвіл припиняється, коли ви їх видаляєте, крім копій, які інші вже вбудували чи зберегли.

**terms, before:**

> - Будь-хто, хто увійшов, може поскаржитися на тред чи відповідь. Модератори можуть вилучити допис (його зображення видаляються одразу), закрити тред, щоб відповідати могли лише модератори, або закріпити його. Кожне вилучення й закриття має причину, яку бачить автор. Вилучений допис лишається видимим автору й модераторам, щоб рішення можна було перевірити; адміністратори можуть відновити його текст.

**terms, after:**

> - Будь-хто, хто увійшов, може поскаржитися на тред чи відповідь.
> - Модератори можуть вилучити допис (його зображення видаляються одразу), закрити тред, щоб відповідати могли лише модератори, або закріпити його. Кожне вилучення й закриття має причину, яку бачить автор.
> - Вилучений допис лишається видимим автору й модераторам, щоб рішення можна було перевірити. Адміністратори можуть відновити його текст.

**terms, before:**

> Будь-хто з акаунтом може поскаржитися на проєкт, профіль або запис build log. Модератори можуть відхилити скаргу, вилучити проєкт, очистити поля профілю (фото й обкладинка, короткий опис і «Про себе», посилання), обмежити акаунт до 7 днів (ви й далі можете читати, змінювати налаштування, завантажити чи видалити свої дані, але не публікувати) або заблокувати його до 14 днів (вас виводять з акаунта, увійти не можна, профіль і проєкти не публічні). Кожне рішення має причину, яку ви бачите. Довші або безстрокові санкції ухвалюють лише адміністратори сайту; вони також можуть приховувати проєкти або призупиняти акаунти. Видалення акаунта не скасовує блокування (див. [Політику конфіденційності](/legal/privacy/)). Якщо вважаєте, що ми помилилися, напишіть на [{{ contact_email }}](mailto:{{ contact_email }}).

**terms, after:**

> Будь-хто з акаунтом може поскаржитися на проєкт, профіль або запис журналу розробки. Модератори можуть:
>
> - відхилити скаргу;
> - вилучити проєкт;
> - очистити поля профілю (фото й обкладинка, короткий опис і «Про себе», посилання);
> - обмежити акаунт до 7 днів: ви й далі можете читати, змінювати налаштування, завантажити чи видалити свої дані, але не публікувати;
> - заблокувати акаунт до 14 днів: вас виводять з акаунта, увійти не можна, профіль і проєкти не публічні.
>
> Кожне рішення має причину, яку ви бачите. Довші або безстрокові санкції ухвалюють лише адміністратори сайту; вони також можуть приховувати проєкти або призупиняти акаунти. Видалення акаунта не скасовує блокування (див. [Політику конфіденційності](/legal/privacy/)). Якщо вважаєте, що ми помилилися, напишіть на [{{ contact_email }}](mailto:{{ contact_email }}).

### pl

**privacy, before:**

> **Gdy logujesz się przez GitHub.** Od GitHuba otrzymujemy identyfikator Twojego konta, login, imię i nazwisko, bio, link do awatara i pozostałe publiczne pola profilu GitHub, a także adresy e-mail przypisane do Twojego konta GitHub. Prosimy GitHub tylko o `read:user` i `user:email`: przez Twoje konto nigdy nie mamy dostępu do Twoich repozytoriów, ani prywatnych, ani publicznych. Po zalogowaniu nie przechowujemy Twojego tokenu dostępu do GitHuba. Potrzebujemy tych danych, by założyć konto i rozpoznać Cię następnym razem (wykonanie umowy z Tobą). Twój login GitHub jest odświeżany przy każdym logowaniu, więc profil zawsze prowadzi do Twojego obecnego konta GitHub.

**privacy, after:**

> **Gdy logujesz się przez GitHub.** GitHub przekazuje nam:
>
> - identyfikator i login Twojego konta, imię, bio, link do awatara i pozostałe publiczne pola Twojego profilu GitHub;
> - adresy e-mail z Twojego konta GitHub.
>
> Prosimy GitHub tylko o dwa uprawnienia: `read:user` i `user:email`. Przez Twoje konto nigdy nie dostajemy dostępu do Twoich repozytoriów, ani prywatnych, ani publicznych. Nie przechowujemy Twojego tokenu dostępu GitHub po zalogowaniu. Te dane są potrzebne, aby utworzyć konto i rozpoznać Cię następnym razem (wykonanie naszej umowy z Tobą). Twój login GitHub odświeża się przy każdym logowaniu, więc profil zawsze prowadzi do Twojego aktualnego konta GitHub.

**privacy, before:**

> - *Repo owner:* pytamy publiczne API GitHuba o repozytorium, które podajesz, i zapisujemy jego identyfikator, identyfikator konta właściciela, czy należy do Ciebie, datę utworzenia i pole Website, pierwszy commit jego historii (identyfikator i datę), liczbę Twoich commitów, daty pierwszego i ostatniego, liczbę tygodni z Twoimi commitami oraz stan ręcznej weryfikacji, gdy jest potrzebna. Sprawdzamy to ponownie co tydzień. Listę innych współtwórców czytamy podczas sprawdzania i nie zapisujemy jej. Jeśli używasz pliku weryfikacyjnego w repozytorium organizacji, zapisujemy też, czy go znaleziono.

**privacy, after:**

> - *Repo owner:* pytamy publiczne API GitHuba o repozytorium, które podajesz, i co tydzień sprawdzamy je ponownie. Listę innych współtwórców z GitHuba czytamy podczas sprawdzenia i nie zapisujemy jej. Zapisujemy:
>     - jego identyfikator, identyfikator konta właściciela, czy należy do Ciebie, datę utworzenia i pole Website;
>     - pierwszy commit w jego historii (identyfikator i datę);
>     - liczbę Twoich commitów, daty pierwszego i ostatniego oraz liczbę tygodni z Twoimi commitami;
>     - stan ręcznej weryfikacji, gdy jest potrzebna;
>     - czy znaleziono plik weryfikacyjny, jeśli używasz go dla repozytorium organizacji.

**privacy, before:**

> **Zgłoszenia i moderacja.** Jeśli zgłosisz projekt, profil lub wpis w dzienniku rozwoju, zapisujemy powód i podane przez Ciebie szczegóły. Zgłoszenia widzą moderatorzy (osoby z odznaką moderatora) i zespół. Aby podjąć decyzję, widzą też zgłoszoną treść i historię zgłoszonej osoby w {{ site_name }}: datę dołączenia, wcześniejsze sankcje, inne zgłoszenia na nią i usunięte projekty. Strony moderacji nie pokazują adresów e-mail. Zgłoszona osoba nigdy nie dowiaduje się, kto ją zgłosił. Gdy moderatorzy podejmują działanie, zapisujemy decyzję i jej powód: usunięty projekt zachowuje treść i powód (widzisz go tylko Ty, moderatorzy i zespół), wyczyszczone pola profilu (zdjęcie i obraz w tle, krótki opis i „O mnie” albo linki) są usuwane, a wyciszenia i blokady są zapisywane z powodem, początkiem i końcem. Powód widzisz w powiadomieniu na stronie, które przechowujemy, dopóki nie usuniesz konta. Decyzje dotyczące Ciebie i te powiadomienia są w „Pobierz moje dane”. Aby odwołać się od decyzji, napisz na [{{ contact_email }}](mailto:{{ contact_email }}).

**privacy, after:**

> **Zgłoszenia i moderacja.**
>
> - Jeśli zgłosisz projekt, profil lub wpis w dzienniku rozwoju, zapisujemy powód i szczegóły, które napiszesz.
> - Zgłoszenia widzą moderatorzy (osoby z odznaką moderatora) i zespół. Aby podjąć decyzję, widzą też zgłoszoną treść i historię zgłoszonej osoby w {{ site_name }}: kiedy dołączyła, wcześniejsze sankcje, inne zgłoszenia na jej temat i usunięte projekty. Strony moderacji nie pokazują adresów e-mail.
> - Zgłoszona osoba nigdy nie dowiaduje się, kto ją zgłosił.
> - Gdy moderatorzy podejmują działanie, zapisujemy decyzję i jej powód. Usunięty projekt zachowuje treść i powód (widzisz go tylko Ty, moderatorzy i zespół). Wyczyszczone pola profilu (zdjęcie i okładka, nagłówek i „O mnie” albo linki) są usuwane. Wyciszenia i blokady zapisujemy z powodem, początkiem i końcem.
> - Powód widzisz w powiadomieniu na stronie, które przechowujemy, dopóki nie usuniesz konta. Decyzje dotyczące Ciebie i te powiadomienia są w „Pobierz moje dane”.
> - Aby odwołać się od decyzji, napisz na [{{ contact_email }}](mailto:{{ contact_email }}).
>
> **Społeczność.** Gdy piszesz w społeczności, zapisujemy:

**privacy, before:**

> **Społeczność.** Gdy piszesz w społeczności, zapisujemy Twoje wątki (dział, tytuł, tekst, daty oraz to, czy wątek był edytowany, przypięty, zamknięty lub usunięty), Twoje odpowiedzi (tekst, wybraną naklejkę, post, na który odpowiadają) i dołączone obrazy. Obrazy są kodowane na nowo tak jak zrzuty ekranu: ukryte metadane, np. lokalizacja GPS, są usuwane, nazwy plików są losowe, a na naszym serwerze przechowujemy kopię do 1600 px i miniaturę 640 px. Posty, ich obrazy, liczba głosów i Twoja nazwa użytkownika przy nich są **publiczne**. Zapisujemy też Twoje głosy; nikt nie widzi, kto na co głosował, ani na stronie, ani w panelu administracyjnym. Gdy usuwasz post, jego tekst, naklejka i obrazy są kasowane od razu (tytuł wątku zostaje, dopóki są pod nim odpowiedzi innych, i jest widoczny jako „[usunięto]”). Gdy post usuwają moderatorzy, jego obrazy są kasowane od razu, a tekst zostaje zachowany wraz z powodem i widzą go tylko Ty, moderatorzy i personel. Moderatorzy widzą zgłoszony post razem z historią autora, tak jak przy innych zgłoszeniach.

**privacy, after:**

> - Twoje wątki: dział, tytuł, tekst, daty oraz to, czy wątek był edytowany, przypięty, zamknięty lub usunięty;
> - Twoje odpowiedzi: tekst, wybraną naklejkę i to, na który wpis odpowiadają;
> - dołączone obrazy. Są ponownie kodowane jak zrzuty ekranu: ukryte metadane, takie jak lokalizacja GPS, są usuwane, nazwy plików są losowe, a na naszym serwerze trzymamy kopię do 1600 px i miniaturę 640 px.
>
> Wpisy, ich obrazy, liczba głosów i Twoja nazwa użytkownika przy nich są **publiczne**. Zapisujemy też Twoje głosy; nikt nie widzi, kto na co głosował, ani na stronie, ani w panelu administracyjnym.
>
> Gdy usuwasz wpis, jego tekst, naklejka i obrazy są usuwane od razu. Tytuł wątku zostaje, dopóki są pod nim odpowiedzi innych osób, i jest pokazywany jako „[usunięto]”. Gdy wpis usuwają moderatorzy, jego obrazy są usuwane od razu, a tekst zostaje zachowany z powodem i widzisz go tylko Ty, moderatorzy i zespół. Moderatorzy widzą zgłoszone wpisy razem z historią autora, tak jak przy innych zgłoszeniach.

**privacy, before:**

> **Dziennik błędów.** Gdy coś się psuje, aplikacja zapisuje krótki wpis w pliku błędów na naszym serwerze: czas, losowy numer referencyjny (ten widoczny na stronie błędu), metodę żądania, adres strony bez części po `?` i z nazwami użytkowników zastąpionymi przez `[user]`, status odpowiedzi, część kodu, w której wystąpił błąd, oraz techniczny komunikat, z którego usunięto adresy e-mail, adresy IP i wszystko, co wygląda na hasło lub klucz. Nieznalezione strony trafiają do osobnego pliku, każdy adres najwyżej raz na minutę. Te pliki nigdy nie zawierają Twojego adresu IP, danych przeglądarki, plików cookie, tego, co wpisujesz w formularze, Twojego adresu e-mail ani nazwy użytkownika. Każdy plik ma limit 5 MB plus 5 starszych kopii; po osiągnięciu limitu najstarsza jest usuwana.

**privacy, after:**

> **Dziennik błędów.** Gdy coś się psuje, aplikacja zapisuje krótki wpis w pliku błędów na naszym serwerze. Wpis zawiera:
>
> - czas i losowy numer referencyjny (ten widoczny na stronie błędu);
> - metodę żądania i adres strony bez tego, co jest po `?`, z nazwami użytkowników zastąpionymi przez `[user]`;
> - status odpowiedzi i część kodu, w której wystąpił błąd;
> - techniczny komunikat błędu, z którego usunięto adresy e-mail, adresy IP i wszystko, co wygląda na hasło lub klucz.
>
> Strony, których nie znaleziono, trafiają do osobnego pliku, każdy adres najwyżej raz na minutę. Te pliki nigdy nie zawierają Twojego adresu IP, danych przeglądarki, plików cookie, tego, co wpisano w formularzu, Twojego adresu e-mail ani nazwy użytkownika. Każdy plik jest ograniczony do 5 MB plus 5 starszych kopii; po osiągnięciu limitu najstarsza jest usuwana.

**terms, before:**

> - Dajesz nam zgodę na przechowywanie, wyświetlanie i udostępnianie ich w {{ site_name }} (strony projektów, profile, aktualności, wyszukiwarka i plakietki), dopóki są opublikowane. Zgoda wygasa, gdy je usuniesz, z wyjątkiem kopii, które inni już osadzili lub zapisali.

**terms, after:**

> - Dajesz nam zgodę na przechowywanie, wyświetlanie i udostępnianie ich w {{ site_name }} (strony projektów, profile, strona Dla Ciebie, wyszukiwarka i plakietki), dopóki są opublikowane. Zgoda wygasa, gdy je usuniesz, z wyjątkiem kopii, które inni już osadzili lub zapisali.

**terms, before:**

> - Każda zalogowana osoba może zgłosić wątek lub odpowiedź. Moderatorzy mogą usunąć post (jego obrazy są kasowane od razu), zamknąć wątek, tak aby odpowiadać mogli tylko moderatorzy, albo go przypiąć. Każde usunięcie i zamknięcie ma powód, który widzi autor. Usunięty post pozostaje widoczny dla autora i moderatorów, aby można było sprawdzić decyzję; administratorzy mogą przywrócić jego tekst.

**terms, after:**

> - Każda zalogowana osoba może zgłosić wątek lub odpowiedź.
> - Moderatorzy mogą usunąć wpis (jego obrazy są usuwane od razu), zamknąć wątek, tak aby odpowiadać mogli tylko moderatorzy, albo go przypiąć. Każde usunięcie i zamknięcie ma powód, który widzi autor.
> - Usunięty wpis pozostaje widoczny dla autora i moderatorów, aby można go było sprawdzić. Administratorzy mogą przywrócić jego tekst.

**terms, before:**

> Każda zalogowana osoba może zgłosić projekt, profil lub wpis w dzienniku zmian. Moderatorzy mogą odrzucić zgłoszenie, usunąć projekt, wyczyścić pola profilu (zdjęcie i obraz w tle, krótki opis i „O mnie”, linki), wyciszyć konto na maksymalnie 7 dni (nadal możesz czytać, zmieniać ustawienia, pobrać lub usunąć swoje dane, ale nie publikować) albo zablokować je na maksymalnie 14 dni (zostajesz wylogowany, nie możesz się zalogować, a profil i projekty nie są publiczne). Każda decyzja ma powód, który widzisz. O dłuższych lub stałych sankcjach decydują tylko administratorzy serwisu, którzy mogą też ukrywać projekty lub zawieszać konta. Usunięcie konta nie kończy blokady (zob. [Politykę prywatności](/legal/privacy/)). Jeśli uważasz, że popełniliśmy błąd, napisz na [{{ contact_email }}](mailto:{{ contact_email }}).

**terms, after:**

> Każda zalogowana osoba może zgłosić projekt, profil lub wpis w dzienniku rozwoju. Moderatorzy mogą:
>
> - odrzucić zgłoszenie;
> - usunąć projekt;
> - wyczyścić pola profilu (zdjęcie i okładka, nagłówek i „O mnie”, linki);
> - wyciszyć konto na maksymalnie 7 dni: nadal możesz czytać, zmieniać ustawienia, pobrać lub usunąć swoje dane, ale nie możesz publikować;
> - zablokować konto na maksymalnie 14 dni: zostajesz wylogowany, nie możesz się zalogować, a Twój profil i projekty nie są publiczne.
>
> Każda decyzja ma powód, który widzisz. O dłuższych lub stałych sankcjach decydują tylko administratorzy strony, którzy mogą też ukrywać projekty lub zawieszać konta. Usunięcie konta nie kończy blokady (zobacz [Politykę prywatności](/legal/privacy/)). Jeśli uważasz, że popełniliśmy błąd, napisz na [{{ contact_email }}](mailto:{{ contact_email }}).

### de

**privacy, before:**

> **Wenn du dich mit GitHub anmeldest.** Von GitHub erhalten wir deine Konto-ID, deinen Login, deinen Namen, deine Bio, den Link zu deinem Avatar und die übrigen öffentlichen Felder deines GitHub-Profils sowie die E-Mail-Adressen deines GitHub-Kontos. Wir fragen GitHub nur nach `read:user` und `user:email`: Über dein Konto bekommen wir nie Zugriff auf deine Repositories, weder private noch öffentliche. Dein GitHub-Zugriffstoken behalten wir nach der Anmeldung nicht. Wir brauchen das, um dein Konto anzulegen und dich beim nächsten Mal wiederzuerkennen (Erfüllung unserer Vereinbarung mit dir). Dein GitHub-Login wird bei jeder Anmeldung aktualisiert, damit dein Profil immer auf dein aktuelles GitHub-Konto verweist.

**privacy, after:**

> **Wenn du dich mit GitHub anmeldest.** GitHub schickt uns:
>
> - deine Konto-ID, deinen Login, Namen, Bio, Avatar-Link und die anderen öffentlichen Felder deines GitHub-Profils;
> - die E-Mail-Adressen deines GitHub-Kontos.
>
> Wir fragen GitHub nur nach zwei Berechtigungen: `read:user` und `user:email`. Über dein Konto erhalten wir nie Zugriff auf deine Repositories, weder private noch öffentliche. Deinen GitHub-Zugangstoken speichern wir nach der Anmeldung nicht. Diese Daten brauchen wir, um dein Konto anzulegen und dich beim nächsten Mal wiederzuerkennen (Erfüllung unseres Vertrags mit dir). Dein GitHub-Login wird bei jeder Anmeldung aktualisiert, damit dein Profil immer auf dein aktuelles GitHub-Konto verweist.

**privacy, before:**

> - *Repo owner:* Wir fragen die öffentliche API von GitHub nach dem Repository, das du verknüpfst, und speichern seine ID, die Konto-ID der Person, der es gehört, ob es dir gehört, sein Erstellungsdatum und sein Website-Feld, den ersten Commit seines Verlaufs (ID und Datum), deine Anzahl an Commits, das Datum deines ersten und letzten Commits, die Anzahl der Wochen mit deinen Commits und den Stand einer manuellen Prüfung, falls eine nötig ist. Wir prüfen das jede Woche erneut. Die Liste der anderen Beitragenden lesen wir während der Prüfung und speichern sie nicht. Wenn du die Bestätigungsdatei für ein Repository einer Organisation nutzt, speichern wir auch, ob sie gefunden wurde.

**privacy, after:**

> - *Repo owner:* Wir fragen die öffentliche API von GitHub nach dem Repository, das du verknüpfst, und prüfen es jede Woche erneut. Die Liste der anderen Mitwirkenden auf GitHub lesen wir bei der Prüfung und speichern sie nicht. Wir speichern:
>     - seine ID, die Konto-ID des Eigentümers, ob es dir gehört, sein Erstellungsdatum und sein Website-Feld;
>     - den ersten Commit seiner Historie (ID und Datum);
>     - die Zahl deiner Commits, das Datum deines ersten und letzten Commits und die Zahl der Wochen mit deinen Commits;
>     - den Stand einer manuellen Prüfung, wenn eine nötig ist;
>     - ob die Verifizierungsdatei gefunden wurde, wenn du sie für ein Organisations-Repository nutzt.

**privacy, before:**

> **Meldungen und Moderation.** Wenn du ein Projekt, ein Profil oder einen Build-Log-Eintrag meldest, speichern wir den Grund und die Details, die du schreibst. Meldungen sehen Moderatorinnen und Moderatoren (Personen mit dem Moderator-Abzeichen) und das Team. Für ihre Entscheidung sehen sie auch den gemeldeten Inhalt und die Vorgeschichte der gemeldeten Person auf {{ site_name }}: wann sie beigetreten ist, frühere Sanktionen, andere Meldungen über sie und entfernte Projekte. Die Moderationsseiten zeigen keine E-Mail-Adressen. Die gemeldete Person erfährt nie, wer sie gemeldet hat. Wenn die Moderation handelt, speichern wir die Entscheidung und ihren Grund: Ein entferntes Projekt behält seinen Inhalt und den Grund (nur du, die Moderation und das Team sehen ihn), geleerte Profilfelder (Profilbild und Titelbild, Kurzbeschreibung und „Über mich“ oder Links) werden gelöscht, und Stummschaltungen und Sperren werden mit Grund, Beginn und Ende gespeichert. Den Grund siehst du in einem Hinweis auf der Website, den wir behalten, bis du dein Konto löschst. Entscheidungen über dich und diese Hinweise sind in „Meine Daten herunterladen“ enthalten. Um eine Entscheidung anzufechten, schreib an [{{ contact_email }}](mailto:{{ contact_email }}).

**privacy, after:**

> **Meldungen und Moderation.**
>
> - Wenn du ein Projekt, ein Profil oder einen Build-Log-Eintrag meldest, speichern wir den Grund und die Details, die du schreibst.
> - Meldungen sehen die Moderatorinnen und Moderatoren (Personen mit dem Moderator-Abzeichen) und das Team. Für die Entscheidung sehen sie auch den gemeldeten Inhalt und die Geschichte der gemeldeten Person auf {{ site_name }}: wann sie beigetreten ist, frühere Sanktionen, andere Meldungen über sie und entfernte Projekte. Die Moderationsseiten zeigen keine E-Mail-Adressen.
> - Die gemeldete Person erfährt nie, wer sie gemeldet hat.
> - Wenn die Moderation handelt, speichern wir die Entscheidung und ihren Grund. Ein entferntes Projekt behält seinen Inhalt und den Grund (sichtbar nur für dich, die Moderation und das Team). Geleerte Profilfelder (Bild und Titelbild, Kurzbeschreibung und „Über mich“ oder Links) werden gelöscht. Stummschaltungen und Sperren speichern wir mit Grund, Beginn und Ende.
> - Den Grund siehst du in einem Hinweis auf der Website, den wir behalten, bis du dein Konto löschst. Entscheidungen über dich und diese Hinweise sind in „Meine Daten herunterladen“ enthalten.
> - Um gegen eine Entscheidung Einspruch einzulegen, schreib an [{{ contact_email }}](mailto:{{ contact_email }}).
>
> **Community.** Wenn du in der Community schreibst, speichern wir:

**privacy, before:**

> **Community.** Wenn du in der Community schreibst, speichern wir deine Threads (Bereich, Titel, Text, Daten und ob ein Thread bearbeitet, angeheftet, geschlossen oder entfernt wurde), deine Antworten (Text, den gewählten Sticker, auf welchen Beitrag sie antworten) und die angehängten Bilder. Bilder werden wie Screenshots neu kodiert: Versteckte Metadaten wie der GPS-Standort werden entfernt, die Dateinamen sind zufällig, und auf unserem eigenen Server liegen eine Kopie bis 1600 px und ein Vorschaubild mit 640 px. Beiträge, ihre Bilder, ihre Stimmenzahl und dein Benutzername daran sind **öffentlich**. Wir speichern auch deine Stimmen; niemand sieht, wer wofür gestimmt hat, weder auf der Website noch im Admin-Bereich. Wenn du einen Beitrag löschst, werden sein Text, sein Sticker und seine Bilder sofort gelöscht (der Titel eines Threads bleibt, solange Antworten anderer darunter stehen, und wird als „[gelöscht]“ angezeigt). Wenn Moderatoren einen Beitrag entfernen, werden seine Bilder sofort gelöscht und der Text bleibt mit dem Grund gespeichert, sichtbar nur für dich, Moderatoren und das Team. Moderatoren sehen gemeldete Beiträge zusammen mit der Vorgeschichte der Person, die sie geschrieben hat, wie bei anderen Meldungen.

**privacy, after:**

> - deine Threads: Bereich, Titel, Text, Daten und ob ein Thread bearbeitet, angeheftet, gesperrt oder entfernt wurde;
> - deine Antworten: Text, den gewählten Sticker und auf welchen Beitrag sie antworten;
> - die angehängten Bilder. Sie werden wie Screenshots neu kodiert: Versteckte Metadaten wie der GPS-Standort werden entfernt, die Dateinamen sind zufällig, und wir speichern eine Kopie bis 1600 px und eine Vorschau mit 640 px auf unserem eigenen Server.
>
> Beiträge, ihre Bilder, die Zahl ihrer Stimmen und dein Benutzername daran sind **öffentlich**. Wir speichern auch deine Stimmen; niemand sieht, wer wofür gestimmt hat, weder auf der Website noch im Admin-Bereich.
>
> Wenn du einen Beitrag löschst, werden Text, Sticker und Bilder sofort gelöscht. Der Titel eines Threads bleibt, solange darunter Antworten anderer stehen, und wird als „[gelöscht]“ angezeigt. Wenn die Moderation einen Beitrag entfernt, werden seine Bilder sofort gelöscht, und der Text wird mit dem Grund aufbewahrt, sichtbar nur für dich, die Moderation und das Team. Die Moderation sieht gemeldete Beiträge zusammen mit der Geschichte der Autorin oder des Autors, wie bei anderen Meldungen.

**privacy, before:**

> **Fehlerprotokoll.** Wenn etwas schiefgeht, schreibt die Anwendung einen kurzen Eintrag in eine Fehlerdatei auf unserem Server: Zeitpunkt, eine zufällige Referenznummer (die auf der Fehlerseite angezeigt wird), die Anfragemethode, die Seitenadresse ohne alles nach einem `?` und mit Benutzernamen ersetzt durch `[user]`, den Antwortstatus, den Teil des Codes, der fehlgeschlagen ist, und die technische Fehlermeldung, aus der E-Mail-Adressen, IP-Adressen und alles, was wie ein Passwort oder Schlüssel aussieht, entfernt sind. Nicht gefundene Seiten kommen in eine eigene Datei, jede Adresse höchstens einmal pro Minute. Diese Dateien enthalten nie deine IP-Adresse, Browserdaten, Cookies, Formulareingaben, deine E-Mail-Adresse oder deinen Benutzernamen. Jede Datei ist auf 5 MB plus 5 ältere Kopien begrenzt; ist die Grenze erreicht, wird die älteste gelöscht.

**privacy, after:**

> **Fehlerprotokoll.** Wenn etwas schiefgeht, schreibt die Anwendung einen kurzen Eintrag in eine Fehlerdatei auf unserem Server. Der Eintrag enthält:
>
> - die Uhrzeit und eine zufällige Referenznummer (die auf der Fehlerseite angezeigte);
> - die Anfragemethode und die Seitenadresse ohne alles nach einem `?`, mit Benutzernamen ersetzt durch `[user]`;
> - den Antwortstatus und den Teil des Codes, der fehlgeschlagen ist;
> - die technische Fehlermeldung, aus der E-Mail-Adressen, IP-Adressen und alles, was wie ein Passwort oder Schlüssel aussieht, entfernt sind.
>
> Nicht gefundene Seiten werden in eine eigene Datei geschrieben, jede Adresse höchstens einmal pro Minute. Diese Dateien enthalten nie deine IP-Adresse, Browserdaten, Cookies, was du in ein Formular eingegeben hast, deine E-Mail-Adresse oder deinen Benutzernamen. Jede Datei ist auf 5 MB plus 5 ältere Kopien begrenzt; ist die Grenze erreicht, wird die älteste gelöscht.

**terms, before:**

> - Du erlaubst uns, sie auf {{ site_name }} zu speichern, anzuzeigen und zu teilen (Projektseiten, Profile, Feed, Suche und Badges), solange sie veröffentlicht sind. Diese Erlaubnis endet, wenn du sie löschst, außer für Kopien, die andere bereits eingebettet oder gespeichert haben.

**terms, after:**

> - Du erlaubst uns, sie auf {{ site_name }} zu speichern, anzuzeigen und zu teilen (Projektseiten, Profile, Für-dich-Seite, Suche und Badges), solange sie veröffentlicht sind. Diese Erlaubnis endet, wenn du sie löschst, außer für Kopien, die andere bereits eingebettet oder gespeichert haben.

**terms, before:**

> - Alle angemeldeten Personen können einen Thread oder eine Antwort melden. Moderatoren können einen Beitrag entfernen (seine Bilder werden sofort gelöscht), einen Thread schließen, sodass nur Moderatoren antworten können, oder ihn anheften. Jede Entfernung und jede Schließung hat einen Grund, den die Person sieht, die den Beitrag geschrieben hat. Ein entfernter Beitrag bleibt für sie und für Moderatoren sichtbar, damit die Entscheidung überprüft werden kann; Administratoren können seinen Text wiederherstellen.

**terms, after:**

> - Alle angemeldeten Personen können einen Thread oder eine Antwort melden.
> - Die Moderation kann einen Beitrag entfernen (seine Bilder werden sofort gelöscht), einen Thread sperren, sodass nur die Moderation antworten kann, oder ihn anheften. Jede Entfernung und Sperrung kommt mit einem Grund, den die Autorin oder der Autor sieht.
> - Ein entfernter Beitrag bleibt für die Autorin oder den Autor und die Moderation sichtbar, damit er geprüft werden kann. Die Administratoren können seinen Text wiederherstellen.

**terms, before:**

> Alle angemeldeten Personen können ein Projekt, ein Profil oder einen Build-Log-Eintrag melden. Moderatoren können eine Meldung ablehnen, ein Projekt entfernen, Profilfelder leeren (Profil- und Titelbild, Kurzbeschreibung und „Über mich“, Links), ein Konto bis zu 7 Tage stummschalten (du kannst weiter lesen, Einstellungen ändern, deine Daten herunterladen oder löschen, aber nichts veröffentlichen) oder es bis zu 14 Tage sperren (du wirst abgemeldet, kannst dich nicht anmelden, und Profil und Projekte sind nicht öffentlich). Jede Entscheidung hat einen Grund, den du siehst. Über längere oder dauerhafte Sanktionen entscheiden nur die Administratoren der Website; sie können auch Projekte verbergen oder Konten sperren. Das Löschen deines Kontos beendet keine Sperre (siehe [Datenschutzerklärung](/legal/privacy/)). Wenn du denkst, dass wir einen Fehler gemacht haben, schreib an [{{ contact_email }}](mailto:{{ contact_email }}).

**terms, after:**

> Alle angemeldeten Personen können ein Projekt, ein Profil oder einen Build-Log-Eintrag melden. Die Moderation kann:
>
> - eine Meldung zurückweisen;
> - ein Projekt entfernen;
> - Profilfelder leeren (Bild und Titelbild, Kurzbeschreibung und „Über mich“, Links);
> - ein Konto für bis zu 7 Tage stummschalten: Du kannst weiter lesen, deine Einstellungen ändern, deine Daten herunterladen oder löschen, aber nichts veröffentlichen;
> - ein Konto für bis zu 14 Tage sperren: Du wirst abgemeldet, kannst dich nicht anmelden, und dein Profil und deine Projekte sind nicht öffentlich.
>
> Jede Entscheidung kommt mit einem Grund, den du siehst. Über längere oder dauerhafte Sanktionen entscheiden nur die Administratoren der Website, die auch Projekte verbergen oder Konten sperren können. Das Löschen deines Kontos beendet eine Sperre nicht (siehe [Datenschutzerklärung](/legal/privacy/)). Wenn du glaubst, dass wir einen Fehler gemacht haben, schreib an [{{ contact_email }}](mailto:{{ contact_email }}).

### es

**privacy, before:**

> **Cuando inicias sesión con GitHub.** Recibimos de GitHub el id de tu cuenta, tu login, tu nombre, tu biografía, el enlace a tu avatar y los demás campos públicos de tu perfil de GitHub, además de las direcciones de correo de tu cuenta de GitHub. Solo pedimos a GitHub `read:user` y `user:email`: nunca obtenemos acceso a tus repositorios, ni privados ni públicos, a través de tu cuenta. No conservamos tu token de acceso de GitHub después de iniciar sesión. Necesitamos estos datos para crear tu cuenta y reconocerte la próxima vez (ejecución de nuestro acuerdo contigo). Tu usuario de GitHub se actualiza cada vez que inicias sesión, así tu perfil siempre enlaza a tu cuenta actual de GitHub.

**privacy, after:**

> **Cuando inicias sesión con GitHub.** GitHub nos envía:
>
> - el id de tu cuenta, tu login, nombre, biografía, enlace al avatar y los demás campos públicos de tu perfil de GitHub;
> - las direcciones de correo de tu cuenta de GitHub.
>
> Solo pedimos a GitHub dos permisos: `read:user` y `user:email`. A través de tu cuenta nunca obtenemos acceso a tus repositorios, ni privados ni públicos. No guardamos tu token de acceso de GitHub después de iniciar sesión. Necesitamos estos datos para crear tu cuenta y reconocerte la próxima vez (ejecución de nuestro acuerdo contigo). Tu login de GitHub se actualiza en cada inicio de sesión, así que tu perfil siempre enlaza a tu cuenta actual de GitHub.

**privacy, before:**

> - *Repo owner:* consultamos la API pública de GitHub sobre el repositorio que enlazas y guardamos su identificador, el identificador de la cuenta propietaria, si es tuyo, su fecha de creación y su campo Website, el primer commit de su historial (identificador y fecha), tu número de commits, las fechas de tu primer y último commit, el número de semanas con commits tuyos y el estado de una revisión manual cuando hace falta. Lo volvemos a comprobar cada semana. La lista de otras personas que contribuyen se lee durante la comprobación y no se guarda. Si usas el archivo de verificación para un repositorio de una organización, también guardamos si se encontró.

**privacy, after:**

> - *Repo owner:* consultamos la API pública de GitHub sobre el repositorio que enlazas y lo comprobamos de nuevo cada semana. La lista de otros colaboradores de GitHub se lee durante la comprobación y no se guarda. Guardamos:
>     - su id, el id de la cuenta de su propietario, si es tuyo, su fecha de creación y su campo Website;
>     - el primer commit de su historial (id y fecha);
>     - tu número de commits, las fechas de tu primer y último commit y el número de semanas con commits tuyos;
>     - el estado de una revisión manual, cuando hace falta;
>     - si se encontró el archivo de verificación, cuando lo usas para un repositorio de una organización.

**privacy, before:**

> **Denuncias y moderación.** Si denuncias un proyecto, un perfil o una entrada del registro de desarrollo, guardamos el motivo y los detalles que escribas. Las denuncias las ven los moderadores (personas con la insignia de moderador) y el equipo. Para decidir, también ven el contenido denunciado y el historial de la persona denunciada en {{ site_name }}: cuándo se unió, sanciones anteriores, otras denuncias sobre ella y proyectos retirados. Las páginas de moderación no muestran direcciones de correo. A la persona denunciada nunca se le dice quién la denunció. Cuando los moderadores actúan, guardamos la decisión y su motivo: un proyecto retirado conserva su contenido y el motivo (solo lo ven tú, los moderadores y el equipo), los campos de perfil vaciados (foto y portada, descripción breve y «Acerca de», o enlaces) se borran, y los silencios y bloqueos se guardan con su motivo, inicio y fin. Ves el motivo en un aviso en el sitio, que guardamos hasta que eliminas tu cuenta. Las decisiones sobre ti y estos avisos se incluyen en «Descargar mis datos». Para recurrir una decisión, escribe a [{{ contact_email }}](mailto:{{ contact_email }}).

**privacy, after:**

> **Denuncias y moderación.**
>
> - Si denuncias un proyecto, un perfil o una entrada del registro de desarrollo, guardamos el motivo y los detalles que escribas.
> - Las denuncias las ven los moderadores (personas con la insignia de moderador) y el equipo. Para decidir, también ven el contenido denunciado y el historial de la persona denunciada en {{ site_name }}: cuándo se unió, sanciones anteriores, otras denuncias sobre ella y proyectos retirados. Las páginas de moderación no muestran direcciones de correo.
> - A la persona denunciada nunca se le dice quién la denunció.
> - Cuando los moderadores actúan, guardamos la decisión y su motivo. Un proyecto retirado conserva su contenido y el motivo (solo lo ves tú, los moderadores y el equipo). Los campos del perfil que se vacían (foto y portada, titular y «Sobre mí», o enlaces) se borran. Los silencios y bloqueos se guardan con su motivo, inicio y fin.
> - Ves el motivo en un aviso en el sitio, que guardamos hasta que eliminas tu cuenta. Las decisiones sobre ti y estos avisos están incluidos en «Descargar mis datos».
> - Para recurrir una decisión, escribe a [{{ contact_email }}](mailto:{{ contact_email }}).
>
> **Comunidad.** Cuando publicas en la comunidad guardamos:

**privacy, before:**

> **Comunidad.** Cuando publicas en la comunidad guardamos tus hilos (sección, título, texto, fechas y si un hilo fue editado, fijado, cerrado o retirado), tus respuestas (texto, el sticker que elegiste, a qué publicación responden) y las imágenes que adjuntas. Las imágenes se vuelven a codificar como las capturas de pantalla: se eliminan metadatos ocultos como la ubicación GPS, los nombres de archivo son aleatorios y en nuestro propio servidor guardamos una copia de hasta 1600 px y una miniatura de 640 px. Las publicaciones, sus imágenes, su número de votos y tu nombre de usuario en ellas son **públicos**. También guardamos tus votos; nadie ve quién votó qué, ni en el sitio ni en el panel de administración. Cuando eliminas una publicación, su texto, su sticker y sus imágenes se eliminan en el acto (el título de un hilo se queda mientras haya respuestas de otras personas debajo y aparece como «[eliminado]»). Cuando los moderadores retiran una publicación, sus imágenes se eliminan en el acto y su texto se conserva con el motivo, visible solo para ti, los moderadores y el personal. Los moderadores ven las publicaciones denunciadas junto con el historial de su autor, como en otras denuncias.

**privacy, after:**

> - tus hilos: sección, título, texto, fechas y si un hilo fue editado, fijado, cerrado o retirado;
> - tus respuestas: texto, el sticker que elegiste y a qué publicación responden;
> - las imágenes que adjuntas. Se recodifican como las capturas de pantalla: se eliminan los metadatos ocultos, como la ubicación GPS, los nombres de archivo son aleatorios y guardamos una copia de hasta 1600 px y una miniatura de 640 px en nuestro propio servidor.
>
> Las publicaciones, sus imágenes, su número de votos y tu nombre de usuario en ellas son **públicos**. También guardamos tus votos; nadie ve quién votó qué, ni en el sitio ni en el panel de administración.
>
> Cuando eliminas una publicación, su texto, sticker e imágenes se borran al momento. El título de un hilo se queda mientras haya respuestas de otras personas debajo, y se muestra como «[eliminado]». Cuando los moderadores retiran una publicación, sus imágenes se borran al momento y su texto se guarda con el motivo, visible solo para ti, los moderadores y el equipo. Los moderadores ven las publicaciones denunciadas junto con el historial de su autor, como en otras denuncias.

**privacy, before:**

> **Registro de errores.** Cuando algo falla, la aplicación escribe una entrada breve en un archivo de errores de nuestro servidor: la hora, un número de referencia aleatorio (el que aparece en la página de error), el método de la solicitud, la dirección de la página sin lo que va después de `?` y con los nombres de usuario sustituidos por `[user]`, el estado de la respuesta, la parte del código que falló y el mensaje técnico, del que se eliminan direcciones de correo, direcciones IP y todo lo que parezca una contraseña o una clave. Las páginas no encontradas van a un archivo aparte, cada dirección como mucho una vez por minuto. Estos archivos nunca contienen tu dirección IP, datos del navegador, cookies, lo que escribes en los formularios, tu correo ni tu nombre de usuario. Cada archivo está limitado a 5 MB más 5 copias anteriores; al llegar al límite se borra la más antigua.

**privacy, after:**

> **Registro de errores.** Cuando algo falla, la aplicación escribe una entrada corta en un archivo de errores de nuestro servidor. La entrada contiene:
>
> - la hora y un número de referencia aleatorio (el que aparece en la página de error);
> - el método de la solicitud y la dirección de la página sin lo que va después de `?`, con los nombres de usuario sustituidos por `[user]`;
> - el estado de la respuesta y la parte del código que falló;
> - el mensaje técnico de error, sin direcciones de correo, direcciones IP ni nada que parezca una contraseña o una clave.
>
> Las páginas no encontradas se escriben en un archivo aparte, cada dirección como mucho una vez por minuto. Estos archivos nunca contienen tu dirección IP, datos del navegador, cookies, lo que escribiste en un formulario, tu correo ni tu nombre de usuario. Cada archivo está limitado a 5 MB más 5 copias anteriores; al llegar al límite se borra la más antigua.

**terms, before:**

> - Nos das permiso para almacenarlos, mostrarlos y compartirlos en {{ site_name }} (páginas de proyecto, perfiles, novedades, búsqueda e insignias) mientras estén publicados. Este permiso termina cuando los eliminas, salvo por las copias que otras personas ya hayan insertado o guardado.

**terms, after:**

> - Nos das permiso para almacenarlos, mostrarlos y compartirlos en {{ site_name }} (páginas de proyecto, perfiles, la página Para ti, búsqueda e insignias) mientras estén publicados. Este permiso termina cuando los eliminas, salvo por las copias que otras personas ya hayan insertado o guardado.

**terms, before:**

> - Cualquier persona con sesión iniciada puede denunciar un hilo o una respuesta. Los moderadores pueden retirar una publicación (sus imágenes se eliminan en el acto), cerrar un hilo para que solo respondan los moderadores o fijarlo. Cada retirada y cada cierre tienen un motivo que la persona autora ve. Una publicación retirada sigue visible para su autor y para los moderadores, para poder revisar la decisión; los administradores pueden restaurar su texto.

**terms, after:**

> - Cualquier persona con sesión iniciada puede denunciar un hilo o una respuesta.
> - Los moderadores pueden retirar una publicación (sus imágenes se borran al momento), cerrar un hilo para que solo los moderadores puedan responder, o fijarlo. Cada retirada y cierre lleva un motivo que ve el autor.
> - Una publicación retirada sigue visible para su autor y para los moderadores, para que se pueda revisar. Los administradores pueden restaurar su texto.

**terms, before:**

> Cualquier persona con sesión iniciada puede denunciar un proyecto, un perfil o una entrada del registro de cambios. Los moderadores pueden descartar una denuncia, retirar un proyecto, vaciar campos del perfil (foto y portada, descripción breve y «Acerca de», enlaces), silenciar una cuenta hasta 7 días (puedes seguir leyendo, cambiar tus ajustes, descargar o eliminar tus datos, pero no publicar) o bloquearla hasta 14 días (se cierra tu sesión, no puedes iniciarla y tu perfil y proyectos no son públicos). Cada decisión tiene un motivo que ves. Las sanciones más largas o permanentes solo las deciden los administradores del sitio, que también pueden ocultar proyectos o suspender cuentas. Eliminar tu cuenta no termina un bloqueo (consulta la [Política de privacidad](/legal/privacy/)). Si crees que nos equivocamos, escribe a [{{ contact_email }}](mailto:{{ contact_email }}).

**terms, after:**

> Cualquier persona con sesión iniciada puede denunciar un proyecto, un perfil o una entrada del registro de desarrollo. Los moderadores pueden:
>
> - descartar una denuncia;
> - retirar un proyecto;
> - vaciar campos del perfil (foto y portada, titular y «Sobre mí», enlaces);
> - silenciar una cuenta hasta 7 días: puedes seguir leyendo, cambiar tus ajustes, descargar o eliminar tus datos, pero no publicar;
> - bloquear una cuenta hasta 14 días: se cierra tu sesión, no puedes iniciarla y tu perfil y tus proyectos no son públicos.
>
> Cada decisión lleva un motivo que tú ves. Las sanciones más largas o permanentes solo las deciden los administradores del sitio, que también pueden ocultar proyectos o suspender cuentas. Eliminar tu cuenta no termina un bloqueo (consulta la [Política de privacidad](/legal/privacy/)). Si crees que nos equivocamos, escribe a [{{ contact_email }}](mailto:{{ contact_email }}).

### fr

**privacy, before:**

> **Lorsque vous vous connectez avec GitHub.** Nous recevons de GitHub l’identifiant de votre compte, votre login, votre nom, votre bio, le lien de votre avatar et les autres champs publics de votre profil GitHub, ainsi que les adresses e-mail de votre compte GitHub. Nous demandons à GitHub uniquement `read:user` et `user:email` : nous n’obtenons jamais d’accès à vos dépôts, privés ou publics, via votre compte. Nous ne conservons pas votre jeton d’accès GitHub après la connexion. Nous avons besoin de ces données pour créer votre compte et vous reconnaître la fois suivante (exécution de notre accord avec vous). Votre identifiant GitHub est mis à jour à chaque connexion, pour que votre profil mène toujours à votre compte GitHub actuel.

**privacy, after:**

> **Lorsque vous vous connectez avec GitHub.** GitHub nous transmet :
>
> - l’identifiant de votre compte, votre login, votre nom, votre bio, le lien de votre avatar et les autres champs publics de votre profil GitHub ;
> - les adresses e-mail de votre compte GitHub.
>
> Nous ne demandons à GitHub que deux autorisations : `read:user` et `user:email`. Par votre compte, nous n’avons jamais accès à vos dépôts, ni privés ni publics. Nous ne gardons pas votre jeton d’accès GitHub après la connexion. Ces données nous servent à créer votre compte et à vous reconnaître la fois suivante (exécution de notre accord avec vous). Votre login GitHub est mis à jour à chaque connexion, afin que votre profil renvoie toujours vers votre compte GitHub actuel.

**privacy, before:**

> - *Repo owner :* nous interrogeons l’API publique de GitHub sur le dépôt que vous liez et enregistrons son identifiant, l’identifiant du compte propriétaire, s’il vous appartient, sa date de création et son champ Website, le premier commit de son historique (identifiant et date), votre nombre de commits, les dates de votre premier et de votre dernier commit, le nombre de semaines avec vos commits et l’état d’une vérification manuelle si elle est nécessaire. Nous le recontrôlons chaque semaine. La liste des autres contributeurs est lue pendant le contrôle et n’est pas enregistrée. Si vous utilisez le fichier de vérification pour le dépôt d’une organisation, nous enregistrons aussi s’il a été trouvé.

**privacy, after:**

> - *Repo owner :* nous interrogeons l’API publique de GitHub sur le dépôt que vous liez, et nous le contrôlons de nouveau chaque semaine. La liste des autres contributeurs sur GitHub est lue pendant le contrôle et n’est pas conservée. Nous conservons :
>     - son identifiant, l’identifiant du compte de son propriétaire, s’il vous appartient, sa date de création et son champ Website ;
>     - le premier commit de son historique (identifiant et date) ;
>     - votre nombre de commits, les dates de votre premier et de votre dernier commit, et le nombre de semaines avec vos commits ;
>     - l’état d’une vérification manuelle, quand elle est nécessaire ;
>     - si le fichier de vérification a été trouvé, quand vous l’utilisez pour le dépôt d’une organisation.

**privacy, before:**

> **Signalements et modération.** Si vous signalez un projet, un profil ou une entrée du journal de développement, nous enregistrons le motif et les détails que vous écrivez. Les signalements sont vus par les modérateurs (personnes ayant le badge de modérateur) et l’équipe. Pour décider, ils voient aussi le contenu signalé et l’historique de la personne signalée sur {{ site_name }} : sa date d’inscription, ses sanctions précédentes, les autres signalements la concernant et ses projets retirés. Les pages de modération n’affichent pas les adresses e-mail. La personne signalée n’apprend jamais qui l’a signalée. Quand les modérateurs agissent, nous enregistrons la décision et son motif : un projet retiré garde son contenu et le motif (seuls vous, les modérateurs et l’équipe le voient), les champs de profil effacés (photo et couverture, phrase d’accroche et « À propos », ou liens) sont supprimés, et les mises en sourdine et bannissements sont enregistrés avec leur motif, leur début et leur fin. Vous voyez le motif dans un avis sur le site, que nous gardons jusqu’à la suppression de votre compte. Les décisions vous concernant et ces avis figurent dans « Télécharger mes données ». Pour contester une décision, écrivez à [{{ contact_email }}](mailto:{{ contact_email }}).

**privacy, after:**

> **Signalements et modération.**
>
> - Si vous signalez un projet, un profil ou une entrée du journal de développement, nous conservons le motif et les détails que vous écrivez.
> - Les signalements sont vus par les modérateurs (les personnes avec le badge de modérateur) et l’équipe. Pour décider, ils voient aussi le contenu signalé et l’historique de la personne signalée sur {{ site_name }} : sa date d’arrivée, ses sanctions passées, les autres signalements la concernant et ses projets retirés. Les pages de modération n’affichent pas d’adresses e-mail.
> - La personne signalée n’apprend jamais qui l’a signalée.
> - Quand les modérateurs agissent, nous conservons la décision et son motif. Un projet retiré garde son contenu et le motif (seuls vous, les modérateurs et l’équipe le voient). Les champs du profil effacés (photo et couverture, accroche et « À propos », ou liens) sont supprimés. Les mises en sourdine et les bannissements sont conservés avec leur motif, leur début et leur fin.
> - Vous voyez le motif dans un avis sur le site, que nous gardons jusqu’à la suppression de votre compte. Les décisions vous concernant et ces avis figurent dans « Télécharger mes données ».
> - Pour contester une décision, écrivez à [{{ contact_email }}](mailto:{{ contact_email }}).
>
> **Communauté.** Quand vous publiez dans la communauté, nous conservons :

**privacy, before:**

> **Communauté.** Quand vous publiez dans la communauté, nous conservons vos fils (rubrique, titre, texte, dates, et si un fil a été modifié, épinglé, verrouillé ou retiré), vos réponses (texte, l’autocollant choisi, le message auquel elles répondent) et les images que vous joignez. Les images sont réencodées comme les captures d’écran : les métadonnées cachées comme la position GPS sont supprimées, les noms de fichiers sont aléatoires, et nous conservons sur notre propre serveur une copie jusqu’à 1600 px et une miniature de 640 px. Les messages, leurs images, leur nombre de votes et votre nom d’utilisateur sont **publics**. Nous conservons aussi vos votes ; personne ne voit qui a voté pour quoi, ni sur le site ni dans l’administration. Quand vous supprimez un message, son texte, son autocollant et ses images sont supprimés immédiatement (le titre d’un fil reste tant que des réponses d’autres personnes s’y trouvent, affiché comme « [supprimé] »). Quand les modérateurs retirent un message, ses images sont supprimées immédiatement et son texte est conservé avec le motif, visible seulement par vous, les modérateurs et l’équipe. Les modérateurs voient les messages signalés avec l’historique de leur auteur, comme pour les autres signalements.

**privacy, after:**

> - vos fils : rubrique, titre, texte, dates, et si un fil a été modifié, épinglé, verrouillé ou retiré ;
> - vos réponses : texte, l’autocollant choisi, et le message auquel elles répondent ;
> - les images que vous joignez. Elles sont réencodées comme les captures d’écran : les métadonnées cachées comme la position GPS sont supprimées, les noms de fichiers sont aléatoires, et nous gardons une copie jusqu’à 1600 px et une vignette de 640 px sur notre propre serveur.
>
> Les messages, leurs images, leur nombre de votes et votre nom d’utilisateur sur ceux-ci sont **publics**. Nous conservons aussi vos votes ; personne ne voit qui a voté pour quoi, ni sur le site ni dans l’administration.
>
> Quand vous supprimez un message, son texte, son autocollant et ses images sont supprimés aussitôt. Le titre d’un fil reste tant que des réponses d’autres personnes se trouvent dessous, et s’affiche comme « [supprimé] ». Quand les modérateurs retirent un message, ses images sont supprimées aussitôt et son texte est conservé avec le motif, visible seulement par vous, les modérateurs et l’équipe. Les modérateurs voient les messages signalés avec l’historique de leur auteur, comme pour les autres signalements.

**privacy, before:**

> **Journal des erreurs.** Quand quelque chose échoue, l’application écrit une courte entrée dans un fichier d’erreurs sur notre serveur : l’heure, un numéro de référence aléatoire (celui affiché sur la page d’erreur), la méthode de la requête, l’adresse de la page sans ce qui suit un `?` et avec les noms d’utilisateur remplacés par `[user]`, le statut de la réponse, la partie du code qui a échoué et le message technique, dont sont retirés les adresses e-mail, les adresses IP et tout ce qui ressemble à un mot de passe ou une clé. Les pages introuvables sont écrites dans un fichier séparé, chaque adresse au plus une fois par minute. Ces fichiers ne contiennent jamais votre adresse IP, les informations de votre navigateur, vos cookies, ce que vous saisissez dans les formulaires, votre adresse e-mail ni votre nom d’utilisateur. Chaque fichier est limité à 5 Mo plus 5 copies plus anciennes ; une fois la limite atteinte, la plus ancienne est supprimée.

**privacy, after:**

> **Journal des erreurs.** Quand quelque chose échoue, l’application écrit une courte entrée dans un fichier d’erreurs sur notre serveur. L’entrée contient :
>
> - l’heure et un numéro de référence aléatoire (celui affiché sur la page d’erreur) ;
> - la méthode de la requête et l’adresse de la page sans ce qui suit un `?`, avec les noms d’utilisateur remplacés par `[user]` ;
> - le statut de la réponse et la partie du code qui a échoué ;
> - le message d’erreur technique, dont on a retiré les adresses e-mail, les adresses IP et tout ce qui ressemble à un mot de passe ou à une clé.
>
> Les pages introuvables sont écrites dans un fichier séparé, chaque adresse au plus une fois par minute. Ces fichiers ne contiennent jamais votre adresse IP, les informations de votre navigateur, vos cookies, ce que vous avez saisi dans un formulaire, votre adresse e-mail ni votre nom d’utilisateur. Chaque fichier est limité à 5 Mo plus 5 copies plus anciennes ; à la limite, la plus ancienne est supprimée.

**terms, before:**

> - Vous nous autorisez à les stocker, les afficher et les partager sur {{ site_name }} (pages de projet, profils, fil, recherche et badges) tant qu’ils sont publiés. Cette autorisation prend fin lorsque vous les supprimez, sauf pour les copies que d’autres ont déjà intégrées ou enregistrées.

**terms, after:**

> - Vous nous autorisez à les stocker, les afficher et les partager sur {{ site_name }} (pages de projet, profils, page Pour vous, recherche et badges) tant qu’ils sont publiés. Cette autorisation prend fin lorsque vous les supprimez, sauf pour les copies que d’autres ont déjà intégrées ou enregistrées.

**terms, before:**

> - Toute personne connectée peut signaler un fil ou une réponse. Les modérateurs peuvent retirer un message (ses images sont supprimées immédiatement), verrouiller un fil pour que seuls les modérateurs puissent répondre, ou l’épingler. Chaque retrait et chaque verrouillage s’accompagne d’un motif que l’auteur voit. Un message retiré reste visible pour son auteur et pour les modérateurs, afin que la décision puisse être revue ; les administrateurs peuvent en restaurer le texte.

**terms, after:**

> - Toute personne connectée peut signaler un fil ou une réponse.
> - Les modérateurs peuvent retirer un message (ses images sont supprimées aussitôt), verrouiller un fil pour que seuls les modérateurs puissent répondre, ou l’épingler. Chaque retrait et chaque verrouillage s’accompagne d’un motif que l’auteur voit.
> - Un message retiré reste visible pour son auteur et pour les modérateurs, afin de pouvoir être réexaminé. Les administrateurs peuvent restaurer son texte.

**terms, before:**

> Toute personne connectée peut signaler un projet, un profil ou une entrée du journal de construction. Les modérateurs peuvent rejeter un signalement, retirer un projet, effacer des champs du profil (photo et couverture, phrase d’accroche et « À propos », liens), mettre un compte en sourdine jusqu’à 7 jours (vous pouvez toujours lire, modifier vos paramètres, télécharger ou supprimer vos données, mais pas publier) ou le bannir jusqu’à 14 jours (vous êtes déconnecté, ne pouvez pas vous connecter, et votre profil et vos projets ne sont pas publics). Chaque décision est accompagnée d’un motif que vous voyez. Les sanctions plus longues ou permanentes sont décidées uniquement par les administrateurs du site, qui peuvent aussi masquer des projets ou suspendre des comptes. Supprimer votre compte ne met pas fin à un bannissement (voir la [Politique de confidentialité](/legal/privacy/)). Si vous pensez que nous nous sommes trompés, écrivez à [{{ contact_email }}](mailto:{{ contact_email }}).

**terms, after:**

> Toute personne connectée peut signaler un projet, un profil ou une entrée du journal de développement. Les modérateurs peuvent :
>
> - rejeter un signalement ;
> - retirer un projet ;
> - effacer des champs du profil (photo et couverture, accroche et « À propos », liens) ;
> - mettre un compte en sourdine jusqu’à 7 jours : vous pouvez toujours lire, modifier vos paramètres, télécharger ou supprimer vos données, mais pas publier ;
> - bannir un compte jusqu’à 14 jours : vous êtes déconnecté, vous ne pouvez pas vous reconnecter, et votre profil et vos projets ne sont pas publics.
>
> Chaque décision s’accompagne d’un motif que vous voyez. Les sanctions plus longues ou définitives sont décidées uniquement par les administrateurs du site, qui peuvent aussi masquer des projets ou suspendre des comptes. Supprimer votre compte ne met pas fin à un bannissement (voir la [Politique de confidentialité](/legal/privacy/)). Si vous pensez que nous nous sommes trompés, écrivez à [{{ contact_email }}](mailto:{{ contact_email }}).

### pt-br

**privacy, before:**

> **Quando você entra com o GitHub.** Recebemos do GitHub o id da sua conta, seu login, nome, bio, o link do seu avatar e os demais campos públicos do seu perfil do GitHub, além dos endereços de e-mail da sua conta do GitHub. Pedimos ao GitHub apenas `read:user` e `user:email`: nunca obtemos acesso aos seus repositórios, privados ou públicos, por meio da sua conta. Não guardamos seu token de acesso do GitHub depois do login. Precisamos disso para criar sua conta e reconhecer você na próxima vez (execução do nosso acordo com você). O seu login do GitHub é atualizado a cada entrada, então o seu perfil sempre leva à sua conta atual do GitHub.

**privacy, after:**

> **Quando você entra com o GitHub.** O GitHub nos envia:
>
> - o id da sua conta, seu login, nome, bio, link do avatar e os outros campos públicos do seu perfil do GitHub;
> - os endereços de e-mail da sua conta do GitHub.
>
> Pedimos ao GitHub só duas permissões: `read:user` e `user:email`. Pela sua conta, nunca temos acesso aos seus repositórios, nem privados nem públicos. Não guardamos seu token de acesso do GitHub depois do login. Precisamos desses dados para criar sua conta e reconhecer você da próxima vez (execução do nosso acordo com você). Seu login do GitHub é atualizado a cada entrada, então seu perfil sempre leva à sua conta atual do GitHub.

**privacy, before:**

> - *Repo owner:* consultamos a API pública do GitHub sobre o repositório que você vincula e guardamos o id dele, o id da conta dona, se ele é seu, a data de criação e o campo Website, o primeiro commit do histórico (id e data), o seu número de commits, as datas do seu primeiro e último commit, o número de semanas com commits seus e o estado de uma revisão manual, quando for necessária. Verificamos de novo toda semana. A lista de outras pessoas que contribuem é lida durante a verificação e não é guardada. Se você usa o arquivo de verificação em um repositório de organização, também guardamos se ele foi encontrado.

**privacy, after:**

> - *Repo owner:* consultamos a API pública do GitHub sobre o repositório que você vincula e o verificamos de novo toda semana. A lista de outros colaboradores do GitHub é lida durante a verificação e não é guardada. Guardamos:
>     - o id dele, o id da conta do dono, se ele é seu, a data de criação e o campo Website;
>     - o primeiro commit do histórico (id e data);
>     - o número dos seus commits, as datas do seu primeiro e último commit e o número de semanas com commits seus;
>     - o estado de uma revisão manual, quando ela é necessária;
>     - se o arquivo de verificação foi encontrado, quando você o usa em um repositório de organização.

**privacy, before:**

> **Denúncias e moderação.** Se você denunciar um projeto, um perfil ou uma entrada do diário de desenvolvimento, guardamos o motivo e os detalhes que você escrever. As denúncias são vistas pelos moderadores (pessoas com o selo de moderador) e pela equipe. Para decidir, eles também veem o conteúdo denunciado e o histórico da pessoa denunciada no {{ site_name }}: quando ela entrou, sanções anteriores, outras denúncias sobre ela e projetos removidos. As páginas de moderação não mostram endereços de e-mail. A pessoa denunciada nunca fica sabendo quem a denunciou. Quando os moderadores agem, guardamos a decisão e o motivo: um projeto removido mantém o conteúdo e o motivo (só você, os moderadores e a equipe veem), os campos de perfil limpos (foto e capa, resumo curto e “Sobre”, ou links) são apagados, e silenciamentos e banimentos são guardados com motivo, início e fim. Você vê o motivo em um aviso no site, que guardamos até você excluir sua conta. As decisões sobre você e esses avisos estão em “Baixar meus dados”. Para recorrer de uma decisão, escreva para [{{ contact_email }}](mailto:{{ contact_email }}).

**privacy, after:**

> **Denúncias e moderação.**
>
> - Se você denunciar um projeto, um perfil ou uma entrada do diário de desenvolvimento, guardamos o motivo e os detalhes que você escrever.
> - As denúncias são vistas pelos moderadores (pessoas com o badge de moderador) e pela equipe. Para decidir, eles também veem o conteúdo denunciado e o histórico da pessoa denunciada no {{ site_name }}: quando ela entrou, sanções anteriores, outras denúncias sobre ela e projetos removidos. As páginas de moderação não mostram endereços de e-mail.
> - A pessoa denunciada nunca fica sabendo quem a denunciou.
> - Quando os moderadores agem, guardamos a decisão e o motivo. Um projeto removido mantém o conteúdo e o motivo (só você, os moderadores e a equipe veem). Os campos do perfil limpos (foto e capa, título e “Sobre”, ou links) são apagados. Silenciamentos e banimentos são guardados com motivo, início e fim.
> - Você vê o motivo em um aviso no site, que guardamos até você excluir sua conta. As decisões sobre você e esses avisos estão em “Baixar meus dados”.
> - Para recorrer de uma decisão, escreva para [{{ contact_email }}](mailto:{{ contact_email }}).
>
> **Comunidade.** Quando você publica na comunidade, guardamos:

**privacy, before:**

> **Comunidade.** Quando você publica na comunidade, guardamos seus tópicos (seção, título, texto, datas e se o tópico foi editado, fixado, trancado ou removido), suas respostas (texto, a figurinha escolhida, a qual publicação elas respondem) e as imagens que você anexa. As imagens são recodificadas como as capturas de tela: metadados ocultos, como a localização GPS, são removidos, os nomes dos arquivos são aleatórios, e guardamos no nosso próprio servidor uma cópia de até 1600 px e uma miniatura de 640 px. As publicações, suas imagens, o número de votos e seu nome de usuário nelas são **públicos**. Também guardamos seus votos; ninguém vê quem votou em quê, nem no site nem no painel de administração. Quando você exclui uma publicação, o texto, a figurinha e as imagens dela são apagados na hora (o título de um tópico fica enquanto houver respostas de outras pessoas embaixo, mostrado como “[excluído]”). Quando os moderadores removem uma publicação, as imagens dela são apagadas na hora e o texto é mantido com o motivo, visível só para você, os moderadores e a equipe. Os moderadores veem as publicações denunciadas junto com o histórico de quem as escreveu, como nas outras denúncias.

**privacy, after:**

> - seus tópicos: seção, título, texto, datas e se um tópico foi editado, fixado, trancado ou removido;
> - suas respostas: texto, a figurinha que você escolheu e a qual publicação elas respondem;
> - as imagens que você anexa. Elas são recodificadas como as capturas de tela: metadados ocultos, como a localização GPS, são removidos, os nomes dos arquivos são aleatórios e guardamos uma cópia de até 1600 px e uma miniatura de 640 px no nosso próprio servidor.
>
> As publicações, suas imagens, o número de votos e seu nome de usuário nelas são **públicos**. Também guardamos seus votos; ninguém vê quem votou em quê, nem no site nem na administração.
>
> Quando você exclui uma publicação, o texto, a figurinha e as imagens são apagados na hora. O título de um tópico fica enquanto houver respostas de outras pessoas embaixo dele, mostrado como “[excluído]”. Quando os moderadores removem uma publicação, as imagens são apagadas na hora e o texto é guardado com o motivo, visível só para você, os moderadores e a equipe. Os moderadores veem as publicações denunciadas junto com o histórico do autor, como nas outras denúncias.

**privacy, before:**

> **Registro de erros.** Quando algo falha, o aplicativo grava uma entrada curta em um arquivo de erros no nosso servidor: a hora, um número de referência aleatório (o mesmo mostrado na página de erro), o método da requisição, o endereço da página sem o que vem depois de `?` e com nomes de usuário trocados por `[user]`, o status da resposta, a parte do código que falhou e a mensagem técnica, da qual são removidos endereços de e-mail, endereços IP e tudo o que pareça senha ou chave. Páginas não encontradas vão para um arquivo separado, cada endereço no máximo uma vez por minuto. Esses arquivos nunca contêm seu endereço IP, dados do navegador, cookies, o que você digita em formulários, seu e-mail nem seu nome de usuário. Cada arquivo é limitado a 5 MB mais 5 cópias anteriores; ao atingir o limite, a mais antiga é apagada.

**privacy, after:**

> **Registro de erros.** Quando algo falha, o aplicativo grava uma entrada curta em um arquivo de erros no nosso servidor. A entrada contém:
>
> - a hora e um número de referência aleatório (o que aparece na página de erro);
> - o método da requisição e o endereço da página sem o que vem depois de `?`, com os nomes de usuário trocados por `[user]`;
> - o status da resposta e a parte do código que falhou;
> - a mensagem técnica de erro, sem endereços de e-mail, endereços IP e qualquer coisa que pareça uma senha ou chave.
>
> Páginas não encontradas vão para um arquivo separado, cada endereço no máximo uma vez por minuto. Esses arquivos nunca contêm seu endereço IP, dados do navegador, cookies, o que você digitou em um formulário, seu e-mail ou seu nome de usuário. Cada arquivo é limitado a 5 MB mais 5 cópias anteriores; ao atingir o limite, a mais antiga é apagada.

**terms, before:**

> - Você nos dá permissão para armazená-los, exibi-los e compartilhá-los no {{ site_name }} (páginas de projeto, perfis, feed, busca e badges) enquanto estiverem publicados. Essa permissão termina quando você os exclui, exceto para cópias que outras pessoas já incorporaram ou salvaram.

**terms, after:**

> - Você nos dá permissão para armazená-los, exibi-los e compartilhá-los no {{ site_name }} (páginas de projeto, perfis, página Para você, busca e badges) enquanto estiverem publicados. Essa permissão termina quando você os exclui, exceto para cópias que outras pessoas já incorporaram ou salvaram.

**terms, before:**

> - Qualquer pessoa conectada pode denunciar um tópico ou uma resposta. Os moderadores podem remover uma publicação (as imagens dela são apagadas na hora), trancar um tópico para que só moderadores respondam ou fixá-lo. Toda remoção e todo trancamento vêm com um motivo que quem escreveu vê. Uma publicação removida continua visível para quem a escreveu e para os moderadores, para que a decisão possa ser revista; os administradores podem restaurar o texto.

**terms, after:**

> - Qualquer pessoa conectada pode denunciar um tópico ou uma resposta.
> - Os moderadores podem remover uma publicação (as imagens são apagadas na hora), trancar um tópico para que só os moderadores possam responder, ou fixá-lo. Cada remoção e trancamento vem com um motivo que o autor vê.
> - Uma publicação removida continua visível para o autor e os moderadores, para que possa ser revisada. Os administradores podem restaurar o texto dela.

**terms, before:**

> Qualquer pessoa conectada pode denunciar um projeto, um perfil ou uma entrada do registro de mudanças. Os moderadores podem descartar uma denúncia, remover um projeto, limpar campos do perfil (foto e capa, resumo curto e “Sobre”, links), silenciar uma conta por até 7 dias (você ainda pode ler, mudar suas configurações, baixar ou excluir seus dados, mas não publicar) ou bani-la por até 14 dias (você é desconectado, não consegue entrar, e seu perfil e projetos não ficam públicos). Toda decisão vem com um motivo que você vê. Sanções mais longas ou permanentes são decididas só pelos administradores do site, que também podem ocultar projetos ou suspender contas. Excluir a conta não encerra um banimento (veja a [Política de privacidade](/legal/privacy/)). Se você acha que erramos, escreva para [{{ contact_email }}](mailto:{{ contact_email }}).

**terms, after:**

> Qualquer pessoa conectada pode denunciar um projeto, um perfil ou uma entrada do diário de desenvolvimento. Os moderadores podem:
>
> - descartar uma denúncia;
> - remover um projeto;
> - limpar campos do perfil (foto e capa, título e “Sobre”, links);
> - silenciar uma conta por até 7 dias: você ainda pode ler, mudar suas configurações, baixar ou excluir seus dados, mas não publicar;
> - banir uma conta por até 14 dias: você é desconectado, não pode entrar, e seu perfil e seus projetos não ficam públicos.
>
> Cada decisão vem com um motivo que você vê. Sanções mais longas ou permanentes são decididas só pelos administradores do site, que também podem ocultar projetos ou suspender contas. Excluir sua conta não encerra um banimento (veja a [Política de privacidade](/legal/privacy/)). Se você acha que erramos, escreva para [{{ contact_email }}](mailto:{{ contact_email }}).
