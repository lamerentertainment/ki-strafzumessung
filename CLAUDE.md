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
  und Enddispositiv-Werte auseinanderfallen in die andere Richtung — auch dann gilt:
  vorinstanzlicher Wert ins DB-Feld.
- `fall_nr` = die **Geschäfts-Nr. des Obergerichtsurteils** (z.B. `SB240509`), nicht die
  der Vorinstanz (steht so auch in der Feldbeschreibung: "Verfahrensnummer des
  obergerichtlichen Urteils, aus welchem die Informationen entstammen").
- `url_link` = Link zum (Obergerichts-)PDF, das als Quelle diente.
- `zusammenfassung` sollte trotzdem den ganzen Fall abdecken: Anklagevorwurf,
  vorinstanzliche Erwägungen/Strafe UND was das Obergericht geändert hat
  (Freisprüche, abweichende Strafzumessung, Landesverweisung etc.) — das ist der
  einzige Ort, an dem der Berufungsausgang für spätere Leser festgehalten wird.

### 4. Feldlogik / Choices von `database.models.Urteil`

| Feld | Codierung |
|---|---|
| `geschlecht` | `'0'` männlich, `'1'` weiblich |
| `nationalitaet` | `'0'` CH, `'1'` Ausländer/in, `'2'` unbekannt |
| `hauptdelikt` | exakt einer von: `Betrug`, `Veruntreuung`, `ung. Geschäftsbesorgung`, `betr. Missbrauch DVA`, `Diebstahl`, `Sachbeschädigung` — dasjenige Delikt, auf das die Vorinstanz die **Einsatzstrafe** abgestützt hat |
| `hauptsanktion` | `'0'` Freiheitsstrafe, `'1'` Geldstrafe, `'2'` Busse |
| `vollzug` | `'0'` bedingt, `'1'` teilbedingt, `'2'` unbedingt |
| `mehrfach` / `gewerbsmaessig` / `bandenmaessig` | beziehen sich nur auf das Hauptdelikt |
| `deliktssumme` | Deliktsbetrag des Hauptdelikts (subsidiär Gesamtdeliktssumme) |
| `vorbestraft_einschlaegig` | darf nur `True` sein, wenn `vorbestraft` auch `True` ist |

**`nebenverurteilungsscore`** (nicht in `validate_extracted_data` geprüft, muss manuell
berechnet werden): Punkte für alle vorinstanzlichen Schuldsprüche **ausser** dem
Hauptdelikt:
- **+1** pro weiterem **Vergehen** (Strafandrohung: Freiheitsstrafe bis 3 Jahre oder Geldstrafe)
- **+2** pro weiterem **Verbrechen** (Strafandrohung: Freiheitsstrafe > 3 Jahre)
- **+1** zusätzlich, wenn dieses Nebendelikt selbst mehrfach begangen wurde

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

### 6. Eintrag erstellen

Objekt mit allen Pflichtfeldern instanziieren, `full_clean()` vor `save()` aufrufen
(führt Model-Validierung inkl. Choices-Check aus, bevor in die DB geschrieben wird):

```python
from database.models import Urteil
from datetime import date

u = Urteil(
    gericht=...,
    urteilsdatum=date(...),
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

Beide Modelle teilen `gericht`, `urteilsdatum`, `fall_nr`, `url_link`, `geschlecht`,
`nationalitaet`, `hauptsanktion`/`freiheitsstrafe_in_monaten`/`anzahl_tagessaetze`/
`vollzug`, `verfahrensart`, `vorbestraft`/`vorbestraft_einschlaegig` und
`zusammenfassung` mit denselben Codierungen wie `Urteil` (siehe Abschnitt 4) und dieselbe
Vorinstanz-Logik (Abschnitt 3). Vor dem Insert immer `fall_nr` auf Duplikate prüfen
(Abschnitt 5, analog mit dem jeweiligen Modell statt `Urteil`).

**`BetmUrteil`** (`database.models.BetmUrteil`):

- Kein `hauptdelikt`-Feld; das Hauptdelikt ergibt sich implizit aus dem Betäubungsmittel,
  auf das die Einsatzstrafe abgestützt wird.
- `mengenmaessig` / `bandenmaessig` / `gewerbsmaessig` / `anstaltentreffen` / `mehrfach`
  beziehen sich nur auf das Hauptdelikt (Art. 19 Abs. 2 lit. a–c bzw. Abs. 1 BetmG).
- `beschaffungskriminalitaet` = `True` nur, wenn dem Täter im Urteil explizit ein
  Suchtdruck/eigene Konsumabhängigkeit attestiert wird (nicht selbst herleiten).
- `betm` (M2M zu `Betm`, das wiederum auf `BetmArt` verweist): pro sichergestellter/
  gehandelter Substanz einen `Betm`-Datensatz anlegen (`menge_in_g` als Integer runden,
  `rein=True` nur wenn die Menge als reine Wirkstoffmenge gutachterlich festgestellt
  wurde, sonst `rein=False` für Bruttomenge). Existierende `BetmArt`-Werte vorher prüfen
  (`BetmArt.objects.values_list('name', flat=True)`), nicht neue Substanznamen erfinden.
- `rolle` (FK zu `Rolle`): existierende Werte prüfen (`Rolle.objects.values_list('name',
  flat=True)`, z.B. "Verkauf Konsumeinheiten", "Grosshandel", "Transport",
  "Aufbewahrung/Besitz") und den zur Tatbeteiligung passenden auswählen.
- `deliktsertrag` = Erlös/Vermögensvorteil aus dem Handel (subsidiär die vom Gericht
  festgesetzte Ersatzforderung, falls kein expliziter Ertrag beziffert wird).
- `deliktsdauer_in_monaten` = Zeitraum der (Haupt-)Deliktsbegehung gemäss Sachverhalt.
- `nebenverurteilungsscore`-Berechnung identisch zu `Urteil` (Abschnitt 4), bezogen auf
  alle Schuldsprüche ausser dem Hauptdelikt (z.B. weitere BetmG-Tatbestände, HMG-Vergehen).
- `kanton` ist FK zu `Kanton` (Feld `abk`, nicht `name`, z.B. `Kanton.objects.get(abk='ZH')`).

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

## Repo-Hygiene

- `dbdump*.sql`-Dateien im Root sind lokale, nicht committete Datenbank-Dumps —
  nicht versehentlich zu Git hinzufügen.
- Kein `.env` committen; `GOOGLE_API_KEY`/`GEMINI_API_KEY` sind Secrets.
