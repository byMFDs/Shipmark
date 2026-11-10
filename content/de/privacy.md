# Datenschutzerklärung

> **Entwurf**, zuletzt aktualisiert am 10. November 2026. Dieser Text wurde noch nicht von einer Juristin oder einem Juristen geprüft.
>
> Übersetzung zur Orientierung; maßgeblich ist die englische Fassung.

Diese Seite erklärt, was {{ site_name }} über dich speichert, warum, wie lange und was du dagegen tun kannst. Sie beschreibt, was die Seite tatsächlich tut.

## Wer verantwortlich ist {#controller}

{{ site_name }} wird von {{ legal_owner_name }} betrieben, der für deine Daten verantwortlich ist (der „Verantwortliche“).
Fragen oder Anliegen: [{{ contact_email }}](mailto:{{ contact_email }}).

## Was wir speichern und warum {#data}

**Wenn du dich mit GitHub anmeldest.** Von GitHub erhalten wir deine Konto-ID, deinen Login, deinen Namen, deine Bio, den Link zu deinem Avatar und die übrigen öffentlichen Felder deines GitHub-Profils sowie die E-Mail-Adressen deines GitHub-Kontos. Wir fragen GitHub nur nach `read:user` und `user:email`: Über dein Konto bekommen wir nie Zugriff auf deine Repositories, weder private noch öffentliche. Dein GitHub-Zugriffstoken behalten wir nach der Anmeldung nicht. Wir brauchen das, um dein Konto anzulegen und dich beim nächsten Mal wiederzuerkennen (Erfüllung unserer Vereinbarung mit dir).

**Dein Profil.** Benutzername, Anzeigename, Bio, Website und Sprache. Name und Bio beginnen mit deinen GitHub-Werten; du kannst sie in den Einstellungen ändern. Dein Benutzername, Anzeigename, deine Bio, Website, dein GitHub-Login und der Monat deines Beitritts sind **öffentlich**.

**Deine E-Mail-Adresse.** Sie wird mit deinem Konto gespeichert und ist nur für unser Team sichtbar. Sie wird nie auf der Seite angezeigt. Die Seite versendet keine E-Mails; wir würden die Adresse nur nutzen, um dich zu deinem Konto oder zu einer Meldung zu kontaktieren.

**Deine Projekte.** Alles, was du eingibst: Name, Slogan, Beschreibung, Links, Tags, die KI-Tools, die du nach eigener Aussage genutzt hast (als selbst angegeben angezeigt), Screenshots und Build-Log-Einträge. Veröffentlichte Projekte sind öffentlich; Entwürfe sind nur für dich und unser Team sichtbar. Screenshots werden beim Hochladen neu kodiert, wodurch versteckte Metadaten wie Kameradetails oder GPS-Standort entfernt werden.

**Nachweis-Prüfungen.** Um Prüfzeichen zu vergeben, prüfen wir Fakten selbst (unser berechtigtes Interesse an Nachweisen, denen man vertrauen kann):

- *Authored:* Wir fragen die öffentliche API von GitHub zum verknüpften Repository ab und speichern, ob es dir gehört, deine Commit-Anzahl sowie das Datum deines ersten und letzten Commits. Die Liste der anderen Mitwirkenden von GitHub wird bei der Prüfung gelesen und nicht gespeichert.
- *Live:* Wir fragen die DNS-Einträge der Domain deines Projekts ab oder rufen seine Seite ab, um dein Verifizierungs-Token zu finden.
- *Steady:* Wir rufen die Adresse deines Projekts alle paar Stunden ab und speichern, ob sie geantwortet hat und wie schnell. Diese Prüfungen werden **90 Tage** aufbewahrt.

Die Ergebnisse werden auf deiner öffentlichen Projektseite angezeigt.

**Follows und Likes.** Wir speichern, wem du folgst und welche Projekte du geliked hast. Andere sehen nur die Zahlen, nicht die Listen.

**Meldungen.** Wenn du ein Projekt oder ein Profil meldest, speichern wir den Grund und die Details, die du schreibst. Nur unser Team sieht Meldungen. Die gemeldete Person erfährt nicht, wer sie gemeldet hat.

**Annahme der Bedingungen.** Wir speichern, welche Version der Nutzungsbedingungen du wann akzeptiert hast.

**Audit-Log.** Wir führen intern Buch über Änderungen an Prüfzeichen, Moderationsmaßnahmen und Kontolöschungen, damit Entscheidungen später nachvollziehbar sind. Nur unser Team kann es sehen.

**Was wir nicht speichern.** Die Seite speichert deine IP-Adresse nicht. Um Missbrauch zu begrenzen, zählen wir Aktionen pro Konto (zum Beispiel Likes pro Stunde) höchstens eine Stunde lang im temporären Speicher. Es gibt keine Analyse, keine Werbung und keine Tracking-Skripte. Schriften werden von unserem eigenen Server ausgeliefert.

## Wie lange wir es aufbewahren {#retention}

- Dein Konto, Profil, deine Projekte, Follows und Likes: bis du sie oder dein Konto löschst.
- Uptime-Prüfungen: 90 Tage.
- Anmelde-Sitzungen: 2 Wochen oder bis zum Abmelden.
- Meldungen, die du gemacht hast: bleiben nach der Bearbeitung erhalten. Wenn du dein Konto löschst, bleiben sie ohne deinen Namen.
- Audit-Log: bleibt erhalten. Einträge zu einem gelöschten Konto enthalten weder Benutzername noch E-Mail-Adresse.

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
