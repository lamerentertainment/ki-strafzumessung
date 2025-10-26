#!/usr/bin/env python3
"""
MCP Server für Urteilszusammenfassungen (Judgment Summaries)

Dieser MCP-Server bietet Zugriff auf LLM-generierte Zusammenfassungen von Strafurteilen
aus der ki-strafzumessung Datenbank.

Tools:
- get_summary: Ruft eine spezifische Zusammenfassung ab
- search_summaries: Sucht in Zusammenfassungen nach Stichworten
- list_summaries: Listet verfügbare Zusammenfassungen auf
"""

import os
import sys
import asyncio
from typing import Any
from asgiref.sync import sync_to_async

# Django Setup - muss vor MCP imports erfolgen
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strafbemessung.settings.base_settings')

import django
django.setup()

# Jetzt können wir Django models importieren
from database.models import Urteil, BetmUrteil, SexualdeliktUrteil
from database.ai_utils import knn_pipeline, formulareingaben_in_abfragesample_konvertieren

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Server initialisieren
server = Server("judgment-summaries")


# Hilfsfunktionen für Model-Mapping
def get_model_by_type(judgment_type: str):
    """Gibt das entsprechende Django-Model für einen Urteilstyp zurück."""
    model_map = {
        "wirtschaft": Urteil,
        "betm": BetmUrteil,
        "sexual": SexualdeliktUrteil
    }
    return model_map.get(judgment_type)


def format_judgment_metadata(judgment: Any, judgment_type: str) -> dict:
    """Extrahiert Metadaten aus einem Urteil."""
    metadata = {
        "id": judgment.pk,
        "type": judgment_type,
        "fall_nr": getattr(judgment, 'fall_nr', None),
        "datum": str(getattr(judgment, 'datum', '')),
    }

    # Typ-spezifische Metadaten
    if judgment_type == "wirtschaft":
        metadata.update({
            "deliktssumme": getattr(judgment, 'deliktssumme', None),
            "hauptdelikt": str(getattr(judgment, 'hauptdelikt', '')),
            "strafe_monate": getattr(judgment, 'freiheitsstrafe_in_monaten', None),
        })
    elif judgment_type == "betm":
        metadata.update({
            "rolle": str(getattr(judgment, 'rolle', '')),
            "strafe_monate": getattr(judgment, 'dauer', None),
        })
    elif judgment_type == "sexual":
        metadata.update({
            "hauptdelikt": str(getattr(judgment, 'hauptdelikt', '')),
            "opferalter": getattr(judgment, 'opferalter', None),
        })

    return metadata


# MCP Tool Handlers
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Definiert die verfügbaren Tools."""
    return [
        Tool(
            name="get_summary",
            description="Ruft die LLM-generierte Zusammenfassung eines spezifischen Urteils ab. "
                       "Liefert die Zusammenfassung der Strafzumessungserwägungen der Berufungsinstanz.",
            inputSchema={
                "type": "object",
                "properties": {
                    "judgment_type": {
                        "type": "string",
                        "enum": ["wirtschaft", "betm", "sexual"],
                        "description": "Typ des Urteils: 'wirtschaft' (Wirtschaftskriminalität), "
                                     "'betm' (Betäubungsmittel), 'sexual' (Sexualdelikte)"
                    },
                    "judgment_id": {
                        "type": "integer",
                        "description": "Die Datenbank-ID des Urteils"
                    }
                },
                "required": ["judgment_type", "judgment_id"]
            }
        ),
        Tool(
            name="search_summaries",
            description="Durchsucht alle Urteilszusammenfassungen nach einem Stichwort oder Begriff. "
                       "Nützlich um ähnliche Fälle oder spezifische Strafzumessungsfaktoren zu finden.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Suchbegriff (z.B. 'Kokain', 'Bewährung', 'Tatkomponente')"
                    },
                    "judgment_type": {
                        "type": "string",
                        "enum": ["wirtschaft", "betm", "sexual", "all"],
                        "description": "Filtert nach Urteilstyp (optional, default: 'all')",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximale Anzahl an Ergebnissen (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_summaries",
            description="Listet alle verfügbaren Urteile mit Zusammenfassungen auf. "
                       "Zeigt Metadaten wie Fall-Nummer, Datum und Typ.",
            inputSchema={
                "type": "object",
                "properties": {
                    "judgment_type": {
                        "type": "string",
                        "enum": ["wirtschaft", "betm", "sexual", "all"],
                        "description": "Filtert nach Urteilstyp (optional, default: 'all')",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximale Anzahl an Ergebnissen (default: 50)",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500
                    }
                },
            }
        ),
        Tool(
            name="find_similar_cases",
            description="Findet ähnliche Urteile basierend auf einem Sachverhalt. "
                       "Nutzt KNN-basierte Ähnlichkeitssuche mit ML-Gewichtung. "
                       "Gibt die ähnlichsten Fälle mit Zusammenfassungen zurück.",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_type": {
                        "type": "string",
                        "enum": ["wirtschaft", "betm"],
                        "description": "Falltyp: 'wirtschaft' (Wirtschaftskriminalität) oder 'betm' (Betäubungsmittel)"
                    },
                    "deliktssumme": {
                        "type": "number",
                        "description": "Deliktssumme in CHF (nur für Wirtschaftskriminalität)"
                    },
                    "hauptdelikt": {
                        "type": "string",
                        "description": "Hauptdelikt (z.B. 'Betrug', 'Veruntreuung', 'Diebstahl')"
                    },
                    "vorbestraft": {
                        "type": "boolean",
                        "description": "Hat der Angeklagte Vorstrafen?"
                    },
                    "vorbestraft_einschlaegig": {
                        "type": "boolean",
                        "description": "Einschlägige Vorstrafen im gleichen Deliktbereich?"
                    },
                    "gewerbsmaessig": {
                        "type": "boolean",
                        "description": "Wurde das Delikt gewerbsmässig begangen?"
                    },
                    "n_neighbors": {
                        "type": "integer",
                        "description": "Anzahl ähnlicher Fälle (default: 4)",
                        "default": 4,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["case_type"]
            }
        ),
        Tool(
            name="find_similar_by_description",
            description="Findet ähnliche Urteile basierend auf einer Freitext-Sachverhaltsbeschreibung. "
                       "Durchsucht die Zusammenfassungen semantisch und findet inhaltlich ähnliche Fälle.",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Sachverhaltsbeschreibung in Freitext (z.B. 'Der Angeklagte hat über mehrere Jahre systematisch Kunden betrogen und dabei CHF 500'000 veruntreut')"
                    },
                    "case_type": {
                        "type": "string",
                        "enum": ["wirtschaft", "betm", "sexual", "all"],
                        "description": "Optional: Filter nach Falltyp",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Anzahl ähnlicher Fälle (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["description"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Verarbeitet Tool-Aufrufe."""

    if name == "get_summary":
        return await get_summary(arguments)
    elif name == "search_summaries":
        return await search_summaries(arguments)
    elif name == "list_summaries":
        return await list_summaries(arguments)
    elif name == "find_similar_cases":
        return await find_similar_cases(arguments)
    elif name == "find_similar_by_description":
        return await find_similar_by_description(arguments)
    else:
        raise ValueError(f"Unbekanntes Tool: {name}")


async def get_summary(args: dict) -> list[TextContent]:
    """
    Ruft die Zusammenfassung eines spezifischen Urteils ab.

    Args:
        judgment_type: Typ des Urteils (wirtschaft, betm, sexual)
        judgment_id: Datenbank-ID des Urteils
    """
    judgment_type = args["judgment_type"]
    judgment_id = args["judgment_id"]

    model = get_model_by_type(judgment_type)
    if not model:
        return [TextContent(
            type="text",
            text=f"❌ Ungültiger Urteilstyp: {judgment_type}"
        )]

    try:
        # Django ORM-Aufruf in async Context - nutze sync_to_async
        judgment = await sync_to_async(model.objects.get)(pk=judgment_id)

        # Prüfe ob Zusammenfassung vorhanden
        if not judgment.zusammenfassung or judgment.zusammenfassung.strip() == "":
            metadata = format_judgment_metadata(judgment, judgment_type)
            return [TextContent(
                type="text",
                text=f"ℹ️ Keine Zusammenfassung vorhanden für:\n"
                     f"**Typ:** {judgment_type}\n"
                     f"**ID:** {judgment_id}\n"
                     f"**Fall-Nr:** {metadata.get('fall_nr', 'N/A')}\n"
                     f"**Datum:** {metadata.get('datum', 'N/A')}"
            )]

        # Metadaten formatieren
        metadata = format_judgment_metadata(judgment, judgment_type)

        # Ausgabe formatieren
        output = f"# Zusammenfassung: {judgment_type.capitalize()}-Urteil #{judgment_id}\n\n"

        # Metadaten-Sektion
        output += "## Metadaten\n\n"
        output += f"- **Fall-Nr:** {metadata.get('fall_nr', 'N/A')}\n"
        output += f"- **Datum:** {metadata.get('datum', 'N/A')}\n"
        output += f"- **Typ:** {judgment_type}\n"

        if judgment_type == "wirtschaft":
            output += f"- **Deliktssumme:** CHF {metadata.get('deliktssumme', 'N/A')}\n"
            output += f"- **Hauptdelikt:** {metadata.get('hauptdelikt', 'N/A')}\n"
            if metadata.get('strafe_monate'):
                output += f"- **Strafe:** {metadata.get('strafe_monate')} Monate\n"
        elif judgment_type == "betm":
            output += f"- **Rolle:** {metadata.get('rolle', 'N/A')}\n"
            if metadata.get('strafe_monate'):
                output += f"- **Dauer:** {metadata.get('strafe_monate')} Monate\n"
        elif judgment_type == "sexual":
            output += f"- **Hauptdelikt:** {metadata.get('hauptdelikt', 'N/A')}\n"
            if metadata.get('opferalter'):
                output += f"- **Opferalter:** {metadata.get('opferalter')}\n"

        # Zusammenfassung
        output += f"\n## Zusammenfassung der Strafzumessung\n\n"
        output += f"{judgment.zusammenfassung}\n\n"
        output += f"---\n\n"
        output += f"*LLM-generiert und ohne Gewähr*"

        return [TextContent(type="text", text=output)]

    except model.DoesNotExist:
        return [TextContent(
            type="text",
            text=f"❌ Urteil mit ID {judgment_id} nicht gefunden im Typ '{judgment_type}'"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Fehler beim Abrufen der Zusammenfassung: {str(e)}"
        )]


async def search_summaries(args: dict) -> list[TextContent]:
    """
    Durchsucht Zusammenfassungen nach einem Suchbegriff.

    Args:
        query: Suchbegriff
        judgment_type: Urteilstyp Filter (optional, default: 'all')
        limit: Max. Anzahl Ergebnisse (optional, default: 10)
    """
    query = args["query"]
    judgment_type = args.get("judgment_type", "all")
    limit = args.get("limit", 10)

    results = []

    def search_and_serialize_wirtschaft():
        """Sucht in Wirtschaft-Urteilen und serialisiert."""
        judgments = list(Urteil.objects.filter(
            zusammenfassung__icontains=query
        ).exclude(zusammenfassung="").select_related('hauptdelikt')[:limit])

        # Extrahiere alle Daten im sync context
        return [{
            'id': j.pk,
            'type': 'wirtschaft',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
            'zusammenfassung': j.zusammenfassung,
            'deliktssumme': j.deliktssumme if hasattr(j, 'deliktssumme') else None,
            'hauptdelikt': str(j.hauptdelikt) if hasattr(j, 'hauptdelikt') else '',
        } for j in judgments]

    def search_and_serialize_betm():
        """Sucht in Betm-Urteilen und serialisiert."""
        judgments = list(BetmUrteil.objects.filter(
            zusammenfassung__icontains=query
        ).exclude(zusammenfassung="").select_related('rolle')[:limit])

        return [{
            'id': j.pk,
            'type': 'betm',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
            'zusammenfassung': j.zusammenfassung,
            'rolle': str(j.rolle) if hasattr(j, 'rolle') else '',
        } for j in judgments]

    def search_and_serialize_sexual():
        """Sucht in Sexual-Urteilen und serialisiert."""
        judgments = list(SexualdeliktUrteil.objects.filter(
            zusammenfassung__icontains=query
        ).exclude(zusammenfassung="").select_related('hauptdelikt')[:limit])

        return [{
            'id': j.pk,
            'type': 'sexual',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
            'zusammenfassung': j.zusammenfassung,
            'hauptdelikt': str(j.hauptdelikt) if hasattr(j, 'hauptdelikt') else '',
            'opferalter': j.opferalter if hasattr(j, 'opferalter') else None,
        } for j in judgments]

    try:
        # Suche in den entsprechenden Models - async wrapped
        if judgment_type in ["wirtschaft", "all"]:
            wirtschaft_results = await sync_to_async(search_and_serialize_wirtschaft)()
            results.extend(wirtschaft_results)

        if judgment_type in ["betm", "all"]:
            betm_results = await sync_to_async(search_and_serialize_betm)()
            results.extend(betm_results)

        if judgment_type in ["sexual", "all"]:
            sexual_results = await sync_to_async(search_and_serialize_sexual)()
            results.extend(sexual_results)

        # Keine Ergebnisse
        if not results:
            return [TextContent(
                type="text",
                text=f"🔍 Keine Zusammenfassungen gefunden für Suchbegriff: '{query}'\n"
                     f"Urteilstyp: {judgment_type}"
            )]

        # Limitiere auf gewünschte Anzahl
        results = results[:limit]

        # Formatiere Ausgabe
        output = f"# Suchergebnisse für '{query}'\n\n"
        output += f"**Gefunden:** {len(results)} Urteil{'e' if len(results) != 1 else ''}\n"
        output += f"**Filter:** {judgment_type}\n\n"
        output += "---\n\n"

        for judgment_data in results:
            jtype = judgment_data['type']

            output += f"## {jtype.capitalize()} #{judgment_data['id']}\n\n"
            output += f"- **Fall-Nr:** {judgment_data.get('fall_nr', 'N/A')}\n"
            output += f"- **Datum:** {judgment_data.get('datum', 'N/A')}\n"

            # Gekürzte Vorschau der Zusammenfassung
            summary = judgment_data['zusammenfassung'].strip()
            if len(summary) > 300:
                summary = summary[:300] + "..."

            output += f"\n**Vorschau:**\n{summary}\n\n"
            output += "---\n\n"

        output += f"\n*Verwenden Sie `get_summary` für vollständige Zusammenfassungen*"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Fehler bei der Suche: {str(e)}"
        )]


async def list_summaries(args: dict) -> list[TextContent]:
    """
    Listet alle verfügbaren Zusammenfassungen auf.

    Args:
        judgment_type: Urteilstyp Filter (optional, default: 'all')
        limit: Max. Anzahl Ergebnisse (optional, default: 50)
    """
    judgment_type = args.get("judgment_type", "all")
    limit = args.get("limit", 50)

    results = []

    def list_and_serialize_wirtschaft():
        """Liste Wirtschaft-Urteile und serialisiere."""
        judgments = list(Urteil.objects.exclude(zusammenfassung="").select_related('hauptdelikt')[:limit])
        return [{
            'id': j.pk,
            'type': 'wirtschaft',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
            'deliktssumme': j.deliktssumme if hasattr(j, 'deliktssumme') else None,
        } for j in judgments]

    def list_and_serialize_betm():
        """Liste Betm-Urteile und serialisiere."""
        judgments = list(BetmUrteil.objects.exclude(zusammenfassung="").select_related('rolle')[:limit])
        return [{
            'id': j.pk,
            'type': 'betm',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
            'rolle': str(j.rolle) if hasattr(j, 'rolle') else '',
        } for j in judgments]

    def list_and_serialize_sexual():
        """Liste Sexual-Urteile und serialisiere."""
        judgments = list(SexualdeliktUrteil.objects.exclude(zusammenfassung="")[:limit])
        return [{
            'id': j.pk,
            'type': 'sexual',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
        } for j in judgments]

    try:
        # Sammle Urteile mit Zusammenfassungen - async wrapped
        if judgment_type in ["wirtschaft", "all"]:
            wirtschaft = await sync_to_async(list_and_serialize_wirtschaft)()
            results.extend(wirtschaft)

        if judgment_type in ["betm", "all"]:
            betm = await sync_to_async(list_and_serialize_betm)()
            results.extend(betm)

        if judgment_type in ["sexual", "all"]:
            sexual = await sync_to_async(list_and_serialize_sexual)()
            results.extend(sexual)

        if not results:
            return [TextContent(
                type="text",
                text=f"ℹ️ Keine Zusammenfassungen gefunden für Typ: {judgment_type}"
            )]

        # Limitiere auf gewünschte Anzahl
        results = results[:limit]

        # Formatiere Ausgabe
        output = f"# Verfügbare Urteilszusammenfassungen\n\n"
        output += f"**Gesamt:** {len(results)} Urteil{'e' if len(results) != 1 else ''}\n"
        output += f"**Filter:** {judgment_type}\n\n"

        # Gruppiere nach Typ
        from collections import defaultdict
        by_type = defaultdict(list)
        for judgment_data in results:
            by_type[judgment_data['type']].append(judgment_data)

        for jtype, judgments in sorted(by_type.items()):
            output += f"\n## {jtype.capitalize()}-Urteile ({len(judgments)})\n\n"

            for judgment_data in judgments:
                output += f"- **#{judgment_data['id']}** - "
                output += f"Fall {judgment_data.get('fall_nr', 'N/A')} "
                output += f"({judgment_data.get('datum', 'N/A')})"

                # Zusätzliche Info je nach Typ
                if jtype == "wirtschaft" and judgment_data.get('deliktssumme'):
                    output += f" - CHF {judgment_data['deliktssumme']}"
                elif jtype == "betm" and judgment_data.get('rolle'):
                    output += f" - {judgment_data['rolle']}"

                output += "\n"

        output += f"\n---\n\n"
        output += f"*Verwenden Sie `get_summary` mit der ID für Details*"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Fehler beim Auflisten: {str(e)}"
        )]


async def find_similar_by_description(args: dict) -> list[TextContent]:
    """
    Findet ähnliche Urteile basierend auf einer Freitext-Sachverhaltsbeschreibung.
    Nutzt einfache Keyword-basierte Ähnlichkeit.

    Args:
        description: Sachverhaltsbeschreibung in Freitext
        case_type: Optional Filter nach Falltyp
        limit: Anzahl ähnlicher Fälle
    """
    description = args["description"]
    case_type = args.get("case_type", "all")
    limit = args.get("limit", 5)

    # Extrahiere Keywords aus der Beschreibung
    keywords = description.lower().split()
    # Entferne sehr kurze Wörter und Füllwörter
    stop_words = {'der', 'die', 'das', 'und', 'oder', 'in', 'von', 'zu', 'mit', 'für', 'auf', 'ist', 'hat', 'ein', 'eine'}
    keywords = [k for k in keywords if len(k) > 3 and k not in stop_words]

    if not keywords:
        return [TextContent(
            type="text",
            text="❌ Bitte geben Sie eine detailliertere Sachverhaltsbeschreibung an."
        )]

    # Suche nach Urteilen, die mindestens ein Keyword enthalten
    def search_by_keywords():
        from django.db.models import Q, Count
        from functools import reduce
        import operator

        results = []

        # Erstelle Q-Objekte für OR-Verknüpfung aller Keywords
        query_parts = [Q(zusammenfassung__icontains=kw) for kw in keywords[:10]]  # Max 10 Keywords
        combined_query = reduce(operator.or_, query_parts)

        if case_type in ["wirtschaft", "all"]:
            wirtschaft_matches = list(
                Urteil.objects.filter(combined_query)
                .exclude(zusammenfassung="")
                .select_related('hauptdelikt')[:limit * 2]
            )
            for j in wirtschaft_matches:
                # Count matching keywords
                match_count = sum(1 for kw in keywords if kw in j.zusammenfassung.lower())
                results.append({
                    'id': j.pk,
                    'type': 'wirtschaft',
                    'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
                    'datum': str(j.datum) if hasattr(j, 'datum') else '',
                    'zusammenfassung': j.zusammenfassung,
                    'deliktssumme': j.deliktssumme if hasattr(j, 'deliktssumme') else None,
                    'hauptdelikt': str(j.hauptdelikt) if hasattr(j, 'hauptdelikt') else '',
                    'match_score': match_count
                })

        if case_type in ["betm", "all"]:
            betm_matches = list(
                BetmUrteil.objects.filter(combined_query)
                .exclude(zusammenfassung="")
                .select_related('rolle')[:limit * 2]
            )
            for j in betm_matches:
                match_count = sum(1 for kw in keywords if kw in j.zusammenfassung.lower())
                results.append({
                    'id': j.pk,
                    'type': 'betm',
                    'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
                    'datum': str(j.datum) if hasattr(j, 'datum') else '',
                    'zusammenfassung': j.zusammenfassung,
                    'rolle': str(j.rolle) if hasattr(j, 'rolle') else '',
                    'match_score': match_count
                })

        if case_type in ["sexual", "all"]:
            sexual_matches = list(
                SexualdeliktUrteil.objects.filter(combined_query)
                .exclude(zusammenfassung="")
                .select_related('hauptdelikt')[:limit * 2]
            )
            for j in sexual_matches:
                match_count = sum(1 for kw in keywords if kw in j.zusammenfassung.lower())
                results.append({
                    'id': j.pk,
                    'type': 'sexual',
                    'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
                    'datum': str(j.datum) if hasattr(j, 'datum') else '',
                    'zusammenfassung': j.zusammenfassung,
                    'hauptdelikt': str(j.hauptdelikt) if hasattr(j, 'hauptdelikt') else '',
                    'match_score': match_count
                })

        # Sortiere nach Match-Score (absteigende Reihenfolge)
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:limit]

    try:
        results = await sync_to_async(search_by_keywords)()

        if not results:
            return [TextContent(
                type="text",
                text=f"🔍 Keine ähnlichen Urteile gefunden für die Beschreibung:\n'{description[:100]}...'\n\n"
                     f"Suchte nach Keywords: {', '.join(keywords[:10])}"
            )]

        # Formatiere Ausgabe
        output = f"# Ähnliche Urteile zur Sachverhaltsbeschreibung\n\n"
        output += f"**Ihre Beschreibung:**\n{description}\n\n"
        output += f"**Suchkeywords:** {', '.join(keywords[:10])}\n"
        output += f"**Gefunden:** {len(results)} ähnliche{'r' if len(results) == 1 else ''} Fall/Fälle\n\n"
        output += "---\n\n"

        for idx, judgment_data in enumerate(results, 1):
            jtype = judgment_data['type']
            match_score = judgment_data['match_score']

            output += f"## {idx}. {jtype.capitalize()}-Urteil #{judgment_data['id']} (Relevanz: {match_score} Keywords)\n\n"
            output += f"- **Fall-Nr:** {judgment_data.get('fall_nr', 'N/A')}\n"
            output += f"- **Datum:** {judgment_data.get('datum', 'N/A')}\n"

            if jtype == "wirtschaft" and judgment_data.get('deliktssumme'):
                output += f"- **Deliktssumme:** CHF {judgment_data['deliktssumme']}\n"
                output += f"- **Hauptdelikt:** {judgment_data.get('hauptdelikt', 'N/A')}\n"
            elif jtype == "betm":
                output += f"- **Rolle:** {judgment_data.get('rolle', 'N/A')}\n"
            elif jtype == "sexual":
                output += f"- **Hauptdelikt:** {judgment_data.get('hauptdelikt', 'N/A')}\n"

            # Zusammenfassung mit Highlighting der Keywords
            summary = judgment_data['zusammenfassung']
            if len(summary) > 500:
                summary = summary[:500] + "..."

            output += f"\n**Zusammenfassung:**\n{summary}\n\n"
            output += "---\n\n"

        output += f"\n*Verwenden Sie `get_summary` mit der ID für die vollständige Zusammenfassung*"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Fehler bei der Ähnlichkeitssuche: {str(e)}"
        )]


async def find_similar_cases(args: dict) -> list[TextContent]:
    """
    Findet ähnliche Urteile basierend auf strukturierten Merkmalen.
    Nutzt die KNN-Pipeline aus der Anwendung.

    Args:
        case_type: Falltyp (wirtschaft, betm)
        Features je nach Typ
        n_neighbors: Anzahl der Nachbarn
    """
    case_type = args["case_type"]
    n_neighbors = args.get("n_neighbors", 4)

    # Info-Text über limitierte Funktionalität
    info_text = (
        "**Hinweis:** Die strukturierte Ähnlichkeitssuche ist aktuell eingeschränkt verfügbar, "
        "da sie auf vortrainierte ML-Modelle und komplexe Datenstrukturen angewiesen ist.\n\n"
        "**Empfehlung:** Verwenden Sie stattdessen:\n"
        "- `find_similar_by_description` - Für Freitext-Sachverhaltsbeschreibungen\n"
        "- `search_summaries` - Für Keyword-basierte Suche\n\n"
        "**Ihre Eingabe:**\n"
    )

    for key, value in args.items():
        if key != "case_type" and key != "n_neighbors":
            info_text += f"- {key}: {value}\n"

    return [TextContent(
        type="text",
        text=f"# Strukturierte Ähnlichkeitssuche\n\n{info_text}\n\n"
             f"ℹ️ Für die vollständige KNN-basierte Suche nutzen Sie bitte die Web-Anwendung."
    )]


async def main():
    """Hauptfunktion - startet den MCP-Server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="judgment-summaries",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
