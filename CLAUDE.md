# CLAUDE.md

Hinweise für Claude Code bei der Arbeit in diesem Repo.

## Django-Setup

- App: `database` (Modelle in `database/models.py`), Projekt: `strafbemessung`.
- DB: lokales Postgres, Verbindungsdaten fix in `strafbemessung/settings/base_settings.py`
  (`kizumessung` / `djangouser` / `localhost:5432`), kein `.env`-Override nötig.
- Virtualenv liegt unter `.venv/`. Vor jedem `manage.py`-Aufruf: `source .venv/bin/activate`.
- Management-Shell-Snippets über `python manage.py shell -c "..."` sind der übliche Weg,
  um Objekte direkt per ORM anzulegen/zu prüfen (kein separates Skript nötig).

## Task: Urteil eigenständig aus einem PDF-Link in die DB eintragen

Wenn der Nutzer einen Link zu einem Urteil (i.d.R. Zürcher Gerichte,
`https://www.gerichte-zh.ch/fileadmin/user_upload/entscheide/oeffentlich/*.pdf`)
schickt und einen neuen DB-Eintrag verlangt, gilt folgender Ablauf. Er gilt analog für
alle drei Deliktsmodelle – `database.models.Urteil` (Vermögensdelikte),
`BetmUrteil` (Betäubungsmitteldelikte) und `SexualdeliktUrteil` (Sexualdelikte) –,
das Vorgehen (PDF lesen statt Gemini-Extraktion, Vorinstanz-Prinzip, Duplikat-Check,
`full_clean()` vor `save()`) ist modellunabhängig. Nur die konkrete Feldliste/Choices
unterscheiden sich; siehe Abschnitt 4 sowie Abschnitt 8 für die Besonderheiten von
`BetmUrteil` und `SexualdeliktUrteil`.

### 1. Nicht zuerst die Gemini-Auto-Extraktion versuchen

Es gibt zwar `database/services/urteil_extractor.py` (Gemini-Structured-Output-Pipeline,
auch über den Admin-Button "🤖 Formular automatisch ausfüllen" nutzbar), aber:

- Sie liefert bei API-Überlastung (503 "high demand") keine Ergebnisse.
- **Feedback des Nutzers:** Bei diesem Task nicht mit der KI-Extraktion herumprobieren
  (auch nicht mit Retry-Loops) — stattdessen das PDF selbst lesen und den Eintrag
  selbst erstellen. Das ist der bevorzugte Weg für diesen Task, nicht nur ein Fallback.

### 2. PDF herunterladen und lesen

```bash
curl -sL "<url>" -o <scratchpad>/<fall_nr>-O1.pdf
```

Dann mit dem `Read`-Tool auslesen (max. 20 Seiten pro Aufruf, ggf. in Blöcken
1-20, 21-40, ... durchgehen). Manchmal ist das verlinkte PDF selbst bereits das
erstinstanzliche Urteil (z.B. eines Bezirksgerichts), nicht ein Obergerichtsurteil —
das erkennt man am Rubrum (kein "Obergericht des Kantons Zürich", kein Hinweis auf
Vorinstanz/Berufung im Text) bzw. daran, dass am Ende evtl. erst noch eine Berufung
angemeldet wurde, aber der Endentscheid dieses Urteils selbst der erstinstanzliche ist.
In diesem Fall entfällt Abschnitt 3 (keine Vorinstanz-Unterscheidung nötig) und man
trägt schlicht die Angaben aus diesem einen Urteil ein; `fall_nr` = dessen eigene
Geschäfts-Nr., `url_link` = der Link zu genau diesem PDF. Relevante Abschnitte eines
Obergerichtsurteils (falls doch ein Berufungsurteil vorliegt):

- S. 1-2: Rubrum (Geschäfts-Nr., Datum, Parteien, Vorinstanz + deren Fall-Nr./Datum)
- S. ~3-6: Dispositiv der Vorinstanz (Schuldsprüche, Strafe, Vollzug) — das ist die
  **primäre Datenquelle** für die meisten Modellfelder, siehe unten
- Erwägungen "III. Schuldpunkt": Sachverhalt & rechtliche Würdigung pro Delikt
  (liefert Deliktssumme, mehrfach/gewerbsmässig/bandenmässig, Freispruch/Bestätigung
  einzelner Anklagepunkte)
- "IV. Strafzumessung": Einsatzstrafe, Asperation, Täterkomponente (Vorstrafen!),
  Verschlechterungsverbot (§ 391 Abs. 2 StPO) — zeigt, ob das Berufungsgericht bei der
  vorinstanzlichen Strafe bleiben musste
- "V./VI. Vollzug / Landesverweisung": Vollzugsart, ggf. Hinweis auf Nationalität
  (Landesverweisung wird nur bei ausländischen Beschuldigten und nur bei
  Katalogtaten nach Art. 66a StGB geprüft — Fehlen ist kein sicherer Beweis für
  Schweizer Nationalität, v.a. wenn keine Katalogtat vorliegt)
- Schlussdispositiv ("Es wird erkannt") ganz am Ende: definitive Schuldsprüche/Freisprüche
  und Strafe des Berufungsgerichts

### 3. Wichtig: Das Modell bildet die VORINSTANZLICHE Verurteilung ab

Die Feldbeschreibungen in `Urteil` bzw. in `urteil_extractor.py` sind eindeutig:
`gericht`, `urteilsdatum`, `hauptsanktion`, `freiheitsstrafe_in_monaten`,
`anzahl_tagessaetze`, `vollzug` etc. beziehen sich auf das **erstinstanzliche
(vorinstanzliche) Urteil**, nicht auf den Endentscheid des Obergerichts. Der Grund:
Die Datenbank sammelt systematisch erstinstanzliche Strafzumessungsentscheide;
Obergerichtsurteile dienen nur als (ausführlichere) Quelle dafür.

Praktisch heisst das:

- `gericht` = das Bezirksgericht (nicht "Obergericht des Kantons Zürich")
- `urteilsdatum` = Datum des Bezirksgerichtsurteils
- `hauptsanktion` / `freiheitsstrafe_in_monaten` / `anzahl_tagessaetze` / `vollzug`
  = wie vom Bezirksgericht ausgesprochen, **auch wenn** das Obergericht die Strafe
  im Berufungsverfahren später reduziert hat (z.B. wegen Freispruchs in einem
  Anklagepunkt oder eigener milderer Strafzumessung). Das kommt vor, wenn nur der
  Beschuldigte Berufung erhoben hat (`reformatio in peius`-Verbot schützt nur vor
  Verschlechterung, nicht vor Bestätigung).
- Nur wenn das Obergericht selbst *strenger* urteilen musste/durfte (z.B. weil auch
  die Staatsanwaltschaft Berufung/Anschlussberufung erhoben hat), können vorinstanzliche
  und Enddispositiv-Werte auseinanderfallen in die andere Richtung — auch dann gilt
  grundsätzlich: vorinstanzlicher Wert ins DB-Feld.
- **Ausnahme 1 (Nutzerentscheid 10.10.2026):** Konnte die Berufungsinstanz die Strafe frei
  festlegen, also ohne Einschränkung durch das Verschlechterungsverbot (z.B. Berufung der
  Staatsanwaltschaft, oder Schuldspruch erst im Berufungsverfahren auf Berufung der
  Privatklägerschaft), dürfen die Felder ausnahmsweise aus Sicht der Berufungsinstanz
  ausgefüllt werden (`gericht`, `urteilsdatum`, Sanktion, Score nach deren Schuldsprüchen).
  Das ist v.a. nötig, wenn die Vorinstanz vom Hauptdelikt freigesprochen hat.
- **Ausnahme 2 (Nutzerentscheid 10.10.2026), Freispruch durch die Berufungsinstanz:** Der
  Eintrag darf mit den vorinstanzlichen Werten bestehen bleiben, wenn (a) alle Felder aus
  den Erwägungen erkennbar sind und (b) das erstinstanzliche Urteil nur einen Schuldspruch
  wegen der Haupttat enthält, ohne weitere Vergehens- oder Verbrechensschuldsprüche, die
  keinen Konnex zum Vermögensdelikt haben. Sonst ist der Eintrag zu verwerfen. Gelockert durch Nutzerentscheid
  vom 11.10.2026: Für (a) genügt, dass die **erfassten Feldwerte** bekannt sind (Vorinstanz-Sanktion und Vollzug,
  Vorstrafen, Deliktssumme, Schuldsprüche usw.); dass das Berufungsurteil die Strafzumessungserwägungen der
  Vorinstanz wiedergibt, ist nicht nötig.
- **Herabstufung oder Tatbestandswechsel beim Hauptdelikt (Nutzerentscheide 11.10.2026):** Stuft die
  Berufungsinstanz das Hauptdelikt herab, sei es nur durch Wegfall der Qualifikation (z.B. gewerbsmässiger →
  einfacher Betrug), durch Wechsel zu einem anderen Tatbestand (z.B. Betrug → Art. 141bis StGB) oder bis zur
  Übertretung (z.B. qualifizierte → geringfügige Sachbeschädigung), bleibt der Eintrag mit den vorinstanzlichen
  Werten bestehen, sofern die erfassten Feldwerte bekannt sind. Fälle, bei denen das unklar ist, dem Nutzer melden
  statt selbst löschen.
- `fall_nr` = die **Geschäfts-Nr. des Obergerichtsurteils** (z.B. `SB240509`), nicht die
  der Vorinstanz (steht so auch in der Feldbeschreibung: "Verfahrensnummer des
  obergerichtlichen Urteils, aus welchem die Informationen entstammen").
- `url_link` = Link zum (Obergerichts-)PDF, das als Quelle diente.
- `zusammenfassung` sollte trotzdem den ganzen Fall abdecken: Anklagevorwurf,
  vorinstanzliche Erwägungen/Strafe UND was das Obergericht geändert hat
  (Freisprüche, abweichende Strafzumessung, Landesverweisung etc.) — das ist der
  einzige Ort, an dem der Berufungsausgang für spätere Leser festgehalten wird.
  Verbindliche Struktur, Mindestumfang und delikt-spezifische Pflichtangaben (auch für
  Vermögensdelikte): Skill `praejudiz-recherche`
  (`.agents/skills/praejudiz-recherche/SKILL.md`), Abschnitt 5.
- **Verbot französischer Tatbestandsbezeichnungen (Nutzerentscheid 19.10.2026):** In
  `kurzsachverhalt`, `zusammenfassung` und `bemerkungen` dürfen niemals französische
  Tatbestands- oder Gesetzesbezeichnungen stehen (weder allein noch in Klammern, z.B. kein
  «tentative de meurtre», «assassinat», «brigandage», «lésions corporelles», «abus de confiance»,
  «escroquerie», «dommages à la propriété», «contrainte», «menaces», «rixe», «voies de fait»,
  «diffamation», «conduite en état d'incapacité», «faux dans les titres», «LStup», «LArm», «LCR»,
  «LEI»). Bei Urteilen aus der Romandie (GE, VD, FR, NE, VS, JU) ist der offizielle deutsche
  Name des Tatbestands zwingend über Fedlex (`get_article`/`get_law_text` bzw. `swiss-caselaw` `get_law`,
  RS 311.0 StGB etc.) zu eruieren und ausschliesslich auf Deutsch zu verwenden (z.B. «versuchte vorsätzliche Tötung»,
  «Mord», «Raub», «einfache/schwere Körperverletzung», «Veruntreuung», «Betrug», «Sachbeschädigung»,
  «Nötigung», «Drohung», «Raufhandel», «Tätlichkeiten», «Fahren in fahrunfähigem Zustand», «BetmG», «WG»).

### 4. Feldlogik / Choices von `database.models.Urteil`

| Feld | Codierung |
|---|---|
| `kanton` | FK zu `Kanton` (nur Feld `abk`, z.B. `Kanton.objects.get(abk='ZH')`) — Kanton des **vorinstanzlichen** Gerichts (`gericht`) |
| `geschlecht` | `'0'` männlich, `'1'` weiblich |
| `nationalitaet` | `'0'` CH, `'1'` Ausländer/in, `'2'` unbekannt |
| `hauptdelikt` | exakt einer von: `Betrug`, `Veruntreuung`, `ung. Geschäftsbesorgung`, `betr. Missbrauch DVA`, `Diebstahl`, `Sachbeschädigung` — dasjenige Delikt, auf das die Vorinstanz die **Einsatzstrafe** abgestützt hat |
| `hauptsanktion` | `'0'` Freiheitsstrafe, `'1'` Geldstrafe, `'2'` Busse |
| `vollzug` | `'0'` bedingt, `'1'` teilbedingt, `'2'` unbedingt |
| `mehrfach` / `gewerbsmaessig` / `bandenmaessig` | beziehen sich nur auf das Hauptdelikt; `mehrfach` nur, wenn der Schuldspruch beim Hauptdelikt ausdrücklich auf »mehrfach« lautet (gewerbsmässig ≠ mehrfach) |
| `deliktssumme` | Deliktsbetrag des Hauptdelikts, d.h. nur der für die Einsatzstrafe massgebende Betrag (subsidiär Gesamtdeliktssumme) |
| `freiheitsstrafe_in_monaten` / `anzahl_tagessaetze` | wird mit dem neuen Urteil eine Gesamtstrafe zusammen mit einer widerrufenen früheren Strafe gebildet, nur die neu ausgesprochene Grundstrafe erfassen; ebenso bei einer Zusatzstrafe (Art. 49 Abs. 2 StGB) nur die Strafe für die nach dem früheren Urteil begangenen Taten (falls nicht separat beziffert, proportional herleiten und in `bemerkungen` begründen) |
| `vorbestraft_einschlaegig` | darf nur `True` sein, wenn `vorbestraft` auch `True` ist |
| `private_geschaedigte` | `'ja'` / `'nein'` / `'unbekannt'` (Default) — ob durch das Hauptdelikt (als Ganzes, bei mehrfacher Begehung alle Einzeltaten) Privatpersonen in ihrem Vermögen geschädigt wurden; `'nein'` nur, wenn ausschliesslich Staat/juristische Personen geschädigt wurden |
| `besonderheiten` / `kurzsachverhalt` / `bemerkungen` | wie bei `BetmUrteil` (Abschnitt 8); `besonderheiten` nach `save()` per `.set([...])`; `'Gehilfenschaft'` vergeben, wenn der Schuldspruch auf Gehilfenschaft (Art. 25 StGB) zum Hauptdelikt lautet |

`private_geschaedigte` fliesst als kategoriales Merkmal in die Vermögensdelikt-Prognose ein
(`VM_CAT_FTS` in `ai_utils.py`); deshalb bei neuen Einträgen möglichst `'ja'`/`'nein'` statt
`'unbekannt'` setzen. `besonderheiten`, `kurzsachverhalt` und `bemerkungen` fliessen (noch)
nicht in die ML-Prognose ein — nicht in die Feature-Listen in `ai_utils.py` aufnehmen.

**`nebenverurteilungsscore`** (nicht in `validate_extracted_data` geprüft, muss manuell
berechnet werden): Punkte für alle vorinstanzlichen Schuldsprüche **ausser** dem
Hauptdelikt:
- **+1** pro weiterem **Vergehen** (Strafandrohung: Freiheitsstrafe bis 3 Jahre oder Geldstrafe)
- **+2** pro weiterem **Verbrechen** (Strafandrohung: Freiheitsstrafe > 3 Jahre)
- **+1** zusätzlich, wenn dieses Nebendelikt selbst mehrfach begangen wurde

Massgebend ist immer der **vorinstanzliche** Schuldspruch: Spricht das Berufungsgericht
bei einem Nebendelikt frei oder zusätzlich schuldig, bleibt der Score unverändert; die
Änderung gehört in `zusammenfassung` und `bemerkungen`.

Gezählt wird **pro Schuldspruch** (pro Zeile im vorinstanzlichen Dispositiv), nicht pro
Gesetzesartikel: Zwei separate Schuldsprüche nach demselben Artikel (z.B. Art. 251 Ziff. 1
Abs. 2 und Abs. 3 StGB) zählen je einzeln, ebenso ein separater Schuldspruch nach dem Artikel
des Hauptdelikts (z.B. einfacher oder versuchter Betrug neben dem gewerbsmässigen Betrug,
versuchter Diebstahl neben dem mehrfachen Diebstahl). Nutzerentscheid vom 10.10.2026.

Verbrechen/Vergehen-Einstufung anhand der Strafandrohung im Gesetzestext prüfen
(nicht raten) — z.B. Art. 146/165/251 StGB (Höchststrafe 5 Jahre) = Verbrechen,
Art. 166/305bis StGB (Höchststrafe 3 Jahre) = Vergehen, Art. 148a StGB Abs. 1
(Höchststrafe 1 Jahr) = Vergehen. Übertretungstatbestände (reine Bussen, z.B.
Art. 87 Abs. 4 AHVG wird im Urteil oft ausdrücklich als "Vergehen" bezeichnet —
dort die explizite Qualifikation im Urteilstext übernehmen, nicht selbst herleiten.

### 5. Vor dem Anlegen: Duplikat-Check

`fall_nr` ist `unique`. Vor dem Insert prüfen:

```bash
python manage.py shell -c "
from database.models import Urteil
print(Urteil.objects.filter(fall_nr__icontains='<FALL_NR>').count())
"
```

**Duplikate (Erstinstanz vs. Obergericht):** Auf Publikationsplattformen (wie `gerichte-zh.ch`) werden zunehmend auch erstinstanzliche Urteile veröffentlicht. Liegt für denselben Fall sowohl das erstinstanzliche als auch das zweitinstanzliche Urteil vor (oder ist der Fall schon als OG-Urteil `SB...` erfasst): **Stets das erstinstanzliche Urteil (`DG...`, `GG...`) als Originalquelle bevorzugen.** Begründung: Das erstinstanzliche Gericht verfügt über die **volle Kognition bei der Strafzumessung** und unterliegt **keinem Verschlechterungsverbot** (Art. 391 Abs. 2 StPO / *reformatio in peius*); die Strafzumessung ist dort regelmässig ausführlicher und unverfälschter. Der OG-Eintrag wird gelöscht, und der weitere Instanzenzug wird in den `bemerkungen` sowie der `zusammenfassung` des erstinstanzlichen Eintrags festgehalten.

### 6. Eintrag erstellen

Objekt mit allen Pflichtfeldern instanziieren, `full_clean()` vor `save()` aufrufen
(führt Model-Validierung inkl. Choices-Check aus, bevor in die DB geschrieben wird):

```python
from database.models import Urteil, Kanton
from datetime import date

u = Urteil(
    gericht=...,
    urteilsdatum=date(...),
    kanton=Kanton.objects.get(abk=...),  # Kanton der Vorinstanz
    fall_nr=...,
    url_link=...,
    verfahrensart='0',  # '0' ordentlich, '1' abgekürzt — meist '0', prüfen falls abgekürztes Verfahren erwähnt wird
    geschlecht=...,
    nationalitaet=...,
    hauptdelikt=...,
    mehrfach=...,
    gewerbsmaessig=...,
    bandenmaessig=...,
    deliktssumme=...,
    nebenverurteilungsscore=...,
    vorbestraft=...,
    vorbestraft_einschlaegig=...,
    hauptsanktion=...,
    freiheitsstrafe_in_monaten=...,
    anzahl_tagessaetze=...,
    vollzug=...,
    zusammenfassung=...,
    in_ki_modell=True,
)
u.full_clean()
u.save()
```

`in_ki_modell=True` setzen, wenn der Fall sauber dokumentiert und die Angaben
zuverlässig ableitbar waren (Standardfall bei manuell aus dem PDF gelesenen Daten).

### 7. Am Ende dem Nutzer eine kompakte Zusammenfassung geben

Kurz auflisten: Fall-Nr., Vorinstanz+Datum, Geschlecht/Nationalität, Hauptdelikt +
Deliktssumme, Nebenverurteilungsscore mit Begründung, Vorstrafen, Hauptsanktion +
Vollzug, und jede Besonderheit, bei der Obergericht von der Vorinstanz abgewichen ist
(Freisprüche, Landesverweisung, Verschlechterungsverbot).

### 8. Besonderheiten von `BetmUrteil` und `SexualdeliktUrteil`

Beide Modelle teilen `gericht`, `urteilsdatum`, `kanton`, `fall_nr`, `url_link`, `geschlecht`,
`nationalitaet`, `hauptsanktion`/`freiheitsstrafe_in_monaten`/`anzahl_tagessaetze`/
`vollzug`, `verfahrensart`, `vorbestraft`/`vorbestraft_einschlaegig` und
`zusammenfassung` mit denselben Codierungen wie `Urteil` (siehe Abschnitt 4) und dieselbe
Vorinstanz-Logik (Abschnitt 3). Vor dem Insert immer `fall_nr` auf Duplikate prüfen
(Abschnitt 5, analog mit dem jeweiligen Modell statt `Urteil`).

**`BetmUrteil`** (`database.models.BetmUrteil`):

- **Ketamin: vorerst nicht erfassen.** Das ML-Modell wurde ohne Ketamin trainiert und wirft
  aktuell einen Fehler, sobald Ketamin in der DB auftaucht. Konkret:
  - Ist Ketamin das **Hauptbetäubungsmittel** (die Einsatzstrafe stützt sich darauf ab), den
    ganzen Fall **nicht** in die DB eintragen.
  - Ist Ketamin nur ein **Nebenbestandteil** neben einer anderen Hauptdroge, den Fall wie
    gewohnt eintragen, aber den Ketamin-Anteil **nicht** als `Betm`-Datensatz erfassen (nur
    die übrigen Substanzen).
  - Sobald das Modell mit Ketamin neu trainiert wurde, entfällt diese Einschränkung.
- Kein `hauptdelikt`-Feld; das Hauptdelikt ergibt sich implizit aus dem Betäubungsmittel,
  auf das die Einsatzstrafe abgestützt wird.
- `mengenmaessig` / `bandenmaessig` / `gewerbsmaessig` / `anstaltentreffen` / `mehrfach`
  beziehen sich nur auf das Hauptdelikt (Art. 19 Abs. 2 lit. a–c bzw. Abs. 1 BetmG).
- `beschaffungskriminalitaet` = `True` nur, wenn dem Täter im Urteil explizit ein
  Suchtdruck/eigene Konsumabhängigkeit attestiert wird (nicht selbst herleiten).
- `betm` (M2M zu `Betm`, das wiederum auf `BetmArt` verweist): pro sichergestellter/
  gehandelter Substanz einen `Betm`-Datensatz anlegen (`menge_in_g` als Integer runden).
  `rein=True`, wenn das Urteil die Reinmenge beziffert **oder** eine analysierte bzw.
  vom Gericht angewandte Reinheit nennt: dann Reinmenge = Nettomenge × Reinheit (bei
  Spannen der untere Wert; Rechnung in `bemerkungen` festhalten). Immer die
  **vorinstanzliche** Menge verwenden und nie Zahlen aus im Urteil zitierten
  Vergleichsfällen übernehmen. Teilmengen ohne Analyse als zusätzlichen Datensatz mit
  `rein=False` erfassen (pro Substanz höchstens ein reiner und ein Gemisch-Datensatz). Existierende `BetmArt`-Werte vorher prüfen
  (`BetmArt.objects.values_list('name', flat=True)`), nicht neue Substanznamen erfinden.
- `rolle` (FK zu `Rolle`): existierende Werte prüfen (`Rolle.objects.values_list('name',
  flat=True)`, z.B. "Verkauf Konsumeinheiten", "Grosshandel", "Transport",
  "Aufbewahrung/Besitz") und den zur Tatbeteiligung passenden auswählen.
  **"Verkauf Konsumeinheiten" vs. "Handel":** "Verkauf Konsumeinheiten" gilt nur, wenn der
  Täter hauptsächlich in kleinen, konsumfertigen Portionen (v.a. 1g-Einheiten) direkt an
  Süchtige verkauft hat (sog. "Kügelidealer"). Werden regelmässig mehrere Gramm auf einmal
  abgegeben (z.B. an Zwischenhändler oder in grösseren Mengen pro Verkauf), ist stattdessen
  "Handel" die richtige Rolle — unabhängig davon, ob insgesamt nur kleine Gesamtmengen
  betroffen sind.
- `deliktsertrag` = Erlös/Vermögensvorteil aus dem Handel (subsidiär die vom Gericht
  festgesetzte Ersatzforderung, falls kein expliziter Ertrag beziffert wird).
- `deliktsdauer_in_monaten` = Zeitraum der (Haupt-)Deliktsbegehung gemäss Sachverhalt.
- `nebenverurteilungsscore`-Berechnung identisch zu `Urteil` (Abschnitt 4), bezogen auf
  alle Schuldsprüche ausser dem Hauptdelikt (z.B. weitere BetmG-Tatbestände, HMG-Vergehen).
- `kanton` ist FK zu `Kanton` (Feld `abk`, nicht `name`, z.B. `Kanton.objects.get(abk='ZH')`).
- `kurzsachverhalt` (zwei bis drei Sätze zum Tatgeschehen, wird als Tooltip in der
  Datenbankansicht angezeigt), `bemerkungen` (freie Notizen) und `besonderheiten`
  (M2M zu `Besonderheiten`, gleicher Katalog wie bei Sexual- und Gewaltdelikten)
  sind optional und identisch zu den entsprechenden Feldern von `GewaltdeliktUrteil`.
  `besonderheiten` erst nach dem Speichern per `.set([...])` zuweisen. Bestehende
  Katalogwerte prüfen (`Besonderheiten.objects.values_list('name', flat=True)`) und
  keine neuen Bezeichnungen erfinden — der Katalog wird von allen drei Deliktsmodellen
  geteilt. Keines der drei Felder fliesst in die ML-Prognose ein.

**`SexualdeliktUrteil`** (`database.models.SexualdeliktUrteil`):

- `hauptdelikt` (FK zu `Hauptdelikt`) und `hauptdelikt_tatmittel` (FK zu `Tatmittel`):
  existierende Werte prüfen, nicht neue Bezeichnungen erfinden, ausser der Fall erfordert
  es klar.
- `hauptdelikt_mehrfachbegehung` / `hauptdelikt_mehrfachbegehung_anzahl` /
  `hauptdelikt_mehrfachbegehung_deliktsperiode`: nur befüllen, wenn das Hauptdelikt
  mehrfach begangen wurde; sonst Default (`False`/`None`) belassen.
- `hauptdelikt_deliktsdauer_bekannt` / `hautpdelikt_deliktsdauer_einfachbegehung`
  (Dauer einer einzelnen Tatbegehung als `timedelta`) nur setzen, wenn die Dauer im
  Urteil konkret beziffert wird.
- `hauptdelikt_taeter_opfer_beziehung` und `hauptdelikt_opferalter` exakt aus den
  Choices im Modell wählen (nicht raten, wenn das Urteil "unbekannt"/keine Angabe macht
  → entsprechende Choice wie `'Beziehung unbekannt'`/`'nicht bekannt'` verwenden).
- `hauptdelikt_opfer_vorerfahrung`: `'Ja'`/`'Nein'`/`'unbekannt'` — nur auf `'Ja'`/`'Nein'`
  setzen, wenn das Urteil das explizit feststellt.
- `sexualdelikte_zusaetzliche` (M2M zu `ZusaetzlicheSexualdelikte`) und `besonderheiten`
  (M2M zu `Besonderheiten`): existierende Werte verwenden, nach dem Speichern des
  Hauptobjekts per `.set([...])` zuweisen (M2M-Felder können nicht im Konstruktor
  gesetzt werden).
- `deliktsscore_uebrige_delikte` entspricht `nebenverurteilungsscore` bei `Urteil`/
  `BetmUrteil` (gleiche Berechnungslogik, Abschnitt 4), bezogen auf alle Schuldsprüche
  ausser den Sexualdelikten.
- Kein separates `deliktssumme`-Feld.
- **Neues Sexualstrafrecht (Taten ab 1.7.2024, Nutzerentscheid 17.10.2026):** Dafür gibt es eigene
  Katalogwerte ohne «altrechtlich», nur mit Artikelnummer und dem Titel gemäss Fedlex (z.B.
  `190, Vergewaltigung`, `189, Sexueller Übergriff und sexuelle Nötigung`,
  `193, Ausnützung einer Notlage oder Abhängigkeit`) bei `Hauptdelikt` und
  `ZusaetzlicheSexualdelikte`. Taten bis 30.6.2024 bleiben bei den altrechtlichen Werten. Fehlt ein Wert,
  den Wortlaut des Titels über Fedlex (`get_law_text`, RS 311.0) prüfen und neu anlegen.
- **`freiheitsstrafe_in_monaten`/`anzahl_tagessaetze` bei Gesamtstrafen:** Eine Gesamtstrafe nach Art. 49
  Abs. 1 StGB (Sexual- und Nebendelikte gleichzeitig beurteilt) wird als ausgesprochene Gesamtstrafe
  erfasst; die Nebendelikte stehen im `deliktsscore_uebrige_delikte`. Wird dagegen die Strafe eines
  früheren Urteils hinzugezogen (Zusatzstrafe, Art. 49 Abs. 2 StGB), nur die Strafe für die neu beurteilten Taten erfassen.
- **Nationalität bei Flüchtlingen:** Flüchtlinge sind zwingend ausländischer Herkunft (`nationalitaet='1'`).
- **`Verletzung Beschleunigungsgebot`:** Nur setzen, wenn die Strafminderung in der erfassten (Vorinstanz-)Strafe
  enthalten ist. Prüfen, ob das Gericht von einer Verletzung im Rechtsmittelverfahren oder im Verfahren insgesamt
  (inkl. Untersuchungsverfahren) spricht. Bei Letzterem ist anzunehmen, dass die Minderung schon im Vorverfahren
  gewährt wurde. Nimmt die Berufungsinstanz erst selbst die Minderung vor, nicht setzen.

### 9. Besonderheiten von `KonkursdeliktUrteil` (Art. 163–169 StGB, kein ML-Modell)

Zweck: die Strafzumessungs- **und Asperationspraxis** zu den Konkursdelikten systematisch erfassen
(Grundlage der Praxiskommentare `kommentar_*.html`). Gemeinsame Felder und Vorinstanz-Prinzip wie oben;
kein `in_ki_modell`.

- **Zwei Fallgruppen:**
  - Konkursdelikt trägt die Einsatzstrafe → `hauptdelikt` (FK zu `Konkursdelikt`) setzen, dazu
    `hauptdelikt_mehrfach`/`_deliktssumme`/`_deliktsdauer_in_monaten`/`_anzahl_tathandlungen`.
  - Einsatzstrafe beruht auf einem anderen Delikt (z.B. Art. 158, 146, 251 StGB), Konkursdelikte nur
    asperiert → `hauptdelikt` leer, `einsatzdelikt_uebriges` mit Bezeichnung und Artikel ausfüllen,
    `hauptdelikt_*` leer lassen. Mindestens eine `KonkursdeliktAsperation`-Zeile ist Pflicht. Ist das
    Einsatzdelikt ein Vermögensdelikt aus Abschnitt 4, gehört der Fall **zusätzlich** wie bisher in `Urteil`.
  - `clean()` erzwingt: genau eines von `hauptdelikt`/`einsatzdelikt_uebriges`.
- **`KonkursdeliktAsperation`** (Through-Modell von `konkursdelikte_zusaetzliche`): eine Zeile pro weiterem
  Konkursdelikt-Schuldspruch mit `einzelstrafe_*` (isoliert bemessen) und `zuschlag_*`
  (Asperationszuschlag), je in Monaten **oder** Tagessätzen. Derselbe Tatbestand darf mehrfach vorkommen
  (z.B. Misswirtschaft je Gesellschaft, `bezeichnung` = Gesellschaft/Tatkomplex). Anlegen per
  `KonkursdeliktAsperation.objects.create(urteil=..., delikt=..., ...)` nach `save()` (nicht `.set()`).
- **`einsatzstrafe_*`:** Einsatzstrafe des Einsatzdelikts (Tatkomponente, vor Asperation/Täterkomponente).
  Einsatz-, Einzelstrafen und Zuschläge nur übernehmen, wenn sie im Urteil beziffert sind (keine
  Rückrechnung); `strafzumessung_quelle` hält fest, ob sie aus den Erwägungen der Vorinstanz oder der
  Berufungsinstanz stammen. Die ausgesprochene Sanktion (`hauptsanktion` usw.) folgt immer Abschnitt 3.
- **`deliktsscore_uebrige_delikte`:** alle Schuldsprüche ausser den Konkursdelikten (Katalog) und ausser dem
  Einsatzdelikt gemäss `einsatzdelikt_uebriges`; Berechnung wie Abschnitt 4. Art. 323–325 StGB sind
  Übertretungen und zählen nicht.
- **`hauptdelikt_deliktssumme` je Tatbestand:** 163 = dem Zugriff entzogener Wert (nicht die
  Verlustscheinsumme), 164 = entzogenes Haftungssubstrat, 165 = Verschleppungsschaden, 167 =
  Bevorzugungsbetrag, 166 = leer. `deliktsdauer`: 165 Verschleppungsdauer, 166 Dauer der Unterlassung.
- **Merkmale nur setzen, wenn das Urteil sie feststellt:** `beweggrund` (bei 163/164 ist das finanzielle
  Motiv deliktsimmanent → dort nur `Firmenbestattung`/`fremdnützig`), `konstrukt_machenschaften`,
  `notlage_oder_sucht`, `untergeordnete_rolle`; `buchfuehrung_fehlt_vollstaendig` nur bei einem
  Schuldspruch nach Art. 166 StGB, sonst leer.
- `vorbestraft_einschlaegig` = Vorstrafe wegen Betreibungs- oder Konkursdelikten, auch per Strafbefehl.
- Duplikat-Check analog Abschnitt 5 mit `KonkursdeliktUrteil`.

## Repo-Hygiene

- `dbdump*.sql`-Dateien im Root sind lokale, nicht committete Datenbank-Dumps —
  nicht versehentlich zu Git hinzufügen.
- Kein `.env` committen; `GOOGLE_API_KEY`/`GEMINI_API_KEY` sind Secrets.
