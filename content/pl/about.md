# O {{ site_name }}

{{ site_name }} to publiczne miejsce, w którym osoby budujące z narzędziami AI pokazują to, co naprawdę wypuściły. Zamiast deklaracji każdy projekt ma znaki potwierdzenia, które sprawdzamy sami.

## Problem {#problem}

Powiedzieć „wypuściłem to” nic nie kosztuje. Zrzut ekranu, post o premierze czy linijka w CV mogą opisać cokolwiek, a z zewnątrz nie da się stwierdzić, czy produkt istnieje, kto nim zarządza i czy działa jeszcze miesiąc później.

GitHub pokazuje kod. LinkedIn pokazuje deklaracje. {{ site_name }} próbuje pokazać efekty: projekt, fakty o nim, które udało się sprawdzić, i to, co jego twórca zrobił dalej. Najważniejszy jest tu projekt; profil to po prostu zbiór czyichś projektów.

## Jak działa dowód {#proof}

Projekt może zdobyć trzy znaki. Każdy z nich to fakt sprawdzany przez nasz serwer i każdy znika, gdy fakt przestaje być prawdziwy.

- **Repo owner.** Projekt wskazuje publiczne repozytorium GitHub. Pytamy publiczne API GitHuba, czy należy ono do osobistego konta GitHub autora i nie jest forkiem, i sprawdzamy to ponownie co tydzień.
- **Live.** Autor udowadnia, że kontroluje domenę projektu, za pomocą wygenerowanego przez nas tokenu: rekordu TXT w DNS albo metatagu na stronie głównej. Regularnie sprawdzamy to ponownie, a znak obowiązuje tylko, dopóki domena była potwierdzona w ciągu ostatnich 35 dni.
- **Steady.** Gdy projekt ma Live, otwieramy jego adres mniej więcej co 3 godziny. Steady wymaga co najmniej 40 sprawdzeń w ostatnich 30 dniach, z których co najmniej 95% musi dostać odpowiedź bez błędu w ciągu 5 sekund.

Pełne zasady, w tym to, jak można stracić każdy znak, są na stronie [Jak działa dowód](/how-proof-works/).

## Czego nie sprawdzamy {#not-verified}

- **Kto napisał kod.** {{ site_name }} sprawdza fakty, które da się udowodnić: do kogo należy połączone repozytorium GitHub, kto kontroluje domenę i czy strona odpowiada. Nie sprawdza i nie może sprawdzić, kto napisał kod ani ile napisało go narzędzie AI. Historię commitów i ich daty zapisuje właściciel repozytorium i można je zmienić. Jeśli uważasz, że projekt jest skopiowany, zgłoś go.
- **Czy projekt jest dobry.** Znaki to nie recenzje. Projekt ze znakiem Steady może być słabym pomysłem, a świetny projekt może jeszcze nie mieć żadnego znaku.
- **Co pisze autor.** Nazwę, opis, zrzuty ekranu, tagi, datę premiery i narzędzia AI w sekcji „Zbudowano z” podaje autor. „Zbudowano z” jest zawsze oznaczone jako deklaracja autora.

## Co dostają twórcy {#builders}

- Publiczny profil, który zbiera Twoje projekty. Logujesz się przez GitHub; prosimy tylko o publiczny profil i adresy e-mail, nigdy o dostęp do repozytoriów.
- Stronę każdego projektu ze znakami, zrzutami ekranu, 30-dniowym paskiem dostępności (gdy projekt ma Live) i dziennikiem rozwoju: krótkimi aktualizacjami i notatkami o premierze, po kolei.
- Plakietkę do README na GitHubie lub na stronę, która pokazuje znaki, jakie projekt ma w tej chwili. Kod do wklejenia jest na stronie projektu.
- Obserwowanie, polubienia, aktualności z nowymi premierami i od osób, które obserwujesz, oraz stronę „Przeglądaj”, gdzie projekty można szukać po tagu, narzędziu lub znaku.
- Kontrolę nad danymi: pobierz je wszystkie jako plik albo usuń konto w Ustawieniach. Bez reklam, bez analityki, bez skryptów śledzących.

## Kto za tym stoi {#who}

{{ site_name }} tworzy i prowadzi jedna osoba, Danylo Rudenko, samodzielny twórca. Powstaje tak, jak wiele projektów tutaj: z narzędziami AI, głównie Claude Code, a o tym, co budować i czy wynik jest dobry, decyduje jedna osoba.

**TODO (Danylo):** potwierdź ten akapit i, jeśli chcesz, dodaj zdanie o sobie (skąd jesteś, dlaczego zacząłeś).

## Co dalej {#next}

Zaplanowane po pierwszej wersji, bez ustalonej kolejności:

- jedna strona aktualności z filtrem zamiast osobnych kart;
- awatary i więcej możliwości dopasowania profilu;
- osiągnięcia;
- lepsze sprawdzanie repozytoriów, na przykład forków, oraz powiązanie repozytorium z domeną;
- co ma znaczyć Live dla projektów, które nie są stronami: narzędzi wiersza poleceń, bibliotek, aplikacji mobilnych.

**TODO (Danylo):** przed publikacją sprawdź, czy lista nadal zgadza się z planami.

## Kontakt {#contact}

Pytania, pomysły, błąd albo projekt, którego nie powinno tu być: napisz na [{{ contact_email }}](mailto:{{ contact_email }}). Możesz też użyć linku „Zgłoś” na stronie każdego projektu lub profilu.

**TODO przed startem:** ten adres pochodzi z `CONTACT_EMAIL` w `config/branding.py` i nadal jest tymczasowy.
