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
