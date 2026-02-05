# MCP Server für Urteilszusammenfassungen

Dieser MCP-Server ermöglicht es Claude und anderen Clients, auf LLM-generierte Zusammenfassungen von Strafurteilen aus der ki-strafzumessung Datenbank zuzugreifen.

**Verfügbar in zwei Varianten:**
- **stdio** (`summary_server.py`) - Für lokale Claude Desktop Integration
- **HTTP** (`http_summary_server.py`) - Öffentlicher Server für jedermann

## Features

### Basis-Tools

- **get_summary**: Ruft eine spezifische Urteilszusammenfassung ab
- **search_summaries**: Durchsucht Zusammenfassungen nach Stichworten
- **list_summaries**: Listet alle verfügbaren Zusammenfassungen auf

### Ähnlichkeitssuche (NEU)

- **find_similar_by_description**: Findet ähnliche Urteile basierend auf einer Freitext-Sachverhaltsbeschreibung
  - Nutzt Keyword-Extraktion und semantische Ähnlichkeit
  - Berechnet Relevanz-Scores basierend auf übereinstimmenden Keywords
  - Zeigt die ähnlichsten Fälle mit Zusammenfassungen

- **find_similar_cases**: Strukturierte Suche nach ähnlichen Urteilen
  - Basiert auf strukturierten Merkmalen (Deliktssumme, Vorstrafen, etc.)
  - Hinweis: Aktuell eingeschränkt verfügbar (verweist auf Web-Anwendung)

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

## Nutzung

### Option A: HTTP-Server (Öffentlich, für jedermann)

Der HTTP-Server ermöglicht es, die MCP-Tools über HTTP/JSON Public API zu nutzen.

#### Lokal starten:

```bash
cd /home/user/ki-strafzumessung
python -m uvicorn mcp_server.http_summary_server:app --host 0.0.0.0 --port 8000
```

Server läuft dann unter: `http://localhost:8000`

**Verfügbare Endpoints:**

- `GET /` - Server-Informationen
- `GET /health` - Health Check
- `GET /docs` - API Dokumentation (Swagger UI)
- `GET /tools` - Liste aller Tools
- `POST /tools/call` - Tool-Aufruf mit JSON Body
- `GET /summary/{judgment_type}/{judgment_id}` - Zusammenfassung abrufen (shortcut)
- `GET /search?q=...&type=...` - Suchfunktion (shortcut)

**Beispiele:**

```bash
# Health Check
curl http://localhost:8000/health

# Zusammenfassung abrufen
curl http://localhost:8000/summary/betm/42

# Suche
curl "http://localhost:8000/search?q=Kokain&type=betm&limit=5"

# Tool-Aufruf (JSON)
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_summary",
    "arguments": {"judgment_type": "betm", "judgment_id": 42}
  }'
```

#### Deployment (Production):

Der Server ist stateless und kann überall deployed werden:

**Heroku:**
```bash
# Procfile
web: python -m uvicorn mcp_server.http_summary_server:app --host 0.0.0.0 --port $PORT
```

**Docker:**
```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r mcp_server/requirements.txt
CMD ["python", "-m", "uvicorn", "mcp_server.http_summary_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**AWS/Google Cloud/DigitalOcean:**
Deployed as standard Python ASGI app (uvicorn)

---

### Option B: Stdio-Server (Lokal mit Claude Desktop)

Für lokale Integration mit Claude Desktop.

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

### Beispiel 4: Ähnliche Fälle per Sachverhaltsbeschreibung finden (NEU)

```
User: Finde ähnliche Urteile zu folgendem Sachverhalt:
Der Angeklagte hat über 2 Jahre hinweg systematisch Kunden getäuscht
und dabei CHF 300'000 veruntreut. Er ist vorbestraft.

Claude verwendet das Tool: find_similar_by_description
- description: "Der Angeklagte hat über 2 Jahre hinweg systematisch
  Kunden getäuscht und dabei CHF 300'000 veruntreut. Er ist vorbestraft."
- case_type: "all"
- limit: 5
```

**Ausgabe:**
- Extrahiert Keywords (getäuscht, kunden, veruntreut, vorbestraft, etc.)
- Findet Urteile mit den meisten Keyword-Übereinstimmungen
- Zeigt Relevanz-Score für jedes Urteil
- Gibt Zusammenfassungen der ähnlichsten Fälle zurück

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

## Sicherheit

### Read-Only Garantie

Der HTTP-Server bietet **garantierten Read-Only Zugriff** auf die Datenbank:

✅ **Schreibvorgänge sind technisch unmöglich:**
- Alle Tools verwenden Django ORM SELECT-Queries (`.get()`, `.filter()`, `.exclude()`)
- Keine `INSERT`, `UPDATE` oder `DELETE` Operationen implementiert
- Django ORM schützt vor SQL Injection
- Keine Raw-SQL Queries

✅ **Datenbankebene (zusätzlich empfohlen):**
```sql
-- Optional: Create read-only database user
CREATE ROLE judgment_reader WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE ki_strafzumessung TO judgment_reader;
GRANT USAGE ON SCHEMA public TO judgment_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO judgment_reader;
```

Dann in `DJANGO_SETTINGS_MODULE` den `judgment_reader` User konfigurieren.

### Öffentlicher Zugriff (CORS)

Der HTTP-Server aktiviert CORS für öffentlichen Zugriff:
- Jeder kann die API aufrufen (keine Authentifizierung nötig)
- CORS erlaubt Requests von überall (`allow_origins=["*"]`)
- Ideal für öffentliche Urteile/Zusammenfassungen
- Keine sensitiven Daten preisgeben!

### Rate-Limiting (Empfohlen für Production)

Für Production sollte Rate-Limiting hinzugefügt werden:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/tools/call")
@limiter.limit("30/minute")  # 30 Requests pro Minute
async def call_tool(request: ToolCallRequest):
    ...
```

## Lizenz

Teil des ki-strafzumessung Projekts.
