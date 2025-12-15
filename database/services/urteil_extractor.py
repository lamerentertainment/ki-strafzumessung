"""
Service für die automatische Extraktion von Urteilsdaten aus Volltexten
mittels Google Gemini API mit Structured Output.
"""
from typing import Optional
from pydantic import BaseModel, Field
from django.conf import settings
import json


class UrteilExtraction(BaseModel):
    """
    Pydantic Model für strukturierte Extraktion von Urteilsdaten.
    Entspricht dem database.models.Urteil Model.
    """
    gericht: str = Field(
        description="Name des Gerichts (z.B. 'Bezirksgericht Zürich', 'Obergericht Bern')"
    )
    urteilsdatum: str = Field(
        description="Datum des Urteils im Format YYYY-MM-DD"
    )
    fall_nr: str = Field(
        description="Geschäftsnummer/Fallnummer (z.B. 'SB190145', 'SK.2019.12')"
    )
    url_link: Optional[str] = Field(
        default="",
        description="URL zum PDF des Urteils"
    )
    geschlecht: str = Field(
        description="Geschlecht der beschuldigten Person: 'männlich' oder 'weiblich'"
    )
    nationalitaet: str = Field(
        description="Nationalität der beschuldigten Person (z.B. 'Schweiz', 'Deutschland')"
    )
    hauptdelikt: str = Field(
        description="Art des Hauptdelikts. Mögliche Werte: 'Betrug', 'Veruntreuung', 'ungetreue Geschäftsbesorgung', 'betrügerischer Konkurs', 'Gläubigerschädigung durch Vermögensverminderung', 'Misswirtschaft', 'Urkundenfälschung', 'mehrere'"
    )
    mehrfach: bool = Field(
        description="Wurde das Delikt mehrfach begangen? (Art. 47 StGB)"
    )
    gewerbsmaessig: bool = Field(
        description="Wurde das Delikt gewerbsmässig begangen?"
    )
    bandenmaessig: bool = Field(
        description="Wurde das Delikt bandenmässig begangen?"
    )
    deliktssumme: int = Field(
        description="Deliktssumme in CHF (Schadenssumme)"
    )
    nebenverurteilungsscore: int = Field(
        default=0,
        description="Score für Nebenverurteilungen (0-100). Berechnung: Anzahl Nebendelikte * Faktor je nach Schwere"
    )
    vorbestraft: bool = Field(
        description="Ist die Person vorbestraft?"
    )
    vorbestraft_einschlaegig: bool = Field(
        description="Ist die Person einschlägig vorbestraft (gleichartiges Delikt)?"
    )
    hauptsanktion: str = Field(
        description="Art der Hauptsanktion. Mögliche Werte: 'Freiheitsstrafe', 'Geldstrafe', 'Busse'"
    )
    freiheitsstrafe_in_monaten: int = Field(
        default=0,
        description="Dauer der Freiheitsstrafe in Monaten (0 wenn keine Freiheitsstrafe)"
    )
    anzahl_tagessaetze: int = Field(
        default=0,
        description="Anzahl Tagessätze bei Geldstrafe (0 wenn keine Geldstrafe)"
    )
    vollzug: str = Field(
        description="Art des Vollzugs. Mögliche Werte: 'bedingt', 'teilbedingt', 'unbedingt'"
    )
    zusammenfassung: str = Field(
        default="",
        description="Zusammenfassung der Strafzumessungserwägungen aus dem Urteil"
    )
    in_ki_modell: bool = Field(
        default=False,
        description="Soll dieses Urteil im KI-Modell verwendet werden?"
    )


def extract_urteil_data(volltext: str) -> dict:
    """
    Extrahiert Urteilsdaten aus einem Volltext mittels Google Gemini API.

    Args:
        volltext: Der Volltext des Urteils

    Returns:
        Dictionary mit extrahierten Urteilsdaten

    Raises:
        ValueError: Wenn die API-Konfiguration fehlt
        Exception: Bei API-Fehlern
    """
    try:
        # Gemini API Client initialisieren
        # Der Client holt sich automatisch den API Key aus der Umgebungsvariable GOOGLE_API_KEY
        from google import genai
        from google.genai import types

        client = genai.Client()

        # Prompt für die Extraktion
        prompt = f"""Du bist ein Experte für Schweizer Strafrecht und spezialisiert auf die Analyse von Gerichtsurteilen.

Analysiere das folgende Gerichtsurteil und extrahiere alle relevanten Informationen gemäss dem vorgegebenen Schema.

WICHTIGE HINWEISE:
- Das Urteil betrifft Vermögensdelikte (Betrug, Veruntreuung, etc.)
- Achte besonders auf die Strafzumessungserwägungen
- Extrahiere die Deliktssumme präzise (Schadensbetrag in CHF)
- Bei der Hauptsanktion: unterscheide zwischen Freiheitsstrafe, Geldstrafe und Busse
- Bei Freiheitsstrafen: gib die Dauer in Monaten an (auch bei Jahren: z.B. 2 Jahre = 24 Monate)
- Bei Geldstrafen: gib die Anzahl der Tagessätze an
- Vollzug kann sein: 'bedingt' (vollständig bedingt), 'teilbedingt' (teilweise bedingt), oder 'unbedingt'
- Geschlecht: 'männlich' oder 'weiblich'
- Hauptdelikt Optionen: 'Betrug', 'Veruntreuung', 'ungetreue Geschäftsbesorgung', 'betrügerischer Konkurs', 'Gläubigerschädigung durch Vermögensverminderung', 'Misswirtschaft', 'Urkundenfälschung', 'mehrere'

URTEILSTEXT:
{volltext}

Extrahiere alle Informationen gemäss dem Schema."""

        # API Call mit Structured Output
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=UrteilExtraction,
                temperature=0.1,  # Niedrige Temperatur für präzise Extraktion
            )
        )

        # Response parsen
        extracted_data = json.loads(response.text)

        return extracted_data

    except ImportError:
        raise ImportError(
            "Das 'google-genai' Paket ist nicht installiert. "
            "Bitte installieren Sie es mit: pip install google-genai"
        )
    except Exception as e:
        error_message = str(e)
        # Spezielle Behandlung für API Key Fehler
        if 'API key' in error_message or 'authentication' in error_message.lower():
            raise ValueError(
                "GOOGLE_API_KEY ist nicht konfiguriert oder ungültig. "
                "Bitte setzen Sie die Umgebungsvariable GOOGLE_API_KEY mit Ihrem Google AI API Key. "
                "Sie können einen Key unter https://ai.google.dev/ erhalten."
            )
        raise Exception(f"Fehler bei der Gemini API-Anfrage: {error_message}")


def validate_extracted_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validiert die extrahierten Daten.

    Args:
        data: Dictionary mit extrahierten Daten

    Returns:
        Tuple (is_valid, error_messages)
    """
    errors = []

    # Pflichtfelder prüfen
    required_fields = ['gericht', 'urteilsdatum', 'fall_nr', 'geschlecht',
                      'nationalitaet', 'hauptdelikt', 'hauptsanktion', 'vollzug']

    for field in required_fields:
        if not data.get(field):
            errors.append(f"Pflichtfeld '{field}' fehlt oder ist leer")

    # Geschlecht validieren
    if data.get('geschlecht') not in ['männlich', 'weiblich']:
        errors.append("Geschlecht muss 'männlich' oder 'weiblich' sein")

    # Hauptsanktion validieren
    valid_sanctions = ['Freiheitsstrafe', 'Geldstrafe', 'Busse']
    if data.get('hauptsanktion') not in valid_sanctions:
        errors.append(f"Hauptsanktion muss eine der folgenden sein: {', '.join(valid_sanctions)}")

    # Vollzug validieren
    valid_vollzug = ['bedingt', 'teilbedingt', 'unbedingt']
    if data.get('vollzug') not in valid_vollzug:
        errors.append(f"Vollzug muss einer der folgenden sein: {', '.join(valid_vollzug)}")

    # Logik-Checks
    if data.get('hauptsanktion') == 'Freiheitsstrafe' and data.get('freiheitsstrafe_in_monaten', 0) == 0:
        errors.append("Bei Freiheitsstrafe muss die Dauer in Monaten angegeben werden")

    if data.get('hauptsanktion') == 'Geldstrafe' and data.get('anzahl_tagessaetze', 0) == 0:
        errors.append("Bei Geldstrafe muss die Anzahl Tagessätze angegeben werden")

    # Vorbestraft einschlägig kann nur true sein, wenn vorbestraft auch true ist
    if data.get('vorbestraft_einschlaegig') and not data.get('vorbestraft'):
        errors.append("Vorbestraft einschlägig kann nur gesetzt sein, wenn auch vorbestraft gesetzt ist")

    return (len(errors) == 0, errors)
