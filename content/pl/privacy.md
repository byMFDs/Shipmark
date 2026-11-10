# Polityka prywatności

> **Wersja robocza**, ostatnia aktualizacja: 10 listopada 2026. Ten tekst nie został jeszcze sprawdzony przez prawnika.
>
> Tłumaczenie dla wygody; obowiązuje wersja angielska.

Ta strona wyjaśnia, co {{ site_name }} przechowuje o Tobie, po co, jak długo i co możesz w tej sprawie zrobić. Opisuje to, co serwis faktycznie robi.

## Kto odpowiada {#controller}

{{ site_name }} prowadzi {{ legal_owner_name }}, który odpowiada za Twoje dane („administrator”).
Pytania i wnioski: [{{ contact_email }}](mailto:{{ contact_email }}).

## Co przechowujemy i po co {#data}

**Gdy logujesz się przez GitHub.** Od GitHuba otrzymujemy identyfikator Twojego konta, login, imię i nazwisko, bio, link do awatara i pozostałe publiczne pola profilu GitHub, a także adresy e-mail przypisane do Twojego konta GitHub. Prosimy GitHub tylko o `read:user` i `user:email`: przez Twoje konto nigdy nie mamy dostępu do Twoich repozytoriów, ani prywatnych, ani publicznych. Po zalogowaniu nie przechowujemy Twojego tokenu dostępu do GitHuba. Potrzebujemy tych danych, by założyć konto i rozpoznać Cię następnym razem (wykonanie umowy z Tobą).

**Twój profil.** Nazwa użytkownika, nazwa wyświetlana, bio, strona WWW i język. Nazwa i bio zaczynają od wartości z GitHuba; możesz je zmienić w Ustawieniach. Twoja nazwa użytkownika, nazwa wyświetlana, bio, strona WWW, login GitHub i miesiąc dołączenia są **publiczne**.

**Twój adres e-mail.** Jest przechowywany przy koncie i widoczny tylko dla naszego zespołu. Nigdy nie jest pokazywany w serwisie. Serwis nie wysyła e-maili; użyjemy adresu tylko po to, by skontaktować się z Tobą w sprawie konta lub zgłoszenia.

**Twoje projekty.** Wszystko, co wpiszesz: nazwa, opis, długi opis, linki, tagi, narzędzia AI, których według Ciebie użyto (pokazywane jako deklaracja autora), zrzuty ekranu i wpisy dziennika rozwoju. Opublikowane projekty są publiczne; szkice widzisz tylko Ty i nasz zespół. Zrzuty ekranu są kodowane ponownie przy wysyłaniu, co usuwa ukryte metadane, takie jak dane aparatu czy lokalizacja GPS.

**Sprawdzenia dowodów.** Aby przyznawać znaki, sprawdzamy fakty sami (nasz uzasadniony interes w pokazywaniu dowodów, którym można ufać):

- *Authored:* pytamy publiczne API GitHuba o powiązane repozytorium i zapisujemy, czy jesteś jego właścicielem, liczbę Twoich commitów oraz daty pierwszego i ostatniego commita. Listę pozostałych współtwórców z GitHuba czytamy podczas sprawdzenia i nie zapisujemy jej.
- *Live:* sprawdzamy rekordy DNS domeny Twojego projektu albo pobieramy jego stronę, aby znaleźć Twój token weryfikacyjny.
- *Steady:* wysyłamy żądanie pod adres Twojego projektu co kilka godzin i zapisujemy, czy odpowiedział i jak szybko. Te sprawdzenia przechowujemy przez **90 dni**.

Wyniki są pokazywane na publicznej stronie Twojego projektu.

**Obserwowania i polubienia.** Zapisujemy, kogo obserwujesz i które projekty lubisz. Inni widzą tylko liczby, nie listy.

**Zgłoszenia.** Jeśli zgłosisz projekt lub profil, zapisujemy powód i szczegóły, które napiszesz. Zgłoszenia widzi tylko nasz zespół. Zgłoszona osoba nie dowiaduje się, kto ją zgłosił.

**Akceptacja Regulaminu.** Zapisujemy, którą wersję Regulaminu zaakceptowano i kiedy.

**Dziennik audytu.** Prowadzimy wewnętrzny zapis zmian znaków, działań moderacyjnych i usunięć kont, aby decyzje dało się później sprawdzić. Widzi go tylko nasz zespół.

**Czego nie przechowujemy.** Serwis nie zapisuje Twojego adresu IP. Aby ograniczać nadużycia, liczymy działania na konto (na przykład polubienia na godzinę) w pamięci tymczasowej, najwyżej przez godzinę. Nie ma analityki, reklam ani skryptów śledzących. Czcionki są serwowane z naszego własnego serwera.

## Jak długo to przechowujemy {#retention}

- Konto, profil, projekty, obserwowania i polubienia: dopóki ich nie usuniesz albo nie usuniesz konta.
- Sprawdzenia dostępności: 90 dni.
- Sesje logowania: 2 tygodnie lub do wylogowania.
- Zgłoszenia, które wysłano z Twojego konta: zostają po rozpatrzeniu. Jeśli usuniesz konto, zostają bez Twojego imienia.
- Dziennik audytu: jest zachowywany. Wpisy o usuniętym koncie nie zawierają nazwy użytkownika ani adresu e-mail.

## Kto jeszcze otrzymuje dane {#recipients}

- **GitHub, Inc.** Logujesz się na github.com, a nasz serwer odczytuje Twój profil i publiczne dane repozytoriów z API GitHuba. Do korzystania z GitHuba stosuje się jego własne oświadczenie o prywatności.
- **Serwery Twojego projektu.** Przy sprawdzeniach Live i Steady nasz serwer łączy się z DNS Twojej domeny i z adresem Twojego projektu. Widzą nasz serwer, nie Ciebie.
- **Nasz dostawca hostingu**, który prowadzi dla nas serwer i bazę danych.

Nie sprzedajemy Twoich danych i nie udostępniamy ich do celów reklamowych.

## Twoje prawa {#rights}

- **Zobacz i pobierz swoje dane:** Ustawienia → „Pobierz moje dane” daje plik JSON z Twoim profilem, danymi z GitHuba, projektami, dziennikiem rozwoju, polubieniami, obserwowanymi i wysłanymi zgłoszeniami.
- **Popraw je:** edytuj profil w Ustawieniach, a projekty na ich stronach.
- **Usuń je:** Ustawienia → „Usuń konto”. To od razu usuwa Twój profil oraz wszystkie projekty, polubienia i obserwowania i nie można tego cofnąć. Twoja nazwa użytkownika staje się wolna.
- **Sprzeciw lub skarga:** napisz na [{{ contact_email }}](mailto:{{ contact_email }}). Jeśli mieszkasz w UE, Wielkiej Brytanii lub na Ukrainie, możesz też złożyć skargę do organu ochrony danych.

## Pliki cookie {#cookies}

Używamy tylko plików cookie potrzebnych do działania serwisu. Zobacz [politykę plików cookie](/legal/cookies/).

## Zmiany {#changes}

Jeśli ta polityka się zmieni, zaktualizujemy datę na górze. Jeśli zmiana będzie ważna, poprosimy Cię o zaakceptowanie zaktualizowanego Regulaminu przy następnej wizycie.
