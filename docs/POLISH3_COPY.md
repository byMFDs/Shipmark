# Polish-3: copy changes (before / after)

English source → new English source. Translations listed where they changed in a notable way;
all 6 translated languages were updated in the same commit. Non-English texts are machine-translated
and need a native speaker's review.

## 1a. Names

| Where | Before | After | uk | pl | de | es | fr | pt-br |
|---|---|---|---|---|---|---|---|---|
| Header + footer link to `/feed/` | Feed | For You | Для вас | Dla Ciebie | Für dich | Para ti | Pour vous | Para você |
| `/feed/` page title, h1 | Feed | For You Page | Сторінка «Для вас» | Strona Dla Ciebie | Für-dich-Seite | Página Para ti | Page Pour vous | Página Para você |
| `/feed/` first tab (side menu + tabs) | For you | Recommended | Рекомендоване | Polecane | Empfohlen | Recomendados | Recommandés | Recomendados |
| Header, footer, `/explore/` title, h1, feed side menu | Explore | Discover | Пошук | Odkrywaj | Entdecken | Descubrir | Découvrir | Descobrir |
| Landing "see all" link | Explore projects | Discover projects | Знайти проєкти | Odkryj projekty | Projekte entdecken | Descubrir proyectos | Découvrir les projets | Descobrir projetos |
| Error pages, support "sent" page | Go to your feed | See projects for you (existing string) | Дивитися проєкти для вас | … | … | … | … | … |
| Feed side menu (screen readers) | Feed navigation | Page menu | Меню сторінки | Menu strony | Seitenmenü | Menú de la página | Menu de la page | Menu da página |
| Feed tabs (screen readers) | Feed sections | Sections | Розділи | Sekcje | Bereiche | Secciones | Sections | Seções |
| About page, "what you get" + "what is next" | "a feed … an Explore page", "one feed page" | "a For You Page … a Discover page", "one For You Page" | same in all 7 `content/<lang>/about.md` | | | | | |

Why "Discover": one short everyday word, the same idea in every language, and it will hold both tabs
(Projects, People) after stage 7. "Find projects" is longer and would be wrong once People is added;
"Browse" is less familiar outside tech. Ukrainian uses «Пошук» (search): the natural nav word; a literal
«Відкривайте» sounds like an ad.
Why "For You" in the nav and "For You Page" as the title: the long form does not fit the header in German
or French; the inner tab became "Recommended" so "For you" is not shown twice.

## 1b. UI text sweep

How: all 1146 English strings were read one by one (`locale/*/django.po`), plus automatic checks in every
language: the form of address (uk «ви», de «du», fr «vous», es «tú», pt-br «você»), the glossary terms
(hallmark names, «позначка»), and admin messages with "(s)" instead of real plurals. Pages were rendered at
360 px in German and French (project form, settings, project page): buttons fit.
Most English text was already plain; only the strings below changed.

| Where | Before | After |
|---|---|---|
| Sign-up, username hint | Lowercase letters, digits, - and _. | Use small letters, numbers, - and _. |
| Username error | Use only lowercase letters, digits, hyphens and underscores, starting with a letter or digit. | Use only small letters, numbers, - and _, and start with a letter or a number. |
| Username error | This username is reserved. Please choose another. | This username is not available. Choose another one. |
| Community, broken form post | Bad request. | Something went wrong. Reload the page and try again. |
| Image upload | The image has too many pixels. | The image is too big (too many pixels). Use a smaller one. |
| Image upload | This file is not a valid image. | We could not open this file as an image. |
| Tags error | Tags use letters, digits, spaces … | Tags can use letters, numbers, spaces … |
| Repo check result | Repository checked. Repo owner earned. | Repository checked. You earned Repo owner. |
| Domain check result | Verified. Domain verified earned. | Verified. You earned Domain verified. |
| Domain re-check result | Verified. Confirmed again. | Verified. Your domain is confirmed again. |
| Domain status | Verified: %(domain)s. Domain verified earned. | %(domain)s is verified. You earned Domain verified. |
| 400 page | We could not read that request / Something in it was malformed or incomplete. … | Something was wrong with that request / Part of it was missing or broken. … |
| 403 page title | This record is closed | You cannot open this page |
| 404 page title | No record found | Page not found |
| 500 page | It is not your fault, and the error has been logged. … | It is not your fault. We keep a note of the error. … |
| Sign-in error | GitHub did not complete the sign-in, or the request expired. … Please try again. | GitHub did not finish the sign-in, or it took too long. … Try again. |
| Repo check errors | GitHub's rate limit was reached. … / GitHub did not answer properly. … | GitHub is limiting our checks right now. … / GitHub did not answer as expected. … |
| Domain check error | Your homepage could not be loaded (…) | We could not open your homepage (…) |
| Settings, export | A JSON file with your profile, … | One file (JSON) with your profile, … |
| Toast close button (screen readers) | Dismiss | Close |
| Admin messages | Suspended 3 user(s). (and 8 more with "(s)") | real singular/plural forms (ngettext) in all 7 languages; "Unhid" → "Made … visible again", "Purged" → "Deleted … for good" |

Delete-account page (facts corrected to match `accounts/deletion.py`):

| Before | After |
|---|---|
| Your profile: username, display name, bio, website, language, … | Your profile: username, display name, headline, About, links, picture, cover, language, … (bio and website are no longer used) |
| (missing) | Your support messages and their attachments. |
| (missing, community on) | In the community: your images, your upvotes, and threads nobody else replied to. |
| (missing, community on, "What is kept") | Your community replies, and threads other people replied to, stay without your name. They show as “[deleted]”. |

Translation fixes without an English change:

| Language | Where | Before | After |
|---|---|---|---|
| uk | Landing hero | Покажи, що ти запустив із ШІ. … | Покажіть, що ви запустили з ШІ. … (the site says «ви» everywhere; no gendered verb) |
| uk | Delete page (2 lines) | відзнаки, журнал | позначки, журнал розробки (glossary) |
| de | Feed tip | Bestätige deine Domain … | Verifiziere deine Domain … (glossary: verify = verifizieren) |
