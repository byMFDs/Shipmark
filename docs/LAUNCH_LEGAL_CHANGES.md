# Журнал юридичних і редакційних змін перед запуском

Сім мов: en, uk, pl, de, es, fr, pt-br. Нижче — повні змінені абзаци до й після, щоб кожне змінене речення можна було перевірити. База порівняння: коміт етапу 2 `ab893da`.

## Погоджені рішення

Розробник погодив короткий потік журналів Heroku (приблизно до одного тижня, доступ власника акаунта), відсутність довгострокового drain/add-on і режим Cloudflare DNS-only. У Privacy використано загальні категорії обробників. Політику треба оновити до ввімкнення архіву журналів або проксі. Це погоджена політика майбутнього запуску; налаштування зовнішніх ресурсів локально не перевірялися.

Погоджено уточнення про солений IP-хеш у database-backed cache. Перевірка ізольованої in-memory таблиці Django показала: прострочений рядок залишається до читання (до читання — 1 рядок, get повертає None і прибирає рядок). Текст розрізняє строк дії лічильника (до 24 годин) і фізичне видалення під час щоденного обслуговування. Очищення додано до існуючого `prune_support` з регресійним тестом під час завершення етапу 3. Також етап 6 має підтвердити відсутність персональних даних у stdout. До виконання цих умов запуск не готовий.

Наявні дати, версію Умов, права, санкції, строки інших даних і пороги proof-перевірок не змінено. П’ять наявних English-prevails приміток збережено як звичайні абзаци; нової норми для української версії не додавали. Функціональний стан проєкту «draft/чернетка» залишається: це стан даних, а не редакційна примітка.

About скорочено до фактів, розділи про автора й непідтверджені плани вилучено; контакт підставляється з branding, додано support. Прибрано згадки про вибір нових стікерів; наявні ключі в базі й експорті не змінені.

## До і після

### content/de/about.md

Було:

```markdown
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
```

Стало:

```markdown
{{ site_name }} ist ein öffentlicher Ort für Softwareprojekte, die mit KI-Werkzeugen entstehen. Projektseiten verbinden Beschreibungen, Screenshots, Entwicklungsberichte und Prüfzeichen.

## Was wir prüfen {#proof}

Wir prüfen die Eigentümerschaft oder den Schreibzugriff auf ein öffentliches GitHub-Repository, die Kontrolle über die Projektdomain und ob die Website antwortet. Die Prüfungen und ihre Grenzen erklärt [So funktionieren die Prüfungen](/how-proof-works/).
```

Було:

```markdown
- **Wer den Code geschrieben hat.** {{ site_name }} prüft Fakten, die sich belegen lassen: wem das verknüpfte GitHub-Repository gehört, wer die Domain kontrolliert und ob die Website antwortet. Wer den Code geschrieben hat oder wie viel davon ein KI-Werkzeug geschrieben hat, prüfen wir nicht und können wir nicht prüfen. Commit-Verlauf und Daten schreibt die Person, der das Repository gehört, und sie lassen sich ändern. Wenn du glaubst, dass ein Projekt kopiert ist, melde es.
- **Ob das Projekt gut ist.** Prüfzeichen sind keine Bewertungen. Ein Projekt mit Steady kann trotzdem eine schwache Idee sein, und ein großartiges Projekt hat vielleicht noch kein Zeichen.
- **Was die Person schreibt.** Name, Beschreibung, Screenshots, Tags, Launch-Datum und die KI-Werkzeuge unter „Gebaut mit“ kommen von der Person selbst. „Gebaut mit“ ist immer als selbst angegeben markiert.

## Was du bekommst {#builders}

- Ein öffentliches Profil, das deine Projekte sammelt. Du meldest dich mit GitHub an; wir fragen nur nach deinem öffentlichen Profil und deinen E-Mail-Adressen, nie nach Zugriff auf deine Repositories.
- Eine Seite für jedes Projekt mit seinen Prüfzeichen, Screenshots, einem 30-Tage-Verfügbarkeitsstreifen (sobald es Domain verified hat) und einem Build-Log: kurze Updates und Launch-Notizen, der Reihe nach.
- Ein Badge für dein GitHub-README oder deine Website, das die Prüfzeichen zeigt, die das Projekt gerade hat. Den Code zum Einfügen findest du auf der Projektseite.
- Folgen, Likes, eine Für-dich-Seite mit neuen Launches und Leuten, denen du folgst, und eine Seite „Entdecken“, auf der du Projekte nach Tag, Werkzeug oder Prüfzeichen findest.
- Kontrolle über deine Daten: Lade sie alle als Datei herunter oder lösche dein Konto in den Einstellungen. Keine Werbung, keine Analyse, keine Tracking-Skripte.

## Wer dahintersteht {#who}

{{ site_name }} wird von einer Person gebaut und betrieben: Danylo Rudenko, Solo-Entwickler. Es entsteht so wie viele Projekte hier: mit KI-Werkzeugen, vor allem Claude Code, und eine Person entscheidet, was gebaut wird und ob das Ergebnis taugt.

**TODO (Danylo):** Bestätige diesen Absatz und füge, wenn du willst, einen Satz über dich hinzu (wo du lebst, warum du angefangen hast).

## Wie es weitergeht {#next}

Geplant nach der ersten Version, ohne feste Reihenfolge:

- eine Für-dich-Seite mit Filter statt getrennter Tabs;
- Avatare und mehr Möglichkeiten, ein Profil zu gestalten;
- Erfolge;
- bessere Prüfung von Repositories, zum Beispiel bei Forks, und die Verknüpfung eines Repositorys mit seiner Domain;
- was Domain verified für Projekte bedeuten soll, die keine Websites sind: Kommandozeilen-Werkzeuge, Bibliotheken, mobile Apps.

**TODO (Danylo):** Prüfe vor der Veröffentlichung, ob die Liste noch zu deinen Plänen passt.
```

Стало:

```markdown
Diese Prüfungen stellen nicht fest, wer den Code geschrieben hat, wie viel KI eingesetzt wurde oder wie gut oder sicher ein Projekt ist. Die Beschreibung und die Liste der KI-Werkzeuge stammen von der Person, die das Projekt vorstellt.
```

Було:

```markdown
Fragen, Ideen, ein Fehler oder ein Projekt, das nicht hierher gehört: schreib an [{{ contact_email }}](mailto:{{ contact_email }}). Du kannst auch den Link „Melden“ auf jeder Projekt- oder Profilseite nutzen.

**TODO vor dem Start:** Diese Adresse kommt aus `CONTACT_EMAIL` in `config/branding.py` und ist noch ein Platzhalter.

```

Стало:

```markdown
Bei Fragen oder für Hilfe nutze die Seite [Support](/support/) oder schreibe an [{{ contact_email }}](mailto:{{ contact_email }}).

```

### content/de/community-rules.md

Було:

```markdown
*Entwurf. Diese Regeln sind Teil der [Nutzungsbedingungen](/legal/terms/) und können sich vor dem Start ändern.*
```

Стало:

```markdown
Diese Regeln sind Teil der [Nutzungsbedingungen](/legal/terms/).
```

Було:

```markdown
- Neue Konten können 10 Minuten nach der Registrierung posten. In den ersten 24 Stunden darf ein Beitrag einen Link und kein Bild enthalten.
- Es gibt Limits pro Stunde (Threads, Antworten, Stimmen, Bilder), und derselbe Text kann nicht zweimal hintereinander gepostet werden.
- Es gibt nur Upvotes. Für deinen eigenen Beitrag kannst du nicht stimmen.
- Du kannst deinen Beitrag bearbeiten. Änderungen in den ersten 15 Minuten bleiben unsichtbar, spätere bekommen den Hinweis „bearbeitet“. Der Titel eines Threads lässt sich nur in diesen ersten 15 Minuten ändern.
- Du kannst deinen Beitrag löschen. Haben andere schon geantwortet, bleiben ihre Antworten stehen und dein Beitrag erscheint als „[gelöscht]“.
- Die Sticker sind unser eigenes Set. Bilder werden geprüft und neu kodiert, ihre Metadaten (etwa der Aufnahmeort) werden entfernt.
```

Стало:

```markdown
- Neue Konten können 10 Minuten nach der Registrierung posten. In den ersten 24 Stunden darf ein Beitrag einen Link und kein Bild enthalten.
- Es gibt Limits pro Stunde (Threads, Antworten, Stimmen, Bilder), und derselbe Text kann nicht zweimal hintereinander gepostet werden.
- Es gibt nur Upvotes. Für deinen eigenen Beitrag kannst du nicht stimmen.
- Du kannst deinen Beitrag bearbeiten. Änderungen in den ersten 15 Minuten bleiben unsichtbar, spätere bekommen den Hinweis „bearbeitet“. Der Titel eines Threads lässt sich nur in diesen ersten 15 Minuten ändern.
- Du kannst deinen Beitrag löschen. Haben andere schon geantwortet, bleiben ihre Antworten stehen und dein Beitrag erscheint als „[gelöscht]“.
- Bilder werden geprüft und neu kodiert, ihre Metadaten (etwa der Aufnahmeort) werden entfernt.
```

### content/de/cookies.md

Було:

```markdown
> **Entwurf**, zuletzt aktualisiert am 12. November 2026. Dieser Text wurde noch nicht von einer Juristin oder einem Juristen geprüft.
>
> Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.
```

Стало:

```markdown
Zuletzt aktualisiert am 12. November 2026.

Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.
```

### content/de/privacy.md

Було:

```markdown
> **Entwurf**, zuletzt aktualisiert am 14. November 2026. Dieser Text wurde noch nicht von einer Juristin oder einem Juristen geprüft.
>
> Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.
```

Стало:

```markdown
Zuletzt aktualisiert am 14. November 2026.

Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.
```

Було:

```markdown
**Profilbild und Titelbild.** Du kannst ein Bild und ein breites Titelbild hochladen oder dein GitHub-Bild einmal kopieren lassen. Jedes Bild wird neu kodiert (das Profilbild auf 512×512, das Titelbild auf 1500×500), was versteckte Metadaten wie den GPS-Standort entfernt, bekommt einen zufälligen Dateinamen und wird auf unserem eigenen Server gespeichert: Die Seiten laden dein Bild nie von GitHub. Beide sind **öffentlich**. Wenn du ein Bild entfernst oder ersetzt oder dein Konto löschst, wird die Datei gelöscht; Kopien bleiben bis zu 14 Tage in den Backups. Ohne Bild werden deine Initialen gezeigt.
```

Стало:

```markdown
**Profilbild und Titelbild.** Du kannst ein Bild und ein breites Titelbild hochladen oder dein GitHub-Bild einmal kopieren lassen. Jedes Bild wird neu kodiert (das Profilbild auf 512×512, das Titelbild auf 1500×500), was versteckte Metadaten wie den GPS-Standort entfernt, bekommt einen zufälligen Dateinamen und wird in unserem Speicher gespeichert: Die Seiten laden dein Bild nie von GitHub. Beide sind **öffentlich**. Wenn du ein Bild entfernst oder ersetzt oder dein Konto löschst, wird die Datei gelöscht; Kopien bleiben bis zu 14 Tage in den Backups. Ohne Bild werden deine Initialen gezeigt.
```

Було:

```markdown
- deine Threads: Bereich, Titel, Text, Daten und ob ein Thread bearbeitet, angeheftet, gesperrt oder entfernt wurde;
- deine Antworten: Text, den gewählten Sticker und auf welchen Beitrag sie antworten;
- die angehängten Bilder. Sie werden wie Screenshots neu kodiert: Versteckte Metadaten wie der GPS-Standort werden entfernt, die Dateinamen sind zufällig, und wir speichern eine Kopie bis 1600 px und eine Vorschau mit 640 px auf unserem eigenen Server.
```

Стало:

```markdown
- deine Threads: Bereich, Titel, Text, Daten und ob ein Thread bearbeitet, angeheftet, gesperrt oder entfernt wurde;
- deine Antworten: Text und auf welchen Beitrag sie antworten;
- die angehängten Bilder. Sie werden wie Screenshots neu kodiert: Versteckte Metadaten wie der GPS-Standort werden entfernt, die Dateinamen sind zufällig, und wir speichern eine Kopie bis 1600 px und eine Vorschau mit 640 px in unserem Speicher.
```

Було:

```markdown
Wenn du einen Beitrag löschst, werden Text, Sticker und Bilder sofort gelöscht. Der Titel eines Threads bleibt, solange darunter Antworten anderer stehen, und wird als „[gelöscht]“ angezeigt. Wenn die Moderation einen Beitrag entfernt, werden seine Bilder sofort gelöscht, und der Text wird mit dem Grund aufbewahrt, sichtbar nur für dich, die Moderation und das Team. Die Moderation sieht gemeldete Beiträge zusammen mit der Geschichte der Autorin oder des Autors, wie bei anderen Meldungen.
```

Стало:

```markdown
Wenn du einen Beitrag löschst, werden Text und Bilder sofort gelöscht. Der Titel eines Threads bleibt, solange darunter Antworten anderer stehen, und wird als „[gelöscht]“ angezeigt. Wenn die Moderation einen Beitrag entfernt, werden seine Bilder sofort gelöscht, und der Text wird mit dem Grund aufbewahrt, sichtbar nur für dich, die Moderation und das Team. Die Moderation sieht gemeldete Beiträge zusammen mit der Geschichte der Autorin oder des Autors, wie bei anderen Meldungen.
```

Було:

```markdown
**IP-Adressen und Logs.** Die Anwendung speichert deine IP-Adresse nicht, und ihre eigenen Logs enthalten sie nicht. Zu jeder Seitenanfrage halten die Logs nur die Methode, die Seitenadresse (ohne alles nach einem `?`), den Antwortstatus, die Größe und die Antwortzeit fest, dazu Fehler. Angaben zu deinem Browser sind nicht darin. Seitenadressen enthalten Benutzernamen (`/u/<username>/`); eine Logzeile kann also zeigen, welches Profil geöffnet wurde, aber nicht von wem.
```

Стало:

```markdown
**Anwendungslogs.** Unsere Anwendungslogs enthalten die Anfragemethode, eine Route mit ausgeblendeten Daten, Antwortstatus, Größe und Dauer sowie bereinigte Fehlermeldungen. Sie enthalten keine IP-Adressen, Browserangaben, Nutzernamen, Abfrageparameter oder Formularinhalte.
```

Було:

```markdown
> **TODO vor dem Start:** Der Webserver vor der Anwendung führt ein eigenes Zugriffslog, das standardmäßig IP-Adressen enthält. Was er aufzeichnet und wie lange er es aufbewahrt (und wie lange die Logs der Anwendung aufbewahrt werden), ist noch nicht entschieden. Das muss ergänzt oder die IP-Protokollierung abgeschaltet werden, bevor diese Seite öffentlich wird.
```

Стало:

```markdown
Die Routing-Logs unseres Webhosting-Anbieters enthalten die IP-Adressen der Besuchenden. Routing-Logs und die JSON-stdout-Logs der Anwendung werden im Log-Stream des Anbieters bis zu etwa einer Woche aufbewahrt. Nur die Person, der das Hosting-Konto gehört, kann diesen Stream lesen. Die Anwendungslogs enthalten keine IP-Adressen oder personenbezogenen Daten. Zum Start nutzen wir weder ein langfristiges Log-Archiv noch ein Logging-Add-on; unser DNS-Anbieter leitet den Website-Verkehr nicht über einen Proxy. Vor dem Einrichten eines Log-Archivs oder eines Verkehrs-Proxys aktualisieren wir diese Erklärung.
```

Було:

```markdown
Wenn du uns über das [Support-Formular](/support/) schreibst, speichern wir das Thema, den Betreff, deine Nachricht, die angegebene E-Mail-Adresse (oder die deines Kontos), das Konto, mit dem du angemeldet warst, die Referenznummer einer Fehlerseite, falls du von dort kommst, und bis zu 3 Anhänge. Bilder werden wie andere Bilder neu kodiert (versteckte Metadaten wie der GPS-Standort werden entfernt); Textdateien werden als Text gespeichert. Anhänge liegen in einem privaten Ordner auf unserem Server ohne öffentliche Adresse: Nur Teammitglieder mit Zugang zum Support-Postfach können sie herunterladen. Deine E-Mail-Adresse nutzen wir nur, um zu antworten.

Wir speichern zur Nachricht weder deine IP-Adresse noch Browserdaten. Gegen Spam wird ein gesalzener Einweg-Fingerabdruck deiner IP-Adresse höchstens 24 Stunden im Cache des Servers gehalten, nie in der Datenbank oder in Logs.
```

Стало:

```markdown
Wenn du uns über das [Support-Formular](/support/) schreibst, speichern wir das Thema, den Betreff, deine Nachricht, die angegebene E-Mail-Adresse (oder die deines Kontos), das Konto, mit dem du angemeldet warst, die Referenznummer einer Fehlerseite, falls du von dort kommst, und bis zu 3 Anhänge. Bilder werden wie andere Bilder neu kodiert (versteckte Metadaten wie der GPS-Standort werden entfernt); Textdateien werden als Text gespeichert. Anhänge liegen in privatem Speicher ohne öffentliche Adresse: Nur Teammitglieder mit Zugang zum Support-Postfach können sie herunterladen. Deine E-Mail-Adresse nutzen wir nur, um zu antworten.

Wir speichern weder deine IP-Adresse noch Browserangaben zusammen mit der Nachricht. Gegen Spam enthält der Server-Cache Zähler, die durch einen gesalzenen Einweg-Hash deiner IP-Adresse gekennzeichnet sind, niemals durch die Adresse selbst. In der Produktionsumgebung nutzt dieser Cache die Datenbank. Ein Zähler gilt höchstens 24 Stunden. Abgelaufene Cache-Zeilen können bis zur täglichen Bereinigung in der Datenbank verbleiben. Der Hash wird weder mit der Support-Nachricht noch in den Anwendungslogs gespeichert.
```

Було:

```markdown
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
- Logs von Webserver und Anwendung: **TODO**, noch nicht entschieden.
```

Стало:

```markdown
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
```

Було:

```markdown
- **GitHub, Inc.** Du meldest dich auf github.com an, und unser Server liest dein Profil und öffentliche Repository-Daten über die API von GitHub. Für deine Nutzung von GitHub gilt dessen eigene Datenschutzerklärung.
- **Unser E-Mail-Anbieter** (zum Beispiel Google, wenn das Postfach des Teams ein Gmail-Konto ist) stellt den Hinweis zu jeder Support-Nachricht mit ihrem Text und deiner E-Mail-Adresse im Postfach des Teams zu.
- **Die Server deines Projekts.** Für die Prüfungen Domain verified und Steady kontaktiert unser Server das DNS deiner Domain und die Adresse deines Projekts. Sie sehen unseren Server, nicht dich.
- **Unser Hosting-Anbieter**, der für uns den Server und die Datenbank betreibt.
```

Стало:

```markdown
- **Anbieter für Webhosting und verwaltete Datenbanken** betreiben die Anwendung und speichern ihre Datensätze für uns.
- **S3-kompatibler Objektspeicher** speichert hochgeladene Bilder und private Support-Anhänge in unserem Auftrag.
- **GitHub** ermöglicht die Anmeldung und liefert Profil- und öffentliche Repository-Daten für unsere Prüfungen. Für deine Nutzung von GitHub gilt dessen eigene Datenschutzerklärung.
- **Ein E-Mail-Dienst** liefert Support-Benachrichtigungen mit Nachricht und E-Mail-Adresse der absendenden Person an unser Team-Postfach.
- **DNS- und Webserver deines Projekts** erhalten unsere Prüfungsanfragen. Sie sehen die Adresse unseres Servers, nicht die der Besuchenden.
```

### content/de/terms.md

Було:

```markdown
> **Entwurf**, zuletzt aktualisiert am 14. November 2026 (Version {{ terms_version }}). Dieser Text wurde noch nicht von einer Juristin oder einem Juristen geprüft.
>
> Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.
```

Стало:

```markdown
Zuletzt aktualisiert am 14. November 2026 (Version {{ terms_version }}).

Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.
```

### content/en/about.md

Було:

```markdown
{{ site_name }} is a public place where people who build with AI tools show the work they actually shipped. Instead of claims, each project carries proof marks that we check ourselves.

## The problem {#problem}

Saying "I shipped it" costs nothing. A screenshot, a launch post or a line in a CV can describe anything, and from the outside nobody can tell whether the product exists, who controls it, or whether it still runs a month later.

GitHub shows code. LinkedIn shows claims. {{ site_name }} tries to show outcomes: a project, the facts we could check about it, and what its builder did next. The project is the main thing here; a profile is just the collection of someone's projects.

## How proof works {#proof}

A project can earn three hallmarks. Each one is a fact our server checks, and each one disappears when the fact stops being true.

- **Repo owner.** The project links a public GitHub repository. We ask GitHub's public API whether it belongs to the author's personal GitHub account and is not a fork; for organisation and team repositories, the author adds a file with this project's token instead. We check it again every week.
- **Domain verified.** The author proves control of the project's domain with a token we generate: a DNS TXT record or a meta tag on the homepage. We re-check it regularly, and the mark holds only while the domain was confirmed in the last 35 days.
- **Steady.** Once a project has Domain verified, we open its address about every 3 hours. Steady needs at least 40 checks in the last 30 days, and at least 95% of them must get an answer without an error within 5 seconds.

The full rules, including how each mark can be lost, are on [How proof works](/how-proof-works/).

## What we do not verify {#not-verified}

- **Who wrote the code.** {{ site_name }} checks facts it can prove: who owns the linked GitHub repository, who controls the domain, and whether the site answers. It does not and cannot check who wrote the code, or how much of it an AI tool wrote. Commit history and dates are written by the repository owner and can be changed. If you think a project is copied, report it.
- **Whether the project is good.** Hallmarks are not reviews. A Steady project can still be a weak idea, and a great project can have no marks yet.
- **What the author writes.** Name, description, screenshots, tags, launch date and the AI tools under "Built with" come from the author. "Built with" is always labeled self-declared.

## What builders get {#builders}

- A public profile that collects your projects. You sign in with GitHub; we ask only for your public profile and your email addresses, never for access to your repositories.
- A page for each project with its hallmarks, screenshots, a 30-day uptime strip once it has Domain verified, and a build log: short updates and launch notes, in order.
- A badge for your GitHub README or website that shows the hallmarks the project has right now. The project page gives you the code to paste.
- Follows, likes, a For You Page with new launches and with the people you follow, and a Discover page to find projects by tag, tool or hallmark.
- Control over your data: download all of it as a file, or delete your account, from Settings. No ads, no analytics, no tracking scripts.

## Who is behind it {#who}

{{ site_name }} is built and run by one person, Danylo Rudenko, a solo builder. It is made the way many projects here are made: with AI tools, mostly Claude Code, with one person deciding what gets built and checking the result.

**TODO (Danylo):** confirm this paragraph, and add a sentence about yourself if you want (where you are, why you started).

## What is next {#next}

Planned after the first version, in no fixed order:

- one For You Page with a filter, instead of separate tabs;
- avatars and more ways to shape a profile;
- achievements;
- better repository checks, for example for forks, and linking a repository to its domain;
- what "Domain verified" should mean for projects that are not websites: command-line tools, libraries, mobile apps.

**TODO (Danylo):** check that this list still matches your plans before publishing.
```

Стало:

```markdown
{{ site_name }} is a public place to show software projects built with AI tools. Project pages bring together descriptions, screenshots, build updates and proof marks.

## What we check {#proof}

We check ownership or write access to a public GitHub repository, control of the project domain and whether the website responds. The checks and their limits are explained in [How proof works](/how-proof-works/).

## What we do not check {#not-verified}

These checks do not establish who wrote the code, how much AI was used, or the quality or safety of a project. Descriptions and listed AI tools are supplied by the author.
```

Було:

```markdown
Questions, ideas, a bug, or a project that should not be here: write to [{{ contact_email }}](mailto:{{ contact_email }}). You can also use the "Report" link on any project or profile.

**TODO before launch:** this address comes from `CONTACT_EMAIL` in `config/branding.py` and is still a placeholder.

```

Стало:

```markdown
For questions or help, use [Support](/support/) or write to [{{ contact_email }}](mailto:{{ contact_email }}).

```

### content/en/community-rules.md

Було:

```markdown
*Draft. These rules are part of the [Terms](/legal/terms/) and may change before launch.*
```

Стало:

```markdown
These rules are part of the [Terms](/legal/terms/).
```

Було:

```markdown
- New accounts can post 10 minutes after signing up. During the first 24 hours a post can hold one link and no images.
- There are limits per hour (threads, replies, upvotes, images) and the same text cannot be posted twice in a row.
- There are upvotes only. You cannot upvote your own post.
- You can edit your post. Edits in the first 15 minutes are silent; later ones show an "edited" mark. A thread's title can only be changed in those first 15 minutes.
- You can delete your post. If others already replied, their replies stay and yours shows as "[deleted]".
- Stickers are our own set. Images are checked and re-encoded, and their metadata (such as camera location) is removed.
```

Стало:

```markdown
- New accounts can post 10 minutes after signing up. During the first 24 hours a post can hold one link and no images.
- There are limits per hour (threads, replies, upvotes, images) and the same text cannot be posted twice in a row.
- There are upvotes only. You cannot upvote your own post.
- You can edit your post. Edits in the first 15 minutes are silent; later ones show an "edited" mark. A thread's title can only be changed in those first 15 minutes.
- You can delete your post. If others already replied, their replies stay and yours shows as "[deleted]".
- Images are checked and re-encoded, and their metadata (such as camera location) is removed.
```

### content/en/cookies.md

Було:

```markdown
> **Draft**, last updated 12 November 2026. This text has not been reviewed by a lawyer yet.
```

Стало:

```markdown
Last updated 12 November 2026.
```

### content/en/privacy.md

Було:

```markdown
> **Draft**, last updated 14 November 2026. This text has not been reviewed by a lawyer yet.
```

Стало:

```markdown
Last updated 14 November 2026.
```

Було:

```markdown
**Profile picture and cover.** You can upload a picture and a wide cover image, or copy your GitHub picture once with "Use my GitHub picture". Every image is re-encoded (the picture to 512×512, the cover to 1500×500), which removes hidden metadata such as GPS location, gets a random file name and is stored on our own server: pages never load your picture from GitHub. Both are **public**. When you remove or replace one, or delete your account, the file is deleted; copies stay in backups for up to 14 days. Without a picture, your initials are shown.
```

Стало:

```markdown
**Profile picture and cover.** You can upload a picture and a wide cover image, or copy your GitHub picture once with "Use my GitHub picture". Every image is re-encoded (the picture to 512×512, the cover to 1500×500), which removes hidden metadata such as GPS location, gets a random file name and is stored for us: pages never load your picture from GitHub. Both are **public**. When you remove or replace one, or delete your account, the file is deleted; copies stay in backups for up to 14 days. Without a picture, your initials are shown.
```

Було:

```markdown
- your threads: board, title, text, dates, and whether a thread was edited, pinned, locked or removed;
- your replies: text, the sticker you picked, and which post they answer;
- the images you attach. They are re-encoded like screenshots: hidden metadata such as GPS location is removed, file names are random, and we keep a copy up to 1600 px and a 640 px thumbnail on our own server.
```

Стало:

```markdown
- your threads: board, title, text, dates, and whether a thread was edited, pinned, locked or removed;
- your replies: text and which post they answer;
- the images you attach. They are re-encoded like screenshots: hidden metadata such as GPS location is removed, file names are random, and we keep a copy up to 1600 px and a 640 px thumbnail in our storage.
```

Було:

```markdown
When you delete a post, its text, sticker and images are deleted at once. A thread's title stays while replies of others are under it, shown as "[deleted]". When moderators remove a post, its images are deleted at once, and its text is kept with the reason, visible only to you, moderators and staff. Moderators see reported posts together with the author's history, as for other reports.
```

Стало:

```markdown
When you delete a post, its text and images are deleted at once. A thread's title stays while replies of others are under it, shown as "[deleted]". When moderators remove a post, its images are deleted at once, and its text is kept with the reason, visible only to you, moderators and staff. Moderators see reported posts together with the author's history, as for other reports.
```

Було:

```markdown
**IP addresses and logs.** The application does not store your IP address, and its own logs do not contain it. For each page request the logs record only the method, the page address (without anything after a `?`), the response status, size and time taken, plus errors. They hold no browser details. Page addresses include usernames (`/u/<username>/`), so a log line can show which profile was opened, but not by whom.
```

Стало:

```markdown
**Application logs.** Our application logs contain the request method, a redacted route, response status, size and duration, and sanitized errors. They do not contain IP addresses, browser details, usernames, query strings or form contents.
```

Було:

```markdown
> **TODO before launch:** the web server in front of the application keeps its own access log, which by default includes IP addresses. What it records and how long it keeps it (and how long the application logs are kept) has not been decided yet. Fill this in, or switch IP logging off, before this page goes public.
```

Стало:

```markdown
Our web hosting provider's routing logs include visitors' IP addresses. Routing logs and the application's JSON stdout logs are kept in the provider's log stream for up to approximately one week. Only the hosting account holder can read that stream. The application logs do not include IP addresses or personal data. At launch, we do not use a long-term log archive or logging add-on, and our DNS provider does not proxy website traffic. We update this policy before introducing a log archive or enabling a traffic proxy.
```

Було:

```markdown
When you write to us through the [support form](/support/), we store the topic, the subject, your message, the email address you give (or your account's), the account you were signed in with, the reference number of an error page if you came from one, and up to 3 attachments. Images are re-encoded like other pictures (hidden metadata such as GPS location is removed); text files are kept as text. Attachments are stored in a private folder on our server that has no public address: only staff with access to the support inbox can download them. We use your email address only to reply.

We do not store your IP address or browser details with the message. To stop spam, a salted one-way fingerprint of your IP address is kept in the server's cache for at most 24 hours, never in the database or the logs.
```

Стало:

```markdown
When you write to us through the [support form](/support/), we store the topic, the subject, your message, the email address you give (or your account's), the account you were signed in with, the reference number of an error page if you came from one, and up to 3 attachments. Images are re-encoded like other pictures (hidden metadata such as GPS location is removed); text files are kept as text. Attachments are stored in private storage that has no public address: only staff with access to the support inbox can download them. We use your email address only to reply.

We do not store your IP address or browser details with the message. To limit spam, the server cache holds counters identified by a salted one-way hash of your IP address, never the address itself. In production, this cache uses the database. A counter applies for at most 24 hours. Expired database cache rows can remain until they are removed during daily maintenance. The hash is not stored with the support message or in application logs.
```

Було:

```markdown
- Your account, profile, projects, follows and likes: until you delete them or your account.
- Support messages and their attachments: closed ones 12 months after they were sent, the others until they are closed; with your account.
- Community threads, replies and images: until you delete them or your account (see "Community" above for what stays). Upvotes: until you take them back or delete your account.
- Reply notifications: 90 days.
- Profile picture and cover: until you remove or replace them, or delete your account.
- Uptime checks: 90 days.
- Moderation decisions about you (mutes, bans, removed projects) and notices: while your account exists; they are deleted with it. Reports about you stay without a link to your account, with only the name shown at the time.
- Ban hash of a GitHub id: only until the ban ends or is lifted.
- Sign-in sessions: 2 weeks, or until you sign out.
- Reports you made: kept after they are handled. If you delete your account, they stay without your name.
- Audit log: kept. Entries about a deleted account do not contain the username or email.
- Abuse-protection counters: at most 24 hours.
- Backups: 14 days. A deleted account disappears from them within 14 days.
- Error log files: until they are full (5 MB, plus 5 older copies of 5 MB each), then the oldest entries are deleted.
- Web server and application logs: **TODO**, not decided yet.
```

Стало:

```markdown
- Your account, profile, projects, follows and likes: until you delete them or your account.
- Support messages and their attachments: closed ones 12 months after they were sent, the others until they are closed; with your account.
- Community threads, replies and images: until you delete them or your account (see "Community" above for what stays). Upvotes: until you take them back or delete your account.
- Reply notifications: 90 days.
- Profile picture and cover: until you remove or replace them, or delete your account.
- Uptime checks: 90 days.
- Moderation decisions about you (mutes, bans, removed projects) and notices: while your account exists; they are deleted with it. Reports about you stay without a link to your account, with only the name shown at the time.
- Ban hash of a GitHub id: only until the ban ends or is lifted.
- Sign-in sessions: 2 weeks, or until you sign out.
- Reports you made: kept after they are handled. If you delete your account, they stay without your name.
- Audit log: kept. Entries about a deleted account do not contain the username or email.
- Abuse-protection counters: at most 24 hours.
- Backups: 14 days. A deleted account disappears from them within 14 days.
- Error log files: until they are full (5 MB, plus 5 older copies of 5 MB each), then the oldest entries are deleted.
- Hosting routing logs and application stdout logs: up to approximately one week in the hosting log stream; no long-term log archive at launch.
```

Було:

```markdown
- **GitHub, Inc.** You sign in on github.com, and our server reads your profile and public repository data from GitHub's API. GitHub's own privacy statement applies to your use of GitHub.
- **Our email provider** (for example Google, if the team's mailbox is a Gmail account) carries the notice about each support message, with its text and your email address, to the team's mailbox.
- **The servers of your project.** For the Domain verified and Steady checks our server contacts your domain's DNS and your project's address. They see our server, not you.
- **Our hosting provider**, which runs the server and the database for us.

We do not sell your data and do not share it for advertising.
```

Стало:

```markdown
- **Web hosting and managed database providers** operate the application and store its records for us.
- **S3-compatible object storage** stores uploaded images and private support attachments on our behalf.
- **GitHub** provides sign-in and the profile and public repository data used by our checks. GitHub's own privacy statement applies to your use of GitHub.
- **An email service** carries support notifications, including the message and the sender's email address, to our team's mailbox.
- **Your project's DNS and web servers** receive our verification requests. They see our server's address, not the visitor's.

We do not sell your data or share it for advertising.
```

### content/en/terms.md

Було:

```markdown
> **Draft**, last updated 14 November 2026 (version {{ terms_version }}). This text has not been reviewed by a lawyer yet.
```

Стало:

```markdown
Last updated 14 November 2026 (version {{ terms_version }}).
```

### content/es/about.md

Було:

```markdown
# Sobre {{ site_name }}

{{ site_name }} es un lugar público donde quienes construyen con herramientas de IA muestran lo que de verdad lanzaron. En lugar de afirmaciones, cada proyecto lleva sellos de prueba que comprobamos nosotros mismos.

## El problema {#problem}

Decir «lo lancé» no cuesta nada. Una captura, un post de lanzamiento o una línea en el CV pueden describir cualquier cosa, y desde fuera nadie sabe si el producto existe, quién lo controla o si sigue funcionando un mes después.

GitHub muestra código. LinkedIn muestra afirmaciones. {{ site_name }} intenta mostrar resultados: un proyecto, los hechos que pudimos comprobar sobre él y lo que hizo después quien lo construyó. Lo principal aquí es el proyecto; un perfil es solo la colección de proyectos de alguien.

## Cómo funciona la verificación {#proof}

Un proyecto puede ganar tres sellos. Cada uno es un hecho que comprueba nuestro servidor, y cada uno desaparece cuando el hecho deja de ser cierto.

- **Repo owner.** El proyecto enlaza un repositorio público de GitHub. Preguntamos a la API pública de GitHub si pertenece a la cuenta personal de GitHub del autor y no es un fork; en repositorios de organizaciones y equipos, el autor añade en su lugar un archivo con el token de este proyecto. Lo volvemos a comprobar cada semana.
- **Domain verified.** El autor demuestra que controla el dominio del proyecto con un token que generamos: un registro TXT en el DNS o una metaetiqueta en la página principal. Lo volvemos a comprobar con regularidad, y el sello solo se mantiene mientras el dominio se haya confirmado en los últimos 35 días.
- **Steady.** Cuando un proyecto tiene Domain verified, abrimos su dirección más o menos cada 3 horas. Steady necesita al menos 40 comprobaciones en los últimos 30 días, y al menos el 95 % de ellas debe recibir respuesta sin error en 5 segundos.

Las reglas completas, incluido cómo se puede perder cada sello, están en [Cómo funciona la verificación](/how-proof-works/).

## Lo que no verificamos {#not-verified}

- **Quién escribió el código.** {{ site_name }} comprueba hechos que puede demostrar: a quién pertenece el repositorio de GitHub enlazado, quién controla el dominio y si el sitio responde. No comprueba ni puede comprobar quién escribió el código ni cuánto escribió una herramienta de IA. El historial de commits y sus fechas los escribe el propietario del repositorio y se pueden cambiar. Si crees que un proyecto está copiado, denúncialo.
- **Si el proyecto es bueno.** Los sellos no son reseñas. Un proyecto con Steady puede ser una idea floja, y un gran proyecto puede no tener todavía ningún sello.
- **Lo que escribe el autor.** El nombre, la descripción, las capturas, las etiquetas, la fecha de lanzamiento y las herramientas de IA en «Creado con» los indica el autor. «Creado con» siempre aparece como declarado por el autor.

## Qué obtienes {#builders}

- Un perfil público que reúne tus proyectos. Inicias sesión con GitHub; solo pedimos tu perfil público y tus direcciones de correo, nunca acceso a tus repositorios.
- Una página para cada proyecto con sus sellos, capturas, una franja de disponibilidad de 30 días (cuando tiene Domain verified) y un registro de desarrollo: actualizaciones breves y notas de lanzamiento, en orden.
- Una insignia para el README de GitHub o tu web que muestra los sellos que tiene el proyecto en este momento. El código para pegar está en la página del proyecto.
- Seguir, me gusta, una página Para ti con nuevos lanzamientos y con la gente que sigues, y una página «Descubrir» para encontrar proyectos por etiqueta, herramienta o sello.
- Control sobre tus datos: descárgalos todos en un archivo o elimina tu cuenta desde Ajustes. Sin anuncios, sin analítica, sin scripts de seguimiento.

## Quién está detrás {#who}

{{ site_name }} lo construye y lo mantiene una sola persona, Danylo Rudenko, desarrollador independiente. Está hecho como muchos proyectos de aquí: con herramientas de IA, sobre todo Claude Code, y una persona decide qué se construye y si el resultado sirve.

**TODO (Danylo):** confirma este párrafo y, si quieres, añade una frase sobre ti (dónde estás, por qué empezaste).

## Qué viene después {#next}

Previsto después de la primera versión, sin un orden fijo:

- una sola página Para ti con un filtro en lugar de pestañas separadas;
- avatares y más formas de personalizar un perfil;
- logros;
- mejores comprobaciones de repositorios, por ejemplo con forks, y vincular un repositorio con su dominio;
- qué debería significar Domain verified para proyectos que no son webs: herramientas de línea de comandos, bibliotecas, apps móviles.

**TODO (Danylo):** antes de publicar, comprueba que la lista sigue coincidiendo con tus planes.
```

Стало:

```markdown
# Acerca de {{ site_name }}

{{ site_name }} es un espacio público para mostrar proyectos de software creados con herramientas de IA. Las páginas de los proyectos reúnen descripciones, capturas de pantalla, novedades del desarrollo y sellos de verificación.

## Qué comprobamos {#proof}

Comprobamos la propiedad o el acceso de escritura a un repositorio público de GitHub, el control del dominio del proyecto y si el sitio responde. Las comprobaciones y sus límites se explican en [Cómo funcionan las pruebas](/how-proof-works/).

## Qué no comprobamos {#not-verified}

Estas comprobaciones no determinan quién escribió el código, cuánto se utilizó la IA ni la calidad o seguridad del proyecto. El autor proporciona la descripción y la lista de herramientas de IA.
```

Було:

```markdown
Preguntas, ideas, un error o un proyecto que no debería estar aquí: escribe a [{{ contact_email }}](mailto:{{ contact_email }}). También puedes usar el enlace «Denunciar» en cualquier proyecto o perfil.

**TODO antes del lanzamiento:** esta dirección viene de `CONTACT_EMAIL` en `config/branding.py` y todavía es provisional.

```

Стало:

```markdown
Si tienes preguntas o necesitas ayuda, usa la página de [Soporte](/support/) o escribe a [{{ contact_email }}](mailto:{{ contact_email }}).

```

### content/es/community-rules.md

Було:

```markdown
*Borrador. Estas normas forman parte de los [Términos](/legal/terms/) y pueden cambiar antes del lanzamiento.*
```

Стало:

```markdown
Estas normas forman parte de los [Términos](/legal/terms/).
```

Було:

```markdown
- Las cuentas nuevas pueden publicar 10 minutos después de registrarse. Durante las primeras 24 horas, una publicación puede tener un enlace y ninguna imagen.
- Hay límites por hora (hilos, respuestas, votos, imágenes) y no se puede publicar el mismo texto dos veces seguidas.
- Solo hay votos a favor. No puedes votar tu propia publicación.
- Puedes editar tu publicación. Los cambios en los primeros 15 minutos no se marcan; los posteriores muestran la marca «editado». El título de un hilo solo se puede cambiar en esos primeros 15 minutos.
- Puedes eliminar tu publicación. Si otras personas ya respondieron, sus respuestas se quedan y la tuya aparece como «[eliminado]».
- Los stickers son un conjunto propio. Las imágenes se revisan y se vuelven a codificar, y se eliminan sus metadatos (como la ubicación de la cámara).
```

Стало:

```markdown
- Las cuentas nuevas pueden publicar 10 minutos después de registrarse. Durante las primeras 24 horas, una publicación puede tener un enlace y ninguna imagen.
- Hay límites por hora (hilos, respuestas, votos, imágenes) y no se puede publicar el mismo texto dos veces seguidas.
- Solo hay votos a favor. No puedes votar tu propia publicación.
- Puedes editar tu publicación. Los cambios en los primeros 15 minutos no se marcan; los posteriores muestran la marca «editado». El título de un hilo solo se puede cambiar en esos primeros 15 minutos.
- Puedes eliminar tu publicación. Si otras personas ya respondieron, sus respuestas se quedan y la tuya aparece como «[eliminado]».
- Las imágenes se revisan y se vuelven a codificar, y se eliminan sus metadatos (como la ubicación de la cámara).
```

### content/es/cookies.md

Було:

```markdown
> **Borrador**, última actualización el 12 de noviembre de 2026. Este texto aún no ha sido revisado por un abogado.
>
> Traducción de cortesía; prevalece la versión en inglés.
```

Стало:

```markdown
Última actualización el 12 de noviembre de 2026.

Traducción de cortesía; prevalece la versión en inglés.
```

### content/es/privacy.md

Було:

```markdown
> **Borrador**, última actualización el 14 de noviembre de 2026. Este texto aún no ha sido revisado por un abogado.
>
> Traducción de cortesía; prevalece la versión en inglés.
```

Стало:

```markdown
Última actualización el 14 de noviembre de 2026.

Traducción de cortesía; prevalece la versión en inglés.
```

Було:

```markdown
**Foto de perfil y portada.** Puedes subir una foto y una imagen de portada ancha, o copiar una vez tu imagen de GitHub. Cada imagen se vuelve a codificar (la foto a 512×512, la portada a 1500×500), lo que elimina metadatos ocultos como la ubicación GPS, recibe un nombre de archivo aleatorio y se guarda en nuestro propio servidor: las páginas nunca cargan tu foto desde GitHub. Ambas son **públicas**. Cuando quitas o reemplazas una, o eliminas tu cuenta, el archivo se borra; las copias quedan en las copias de seguridad hasta 14 días. Sin foto, se muestran tus iniciales.
```

Стало:

```markdown
**Foto de perfil y portada.** Puedes subir una foto y una imagen de portada ancha, o copiar una vez tu imagen de GitHub. Cada imagen se vuelve a codificar (la foto a 512×512, la portada a 1500×500), lo que elimina metadatos ocultos como la ubicación GPS, recibe un nombre de archivo aleatorio y se guarda en nuestro almacenamiento: las páginas nunca cargan tu foto desde GitHub. Ambas son **públicas**. Cuando quitas o reemplazas una, o eliminas tu cuenta, el archivo se borra; las copias quedan en las copias de seguridad hasta 14 días. Sin foto, se muestran tus iniciales.
```

Було:

```markdown
- tus hilos: sección, título, texto, fechas y si un hilo fue editado, fijado, cerrado o retirado;
- tus respuestas: texto, el sticker que elegiste y a qué publicación responden;
- las imágenes que adjuntas. Se recodifican como las capturas de pantalla: se eliminan los metadatos ocultos, como la ubicación GPS, los nombres de archivo son aleatorios y guardamos una copia de hasta 1600 px y una miniatura de 640 px en nuestro propio servidor.
```

Стало:

```markdown
- tus hilos: sección, título, texto, fechas y si un hilo fue editado, fijado, cerrado o retirado;
- tus respuestas: texto y a qué publicación responden;
- las imágenes que adjuntas. Se recodifican como las capturas de pantalla: se eliminan los metadatos ocultos, como la ubicación GPS, los nombres de archivo son aleatorios y guardamos una copia de hasta 1600 px y una miniatura de 640 px en nuestro almacenamiento.
```

Було:

```markdown
Cuando eliminas una publicación, su texto, sticker e imágenes se borran al momento. El título de un hilo se queda mientras haya respuestas de otras personas debajo, y se muestra como «[eliminado]». Cuando los moderadores retiran una publicación, sus imágenes se borran al momento y su texto se guarda con el motivo, visible solo para ti, los moderadores y el equipo. Los moderadores ven las publicaciones denunciadas junto con el historial de su autor, como en otras denuncias.
```

Стало:

```markdown
Cuando eliminas una publicación, su texto e imágenes se borran al momento. El título de un hilo se queda mientras haya respuestas de otras personas debajo, y se muestra como «[eliminado]». Cuando los moderadores retiran una publicación, sus imágenes se borran al momento y su texto se guarda con el motivo, visible solo para ti, los moderadores y el equipo. Los moderadores ven las publicaciones denunciadas junto con el historial de su autor, como en otras denuncias.
```

Було:

```markdown
**Direcciones IP y registros.** La aplicación no guarda tu dirección IP y sus propios registros no la contienen. De cada petición de página los registros anotan solo el método, la dirección de la página (sin lo que va después de un `?`), el estado de la respuesta, el tamaño y el tiempo empleado, además de los errores. No contienen datos de tu navegador. Las direcciones de página incluyen nombres de usuario (`/u/<username>/`), así que una línea del registro puede mostrar qué perfil se abrió, pero no quién lo abrió.
```

Стало:

```markdown
**Registros de la aplicación.** Los registros de nuestra aplicación contienen el método de solicitud, una ruta con los datos ocultos, el estado, tamaño y duración de la respuesta y errores depurados. No contienen direcciones IP, datos del navegador, nombres de usuario, parámetros de consulta ni contenido de formularios.
```

Було:

```markdown
> **TODO antes del lanzamiento:** el servidor web que está delante de la aplicación lleva su propio registro de accesos, que por defecto incluye direcciones IP. Aún no se ha decidido qué anota ni cuánto tiempo lo conserva (ni cuánto se conservan los registros de la aplicación). Hay que completarlo, o desactivar el registro de IP, antes de que esta página sea pública.
```

Стало:

```markdown
Los registros de enrutamiento de nuestro proveedor de alojamiento web incluyen las direcciones IP de los visitantes. Estos registros y los registros JSON de stdout de la aplicación se conservan en el flujo de registros del proveedor durante un máximo de aproximadamente una semana. Solo el titular de la cuenta de alojamiento puede leer ese flujo. Los registros de la aplicación no incluyen direcciones IP ni datos personales. En el lanzamiento no usamos archivos de registros a largo plazo ni complementos de registro, y nuestro proveedor de DNS no actúa como proxy del tráfico del sitio. Actualizamos esta política antes de añadir un archivo de registros o activar un proxy de tráfico.
```

Було:

```markdown
Cuando nos escribes con el [formulario de soporte](/support/), guardamos el tema, el asunto, tu mensaje, la dirección de correo que indicas (o la de tu cuenta), la cuenta con la que habías iniciado sesión, el número de referencia de una página de error si vienes de una y hasta 3 archivos adjuntos. Las imágenes se vuelven a codificar como las demás (se eliminan metadatos ocultos como la ubicación GPS); los archivos de texto se guardan como texto. Los adjuntos se guardan en una carpeta privada de nuestro servidor que no tiene dirección pública: solo el personal con acceso al buzón de soporte puede descargarlos. Usamos tu correo solo para responderte.

No guardamos tu dirección IP ni datos del navegador con el mensaje. Para frenar el spam, una huella unidireccional con sal de tu dirección IP se guarda en la caché del servidor como máximo 24 horas, nunca en la base de datos ni en los registros.
```

Стало:

```markdown
Cuando nos escribes con el [formulario de soporte](/support/), guardamos el tema, el asunto, tu mensaje, la dirección de correo que indicas (o la de tu cuenta), la cuenta con la que habías iniciado sesión, el número de referencia de una página de error si vienes de una y hasta 3 archivos adjuntos. Las imágenes se vuelven a codificar como las demás (se eliminan metadatos ocultos como la ubicación GPS); los archivos de texto se guardan como texto. Los adjuntos se guardan en almacenamiento privado que no tiene dirección pública: solo el personal con acceso al buzón de soporte puede descargarlos. Usamos tu correo solo para responderte.

No guardamos tu dirección IP ni datos del navegador con el mensaje. Para limitar el spam, la caché del servidor contiene contadores identificados por un hash unidireccional con sal de tu dirección IP, nunca por la dirección en sí. En producción esta caché usa la base de datos. Un contador se aplica durante un máximo de 24 horas. Las filas caducadas de la caché pueden permanecer en la base de datos hasta su eliminación durante el mantenimiento diario. El hash no se guarda con el mensaje de soporte ni en los registros de la aplicación.
```

Було:

```markdown
- Tu cuenta, perfil, proyectos, seguimientos y me gusta: hasta que los elimines a ellos o a tu cuenta.
- Mensajes de soporte y adjuntos: los cerrados, 12 meses después de enviarse; los demás, hasta que se cierran; con tu cuenta.
- Hilos, respuestas e imágenes de la comunidad: hasta que los elimines o elimines tu cuenta (lo que se queda se explica arriba, en «Comunidad»). Votos: hasta que los retires o elimines tu cuenta.
- Avisos de respuestas: 90 días.
- Foto de perfil y portada: hasta que las quites o reemplaces, o elimines tu cuenta.
- Comprobaciones de disponibilidad: 90 días.
- Decisiones de moderación sobre ti (silencios, bloqueos, proyectos retirados) y avisos: mientras exista tu cuenta; se borran con ella. Las denuncias sobre ti se conservan sin vínculo con tu cuenta, solo con el nombre de ese momento.
- Hash del id de GitHub de una cuenta bloqueada: solo hasta que el bloqueo termine o se levante.
- Sesiones de inicio de sesión: 2 semanas, o hasta que cierres sesión.
- Denuncias que hiciste: se conservan una vez tramitadas. Si eliminas tu cuenta, quedan sin tu nombre.
- Registro de auditoría: se conserva. Las entradas sobre una cuenta eliminada no contienen el nombre de usuario ni el correo.
- Contadores contra abusos: 24 horas como máximo.
- Copias de seguridad: 14 días. Una cuenta eliminada desaparece de ellas en un plazo de 14 días.
- Archivos del registro de errores: hasta que se llenan (5 MB más 5 copias anteriores de 5 MB), luego se borran las entradas más antiguas.
- Registros del servidor web y de la aplicación: **TODO**, aún sin decidir.
```

Стало:

```markdown
- Tu cuenta, perfil, proyectos, seguimientos y me gusta: hasta que los elimines a ellos o a tu cuenta.
- Mensajes de soporte y adjuntos: los cerrados, 12 meses después de enviarse; los demás, hasta que se cierran; con tu cuenta.
- Hilos, respuestas e imágenes de la comunidad: hasta que los elimines o elimines tu cuenta (lo que se queda se explica arriba, en «Comunidad»). Votos: hasta que los retires o elimines tu cuenta.
- Avisos de respuestas: 90 días.
- Foto de perfil y portada: hasta que las quites o reemplaces, o elimines tu cuenta.
- Comprobaciones de disponibilidad: 90 días.
- Decisiones de moderación sobre ti (silencios, bloqueos, proyectos retirados) y avisos: mientras exista tu cuenta; se borran con ella. Las denuncias sobre ti se conservan sin vínculo con tu cuenta, solo con el nombre de ese momento.
- Hash del id de GitHub de una cuenta bloqueada: solo hasta que el bloqueo termine o se levante.
- Sesiones de inicio de sesión: 2 semanas, o hasta que cierres sesión.
- Denuncias que hiciste: se conservan una vez tramitadas. Si eliminas tu cuenta, quedan sin tu nombre.
- Registro de auditoría: se conserva. Las entradas sobre una cuenta eliminada no contienen el nombre de usuario ni el correo.
- Contadores contra abusos: 24 horas como máximo.
- Copias de seguridad: 14 días. Una cuenta eliminada desaparece de ellas en un plazo de 14 días.
- Archivos del registro de errores: hasta que se llenan (5 MB más 5 copias anteriores de 5 MB), luego se borran las entradas más antiguas.
- Registros de enrutamiento del alojamiento y stdout de la aplicación: hasta aproximadamente una semana en el flujo de registros del alojamiento; sin archivo a largo plazo en el lanzamiento.
```

Було:

```markdown
- **GitHub, Inc.** Inicias sesión en github.com y nuestro servidor lee tu perfil y los datos públicos de repositorios desde la API de GitHub. La declaración de privacidad propia de GitHub se aplica a tu uso de GitHub.
- **Nuestro proveedor de correo** (por ejemplo Google, si el buzón del equipo es una cuenta de Gmail) entrega al buzón del equipo el aviso de cada mensaje de soporte, con su texto y tu correo.
- **Los servidores de tu proyecto.** Para las comprobaciones de Domain verified y Steady, nuestro servidor contacta con el DNS de tu dominio y con la dirección de tu proyecto. Ven nuestro servidor, no a ti.
- **Nuestro proveedor de alojamiento**, que ejecuta el servidor y la base de datos por nosotros.
```

Стало:

```markdown
- **Los proveedores de alojamiento web y base de datos gestionada** operan la aplicación y almacenan sus registros por nosotros.
- **El almacenamiento de objetos compatible con S3** almacena las imágenes subidas y los adjuntos privados de soporte en nuestro nombre.
- **GitHub** permite el inicio de sesión y proporciona datos de perfiles y repositorios públicos para nuestras comprobaciones. Su propia política de privacidad se aplica a tu uso de GitHub.
- **Un servicio de correo** entrega al buzón del equipo los avisos de soporte, con el mensaje y la dirección de correo del remitente.
- **Los servidores DNS y web de tu proyecto** reciben nuestras solicitudes de verificación. Ven la dirección de nuestro servidor, no la del visitante.
```

### content/es/terms.md

Було:

```markdown
> **Borrador**, última actualización el 14 de noviembre de 2026 (versión {{ terms_version }}). Este texto aún no ha sido revisado por un abogado.
>
> Traducción de cortesía; prevalece la versión en inglés.
```

Стало:

```markdown
Última actualización el 14 de noviembre de 2026 (versión {{ terms_version }}).

Traducción de cortesía; prevalece la versión en inglés.
```

### content/fr/about.md

Було:

```markdown
{{ site_name }} est un lieu public où les personnes qui construisent avec des outils d'IA montrent ce qu'elles ont réellement lancé. Au lieu d'affirmations, chaque projet porte des poinçons de preuve que nous vérifions nous-mêmes.

## Le problème {#problem}

Dire « je l'ai lancé » ne coûte rien. Une capture d'écran, un post de lancement ou une ligne sur un CV peuvent décrire n'importe quoi, et de l'extérieur personne ne peut savoir si le produit existe, qui le contrôle, ni s'il fonctionne encore un mois plus tard.

GitHub montre du code. LinkedIn montre des affirmations. {{ site_name }} essaie de montrer des résultats : un projet, les faits que nous avons pu vérifier à son sujet, et ce que son auteur a fait ensuite. L'essentiel ici, c'est le projet ; un profil n'est que la collection des projets de quelqu'un.

## Comment fonctionne la preuve {#proof}

Un projet peut obtenir trois poinçons. Chacun est un fait que notre serveur vérifie, et chacun disparaît dès que le fait n'est plus vrai.

- **Repo owner.** Le projet lie un dépôt GitHub public. Nous demandons à l’API publique de GitHub s’il appartient au compte GitHub personnel de l’auteur et n’est pas un fork ; pour les dépôts d’organisations et d’équipes, l’auteur ajoute à la place un fichier contenant le jeton de ce projet. Nous le recontrôlons chaque semaine.
- **Domain verified.** L'auteur prouve qu'il contrôle le domaine du projet avec un jeton que nous générons : un enregistrement TXT dans le DNS ou une balise meta sur la page d'accueil. Nous le revérifions régulièrement, et le poinçon ne tient que tant que le domaine a été confirmé au cours des 35 derniers jours.
- **Steady.** Dès qu'un projet a Domain verified, nous ouvrons son adresse environ toutes les 3 heures. Steady exige au moins 40 vérifications sur les 30 derniers jours, dont au moins 95 % doivent obtenir une réponse sans erreur en moins de 5 secondes.

Les règles complètes, y compris comment chaque poinçon peut être perdu, sont sur [Comment fonctionne la preuve](/how-proof-works/).
```

Стало:

```markdown
{{ site_name }} est un espace public où présenter des projets logiciels créés avec des outils d’IA. Les pages des projets rassemblent descriptions, captures d’écran, nouvelles du développement et marques de vérification.

## Ce que nous vérifions {#proof}

Nous vérifions la propriété ou l’accès en écriture à un dépôt GitHub public, le contrôle du domaine du projet et si le site répond. Les vérifications et leurs limites sont expliquées dans [Comment fonctionnent les preuves](/how-proof-works/).
```

Було:

```markdown
- **Qui a écrit le code.** {{ site_name }} contrôle les faits qu’il peut prouver : à qui appartient le dépôt GitHub lié, qui contrôle le domaine et si le site répond. Il ne contrôle pas, et ne peut pas contrôler, qui a écrit le code ni quelle part en a écrit un outil d’IA. L’historique des commits et ses dates sont écrits par le propriétaire du dépôt et peuvent être modifiés. Si vous pensez qu’un projet est copié, signalez-le.
- **Si le projet est bon.** Les poinçons ne sont pas des avis. Un projet Steady peut être une idée faible, et un excellent projet peut n'avoir encore aucun poinçon.
- **Ce que l'auteur écrit.** Le nom, la description, les captures, les tags, la date de lancement et les outils d'IA sous « Créé avec » sont indiqués par l'auteur. « Créé avec » est toujours marqué comme déclaré par l'auteur.

## Ce que vous obtenez {#builders}

- Un profil public qui rassemble vos projets. Vous vous connectez avec GitHub ; nous ne demandons que votre profil public et vos adresses e-mail, jamais l'accès à vos dépôts.
- Une page par projet avec ses poinçons, ses captures, une bande de disponibilité sur 30 jours (dès qu'il a Domain verified) et un journal de développement : de courtes mises à jour et des notes de lancement, dans l'ordre.
- Un badge pour votre README GitHub ou votre site, qui affiche les poinçons du projet à l'instant présent. Le code à coller se trouve sur la page du projet.
- Abonnements, j'aime, une page Pour vous avec les nouveaux lancements et les personnes que vous suivez, et une page « Découvrir » pour trouver des projets par tag, outil ou poinçon.
- La maîtrise de vos données : téléchargez-les toutes dans un fichier ou supprimez votre compte depuis les Réglages. Pas de publicité, pas d'analytique, pas de scripts de pistage.

## Qui est derrière {#who}

{{ site_name }} est construit et géré par une seule personne, Danylo Rudenko, développeur indépendant. Il est fait comme beaucoup de projets ici : avec des outils d'IA, surtout Claude Code, et une personne qui décide de ce qui est construit et vérifie le résultat.

**TODO (Danylo) :** confirme ce paragraphe et, si tu veux, ajoute une phrase sur toi (où tu es, pourquoi tu as commencé).

## La suite {#next}

Prévu après la première version, sans ordre fixe :

- une seule page Pour vous avec un filtre au lieu d'onglets séparés ;
- des avatars et plus de façons de personnaliser un profil ;
- des succès ;
- de meilleures vérifications des dépôts, par exemple pour les forks, et le lien entre un dépôt et son domaine ;
- ce que Domain verified doit signifier pour les projets qui ne sont pas des sites : outils en ligne de commande, bibliothèques, applications mobiles.

**TODO (Danylo) :** avant publication, vérifie que la liste correspond toujours à tes plans.
```

Стало:

```markdown
Ces vérifications ne déterminent pas qui a écrit le code, dans quelle mesure l’IA a été utilisée, ni la qualité ou la sécurité du projet. L’auteur fournit la description et la liste des outils d’IA.
```

Було:

```markdown
Questions, idées, un bug ou un projet qui ne devrait pas être ici : écrivez à [{{ contact_email }}](mailto:{{ contact_email }}). Vous pouvez aussi utiliser le lien « Signaler » sur n'importe quel projet ou profil.

**TODO avant le lancement :** cette adresse vient de `CONTACT_EMAIL` dans `config/branding.py` et reste provisoire.

```

Стало:

```markdown
Pour toute question ou demande d’aide, utilisez la page [Assistance](/support/) ou écrivez à [{{ contact_email }}](mailto:{{ contact_email }}).

```

### content/fr/community-rules.md

Було:

```markdown
*Brouillon. Ces règles font partie des [Conditions](/legal/terms/) et peuvent changer avant le lancement.*
```

Стало:

```markdown
Ces règles font partie des [Conditions](/legal/terms/).
```

Було:

```markdown
- Les nouveaux comptes peuvent publier 10 minutes après l’inscription. Pendant les 24 premières heures, un message peut contenir un lien et aucune image.
- Il y a des limites par heure (fils, réponses, votes, images) et le même texte ne peut pas être publié deux fois de suite.
- Il n’y a que des votes positifs. Vous ne pouvez pas voter pour votre propre message.
- Vous pouvez modifier votre message. Les modifications des 15 premières minutes sont discrètes ; les suivantes affichent la mention « modifié ». Le titre d’un fil ne peut être changé que pendant ces 15 premières minutes.
- Vous pouvez supprimer votre message. Si d’autres ont déjà répondu, leurs réponses restent et le vôtre s’affiche comme « [supprimé] ».
- Les autocollants sont notre propre collection. Les images sont vérifiées et réencodées, et leurs métadonnées (comme la position de l’appareil) sont supprimées.
```

Стало:

```markdown
- Les nouveaux comptes peuvent publier 10 minutes après l’inscription. Pendant les 24 premières heures, un message peut contenir un lien et aucune image.
- Il y a des limites par heure (fils, réponses, votes, images) et le même texte ne peut pas être publié deux fois de suite.
- Il n’y a que des votes positifs. Vous ne pouvez pas voter pour votre propre message.
- Vous pouvez modifier votre message. Les modifications des 15 premières minutes sont discrètes ; les suivantes affichent la mention « modifié ». Le titre d’un fil ne peut être changé que pendant ces 15 premières minutes.
- Vous pouvez supprimer votre message. Si d’autres ont déjà répondu, leurs réponses restent et le vôtre s’affiche comme « [supprimé] ».
- Les images sont vérifiées et réencodées, et leurs métadonnées (comme la position de l’appareil) sont supprimées.
```

### content/fr/cookies.md

Було:

```markdown
> **Brouillon**, dernière mise à jour le 12 novembre 2026. Ce texte n’a pas encore été relu par un juriste.
>
> Traduction fournie à titre indicatif ; la version anglaise prévaut.
```

Стало:

```markdown
Dernière mise à jour le 12 novembre 2026.

Traduction fournie à titre indicatif ; la version anglaise prévaut.
```

### content/fr/privacy.md

Було:

```markdown
> **Brouillon**, dernière mise à jour le 14 novembre 2026. Ce texte n’a pas encore été relu par un juriste.
>
> Traduction fournie à titre indicatif ; la version anglaise prévaut.
```

Стало:

```markdown
Dernière mise à jour le 14 novembre 2026.

Traduction fournie à titre indicatif ; la version anglaise prévaut.
```

Було:

```markdown
**Photo de profil et couverture.** Vous pouvez envoyer une photo et une image de couverture large, ou copier une fois votre image GitHub. Chaque image est réencodée (la photo en 512×512, la couverture en 1500×500), ce qui supprime les métadonnées cachées comme la position GPS, reçoit un nom de fichier aléatoire et est stockée sur notre propre serveur : les pages ne chargent jamais votre photo depuis GitHub. Les deux sont **publiques**. Quand vous en retirez ou remplacez une, ou supprimez votre compte, le fichier est supprimé ; des copies restent dans les sauvegardes jusqu’à 14 jours. Sans photo, vos initiales sont affichées.
```

Стало:

```markdown
**Photo de profil et couverture.** Vous pouvez envoyer une photo et une image de couverture large, ou copier une fois votre image GitHub. Chaque image est réencodée (la photo en 512×512, la couverture en 1500×500), ce qui supprime les métadonnées cachées comme la position GPS, reçoit un nom de fichier aléatoire et est stockée dans notre stockage : les pages ne chargent jamais votre photo depuis GitHub. Les deux sont **publiques**. Quand vous en retirez ou remplacez une, ou supprimez votre compte, le fichier est supprimé ; des copies restent dans les sauvegardes jusqu’à 14 jours. Sans photo, vos initiales sont affichées.
```

Було:

```markdown
- vos fils : rubrique, titre, texte, dates, et si un fil a été modifié, épinglé, verrouillé ou retiré ;
- vos réponses : texte, l’autocollant choisi, et le message auquel elles répondent ;
- les images que vous joignez. Elles sont réencodées comme les captures d’écran : les métadonnées cachées comme la position GPS sont supprimées, les noms de fichiers sont aléatoires, et nous gardons une copie jusqu’à 1600 px et une vignette de 640 px sur notre propre serveur.
```

Стало:

```markdown
- vos fils : rubrique, titre, texte, dates, et si un fil a été modifié, épinglé, verrouillé ou retiré ;
- vos réponses : texte et le message auquel elles répondent ;
- les images que vous joignez. Elles sont réencodées comme les captures d’écran : les métadonnées cachées comme la position GPS sont supprimées, les noms de fichiers sont aléatoires, et nous gardons une copie jusqu’à 1600 px et une vignette de 640 px dans notre stockage.
```

Було:

```markdown
Quand vous supprimez un message, son texte, son autocollant et ses images sont supprimés aussitôt. Le titre d’un fil reste tant que des réponses d’autres personnes se trouvent dessous, et s’affiche comme « [supprimé] ». Quand les modérateurs retirent un message, ses images sont supprimées aussitôt et son texte est conservé avec le motif, visible seulement par vous, les modérateurs et l’équipe. Les modérateurs voient les messages signalés avec l’historique de leur auteur, comme pour les autres signalements.
```

Стало:

```markdown
Quand vous supprimez un message, son texte et ses images sont supprimés aussitôt. Le titre d’un fil reste tant que des réponses d’autres personnes se trouvent dessous, et s’affiche comme « [supprimé] ». Quand les modérateurs retirent un message, ses images sont supprimées aussitôt et son texte est conservé avec le motif, visible seulement par vous, les modérateurs et l’équipe. Les modérateurs voient les messages signalés avec l’historique de leur auteur, comme pour les autres signalements.
```

Було:

```markdown
**Adresses IP et journaux.** L’application ne conserve pas votre adresse IP et ses propres journaux ne la contiennent pas. Pour chaque requête de page, les journaux notent seulement la méthode, l’adresse de la page (sans ce qui suit un `?`), le statut de la réponse, la taille et le temps de traitement, ainsi que les erreurs. Ils ne contiennent aucune information sur votre navigateur. Les adresses de page contiennent des noms d’utilisateur (`/u/<username>/`) : une ligne de journal peut donc montrer quel profil a été ouvert, mais pas par qui.
```

Стало:

```markdown
**Journaux de l’application.** Nos journaux applicatifs contiennent la méthode de requête, une route dont les données sont masquées, le statut, la taille et la durée de réponse, ainsi que des erreurs expurgées. Ils ne contiennent ni adresses IP, ni informations du navigateur, ni noms d’utilisateur, ni paramètres de requête, ni contenu de formulaires.
```

Було:

```markdown
> **TODO avant le lancement :** le serveur web placé devant l’application tient son propre journal d’accès, qui contient par défaut des adresses IP. Ce qu’il enregistre et combien de temps il le conserve (ainsi que la durée de conservation des journaux de l’application) n’est pas encore décidé. Il faut le compléter, ou désactiver l’enregistrement des IP, avant que cette page ne devienne publique.
```

Стало:

```markdown
Les journaux de routage de notre hébergeur web contiennent les adresses IP des visiteurs. Ces journaux et les journaux JSON stdout de l’application sont conservés dans le flux de journaux du fournisseur pendant une durée maximale d’environ une semaine. Seul le titulaire du compte d’hébergement peut lire ce flux. Les journaux de l’application ne contiennent ni adresses IP ni données personnelles. Au lancement, nous n’utilisons ni archive de journaux à long terme ni module de journalisation, et notre fournisseur DNS ne sert pas de proxy pour le trafic du site. Nous mettons cette politique à jour avant d’ajouter une archive de journaux ou d’activer un proxy de trafic.
```

Було:

```markdown
Quand vous nous écrivez via le [formulaire de support](/support/), nous conservons le sujet, l’objet, votre message, l’adresse e-mail indiquée (ou celle de votre compte), le compte avec lequel vous étiez connecté, le numéro de référence d’une page d’erreur si vous en venez, et jusqu’à 3 pièces jointes. Les images sont réencodées comme les autres (les métadonnées cachées comme la position GPS sont supprimées) ; les fichiers texte sont conservés en texte. Les pièces jointes sont stockées dans un dossier privé de notre serveur sans adresse publique : seule l’équipe ayant accès à la boîte du support peut les télécharger. Nous utilisons votre adresse e-mail uniquement pour vous répondre.

Nous ne conservons ni votre adresse IP ni les informations de votre navigateur avec le message. Pour arrêter le spam, une empreinte salée à sens unique de votre adresse IP est gardée dans le cache du serveur 24 heures au plus, jamais dans la base de données ni dans les journaux.
```

Стало:

```markdown
Quand vous nous écrivez via le [formulaire de support](/support/), nous conservons le sujet, l’objet, votre message, l’adresse e-mail indiquée (ou celle de votre compte), le compte avec lequel vous étiez connecté, le numéro de référence d’une page d’erreur si vous en venez, et jusqu’à 3 pièces jointes. Les images sont réencodées comme les autres (les métadonnées cachées comme la position GPS sont supprimées) ; les fichiers texte sont conservés en texte. Les pièces jointes sont stockées dans un stockage privé sans adresse publique : seule l’équipe ayant accès à la boîte du support peut les télécharger. Nous utilisons votre adresse e-mail uniquement pour vous répondre.

Nous ne conservons ni votre adresse IP ni les informations de votre navigateur avec le message. Pour limiter le spam, le cache du serveur contient des compteurs identifiés par un hachage salé à sens unique de votre adresse IP, jamais par l’adresse elle-même. En production, ce cache utilise la base de données. Un compteur s’applique pendant 24 heures au maximum. Les lignes expirées du cache peuvent rester dans la base jusqu’à leur suppression lors de la maintenance quotidienne. Le hachage n’est conservé ni avec le message d’assistance ni dans les journaux de l’application.
```

Було:

```markdown
- Votre compte, profil, projets, abonnements et mentions J’aime : jusqu’à ce que vous les supprimiez, ou que vous supprimiez votre compte.
- Messages au support et pièces jointes : clos, 12 mois après l’envoi ; les autres, jusqu’à leur clôture ; avec votre compte.
- Fils, réponses et images de la communauté : jusqu’à ce que vous les supprimiez ou supprimiez votre compte (ce qui reste est décrit plus haut, dans « Communauté »). Votes : jusqu’à ce que vous les retiriez ou supprimiez votre compte.
- Notifications de réponses : 90 jours.
- Photo de profil et couverture : jusqu’à ce que vous les retiriez ou remplaciez, ou supprimiez votre compte.
- Contrôles de disponibilité : 90 jours.
- Décisions de modération vous concernant (mises en sourdine, bannissements, projets retirés) et avis : tant que votre compte existe ; ils sont supprimés avec lui. Les signalements à votre sujet restent sans lien avec votre compte, avec seulement le nom affiché à l’époque.
- Empreinte de l’identifiant GitHub d’un compte banni : seulement jusqu’à la fin ou la levée du bannissement.
- Sessions de connexion : 2 semaines, ou jusqu’à la déconnexion.
- Signalements que vous avez faits : conservés après traitement. Si vous supprimez votre compte, ils restent sans votre nom.
- Journal d’audit : conservé. Les entrées concernant un compte supprimé ne contiennent ni le nom d’utilisateur ni l’e-mail.
- Compteurs de protection contre les abus : 24 heures au plus.
- Sauvegardes : 14 jours. Un compte supprimé en disparaît dans ce délai de 14 jours.
- Fichiers du journal des erreurs : jusqu’à ce qu’ils soient pleins (5 Mo plus 5 copies de 5 Mo), puis les entrées les plus anciennes sont supprimées.
- Journaux du serveur web et de l’application : **TODO**, pas encore décidé.
```

Стало:

```markdown
- Votre compte, profil, projets, abonnements et mentions J’aime : jusqu’à ce que vous les supprimiez, ou que vous supprimiez votre compte.
- Messages au support et pièces jointes : clos, 12 mois après l’envoi ; les autres, jusqu’à leur clôture ; avec votre compte.
- Fils, réponses et images de la communauté : jusqu’à ce que vous les supprimiez ou supprimiez votre compte (ce qui reste est décrit plus haut, dans « Communauté »). Votes : jusqu’à ce que vous les retiriez ou supprimiez votre compte.
- Notifications de réponses : 90 jours.
- Photo de profil et couverture : jusqu’à ce que vous les retiriez ou remplaciez, ou supprimiez votre compte.
- Contrôles de disponibilité : 90 jours.
- Décisions de modération vous concernant (mises en sourdine, bannissements, projets retirés) et avis : tant que votre compte existe ; ils sont supprimés avec lui. Les signalements à votre sujet restent sans lien avec votre compte, avec seulement le nom affiché à l’époque.
- Empreinte de l’identifiant GitHub d’un compte banni : seulement jusqu’à la fin ou la levée du bannissement.
- Sessions de connexion : 2 semaines, ou jusqu’à la déconnexion.
- Signalements que vous avez faits : conservés après traitement. Si vous supprimez votre compte, ils restent sans votre nom.
- Journal d’audit : conservé. Les entrées concernant un compte supprimé ne contiennent ni le nom d’utilisateur ni l’e-mail.
- Compteurs de protection contre les abus : 24 heures au plus.
- Sauvegardes : 14 jours. Un compte supprimé en disparaît dans ce délai de 14 jours.
- Fichiers du journal des erreurs : jusqu’à ce qu’ils soient pleins (5 Mo plus 5 copies de 5 Mo), puis les entrées les plus anciennes sont supprimées.
- Journaux de routage de l’hébergement et stdout de l’application : jusqu’à environ une semaine dans le flux de journaux de l’hébergeur ; aucune archive à long terme au lancement.
```

Було:

```markdown
- **GitHub, Inc.** Vous vous connectez sur github.com et notre serveur lit votre profil et les données publiques de dépôts depuis l’API de GitHub. La politique de confidentialité propre à GitHub s’applique à votre usage de GitHub.
- **Notre fournisseur de messagerie** (par exemple Google, si la boîte de l’équipe est un compte Gmail) achemine vers la boîte de l’équipe l’avis de chaque message au support, avec son texte et votre adresse e-mail.
- **Les serveurs de votre projet.** Pour les contrôles Domain verified et Steady, notre serveur contacte le DNS de votre domaine et l’adresse de votre projet. Ils voient notre serveur, pas vous.
- **Notre hébergeur**, qui exploite pour nous le serveur et la base de données.
```

Стало:

```markdown
- **Les prestataires d’hébergement web et de base de données gérée** exploitent l’application et conservent ses enregistrements pour nous.
- **Le stockage d’objets compatible S3** conserve les images téléversées et les pièces jointes privées d’assistance pour notre compte.
- **GitHub** assure la connexion et fournit les données de profil et de dépôts publics utilisées par nos vérifications. Sa propre politique de confidentialité s’applique à votre utilisation de GitHub.
- **Un service de messagerie** transmet à la boîte de notre équipe les notifications d’assistance, avec le message et l’adresse e-mail de l’expéditeur.
- **Les serveurs DNS et web de votre projet** reçoivent nos requêtes de vérification. Ils voient l’adresse de notre serveur, pas celle du visiteur.
```

### content/fr/terms.md

Було:

```markdown
> **Brouillon**, dernière mise à jour le 14 novembre 2026 (version {{ terms_version }}). Ce texte n’a pas encore été relu par un juriste.
>
> Traduction fournie à titre indicatif ; la version anglaise prévaut.
```

Стало:

```markdown
Dernière mise à jour le 14 novembre 2026 (version {{ terms_version }}).

Traduction fournie à titre indicatif ; la version anglaise prévaut.
```

### content/pl/about.md

Було:

```markdown
{{ site_name }} to publiczne miejsce, w którym osoby budujące z narzędziami AI pokazują to, co naprawdę wypuściły. Zamiast deklaracji każdy projekt ma znaki potwierdzenia, które sprawdzamy sami.

## Problem {#problem}

Powiedzieć „wypuściłem to” nic nie kosztuje. Zrzut ekranu, post o premierze czy linijka w CV mogą opisać cokolwiek, a z zewnątrz nie da się stwierdzić, czy produkt istnieje, kto nim zarządza i czy działa jeszcze miesiąc później.

GitHub pokazuje kod. LinkedIn pokazuje deklaracje. {{ site_name }} próbuje pokazać efekty: projekt, fakty o nim, które udało się sprawdzić, i to, co jego twórca zrobił dalej. Najważniejszy jest tu projekt; profil to po prostu zbiór czyichś projektów.

## Jak działa dowód {#proof}

Projekt może zdobyć trzy znaki. Każdy z nich to fakt sprawdzany przez nasz serwer i każdy znika, gdy fakt przestaje być prawdziwy.

- **Repo owner.** Projekt wskazuje publiczne repozytorium GitHub. Pytamy publiczne API GitHuba, czy należy ono do osobistego konta GitHub autora i nie jest forkiem; w repozytoriach organizacji i zespołów autor zamiast tego dodaje plik z tokenem tego projektu. Sprawdzamy to ponownie co tydzień.
- **Domain verified.** Autor udowadnia, że kontroluje domenę projektu, za pomocą wygenerowanego przez nas tokenu: rekordu TXT w DNS albo metatagu na stronie głównej. Regularnie sprawdzamy to ponownie, a znak obowiązuje tylko, dopóki domena była potwierdzona w ciągu ostatnich 35 dni.
- **Steady.** Gdy projekt ma Domain verified, otwieramy jego adres mniej więcej co 3 godziny. Steady wymaga co najmniej 40 sprawdzeń w ostatnich 30 dniach, z których co najmniej 95% musi dostać odpowiedź bez błędu w ciągu 5 sekund.

Pełne zasady, w tym to, jak można stracić każdy znak, są na stronie [Jak działa dowód](/how-proof-works/).
```

Стало:

```markdown
{{ site_name }} to publiczne miejsce do prezentowania projektów oprogramowania tworzonych z narzędziami AI. Strony projektów łączą opisy, zrzuty ekranu, aktualizacje z prac i oznaczenia potwierdzonych faktów.

## Co sprawdzamy {#proof}

Sprawdzamy własność publicznego repozytorium GitHub lub prawo zapisu w nim, kontrolę nad domeną projektu i to, czy witryna odpowiada. Kontrole i ich ograniczenia opisuje strona [Jak działają potwierdzenia](/how-proof-works/).
```

Було:

```markdown
- **Kto napisał kod.** {{ site_name }} sprawdza fakty, które da się udowodnić: do kogo należy połączone repozytorium GitHub, kto kontroluje domenę i czy strona odpowiada. Nie sprawdza i nie może sprawdzić, kto napisał kod ani ile napisało go narzędzie AI. Historię commitów i ich daty zapisuje właściciel repozytorium i można je zmienić. Jeśli uważasz, że projekt jest skopiowany, zgłoś go.
- **Czy projekt jest dobry.** Znaki to nie recenzje. Projekt ze znakiem Steady może być słabym pomysłem, a świetny projekt może jeszcze nie mieć żadnego znaku.
- **Co pisze autor.** Nazwę, opis, zrzuty ekranu, tagi, datę premiery i narzędzia AI w sekcji „Zbudowano z” podaje autor. „Zbudowano z” jest zawsze oznaczone jako deklaracja autora.

## Co dostają twórcy {#builders}

- Publiczny profil, który zbiera Twoje projekty. Logujesz się przez GitHub; prosimy tylko o publiczny profil i adresy e-mail, nigdy o dostęp do repozytoriów.
- Stronę każdego projektu ze znakami, zrzutami ekranu, 30-dniowym paskiem dostępności (gdy projekt ma Domain verified) i dziennikiem rozwoju: krótkimi aktualizacjami i notatkami o premierze, po kolei.
- Plakietkę do README na GitHubie lub na stronę, która pokazuje znaki, jakie projekt ma w tej chwili. Kod do wklejenia jest na stronie projektu.
- Obserwowanie, polubienia, stronę Dla Ciebie z nowymi premierami i osobami, które obserwujesz, oraz stronę „Odkrywaj”, gdzie projekty można szukać po tagu, narzędziu lub znaku.
- Kontrolę nad danymi: pobierz je wszystkie jako plik albo usuń konto w Ustawieniach. Bez reklam, bez analityki, bez skryptów śledzących.

## Kto za tym stoi {#who}

{{ site_name }} tworzy i prowadzi jedna osoba, Danylo Rudenko, samodzielny twórca. Powstaje tak, jak wiele projektów tutaj: z narzędziami AI, głównie Claude Code, a o tym, co budować i czy wynik jest dobry, decyduje jedna osoba.

**TODO (Danylo):** potwierdź ten akapit i, jeśli chcesz, dodaj zdanie o sobie (skąd jesteś, dlaczego zacząłeś).

## Co dalej {#next}

Zaplanowane po pierwszej wersji, bez ustalonej kolejności:

- jedna strona Dla Ciebie z filtrem zamiast osobnych kart;
- awatary i więcej możliwości dopasowania profilu;
- osiągnięcia;
- lepsze sprawdzanie repozytoriów, na przykład forków, oraz powiązanie repozytorium z domeną;
- co ma znaczyć Domain verified dla projektów, które nie są stronami: narzędzi wiersza poleceń, bibliotek, aplikacji mobilnych.

**TODO (Danylo):** przed publikacją sprawdź, czy lista nadal zgadza się z planami.
```

Стало:

```markdown
Te kontrole nie ustalają, kto napisał kod, w jakim stopniu użyto AI ani jaka jest jakość lub bezpieczeństwo projektu. Opis i listę narzędzi AI podaje autor.
```

Було:

```markdown
Pytania, pomysły, błąd albo projekt, którego nie powinno tu być: napisz na [{{ contact_email }}](mailto:{{ contact_email }}). Możesz też użyć linku „Zgłoś” na stronie każdego projektu lub profilu.

**TODO przed startem:** ten adres pochodzi z `CONTACT_EMAIL` w `config/branding.py` i nadal jest tymczasowy.

```

Стало:

```markdown
Z pytaniami lub prośbą o pomoc skorzystaj ze strony [Pomoc](/support/) albo napisz na [{{ contact_email }}](mailto:{{ contact_email }}).

```

### content/pl/community-rules.md

Було:

```markdown
*Wersja robocza. Te zasady są częścią [Regulaminu](/legal/terms/) i mogą się zmienić przed startem.*
```

Стало:

```markdown
Te zasady są częścią [Regulaminu](/legal/terms/).
```

Було:

```markdown
- Nowe konta mogą pisać 10 minut po rejestracji. Przez pierwsze 24 godziny post może zawierać jeden link i żadnego obrazu.
- Obowiązują limity na godzinę (wątki, odpowiedzi, głosy, obrazy), a tego samego tekstu nie można opublikować dwa razy z rzędu.
- Są tylko głosy za. Nie możesz głosować na własny post.
- Możesz edytować swój post. Zmiany w pierwszych 15 minutach są niewidoczne; późniejsze dostają oznaczenie „edytowano”. Tytuł wątku można zmienić tylko w tych pierwszych 15 minutach.
- Możesz usunąć swój post. Jeśli ktoś już odpowiedział, odpowiedzi zostają, a Twój post jest widoczny jako „[usunięto]”.
- Naklejki to nasz własny zestaw. Obrazy są sprawdzane i kodowane na nowo, a ich metadane (np. lokalizacja aparatu) są usuwane.
```

Стало:

```markdown
- Nowe konta mogą pisać 10 minut po rejestracji. Przez pierwsze 24 godziny post może zawierać jeden link i żadnego obrazu.
- Obowiązują limity na godzinę (wątki, odpowiedzi, głosy, obrazy), a tego samego tekstu nie można opublikować dwa razy z rzędu.
- Są tylko głosy za. Nie możesz głosować na własny post.
- Możesz edytować swój post. Zmiany w pierwszych 15 minutach są niewidoczne; późniejsze dostają oznaczenie „edytowano”. Tytuł wątku można zmienić tylko w tych pierwszych 15 minutach.
- Możesz usunąć swój post. Jeśli ktoś już odpowiedział, odpowiedzi zostają, a Twój post jest widoczny jako „[usunięto]”.
- Obrazy są sprawdzane i kodowane na nowo, a ich metadane (np. lokalizacja aparatu) są usuwane.
```

### content/pl/cookies.md

Було:

```markdown
> **Wersja robocza**, ostatnia aktualizacja: 12 listopada 2026. Ten tekst nie został jeszcze sprawdzony przez prawnika.
>
> Tłumaczenie dla wygody; obowiązuje wersja angielska.
```

Стало:

```markdown
Ostatnia aktualizacja: 12 listopada 2026.

Tłumaczenie dla wygody; obowiązuje wersja angielska.
```

### content/pl/privacy.md

Було:

```markdown
> **Wersja robocza**, ostatnia aktualizacja: 14 listopada 2026. Ten tekst nie został jeszcze sprawdzony przez prawnika.
>
> Tłumaczenie dla wygody; obowiązuje wersja angielska.
```

Стало:

```markdown
Ostatnia aktualizacja: 14 listopada 2026.

Tłumaczenie dla wygody; obowiązuje wersja angielska.
```

Було:

```markdown
**Zdjęcie profilowe i obraz w tle.** Możesz wysłać zdjęcie i szeroki obraz w tle albo raz skopiować swój obraz z GitHuba. Każdy obraz kodujemy na nowo (zdjęcie do 512×512, obraz w tle do 1500×500), co usuwa ukryte metadane, np. lokalizację GPS, nadajemy mu losową nazwę i przechowujemy na własnym serwerze: strony nigdy nie wczytują Twojego zdjęcia z GitHuba. Oba są **publiczne**. Gdy usuniesz lub zastąpisz obraz albo usuniesz konto, plik jest usuwany; kopie zostają w kopiach zapasowych do 14 dni. Bez zdjęcia pokazujemy Twoje inicjały.
```

Стало:

```markdown
**Zdjęcie profilowe i obraz w tle.** Możesz wysłać zdjęcie i szeroki obraz w tle albo raz skopiować swój obraz z GitHuba. Każdy obraz kodujemy na nowo (zdjęcie do 512×512, obraz w tle do 1500×500), co usuwa ukryte metadane, np. lokalizację GPS, nadajemy mu losową nazwę i przechowujemy w naszym magazynie: strony nigdy nie wczytują Twojego zdjęcia z GitHuba. Oba są **publiczne**. Gdy usuniesz lub zastąpisz obraz albo usuniesz konto, plik jest usuwany; kopie zostają w kopiach zapasowych do 14 dni. Bez zdjęcia pokazujemy Twoje inicjały.
```

Було:

```markdown
- Twoje wątki: dział, tytuł, tekst, daty oraz to, czy wątek był edytowany, przypięty, zamknięty lub usunięty;
- Twoje odpowiedzi: tekst, wybraną naklejkę i to, na który wpis odpowiadają;
- dołączone obrazy. Są ponownie kodowane jak zrzuty ekranu: ukryte metadane, takie jak lokalizacja GPS, są usuwane, nazwy plików są losowe, a na naszym serwerze trzymamy kopię do 1600 px i miniaturę 640 px.
```

Стало:

```markdown
- Twoje wątki: dział, tytuł, tekst, daty oraz to, czy wątek był edytowany, przypięty, zamknięty lub usunięty;
- Twoje odpowiedzi: tekst i to, na który wpis odpowiadają;
- dołączone obrazy. Są ponownie kodowane jak zrzuty ekranu: ukryte metadane, takie jak lokalizacja GPS, są usuwane, nazwy plików są losowe, a w naszym magazynie przechowujemy kopię do 1600 px i miniaturę 640 px.
```

Було:

```markdown
Gdy usuwasz wpis, jego tekst, naklejka i obrazy są usuwane od razu. Tytuł wątku zostaje, dopóki są pod nim odpowiedzi innych osób, i jest pokazywany jako „[usunięto]”. Gdy wpis usuwają moderatorzy, jego obrazy są usuwane od razu, a tekst zostaje zachowany z powodem i widzisz go tylko Ty, moderatorzy i zespół. Moderatorzy widzą zgłoszone wpisy razem z historią autora, tak jak przy innych zgłoszeniach.
```

Стало:

```markdown
Gdy usuwasz wpis, jego tekst i obrazy są usuwane od razu. Tytuł wątku zostaje, dopóki są pod nim odpowiedzi innych osób, i jest pokazywany jako „[usunięto]”. Gdy wpis usuwają moderatorzy, jego obrazy są usuwane od razu, a tekst zostaje zachowany z powodem i widzisz go tylko Ty, moderatorzy i zespół. Moderatorzy widzą zgłoszone wpisy razem z historią autora, tak jak przy innych zgłoszeniach.
```

Було:

```markdown
**Adresy IP i dzienniki.** Aplikacja nie zapisuje Twojego adresu IP, a jej własne dzienniki go nie zawierają. Przy każdym żądaniu strony dzienniki zapisują tylko metodę, adres strony (bez tego, co następuje po `?`), status odpowiedzi, rozmiar i czas obsługi oraz błędy. Nie ma w nich danych o Twojej przeglądarce. Adresy stron zawierają nazwy użytkowników (`/u/<username>/`), więc wiersz dziennika może pokazać, który profil otwarto, ale nie kto to zrobił.
```

Стало:

```markdown
**Dzienniki aplikacji.** Dzienniki naszej aplikacji zawierają metodę żądania, trasę z ukrytymi danymi, status odpowiedzi, rozmiar i czas wykonania oraz oczyszczone komunikaty błędów. Nie zawierają adresów IP, danych przeglądarki, nazw użytkowników, parametrów zapytań ani treści formularzy.
```

Було:

```markdown
> **TODO przed uruchomieniem:** serwer WWW przed aplikacją prowadzi własny dziennik dostępu, który domyślnie zawiera adresy IP. Co dokładnie zapisuje i jak długo to przechowuje (oraz jak długo przechowywane są dzienniki aplikacji), nie zostało jeszcze ustalone. Trzeba to uzupełnić albo wyłączyć zapisywanie IP, zanim ta strona stanie się publiczna.
```

Стало:

```markdown
Dzienniki routingu naszego dostawcy hostingu zawierają adresy IP odwiedzających. Dzienniki routingu i dzienniki JSON stdout aplikacji są przechowywane w strumieniu dzienników dostawcy przez okres do około tygodnia. Dostęp do tego strumienia ma tylko właściciel konta hostingowego. Dzienniki aplikacji nie zawierają adresów IP ani danych osobowych. Przy uruchomieniu nie korzystamy z długoterminowego archiwum ani dodatku do dzienników, a dostawca DNS nie pośredniczy w ruchu witryny jako proxy. Przed dodaniem archiwum lub włączeniem proxy ruchu aktualizujemy tę politykę.
```

Було:

```markdown
Gdy piszesz do nas przez [formularz wsparcia](/support/), zapisujemy temat, tytuł, Twoją wiadomość, podany adres e-mail (lub adres konta), konto, z którego pisałeś, numer strony błędu, jeśli z niej przyszedłeś, oraz do 3 załączników. Obrazy są kodowane na nowo jak inne zdjęcia (ukryte metadane, np. lokalizacja GPS, są usuwane); pliki tekstowe są przechowywane jako tekst. Załączniki leżą w prywatnym folderze na naszym serwerze, który nie ma publicznego adresu: pobrać je może tylko personel z dostępem do skrzynki wsparcia. Twojego adresu e-mail używamy tylko do odpowiedzi.

Nie zapisujemy razem z wiadomością Twojego adresu IP ani danych przeglądarki. Aby powstrzymać spam, solony jednokierunkowy odcisk Twojego adresu IP jest trzymany w pamięci podręcznej serwera najwyżej 24 godziny, nigdy w bazie danych ani w logach.
```

Стало:

```markdown
Gdy piszesz do nas przez [formularz wsparcia](/support/), zapisujemy temat, tytuł, Twoją wiadomość, podany adres e-mail (lub adres konta), konto, z którego pisałeś, numer strony błędu, jeśli z niej przyszedłeś, oraz do 3 załączników. Obrazy są kodowane na nowo jak inne zdjęcia (ukryte metadane, np. lokalizacja GPS, są usuwane); pliki tekstowe są przechowywane jako tekst. Załączniki leżą w prywatnym magazynie, który nie ma publicznego adresu: pobrać je może tylko personel z dostępem do skrzynki wsparcia. Twojego adresu e-mail używamy tylko do odpowiedzi.

Nie zapisujemy adresu IP ani danych przeglądarki razem z wiadomością. Aby ograniczać spam, pamięć podręczna serwera przechowuje liczniki identyfikowane przez solony jednokierunkowy skrót adresu IP, nigdy przez sam adres. W środowisku produkcyjnym ta pamięć podręczna korzysta z bazy danych. Licznik obowiązuje najwyżej przez 24 godziny. Wygasłe wiersze pamięci podręcznej mogą pozostać w bazie do usunięcia podczas codziennej konserwacji. Skrót nie jest zapisywany z wiadomością do pomocy ani w dziennikach aplikacji.
```

Було:

```markdown
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
```

Стало:

```markdown
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
- Dzienniki routingu hostingu i stdout aplikacji: do około tygodnia w strumieniu dzienników hostingu; bez długoterminowego archiwum przy uruchomieniu.
```

Було:

```markdown
- **GitHub, Inc.** Logujesz się na github.com, a nasz serwer odczytuje Twój profil i publiczne dane repozytoriów z API GitHuba. Do korzystania z GitHuba stosuje się jego własne oświadczenie o prywatności.
- **Nasz dostawca poczty** (np. Google, jeśli skrzynka zespołu to Gmail) dostarcza na skrzynkę zespołu powiadomienie o każdej wiadomości do wsparcia, z jej treścią i Twoim adresem e-mail.
- **Serwery Twojego projektu.** Przy sprawdzeniach Domain verified i Steady nasz serwer łączy się z DNS Twojej domeny i z adresem Twojego projektu. Widzą nasz serwer, nie Ciebie.
- **Nasz dostawca hostingu**, który prowadzi dla nas serwer i bazę danych.

Nie sprzedajemy Twoich danych i nie udostępniamy ich do celów reklamowych.
```

Стало:

```markdown
- **Dostawcy hostingu i zarządzanej bazy danych** obsługują aplikację i przechowują jej rekordy w naszym imieniu.
- **Magazyn obiektowy zgodny z S3** przechowuje przesłane obrazy i prywatne załączniki pomocy w naszym imieniu.
- **GitHub** zapewnia logowanie oraz dane profilu i publicznych repozytoriów do naszych kontroli. Korzystanie z GitHuba podlega jego własnej polityce prywatności.
- **Usługa pocztowa** dostarcza do skrzynki zespołu powiadomienia pomocy zawierające wiadomość i adres email nadawcy.
- **Serwery DNS i WWW Twojego projektu** otrzymują nasze żądania weryfikacyjne. Widzą adres naszego serwera, a nie odwiedzającego.

Nie sprzedajemy Twoich danych ani nie udostępniamy ich do celów reklamowych.
```

### content/pl/terms.md

Було:

```markdown
> **Wersja robocza**, ostatnia aktualizacja: 14 listopada 2026 (wersja {{ terms_version }}). Ten tekst nie został jeszcze sprawdzony przez prawnika.
>
> Tłumaczenie dla wygody; obowiązuje wersja angielska.
```

Стало:

```markdown
Ostatnia aktualizacja: 14 listopada 2026 (wersja {{ terms_version }}).

Tłumaczenie dla wygody; obowiązuje wersja angielska.
```

### content/pt-br/about.md

Було:

```markdown
O {{ site_name }} é um lugar público onde quem constrói com ferramentas de IA mostra o que realmente lançou. Em vez de afirmações, cada projeto traz selos de comprovação que nós mesmos verificamos.

## O problema {#problem}

Dizer "eu lancei" não custa nada. Uma captura de tela, um post de lançamento ou uma linha no currículo podem descrever qualquer coisa, e de fora ninguém sabe se o produto existe, quem o controla ou se ainda funciona um mês depois.

O GitHub mostra código. O LinkedIn mostra afirmações. O {{ site_name }} tenta mostrar resultados: um projeto, os fatos que conseguimos verificar sobre ele e o que a pessoa fez depois. O principal aqui é o projeto; um perfil é só a coleção de projetos de alguém.

## Como funciona a comprovação {#proof}

Um projeto pode ganhar três selos. Cada um é um fato que o nosso servidor verifica, e cada um desaparece quando o fato deixa de ser verdade.

- **Repo owner.** O projeto vincula um repositório público do GitHub. Perguntamos à API pública do GitHub se ele pertence à conta pessoal do GitHub do autor e não é um fork; em repositórios de organizações e equipes, o autor adiciona em vez disso um arquivo com o token deste projeto. Verificamos de novo toda semana.
- **Domain verified.** O autor prova que controla o domínio do projeto com um token que geramos: um registro TXT no DNS ou uma meta tag na página inicial. Verificamos de novo regularmente, e o selo só vale enquanto o domínio tiver sido confirmado nos últimos 35 dias.
- **Steady.** Quando um projeto tem Domain verified, abrimos o endereço dele mais ou menos a cada 3 horas. Steady exige pelo menos 40 verificações nos últimos 30 dias, e pelo menos 95% delas precisam receber resposta sem erro em até 5 segundos.

As regras completas, incluindo como cada selo pode ser perdido, estão em [Como funciona a comprovação](/how-proof-works/).
```

Стало:

```markdown
O {{ site_name }} é um espaço público para apresentar projetos de software criados com ferramentas de IA. As páginas dos projetos reúnem descrições, capturas de tela, atualizações do desenvolvimento e marcas de verificação.

## O que verificamos {#proof}

Verificamos a propriedade ou o acesso de escrita a um repositório público do GitHub, o controle do domínio do projeto e se o site responde. As verificações e seus limites são explicados em [Como funcionam as provas](/how-proof-works/).
```

Було:

```markdown
- **Quem escreveu o código.** O {{ site_name }} verifica fatos que consegue provar: a quem pertence o repositório do GitHub vinculado, quem controla o domínio e se o site responde. Ele não verifica, nem pode verificar, quem escreveu o código ou quanto dele foi escrito por uma ferramenta de IA. O histórico de commits e as datas são escritos pelo dono do repositório e podem ser alterados. Se você acha que um projeto foi copiado, denuncie.
- **Se o projeto é bom.** Selos não são avaliações. Um projeto Steady ainda pode ser uma ideia fraca, e um ótimo projeto pode ainda não ter nenhum selo.
- **O que o autor escreve.** Nome, descrição, capturas de tela, tags, data de lançamento e as ferramentas de IA em "Feito com" são informados pelo autor. "Feito com" sempre aparece como declarado pelo autor.

## O que você ganha {#builders}

- Um perfil público que reúne seus projetos. Você entra com o GitHub; pedimos só o seu perfil público e seus endereços de e-mail, nunca acesso aos seus repositórios.
- Uma página para cada projeto com seus selos, capturas de tela, uma faixa de disponibilidade de 30 dias (quando tem Domain verified) e um diário de desenvolvimento: atualizações curtas e notas de lançamento, em ordem.
- Um badge para o README do GitHub ou para o seu site que mostra os selos que o projeto tem agora. O código para colar está na página do projeto.
- Seguir, curtidas, uma página Para você com novos lançamentos e com as pessoas que você segue, e uma página "Descobrir" para encontrar projetos por tag, ferramenta ou selo.
- Controle sobre seus dados: baixe tudo em um arquivo ou exclua sua conta em Configurações. Sem anúncios, sem analytics, sem scripts de rastreamento.

## Quem está por trás {#who}

O {{ site_name }} é construído e mantido por uma pessoa, Danylo Rudenko, desenvolvedor solo. Ele é feito do mesmo jeito que muitos projetos daqui: com ferramentas de IA, principalmente o Claude Code, e uma pessoa decide o que construir e se o resultado está bom.

**TODO (Danylo):** confirme este parágrafo e, se quiser, acrescente uma frase sobre você (onde está, por que começou).

## O que vem depois {#next}

Planejado depois da primeira versão, sem ordem definida:

- uma única página Para você com filtro, em vez de abas separadas;
- avatares e mais formas de personalizar um perfil;
- conquistas;
- verificações melhores de repositórios, por exemplo com forks, e ligar um repositório ao seu domínio;
- o que Domain verified deve significar para projetos que não são sites: ferramentas de linha de comando, bibliotecas, apps móveis.

**TODO (Danylo):** antes de publicar, confira se a lista ainda corresponde aos seus planos.
```

Стало:

```markdown
Essas verificações não determinam quem escreveu o código, quanto a IA foi usada nem a qualidade ou a segurança do projeto. O autor fornece a descrição e a lista de ferramentas de IA.
```

Було:

```markdown
Dúvidas, ideias, um bug ou um projeto que não deveria estar aqui: escreva para [{{ contact_email }}](mailto:{{ contact_email }}). Você também pode usar o link "Denunciar" em qualquer projeto ou perfil.

**TODO antes do lançamento:** este endereço vem de `CONTACT_EMAIL` em `config/branding.py` e ainda é provisório.

```

Стало:

```markdown
Para dúvidas ou ajuda, use a página de [Suporte](/support/) ou escreva para [{{ contact_email }}](mailto:{{ contact_email }}).

```

### content/pt-br/community-rules.md

Було:

```markdown
*Rascunho. Estas regras fazem parte dos [Termos](/legal/terms/) e podem mudar antes do lançamento.*
```

Стало:

```markdown
Estas regras fazem parte dos [Termos](/legal/terms/).
```

Було:

```markdown
- Contas novas podem publicar 10 minutos depois do cadastro. Nas primeiras 24 horas, uma publicação pode ter um link e nenhuma imagem.
- Há limites por hora (tópicos, respostas, votos, imagens) e o mesmo texto não pode ser publicado duas vezes seguidas.
- Só existem votos a favor. Você não pode votar na sua própria publicação.
- Você pode editar sua publicação. Mudanças nos primeiros 15 minutos não aparecem; as posteriores mostram a marca “editado”. O título de um tópico só pode ser alterado nesses primeiros 15 minutos.
- Você pode excluir sua publicação. Se outras pessoas já responderam, as respostas delas ficam e a sua aparece como “[excluído]”.
- As figurinhas são um conjunto próprio. As imagens são verificadas e recodificadas, e os metadados delas (como a localização da câmera) são removidos.
```

Стало:

```markdown
- Contas novas podem publicar 10 minutos depois do cadastro. Nas primeiras 24 horas, uma publicação pode ter um link e nenhuma imagem.
- Há limites por hora (tópicos, respostas, votos, imagens) e o mesmo texto não pode ser publicado duas vezes seguidas.
- Só existem votos a favor. Você não pode votar na sua própria publicação.
- Você pode editar sua publicação. Mudanças nos primeiros 15 minutos não aparecem; as posteriores mostram a marca “editado”. O título de um tópico só pode ser alterado nesses primeiros 15 minutos.
- Você pode excluir sua publicação. Se outras pessoas já responderam, as respostas delas ficam e a sua aparece como “[excluído]”.
- As imagens são verificadas e recodificadas, e os metadados delas (como a localização da câmera) são removidos.
```

### content/pt-br/cookies.md

Було:

```markdown
> **Rascunho**, última atualização em 12 de novembro de 2026. Este texto ainda não foi revisado por um advogado.
>
> Tradução por conveniência; a versão em inglês prevalece.
```

Стало:

```markdown
Última atualização em 12 de novembro de 2026.

Tradução por conveniência; a versão em inglês prevalece.
```

### content/pt-br/privacy.md

Було:

```markdown
> **Rascunho**, última atualização em 14 de novembro de 2026. Este texto ainda não foi revisado por um advogado.
>
> Tradução por conveniência; a versão em inglês prevalece.
```

Стало:

```markdown
Última atualização em 14 de novembro de 2026.

Tradução por conveniência; a versão em inglês prevalece.
```

Було:

```markdown
**Foto de perfil e capa.** Você pode enviar uma foto e uma imagem de capa larga, ou copiar uma vez sua imagem do GitHub. Cada imagem é recodificada (a foto em 512×512, a capa em 1500×500), o que remove metadados ocultos como a localização GPS, recebe um nome de arquivo aleatório e é guardada no nosso próprio servidor: as páginas nunca carregam sua foto do GitHub. As duas são **públicas**. Quando você remove ou substitui uma delas, ou exclui sua conta, o arquivo é apagado; cópias ficam nos backups por até 14 dias. Sem foto, mostramos suas iniciais.
```

Стало:

```markdown
**Foto de perfil e capa.** Você pode enviar uma foto e uma imagem de capa larga, ou copiar uma vez sua imagem do GitHub. Cada imagem é recodificada (a foto em 512×512, a capa em 1500×500), o que remove metadados ocultos como a localização GPS, recebe um nome de arquivo aleatório e é guardada em nosso armazenamento: as páginas nunca carregam sua foto do GitHub. As duas são **públicas**. Quando você remove ou substitui uma delas, ou exclui sua conta, o arquivo é apagado; cópias ficam nos backups por até 14 dias. Sem foto, mostramos suas iniciais.
```

Було:

```markdown
- seus tópicos: seção, título, texto, datas e se um tópico foi editado, fixado, trancado ou removido;
- suas respostas: texto, a figurinha que você escolheu e a qual publicação elas respondem;
- as imagens que você anexa. Elas são recodificadas como as capturas de tela: metadados ocultos, como a localização GPS, são removidos, os nomes dos arquivos são aleatórios e guardamos uma cópia de até 1600 px e uma miniatura de 640 px no nosso próprio servidor.
```

Стало:

```markdown
- seus tópicos: seção, título, texto, datas e se um tópico foi editado, fixado, trancado ou removido;
- suas respostas: texto e a qual publicação elas respondem;
- as imagens que você anexa. Elas são recodificadas como as capturas de tela: metadados ocultos, como a localização GPS, são removidos, os nomes dos arquivos são aleatórios e guardamos uma cópia de até 1600 px e uma miniatura de 640 px em nosso armazenamento.
```

Було:

```markdown
Quando você exclui uma publicação, o texto, a figurinha e as imagens são apagados na hora. O título de um tópico fica enquanto houver respostas de outras pessoas embaixo dele, mostrado como “[excluído]”. Quando os moderadores removem uma publicação, as imagens são apagadas na hora e o texto é guardado com o motivo, visível só para você, os moderadores e a equipe. Os moderadores veem as publicações denunciadas junto com o histórico do autor, como nas outras denúncias.
```

Стало:

```markdown
Quando você exclui uma publicação, o texto e as imagens são apagados na hora. O título de um tópico fica enquanto houver respostas de outras pessoas embaixo dele, mostrado como “[excluído]”. Quando os moderadores removem uma publicação, as imagens são apagadas na hora e o texto é guardado com o motivo, visível só para você, os moderadores e a equipe. Os moderadores veem as publicações denunciadas junto com o histórico do autor, como nas outras denúncias.
```

Було:

```markdown
**Endereços IP e registros.** O aplicativo não guarda seu endereço IP, e os registros dele não o contêm. De cada requisição de página, os registros anotam apenas o método, o endereço da página (sem o que vem depois de um `?`), o status da resposta, o tamanho e o tempo gasto, além dos erros. Não há dados do seu navegador. Os endereços de página incluem nomes de usuário (`/u/<username>/`), então uma linha de registro pode mostrar qual perfil foi aberto, mas não por quem.
```

Стало:

```markdown
**Registros do aplicativo.** Os registros do nosso aplicativo contêm o método da solicitação, uma rota com dados ocultos, o status, tamanho e duração da resposta e erros sanitizados. Não contêm endereços IP, dados do navegador, nomes de usuário, parâmetros de consulta nem conteúdo de formulários.
```

Було:

```markdown
> **TODO antes do lançamento:** o servidor web na frente do aplicativo mantém seu próprio registro de acessos, que por padrão inclui endereços IP. O que ele registra e por quanto tempo guarda (e por quanto tempo os registros do aplicativo são guardados) ainda não foi decidido. É preciso preencher isso, ou desativar o registro de IP, antes de esta página se tornar pública.
```

Стало:

```markdown
Os registros de roteamento do nosso provedor de hospedagem web incluem os endereços IP dos visitantes. Esses registros e os registros JSON de stdout do aplicativo são mantidos no fluxo de registros do provedor por até aproximadamente uma semana. Somente o titular da conta de hospedagem pode ler esse fluxo. Os registros do aplicativo não incluem endereços IP nem dados pessoais. No lançamento, não usamos arquivo de registros de longo prazo nem complemento de registros, e nosso provedor de DNS não atua como proxy do tráfego do site. Atualizamos esta política antes de adicionar um arquivo de registros ou ativar um proxy de tráfego.
```

Було:

```markdown
Quando você nos escreve pelo [formulário de suporte](/support/), guardamos o tema, o assunto, sua mensagem, o e-mail informado (ou o da sua conta), a conta com que você estava conectado, o número de referência de uma página de erro, se veio de uma, e até 3 anexos. As imagens são recodificadas como as outras (metadados ocultos, como a localização GPS, são removidos); arquivos de texto são guardados como texto. Os anexos ficam em uma pasta privada no nosso servidor, sem endereço público: só a equipe com acesso à caixa de suporte pode baixá-los. Usamos seu e-mail apenas para responder.

Não guardamos seu endereço IP nem dados do navegador com a mensagem. Para barrar spam, uma impressão digital unidirecional e com sal do seu endereço IP fica no cache do servidor por no máximo 24 horas, nunca no banco de dados nem nos registros.
```

Стало:

```markdown
Quando você nos escreve pelo [formulário de suporte](/support/), guardamos o tema, o assunto, sua mensagem, o e-mail informado (ou o da sua conta), a conta com que você estava conectado, o número de referência de uma página de erro, se veio de uma, e até 3 anexos. As imagens são recodificadas como as outras (metadados ocultos, como a localização GPS, são removidos); arquivos de texto são guardados como texto. Os anexos ficam em armazenamento privado, sem endereço público: só a equipe com acesso à caixa de suporte pode baixá-los. Usamos seu e-mail apenas para responder.

Não guardamos seu endereço IP nem dados do navegador com a mensagem. Para limitar spam, o cache do servidor contém contadores identificados por um hash unidirecional com salt do seu endereço IP, nunca pelo endereço em si. Em produção, esse cache usa o banco de dados. Um contador se aplica por no máximo 24 horas. As linhas expiradas do cache podem permanecer no banco até serem removidas durante a manutenção diária. O hash não é guardado com a mensagem de suporte nem nos registros do aplicativo.
```

Було:

```markdown
- Sua conta, perfil, projetos, quem você segue e curtidas: até você excluí-los ou excluir a conta.
- Mensagens ao suporte e anexos: encerradas, 12 meses após o envio; as demais, até serem encerradas; junto com a sua conta.
- Tópicos, respostas e imagens da comunidade: até você excluí-los ou excluir sua conta (o que fica está descrito acima, em “Comunidade”). Votos: até você retirá-los ou excluir sua conta.
- Avisos de respostas: 90 dias.
- Foto de perfil e capa: até você removê-las ou substituí-las, ou excluir sua conta.
- Verificações de disponibilidade: 90 dias.
- Decisões de moderação sobre você (silenciamentos, banimentos, projetos removidos) e avisos: enquanto sua conta existir; são apagados com ela. Denúncias sobre você ficam sem vínculo com a conta, só com o nome mostrado na época.
- Hash do id do GitHub de uma conta banida: só até o banimento terminar ou ser revogado.
- Sessões de login: 2 semanas, ou até você sair da conta.
- Denúncias que você fez: permanecem depois de tratadas. Se você excluir sua conta, ficam sem o seu nome.
- Registro de auditoria: é mantido. As entradas sobre uma conta excluída não contêm o nome de usuário nem o e-mail.
- Contadores de proteção contra abusos: no máximo 24 horas.
- Backups: 14 dias. Uma conta excluída some deles em até 14 dias.
- Arquivos do registro de erros: até encherem (5 MB mais 5 cópias anteriores de 5 MB), depois as entradas mais antigas são apagadas.
- Registros do servidor web e do aplicativo: **TODO**, ainda não decidido.
```

Стало:

```markdown
- Sua conta, perfil, projetos, quem você segue e curtidas: até você excluí-los ou excluir a conta.
- Mensagens ao suporte e anexos: encerradas, 12 meses após o envio; as demais, até serem encerradas; junto com a sua conta.
- Tópicos, respostas e imagens da comunidade: até você excluí-los ou excluir sua conta (o que fica está descrito acima, em “Comunidade”). Votos: até você retirá-los ou excluir sua conta.
- Avisos de respostas: 90 dias.
- Foto de perfil e capa: até você removê-las ou substituí-las, ou excluir sua conta.
- Verificações de disponibilidade: 90 dias.
- Decisões de moderação sobre você (silenciamentos, banimentos, projetos removidos) e avisos: enquanto sua conta existir; são apagados com ela. Denúncias sobre você ficam sem vínculo com a conta, só com o nome mostrado na época.
- Hash do id do GitHub de uma conta banida: só até o banimento terminar ou ser revogado.
- Sessões de login: 2 semanas, ou até você sair da conta.
- Denúncias que você fez: permanecem depois de tratadas. Se você excluir sua conta, ficam sem o seu nome.
- Registro de auditoria: é mantido. As entradas sobre uma conta excluída não contêm o nome de usuário nem o e-mail.
- Contadores de proteção contra abusos: no máximo 24 horas.
- Backups: 14 dias. Uma conta excluída some deles em até 14 dias.
- Arquivos do registro de erros: até encherem (5 MB mais 5 cópias anteriores de 5 MB), depois as entradas mais antigas são apagadas.
- Registros de roteamento da hospedagem e stdout do aplicativo: até aproximadamente uma semana no fluxo de registros da hospedagem; sem arquivo de longo prazo no lançamento.
```

Було:

```markdown
- **GitHub, Inc.** Você entra em github.com, e o nosso servidor lê seu perfil e dados públicos de repositórios pela API do GitHub. A declaração de privacidade do próprio GitHub vale para o seu uso do GitHub.
- **Nosso provedor de e-mail** (por exemplo, o Google, se a caixa da equipe for uma conta do Gmail) entrega na caixa da equipe o aviso de cada mensagem ao suporte, com o texto e o seu e-mail.
- **Os servidores do seu projeto.** Nas verificações de Domain verified e Steady, o nosso servidor acessa o DNS do seu domínio e o endereço do seu projeto. Eles veem o nosso servidor, não você.
- **Nosso provedor de hospedagem**, que mantém o servidor e o banco de dados para nós.
```

Стало:

```markdown
- **Os provedores de hospedagem web e banco de dados gerenciado** operam o aplicativo e armazenam seus registros para nós.
- **O armazenamento de objetos compatível com S3** guarda imagens enviadas e anexos privados de suporte em nosso nome.
- **O GitHub** fornece o acesso à conta e os dados de perfil e repositórios públicos usados nas verificações. A própria política de privacidade dele se aplica ao seu uso do GitHub.
- **Um serviço de email** entrega à caixa da equipe os avisos de suporte, com a mensagem e o endereço de email do remetente.
- **Os servidores DNS e web do seu projeto** recebem nossas solicitações de verificação. Eles veem o endereço do nosso servidor, não o do visitante.
```

### content/pt-br/terms.md

Було:

```markdown
> **Rascunho**, última atualização em 14 de novembro de 2026 (versão {{ terms_version }}). Este texto ainda não foi revisado por um advogado.
>
> Tradução por conveniência; a versão em inglês prevalece.
```

Стало:

```markdown
Última atualização em 14 de novembro de 2026 (versão {{ terms_version }}).

Tradução por conveniência; a versão em inglês prevalece.
```

### content/uk/about.md

Було:

```markdown
{{ site_name }} — публічне місце, де люди, які будують продукти з AI-інструментами, показують те, що справді запустили. Замість заяв кожен проєкт має позначки-підтвердження, які ми перевіряємо самі.

## У чому проблема {#problem}

Сказати «я це запустив» нічого не коштує. Скриншот, пост про запуск чи рядок у резюме можуть описати що завгодно, і ззовні не зрозуміло, чи продукт існує, хто ним керує і чи він працює через місяць.

GitHub показує код. LinkedIn показує заяви. {{ site_name }} намагається показати результат: проєкт, факти про нього, які ми змогли перевірити, і що автор робив далі. Головне тут — проєкт; профіль — це просто збірка чиїхось проєктів.

## Як працюють підтвердження {#proof}

Проєкт може отримати три позначки. Кожна з них — факт, який перевіряє наш сервер, і кожна зникає, щойно факт перестає бути правдою.

- **Власник репозиторію.** Проєкт посилається на публічний репозиторій GitHub. Ми питаємо публічний API GitHub, чи належить він особистому GitHub-акаунту автора і чи це не форк; для репозиторіїв організацій і команд автор натомість додає файл із токеном цього проєкту. Щотижня ми перевіряємо це знову.
- **Домен підтверджено.** Автор доводить, що керує доменом проєкту, за допомогою токена, який ми генеруємо: TXT-запис у DNS або метатег на головній сторінці. Ми регулярно перевіряємо це знову, і позначка тримається, лише поки домен підтверджено за останні 35 днів.
- **Стабільний.** Коли проєкт має позначку «Домен підтверджено», ми відкриваємо його адресу приблизно раз на 3 години. Для «Стабільний» потрібно щонайменше 40 перевірок за останні 30 днів, і щонайменше 95% із них мають отримати відповідь без помилки за 5 секунд.

Повні правила, зокрема як можна втратити кожну позначку, — на сторінці [Як працюють підтвердження](/how-proof-works/).
```

Стало:

```markdown
{{ site_name }} — публічне місце для програмних проєктів, створених з AI-інструментами. Сторінки проєктів об’єднують описи, скриншоти, записи про розробку й позначки підтвердження.

## Що ми перевіряємо {#proof}

Ми перевіряємо володіння публічним репозиторієм GitHub або доступ до запису в ньому, контроль над доменом проєкту й те, чи відповідає сайт. Перевірки та їхні межі описані на сторінці [Як працюють підтвердження](/how-proof-works/).
```

Було:

```markdown
- **Хто написав код.** {{ site_name }} перевіряє лише те, що можна довести: кому належить пов'язаний GitHub-репозиторій, хто контролює домен і чи відповідає сайт. Хто написав код і скільки його написав AI-інструмент, ми не перевіряємо й перевірити не можемо. Історію комітів і дати пише власник репозиторію, і їх можна змінити. Якщо вважаєте, що проєкт скопійовано, поскаржтеся.
- **Чи проєкт хороший.** Позначки — не відгуки. «Стабільний» проєкт може бути слабкою ідеєю, а чудовий проєкт може ще не мати жодної позначки.
- **Що пише автор.** Назву, опис, скриншоти, теги, дату запуску та AI-інструменти в розділі «Створено з» вказує автор. «Створено з» завжди позначено як «зазначено автором».

## Що отримують автори {#builders}

- Публічний профіль, де зібрано ваші проєкти. Ви входите через GitHub; ми просимо лише ваш публічний профіль та адреси пошти, ніколи не доступ до репозиторіїв.
- Сторінку для кожного проєкту з позначками, скриншотами, 30-денною смугою доступності (коли є «Домен підтверджено») і журналом розробки: короткі оновлення та нотатки про запуск, по порядку.
- Бейдж для README на GitHub або для сайту, що показує позначки проєкту саме зараз. Код для вставки є на сторінці проєкту.
- Підписки, вподобання, сторінку «Для вас» з новими запусками і людьми, на яких ви підписані, та сторінку «Пошук», де проєкти можна шукати за тегом, інструментом чи позначкою.
- Контроль над даними: завантажте їх усі файлом або видаліть акаунт у Налаштуваннях. Без реклами, без аналітики, без скриптів стеження.

## Хто за цим стоїть {#who}

{{ site_name }} створює й веде одна людина — Данило Руденко, соло-розробник. Його зроблено так само, як і багато проєктів тут: з AI-інструментами, здебільшого Claude Code, а що будувати і чи результат годиться, вирішує одна людина.

**TODO (Данило):** підтвердь цей абзац і, якщо хочеш, додай речення про себе (де ти, чому почав).

## Що далі {#next}

Заплановано після першої версії, без певного порядку:

- одна сторінка «Для вас» з фільтром замість окремих вкладок;
- аватари й більше можливостей налаштувати профіль;
- досягнення;
- кращі перевірки репозиторіїв, наприклад для форків, і привʼязка репозиторію до домену;
- що має означати «Домен підтверджено» для проєктів, які не є сайтами: консольних інструментів, бібліотек, мобільних застосунків.

**TODO (Данило):** перед публікацією перевір, чи список досі відповідає планам.
```

Стало:

```markdown
Ці перевірки не встановлюють, хто написав код, наскільки використовувався AI, а також якість чи безпеку проєкту. Опис і перелік AI-інструментів надає автор.
```

Було:

```markdown
Питання, ідеї, помилка або проєкт, якому тут не місце: пишіть на [{{ contact_email }}](mailto:{{ contact_email }}). Також можна скористатися посиланням «Поскаржитися» на сторінці будь-якого проєкту чи профілю.

**TODO перед запуском:** ця адреса береться з `CONTACT_EMAIL` у `config/branding.py` і поки що є заглушкою.

```

Стало:

```markdown
З питаннями або по допомогу звертайтеся до [підтримки](/support/) або пишіть на [{{ contact_email }}](mailto:{{ contact_email }}).

```

### content/uk/community-rules.md

Було:

```markdown
*Чернетка. Ці правила є частиною [Умов](/legal/terms/) і можуть змінитися до запуску.*
```

Стало:

```markdown
Ці правила є частиною [Умов](/legal/terms/).
```

Було:

```markdown
- Нові акаунти можуть писати через 10 хвилин після реєстрації. Упродовж перших 24 годин у дописі може бути одне посилання і жодного зображення.
- Є погодинні обмеження (треди, відповіді, голоси, зображення), і той самий текст не можна опублікувати двічі поспіль.
- Голосувати можна лише «за». За власний допис голосувати не можна.
- Свій допис можна змінити. Зміни в перші 15 хвилин непомітні, пізніші отримують позначку «змінено». Назву треду можна змінити лише в ці перші 15 хвилин.
- Свій допис можна видалити. Якщо на нього вже відповіли, відповіді залишаються, а ваш допис показується як «[видалено]».
- Стікери — наш власний набір. Зображення перевіряються й перекодовуються, а їхні метадані (наприклад, місце зйомки) видаляються.
```

Стало:

```markdown
- Нові акаунти можуть писати через 10 хвилин після реєстрації. Упродовж перших 24 годин у дописі може бути одне посилання і жодного зображення.
- Є погодинні обмеження (треди, відповіді, голоси, зображення), і той самий текст не можна опублікувати двічі поспіль.
- Голосувати можна лише «за». За власний допис голосувати не можна.
- Свій допис можна змінити. Зміни в перші 15 хвилин непомітні, пізніші отримують позначку «змінено». Назву треду можна змінити лише в ці перші 15 хвилин.
- Свій допис можна видалити. Якщо на нього вже відповіли, відповіді залишаються, а ваш допис показується як «[видалено]».
- Зображення перевіряються й перекодовуються, а їхні метадані (наприклад, місце зйомки) видаляються.
```

### content/uk/cookies.md

Було:

```markdown
> **Чернетка**, останнє оновлення 12 листопада 2026. Юрист цей текст ще не перевіряв.
```

Стало:

```markdown
Останнє оновлення 12 листопада 2026.
```

### content/uk/privacy.md

Було:

```markdown
> **Чернетка**, останнє оновлення 14 листопада 2026. Юрист цей текст ще не перевіряв.
```

Стало:

```markdown
Останнє оновлення 14 листопада 2026.
```

Було:

```markdown
**Фото профілю й обкладинка.** Ви можете завантажити фото і широку обкладинку або один раз скопіювати своє зображення з GitHub. Кожне зображення ми перекодовуємо (фото до 512×512, обкладинку до 1500×500), що прибирає приховані метадані, як-от GPS-координати, даємо йому випадкову назву й зберігаємо на власному сервері: сторінки ніколи не завантажують ваше фото з GitHub. Обидва зображення **публічні**. Коли ви прибираєте чи замінюєте зображення або видаляєте акаунт, файл видаляється; копії лишаються в резервних копіях до 14 днів. Без фото показуються ваші ініціали.
```

Стало:

```markdown
**Фото профілю й обкладинка.** Ви можете завантажити фото і широку обкладинку або один раз скопіювати своє зображення з GitHub. Кожне зображення ми перекодовуємо (фото до 512×512, обкладинку до 1500×500), що прибирає приховані метадані, як-от GPS-координати, даємо йому випадкову назву й зберігаємо в нашому сховищі: сторінки ніколи не завантажують ваше фото з GitHub. Обидва зображення **публічні**. Коли ви прибираєте чи замінюєте зображення або видаляєте акаунт, файл видаляється; копії лишаються в резервних копіях до 14 днів. Без фото показуються ваші ініціали.
```

Було:

```markdown
- ваші треди: розділ, назва, текст, дати, а також чи тред змінювали, закріпили, закрили чи вилучили;
- ваші відповіді: текст, вибраний стікер і на який допис вони відповідають;
- прикріплені зображення. Вони перекодовуються так само, як знімки екрана: приховані метадані, як-от GPS-координати, видаляються, назви файлів випадкові, а на нашому сервері зберігаються копія до 1600 px і мініатюра 640 px.
```

Стало:

```markdown
- ваші треди: розділ, назва, текст, дати, а також чи тред змінювали, закріпили, закрили чи вилучили;
- ваші відповіді: текст і на який допис вони відповідають;
- прикріплені зображення. Вони перекодовуються так само, як знімки екрана: приховані метадані, як-от GPS-координати, видаляються, назви файлів випадкові, а в нашому сховищі зберігаються копія до 1600 px і мініатюра 640 px.
```

Було:

```markdown
Коли ви видаляєте допис, його текст, стікер і зображення видаляються одразу. Назва треду лишається, поки під ним є чужі відповіді, і показується як «[видалено]». Коли допис вилучають модератори, його зображення видаляються одразу, а текст зберігається разом із причиною, і бачать його лише ви, модератори й команда. Модератори бачать допис, на який поскаржилися, разом з історією автора, як і для інших скарг.
```

Стало:

```markdown
Коли ви видаляєте допис, його текст і зображення видаляються одразу. Назва треду лишається, поки під ним є чужі відповіді, і показується як «[видалено]». Коли допис вилучають модератори, його зображення видаляються одразу, а текст зберігається разом із причиною, і бачать його лише ви, модератори й команда. Модератори бачать допис, на який поскаржилися, разом з історією автора, як і для інших скарг.
```

Було:

```markdown
**IP-адреси та журнали.** Застосунок не зберігає вашу IP-адресу, і в його власних журналах її немає. Про кожен запит сторінки журнали містять лише метод, адресу сторінки (без того, що йде після `?`), статус відповіді, розмір і час обробки, а також помилки. Даних про ваш браузер там немає. Адреси сторінок містять імена користувачів (`/u/<username>/`), тож рядок журналу може показати, чий профіль відкрили, але не хто.

**Журнал помилок.** Коли щось ламається, застосунок записує короткий запис у файл помилок на нашому сервері. У записі є:
```

Стало:

```markdown
**Журнали застосунку.** Власні журнали застосунку містять метод запиту, маршрут із прихованими даними, статус відповіді, її розмір і час виконання, а також очищені повідомлення про помилки. Вони не містять IP-адрес, відомостей про браузер, імен користувачів, параметрів запиту чи вмісту форм.

**Журнал помилок.** Коли щось ламається, застосунок записує короткий запис у файл помилок в нашому сховищі. У записі є:
```

Було:

```markdown
> **TODO перед запуском:** вебсервер перед застосунком веде власний журнал запитів, який за замовчуванням містить IP-адреси. Що саме він записує і як довго зберігає (а також як довго зберігаються журнали застосунку), ще не вирішено. Заповніть це або вимкніть запис IP, перш ніж ця сторінка стане публічною.
```

Стало:

```markdown
Журнали маршрутизації нашого вебхостингу містять IP-адреси відвідувачів. Ці журнали та JSON-журнали stdout застосунку зберігаються в потоці журналів хостингу приблизно до одного тижня. Читати цей потік може лише власник акаунта хостингу. Журнали застосунку не містять IP-адрес або персональних даних. На момент запуску ми не використовуємо довгостроковий архів журналів чи додаток для журналювання, а DNS-провайдер не проксіює трафік сайту. Перш ніж додати архів журналів або ввімкнути проксі трафіку, ми оновимо цю політику.
```

Було:

```markdown
Коли ви пишете нам через [форму підтримки](/support/), ми зберігаємо тему, заголовок, ваше повідомлення, адресу пошти, яку ви вказали (або адресу акаунта), акаунт, з якого ви писали, номер сторінки помилки, якщо ви прийшли з неї, і до 3 вкладень. Зображення перекодовуються так само, як інші картинки (приховані метадані, як-от GPS-координати, видаляються); текстові файли зберігаються як текст. Вкладення лежать у приватній папці на нашому сервері, яка не має публічної адреси: завантажити їх може лише персонал із доступом до скриньки підтримки. Вашу пошту ми використовуємо лише для відповіді.

Ми не зберігаємо разом із повідомленням вашу IP-адресу чи дані браузера. Щоб зупинити спам, солений односторонній відбиток вашої IP-адреси зберігається в кеші сервера щонайбільше 24 години і ніколи не потрапляє в базу даних чи журнали.
```

Стало:

```markdown
Коли ви пишете нам через [форму підтримки](/support/), ми зберігаємо тему, заголовок, ваше повідомлення, адресу пошти, яку ви вказали (або адресу акаунта), акаунт, з якого ви писали, номер сторінки помилки, якщо ви прийшли з неї, і до 3 вкладень. Зображення перекодовуються так само, як інші картинки (приховані метадані, як-от GPS-координати, видаляються); текстові файли зберігаються як текст. Вкладення лежать у приватному сховищі без публічної адреси: завантажити їх може лише персонал із доступом до скриньки підтримки. Вашу пошту ми використовуємо лише для відповіді.

Ми не зберігаємо вашу IP-адресу чи відомості про браузер разом із повідомленням. Для обмеження спаму серверний кеш містить лічильники, ключем яких є солений односторонній хеш IP-адреси, а не сама адреса. У production цей кеш використовує базу даних. Лічильник діє не довше 24 годин. Прострочені рядки кешу можуть залишатися в базі до видалення під час щоденного обслуговування. Хеш не зберігається разом із повідомленням підтримки чи в журналах застосунку.
```

Було:

```markdown
- Акаунт, профіль, проєкти, підписки та вподобання: доки ви їх або акаунт не видалите.
- Звернення в підтримку та вкладення: закриті — 12 місяців після надсилання, інші — доки їх не закриють; разом з акаунтом.
- Треди, відповіді й зображення у спільноті: доки ви їх не видалите або не видалите акаунт (що лишається, описано в «Спільнота» вище). Голоси: доки ви їх не заберете або не видалите акаунт.
- Сповіщення про відповіді: 90 днів.
- Фото профілю й обкладинка: доки ви їх не приберете чи заміните або не видалите акаунт.
- Перевірки доступності: 90 днів.
- Рішення модерації щодо вас (обмеження, блокування, вилучені проєкти) і повідомлення: доки існує ваш акаунт; видаляються разом із ним. Скарги на вас лишаються без звʼязку з акаунтом, лише з імʼям на той момент.
- Хеш GitHub id заблокованого акаунта: лише до кінця або скасування блокування.
- Сесії входу: 2 тижні або до виходу з акаунта.
- Ваші скарги: зберігаються після розгляду. Якщо ви видалите акаунт, вони лишаються без вашого імені.
- Журнал дій: зберігається. Записи про видалений акаунт не містять імені користувача чи пошти.
- Лічильники захисту від зловживань: щонайбільше 24 години.
- Резервні копії: 14 днів. Видалений акаунт зникає з них протягом 14 днів.
- Файли журналу помилок: доки не заповняться (5 МБ плюс 5 старіших копій по 5 МБ), потім найстаріші записи видаляються.
- Журнали вебсервера та застосунку: **TODO**, ще не вирішено.
```

Стало:

```markdown
- Акаунт, профіль, проєкти, підписки та вподобання: доки ви їх або акаунт не видалите.
- Звернення в підтримку та вкладення: закриті — 12 місяців після надсилання, інші — доки їх не закриють; разом з акаунтом.
- Треди, відповіді й зображення у спільноті: доки ви їх не видалите або не видалите акаунт (що лишається, описано в «Спільнота» вище). Голоси: доки ви їх не заберете або не видалите акаунт.
- Сповіщення про відповіді: 90 днів.
- Фото профілю й обкладинка: доки ви їх не приберете чи заміните або не видалите акаунт.
- Перевірки доступності: 90 днів.
- Рішення модерації щодо вас (обмеження, блокування, вилучені проєкти) і повідомлення: доки існує ваш акаунт; видаляються разом із ним. Скарги на вас лишаються без звʼязку з акаунтом, лише з імʼям на той момент.
- Хеш GitHub id заблокованого акаунта: лише до кінця або скасування блокування.
- Сесії входу: 2 тижні або до виходу з акаунта.
- Ваші скарги: зберігаються після розгляду. Якщо ви видалите акаунт, вони лишаються без вашого імені.
- Журнал дій: зберігається. Записи про видалений акаунт не містять імені користувача чи пошти.
- Лічильники захисту від зловживань: щонайбільше 24 години.
- Резервні копії: 14 днів. Видалений акаунт зникає з них протягом 14 днів.
- Файли журналу помилок: доки не заповняться (5 МБ плюс 5 старіших копій по 5 МБ), потім найстаріші записи видаляються.
- Журнали маршрутизації хостингу та stdout застосунку: приблизно до одного тижня в потоці журналів хостингу; на момент запуску довгострокового архіву немає.
```

Було:

```markdown
- **GitHub, Inc.** Ви входите на github.com, а наш сервер читає ваш профіль і публічні дані репозиторію з API GitHub. На користування GitHub поширюється їхня власна політика конфіденційності.
- **Наш поштовий провайдер** (наприклад, Google, якщо скринька команди — це Gmail) доставляє на пошту команди сповіщення про кожне звернення в підтримку з його текстом і вашою адресою пошти.
- **Сервери вашого проєкту.** Для перевірок «Домен підтверджено» і «Стабільний» наш сервер звертається до DNS вашого домену та за адресою проєкту. Вони бачать наш сервер, а не вас.
- **Наш хостинг-провайдер**, який тримає для нас сервер і базу даних.
```

Стало:

```markdown
- **Провайдери вебхостингу й керованої бази даних** забезпечують роботу застосунку й зберігають його записи для нас.
- **S3-сумісне об’єктне сховище** зберігає завантажені зображення й приватні вкладення підтримки від нашого імені.
- **GitHub** забезпечує вхід, дані профілю й публічних репозиторіїв для перевірок. На ваше користування GitHub поширюється його власна політика конфіденційності.
- **Поштовий сервіс** доставляє сповіщення підтримки, включно з повідомленням та адресою відправника, на пошту нашої команди.
- **DNS- і вебсервери вашого проєкту** отримують наші запити перевірки. Вони бачать адресу нашого сервера, а не відвідувача.
```

### content/uk/terms.md

Було:

```markdown
> **Чернетка**, останнє оновлення 14 листопада 2026 (версія {{ terms_version }}). Юрист цей текст ще не перевіряв.
```

Стало:

```markdown
Останнє оновлення 14 листопада 2026 (версія {{ terms_version }}).
```
