#!/usr/bin/env python3
"""
HTTP MCP Server für Urteilszusammenfassungen

Dieser Server macht die Urteilszusammenfassungen über HTTP/JSON verfügbar.
Clients können über JSON-RPC auf die MCP-Tools zugreifen.

Beispiel:
    curl -X POST http://localhost:8000/tools/call \
      -H "Content-Type: application/json" \
      -d '{
        "name": "get_summary",
        "arguments": {"judgment_type": "betm", "judgment_id": 42}
      }'

Start:
    uvicorn http_summary_server:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import asyncio
import json
from typing import Any
from datetime import datetime

# Django Setup - muss vor MCP imports erfolgen
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strafbemessung.settings.base_settings')

import django
django.setup()

# Jetzt können wir Django models importieren
from database.models import Urteil, BetmUrteil, SexualdeliktUrteil
from asgiref.sync import sync_to_async

# FastAPI
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

# App initialisieren
app = FastAPI(
    title="Judgment Summaries MCP Server",
    description="HTTP-basierter MCP Server für Urteilszusammenfassungen",
    version="1.0.0"
)

# CORS für öffentlichen Zugriff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Öffentlich zugänglich
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class ToolCallRequest(BaseModel):
    """Request für einen Tool-Aufruf"""
    name: str = Field(..., description="Name des Tools")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool-Argumente")


class ToolCallResponse(BaseModel):
    """Response eines Tool-Aufrufs"""
    status: str = Field("success", description="Status: success oder error")
    result: Any = Field(None, description="Ergebnis des Tool-Aufrufs")
    error: Optional[str] = Field(None, description="Fehlermeldung falls Status error")


# Hilfsfunktionen (aus original summary_server.py)
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


# Tool-Implementierungen
async def get_summary(args: dict) -> dict:
    """Ruft die Zusammenfassung eines spezifischen Urteils ab."""
    judgment_type = args.get("judgment_type")
    judgment_id = args.get("judgment_id")

    if not judgment_type or judgment_id is None:
        raise ValueError("judgment_type und judgment_id sind erforderlich")

    model = get_model_by_type(judgment_type)
    if not model:
        raise ValueError(f"Ungültiger Urteilstyp: {judgment_type}")

    try:
        judgment = await sync_to_async(model.objects.get)(pk=judgment_id)

        if not judgment.zusammenfassung or judgment.zusammenfassung.strip() == "":
            return {
                "status": "no_summary",
                "message": f"Keine Zusammenfassung für {judgment_type} Urteil #{judgment_id}",
                "metadata": format_judgment_metadata(judgment, judgment_type)
            }

        metadata = format_judgment_metadata(judgment, judgment_type)
        return {
            "status": "found",
            "metadata": metadata,
            "zusammenfassung": judgment.zusammenfassung
        }

    except model.DoesNotExist:
        raise ValueError(f"Urteil #{judgment_id} nicht gefunden")


async def search_summaries(args: dict) -> dict:
    """Durchsucht Zusammenfassungen nach einem Suchbegriff."""
    query = args.get("query")
    judgment_type = args.get("judgment_type", "all")
    limit = args.get("limit", 10)

    if not query:
        raise ValueError("query Parameter erforderlich")

    if limit < 1 or limit > 100:
        limit = 10

    results = []

    def search_and_serialize_wirtschaft():
        judgments = list(Urteil.objects.filter(
            zusammenfassung__icontains=query
        ).exclude(zusammenfassung="").select_related('hauptdelikt')[:limit])
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
        if judgment_type in ["wirtschaft", "all"]:
            wirtschaft_results = await sync_to_async(search_and_serialize_wirtschaft)()
            results.extend(wirtschaft_results)

        if judgment_type in ["betm", "all"]:
            betm_results = await sync_to_async(search_and_serialize_betm)()
            results.extend(betm_results)

        if judgment_type in ["sexual", "all"]:
            sexual_results = await sync_to_async(search_and_serialize_sexual)()
            results.extend(sexual_results)

        results = results[:limit]

        return {
            "status": "found",
            "query": query,
            "judgment_type": judgment_type,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise ValueError(f"Fehler bei Suche: {str(e)}")


async def list_summaries(args: dict) -> dict:
    """Listet alle verfügbaren Zusammenfassungen auf."""
    judgment_type = args.get("judgment_type", "all")
    limit = args.get("limit", 50)

    if limit < 1 or limit > 500:
        limit = 50

    results = []

    def list_and_serialize_wirtschaft():
        judgments = list(Urteil.objects.exclude(zusammenfassung="").select_related('hauptdelikt')[:limit])
        return [{
            'id': j.pk,
            'type': 'wirtschaft',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
            'deliktssumme': j.deliktssumme if hasattr(j, 'deliktssumme') else None,
        } for j in judgments]

    def list_and_serialize_betm():
        judgments = list(BetmUrteil.objects.exclude(zusammenfassung="").select_related('rolle')[:limit])
        return [{
            'id': j.pk,
            'type': 'betm',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
            'rolle': str(j.rolle) if hasattr(j, 'rolle') else '',
        } for j in judgments]

    def list_and_serialize_sexual():
        judgments = list(SexualdeliktUrteil.objects.exclude(zusammenfassung="")[:limit])
        return [{
            'id': j.pk,
            'type': 'sexual',
            'fall_nr': j.fall_nr if hasattr(j, 'fall_nr') else None,
            'datum': str(j.datum) if hasattr(j, 'datum') else '',
        } for j in judgments]

    try:
        if judgment_type in ["wirtschaft", "all"]:
            wirtschaft = await sync_to_async(list_and_serialize_wirtschaft)()
            results.extend(wirtschaft)

        if judgment_type in ["betm", "all"]:
            betm = await sync_to_async(list_and_serialize_betm)()
            results.extend(betm)

        if judgment_type in ["sexual", "all"]:
            sexual = await sync_to_async(list_and_serialize_sexual)()
            results.extend(sexual)

        results = results[:limit]

        return {
            "status": "found",
            "judgment_type": judgment_type,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise ValueError(f"Fehler beim Auflisten: {str(e)}")


async def find_similar_by_description(args: dict) -> dict:
    """Findet ähnliche Urteile basierend auf einer Freitext-Sachverhaltsbeschreibung."""
    description = args.get("description")
    case_type = args.get("case_type", "all")
    limit = args.get("limit", 5)

    if not description:
        raise ValueError("description Parameter erforderlich")

    if limit < 1 or limit > 20:
        limit = 5

    # Extrahiere Keywords
    keywords = description.lower().split()
    stop_words = {'der', 'die', 'das', 'und', 'oder', 'in', 'von', 'zu', 'mit', 'für', 'auf', 'ist', 'hat', 'ein', 'eine'}
    keywords = [k for k in keywords if len(k) > 3 and k not in stop_words]

    if not keywords:
        raise ValueError("Bitte geben Sie eine detailliertere Sachverhaltsbeschreibung an")

    results = []

    def search_by_keywords():
        from django.db.models import Q
        from functools import reduce
        import operator

        results = []
        query_parts = [Q(zusammenfassung__icontains=kw) for kw in keywords[:10]]
        combined_query = reduce(operator.or_, query_parts)

        if case_type in ["wirtschaft", "all"]:
            wirtschaft_matches = list(
                Urteil.objects.filter(combined_query)
                .exclude(zusammenfassung="")
                .select_related('hauptdelikt')[:limit * 2]
            )
            for j in wirtschaft_matches:
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

        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:limit]

    try:
        results = await sync_to_async(search_by_keywords)()
        return {
            "status": "found",
            "description": description,
            "keywords": keywords[:10],
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise ValueError(f"Fehler bei Ähnlichkeitssuche: {str(e)}")


# Tool Registry
TOOLS = {
    "get_summary": get_summary,
    "search_summaries": search_summaries,
    "list_summaries": list_summaries,
    "find_similar_by_description": find_similar_by_description,
}


# API Endpoints
@app.get("/", tags=["Info"])
async def root():
    """Root endpoint mit Informationen"""
    return {
        "name": "Judgment Summaries MCP Server",
        "version": "1.0.0",
        "description": "HTTP-basierter Server für Urteilszusammenfassungen",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs_url": "/docs",
        "available_tools": list(TOOLS.keys())
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/tools", tags=["Tools"])
async def list_tools():
    """Listet alle verfügbaren Tools auf"""
    return {
        "tools": [
            {
                "name": "get_summary",
                "description": "Ruft eine spezifische Urteilszusammenfassung ab",
                "parameters": {
                    "judgment_type": "string (wirtschaft|betm|sexual)",
                    "judgment_id": "integer"
                }
            },
            {
                "name": "search_summaries",
                "description": "Sucht nach Stichworten in Zusammenfassungen",
                "parameters": {
                    "query": "string (erforderlich)",
                    "judgment_type": "string (optional, default: all)",
                    "limit": "integer (1-100, default: 10)"
                }
            },
            {
                "name": "list_summaries",
                "description": "Listet alle verfügbaren Zusammenfassungen auf",
                "parameters": {
                    "judgment_type": "string (optional, default: all)",
                    "limit": "integer (1-500, default: 50)"
                }
            },
            {
                "name": "find_similar_by_description",
                "description": "Findet ähnliche Urteile basierend auf Sachverhaltsbeschreibung",
                "parameters": {
                    "description": "string (erforderlich)",
                    "case_type": "string (optional, default: all)",
                    "limit": "integer (1-20, default: 5)"
                }
            }
        ]
    }


@app.post("/tools/call", tags=["Tools"], response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """Ruft ein Tool auf"""
    tool_name = request.name
    tool_args = request.arguments

    if tool_name not in TOOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekanntes Tool: {tool_name}. Verfügbar: {list(TOOLS.keys())}"
        )

    try:
        tool_func = TOOLS[tool_name]
        result = await tool_func(tool_args)
        return ToolCallResponse(status="success", result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")


@app.post("/tools/{tool_name}", tags=["Tools"], response_model=ToolCallResponse)
async def call_tool_direct(tool_name: str, arguments: dict = None):
    """Direkter Tool-Aufruf mit Query-Parametern"""
    if arguments is None:
        arguments = {}

    if tool_name not in TOOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekanntes Tool: {tool_name}. Verfügbar: {list(TOOLS.keys())}"
        )

    try:
        tool_func = TOOLS[tool_name]
        result = await tool_func(arguments)
        return ToolCallResponse(status="success", result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")


@app.get("/summary/{judgment_type}/{judgment_id}", tags=["Convenience"])
async def get_summary_shortcut(judgment_type: str, judgment_id: int):
    """Convenience Endpoint für Zusammenfassungen"""
    try:
        result = await get_summary({
            "judgment_type": judgment_type,
            "judgment_id": judgment_id
        })
        return ToolCallResponse(status="success", result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/search", tags=["Convenience"])
async def search_shortcut(q: str, type: str = "all", limit: int = 10):
    """Convenience Endpoint für Suchfunktion"""
    try:
        result = await search_summaries({
            "query": q,
            "judgment_type": type,
            "limit": limit
        })
        return ToolCallResponse(status="success", result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
