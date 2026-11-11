# Datenschutzerklärung

> **Entwurf**, zuletzt aktualisiert am 11. November 2026. Dieser Text wurde noch nicht von einer Juristin oder einem Juristen geprüft.
>
> Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.

Diese Seite erklärt, was {{ site_name }} über dich speichert, warum, wie lange und was du dagegen tun kannst. Sie beschreibt, was die Seite tatsächlich tut.

## Wer verantwortlich ist {#controller}

{{ site_name }} wird von {{ legal_owner_name }} betrieben, der für deine Daten verantwortlich ist (der „Verantwortliche“).
Fragen oder Anliegen: [{{ contact_email }}](mailto:{{ contact_email }}).

## Was wir speichern und warum {#data}

**Wenn du dich mit GitHub anmeldest.** Von GitHub erhalten wir deine Konto-ID, deinen Login, deinen Namen, deine Bio, den Link zu deinem Avatar und die übrigen öffentlichen Felder deines GitHub-Profils sowie die E-Mail-Adressen deines GitHub-Kontos. Wir fragen GitHub nur nach `read:user` und `user:email`: Über dein Konto bekommen wir nie Zugriff auf deine Repositories, weder private noch öffentliche. Dein GitHub-Zugriffstoken behalten wir nach der Anmeldung nicht. Wir brauchen das, um dein Konto anzulegen und dich beim nächsten Mal wiederzuerkennen (Erfüllung unserer Vereinbarung mit dir). Dein GitHub-Login wird bei jeder Anmeldung aktualisiert, damit dein Profil immer auf dein aktuelles GitHub-Konto verweist.

**Dein Profil.** Benutzername, Anzeigename, Bio, Website und Sprache. Name und Bio beginnen mit deinen GitHub-Werten; du kannst sie in den Einstellungen ändern. Dein Benutzername, Anzeigename, deine Bio, Website, dein GitHub-Login und der Monat deines Beitritts sind **öffentlich**.

**Deine E-Mail-Adresse.** Sie wird mit deinem Konto gespeichert und ist nur für unser Team sichtbar. Sie wird nie auf der Seite angezeigt. Die Seite versendet keine E-Mails; wir würden die Adresse nur nutzen, um dich zu deinem Konto oder zu einer Meldung zu kontaktieren.

**Deine Projekte.** Alles, was du eingibst: Name, Slogan, Beschreibung, Links, Tags, die KI-Tools, die du nach eigener Aussage genutzt hast (als selbst angegeben angezeigt), Screenshots und Build-Log-Einträge. Veröffentlichte Projekte sind öffentlich; Entwürfe sind nur für dich und unser Team sichtbar. Screenshots werden beim Hochladen neu kodiert, wodurch versteckte Metadaten wie Kameradetails oder GPS-Standort entfernt werden.

**Nachweis-Prüfungen.** Um Prüfzeichen zu vergeben, prüfen wir Fakten selbst (unser berechtigtes Interesse an Nachweisen, denen man vertrauen kann):

- *Repo owner:* Wir fragen die öffentliche API von GitHub nach dem Repository, das du verknüpfst, und speichern seine ID, die Konto-ID der Person, der es gehört, ob es dir gehört, sein Erstellungsdatum und sein Website-Feld, den ersten Commit seines Verlaufs (ID und Datum), deine Anzahl an Commits, das Datum deines ersten und letzten Commits, die Anzahl der Wochen mit deinen Commits und den Stand einer manuellen Prüfung, falls eine nötig ist. Wir prüfen das jede Woche erneut. Die Liste der anderen Beitragenden lesen wir während der Prüfung und speichern sie nicht.
- *Live:* Wir fragen die DNS-Einträge der Domain deines Projekts ab oder rufen seine Seite ab, um dein Verifizierungs-Token zu finden.
- *Steady:* Wir rufen die Adresse deines Projekts alle paar Stunden ab und speichern, ob sie geantwortet hat und wie schnell. Diese Prüfungen werden **90 Tage** aufbewahrt.

Die Ergebnisse werden auf deiner öffentlichen Projektseite angezeigt.

**Follows und Likes.** Wir speichern, wem du folgst und welche Projekte du geliked hast. Andere sehen nur die Zahlen, nicht die Listen.

**Meldungen.** Wenn du ein Projekt oder ein Profil meldest, speichern wir den Grund und die Details, die du schreibst. Nur unser Team sieht Meldungen. Die gemeldete Person erfährt nicht, wer sie gemeldet hat.

**Annahme der Bedingungen.** Wir speichern, welche Version der Nutzungsbedingungen du wann akzeptiert hast.

**Audit-Log.** Wir führen intern Buch über Änderungen an Prüfzeichen, Moderationsmaßnahmen und Kontolöschungen, damit Entscheidungen später nachvollziehbar sind. Nur unser Team kann es sehen.

**IP-Adressen und Logs.** Die Anwendung speichert deine IP-Adresse nicht, und ihre eigenen Logs enthalten sie nicht. Zu jeder Seitenanfrage halten die Logs nur die Methode, die Seitenadresse (ohne alles nach einem `?`), den Antwortstatus, die Größe und die Antwortzeit fest, dazu Fehler. Angaben zu deinem Browser sind nicht darin. Seitenadressen enthalten Benutzernamen (`/u/<username>/`); eine Logzeile kann also zeigen, welches Profil geöffnet wurde, aber nicht von wem.

**Fehlerprotokoll.** Wenn etwas schiefgeht, schreibt die Anwendung einen kurzen Eintrag in eine Fehlerdatei auf unserem Server: Zeitpunkt, eine zufällige Referenznummer (die auf der Fehlerseite angezeigt wird), die Anfragemethode, die Seitenadresse ohne alles nach einem `?` und mit Benutzernamen ersetzt durch `[user]`, den Antwortstatus, den Teil des Codes, der fehlgeschlagen ist, und die technische Fehlermeldung, aus der E-Mail-Adressen, IP-Adressen und alles, was wie ein Passwort oder Schlüssel aussieht, entfernt sind. Nicht gefundene Seiten kommen in eine eigene Datei, jede Adresse höchstens einmal pro Minute. Diese Dateien enthalten nie deine IP-Adresse, Browserdaten, Cookies, Formulareingaben, deine E-Mail-Adresse oder deinen Benutzernamen. Jede Datei ist auf 5 MB plus 5 ältere Kopien begrenzt; ist die Grenze erreicht, wird die älteste gelöscht.

> **TODO vor dem Start:** Der Webserver vor der Anwendung führt ein eigenes Zugriffslog, das standardmäßig IP-Adressen enthält. Was er aufzeichnet und wie lange er es aufbewahrt (und wie lange die Logs der Anwendung aufbewahrt werden), ist noch nicht entschieden. Das muss ergänzt oder die IP-Protokollierung abgeschaltet werden, bevor diese Seite öffentlich wird.

**Schutz vor Missbrauch.** Um Missbrauch zu begrenzen, zählen wir einige Aktionen (zum Beispiel Likes pro Stunde) in der Datenbank der Seite. Jeder Zähler ist eine Zahl, die an dein Konto oder an ein Projekt gebunden ist, ohne IP-Adresse, und gilt höchstens 24 Stunden. Danach wird er nicht mehr verwendet, die Zeile kann aber in der Datenbank bleiben, bis sie bereinigt wird.

**Analyse und Tracking.** Gibt es nicht: keine Analyse, keine Werbung und keine Tracking-Skripte. Schriften werden von unserem eigenen Server ausgeliefert.

**Backups.** Jeden Tag sichern wir die Datenbank und die hochgeladenen Screenshots und bewahren jede Sicherung 14 Tage auf. Wenn du dein Konto löschst, bleiben deine Daten in diesen Sicherungen, bis die letzte, die sie enthält, ersetzt ist – bis zu 14 Tage.

## Wie lange wir es aufbewahren {#retention}

- Dein Konto, Profil, deine Projekte, Follows und Likes: bis du sie oder dein Konto löschst.
- Uptime-Prüfungen: 90 Tage.
- Anmelde-Sitzungen: 2 Wochen oder bis zum Abmelden.
- Meldungen, die du gemacht hast: bleiben nach der Bearbeitung erhalten. Wenn du dein Konto löschst, bleiben sie ohne deinen Namen.
- Audit-Log: bleibt erhalten. Einträge zu einem gelöschten Konto enthalten weder Benutzername noch E-Mail-Adresse.
- Zähler zum Schutz vor Missbrauch: höchstens 24 Stunden.
- Backups: 14 Tage. Ein gelöschtes Konto verschwindet innerhalb von 14 Tagen daraus.
- Fehlerprotokoll-Dateien: bis sie voll sind (5 MB plus 5 ältere Kopien zu je 5 MB), dann werden die ältesten Einträge gelöscht.
- Logs von Webserver und Anwendung: **TODO**, noch nicht entschieden.

## Wer sonst Daten erhält {#recipients}

- **GitHub, Inc.** Du meldest dich auf github.com an, und unser Server liest dein Profil und öffentliche Repository-Daten über die API von GitHub. Für deine Nutzung von GitHub gilt dessen eigene Datenschutzerklärung.
- **Die Server deines Projekts.** Für die Live- und Steady-Prüfungen kontaktiert unser Server das DNS deiner Domain und die Adresse deines Projekts. Sie sehen unseren Server, nicht dich.
- **Unser Hosting-Anbieter**, der für uns den Server und die Datenbank betreibt.

Wir verkaufen deine Daten nicht und geben sie nicht für Werbung weiter.

## Deine Rechte {#rights}

- **Deine Daten ansehen und herunterladen:** Unter Einstellungen → „Meine Daten herunterladen“ bekommst du eine JSON-Datei mit deinem Profil, deinen GitHub-Angaben, Projekten, dem Build-Log, Likes, Follows und deinen Meldungen.
- **Korrigieren:** Bearbeite dein Profil in den Einstellungen und deine Projekte auf ihren Seiten.
- **Löschen:** Einstellungen → „Konto löschen“. Das entfernt sofort dein Profil und alle deine Projekte, Likes und Follows und lässt sich nicht rückgängig machen. Dein Benutzername wird wieder frei.
- **Widerspruch oder Beschwerde:** Schreib an [{{ contact_email }}](mailto:{{ contact_email }}). Wenn du in der EU, im Vereinigten Königreich oder in der Ukraine lebst, kannst du dich auch bei deiner Datenschutzbehörde beschweren.

## Cookies {#cookies}

Wir verwenden nur Cookies, die für den Betrieb der Seite nötig sind. Siehe die [Cookie-Richtlinie](/legal/cookies/).

## Änderungen {#changes}

Wenn sich diese Erklärung ändert, aktualisieren wir das Datum oben. Ist die Änderung wichtig, bitten wir dich bei deinem nächsten Besuch, die aktualisierten Nutzungsbedingungen zu akzeptieren.
