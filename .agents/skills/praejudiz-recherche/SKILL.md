---
name: praejudiz-recherche
description: >
  Sucht eigenständig neue kantonale Präjudizien (Obergerichtsurteile) zu einem Deliktsbereich,
  prüft sie auf Eignung für die Strafzumessungs-DB und legt sie als DB-Eintrag an. Enthält
  verbindliche Prüfregeln für den Dispositiv-Abgleich (Vorinstanz vs. Berufungsgericht), das
  Vorinstanz-Prinzip, Geständnisrabatte, Besonderheiten sowie Redaktionsstandards für Zusammenfassungen.
---

# Präjudizien-Recherche und DB-Eintragung

## Überblick & Datenbank-Architektur

Die Datenbank sammelt systematisch **erstinstanzliche Strafzumessungsentscheide** (Bezirksgerichte, Regionalgerichte, Strafgerichte, Amtsgerichte, Juges de police, Tribunaux de police/pénal). Da erstinstanzliche Entscheide in der Schweiz jedoch selten publiziert werden, dienen publizierte **Berufungsentscheide der Obergerichte bzw. Kantonsgerichte** als primäre Fundgrube.

Daraus ergibt sich das fundamentale **Zwei-Ebenen-Prinzip**:

1. **Strukturierte Datenbankfelder = VORINSTANZ:**
   Die Felder `gericht`, `urteilsdatum`, `hauptsanktion`, `freiheitsstrafe_in_monaten`, `anzahl_tagessaetze`, `vollzug`, `lebensgefahr`, `besondere_gefaehrlichkeit` etc. bilden konsequent das **vorinstanzliche Urteil** ab. Selbst wenn das Berufungsgericht die Strafe später senkt, erhöht oder den Vollzug anpasst, bleiben in diesen Feldern die Werte der Vorinstanz stehen!
   *Regelfall bei Berufungsurteilen als Quelle:* `fall_nr` ist die Geschäfts-Nr. des Obergerichts (z.B. `SST.2023.141`, `SK 22 32`), und `url_link` verlinkt das Dokument des Obergerichts.
2. **`zusammenfassung` = BEIDE INSTANZEN:**
   Die Zusammenfassung ist der einzige Ort in der Datenbank, der den vollständigen Verfahrensverlauf dokumentiert. Sie muss sowohl den Vorinstanzentscheid als auch den **Berufungsausgang mit allen Abweichungen, Gutheissungen, Strafänderungen und Rabatten** wahrheitsgetreu und präzise festhalten.

### Präferenzentscheidung: Erstinstanzliche Urteile als Originalquelle bei Duplikaten

Auf Publikationsplattformen (insbesondere auf `gerichte-zh.ch`) werden zunehmend auch erstinstanzliche Urteile (Bezirksgerichte, z.B. Geschäftsnummern `DG...`, `GG...`) direkt veröffentlicht. Liegt für denselben Fall sowohl das erstinstanzliche Urteil als auch ein oberinstanzliches Berufungsurteil (z.B. Obergericht `SB...`) vor (Duplikat):

* **Vorrang des erstinstanzlichen Urteils:** Das erstinstanzliche Urteil wird **als Originalquelle bevorzugt** (`fall_nr` und `url_link` verweisen auf den erstinstanzlichen Entscheid). Der oberinstanzliche Duplikat-Eintrag wird gelöscht.
* **Juristische Begründung:** Das erstinstanzliche Gericht verfügt über die **volle Kognition bei der Strafzumessung** und unterliegt **keinem Verschlechterungsverbot** (Art. 391 Abs. 2 StPO / *reformatio in peius*). Die Strafzumessungserwägungen sind erstinstanzlich regelmässig deutlich ausführlicher, differenzierter und unverfälschter dargelegt, während das Berufungsgericht oft nur selektiv auf beanstandete Punkte eingeht oder an die vorinstanzliche Strafe gebunden ist.
* **Dokumentation des Instanzenzugs:** Der weitere Instanzenzug (Berufungsentscheid des Ober-/Kantonsgerichts mit Geschäftsnummer, Datum, allfälligen Freisprüchen/Strafkorrekturen) sowie die Löschung des Duplikats werden im Feld `bemerkungen` und in der `zusammenfassung` des verbleibenden erstinstanzlichen Eintrags festgehalten.
* **Subsidiär:** Ist der erstinstanzliche Entscheid nicht als separates Dokument publiziert, bleibt das Obergerichtsurteil als Quelle bestehen, bildet jedoch inhaltlich die Vorinstanz ab.

---

## 1. Auswahlkriterien: Wann ist ein Urteil brauchbar?

Massgebend ist: **Überlebt der Schuldspruch zum Hauptdelikt die Berufung in seiner rechtlichen Qualifikation?**

| Konstellation | Brauchbar? | Vorgehen |
|---|:---:|---|
| Schuldsprüche vollumfänglich bestätigt, Strafe bestätigt oder leicht angepasst | **Ja (Idealfall)** | Vorinstanz-Werte in Felder; Berufungsausgang in Zusammenfassung |
| Nur Privatkläger/Staatsanwaltschaft erhob Berufung, Schuldspruch unangefochten rechtskräftig | **Ja** | Sehr sauber; Vorinstanz-Werte direkt übernehmen |
| Hauptdelikt bestätigt, aber Teilfreispruch bei einem **Nebendelikt** | **Ja** | `deliktsscore_uebrige_delikte` um das weggefallene Nebendelikt bereinigen |
| Hauptdelikt bestätigt, Obergericht spricht bei einem **Nebendelikt zusätzlich schuldig** | **Ja** | `deliktsscore_uebrige_delikte` um das neue Nebendelikt erhöhen (Score bildet finalen Stand ab) |
| Berufungsgericht korrigiert Strafmass (Erhöhung oder Senkung) oder Vollzug (z.B. unbedingt → bedingt) | **Ja** | Strukturierte Felder = Vorinstanz! Die Änderung wird detailliert in der Zusammenfassung begründet |
| Hauptdelikt wird **herabgestuft** (z.B. schwere Körperverletzung → einfache Körperverletzung, einfache Körperverletzung → Tätlichkeiten) | **Nein** | Verwerfen – die vorinstanzliche Qualifikation wurde verworfen |
| Hauptdelikt wird **freigesprochen** (z.B. in dubio pro reo) | **Nein** | Verwerfen |
| Vollständiger Freispruch oder Rückweisung an die Vorinstanz | **Nein** | Verwerfen |
| Vorinstanz hatte **freigesprochen**, erst Obergericht verurteilt | **Nein** | Verwerfen – es existieren keine vorinstanzlichen Strafzumessungsdaten |

### Modell-Abgrenzung (Welches Modell wählen?)

* **`SexualdeliktUrteil`**: Ist ein Sexualdelikt (Art. 189, 190, 191, 187 StGB) das dominante oder auch nur ein mitverurteiltes Delikt, gehört der Fall zwingend in `SexualdeliktUrteil` – selbst wenn daneben erhebliche Körperverletzungen, Drohungen oder Freiheitsberaubungen vorliegen.
* **`BetmUrteil`**: Reine Betäubungsmitteldelikte (Art. 19 ff. BetmG). **Ketamin-Achtung:** Ist
  Ketamin das Hauptbetäubungsmittel, den Fall vorerst überspringen (ML-Modell wurde ohne Ketamin
  trainiert und wirft bei Ketamin in der DB einen Fehler). Ist Ketamin nur Nebenbestandteil neben
  einer anderen Hauptdroge, den Fall wie gewohnt eintragen, aber den Ketamin-Anteil nicht als
  `Betm`-Datensatz erfassen.
* **`Urteil`**: Reine Vermögensdelikte (Art. 138, 139, 140, 144, 146 StGB etc., sofern kein Waffeneinsatz/Gewalt gegen Leib und Leben dominierte).
* **`GewaltdeliktUrteil`**: Delikte gegen Leib und Leben (Mord, vorsätzliche Tötung, schwere/einfache Körperverletzung, Tätlichkeiten, Gefährdung des Lebens, Raub, Angriff, Raufhandel).
* **Komplexe Mehrfachtäter- und Seriendelikte**: Fälle mit mehr als 3–4 Tatkomplexen, unzähligen Opfern über viele Jahre oder unentwirrbaren Anklagepunkten im Zweifel überspringen, da die Reduktion auf ein strukturiertes Schema fehleranfällig ist.

---

## 2. Volltextanalyse & Zwingender 2-Phasen-Dispositiv-Abgleich

> [!CAUTION]
> **Häufigste Fehlerquelle bei KI-Agenten:**
> Agenten neigen dazu, den Berufungsausgang zu halluzinieren (z.B. voreilig zu behaupten, die Berufung sei "abgewiesen und das Urteil bestätigt" worden, oder eine Landesverweisung sei "entfallen").
> **Pflicht:** Das erstinstanzliche und das zweitinstanzliche Dispositiv müssen ZWINGEND Wort für Wort gegeneinander abgeglichen werden!

### Volltext beschaffen
Niemals auf abgeschnittene Textauszüge (z.B. die 100k-Zeichen-Grenze bei MCP-Tools) verlassen. Bei langen Entscheiden das vollständige Dokument herunterladen und konvertieren:
```bash
curl -sL "<URL>" -o /tmp/urteil.pdf && pdftotext /tmp/urteil.pdf /tmp/urteil.txt
```

### Phase 1: Vorinstanz-Dispositiv lokalisieren
Im Obergerichtsurteil wird das erstinstanzliche Dispositiv fast immer in der **Prozessgeschichte** wörtlich zitiert (meist unter Ziff. I oder zu Beginn der Erwägungen):
* **Gericht & Urteilsdatum:** Exakte Bezeichnung des erstinstanzlichen Gerichts (z.B. *Bezirksgericht Zofingen*, *Strafgericht Basel-Landschaft*, *Tribunal pénal de la Sarine*) und dessen Datum.
* **Schuldsprüche der Vorinstanz:** Welche Delikte wurden erstinstanzlich bejaht?
* **Vorinstanzliche Sanktion:** Hauptsanktionsart (Freiheitsstrafe / Geldstrafe), Dauer in Monaten bzw. Anzahl Tagessätze, Vollzugsform (bedingt, teilbedingt, unbedingt) und allfällige Landesverweisung.
* **Diese Werte gehören in die strukturierten Datenbankfelder!**

### Phase 2: Berufungs-Dispositiv lokalisieren
Das Schlussdispositiv des Berufungsgerichts suchen (Formulierungen: *«Das Obergericht erkennt:»*, *«Demnach wird erkannt:»*, *«Par ces motifs, la Cour arrête:»*):
* **Wurde die Strafe abgeändert?**
  * Straferhöhung (z.B. bei Berufung der Staatsanwaltschaft) oder Strafsenkung (z.B. bei Berücksichtigung von Eventualvorsatz, Geständnis oder Verfahrensverzögerung)?
  * Strafart geändert? (z.B. Umwandlung einer kurzen Freiheitsstrafe in eine Geldstrafe oder umgekehrt).
  * Die geänderte Strafe **muss mit genauer Zahl** in der Zusammenfassung genannt werden!
* **Wurde der Vollzug abgeändert?**
  * Wurde aus einer unbedingten Strafe eine bedingte Strafe (z.B. mit Probezeit und Bewährungshilfe)?
  * Wurde auf den Widerruf einer Vorstrafe verzichtet?
  * Wurde eine stationäre Massnahme (Art. 59 StGB) durch eine ambulante Massnahme (Art. 63 StGB) ersetzt?
* **Was geschah mit der Landesverweisung?**
  * Prüfen: Wurde die Landesverweisung bestätigt, aufgehoben (z.B. wegen Härtefalls oder FZA Art. 5 Anhang I) oder deren Dauer verändert?
  * *Niemals mutmassen:* Stand im Dispositiv *«wird bestätigt»*, bleibt sie bestehen!
* **Wurden Qualifikationen geändert?**
  * Wurde z.B. Lebensgefahr (Art. 140 Ziff. 4 StGB) entgegen der Vorinstanz bejaht? Wurde ein Nebendelikt gestrichen (Verjährung, ne bis in idem) oder ein Vorwurf verschärft (z.B. Erpressung statt Nötigung)?

---

## 3. Strafminderungsgründe & Besonderheiten (M2M-Feld)

In `GewaltdeliktUrteil` existiert das Many-to-Many-Feld `besonderheiten`. Folgende Besonderheiten sind verfügbar und **müssen aktiv vergeben werden**, wenn sie im Fall vorliegen:

| Besonderheit | Wann vergeben? | Auswirkung auf `zusammenfassung` |
|---|---|---|
| **`Geständnisrabatt`** | Wenn das Gericht dem Täter ein Geständnis, Einsicht, Reue oder aktive Tataufdeckung **ausdrücklich strafmindernd** anrechnet. | Das genaue Ausmass bzw. die Begründung des Rabatts zwingend beziffern (z.B. *"Täterkomponente mit 3 Jahren bzw. 4 Monaten strafmindernd berücksichtigt"*). |
| **`verminderte Schuldfähigkeit`** | Wenn das Gericht **Art. 19 Abs. 2 StGB** anwendet (psychiatrisches Gutachten, psychische Störung, Intoxikation). | Grad der Verminderung (leicht, mittelgradig) und psychiatrische Diagnose in der Zusammenfassung erwähnen. |
| **`Verletzung Beschleunigungsgebot`** | Wenn das Gericht eine ungerechtfertigte Verfahrensverzögerung (Art. 5 Abs. 2 StPO) feststellt und die Strafe dafür mindert. | Dauer der Überliegezeit und Umfang der Strafminderung (z.B. *-3 Monate*) festhalten. |
| **`Versuch`** | Wenn das Hauptdelikt beim Versuch geblieben ist (Art. 22 StGB). **Zwingend:** Lautet der Schuldspruch der Vorinstanz auf Versuch, **muss** `'Versuch'` in `besonderheiten` markiert werden (in Modellen mit `versuch`-Boolean zusätzlich dort auf `True`). |
| **`jugendlicheR TäterIn`** | Wenn Jugendstrafrecht oder besondere Bestimmungen für junge Erwachsene (Art. 61 StGB) greifen. | In der Zusammenfassung erläutern. |

> [!IMPORTANT]
> `besonderheiten` kann in Django **nicht** im Modell-Konstruktor übergeben werden, sondern erst nach dem Speichern via:
> ```python
> obj.save()
> obj.besonderheiten.set(Besonderheiten.objects.filter(name__in=['Geständnisrabatt', 'verminderte Schuldfähigkeit']))
> ```

---

## 4. Feldreferenz & Spezifische Choices von `GewaltdeliktUrteil`

Choices **niemals erraten**, sondern bei Unklarheit per Shell prüfen.

| Feld | Typ / Choices | Regeln & Typische Fehler |
|---|---|---|
| `hauptdelikt` | Text-Choice | Exakter Name des Delikts, das die **Einsatzstrafe** trägt (`'Mord'`, `'vorsätzliche Tötung'`, `'schwere Körperverletzung'`, `'einfache Körperverletzung'`, `'Raub'`, `'Gefährdung des Lebens'` etc.). Trägt eine versuchte Tat die Einsatzstrafe, Deliktsname hier eintragen und `versuch=True` setzen. |
| `tatmittel` | Text-Choice | **Wichtig:** Die Choice `'Messer/Stichwaffe'` lautet im Modell: *"Messer/Stich-/Schnittwerkzeug (auch Glas/Flasche)"*. Abgebrochene Flaschen oder Glasscherben gehören daher zwingend hierher, **nicht** zu `'andere'`. Knüppel, Stangen, Krücken, Werkzeuge = `'stumpfer Gegenstand'`. Reine Fäuste/Tritte = `'körperliche Gewalt'`. Autos = `'Fahrzeug/Motorfahrzeug'`. |
| `waffe_gefaehrlicher_gegenstand` | Boolean | `True`, wenn ein Messer, eine Schusswaffe, ein gefährlicher Gegenstand (Krücke, Kochlöffel, Metallstange, Glasflasche) als Tatmittel eingesetzt wurde. |
| `vorsatzform` | Choice | `'direktvorsatz'`, `'eventualvorsatz'`, `'fahrlaessig'`, `'unbekannt'`. |
| `taeter_opfer_beziehung` | Choice | `'Partner/Ex-Partner'`, `'Familie'`, `'Bekannte'`, `'flüchtig bekannt'`, `'Unbekannte'`, `'Beziehung unbekannt'`. |
| `verletzungsfolge` | Choice | `'keine'`, `'Tätlichkeit'`, `'leicht'`, `'erheblich'`, `'schwer'`, `'lebensgefährlich'`, `'Tod'`. **Massgebend ist die tatsächlich eingetretene Folge**, nicht die hypothetische Gefahr. |
| `lebensgefahr` | Boolean | `True`, wenn eine konkrete Lebensgefahr für das Opfer geschaffen wurde (auch wenn z.B. Art. 129 StGB mangels Skrupellosigkeit verneint oder Art. 140 Ziff. 4 StGB bejaht wurde). |
| `besondere_gefaehrlichkeit` | Boolean | `True`, wenn besondere Skrupellosigkeit, Grausamkeit oder besondere Gefährlichkeit vorliegt (z.B. Art. 112 oder Art. 140 Ziff. 3 StGB). |
| `deliktsscore_uebrige_delikte` | Integer | Punktesumme aller **weiteren Schuldsprüche ausser dem Hauptdelikt** (finaler Stand nach Berufung):<br>• **+1** pro Vergehen (Höchststrafe bis 3 Jahre)<br>• **+2** pro Verbrechen (Höchststrafe > 3 Jahre)<br>• **+1 zusätzlich**, wenn dieses Nebendelikt mehrfach begangen wurde<br>• Übertretungen zählen 0 Punkte. |
| `hauptsanktion` | Choice | `'0'` Freiheitsstrafe, `'1'` Geldstrafe, `'2'` Busse (Vorinstanz!). |
| `freiheitsstrafe_in_monaten` | Integer | Vorinstanzliche Freiheitsstrafe in Monaten. Bei Geldstrafe `0` setzen. |
| `anzahl_tagessaetze` | Integer | Vorinstanzliche Anzahl Tagessätze. Bei Freiheitsstrafe `0` setzen. |
| `vollzug` | Choice | `'0'` bedingt, `'1'` teilbedingt, `'2'` unbedingt (Vorinstanz!). Bei Aufschub zugunsten Art. 59/61 StGB im Modell meist `'0'` oder `'2'`. |
| `nationalitaet` | Choice | `'0'` Schweiz, `'1'` Ausländer/in, `'2'` unbekannt.<br>• **Zwingender Umkehrschluss bei Katalogtaten ab 1. Oktober 2016:** Fand die Tat nach dem 1. Oktober 2016 statt und enthält der Schuldspruch ein obligatorisches Katalogdelikt nach Art. 66a Abs. 1 StGB (z.B. Art. 187 Ziff. 1/1bis, 188, 189 Abs. 2/3, 190, 191, 193, 193a, 195, 197 Abs. 4 Satz 2 StGB bzw. Tötungs-/schwere Gewaltdelikte) und wird im gesamten Urteil eine Landesverweisung mit **keinem Wort thematisiert**, **muss der Täter Schweizer Staatsangehöriger sein (`'0'`)**, da bei einem Ausländer zwingend eine Prüfung nach Art. 66a StGB erfolgen müsste.<br>• In allen anderen Konstellationen gilt: Nur `'0'`/`'1'`, wenn das Urteil explizite Angaben enthält (Heimatort, Staatsangehörigkeit, Aufenthaltsstatus). |
| `kanton` | FK | ForeignKey auf `Kanton` mit Feld `abk` (z.B. `Kanton.objects.get(abk='BE')`). |

---

## 5. Redaktionsstandards für `kurzsachverhalt` und `zusammenfassung`

### `kurzsachverhalt`
* **Länge:** 1 bis 2 prägnante Sätze im Aktiv.
* **Inhalt:** Ausschliesslich der gerichtlich (zuletzt, i.d.R. vorinstanzlich) festgestellte Sachverhalt, der zur Strafe geführt hat — konkrete Tathandlung, Tatmittel, Ort/Kontext und Verletzungsfolgen in Klammern.
* **Keine** abstrakten Floskeln (*"übte Gewalt aus"*), sondern konkrete Aktionen (*"schlug mit der Faust ins Gesicht und trat mit Füssen gegen den Kopf"*).
* **Keine** Prozess-/Verfahrensangaben und keine Verteidigungsstrategie: nicht ob/wie der Beschuldigte bestritten, gestanden, sich verantwortet oder welche Beweisanträge/Schutzbehauptungen er vorgebracht hat, und nicht wie das Gericht diese gewürdigt hat (z.B. *"wurde als unglaubhafte Schutzbehauptung verworfen"*, *"bestritt den Vorwurf durchgehend"*). Solche Angaben gehören — falls relevant — in `bemerkungen` oder `zusammenfassung`, nicht in `kurzsachverhalt`.

### `zusammenfassung`
> [!IMPORTANT]
> **Die Zusammenfassung darf nicht zu kurz sein!**
> Richtwert: **2 bis 4 strukturierte Absätze (ca. 1500–3000 Zeichen)**. Niemals den Berufungsausgang auslassen oder mittendrin abbrechen!

Struktur der Zusammenfassung:
1. **Absatz 1: Sachverhalt & Tatausführung:**
   Wer, wann, wo, wie und warum? Konkrete Handlung, eingesetzte Tatmittel/Waffen, Rolle von Mittätern, Dynamik (Streit, Eifersucht, Überforderung), konkrete Verletzungen des Opfers (Brüche, Hämatome, Schnittwunden, Traumata, Arbeitsunfähigkeit).
2. **Absatz 2: Vorinstanzliches Urteil (Erstinstanz):**
   Welches Gericht sprach wann welches Urteil aus? Schuldsprüche (Haupt- und Nebendelikte), verhängte Sanktion (Freiheitsstrafe in Monaten/Jahren, Geldstrafe, Tagessatzhöhe), Vollzugsform (Probezeit), allfällige Landesverweisung und Zivilansprüche (Genugtuung, Schadenersatz).
3. **Absatz 3: Berufungsverfahren & Anträge:**
   Wer hat Berufung / Anschlussberufung erhoben? Was wurde verlangt (Freispruch, Schuldspruchänderung, Strafreduktion, Strafverschärfung, Aufhebung der Landesverweisung)? Standpunkt der Verteidigung (z.B. Notwehr, fehlender Vorsatz, Beweisanträge).
4. **Absatz 4: Entscheid des Berufungsgerichts & Strafzumessung:**
   Wie hat das Berufungsgericht entschieden? Wurde der Schuldspruch bestätigt oder geändert?
   *Detaillierte Darlegung der Strafzumessung:*
   * Einsatzstrafe für das Hauptdelikt (objektive und subjektive Tatschwere).
   * Asperation der Nebendelikte.
   * **Strafminderungen:** Wurde ein **Geständnisrabatt** gewährt (in welchem Umfang)? Wurde eine **verminderte Schuldfähigkeit** (Art. 19 Abs. 2 StGB) berücksichtigt? Wurde das **Beschleunigungsgebot** verletzt (wieviele Monate Abzug)?
   * **Definitive Endstrafe:** Das vom Berufungsgericht definitiv ausgefällte Strafmass, der Vollzug und die Entscheidung über die Landesverweisung.

---

## 6. Workflow zur Datenbank-Eintragung (Python/Django)

Eintragungen immer über `manage.py shell` mit Heredoc ausführen (vermeidet Shell-Escaping-Probleme bei Apostrophen und Anführungszeichen):

```bash
source .venv/bin/activate && python manage.py shell << 'EOF'
from datetime import date
from database.models import GewaltdeliktUrteil, Kanton, Besonderheiten

# 1. Duplikat-Check
fall_nr = "SK 22 999"
if GewaltdeliktUrteil.objects.filter(fall_nr=fall_nr).exists():
    print(f"WARNUNG: {fall_nr} existiert bereits!")
else:
    u = GewaltdeliktUrteil(
        fall_nr=fall_nr,
        url_link="https://entscheidsuche.ch/docs/...",
        gericht="Regionalgericht Bern-Mittelland",
        urteilsdatum=date(2022, 5, 15),
        kanton=Kanton.objects.get(abk="BE"),
        geschlecht="0",
        nationalitaet="1",
        vorbestraft=True,
        vorbestraft_einschlaegig=False,
        hauptdelikt="schwere Körperverletzung",
        versuch=True,
        tatmittel="Messer/Stichwaffe",
        vorsatzform="eventualvorsatz",
        waffe_gefaehrlicher_gegenstand=True,
        bandenmaessig=False,
        besondere_gefaehrlichkeit=False,
        lebensgefahr=True,
        mehrfach=False,
        opferzahl=1,
        taeter_opfer_beziehung="Unbekannte",
        verletzungsfolge="erheblich",
        angegriffenes_koerperteil="Kopf/Hals",
        substanzeinfluss="Alkohol",
        deliktsscore_uebrige_delikte=2,
        hauptsanktion="0",
        freiheitsstrafe_in_monaten=24,
        anzahl_tagessaetze=0,
        vollzug="0",
        verfahrensart="0",
        in_ki_modell=True,
        kurzsachverhalt="...",
        zusammenfassung="...",
    )
    u.full_clean()
    u.save()

    # M2M Besonderheiten NACH dem Speichern setzen
    u.besonderheiten.set(Besonderheiten.objects.filter(name__in=["Versuch", "Geständnisrabatt"]))
    u.save()
    print(f"Erfolgreich angelegt mit ID {u.pk}!")
EOF
```

---

## 7. Abschluss-Checkliste

Vor dem Beenden jedes Falls diese Punkte abhaken:

- [ ] **Schuldspruch zum Hauptdelikt** übersteht die Berufung in seiner Qualifikation unverändert.
- [ ] **Modellabgrenzung** beachtet (keine Sexualdelikte in `GewaltdeliktUrteil`).
- [ ] **Duplikat-Check** auf `fall_nr` durchgeführt.
- [ ] **Vorinstanz-Werte in Feldern:** `gericht`, `urteilsdatum`, `hauptsanktion`, `freiheitsstrafe_in_monaten`, `anzahl_tagessaetze`, `vollzug` bilden exakt das erstinstanzliche Dispositiv ab.
- [ ] **Dispositiv-Abgleich:** Berufungsdispositiv Satz für Satz mit der Vorinstanz verglichen (Strafänderungen, Vollzug, Landesverweisung).
- [ ] **Geständnisrabatt:** Geprüft, ob Geständnis/Reue strafmindernd gewürdigt wurde → falls ja: `besonderheiten` enthält `'Geständnisrabatt'` und Zusammenfassung beziffert den Rabatt.
- [ ] **Verminderte Schuldfähigkeit:** Geprüft, ob Art. 19 Abs. 2 StGB angewandt wurde → falls ja: `besonderheiten` enthält `'verminderte Schuldfähigkeit'`.
- [ ] **Tatmittel-Präzision:** Abgebrochene Glasflaschen/Scherben = `'Messer/Stichwaffe'` (*"auch Glas/Flasche"*); Krücken/Stangen = `'stumpfer Gegenstand'`.
- [ ] **`deliktsscore_uebrige_delikte`** anhand der finalen (post-Berufung) Schuldsprüche berechnet.
- [ ] **FS/TS-Konvention:** Bei Freiheitsstrafe `anzahl_tagessaetze=0`; bei Geldstrafe `freiheitsstrafe_in_monaten=0`.
- [ ] **`full_clean()` vor `save()`** ausgeführt.
- [ ] **`besonderheiten`** nach dem Speichern via `.set(...)` zugewiesen.
- [ ] **`kurzsachverhalt`** prägnant (1–2 Sätze) im Aktiv verfasst, nur gerichtlich festgestellter Sachverhalt — keine Prozess-/Verteidigungsangaben (siehe Abschnitt 5).
- [ ] **`zusammenfassung`** ausführlich (1500–3000 Zeichen), vollständig strukturiert (Sachverhalt, Vorinstanz, Berufung, Strafzumessung/Rabatte, Endentscheid) und **ohne vorzeitigen Abbruch** abgeschlossen.
