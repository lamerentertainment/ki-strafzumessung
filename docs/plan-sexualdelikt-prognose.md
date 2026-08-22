# Strafmass-Prognose für Sexualdelikte (nach Betm-Vorbild)

## Kontext

Die App bietet bisher Strafmass-Prognosen für Vermögensdelikte (`prognose`) und Betm-Delikte (`betm_prognose`): Formular → drei Random-Forest-Modelle aus S3 (Hauptsanktion, Vollzug, Strafmass) → gewichteter KNN für 4 vergleichbare Präjudizien. Für `SexualdeliktUrteil` (36 Datensätze, [models.py:366](database/models.py#L366)) existiert **nichts davon**: kein Formular, keine View, keine Templates, keine trainierten Modelle, keine Feature-Engineering-Helfer. Es muss also neben dem Frontend auch die Trainings-Pipeline (analog `betm_kimodelle_neu_generieren`) gebaut werden, sonst gibt es keine Modelle zum Prognostizieren.

**Getroffene Design-Entscheide** (dem Betm-Vorbild folgend, ohne Schema-Änderungen):
- `SexualdeliktUrteil` hat kein `in_ki_modell`-Feld → Training auf **allen** Datensätzen, keine Migration.
- M2M-Felder (`sexualdelikte_zusaetzliche`, `besonderheiten`) werden multi-hot encodiert (Pendant zur Betm-Substanz-One-Hot-Encodierung) und im Formular als Checkboxen angeboten.
- Präjudizien-Filter: ein strikter Filter „gleiches Hauptdelikt" (Pendant zu `gleiche_kategorie_betm1`), Default an, mit demselben Fehlerpfad bei <4 Treffern.
- Kein eigenes `sexual_dev`-Template; Trainings-Trigger als direkter Link im Dev-Dropdown der Navbar.
- DurationFelder werden als Integer erfasst/trainiert: Deliktsdauer in **Minuten**, Deliktsperiode in **Tagen** (Achtung Feld-Typo `hautpdelikt_deliktsdauer_einfachbegehung`).
- Hauptsanktion-Classifier ist mit 35/36 Freiheitsstrafen degeneriert — wird aus Symmetriegründen trotzdem gebaut (prognostiziert faktisch immer Freiheitsstrafe).

## Branch

`feature/sexualdelikt-prognose` ab `master` (Working Tree clean).

## Schritte

### 1. `database/ai_utils.py` — neue Sektion Sexualdelikt-Pipeline (nach der Betm-Pipeline)

Imports um `SexualdeliktUrteil, Hauptdelikt, Tatmittel, ZusaetzlicheSexualdelikte, Besonderheiten` ergänzen.

- **Feature-Konstanten** (Modulebene, von Training und Prognose gemeinsam genutzt):
  - `SEXUAL_KATEGORIALE_PROGNOSEMERKMALE = ["hauptdelikt", "hauptdelikt_tatmittel", "hauptdelikt_mehrfachbegehung", "hauptdelikt_taeter_opfer_beziehung", "hauptdelikt_opferalter", "hauptdelikt_opfer_vorerfahrung", "geschlecht", "nationalitaet", "vorbestraft", "vorbestraft_einschlaegig"]`
  - `SEXUAL_NUMERISCHE_PROGNOSEMERKMALE = ["hauptdelikt_mehrfachbegehung_anzahl", "deliktsperiode_in_tagen", "deliktsdauer_in_minuten", "deliktsscore_uebrige_delikte"]` (Multi-hot-Spalten werden zur Laufzeit angehängt, analog `liste_aller_ohe_betm_spalten`).
- **`sexualurteile_multihot_encoding(pd_df)`** (Pendant zu `betmurteile_onehotencoding`, [ai_utils.py:1603](database/ai_utils.py#L1603)): pro `ZusaetzlicheSexualdelikte`-Wert Spalte `zusatzdelikt_{name}`, pro `Besonderheiten`-Wert `besonderheit_{name}` (0/1), befüllt über die M2M-Through-Tabellen (`SexualdeliktUrteil.sexualdelikte_zusaetzliche.through.objects.values()`), solange der df-Index noch die `id` ist. Rückgabe `(pd_df, liste_aller_multihot_spalten)`. Kein groupby nötig (eine Zeile pro Urteil).
- **`sexual_urteile_dataframe_erzeugen()`** (Pendant zu `betm_urteile_dataframe_erzeugen`, [ai_utils.py:1515](database/ai_utils.py#L1515)):
  1. `pd.DataFrame.from_records(SexualdeliktUrteil.objects.values(), index="id")` (Modell hat keinen `pandas`-Manager — bewusst kein Modell-Change).
  2. FK-IDs → Namen mappen (`hauptdelikt_id`, `hauptdelikt_tatmittel_id`).
  3. Multi-hot-Spalten anhängen.
  4. Codes mit bestehendem `urteilcodes_aufloesen` ([ai_utils.py:1557](database/ai_utils.py#L1557)) in Klartext auflösen (geschlecht, nationalitaet, hauptsanktion, vollzug) — die Prognose-View muss dieselben Klartext-Strings erzeugen.
  5. Durations konvertieren: `deliktsperiode_in_tagen` (`.days`), `deliktsdauer_in_minuten` (`.total_seconds()/60`), aus `hauptdelikt_mehrfachbegehung_deliktsperiode` bzw. `hautpdelikt_deliktsdauer_einfachbegehung`.
  6. Fehlende Numerik mit bestehendem `betmurteile_fehlende_werte_auffuellen(df, spalten_mit_fehlenden_werten=...)` ([ai_utils.py:1670](database/ai_utils.py#L1670)) mit 1 füllen (identisch Training/Prognose).
  7. Index auf `fall_nr` setzen (KNN-Teil liest Nachbarn über den Index als `fall_nr` zurück).
- **`sexual_prognosemerkmale_preprocessen(df)`**: Encoder `encoders/sexual_encoder.pkl` via `kimodell_von_pickle_file_aus_aws_bucket_laden` laden, Featurelisten aus `KIModelPickleFile "sexual_rf_classifier_vollzugsart".prognoseleistung_dict` lesen, transform + concat wie in der Betm-View ([views.py:545-572](database/views.py#L545-L572)) — einmal zentral statt dupliziert.
- **`sexual_nachbarobjekt_mit_sanktionsbewertung_anreichern(...)`** (Spiegel von `betm_nachbarobjekt_mit_sanktionsbewertung_anreichern`, [ai_utils.py:887](database/ai_utils.py#L887)): 1-Zeilen-dict aus dem Urteilsobjekt (FK-Namen, dekodierte Codes, Durations→Minuten/Tage, None→1, Multi-hot 0/1), preprocessen, drei Predictions, Prognosebereich + bestehendes `sanktionsbewertungs_string_erstellen` ([ai_utils.py:1064](database/ai_utils.py#L1064)) wiederverwenden.

### 2. `database/forms.py` — `SexualdeliktUrteilsEckpunkteAbfrageFormular`

Als `forms.Form` nach dem Betm-Formular; alle Felder mit `template_name="database/includes/prognose_form_field.html"`:
- `hauptdelikt` / `hauptdelikt_tatmittel`: `ModelChoiceField` mit auf vorkommende Werte eingeschränktem Queryset (`Hauptdelikt.objects.filter(hauptdelikt__isnull=False).distinct()` — verhindert `OneHotEncoder`-Fehler bei im Training unbekannten Kategorien).
- Booleans (`required=False`): `hauptdelikt_mehrfachbegehung`, `vorbestraft`, `vorbestraft_einschlaegig`, Filter-Toggle `gleiches_hauptdelikt` (initial True).
- Integers (`required=False`): `hauptdelikt_mehrfachbegehung_anzahl`, `deliktsperiode_in_tagen`, `deliktsdauer_in_minuten` (initial 30), `deliktsscore_uebrige_delikte`.
- ChoiceFields aus den Modell-Choices: `hauptdelikt_taeter_opfer_beziehung`, `hauptdelikt_opferalter`, `hauptdelikt_opfer_vorerfahrung`, `geschlecht`, `nationalitaet`.
- `ModelMultipleChoiceField` + `CheckboxSelectMultiple` (`required=False`): `sexualdelikte_zusaetzliche`, `besonderheiten`.

### 3. `database/views.py` — zwei neue Views

- **`sexual_prognose(request)`** (nach `betm_prognose`, Struktur 1:1 von [views.py:455-925](database/views.py#L455-L925), aber ohne Substanz-Aggregation):
  1. Formulareingaben → 1-Zeilen-dict (FK→`.name`, Codes→Klartext identisch zu `urteilcodes_aufloesen`, None→1) + Multi-hot-Spalten aus den M2M-Auswahlen.
  2. `sexual_prognosemerkmale_preprocessen` (try/except `ValueError` → deutsche Fehlermeldung bei unbekannter Kategorie).
  3. Drei S3-Modelle laden (`pickles/sexual_rf_classifier_sanktion.pkl`, `pickles/sexual_rf_classifier_vollzugsart.pkl`, `pickles/sexual_rf_regressor_strafmass.pkl`) und prognostizieren.
  4. Gewichteter KNN wie Betm ([views.py:611-721](database/views.py#L611-L721)): `sexual_urteile_dataframe_erzeugen`, `onehotx_und_y_erstellen_from_dataframe`, `y_strafmass` mit `anzahl_tagessaetze/30`-Fallback, MinMaxScaler, Gewichte aus `prognoseleistung_dict["merkmalswichtigkeit_fuer_prognose_strafmass"]` des Regressors, `KNeighborsRegressor(n_neighbors=min(len(df), 200))`.
  5. Filter `gleiches_hauptdelikt` strikt anwenden; bei <4 Treffern `praejudizien_error_message` wie Betm-Fehlerpfad ([views.py:763-795](database/views.py#L763-L795)).
  6. Top-4 Nachbarn anreichern + innere `differenzengenerator`-Funktion: `entsprechung_hauptdelikt/_tatmittel/_mehrfachbegehung/_taeter_opfer_beziehung/_opferalter/_vorbestraft_einschlaegig`, Diffs für Anzahl/Deliktsperiode (Tage)/Deliktsdauer (Minuten)/Deliktsscore (None→0), `vergleichbarkeitsscore` mit identischer Formel inkl. Zweitpass-KNN ([views.py:865-887](database/views.py#L865-L887)).
- **`sexual_kimodelle_neu_generieren(request)`** (`@login_required`, Spiegel von [views.py:978-1184](database/views.py#L978-L1184)):
  - Drei Estimatoren mit identischen Hyperparametern (`oob_score=True`): Classifier Hauptsanktion, Classifier Vollzug, Regressor Strafmass (mit Tagessatz-Fallback).
  - `prognoseleistung_dict` je Modell: OOB-Score, Merkmalswichtigkeiten (Multi-hot-Spalten via `merkmale_in_merkmalswichtigkeitsliste_zusammenfassen` zu „zusätzliche Sexualdelikte" bzw. „Besonderheiten" zusammenfassen — `neuer_merkmalsname` explizit setzen, Default ist „Menge Betäubungsmittel"); zwingend `liste_kategoriale_prognosemerkmale`/`liste_numerische_prognosemerkmale` in jedes dict; ins Regressor-dict die unzusammengefasste `merkmalswichtigkeit_fuer_prognose_strafmass` (KNN-Gewichte).
  - Persistenz via `ki_modell_als_pickle_file_speichern`; Encoder auf dem Vollzugs-`KIModelPickleFile` speichern wie [views.py:1174-1179](database/views.py#L1174-L1179) (→ `encoders/sexual_encoder.pkl`).
  - `messages.success(...)` + Redirect auf `sexual_prognose` (kein eigenes Dev-Template).

### 4. `database/urls.py` + `includes/navbar.html`

- Routen `sexual_prognose` und `sexual_kimodelle_neu_generieren` registrieren.
- Navbar: „bei Sexualdelikt" im Dropdown „Sanktionsprognose und Präjudizen" ([navbar.html:19](database/templates/database/includes/navbar.html#L19)); Trainings-Link „Sexualdelikt KI-Modelle neu generieren" im Superuser-Dev-Dropdown ([navbar.html:58](database/templates/database/includes/navbar.html#L58)).

### 5. Templates

- **`database/templates/database/sexual_prognose.html`**: Struktur von `betm_prognose.html` kopieren. Collapse-Formular: links Legenden „Schuldspruch/Dispositiv" (Hauptdelikt, Tatmittel, Mehrfachbegehung + Anzahl, Deliktsperiode, Deliktsdauer, Deliktsscore) und „Strafzumessungsfaktoren" (Beziehung, Opferalter, Vorerfahrung, Geschlecht, Nationalität, Vorstrafen); rechts „zusätzliche Sexualdelikte", „Besonderheiten" (Checkboxen), „Präjudizien filtern". Vorhersage-Block mit den bestehenden `prognoseformatierung`-Filtern; Präjudizien 2×2-Grid + `praejudizien_error_message`-Alert.
- **`database/templates/database/includes/sexual_nachbar.html`** (Spiegel von `betm_nachbar.html`): Entsprechungs-Zeilen (grün/rot) für Hauptdelikt/Tatmittel/Mehrfachbegehung/Beziehung/Opferalter/einschlägige Vorstrafe, Differenz-Zellen für die vier numerischen Werte, Listen der M2M-Werte, Sanktionszeile + KI-Sanktionsbewertung + Vergleichbarkeitsscore-Badge, Zusammenfassung.

## Verifikation

1. `python manage.py check`.
2. Shell-Smoke-Test: `sexual_urteile_dataframe_erzeugen()` → 36 Zeilen, 16 Multi-hot-Spalten, keine NaN in Feature-Spalten.
3. `runserver`, als Superuser `/sexual_kimodelle_neu_generieren` aufrufen (**muss vor der ersten Prognose laufen** — erzeugt Pickles/Encoder in S3 und die `KIModelPickleFile`-Einträge).
4. `/sexual_prognose` end-to-end: Default-Eingabe absenden, Vorhersage-Block und 4 Nachbarkarten prüfen; Filter-Fehlerpfad mit seltenem Hauptdelikt provozieren; Filter deaktiviert erneut testen.

## Risiken (akzeptiert)

- 36 Samples → verrauschte OOB-Scores/Wichtigkeiten; Architektur bewusst Betm-identisch.
- Hauptsanktion-Classifier degeneriert (35/36 Freiheitsstrafe); Geldstrafen-Zweig der Templates bleibt aus Symmetriegründen drin.
- Vergleichbarkeitsscore-Formel `1 − dist/(max_dist/20)` kann negativ werden — bekannte Betm-Eigenheit, aus Konsistenz gespiegelt.
