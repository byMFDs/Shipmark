# Über {{ site_name }}

{{ site_name }} ist ein öffentlicher Ort, an dem Menschen, die mit KI-Werkzeugen bauen, zeigen, was sie wirklich veröffentlicht haben. Statt Behauptungen trägt jedes Projekt Prüfzeichen, die wir selbst prüfen.

## Das Problem {#problem}

„Ich habe es veröffentlicht“ zu sagen, kostet nichts. Ein Screenshot, ein Launch-Post oder eine Zeile im Lebenslauf kann alles beschreiben, und von außen sieht niemand, ob das Produkt existiert, wer es kontrolliert und ob es einen Monat später noch läuft.

GitHub zeigt Code. LinkedIn zeigt Behauptungen. {{ site_name }} versucht, Ergebnisse zu zeigen: ein Projekt, die Fakten, die wir darüber prüfen konnten, und was die Person danach gemacht hat. Im Mittelpunkt steht das Projekt; ein Profil ist einfach die Sammlung der Projekte einer Person.

## So funktioniert der Nachweis {#proof}

Ein Projekt kann drei Prüfzeichen verdienen. Jedes ist eine Tatsache, die unser Server prüft, und jedes verschwindet, sobald die Tatsache nicht mehr stimmt.

- **Repo owner.** Das Projekt verknüpft ein öffentliches GitHub-Repository. Wir fragen die öffentliche API von GitHub, ob es dem persönlichen GitHub-Konto der Person gehört und kein Fork ist; bei Repositorys von Organisationen und Teams legt die Person stattdessen eine Datei mit dem Token dieses Projekts an. Wir prüfen das jede Woche erneut.
- **Domain verified.** Die Person weist nach, dass sie die Domain des Projekts kontrolliert, mit einem Token, das wir erzeugen: als DNS-TXT-Eintrag oder als Meta-Tag auf der Startseite. Wir prüfen das regelmäßig erneut, und das Zeichen gilt nur, solange die Domain in den letzten 35 Tagen bestätigt wurde.
- **Steady.** Sobald ein Projekt Domain verified hat, rufen wir seine Adresse etwa alle 3 Stunden auf. Steady braucht mindestens 40 Prüfungen in den letzten 30 Tagen, und mindestens 95 % davon müssen innerhalb von 5 Sekunden eine Antwort ohne Fehler bekommen.

Die vollständigen Regeln, auch wie man jedes Zeichen verlieren kann, stehen unter [So funktioniert der Nachweis](/how-proof-works/).

## Was wir nicht prüfen {#not-verified}

- **Wer den Code geschrieben hat.** {{ site_name }} prüft Fakten, die sich belegen lassen: wem das verknüpfte GitHub-Repository gehört, wer die Domain kontrolliert und ob die Website antwortet. Wer den Code geschrieben hat oder wie viel davon ein KI-Werkzeug geschrieben hat, prüfen wir nicht und können wir nicht prüfen. Commit-Verlauf und Daten schreibt die Person, der das Repository gehört, und sie lassen sich ändern. Wenn du glaubst, dass ein Projekt kopiert ist, melde es.
- **Ob das Projekt gut ist.** Prüfzeichen sind keine Bewertungen. Ein Projekt mit Steady kann trotzdem eine schwache Idee sein, und ein großartiges Projekt hat vielleicht noch kein Zeichen.
- **Was die Person schreibt.** Name, Beschreibung, Screenshots, Tags, Launch-Datum und die KI-Werkzeuge unter „Gebaut mit“ kommen von der Person selbst. „Gebaut mit“ ist immer als selbst angegeben markiert.

## Was du bekommst {#builders}

- Ein öffentliches Profil, das deine Projekte sammelt. Du meldest dich mit GitHub an; wir fragen nur nach deinem öffentlichen Profil und deinen E-Mail-Adressen, nie nach Zugriff auf deine Repositories.
- Eine Seite für jedes Projekt mit seinen Prüfzeichen, Screenshots, einem 30-Tage-Verfügbarkeitsstreifen (sobald es Domain verified hat) und einem Build-Log: kurze Updates und Launch-Notizen, der Reihe nach.
- Ein Badge für dein GitHub-README oder deine Website, das die Prüfzeichen zeigt, die das Projekt gerade hat. Den Code zum Einfügen findest du auf der Projektseite.
- Folgen, Likes, einen Feed mit neuen Launches und von Leuten, denen du folgst, und eine Seite „Entdecken“, auf der du Projekte nach Tag, Werkzeug oder Prüfzeichen findest.
- Kontrolle über deine Daten: Lade sie alle als Datei herunter oder lösche dein Konto in den Einstellungen. Keine Werbung, keine Analyse, keine Tracking-Skripte.

## Wer dahintersteht {#who}

{{ site_name }} wird von einer Person gebaut und betrieben: Danylo Rudenko, Solo-Entwickler. Es entsteht so wie viele Projekte hier: mit KI-Werkzeugen, vor allem Claude Code, und eine Person entscheidet, was gebaut wird und ob das Ergebnis taugt.

**TODO (Danylo):** Bestätige diesen Absatz und füge, wenn du willst, einen Satz über dich hinzu (wo du lebst, warum du angefangen hast).

## Wie es weitergeht {#next}

Geplant nach der ersten Version, ohne feste Reihenfolge:

- eine Feed-Seite mit Filter statt getrennter Tabs;
- Avatare und mehr Möglichkeiten, ein Profil zu gestalten;
- Erfolge;
- bessere Prüfung von Repositories, zum Beispiel bei Forks, und die Verknüpfung eines Repositorys mit seiner Domain;
- was Domain verified für Projekte bedeuten soll, die keine Websites sind: Kommandozeilen-Werkzeuge, Bibliotheken, mobile Apps.

**TODO (Danylo):** Prüfe vor der Veröffentlichung, ob die Liste noch zu deinen Plänen passt.

## Kontakt {#contact}

Fragen, Ideen, ein Fehler oder ein Projekt, das nicht hierher gehört: schreib an [{{ contact_email }}](mailto:{{ contact_email }}). Du kannst auch den Link „Melden“ auf jeder Projekt- oder Profilseite nutzen.

**TODO vor dem Start:** Diese Adresse kommt aus `CONTACT_EMAIL` in `config/branding.py` und ist noch ein Platzhalter.
