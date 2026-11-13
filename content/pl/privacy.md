# Polityka prywatności

> **Wersja robocza**, ostatnia aktualizacja: 14 listopada 2026. Ten tekst nie został jeszcze sprawdzony przez prawnika.
>
> Tłumaczenie dla wygody; obowiązuje wersja angielska.

Ta strona wyjaśnia, co {{ site_name }} przechowuje o Tobie, po co, jak długo i co możesz w tej sprawie zrobić. Opisuje to, co serwis faktycznie robi.

## Kto odpowiada {#controller}

{{ site_name }} prowadzi {{ legal_owner_name }}, który odpowiada za Twoje dane („administrator”).
Pytania i wnioski: [{{ contact_email }}](mailto:{{ contact_email }}).

## Co przechowujemy i po co {#data}

**Gdy logujesz się przez GitHub.** GitHub przekazuje nam:

- identyfikator i login Twojego konta, imię, bio, link do awatara i pozostałe publiczne pola Twojego profilu GitHub;
- adresy e-mail z Twojego konta GitHub.

Prosimy GitHub tylko o dwa uprawnienia: `read:user` i `user:email`. Przez Twoje konto nigdy nie dostajemy dostępu do Twoich repozytoriów, ani prywatnych, ani publicznych. Nie przechowujemy Twojego tokenu dostępu GitHub po zalogowaniu. Te dane są potrzebne, aby utworzyć konto i rozpoznać Cię następnym razem (wykonanie naszej umowy z Tobą). Twój login GitHub odświeża się przy każdym logowaniu, więc profil zawsze prowadzi do Twojego aktualnego konta GitHub.

**Twój profil.** Nazwa użytkownika, wyświetlana nazwa, krótki opis, „O mnie”, lokalizacja, status (np. „Szukam pracy”), do 10 umiejętności, do 6 linków, do 3 przypiętych projektów i język. Wszystko poza nazwą użytkownika jest opcjonalne. Wyświetlana nazwa i „O mnie” na początku pochodzą z Twojej nazwy i bio na GitHubie; możesz je zmienić lub usunąć w Ustawieniach. Zapisujemy też adres Twojego obrazu z GitHuba, tylko po to, aby opcja „Użyj mojego obrazu z GitHub” mogła go skopiować; nigdzie go nie pokazujemy. Twoja nazwa użytkownika, wyświetlana nazwa, krótki opis, „O mnie”, lokalizacja, status, umiejętności, linki, przypięte projekty, login GitHub i miesiąc dołączenia są **publiczne**.

**Zdjęcie profilowe i obraz w tle.** Możesz wysłać zdjęcie i szeroki obraz w tle albo raz skopiować swój obraz z GitHuba. Każdy obraz kodujemy na nowo (zdjęcie do 512×512, obraz w tle do 1500×500), co usuwa ukryte metadane, np. lokalizację GPS, nadajemy mu losową nazwę i przechowujemy na własnym serwerze: strony nigdy nie wczytują Twojego zdjęcia z GitHuba. Oba są **publiczne**. Gdy usuniesz lub zastąpisz obraz albo usuniesz konto, plik jest usuwany; kopie zostają w kopiach zapasowych do 14 dni. Bez zdjęcia pokazujemy Twoje inicjały.

**Twój adres e-mail.** Jest przechowywany przy koncie i widoczny tylko dla naszego zespołu. Nigdy nie jest pokazywany w serwisie. Serwis nie wysyła do Ciebie e-maili (jedyny e-mail, jaki wysyła, to powiadomienie dla naszego zespołu o wiadomości do wsparcia); użyjemy adresu tylko po to, by skontaktować się z Tobą w sprawie konta, zgłoszenia lub wiadomości do wsparcia.

**Twoje projekty.** Wszystko, co wpiszesz: nazwa, opis, długi opis, linki, tagi, narzędzia AI, których według Ciebie użyto (pokazywane jako deklaracja autora), zrzuty ekranu i wpisy dziennika rozwoju. Opublikowane projekty są publiczne; szkice widzisz tylko Ty i nasz zespół. Zrzuty ekranu są kodowane ponownie przy wysyłaniu, co usuwa ukryte metadane, takie jak dane aparatu czy lokalizacja GPS.

**Sprawdzenia dowodów.** Aby przyznawać znaki, sprawdzamy fakty sami (nasz uzasadniony interes w pokazywaniu dowodów, którym można ufać):

- *Repo owner:* pytamy publiczne API GitHuba o repozytorium, które podajesz, i co tydzień sprawdzamy je ponownie. Listę innych współtwórców z GitHuba czytamy podczas sprawdzenia i nie zapisujemy jej. Zapisujemy:
    - jego identyfikator, identyfikator konta właściciela, czy należy do Ciebie, datę utworzenia i pole Website;
    - pierwszy commit w jego historii (identyfikator i datę);
    - liczbę Twoich commitów, daty pierwszego i ostatniego oraz liczbę tygodni z Twoimi commitami;
    - stan ręcznej weryfikacji, gdy jest potrzebna;
    - czy znaleziono plik weryfikacyjny, jeśli używasz go dla repozytorium organizacji.
- *Domain verified:* sprawdzamy rekordy DNS domeny Twojego projektu albo pobieramy jego stronę, aby znaleźć Twój token weryfikacyjny.
- *Steady:* wysyłamy żądanie pod adres Twojego projektu co kilka godzin i zapisujemy, czy odpowiedział i jak szybko. Te sprawdzenia przechowujemy przez **90 dni**.

Wyniki są pokazywane na publicznej stronie Twojego projektu.

**Obserwowania i polubienia.** Zapisujemy, kogo obserwujesz i które projekty lubisz. Inni widzą tylko liczby, nie listy.

**Zgłoszenia i moderacja.**

- Jeśli zgłosisz projekt, profil lub wpis w dzienniku rozwoju, zapisujemy powód i szczegóły, które napiszesz.
- Zgłoszenia widzą moderatorzy (osoby z odznaką moderatora) i zespół. Aby podjąć decyzję, widzą też zgłoszoną treść i historię zgłoszonej osoby w {{ site_name }}: kiedy dołączyła, wcześniejsze sankcje, inne zgłoszenia na jej temat i usunięte projekty. Strony moderacji nie pokazują adresów e-mail.
- Zgłoszona osoba nigdy nie dowiaduje się, kto ją zgłosił.
- Gdy moderatorzy podejmują działanie, zapisujemy decyzję i jej powód. Usunięty projekt zachowuje treść i powód (widzisz go tylko Ty, moderatorzy i zespół). Wyczyszczone pola profilu (zdjęcie i okładka, nagłówek i „O mnie” albo linki) są usuwane. Wyciszenia i blokady zapisujemy z powodem, początkiem i końcem.
- Powód widzisz w powiadomieniu na stronie, które przechowujemy, dopóki nie usuniesz konta. Decyzje dotyczące Ciebie i te powiadomienia są w „Pobierz moje dane”.
- Aby odwołać się od decyzji, napisz na [{{ contact_email }}](mailto:{{ contact_email }}).

**Społeczność.** Gdy piszesz w społeczności, zapisujemy:

- Twoje wątki: dział, tytuł, tekst, daty oraz to, czy wątek był edytowany, przypięty, zamknięty lub usunięty;
- Twoje odpowiedzi: tekst, wybraną naklejkę i to, na który wpis odpowiadają;
- dołączone obrazy. Są ponownie kodowane jak zrzuty ekranu: ukryte metadane, takie jak lokalizacja GPS, są usuwane, nazwy plików są losowe, a na naszym serwerze trzymamy kopię do 1600 px i miniaturę 640 px.

Wpisy, ich obrazy, liczba głosów i Twoja nazwa użytkownika przy nich są **publiczne**. Zapisujemy też Twoje głosy; nikt nie widzi, kto na co głosował, ani na stronie, ani w panelu administracyjnym.

Gdy usuwasz wpis, jego tekst, naklejka i obrazy są usuwane od razu. Tytuł wątku zostaje, dopóki są pod nim odpowiedzi innych osób, i jest pokazywany jako „[usunięto]”. Gdy wpis usuwają moderatorzy, jego obrazy są usuwane od razu, a tekst zostaje zachowany z powodem i widzisz go tylko Ty, moderatorzy i zespół. Moderatorzy widzą zgłoszone wpisy razem z historią autora, tak jak przy innych zgłoszeniach.

**Powiadomienia o odpowiedziach.** Gdy ktoś odpowie na Twój wątek lub Twoją odpowiedź, zapisujemy dla Ciebie powiadomienie (która odpowiedź, kiedy i kiedy otworzyłeś listę) oraz czas najnowszego nieprzeczytanego, aby menu mogło pokazać znacznik. Widzisz je tylko Ty. Są usuwane po **90 dniach** albo razem z kontem. Nigdy nie wysyłamy ich e-mailem.

**Omijanie blokady.** Gdy konto zostaje zablokowane, zapisujemy jednokierunkowy skrót (z solą) jego identyfikatora GitHub, nigdy sam identyfikator, razem z powodem i datą końca. Pozwala on tylko rozpoznać to samo konto GitHub, jeśli zarejestruje się ponownie w czasie blokady. Skrót jest usuwany, gdy blokada się kończy lub zostaje cofnięta, także jeśli zablokowane konto zostało w międzyczasie usunięte.

**Akceptacja Regulaminu.** Zapisujemy, którą wersję Regulaminu zaakceptowano i kiedy.

**Dziennik audytu.** Prowadzimy wewnętrzny zapis zmian znaków, działań moderacyjnych i usunięć kont, aby decyzje dało się później sprawdzić. Widzi go tylko nasz zespół.

**Adresy IP i dzienniki.** Aplikacja nie zapisuje Twojego adresu IP, a jej własne dzienniki go nie zawierają. Przy każdym żądaniu strony dzienniki zapisują tylko metodę, adres strony (bez tego, co następuje po `?`), status odpowiedzi, rozmiar i czas obsługi oraz błędy. Nie ma w nich danych o Twojej przeglądarce. Adresy stron zawierają nazwy użytkowników (`/u/<username>/`), więc wiersz dziennika może pokazać, który profil otwarto, ale nie kto to zrobił.

**Dziennik błędów.** Gdy coś się psuje, aplikacja zapisuje krótki wpis w pliku błędów na naszym serwerze. Wpis zawiera:

- czas i losowy numer referencyjny (ten widoczny na stronie błędu);
- metodę żądania i adres strony bez tego, co jest po `?`, z nazwami użytkowników zastąpionymi przez `[user]`;
- status odpowiedzi i część kodu, w której wystąpił błąd;
- techniczny komunikat błędu, z którego usunięto adresy e-mail, adresy IP i wszystko, co wygląda na hasło lub klucz.

Strony, których nie znaleziono, trafiają do osobnego pliku, każdy adres najwyżej raz na minutę. Te pliki nigdy nie zawierają Twojego adresu IP, danych przeglądarki, plików cookie, tego, co wpisano w formularzu, Twojego adresu e-mail ani nazwy użytkownika. Każdy plik jest ograniczony do 5 MB plus 5 starszych kopii; po osiągnięciu limitu najstarsza jest usuwana.

> **TODO przed uruchomieniem:** serwer WWW przed aplikacją prowadzi własny dziennik dostępu, który domyślnie zawiera adresy IP. Co dokładnie zapisuje i jak długo to przechowuje (oraz jak długo przechowywane są dzienniki aplikacji), nie zostało jeszcze ustalone. Trzeba to uzupełnić albo wyłączyć zapisywanie IP, zanim ta strona stanie się publiczna.

**Ochrona przed nadużyciami.** Aby ograniczać nadużycia, liczymy niektóre działania (na przykład polubienia na godzinę) w bazie danych serwisu. Każdy licznik to liczba przypisana do Twojego konta lub projektu, bez adresu IP, obowiązująca najwyżej 24 godziny. Potem nie jest już używany, ale wiersz może zostać w bazie, dopóki nie zostanie wyczyszczony.

**Analityka i śledzenie.** Nie ma ich: ani analityki, ani reklam, ani skryptów śledzących. Czcionki są serwowane z naszego własnego serwera.

**Kopie zapasowe.** Codziennie robimy kopię bazy danych i wysłanych obrazów (zrzutów ekranu, zdjęć profilowych i obrazów w tle) i przechowujemy każdą kopię przez 14 dni. Jeśli usuniesz konto, Twoje dane zostają w tych kopiach, dopóki ostatnia, która je zawiera, nie zostanie zastąpiona, czyli do 14 dni.

## Wiadomości do wsparcia {#support}

Gdy piszesz do nas przez [formularz wsparcia](/support/), zapisujemy temat, tytuł, Twoją wiadomość, podany adres e-mail (lub adres konta), konto, z którego pisałeś, numer strony błędu, jeśli z niej przyszedłeś, oraz do 3 załączników. Obrazy są kodowane na nowo jak inne zdjęcia (ukryte metadane, np. lokalizacja GPS, są usuwane); pliki tekstowe są przechowywane jako tekst. Załączniki leżą w prywatnym folderze na naszym serwerze, który nie ma publicznego adresu: pobrać je może tylko personel z dostępem do skrzynki wsparcia. Twojego adresu e-mail używamy tylko do odpowiedzi.

Nie zapisujemy razem z wiadomością Twojego adresu IP ani danych przeglądarki. Aby powstrzymać spam, solony jednokierunkowy odcisk Twojego adresu IP jest trzymany w pamięci podręcznej serwera najwyżej 24 godziny, nigdy w bazie danych ani w logach.

Gdy wiadomość dotrze, nasz serwer wysyła na skrzynkę zespołu krótkie powiadomienie tekstowe z Twoją wiadomością i adresem e-mail, przez naszego dostawcę poczty (zob. „Kto jeszcze otrzymuje dane”). Personel może dodawać notatki wewnętrzne i ustawiać status (nowa, przeczytana, z odpowiedzią, zamknięta). Czytamy każdą wiadomość, ale nie możemy obiecać odpowiedzi na wszystkie. Zamknięte wiadomości są usuwane 12 miesięcy po wysłaniu; pozostałe zostają, dopóki nie zostaną zamknięte. „Pobierz moje dane” zawiera wiadomości wysłane z Twojego konta, a usunięcie konta je kasuje, także te wysłane bez logowania z adresu e-mail Twojego konta.

## Jak długo to przechowujemy {#retention}

- Konto, profil, projekty, obserwowania i polubienia: dopóki ich nie usuniesz albo nie usuniesz konta.
- Wiadomości do wsparcia i załączniki: zamknięte 12 miesięcy po wysłaniu, pozostałe do zamknięcia; razem z kontem.
- Wątki, odpowiedzi i obrazy w społeczności: dopóki ich nie usuniesz albo nie usuniesz konta (co zostaje, opisuje sekcja „Społeczność” powyżej). Głosy: dopóki ich nie cofniesz albo nie usuniesz konta.
- Powiadomienia o odpowiedziach: 90 dni.
- Zdjęcie profilowe i obraz w tle: dopóki ich nie usuniesz lub nie zastąpisz albo nie usuniesz konta.
- Sprawdzenia dostępności: 90 dni.
- Decyzje moderacji dotyczące Ciebie (wyciszenia, blokady, usunięte projekty) i powiadomienia: dopóki istnieje Twoje konto; są usuwane razem z nim. Zgłoszenia dotyczące Ciebie zostają bez powiązania z kontem, tylko z ówczesną nazwą.
- Skrót identyfikatora GitHub zablokowanego konta: tylko do końca lub cofnięcia blokady.
- Sesje logowania: 2 tygodnie lub do wylogowania.
- Zgłoszenia, które wysłano z Twojego konta: zostają po rozpatrzeniu. Jeśli usuniesz konto, zostają bez Twojego imienia.
- Dziennik audytu: jest zachowywany. Wpisy o usuniętym koncie nie zawierają nazwy użytkownika ani adresu e-mail.
- Liczniki ochrony przed nadużyciami: najwyżej 24 godziny.
- Kopie zapasowe: 14 dni. Usunięte konto znika z nich w ciągu 14 dni.
- Pliki dziennika błędów: do zapełnienia (5 MB plus 5 starszych kopii po 5 MB), potem najstarsze wpisy są usuwane.
- Dzienniki serwera WWW i aplikacji: **TODO**, jeszcze nie ustalono.

## Kto jeszcze otrzymuje dane {#recipients}

- **GitHub, Inc.** Logujesz się na github.com, a nasz serwer odczytuje Twój profil i publiczne dane repozytoriów z API GitHuba. Do korzystania z GitHuba stosuje się jego własne oświadczenie o prywatności.
- **Nasz dostawca poczty** (np. Google, jeśli skrzynka zespołu to Gmail) dostarcza na skrzynkę zespołu powiadomienie o każdej wiadomości do wsparcia, z jej treścią i Twoim adresem e-mail.
- **Serwery Twojego projektu.** Przy sprawdzeniach Domain verified i Steady nasz serwer łączy się z DNS Twojej domeny i z adresem Twojego projektu. Widzą nasz serwer, nie Ciebie.
- **Nasz dostawca hostingu**, który prowadzi dla nas serwer i bazę danych.

Nie sprzedajemy Twoich danych i nie udostępniamy ich do celów reklamowych.

## Twoje prawa {#rights}

- **Zobacz i pobierz swoje dane:** Ustawienia → „Pobierz moje dane” daje plik JSON z Twoim profilem (z linkami, umiejętnościami, przypiętymi projektami i adresami zdjęcia i obrazu w tle), danymi z GitHuba, projektami, dziennikiem rozwoju, polubieniami, obserwowanymi, wysłanymi zgłoszeniami oraz decyzjami moderacji i powiadomieniami dotyczącymi Ciebie.
- **Popraw je:** edytuj profil w Ustawieniach, a projekty na ich stronach.
- **Usuń je:** Ustawienia → „Usuń konto”. To od razu usuwa Twój profil, zdjęcie i obraz w tle oraz wszystkie projekty, polubienia i obserwowania i nie można tego cofnąć. Twoja nazwa użytkownika staje się wolna.
- **Społeczność:** „Pobierz moje dane” zawiera też Twoje wątki, odpowiedzi, adresy Twoich obrazów, głosy i powiadomienia o odpowiedziach. Usunięcie konta kasuje Twoje obrazy w społeczności, głosy, powiadomienia oraz wątki bez odpowiedzi innych osób; pozostałe posty zostają bez Twojej nazwy, zdjęcia i linku. Obrazy ze społeczności trafiają do codziennych kopii zapasowych, jak inne przesłane pliki (14 dni).
- **Sprzeciw lub skarga:** napisz na [{{ contact_email }}](mailto:{{ contact_email }}). Jeśli mieszkasz w UE, Wielkiej Brytanii lub na Ukrainie, możesz też złożyć skargę do organu ochrony danych.

## Pliki cookie {#cookies}

Używamy tylko plików cookie potrzebnych do działania serwisu. Zobacz [politykę plików cookie](/legal/cookies/).

## Zmiany {#changes}

Jeśli ta polityka się zmieni, zaktualizujemy datę na górze. Jeśli zmiana będzie ważna, poprosimy Cię o zaakceptowanie zaktualizowanego Regulaminu przy następnej wizycie.
