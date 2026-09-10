"""
Service für die Präjudizensuche: ein Chat, der im Hintergrund die Anthropic Messages API
mit Tool-Use aufruft. Claude hat Zugriff auf zwei Remote-MCP-Server (opencaselaw,
entscheidsuche - Schweizer Rechtsprechungsdatenbanken) über den MCP-Connector der API sowie
auf eigene Function-Calling-Tools gegen die kuratierte Urteilsdatenbank
(database.services.praejudizen_tools).
"""
import json
import logging

import anthropic
from django.conf import settings

from database.services.praejudizen_tools import CUSTOM_TOOLS, TOOL_EXECUTORS

logger = logging.getLogger(__name__)


class PraejudizenChatError(Exception):
    """Wird geworfen, wenn der Anthropic-Call fehlschlägt oder kein Ergebnis liefert."""


# MCP-Connector-Beta der Anthropic Messages API - verbindet die Remote-MCP-Server serverseitig
# als Tools, ohne dass dieses Backend selbst MCP-Client-Logik implementieren muss. Beta-Header
# gegen aktuelle Anthropic-SDK-Doku verifiziert (anthropic-Paket 1.4.0, siehe requirements.txt).
MCP_BETA_HEADER = "mcp-client-2025-11-20"

MCP_SERVERS = [
    {"type": "url", "url": "https://mcp.opencaselaw.ch", "name": "opencaselaw"},
    {"type": "url", "url": "https://mcp.entscheidsuche.ch/mcp", "name": "entscheidsuche"},
]

# Jeder in MCP_SERVERS deklarierte Server muss zusätzlich per mcp_toolset-Eintrag in `tools`
# referenziert werden, sonst lehnt die API den Request mit einem 400 ab ("MCP server '...' is
# defined but not referenced by any mcp_toolset in tools"). Live gegen die API verifiziert.
MCP_TOOLSETS = [
    {"type": "mcp_toolset", "mcp_server_name": server["name"]} for server in MCP_SERVERS
]

SYSTEM_PROMPT = """Du bist ein Rechercheassistent für Schweizer Strafzumessung, eingebettet \
in die Plattform strafzumessung.ch. Deine Aufgabe: Nutzerinnen und Nutzern (Anwält:innen, \
Richter:innen, Studierende, Forschende) helfen, Präjudizien zur erstinstanzlichen \
Strafzumessung zu finden.

## Werkzeuge
- search_vermoegensdelikt_urteile / search_betm_urteile / search_sexualdelikt_urteile: \
durchsuchen unsere eigene, kuratierte Datenbank erstinstanzlicher Strafzumessungsentscheide \
mit strukturierten Eckdaten (Deliktssumme, Vorstrafen, Vollzug, ausgesprochene Sanktion \
etc.). Nutze diese Tools IMMER ZUERST, wenn die Anfrage in eine der drei Kategorien \
(Vermögens-, Betäubungsmittel-, Sexualdelikte) fällt - unsere Datenbank liefert die \
genauesten, strukturiert vergleichbaren Fälle.
- opencaselaw / entscheidsuche (externe Rechtsprechungsdatenbanken): nutze diese für \
(a) Delikte ausserhalb der drei obigen Kategorien, (b) höchstrichterliche/publizierte \
Leitentscheide zu Strafzumessungsgrundsätzen, (c) Einordnung der eigenen DB-Treffer in die \
publizierte Rechtsprechung.

## Antwortstruktur
1. Kurze Einschätzung der Anfrage (1-2 Sätze).
2. Gefundene Präjudizien: pro Fall Gericht, Datum/Fall-Nr., zentrale Eckwerte, \
ausgesprochene Sanktion, kurze Begründung der Vergleichbarkeit.
3. Quellenangaben: bei eigener DB als Markdown-Link auf die Detailseite (aus dem \
Tool-Resultat übernehmen), bei externen Quellen mit Fundstelle/Zitat gemäss deren Angaben.
4. Bei Bedarf: kurzer Hinweis auf Grenzen der Vergleichbarkeit.

## Ablehnung themenfremder Anfragen
Wenn die Anfrage nichts mit Schweizer Strafzumessung/Strafrecht zu tun hat, lehne kurz und \
höflich ab (1-2 Sätze), ohne die Werkzeuge zu benutzen. Kein verbindlicher Rechtsrat für \
Einzelfälle - weise bei Bedarf auf den informativen Charakter hin.

Antworte auf Deutsch, prägnant, in Schweizer Hochdeutsch (ss statt ß)."""


def _client() -> anthropic.Anthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise PraejudizenChatError("ANTHROPIC_API_KEY ist nicht konfiguriert.")
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def run_chat_turn(client_history: list, user_message: str) -> tuple[str, list, list]:
    """
    client_history: bereits als reine dicts serialisierte Anthropic-messages (vom Client
                     unverändert zurückgeschickt, leer bei einer neuen Konversation).
    Returns: (finaler Antworttext, neue vollständige History als JSON-serialisierbare Liste,
              Liste der in diesem Turn aufgerufenen eigenen Tools als [{"name", "input"}, ...]
              - fürs Logging, nicht Teil der an Claude geschickten History).
    """
    client = _client()
    messages = list(client_history) + [{"role": "user", "content": user_message}]
    tool_calls_log = []
    max_rounds = getattr(settings, "PRAEJUDIZENSUCHE_MAX_TOOL_ROUNDS", 6)

    for _ in range(max_rounds):
        try:
            response = client.beta.messages.create(
                model=getattr(settings, "PRAEJUDIZENSUCHE_MODEL", "claude-sonnet-5"),
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=CUSTOM_TOOLS + MCP_TOOLSETS,
                mcp_servers=MCP_SERVERS,
                betas=[MCP_BETA_HEADER],
            )
        except anthropic.APIStatusError as e:
            logger.exception("Anthropic API-Fehler in run_chat_turn")
            raise PraejudizenChatError(f"Fehler bei der Anfrage an Claude: {e.message}")
        except anthropic.APIConnectionError:
            logger.exception("Verbindungsfehler zu Anthropic in run_chat_turn")
            raise PraejudizenChatError(
                "Verbindung zu Claude fehlgeschlagen. Bitte später erneut versuchen."
            )

        assistant_content = [block.model_dump(mode="json") for block in response.content]
        messages.append({"role": "assistant", "content": assistant_content})

        # mcp_tool_use/mcp_tool_result-Blöcke sind vom MCP-Connector bereits serverseitig
        # aufgelöst (kein eigener Round-Trip nötig). Nur eigene tool_use-Blöcke ausführen.
        tool_use_blocks = [b for b in assistant_content if b.get("type") == "tool_use"]

        if response.stop_reason != "tool_use" or not tool_use_blocks:
            final_text = "\n".join(
                b["text"] for b in assistant_content if b.get("type") == "text"
            )
            if not final_text:
                raise PraejudizenChatError("Claude hat keine Textantwort geliefert.")
            return final_text, messages, tool_calls_log

        tool_results = []
        for block in tool_use_blocks:
            tool_calls_log.append({"name": block["name"], "input": block.get("input") or {}})
            executor = TOOL_EXECUTORS.get(block["name"])
            if executor is None:
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": f"Unbekanntes Tool: {block['name']}",
                        "is_error": True,
                    }
                )
                continue
            try:
                result = executor(block.get("input") or {})
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
            except Exception as e:
                logger.exception("Fehler bei Tool-Ausführung %s", block["name"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": f"Fehler bei der Ausführung: {e}",
                        "is_error": True,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

    raise PraejudizenChatError(
        "Die Anfrage konnte nicht innerhalb der maximalen Anzahl Suchrunden abgeschlossen werden."
    )
