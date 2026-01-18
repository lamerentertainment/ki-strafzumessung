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
    Entspricht dem database.models.Urteil Model mit numerischen Codes für Choices.
    """
    gericht: str = Field(
        description="Name des Gerichts (z.B. 'Bezirksgericht Zürich', 'Obergericht Bern')"
    )
    urteilsdatum: Optional[str] = Field(
        default=None,
        description="Datum des Urteils im Format YYYY-MM-DD (oder None wenn nicht gefunden)"
    )
    fall_nr: str = Field(
        description="Geschäftsnummer/Fallnummer (z.B. 'SB190145', 'SK.2019.12')"
    )
    url_link: str = Field(
        default="",
        description="URL zum PDF des Urteils (leer lassen wenn nicht vorhanden)"
    )
    geschlecht: str = Field(
        description="Geschlecht der beschuldigten Person: '0' für männlich, '1' für weiblich"
    )
    nationalitaet: str = Field(
        description="Nationalität: '0' für Schweizerin/Schweizer, '1' für Ausländer/Ausländerin, '2' für unbekannt"
    )
    hauptdelikt: str = Field(
        description="Art des Hauptdelikts. EXAKTE Werte: 'Betrug', 'Veruntreuung', 'ung. Geschäftsbesorgung', 'betr. Missbrauch DVA', 'Diebstahl', 'Sachbeschädigung'"
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
        description="Deliktssumme in CHF (Schadenssumme). Falls nicht bekannt: 0"
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
        description="Art der Hauptsanktion: '0' für Freiheitsstrafe, '1' für Geldstrafe, '2' für Busse"
    )
    freiheitsstrafe_in_monaten: int = Field(
        default=0,
        description="Dauer der Freiheitsstrafe in Monaten (0 wenn keine Freiheitsstrafe). Bei Jahren umrechnen: 1 Jahr = 12 Monate"
    )
    anzahl_tagessaetze: int = Field(
        default=0,
        description="Anzahl Tagessätze bei Geldstrafe (0 wenn keine Geldstrafe)"
    )
    vollzug: str = Field(
        description="Art des Vollzugs: '0' für bedingt, '1' für teilbedingt, '2' für unbedingt"
    )
    zusammenfassung: str = Field(
        default="",
        description="Zusammenfassung der Strafzumessungserwägungen aus dem Urteil"
    )
    in_ki_modell: bool = Field(
        default=False,
        description="Soll dieses Urteil im KI-Modell verwendet werden? (Standard: false)"
    )


def _preprocess_urteil_text(volltext: str, max_length: int = 40000) -> str:
    """
    Preprocessed den Urteilstext und extrahiert relevante Teile.

    Args:
        volltext: Der Volltext des Urteils
        max_length: Maximale Länge in Zeichen

    Returns:
        Verkürzter Text mit den relevantesten Teilen
    """
    # Wenn Text kurz genug ist, direkt zurückgeben
    if len(volltext) <= max_length:
        return volltext

    # Wichtige Schlüsselwörter für relevante Abschnitte
    relevante_abschnitte = []

    # Suche nach Dispositivziffern (enthalten die Strafe)
    import re

    # Versuche Dispositiv/Urteil-Abschnitt zu finden
    dispositiv_match = re.search(
        r'(Es wird erkannt:|Dispositiv|URTEIL|wird .* bestraft mit)(.*?)(?=Schriftliche Mitteilung|Gegen diesen Entscheid|$)',
        volltext,
        re.IGNORECASE | re.DOTALL
    )
    if dispositiv_match:
        relevante_abschnitte.append(dispositiv_match.group(0))

    # Suche nach Strafzumessungs-Erwägungen
    strafzumessung_match = re.search(
        r'(Strafzumessung|VII\.|VIII\.)(.*?)(?=VIII\.|IX\.|X\.|Landesverweisung|$)',
        volltext,
        re.IGNORECASE | re.DOTALL
    )
    if strafzumessung_match:
        relevante_abschnitte.append(strafzumessung_match.group(0)[:5000])  # Max 5000 Zeichen

    # Suche nach Grunddaten (Gericht, Datum, Geschäfts-Nr)
    header_match = re.search(
        r'^.*?(?=Anklage:|Sachverhalt|I\.|Es wird erkannt)',
        volltext,
        re.IGNORECASE | re.DOTALL
    )
    if header_match:
        relevante_abschnitte.append(header_match.group(0)[:2000])  # Max 2000 Zeichen

    # Kombiniere die Abschnitte
    processed_text = '\n\n'.join(relevante_abschnitte)

    # Falls immer noch zu lang, schneide am Ende ab
    if len(processed_text) > max_length:
        processed_text = processed_text[:max_length] + "\n\n[Text gekürzt...]"

    return processed_text if processed_text else volltext[:max_length]


def extract_urteil_data(volltext: str) -> dict:
    """
    Extrahiert Urteilsdaten aus einem Volltext mittels Google Gemini API.

    Args:
        volltext: Der Volltext des Urteils

    Returns:
        Dictionary mit extrahierten Urteilsdaten

    Raises:
        ValueError: Wenn die API-Konfiguration fehlt oder Text zu lang
        Exception: Bei API-Fehlern
    """
    # Längenlimit prüfen
    MAX_LENGTH = 50000  # Absolute Obergrenze

    if len(volltext) > MAX_LENGTH:
        raise ValueError(
            f"Der Urteilstext ist zu lang ({len(volltext):,} Zeichen). "
            f"Maximale Länge: {MAX_LENGTH:,} Zeichen.\n\n"
            "Bitte fügen Sie nur die relevanten Teile ein:\n"
            "- Kopf des Urteils (Gericht, Datum, Geschäftsnummer)\n"
            "- Dispositiv/Urteilsspruch (Strafe, Vollzug)\n"
            "- Strafzumessungs-Erwägungen\n\n"
            "Sie können unwichtige Teile wie ausführliche Sachverhalts-Darstellungen, "
            "Beweismittel-Listen, oder Kostenverlegungen weglassen."
        )

    try:
        # Gemini API Client initialisieren
        # Der Client holt sich automatisch den API Key aus der Umgebungsvariable GOOGLE_API_KEY
        from google import genai
        from google.genai import types

        client = genai.Client()

        # Text vorverarbeiten, wenn er lang ist
        processed_text = _preprocess_urteil_text(volltext, max_length=40000)

        # Prompt für die Extraktion
        prompt = f"""Du bist ein Experte für Schweizer Strafrecht und spezialisiert auf die Analyse von Gerichtsurteilen.

Analysiere das folgende Gerichtsurteil und extrahiere alle relevanten Informationen gemäss dem vorgegebenen Schema.

WICHTIGE HINWEISE ZU DEN CODES:
1. Geschlecht: '0' = männlich, '1' = weiblich
2. Nationalität: '0' = Schweizerin/Schweizer, '1' = Ausländer/Ausländerin, '2' = unbekannt
3. Hauptdelikt (EXAKT SO schreiben): 'Betrug', 'Veruntreuung', 'ung. Geschäftsbesorgung', 'betr. Missbrauch DVA', 'Diebstahl', 'Sachbeschädigung'
4. Hauptsanktion: '0' = Freiheitsstrafe, '1' = Geldstrafe, '2' = Busse
5. Vollzug: '0' = bedingt, '1' = teilbedingt, '2' = unbedingt

WICHTIGE HINWEISE ZUR EXTRAKTION:
- Das Urteil betrifft Vermögensdelikte (Betrug, Veruntreuung, Diebstahl, etc.)
- Achte besonders auf die Strafzumessungserwägungen
- Extrahiere die Deliktssumme präzise (Schadensbetrag in CHF). Falls nicht im Text: 0
- Bei Freiheitsstrafen: gib die Dauer in Monaten an (z.B. 2 Jahre = 24 Monate, 1.5 Jahre = 18 Monate)
- Bei Geldstrafen: gib die Anzahl der Tagessätze an
- Datum im Format YYYY-MM-DD (z.B. 2023-05-15)
- Falls Informationen nicht im Text sind: verwende sinnvolle Defaults
- Bei mehreren Beschuldigten: extrahiere die Daten für die beschuldigte Person, die die Hauptstrafe erhält

URTEILSTEXT:
{processed_text}

Extrahiere alle Informationen gemäss dem Schema. Verwende die numerischen Codes wie oben angegeben!"""

        # API Call mit Structured Output
        # Verwende gemini-2.5-flash (stabil und im Projekt bereits verwendet)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=UrteilExtraction,
                temperature=0.2,  # Niedrige Temperatur für präzise Extraktion
            )
        )

        # Response parsen
        try:
            extracted_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            raise Exception(
                f"Die API-Antwort konnte nicht als JSON geparst werden. "
                f"Fehler: {str(e)}. Antwort: {response.text[:500]}"
            )

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

        # Spezielle Behandlung für Pattern-Matching Fehler
        if 'did not match the expected pattern' in error_message.lower():
            text_length = len(volltext)
            raise Exception(
                f"Die KI konnte das Urteil nicht im erwarteten Format extrahieren.\n\n"
                f"Ihr Text hat {text_length:,} Zeichen. "
                f"{'✗ Das ist sehr lang und kann zu Problemen führen!' if text_length > 30000 else '✓ Die Länge ist ok.'}\n\n"
                "Mögliche Ursachen:\n"
                "- Der Text ist zu komplex oder enthält zu viele irrelevante Details\n"
                "- Es fehlen wichtige Informationen (Gericht, Datum, Strafe)\n"
                "- Bei sehr langen Texten: automatische Kürzung hat wichtige Teile entfernt\n\n"
                "💡 LÖSUNG - Fügen Sie NUR diese Teile ein:\n"
                "1. KOPF: Gericht, Datum, Geschäftsnummer (z.B. erste 20 Zeilen)\n"
                "2. DISPOSITIV/URTEILSSPRUCH: \"Es wird erkannt:\" oder \"Der Beschuldigte wird bestraft mit...\"\n"
                "3. STRAFZUMESSUNG: Abschnitt \"VII. Strafzumessung\" (falls vorhanden)\n\n"
                "⚠️ WEGLASSEN können Sie:\n"
                "- Ausführliche Sachverhalts-Darstellungen\n"
                "- Beweismittel-Listen und Aktenverzeichnisse\n"
                "- Zivilforderungen und Kostenverlegungen\n"
                "- Prozessuale Erwägungen\n\n"
                f"Technischer Fehler: {error_message}"
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
    required_fields = ['gericht', 'fall_nr', 'geschlecht',
                      'nationalitaet', 'hauptdelikt', 'hauptsanktion', 'vollzug']

    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"Pflichtfeld '{field}' fehlt oder ist leer")

    # Geschlecht validieren (numerische Codes)
    if data.get('geschlecht') not in ['0', '1']:
        errors.append(f"Geschlecht muss '0' (männlich) oder '1' (weiblich) sein, ist aber: {data.get('geschlecht')}")

    # Nationalität validieren
    if data.get('nationalitaet') not in ['0', '1', '2']:
        errors.append(f"Nationalität muss '0', '1' oder '2' sein, ist aber: {data.get('nationalitaet')}")

    # Hauptdelikt validieren
    valid_hauptdelikte = ['Betrug', 'Veruntreuung', 'ung. Geschäftsbesorgung',
                          'betr. Missbrauch DVA', 'Diebstahl', 'Sachbeschädigung']
    if data.get('hauptdelikt') not in valid_hauptdelikte:
        errors.append(f"Hauptdelikt muss einer der folgenden Werte sein: {', '.join(valid_hauptdelikte)}")

    # Hauptsanktion validieren (numerische Codes)
    if data.get('hauptsanktion') not in ['0', '1', '2']:
        errors.append(f"Hauptsanktion muss '0', '1' oder '2' sein, ist aber: {data.get('hauptsanktion')}")

    # Vollzug validieren (numerische Codes)
    if data.get('vollzug') not in ['0', '1', '2']:
        errors.append(f"Vollzug muss '0', '1' oder '2' sein, ist aber: {data.get('vollzug')}")

    # Logik-Checks
    if data.get('hauptsanktion') == '0' and data.get('freiheitsstrafe_in_monaten', 0) == 0:
        errors.append("Bei Freiheitsstrafe (Code '0') muss die Dauer in Monaten angegeben werden")

    if data.get('hauptsanktion') == '1' and data.get('anzahl_tagessaetze', 0) == 0:
        errors.append("Bei Geldstrafe (Code '1') muss die Anzahl Tagessätze angegeben werden")

    # Vorbestraft einschlägig kann nur true sein, wenn vorbestraft auch true ist
    if data.get('vorbestraft_einschlaegig') and not data.get('vorbestraft'):
        errors.append("Vorbestraft einschlägig kann nur gesetzt sein, wenn auch vorbestraft gesetzt ist")

    # Datum validieren (optional, aber wenn vorhanden, dann korrekt)
    if data.get('urteilsdatum'):
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', data.get('urteilsdatum', '')):
            errors.append("Urteilsdatum muss im Format YYYY-MM-DD sein")

    return (len(errors) == 0, errors)
