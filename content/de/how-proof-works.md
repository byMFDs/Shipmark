# So funktioniert der Nachweis

Ein Projekt kann hier drei Prüfzeichen (Hallmarks) verdienen. Jedes davon ist eine Tatsache, die wir selbst prüfen, und nichts, was die Autorin oder der Autor einträgt. Prüfzeichen werden bei jedem Aufruf einer Seite aus den neuesten Prüfungen neu berechnet. Ein Zeichen, das nicht mehr zutrifft, verschwindet also.

## Authored {#authored}

**Was es bedeutet:** Die Person, die das Projekt eingestellt hat, hat den Code oder einen echten Teil davon geschrieben.

**Wie es geprüft wird:** Die Autorin oder der Autor verknüpft ein öffentliches GitHub-Repository und klickt auf „Repository prüfen“. Wir fragen dazu die öffentliche API von GitHub ab. Das Zeichen wird vergeben, wenn eine der beiden Bedingungen erfüllt ist:

- das Repository gehört zum persönlichen GitHub-Konto des Autors und ist kein Fork, oder
- GitHub zählt in der Mitwirkenden-Liste des Repositorys mindestens 10 Commits vom Konto des Autors.

Konten vergleichen wir über die numerische Konto-ID von GitHub. Eine Umbenennung des GitHub-Kontos spielt also keine Rolle. Wir lesen nur öffentliche Daten: Die Anmeldung gibt uns nie Zugriff auf private Repositories.

**Wie es verloren gehen kann:** Eine spätere Prüfung stellt fest, dass das Repository gelöscht, privat oder verschoben wurde oder nicht mehr vom Konto stammt, oder der Autor verknüpft ein anderes Repository mit dem Projekt. Ein Repository kann nur mit einem Projekt verknüpft sein.

## Live {#live}

**Was es bedeutet:** Der Autor kontrolliert die Domain, auf der das Projekt läuft.

**Wie es geprüft wird:** Der Autor fügt ein Token hinzu, das wir für dieses Projekt und diese Domain erzeugen, auf einem von zwei Wegen:

- als DNS-TXT-Eintrag der Domain, oder
- als Meta-Tag auf der Startseite, die öffentlich erreichbar sein muss (ohne Login), mit 200 OK antwortet und kleiner als 512 KB ist.

`www.example.com` und `example.com` gelten als dieselbe Domain. Eine Domain kann immer nur für ein Projekt verifiziert sein. Tokens sind zufällig und werden nie wiederverwendet.

**Wie es erneut geprüft wird:** Einmal täglich prüfen wir jede Domain erneut, die in den letzten 30 Tagen nicht bestätigt wurde. Das Zeichen gilt nur, solange die Domain in den letzten 35 Tagen bestätigt wurde.

**Wie es verloren gehen kann:**

- das Token ist nicht mehr im DNS oder auf der Startseite: Das Zeichen wird sofort entfernt;
- die Seite oder das DNS antwortet nicht: Wir versuchen es beim nächsten Durchlauf erneut, aber nach 35 Tagen ohne Bestätigung ist das Zeichen weg;
- der Autor ändert die Live-URL auf eine andere Domain.

Jedes Mal, wenn Live vergeben oder entfernt wird, halten wir die Änderung in unserem internen Log fest.

## Steady {#steady}

**Was es bedeutet:** Das Projekt bleibt erreichbar, nicht nur am Tag des Launchs.

**Wie es geprüft wird:** Solange ein Projekt Live hat, rufen wir seine Live-URL etwa alle 3 Stunden ab. Eine Prüfung gilt als erfolgreich, wenn die Seite innerhalb von 5 Sekunden mit einem HTTP-Status unter 400 antwortet. Das Zeichen wird vergeben, wenn in den letzten 30 Tagen:

- mindestens 40 Prüfungen stattfanden und
- mindestens 95 % davon erfolgreich waren.

Die Projektseite zeigt den Uptime-Anteil und einen Streifen über 30 Tage. Die Ergebnisse speichern wir 90 Tage lang.

**Wie es verloren gehen kann:** Die Uptime fällt unter 95 %, oder das Projekt verliert Live. Steady setzt immer Live voraus.

## Was selbst angegeben ist {#self-declared}

Diese Teile eines Projekts schreibt der Autor, und wir prüfen sie **nicht**:

- Name, Slogan, Beschreibung und Screenshots;
- Tags und Launch-Datum;
- „Gebaut mit“, die KI-Tools, die der Autor nach eigener Aussage genutzt hat. Das ist immer als „selbst angegeben“ gekennzeichnet.

Prüfzeichen sagen nur das, was sie sagen. Authored betrifft den Code, Live die Domain, Steady die Uptime. Keines davon ist eine Bewertung des Produkts.
