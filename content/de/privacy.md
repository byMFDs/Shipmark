# Datenschutzerklärung

Zuletzt aktualisiert am 14. November 2026.

Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.

Diese Seite erklärt, was {{ site_name }} über dich speichert, warum, wie lange und was du dagegen tun kannst. Sie beschreibt, was die Seite tatsächlich tut.

## Wer verantwortlich ist {#controller}

{{ site_name }} wird von {{ legal_owner_name }} betrieben, der für deine Daten verantwortlich ist (der „Verantwortliche“).
Fragen oder Anliegen: [{{ contact_email }}](mailto:{{ contact_email }}).

## Was wir speichern und warum {#data}

**Wenn du dich mit GitHub anmeldest.** GitHub schickt uns:

- deine Konto-ID, deinen Login, Namen, Bio, Avatar-Link und die anderen öffentlichen Felder deines GitHub-Profils;
- die E-Mail-Adressen deines GitHub-Kontos.

Wir fragen GitHub nur nach zwei Berechtigungen: `read:user` und `user:email`. Über dein Konto erhalten wir nie Zugriff auf deine Repositories, weder private noch öffentliche. Deinen GitHub-Zugangstoken speichern wir nach der Anmeldung nicht. Diese Daten brauchen wir, um dein Konto anzulegen und dich beim nächsten Mal wiederzuerkennen (Erfüllung unseres Vertrags mit dir). Dein GitHub-Login wird bei jeder Anmeldung aktualisiert, damit dein Profil immer auf dein aktuelles GitHub-Konto verweist.

**Dein Profil.** Benutzername, Anzeigename, Kurzbeschreibung, „Über mich“, Ort, ein Status (zum Beispiel „Offen für Jobs“), bis zu 10 Fähigkeiten, bis zu 6 Links, bis zu 3 angeheftete Projekte und deine Sprache. Alles außer dem Benutzernamen ist freiwillig. Anzeigename und „Über mich“ werden anfangs aus deinem GitHub-Namen und deiner GitHub-Bio übernommen; du kannst sie in den Einstellungen ändern oder entfernen. Wir speichern außerdem die Adresse deines GitHub-Bildes, nur damit „Mein GitHub-Bild verwenden“ es kopieren kann; sie wird nirgends angezeigt. Benutzername, Anzeigename, Kurzbeschreibung, „Über mich“, Ort, Status, Fähigkeiten, Links, angeheftete Projekte, GitHub-Login und der Monat deiner Registrierung sind **öffentlich**.

**Profilbild und Titelbild.** Du kannst ein Bild und ein breites Titelbild hochladen oder dein GitHub-Bild einmal kopieren lassen. Jedes Bild wird neu kodiert (das Profilbild auf 512×512, das Titelbild auf 1500×500), was versteckte Metadaten wie den GPS-Standort entfernt, bekommt einen zufälligen Dateinamen und wird in unserem Speicher gespeichert: Die Seiten laden dein Bild nie von GitHub. Beide sind **öffentlich**. Wenn du ein Bild entfernst oder ersetzt oder dein Konto löschst, wird die Datei gelöscht; Kopien bleiben bis zu 14 Tage in den Backups. Ohne Bild werden deine Initialen gezeigt.

**Deine E-Mail-Adresse.** Sie wird mit deinem Konto gespeichert und ist nur für unser Team sichtbar. Sie wird nie auf der Seite angezeigt. Die Seite schickt dir keine E-Mails (die einzige E-Mail, die sie verschickt, ist ein Hinweis an unser Team über eine Support-Nachricht); wir würden die Adresse nur nutzen, um dich zu deinem Konto, einer Meldung oder einer Support-Nachricht zu kontaktieren.

**Deine Projekte.** Alles, was du eingibst: Name, Slogan, Beschreibung, Links, Tags, die KI-Tools, die du nach eigener Aussage genutzt hast (als selbst angegeben angezeigt), Screenshots und Build-Log-Einträge. Veröffentlichte Projekte sind öffentlich; Entwürfe sind nur für dich und unser Team sichtbar. Screenshots werden beim Hochladen neu kodiert, wodurch versteckte Metadaten wie Kameradetails oder GPS-Standort entfernt werden.

**Nachweis-Prüfungen.** Um Prüfzeichen zu vergeben, prüfen wir Fakten selbst (unser berechtigtes Interesse an Nachweisen, denen man vertrauen kann):

- *Repo owner:* Wir fragen die öffentliche API von GitHub nach dem Repository, das du verknüpfst, und prüfen es jede Woche erneut. Die Liste der anderen Mitwirkenden auf GitHub lesen wir bei der Prüfung und speichern sie nicht. Wir speichern:
    - seine ID, die Konto-ID des Eigentümers, ob es dir gehört, sein Erstellungsdatum und sein Website-Feld;
    - den ersten Commit seiner Historie (ID und Datum);
    - die Zahl deiner Commits, das Datum deines ersten und letzten Commits und die Zahl der Wochen mit deinen Commits;
    - den Stand einer manuellen Prüfung, wenn eine nötig ist;
    - ob die Verifizierungsdatei gefunden wurde, wenn du sie für ein Organisations-Repository nutzt.
- *Domain verified:* Wir fragen die DNS-Einträge der Domain deines Projekts ab oder rufen seine Seite ab, um dein Verifizierungs-Token zu finden.
- *Steady:* Wir rufen die Adresse deines Projekts alle paar Stunden ab und speichern, ob sie geantwortet hat und wie schnell. Diese Prüfungen werden **90 Tage** aufbewahrt.

Die Ergebnisse werden auf deiner öffentlichen Projektseite angezeigt.

**Follows und Likes.** Wir speichern, wem du folgst und welche Projekte du geliked hast. Andere sehen nur die Zahlen, nicht die Listen.

**Meldungen und Moderation.**

- Wenn du ein Projekt, ein Profil oder einen Build-Log-Eintrag meldest, speichern wir den Grund und die Details, die du schreibst.
- Meldungen sehen die Moderatorinnen und Moderatoren (Personen mit dem Moderator-Abzeichen) und das Team. Für die Entscheidung sehen sie auch den gemeldeten Inhalt und die Geschichte der gemeldeten Person auf {{ site_name }}: wann sie beigetreten ist, frühere Sanktionen, andere Meldungen über sie und entfernte Projekte. Die Moderationsseiten zeigen keine E-Mail-Adressen.
- Die gemeldete Person erfährt nie, wer sie gemeldet hat.
- Wenn die Moderation handelt, speichern wir die Entscheidung und ihren Grund. Ein entferntes Projekt behält seinen Inhalt und den Grund (sichtbar nur für dich, die Moderation und das Team). Geleerte Profilfelder (Bild und Titelbild, Kurzbeschreibung und „Über mich“ oder Links) werden gelöscht. Stummschaltungen und Sperren speichern wir mit Grund, Beginn und Ende.
- Den Grund siehst du in einem Hinweis auf der Website, den wir behalten, bis du dein Konto löschst. Entscheidungen über dich und diese Hinweise sind in „Meine Daten herunterladen“ enthalten.
- Um gegen eine Entscheidung Einspruch einzulegen, schreib an [{{ contact_email }}](mailto:{{ contact_email }}).

**Community.** Wenn du in der Community schreibst, speichern wir:

- deine Threads: Bereich, Titel, Text, Daten und ob ein Thread bearbeitet, angeheftet, gesperrt oder entfernt wurde;
- deine Antworten: Text und auf welchen Beitrag sie antworten;
- die angehängten Bilder. Sie werden wie Screenshots neu kodiert: Versteckte Metadaten wie der GPS-Standort werden entfernt, die Dateinamen sind zufällig, und wir speichern eine Kopie bis 1600 px und eine Vorschau mit 640 px in unserem Speicher.

Beiträge, ihre Bilder, die Zahl ihrer Stimmen und dein Benutzername daran sind **öffentlich**. Wir speichern auch deine Stimmen; niemand sieht, wer wofür gestimmt hat, weder auf der Website noch im Admin-Bereich.

Wenn du einen Beitrag löschst, werden Text und Bilder sofort gelöscht. Der Titel eines Threads bleibt, solange darunter Antworten anderer stehen, und wird als „[gelöscht]“ angezeigt. Wenn die Moderation einen Beitrag entfernt, werden seine Bilder sofort gelöscht, und der Text wird mit dem Grund aufbewahrt, sichtbar nur für dich, die Moderation und das Team. Die Moderation sieht gemeldete Beiträge zusammen mit der Geschichte der Autorin oder des Autors, wie bei anderen Meldungen.

**Benachrichtigungen über Antworten.** Wenn jemand auf deinen Thread oder deine Antwort antwortet, speichern wir eine Benachrichtigung für dich (welche Antwort, wann und wann du die Liste geöffnet hast) sowie den Zeitpunkt der neuesten ungelesenen, damit das Menü einen Hinweis zeigen kann. Nur du siehst sie. Sie werden nach **90 Tagen** gelöscht oder mit deinem Konto. Wir verschicken sie nie per E-Mail.

**Umgehung einer Sperre.** Wird ein Konto gesperrt, speichern wir einen gesalzenen Einweg-Hash seiner GitHub-Nutzer-ID (nie die ID selbst) zusammen mit Grund und Enddatum. Er dient nur dazu, dasselbe GitHub-Konto zu erkennen, wenn es sich während der Sperre neu registriert. Er wird gelöscht, wenn die Sperre endet oder aufgehoben wird, auch wenn das gesperrte Konto inzwischen gelöscht wurde.

**Annahme der Bedingungen.** Wir speichern, welche Version der Nutzungsbedingungen du wann akzeptiert hast.

**Audit-Log.** Wir führen intern Buch über Änderungen an Prüfzeichen, Moderationsmaßnahmen und Kontolöschungen, damit Entscheidungen später nachvollziehbar sind. Nur unser Team kann es sehen.

**Anwendungslogs.** Unsere Anwendungslogs enthalten die Anfragemethode, eine Route mit ausgeblendeten Daten, Antwortstatus, Größe und Dauer sowie bereinigte Fehlermeldungen. Sie enthalten keine IP-Adressen, Browserangaben, Nutzernamen, Abfrageparameter oder Formularinhalte.

**Fehlerprotokoll.** Wenn etwas schiefgeht, schreibt die Anwendung einen kurzen Eintrag in eine Fehlerdatei auf unserem Server. Der Eintrag enthält:

- die Uhrzeit und eine zufällige Referenznummer (die auf der Fehlerseite angezeigte);
- die Anfragemethode und die Seitenadresse ohne alles nach einem `?`, mit Benutzernamen ersetzt durch `[user]`;
- den Antwortstatus und den Teil des Codes, der fehlgeschlagen ist;
- die technische Fehlermeldung, aus der E-Mail-Adressen, IP-Adressen und alles, was wie ein Passwort oder Schlüssel aussieht, entfernt sind.

Nicht gefundene Seiten werden in eine eigene Datei geschrieben, jede Adresse höchstens einmal pro Minute. Diese Dateien enthalten nie deine IP-Adresse, Browserdaten, Cookies, was du in ein Formular eingegeben hast, deine E-Mail-Adresse oder deinen Benutzernamen. Jede Datei ist auf 5 MB plus 5 ältere Kopien begrenzt; ist die Grenze erreicht, wird die älteste gelöscht.

Die Routing-Logs unseres Webhosting-Anbieters enthalten die IP-Adressen der Besuchenden. Routing-Logs und die JSON-stdout-Logs der Anwendung werden im Log-Stream des Anbieters bis zu etwa einer Woche aufbewahrt. Nur die Person, der das Hosting-Konto gehört, kann diesen Stream lesen. Die Anwendungslogs enthalten keine IP-Adressen oder personenbezogenen Daten. Zum Start nutzen wir weder ein langfristiges Log-Archiv noch ein Logging-Add-on; unser DNS-Anbieter leitet den Website-Verkehr nicht über einen Proxy. Vor dem Einrichten eines Log-Archivs oder eines Verkehrs-Proxys aktualisieren wir diese Erklärung.

**Schutz vor Missbrauch.** Um Missbrauch zu begrenzen, zählen wir einige Aktionen (zum Beispiel Likes pro Stunde) in der Datenbank der Seite. Jeder Zähler ist eine Zahl, die an dein Konto oder an ein Projekt gebunden ist, ohne IP-Adresse, und gilt höchstens 24 Stunden. Danach wird er nicht mehr verwendet, die Zeile kann aber in der Datenbank bleiben, bis sie bereinigt wird. Eine Ausnahme: Wenn du ohne Anmeldung nach Leuten suchst, ist der Zähler 10 Minuten lang an einen gesalzenen Einweg-Hash deiner IP-Adresse gebunden (nie an die Adresse selbst). Wonach du suchst, speichern wir nie.

**Analyse und Tracking.** Gibt es nicht: keine Analyse, keine Werbung und keine Tracking-Skripte. Schriften werden von unserem eigenen Server ausgeliefert.

**Backups.** Jeden Tag sichern wir die Datenbank und die hochgeladenen Bilder (Screenshots, Profilbilder und Titelbilder) und bewahren jedes Backup 14 Tage auf. Wenn du dein Konto löschst, bleiben deine Daten in diesen Backups, bis das letzte, das sie enthält, ersetzt wird, also höchstens 14 Tage.

## Nachrichten an den Support {#support}

Wenn du uns über das [Support-Formular](/support/) schreibst, speichern wir das Thema, den Betreff, deine Nachricht, die angegebene E-Mail-Adresse (oder die deines Kontos), das Konto, mit dem du angemeldet warst, die Referenznummer einer Fehlerseite, falls du von dort kommst, und bis zu 3 Anhänge. Bilder werden wie andere Bilder neu kodiert (versteckte Metadaten wie der GPS-Standort werden entfernt); Textdateien werden als Text gespeichert. Anhänge liegen in privatem Speicher ohne öffentliche Adresse: Nur Teammitglieder mit Zugang zum Support-Postfach können sie herunterladen. Deine E-Mail-Adresse nutzen wir nur, um zu antworten.

Wir speichern weder deine IP-Adresse noch Browserangaben zusammen mit der Nachricht. Gegen Spam enthält der Server-Cache Zähler, die durch einen gesalzenen Einweg-Hash deiner IP-Adresse gekennzeichnet sind, niemals durch die Adresse selbst. In der Produktionsumgebung nutzt dieser Cache die Datenbank. Ein Zähler gilt höchstens 24 Stunden. Abgelaufene Cache-Zeilen können bis zur täglichen Bereinigung in der Datenbank verbleiben. Der Hash wird weder mit der Support-Nachricht noch in den Anwendungslogs gespeichert.

Wenn eine Nachricht eingeht, schickt unser Server über unseren E-Mail-Anbieter einen kurzen Texthinweis mit deiner Nachricht und deiner E-Mail-Adresse an das Postfach des Teams (siehe „Wer sonst Daten erhält“). Das Team kann interne Notizen hinzufügen und einen Status setzen (neu, gelesen, beantwortet, geschlossen). Wir lesen jede Nachricht, können aber nicht versprechen, auf alle zu antworten. Geschlossene Nachrichten werden 12 Monate nach dem Senden gelöscht; die übrigen bleiben, bis sie geschlossen werden. „Meine Daten herunterladen“ enthält die Nachrichten, die du angemeldet geschickt hast, und wenn du dein Konto löschst, werden sie gelöscht, auch die, die du abgemeldet von der E-Mail-Adresse deines Kontos geschickt hast.

## Wie lange wir es aufbewahren {#retention}

- Dein Konto, Profil, deine Projekte, Follows und Likes: bis du sie oder dein Konto löschst.
- Support-Nachrichten und ihre Anhänge: geschlossene 12 Monate nach dem Senden, die übrigen bis sie geschlossen werden; mit deinem Konto.
- Threads, Antworten und Bilder in der Community: bis du sie oder dein Konto löschst (was bleibt, steht oben unter „Community“). Stimmen: bis du sie zurücknimmst oder dein Konto löschst.
- Benachrichtigungen über Antworten: 90 Tage.
- Profilbild und Titelbild: bis du sie entfernst oder ersetzt oder dein Konto löschst.
- Uptime-Prüfungen: 90 Tage.
- Moderationsentscheidungen über dich (Stummschaltungen, Sperren, entfernte Projekte) und Hinweise: solange dein Konto besteht; sie werden mit ihm gelöscht. Meldungen über dich bleiben ohne Verbindung zu deinem Konto, nur mit dem damaligen Namen.
- Hash der GitHub-ID eines gesperrten Kontos: nur bis die Sperre endet oder aufgehoben wird.
- Anmelde-Sitzungen: 2 Wochen oder bis zum Abmelden.
- Meldungen, die du gemacht hast: bleiben nach der Bearbeitung erhalten. Wenn du dein Konto löschst, bleiben sie ohne deinen Namen.
- Audit-Log: bleibt erhalten. Einträge zu einem gelöschten Konto enthalten weder Benutzername noch E-Mail-Adresse.
- Zähler zum Schutz vor Missbrauch: höchstens 24 Stunden.
- Backups: 14 Tage. Ein gelöschtes Konto verschwindet innerhalb von 14 Tagen daraus.
- Fehlerprotokoll-Dateien: bis sie voll sind (5 MB plus 5 ältere Kopien zu je 5 MB), dann werden die ältesten Einträge gelöscht.
- Routing-Logs des Hostings und stdout-Logs der Anwendung: bis zu etwa einer Woche im Log-Stream des Hostings; zum Start kein langfristiges Log-Archiv.

## Wer sonst Daten erhält {#recipients}

- **Anbieter für Webhosting und verwaltete Datenbanken** betreiben die Anwendung und speichern ihre Datensätze für uns.
- **S3-kompatibler Objektspeicher** speichert hochgeladene Bilder und private Support-Anhänge in unserem Auftrag.
- **GitHub** ermöglicht die Anmeldung und liefert Profil- und öffentliche Repository-Daten für unsere Prüfungen. Für deine Nutzung von GitHub gilt dessen eigene Datenschutzerklärung.
- **Ein E-Mail-Dienst** liefert Support-Benachrichtigungen mit Nachricht und E-Mail-Adresse der absendenden Person an unser Team-Postfach.
- **DNS- und Webserver deines Projekts** erhalten unsere Prüfungsanfragen. Sie sehen die Adresse unseres Servers, nicht die der Besuchenden.

Wir verkaufen deine Daten nicht und geben sie nicht für Werbung weiter.

## Deine Rechte {#rights}

- **Deine Daten ansehen und herunterladen:** Unter Einstellungen → „Meine Daten herunterladen“ bekommst du eine JSON-Datei mit deinem Profil (mit Links, Fähigkeiten, angehefteten Projekten und den Adressen von Profil- und Titelbild), deinen GitHub-Angaben, Projekten, dem Build-Log, Likes, Follows, deinen Meldungen sowie Moderationsentscheidungen und Hinweisen über dich.
- **Korrigieren:** Bearbeite dein Profil in den Einstellungen und deine Projekte auf ihren Seiten.
- **Löschen:** Einstellungen → „Konto löschen“. Das entfernt sofort dein Profil, dein Profil- und Titelbild und alle deine Projekte, Likes und Follows und lässt sich nicht rückgängig machen. Dein Benutzername wird wieder frei.
- **Community:** „Meine Daten herunterladen“ enthält auch deine Threads, Antworten, die Adressen deiner Bilder, deine Stimmen und deine Benachrichtigungen über Antworten. Wenn du dein Konto löschst, werden deine Community-Bilder, Stimmen, Benachrichtigungen und deine Threads ohne Antworten anderer gelöscht; deine übrigen Beiträge bleiben ohne deinen Namen, dein Bild und deinen Link. Community-Bilder sind wie andere Uploads in den täglichen Backups (14 Tage).
- **Widerspruch oder Beschwerde:** Schreib an [{{ contact_email }}](mailto:{{ contact_email }}). Wenn du in der EU, im Vereinigten Königreich oder in der Ukraine lebst, kannst du dich auch bei deiner Datenschutzbehörde beschweren.

## Cookies {#cookies}

Wir verwenden nur Cookies, die für den Betrieb der Seite nötig sind. Siehe die [Cookie-Richtlinie](/legal/cookies/).

## Änderungen {#changes}

Wenn sich diese Erklärung ändert, aktualisieren wir das Datum oben. Ist die Änderung wichtig, bitten wir dich bei deinem nächsten Besuch, die aktualisierten Nutzungsbedingungen zu akzeptieren.
