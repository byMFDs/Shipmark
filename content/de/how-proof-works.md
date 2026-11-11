# So funktioniert der Nachweis

Ein Projekt kann hier drei Prüfzeichen (Hallmarks) verdienen. Jedes davon ist eine Tatsache, die wir selbst prüfen, und nichts, was die Autorin oder der Autor einträgt. Prüfzeichen werden bei jedem Aufruf einer Seite aus den neuesten Prüfungen neu berechnet. Ein Zeichen, das nicht mehr zutrifft, verschwindet also.

## Repo owner {#authored}

**Was es bedeutet:** Das mit dem Projekt verknüpfte GitHub-Repository gehört dem persönlichen GitHub-Konto der Person, die das Projekt veröffentlicht hat. Es beweist nicht, wer den Code geschrieben hat.

**Wie es geprüft wird:** Die Person verknüpft ein öffentliches GitHub-Repository und klickt auf „Repository prüfen“. Wir fragen die öffentliche API von GitHub. Das Prüfzeichen gibt es, wenn das Repository dem persönlichen GitHub-Konto der Person gehört und kein Fork ist.

Konten und Repositorys werden über die numerischen IDs von GitHub verglichen, nicht über Namen: Ein umbenanntes Konto oder Repository ändert nichts, und ein gelöschtes Repository, das jemand unter demselben Namen neu anlegt, ist ein anderes Repository. Wir lesen nur öffentliche Daten: Die Anmeldung gibt uns nie Zugriff auf private Repositorys.

**Was wir außerdem festhalten:** wann das Repository angelegt wurde, seinen ersten Commit, wie viele Commits die Person hat und wann der erste und der letzte entstanden, und in wie vielen Wochen ihre Commits Code geändert haben (aus der Statistik von GitHub; Bots zählen nicht). Die Projektseite zeigt diese Fakten unter „Was geprüft wurde“. In drei Fällen wartet das Prüfzeichen auf eine kurze manuelle Prüfung: Der erste Commit ist viel älter als das Repository, derselbe erste Commit gehört zu einem Repository eines anderen Projekts hier, oder GitHub zeigt keine Commits der Person. Commit-Daten schreibt, wer den Commit erstellt; sie beschreiben die Geschichte, beweisen sie aber nicht.

**Wie es erneut geprüft wird:** Jede Woche suchen wir das Repository erneut über seine ID.

**Wie es verloren gehen kann:** Das Repository wird gelöscht, privat gemacht oder an ein anderes Konto übertragen, oder die Person verknüpft ein anderes Repository. Ein Repository kann nur mit einem Projekt verknüpft sein.

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

Die reine Adresse eines Hosting-Dienstes, den viele Websites teilen (etwa `github.io` oder `vercel.app`), kann nicht bestätigt werden. Deine eigene Adresse darauf (`yourname.github.io`) schon.

## Steady {#steady}

**Was es bedeutet:** Das Projekt bleibt erreichbar, nicht nur am Tag des Launchs.

**Wie es geprüft wird:** Solange ein Projekt Live hat, rufen wir seine Live-URL etwa alle 3 Stunden ab. Eine Prüfung gilt als erfolgreich, wenn die Seite innerhalb von 5 Sekunden mit einem HTTP-Status unter 400 antwortet. Das Zeichen wird vergeben, wenn in den letzten 30 Tagen:

- mindestens 40 Prüfungen stattfanden und
- mindestens 95 % davon erfolgreich waren.

Die Projektseite zeigt den Uptime-Anteil und einen Streifen über 30 Tage. Die Ergebnisse speichern wir 90 Tage lang.

**Wie es verloren gehen kann:** Die Uptime fällt unter 95 %, oder das Projekt verliert Live. Steady setzt immer Live voraus.

Eine Prüfung scheitert auch, wenn die Website erst nach einer Weiterleitung auf eine andere Domain antwortet: Die Antwort muss von der bestätigten Domain kommen.

## Was selbst angegeben ist {#self-declared}

Diese Teile eines Projekts schreibt der Autor, und wir prüfen sie **nicht**:

- Name, Slogan, Beschreibung und Screenshots;
- Tags und Launch-Datum;
- „Gebaut mit“, die KI-Tools, die der Autor nach eigener Aussage genutzt hat. Das ist immer als „selbst angegeben“ gekennzeichnet.

Prüfzeichen sagen nur das, was sie sagen. Repo owner betrifft das Repository, Live die Domain, Steady die Uptime. Keines davon ist eine Bewertung des Produkts.

## Was wir nicht prüfen können {#limits}

{{ site_name }} prüft Fakten, die sich belegen lassen: wem das verknüpfte GitHub-Repository gehört, wer die Domain kontrolliert und ob die Website antwortet. Wer den Code geschrieben hat, prüfen wir nicht und können wir nicht prüfen. Commit-Verlauf und Daten schreibt die Person, der das Repository gehört, und sie lassen sich ändern. Wenn du glaubst, dass ein Projekt kopiert ist, melde es.
