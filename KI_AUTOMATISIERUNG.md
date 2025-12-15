# 🤖 KI-gestützte Automatisierung der Urteilserfassung

## Übersicht

Die KI-Automatisierung nutzt Google's Gemini API mit Structured Output, um Gerichtsurteile automatisch zu analysieren und die Formularfelder im Django Admin auszufüllen.

## Features

✅ **Automatisches Ausfüllen** aller Urteilsfelder aus Volltext
✅ **Strukturierte Datenextraktion** mit Pydantic Models
✅ **Validierung** der extrahierten Daten
✅ **Benutzerfreundliche Integration** direkt im Django Admin
✅ **Kontrolle** - Sie überprüfen vor dem Speichern

## Einrichtung

### 1. Google API Key erhalten

1. Besuchen Sie [Google AI Studio](https://ai.google.dev/)
2. Erstellen Sie einen neuen API-Key
3. Kopieren Sie den API-Key

### 2. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env` Datei im Hauptverzeichnis (falls noch nicht vorhanden):

```bash
cp .env.example .env
```

Fügen Sie Ihren Google API Key hinzu:

```env
GOOGLE_API_KEY=ihr-google-api-key-hier
```

### 3. Dependencies installieren

Die notwendigen Packages sind bereits in `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Wichtige Dependencies:**
- `google-genai` - Google Gemini API Client
- `pydantic` - Datenvalidierung und Structured Output

### 4. Static Files sammeln

```bash
python manage.py collectstatic --noinput
```

## Verwendung

### Im Django Admin

1. **Navigieren Sie zum Admin-Bereich:**
   ```
   http://localhost:8000/admin/database/urteil/add/
   ```

2. **Volltext einfügen:**
   - Ganz oben im Formular finden Sie die Sektion "🤖 KI-Assistenz"
   - Fügen Sie den kompletten Urteilstext in die Textarea ein

3. **Auto-Fill aktivieren:**
   - Klicken Sie auf den Button "🤖 Formular automatisch ausfüllen"
   - Warten Sie, während die KI den Text analysiert (ca. 5-15 Sekunden)

4. **Überprüfen und Korrigieren:**
   - Die Felder werden automatisch ausgefüllt und kurz grün markiert
   - Überprüfen Sie alle Felder auf Richtigkeit
   - Korrigieren Sie bei Bedarf

5. **Speichern:**
   - Klicken Sie auf "Speichern" oder "Speichern und weiter bearbeiten"

### Feldsets

Das Formular ist in logische Bereiche unterteilt:

- **🤖 KI-Assistenz** - Volltext-Eingabe
- **Grunddaten** - Fall-Nr., Gericht, Datum
- **Person** - Geschlecht, Nationalität, Vorstrafen
- **Delikt** - Hauptdelikt, Deliktssumme, Modalitäten
- **Sanktion** - Strafe, Vollzug
- **Weitere Informationen** - Zusammenfassung, KI-Modell

## Extrahierte Felder

Die KI extrahiert automatisch folgende Informationen:

### Grunddaten
- `gericht` - Name des Gerichts
- `urteilsdatum` - Datum des Urteils (YYYY-MM-DD)
- `fall_nr` - Geschäftsnummer/Fallnummer
- `url_link` - URL zum PDF (falls im Text erwähnt)

### Personendaten
- `geschlecht` - männlich/weiblich
- `nationalitaet` - Nationalität der beschuldigten Person
- `vorbestraft` - Ist vorbestraft (ja/nein)
- `vorbestraft_einschlaegig` - Einschlägig vorbestraft (ja/nein)

### Deliktinformationen
- `hauptdelikt` - Art des Hauptdelikts (Betrug, Veruntreuung, etc.)
- `deliktssumme` - Schadenssumme in CHF
- `mehrfach` - Mehrfache Begehung (Art. 47 StGB)
- `gewerbsmaessig` - Gewerbsmässige Begehung
- `bandenmaessig` - Bandenmässige Begehung
- `nebenverurteilungsscore` - Score für Nebenverurteilungen

### Sanktionsdaten
- `hauptsanktion` - Freiheitsstrafe/Geldstrafe/Busse
- `freiheitsstrafe_in_monaten` - Dauer in Monaten
- `anzahl_tagessaetze` - Anzahl Tagessätze (bei Geldstrafe)
- `vollzug` - bedingt/teilbedingt/unbedingt
- `zusammenfassung` - Zusammenfassung der Strafzumessungserwägungen

### Weitere Felder
- `in_ki_modell` - Für KI-Modell verwenden (Standard: false)

## Validierung

Die KI-Extraktion beinhaltet automatische Validierung:

### Pflichtfelder
- Gericht, Urteilsdatum, Fall-Nr., Geschlecht, Nationalität
- Hauptdelikt, Hauptsanktion, Vollzug

### Logik-Checks
- ✅ Geschlecht muss 'männlich' oder 'weiblich' sein
- ✅ Hauptsanktion muss eine der gültigen Optionen sein
- ✅ Bei Freiheitsstrafe muss Dauer angegeben werden
- ✅ Bei Geldstrafe müssen Tagessätze angegeben werden
- ✅ Einschlägige Vorstrafe nur wenn vorbestraft

### Warnungen
Falls Validierungswarnungen auftreten, werden diese angezeigt:
- 🟢 **Success** - Alles OK, Felder ausgefüllt
- 🟡 **Warning** - Ausgefüllt, aber bitte überprüfen
- 🔴 **Error** - Fehler, bitte manuell korrigieren

## Technische Details

### Architektur

```
┌─────────────────┐
│  Django Admin   │
│   (Frontend)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ UrteilAdmin     │
│ auto_fill_view  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ urteil_extractor│
│    (Service)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gemini API     │
│ (Structured     │
│   Output)       │
└─────────────────┘
```

### Dateien

**Backend:**
- `database/admin.py` - Custom Admin Form + API Endpoint
- `database/services/urteil_extractor.py` - Service-Layer mit Gemini API
- `database/services/__init__.py` - Package Init

**Frontend:**
- `database/static/admin/js/urteil_auto_fill.js` - JavaScript für Auto-Fill

**Konfiguration:**
- `strafbemessung/settings/base_settings.py` - Django Settings
- `.env` - Umgebungsvariablen (GOOGLE_API_KEY)
- `requirements.txt` - Python Dependencies

### API Endpoint

**URL:** `/admin/database/urteil/auto-fill/`
**Method:** POST
**Authentication:** Django Admin Session (LoginRequired)

**Request:**
```json
{
  "volltext": "Volltext des Urteils..."
}
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "fall_nr": "SB190145",
    "gericht": "Bezirksgericht Zürich",
    "urteilsdatum": "2019-08-15",
    ...
  },
  "message": "Formular erfolgreich ausgefüllt..."
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Fehlermeldung"
}
```

### Pydantic Model

Das `UrteilExtraction` Model definiert die Struktur der extrahierten Daten:

```python
class UrteilExtraction(BaseModel):
    gericht: str
    urteilsdatum: str
    fall_nr: str
    geschlecht: str
    # ... weitere Felder
```

Gemini API nutzt dieses Schema für **Structured Output**, was garantiert, dass die Antwort dem erwarteten Format entspricht.

## Troubleshooting

### "GOOGLE_API_KEY ist nicht konfiguriert"

**Lösung:**
1. Erstellen Sie eine `.env` Datei im Hauptverzeichnis
2. Fügen Sie `GOOGLE_API_KEY=ihr-key` hinzu
3. Starten Sie den Django Server neu

### "Das 'google-genai' Paket ist nicht installiert"

**Lösung:**
```bash
pip install google-genai
```

### "Fehler bei der Verarbeitung"

**Mögliche Ursachen:**
- API Key ungültig oder abgelaufen
- Netzwerkprobleme
- API-Limit erreicht
- Text zu lang (> 100.000 Zeichen)

**Lösung:**
1. Überprüfen Sie Ihren API Key
2. Überprüfen Sie die Internetverbindung
3. Kürzen Sie den Text falls nötig
4. Warten Sie und versuchen Sie es später erneut

### JavaScript funktioniert nicht

**Lösung:**
```bash
# Static Files sammeln
python manage.py collectstatic --noinput

# Server neustarten
python manage.py runserver
```

### Felder werden nicht korrekt ausgefüllt

**Ursache:** Dropdown-Werte stimmen nicht überein

**Lösung:**
- Die KI verwendet die exakten Werte aus den Model-Choices
- Falls ein Feld nicht ausgefüllt wird, überprüfen Sie die Choices im Model
- Passen Sie ggf. die Beschreibungen im Pydantic Model an

## Kosten

**Google Gemini API Pricing:**
- Modell: `gemini-2.0-flash-exp` (experimentell, ggf. kostenlos)
- Input: ~$0.075 pro 1M Tokens (falls kostenpflichtig)
- Output: ~$0.30 pro 1M Tokens (falls kostenpflichtig)

**Geschätzte Kosten pro Urteil:**
- Durchschnittlicher Volltext: ~5.000 Tokens
- Kosten: < $0.001 pro Urteil

**Tipp:** Nutzen Sie die kostenlose Tier so lange verfügbar!

## Erweiterung auf andere Urteilstypen

Die Implementierung kann einfach auf `BetmUrteil` und `SexualdeliktUrteil` erweitert werden:

1. Neues Pydantic Model erstellen (z.B. `BetmUrteilExtraction`)
2. Admin Form anpassen (`BetmUrteilAdminForm`)
3. API Endpoint hinzufügen (`BetmUrteilAdmin.auto_fill_view`)
4. JavaScript kopieren/anpassen

**Hinweis:** Die Struktur ist bereits vorbereitet - kontaktieren Sie mich für die Implementierung!

## Support

Bei Fragen oder Problemen:
1. Überprüfen Sie diese Dokumentation
2. Schauen Sie in die Console (Browser DevTools)
3. Überprüfen Sie die Django Logs

## Changelog

### Version 1.0.0 (2025-12-15)
- ✅ Initiale Implementierung für Urteil (Vermögensdelikte)
- ✅ Google Gemini API Integration mit Structured Output
- ✅ Django Admin Integration
- ✅ Automatische Validierung
- ✅ Benutzerfreundliches UI mit Feedback
