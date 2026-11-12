# Jak działa dowód

Projekt może tu zdobyć trzy znaki (hallmarks). Każdy z nich to fakt, który sprawdzamy sami, a nie coś, co wpisuje autor. Znaki są obliczane na nowo przy każdym wyświetleniu strony, na podstawie najnowszych sprawdzeń, więc znak, który przestał być aktualny, znika.

## Repo owner {#authored}

**Co to znaczy:** repozytorium GitHub połączone z projektem należy do osobistego konta GitHub osoby, która opublikowała projekt, albo (w repozytoriach organizacji i zespołów) zawiera plik weryfikacyjny tego projektu, do którego dodania potrzebny jest dostęp do zapisu. Nie dowodzi to, kto napisał kod.

**Jak jest sprawdzane:** autor podaje publiczne repozytorium GitHub i klika „Sprawdź repozytorium”. Pytamy publiczne API GitHuba. Oznaczenie zdobywa się, gdy repozytorium należy do osobistego konta GitHub autora i nie jest forkiem.

**Repozytoria organizacji i zespołów:** na stronie edycji każdy projekt dostaje własny losowy token. Dodaj w katalogu głównym domyślnej gałęzi plik `.shipmark-verify` zawierający tylko ten token i sprawdź ponownie. Dodać go mogą tylko osoby z prawem do pushowania, więc potwierdza on dostęp do zapisu, a nie to, kto napisał kod. Forki nie liczą się w żadnym wariancie. Plik jest sprawdzany co tydzień; jeśli go nie ma, oznaczenie jest usuwane.

Konta i repozytoria porównujemy po numerycznych identyfikatorach GitHuba, nie po nazwach: zmiana nazwy konta lub repozytorium niczego nie zmienia, a usunięte repozytorium utworzone przez kogoś od nowa pod tą samą nazwą to inne repozytorium. Czytamy tylko dane publiczne: logowanie nigdy nie daje nam dostępu do prywatnych repozytoriów.

**Co jeszcze zapisujemy:** kiedy utworzono repozytorium, jego pierwszy commit, ile commitów ma autor i kiedy powstał pierwszy i ostatni, oraz w ilu tygodniach commity autora zmieniały kod (ze statystyk GitHuba; boty się nie liczą). Strona projektu pokazuje te fakty w sekcji „Co sprawdzono”. W trzech przypadkach oznaczenie czeka na krótką ręczną weryfikację: pierwszy commit jest dużo starszy niż repozytorium, ten sam pierwszy commit ma repozytorium innego projektu tutaj albo GitHub nie pokazuje żadnych commitów autora. Daty commitów zapisuje ten, kto tworzy commit, więc opisują historię, ale jej nie dowodzą.

**Jak jest sprawdzane ponownie:** co tydzień ponownie odnajdujemy repozytorium po jego identyfikatorze.

**Jak można go utracić:** repozytorium zostaje usunięte, ustawione jako prywatne lub przeniesione na inne konto albo autor podaje inne repozytorium. Jedno repozytorium można połączyć tylko z jednym projektem.

## Domain verified {#live}

**Co to znaczy:** autor kontroluje domenę, na której działa projekt.

**Jak jest sprawdzane:** autor dodaje token, który generujemy dla tego projektu i tej domeny, na jeden z dwóch sposobów:

- rekord DNS TXT w domenie, albo
- metatag na stronie głównej, która musi być publicznie dostępna (bez logowania), odpowiadać 200 OK i mieć mniej niż 512 KB.

`www.example.com` i `example.com` liczą się jako ta sama domena. Domenę można zweryfikować tylko dla jednego projektu naraz. Tokeny są losowe i nigdy nie są używane ponownie.

**Jak jest sprawdzane ponownie:** raz dziennie ponownie sprawdzamy każdą domenę, która nie była potwierdzona w ciągu ostatnich 30 dni. Znak obowiązuje tylko wtedy, gdy domena została potwierdzona w ciągu ostatnich 35 dni.

**Jak można go utracić:**

- tokena nie ma już w DNS ani na stronie głównej: znak jest usuwany od razu;
- strona lub DNS nie odpowiada: spróbujemy przy następnym przebiegu, ale po 35 dniach bez potwierdzenia znak znika;
- autor zmienia adres strony na inną domenę.

Każde zdobycie lub usunięcie Domain verified jest zapisywane w naszym wewnętrznym dzienniku.

Głównego adresu hostingu współdzielonego przez wiele stron (np. `github.io` lub `vercel.app`) nie można zweryfikować. Twój własny adres w tym serwisie (`yourname.github.io`) można.

## Steady {#steady}

**Co to znaczy:** projekt działa nieprzerwanie, a nie tylko w dniu premiery.

**Jak jest sprawdzane:** gdy projekt ma Domain verified, wysyłamy żądanie pod jego adres mniej więcej co 3 godziny. Sprawdzenie kończy się powodzeniem, gdy strona odpowie w ciągu 5 sekund statusem HTTP poniżej 400. Znak jest przyznawany, gdy w ciągu ostatnich 30 dni:

- było co najmniej 40 sprawdzeń, oraz
- co najmniej 95% z nich zakończyło się powodzeniem.

Strona projektu pokazuje odsetek dostępności i pasek z 30 dni. Wyniki przechowujemy przez 90 dni.

**Jak można go utracić:** dostępność spada poniżej 95% albo projekt traci Domain verified. Steady zawsze wymaga Domain verified.

Sprawdzenie nie liczy się też wtedy, gdy strona odpowiada dopiero po przekierowaniu na inną domenę: odpowiedź musi przyjść ze zweryfikowanej domeny.

## Co jest deklaracją autora {#self-declared}

Te elementy projektu pisze autor, a my ich **nie** sprawdzamy:

- nazwa, opis, długi opis i zrzuty ekranu;
- tagi i data premiery;
- „Zbudowano z”, czyli narzędzia AI, których według autora użył. Zawsze jest oznaczone jako deklaracja autora.

Znaki mówią tylko to, co mówią. Repo owner dotyczy repozytorium, Domain verified domeny, Steady dostępności. Żaden z nich nie jest oceną produktu.

## Czego nie możemy sprawdzić {#limits}

{{ site_name }} sprawdza fakty, które da się udowodnić: do kogo należy połączone repozytorium GitHub, kto kontroluje domenę i czy strona odpowiada. Nie sprawdza i nie może sprawdzić, kto napisał kod. Historię commitów i ich daty zapisuje właściciel repozytorium i można je zmienić. Jeśli uważasz, że projekt jest skopiowany, zgłoś go.
