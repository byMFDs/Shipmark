# Jak działa dowód

Projekt może tu zdobyć trzy znaki (hallmarks). Każdy z nich to fakt, który sprawdzamy sami, a nie coś, co wpisuje autor. Znaki są obliczane na nowo przy każdym wyświetleniu strony, na podstawie najnowszych sprawdzeń, więc znak, który przestał być aktualny, znika.

## Repo owner {#authored}

**Co to znaczy:** konto GitHub osoby, która opublikowała projekt, jest właścicielem powiązanego repozytorium albo ma w nim co najmniej 10 commitów. Nie dowodzi to, kto napisał kod.

**Jak jest sprawdzane:** autor podaje publiczne repozytorium na GitHubie i klika „Sprawdź repozytorium”. Pytamy o nie publiczne API GitHuba. Znak jest przyznawany, gdy spełniony jest jeden z warunków:

- repozytorium należy do osobistego konta autora na GitHubie i nie jest forkiem, albo
- GitHub zlicza co najmniej 10 commitów z konta autora na liście współtwórców repozytorium.

Konta porównujemy po numerycznym identyfikatorze konta w GitHubie, więc zmiana nazwy konta nie ma znaczenia. Czytamy tylko dane publiczne: logowanie nigdy nie daje nam dostępu do prywatnych repozytoriów.

**Jak można go utracić:** późniejsze sprawdzenie stwierdzi, że repozytorium zostało usunięte, jest prywatne, zostało przeniesione albo konto nie jest już jego właścicielem i nie ma w nim dość commitów, albo autor powiąże z projektem inne repozytorium. Jedno repozytorium może być powiązane tylko z jednym projektem.

## Live {#live}

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

Każde zdobycie lub usunięcie Live jest zapisywane w naszym wewnętrznym dzienniku.

## Steady {#steady}

**Co to znaczy:** projekt działa nieprzerwanie, a nie tylko w dniu premiery.

**Jak jest sprawdzane:** gdy projekt ma Live, wysyłamy żądanie pod jego adres mniej więcej co 3 godziny. Sprawdzenie kończy się powodzeniem, gdy strona odpowie w ciągu 5 sekund statusem HTTP poniżej 400. Znak jest przyznawany, gdy w ciągu ostatnich 30 dni:

- było co najmniej 40 sprawdzeń, oraz
- co najmniej 95% z nich zakończyło się powodzeniem.

Strona projektu pokazuje odsetek dostępności i pasek z 30 dni. Wyniki przechowujemy przez 90 dni.

**Jak można go utracić:** dostępność spada poniżej 95% albo projekt traci Live. Steady zawsze wymaga Live.

## Co jest deklaracją autora {#self-declared}

Te elementy projektu pisze autor, a my ich **nie** sprawdzamy:

- nazwa, opis, długi opis i zrzuty ekranu;
- tagi i data premiery;
- „Zbudowano z”, czyli narzędzia AI, których według autora użył. Zawsze jest oznaczone jako deklaracja autora.

Znaki mówią tylko to, co mówią. Repo owner dotyczy repozytorium, Live domeny, Steady dostępności. Żaden z nich nie jest oceną produktu.
