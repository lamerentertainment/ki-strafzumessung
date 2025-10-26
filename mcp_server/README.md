# MCP Server für Urteilszusammenfassungen

Dieser MCP-Server ermöglicht es Claude, auf LLM-generierte Zusammenfassungen von Strafurteilen aus der ki-strafzumessung Datenbank zuzugreifen.

## Features

- **get_summary**: Ruft eine spezifische Urteilszusammenfassung ab
- **search_summaries**: Durchsucht Zusammenfassungen nach Stichworten
- **list_summaries**: Listet alle verfügbaren Zusammenfassungen auf

Unterstützte Urteilstypen:
- `wirtschaft` - Wirtschaftskriminalität (Urteil Model)
- `betm` - Betäubungsmitteldelikte (BetmUrteil Model)
- `sexual` - Sexualdelikte (SexualdeliktUrteil Model)

## Installation

### 1. MCP Dependencies installieren

```bash
cd /home/user/ki-strafzumessung/mcp_server
pip install -r requirements.txt
```

**Hinweis:** Falls Sie ein virtuelles Environment für das Hauptprojekt verwenden, aktivieren Sie dieses zuerst:

```bash
# Falls vorhanden
source /pfad/zu/venv/bin/activate
pip install -r requirements.txt
```

### 2. Claude Desktop konfigurieren

Bearbeiten Sie die Claude Desktop Konfigurationsdatei:

**Linux:**
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

**macOS:**
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

Fügen Sie folgende Konfiguration hinzu:

```json
{
  "mcpServers": {
    "judgment-summaries": {
      "command": "python3",
      "args": ["/home/user/ki-strafzumessung/mcp_server/summary_server.py"],
      "env": {
        "DJANGO_SETTINGS_MODULE": "strafzumessung.settings",
        "PYTHONPATH": "/home/user/ki-strafzumessung"
      }
    }
  }
}
```

**Wichtig:** Passen Sie die Pfade an Ihre Installation an!

Falls Sie ein virtuelles Environment verwenden:

```json
{
  "mcpServers": {
    "judgment-summaries": {
      "command": "/pfad/zu/venv/bin/python",
      "args": ["/home/user/ki-strafzumessung/mcp_server/summary_server.py"],
      "env": {
        "DJANGO_SETTINGS_MODULE": "strafzumessung.settings",
        "PYTHONPATH": "/home/user/ki-strafzumessung"
      }
    }
  }
}
```

### 3. Claude Desktop neu starten

Starten Sie Claude Desktop komplett neu, damit die neue Konfiguration geladen wird.

## Verwendung

### Beispiel 1: Spezifische Zusammenfassung abrufen

```
User: Zeige mir die Zusammenfassung von Betäubungsmittel-Urteil mit ID 42

Claude verwendet das Tool: get_summary
- judgment_type: "betm"
- judgment_id: 42
```

### Beispiel 2: Suche nach Stichworten

```
User: Suche nach Urteilen über Kokain

Claude verwendet das Tool: search_summaries
- query: "Kokain"
- judgment_type: "betm"
- limit: 10
```

### Beispiel 3: Alle Zusammenfassungen auflisten

```
User: Liste alle Sexual-Urteile mit Zusammenfassungen auf

Claude verwendet das Tool: list_summaries
- judgment_type: "sexual"
- limit: 50
```

## Verfügbare Tools im Detail

### 1. get_summary

Ruft eine spezifische Urteilszusammenfassung ab.

**Parameter:**
- `judgment_type` (required): `"wirtschaft"`, `"betm"` oder `"sexual"`
- `judgment_id` (required): Datenbank-ID des Urteils (Integer)

**Beispiel:**
```json
{
  "judgment_type": "betm",
  "judgment_id": 123
}
```

**Ausgabe:**
- Metadaten (Fall-Nr, Datum, Deliktssumme/Rolle, etc.)
- Vollständige Zusammenfassung der Strafzumessung
- LLM-generiert Hinweis

### 2. search_summaries

Durchsucht alle Zusammenfassungen nach einem Suchbegriff.

**Parameter:**
- `query` (required): Suchbegriff (String)
- `judgment_type` (optional): Filter nach Typ, default: `"all"`
- `limit` (optional): Max. Ergebnisse, default: 10 (1-100)

**Beispiel:**
```json
{
  "query": "Bewährung",
  "judgment_type": "all",
  "limit": 20
}
```

**Ausgabe:**
- Liste der gefundenen Urteile
- Metadaten für jedes Urteil
- Gekürzte Vorschau (300 Zeichen) der Zusammenfassung

### 3. list_summaries

Listet alle verfügbaren Zusammenfassungen auf.

**Parameter:**
- `judgment_type` (optional): Filter nach Typ, default: `"all"`
- `limit` (optional): Max. Ergebnisse, default: 50 (1-500)

**Beispiel:**
```json
{
  "judgment_type": "wirtschaft",
  "limit": 100
}
```

**Ausgabe:**
- Gruppierte Liste nach Urteilstyp
- ID, Fall-Nr, Datum für jedes Urteil
- Zusätzliche Info (Deliktssumme, Rolle, etc.)

## Troubleshooting

### MCP-Server wird nicht erkannt

**Problem:** Claude zeigt keine MCP-Tools an.

**Lösung:**
1. Prüfen Sie die Konfigurationsdatei auf Syntaxfehler (JSON-Format)
2. Stellen Sie sicher, dass alle Pfade absolut und korrekt sind
3. Claude Desktop komplett neu starten
4. Logs prüfen (siehe unten)

### Django Import-Fehler

**Problem:** `ModuleNotFoundError: No module named 'database'`

**Lösung:**
1. Prüfen Sie `PYTHONPATH` in der Konfiguration
2. Stellen Sie sicher, dass `DJANGO_SETTINGS_MODULE` korrekt ist
3. Falls virtuelles Environment: Verwenden Sie den venv-Python-Interpreter

### Datenbank-Verbindung fehlgeschlagen

**Problem:** `django.db.utils.OperationalError`

**Lösung:**
1. Prüfen Sie die Django-Datenbank-Einstellungen in `strafzumessung/settings.py`
2. Stellen Sie sicher, dass PostgreSQL läuft
3. Verifizieren Sie Datenbankzugangsdaten

### Keine Zusammenfassungen gefunden

**Problem:** Tool liefert "Keine Zusammenfassung vorhanden"

**Erklärung:** Nicht alle Urteile haben eine `zusammenfassung` in der Datenbank.

**Lösung:**
1. Verwenden Sie `list_summaries` um verfügbare Zusammenfassungen zu sehen
2. Prüfen Sie in Django Admin, welche Urteile Zusammenfassungen haben

## Server manuell testen

Sie können den MCP-Server auch manuell testen:

```bash
cd /home/user/ki-strafzumessung
python3 mcp_server/summary_server.py
```

Der Server wartet dann auf stdin-Input im MCP-Protokoll-Format.

**Einfacher Test mit Django Shell:**

```bash
cd /home/user/ki-strafzumessung
python manage.py shell
```

```python
from database.models import BetmUrteil

# Zeige Urteile mit Zusammenfassungen
urteile_mit_summary = BetmUrteil.objects.exclude(zusammenfassung="")
print(f"Anzahl: {urteile_mit_summary.count()}")

# Zeige erste Zusammenfassung
if urteile_mit_summary.exists():
    urteil = urteile_mit_summary.first()
    print(f"ID: {urteil.pk}")
    print(f"Zusammenfassung: {urteil.zusammenfassung[:200]}...")
```

## Logs ansehen

Falls der Server nicht funktioniert, prüfen Sie die Claude Desktop Logs:

**Linux:**
```bash
tail -f ~/.config/Claude/logs/mcp*.log
```

**macOS:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

## Entwicklung & Anpassungen

### Server erweitern

Neue Tools können in `summary_server.py` hinzugefügt werden:

1. Tool in `handle_list_tools()` registrieren
2. Handler-Funktion implementieren
3. In `handle_call_tool()` verknüpfen

### Weitere Urteilstypen hinzufügen

Falls neue Urteilsmodelle hinzukommen:

1. Model-Import in `summary_server.py` hinzufügen
2. In `get_model_by_type()` mappieren
3. In `format_judgment_metadata()` Metadaten definieren
4. Enum in Tool-Schemas erweitern

## Technische Details

- **Protokoll:** MCP (Model Context Protocol) via stdio
- **Transport:** Standard Input/Output
- **Django Version:** 4.2+
- **Datenbank:** PostgreSQL
- **Python:** 3.8+

## Support

Bei Problemen:
1. Prüfen Sie diese README
2. Testen Sie den Server manuell
3. Prüfen Sie Claude Desktop Logs
4. Verifizieren Sie Django-Setup mit `python manage.py check`

## Lizenz

Teil des ki-strafzumessung Projekts.
