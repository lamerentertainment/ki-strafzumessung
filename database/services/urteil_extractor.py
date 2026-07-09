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
        description="Das vorinstanzliche/erstinstanzliche Gericht, welches das vorinstanzliche Urteil gefällt hat (z.B. 'Bezirksgericht Zürich', 'Strafgericht Basel')."
    )
    urteilsdatum: Optional[str] = Field(
        default=None,
        description="Das Datum, an welchem das vorinstanzliche Gericht das Urteil gefällt hat, im Format YYYY-MM-DD."
    )
    fall_nr: str = Field(
        description="Die Verfahrensnummer des obergerichtlichen Urteils, aus welchem die Informationen entstammen (z.B. 'SB190145')."
    )
    url_link: str = Field(
        default="",
        description="URL zum PDF des Urteils (leer lassen wenn nicht vorhanden)."
    )
    geschlecht: str = Field(
        description="Geschlecht der beschuldigten Person: '0' für männlich, '1' für weiblich."
    )
    nationalitaet: str = Field(
        description="Nationalität der beschuldigten Person: '0' für Schweizerin/Schweizer, '1' für Ausländer/Ausländerin, '2' für unbekannt."
    )
    hauptdelikt: str = Field(
        description="Die Deliktsart, für welches die Einsatzstrafe gebildet wurde (z.B. Betrug, ungetreue Geschäftsbesorgung). EXAKTE Werte: 'Betrug', 'Veruntreuung', 'ung. Geschäftsbesorgung', 'betr. Missbrauch DVA', 'Diebstahl', 'Sachbeschädigung'."
    )
    mehrfach: bool = Field(
        description="Ob das Delikt, für welches die Einsatzstrafe gebildet wurde, mehrfach begangen wurde (erkennbar daran, dass der vorinstanzliche Schuldspruch z.B. so lautet: Der Beschuldigte ist schuldig des mehrfachen Diebstahls)."
    )
    gewerbsmaessig: bool = Field(
        description="Ob das Delikt, für welches die Einsatzstrafe gebildet wurde, gewerbsmässig bzw. (bei der Veruntreuung) qualifiziert begangen wurde."
    )
    bandenmaessig: bool = Field(
        description="Ob das Delikt, für welches die Einsatzstrafe gebildet wurde, bandenmässig begangen wurde."
    )
    deliktssumme: int = Field(
        description="Die mit dem Delikt, für welches die Einsatzstrafe gebildet wurde, erzielte Deliktssumme. Subsidiär die gesamthaft, mit allen Straftaten, erzielte Deliktssumme."
    )
    nebenverurteilungsscore: int = Field(
        default=0,
        description="Anzahl der Schuldsprüche, welche die Vorinstanz neben dem Delikt, für welches die Einsatzstrafe gebildet wurde, ausgesprochen hat. + 1 Punkt für jedes weitere Vergehen. + 2 Punkte für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher Begehung."
    )
    vorbestraft: bool = Field(
        description="Ob die verurteilte Person vorbestraft ist."
    )
    vorbestraft_einschlaegig: bool = Field(
        description="Ob die verurteilte Person einschlägig vorbestraft ist."
    )
    hauptsanktion: str = Field(
        description="Art der Hauptsanktion, vorinstanzlich angeordnet: '0' für Freiheitsstrafe, '1' für Geldstrafe, '2' für Busse."
    )
    freiheitsstrafe_in_monaten: int = Field(
        default=0,
        description="Die Dauer der vorinstanzlich ausgesprochenen Freiheitsstrafe in Monaten (sofern dies überhaupt der Fall ist)."
    )
    anzahl_tagessaetze: int = Field(
        default=0,
        description="Die Zahl der vorinstanzlich ausgesprochenen Tagessätze der Geldstrafe (sofern dies der Fall ist)."
    )
    vollzug: str = Field(
        description="Ob die Vorinstanz den bedingten ('0'), teilbedingten ('1') oder unbedingten ('2') Vollzug der Hauptstrafe angeordnet hat."
    )
    zusammenfassung: str = Field(
        default="",
        description="Zusammenfassung des a) Anklagevorwurfs und b) der massgebenden Erwägungen für die Strafzumessung (erwähne unbedingt, wenn das Obergericht bezüglich Strafzumessung zu einem anderen Ergebnis gelangt als die Vorinstanz)."
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


def extract_urteil_data(volltext: str = "", pdf_url: str = "") -> dict:
    """
    Extrahiert Urteilsdaten aus einem Volltext oder einer PDF-URL mittels Google Gemini API.

    Args:
        volltext: Der Volltext des Urteils
        pdf_url: Die URL zu einem PDF-Dokument des Urteils

    Returns:
        Dictionary mit extrahierten Urteilsdaten

    Raises:
        ValueError: Wenn die API-Konfiguration fehlt, Text zu lang oder Download-Fehler
        Exception: Bei API-Fehlern
    """
    pdf_bytes = None
    if pdf_url:
        import requests
        try:
            response = requests.get(pdf_url, timeout=20)
            response.raise_for_status()
            pdf_bytes = response.content
            # Einfacher Check auf PDF Header
            if not pdf_bytes.startswith(b'%PDF'):
                raise ValueError("Die heruntergeladene Datei ist kein gültiges PDF.")
        except Exception as e:
            raise ValueError(f"Fehler beim Herunterladen des PDFs von '{pdf_url}': {str(e)}")
    else:
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

        # Prompt für die Extraktion
        prompt = """Du bist ein Experte für Schweizer Strafrecht und spezialisiert auf die Analyse von Gerichtsurteilen.

Analysiere das folgende Gerichtsurteil und extrahiere alle relevanten Informationen gemäss dem vorgegebenen Schema.

WICHTIGE HINWEISE ZUR EXTRAKTION:
- Fokussiere auf die/den Beschuldigte/n 1, wenn es mehrere Beschuldigte gibt.
- Gericht: Das vorinstanzliche Gericht, welches das vorinstanzliche Urteil gefällt hat.
- Urteilsdatum: Das Datum, an welchem das vorinstanzliche Gericht das Urteil gefällt hat. Bitte im Format YYYY-MM-DD extrahieren.
- Fall nr: Die Verfahrensnummer des obergerichtlichen Urteils, aus welchem die Informationen entstammen.
- Geschlecht: der beschuldigten Person ('0' = männlich, '1' = weiblich).
- Nationalität: der beschuldigten Person ('0' = Schweizerin/Schweizer, '1' = Ausländer/Ausländerin, '2' = unbekannt).
- Hauptdelikt: Die Deliktsart, für welches die Einsatzstrafe gebildet wurde (z.B. Betrug, ungetreue Geschäftsbesorgung). EXAKTE Werte: 'Betrug', 'Veruntreuung', 'ung. Geschäftsbesorgung', 'betr. Missbrauch DVA', 'Diebstahl', 'Sachbeschädigung'.
- Mehrfach: Ob das Delikt, für welches die Einsatzstrafe gebildet wurde, mehrfach begangen wurde (erkennbar daran, dass der vorinstanzliche Schuldspruch z.B. so lautet: Der Beschuldigte ist schuldig des mehrfachen Diebstahls).
- Gewerbsmässig/qualifizierte Begehungsweise: Ob das Delikt, für welches die Einsatzstrafe gebildet wurde, gewerbsmässig bzw. (bei der Veruntreuung) qualifiziert begangen wurde.
- Bandenmässig: Ob das Delikt, für welches die Einsatzstrafe gebildet wurde, bandenmässig begangen wurde.
- Deliktssumme: Die mit dem Delikt, für welches die Einsatzstrafe gebildet wurde, erzielte Deliktssumme. Subsidiär die gesamthaft, mit allen Straftaten, erzielte Deliktssumme.
- Nebenverurteilungsscore: Anzahl der Schuldsprüche, welche die Vorinstanz neben dem Delikt, für welches die Einsatzstrafe gebildet wurde, ausgesprochen hat. Berechne wie folgt: + 1 Punkt für jedes weitere Vergehen. + 2 Punkte für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher Begehung.
- Vorbestraft: Ob die verurteilte Person vorbestraft ist.
- Einschlägig vorbestraft: Ob die verurteilte Person einschlägig vorbestraft ist.
- Hauptsanktion: Freiheitsstrafe ('0') oder Geldstrafe ('1'), vorinstanzlich angeordnet.
- Freiheitsstrafe in Monaten: Die Dauer der vorinstanzlich ausgesprochenen Freiheitsstrafe in Monaten (sofern dies überhaupt der Fall ist).
- Anzahl Tagessätze: Die Zahl der vorinstanzlich ausgesprochenen Tagessätze der Geldstrafe.
- Vollzug: Ob die Vorinstanz den bedingten ('0'), teilbedingten ('1') oder unbedingten ('2') Vollzug der Hauptstrafe angeordnet hat.
- Zusammenfassung: Fasse den a) Anklagevorwurf und b) die massgebenden Erwägungen für die Strafzumessung zusammen. Erwähne unbedingt, wenn das Obergericht bezüglich Strafzumessung zu einem anderen Ergebnis gelangt als die Vorinstanz.
"""

        if pdf_bytes:
            prompt += "\nBitte analysiere das angehängte PDF-Dokument."
            contents = [
                types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type='application/pdf'
                ),
                prompt
            ]
        else:
            # Text vorverarbeiten, wenn er lang ist
            processed_text = _preprocess_urteil_text(volltext, max_length=40000)
            prompt += f"\n\nURTEILSTEXT:\n{processed_text}\n\nExtrahiere alle Informationen gemäss dem Schema. Verwende die numerischen Codes wie oben angegeben!"
            contents = prompt

        # API Call mit Structured Output
        # Verwende gemini-2.5-flash (stabil und im Projekt bereits verwendet)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
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

        # Falls url_link nicht extrahiert wurde, verwenden wir die Eingabe-URL als Fallback
        if pdf_url and not extracted_data.get('url_link'):
            extracted_data['url_link'] = pdf_url

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

    # Datum validieren (optional, aber wenn vorhanden, dann korrekt)
    if data.get('urteilsdatum'):
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', data.get('urteilsdatum', '')):
            errors.append("Urteilsdatum muss im Format YYYY-MM-DD sein")

    return (len(errors) == 0, errors)


class BetmUrteilExtraction(BaseModel):
    """
    Pydantic Model für strukturierte Extraktion von Urteilsdaten im Bereich Betäubungsmittelstrafrecht.
    """
    fall_nr: str = Field(
        description="Die Verfahrensnummer des obergerichtlichen Urteils, dem die Informationen entnommen sind (z.B. 'SB190145')."
    )
    gericht: str = Field(
        description="Das vorinstanzliche Gericht, welches das vorinstanzliche Urteil gefällt hat (z.B. 'Bezirksgericht Zürich', 'Strafgericht Basel')."
    )
    urteilsdatum: Optional[str] = Field(
        default=None,
        description="Das Datum, an welchem das vorinstanzliche Gericht das Urteil gefällt hat im Format DD.MM.YYYY."
    )
    kanton: str = Field(
        description="Abkürzung des Kantons, in welchem das vorinstanzliche Gericht sich befindet (z.B. 'ZH', 'BE', 'AG', 'SG')."
    )
    mengenmaessig: bool = Field(
        description="ob eine Verurteilung nach Art. 19 Abs. 2 lit. a BetmG vorliegt."
    )
    bandenmaessig: bool = Field(
        description="ob eine Verurteilung nach Art. 19 Abs. 2 lit. b BetmG vorliegt."
    )
    gewerbsmaessig: bool = Field(
        description="ob eine Verurteilung nach Art. 19 Abs. 2 lit. c BetmG vorliegt."
    )
    anstaltentreffen: bool = Field(
        description="ob zur ganzen oder einer gewissen Menge Betm lediglich Anstalten getroffen wurden."
    )
    mehrfach: bool = Field(
        description="ob Schuldspruch wegen mehrfacher Begehung vorliegt."
    )
    beschaffungskriminalitaet: bool = Field(
        description="ob dem Täter in der Begründung ein Suchtdruck attestiert wird. Die Anwendung des Privilegierungsgrunds in Art. 19 Abs. 3 lit. b BetmG ist nicht erforderlich."
    )
    hauptsanktion: str = Field(
        description="Hauptsanktion, welche die Vorinstanz ausgesprochen hat. EXAKTE Werte: '0' für Freiheitsstrafe, '1' für Geldstrafe, '2' für Busse."
    )
    freiheitsstrafe_in_monaten: int = Field(
        default=0,
        description="Die Dauer der von der Vorinstanz ausgesprochenen Sanktion in Monaten, sofern eine Freiheitsstrafe ausgesprochen wurde (Die von der Vorinstanz ausgefällte Strafe steht in der Regel am Anfang des obergerichtlichen Urteils)."
    )
    anzahl_tagessaetze: int = Field(
        default=0,
        description="Die Zahl der von der Vorinstanz ausgesprochenen Tagessätze der Geldstrafe (sofern eine ausgesprochen wurde)."
    )
    vollzug: str = Field(
        description="Vollzug der Hauptstrafe (Urteil der Vorinstanz). EXAKTE Werte: '0' für bedingt, '1' für teilbedingt, '2' für unbedingt."
    )
    nebenverurteilungsscore: int = Field(
        default=0,
        description="Anzahl der Schuldsprüche, welche neben dem Delikt, für welches die Einsatzsstrafe gebildet wurde, ausgesprochen wurden. + 1 Punkt für jedes weitere Vergehen. + 2 Punkte für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher Begehung."
    )
    verfahrensart: str = Field(
        description="Die angewandte Verfahrensart. EXAKTE Werte: '0' für ordentlich, '1' für abgekürzt."
    )
    geschlecht: str = Field(
        description="Geschlecht der beschuldigten Person. EXAKTE Werte: '0' für männlich, '1' für weiblich."
    )
    nationalitaet: str = Field(
        description="Nationalität der beschuldigten Person. EXAKTE Werte: '0' für Schweizerin/Schweizer, '1' für Ausländer/Ausländerin (auch wenn Landesverweisung ausgesprochen wurde), '2' für unbekannt."
    )
    betm: str = Field(
        description="Art und Menge des Betäubungsmittels, welches gehandelt wurde."
    )
    rolle: str = Field(
        description="Die Rolle der beschuldigten Person. EXAKTE Werte: 'Transport', 'Kauf', 'Produktion', 'Handel', 'Handel von Konsumeinheiten', 'Handel von Grossmengen', 'Besitz/Aufbewahrung', 'Gehilfenschaft'."
    )
    deliktsertrag: Optional[int] = Field(
        default=None,
        description="Der Deliktsertrag (in CHF, falls im Urteil angegeben)."
    )
    deliktsdauer_in_monaten: Optional[int] = Field(
        default=None,
        description="Die Deliktsdauer in Monaten."
    )
    vorbestraft: bool = Field(
        description="Ob die verurteilte Person vorbestraft ist."
    )
    vorbestraft_einschlaegig: bool = Field(
        description="Ob die verurteilte Person einschlägig vorbestraft ist."
    )
    zusammenfassung: str = Field(
        description="Zusammenfassung des Vorwurfs und der massgebenden Erwägungen der Strafzumessung (durch die Rechtsmittelinstanz, wobei die Strafzumessung der Rechtsmittelinstanz von derjenigen der Vorinstanz abweichen kann) in wenigen Absätzen."
    )
    in_ki_modell: bool = Field(
        default=True,
        description="Soll dieses Urteil im KI-Modell verwendet werden? (Standard: true)"
    )


def extract_betm_urteil_data(volltext: str = "", pdf_url: str = "") -> dict:
    """
    Extrahiert Urteilsdaten für Betäubungsmittelstrafrecht aus einem Volltext oder einer PDF-URL
    mittels Google Gemini API mit Structured Output.
    """
    pdf_bytes = None
    if pdf_url:
        import requests
        try:
            response = requests.get(pdf_url, timeout=20)
            response.raise_for_status()
            pdf_bytes = response.content
            if not pdf_bytes.startswith(b'%PDF'):
                raise ValueError("Die heruntergeladene Datei ist kein gültiges PDF.")
        except Exception as e:
            raise ValueError(f"Fehler beim Herunterladen des PDFs von '{pdf_url}': {str(e)}")
    else:
        MAX_LENGTH = 50000  # Absolute Obergrenze
        if len(volltext) > MAX_LENGTH:
            raise ValueError(
                f"Der Urteilstext ist zu lang ({len(volltext):,} Zeichen). "
                f"Maximale Länge: {MAX_LENGTH:,} Zeichen.\n\n"
                "Bitte fügen Sie nur die relevanten Teile ein."
            )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client()

        # Prompt für die Extraktion gemäss Vorgabe
        prompt = """Du bist ein Experte für Schweizer Strafrecht und spezialisiert auf die Analyse von Gerichtsurteilen im Bereich Betäubungsmittelstrafrecht.

Nachfolgend bekommst du den text eines Gerichtsurteils.

Extrahiere zunächst folgende Daten aus dem Urteil (nur soweit das Urteil Angaben dazu enthält) und fülle das Schema aus.
Wichtig: Beziehe dich bei allen Werten konkret auf den Beschuldigten A.

Feldbeschreibungen und genaue Formate:
- fall_nr: Die Verfahrensnummer des obergerichtlichen Urteils, dem die Informationen entnommen sind.
- gericht: Das vorinstanzliche Gericht, welches das vorinstanzliche Urteil gefällt hat.
- urteilsdatum: Das Datum, an welchem das vorinstanzliche Gericht das Urteil gefällt hat (im Format: DD.MM.YYYY).
- kanton: Abkürzung des Kantons, in welchem das vorinstanzliche Gericht sich befindet.
- mengenmaessig: ob Verurteilung nach Art. 19 Abs. 2 lit. a BetmG vorliegt.
- bandenmaessig: ob Verurteilung nach Art. 19 Abs. 2 lit. b BetmG vorliegt.
- gewerbsmaessig: ob Verurteilung nach Art. 19 Abs. 2 lit. c BetmG vorliegt.
- anstaltentreffen: ob zur ganzen oder einen gewissen Menge Betm lediglich Anstalten getroffen wurden.
- mehrfach: ob Schuldspruch wegen mehrfacher Begehung vorliegt.
- beschaffungskriminalitaet: ob dem Täter in der Begründung ein Suchtdruck attestiert wird. Die Anwendung des Privilegierungsgrunds in Art. 19 Abs. 3 lit. b BetmG ist nicht erforderlich.
- hauptsanktion: Freiheitsstrafe oder Geldstrafe, es geht um die Hauptsanktion, welche die Vorinstanz ausgesprochen hat ('0' = Freiheitsstrafe, '1' = Geldstrafe, '2' = Busse).
- freiheitsstrafe_in_monaten: Die Dauer der von der Vorinstanz ausgesprochenen Sanktion in Monaten, sofern eine Freiheitsstrafe ausgesprochen wurde (Die von der Vorinstanz ausgefällte Strafe steht in der Regel am Anfang des obergerichtlichen Urteils).
- anzahl_tagessaetze: Die Zahl der von der Vorinstanz ausgesprochenen Tagessätze der Geldstrafe (sofern eine ausgesprochen wurde).
- vollzug: ob bedingt, teilbedingt oder unbedingt (Urteil der Vorinstanz). Codes: '0' für bedingt, '1' für teilbedingt, '2' für unbedingt.
- nebenverurteilungsscore: Anzahl der Schuldsprüche, welche neben dem Delikt, für welches die Einsatzsstrafe gebildet wurde, ausgesprochen wurden. + 1 Punkt für jedes weitere Vergehen. + 2 Punkt für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher Begehung.
- verfahrensart: ordentlich oder abgekürzt. Codes: '0' für ordentlich, '1' für abgekürzt.
- geschlecht: Codes: '0' für männlich, '1' für weiblich.
- nationalitaet: Codes: '0' für Schweizerin/Schweizer, '1' für Ausländer/Ausländerin (wenn Landesverweisung ausgesprochen wurde, besteht ausländische Nationalität), '2' für unbekannt.
- betm: Art und Menge des Betäubungsmittels, welches gehandelt wurde.
- rolle: EXAKTE Werte: 'Transport', 'Kauf', 'Produktion', 'Handel', 'Handel von Konsumeinheiten', 'Handel von Grossmengen', 'Besitz/Aufbewahrung', 'Gehilfenschaft'.
- deliktsertrag: Der Deliktsertrag.
- deliktsdauer_in_monaten: Die Deliktsdauer in Monaten.
- vorbestraft: Ob die verurteilte Person vorbestraft ist.
- vorbestraft_einschlaegig: Ob die verurteilte Person einschlägig vorbestraft ist.

Fasse danach den Vorwurf und die massgebenden Erwägungen der Strafzumessung (durch die Rechtsmittelinstanz, wobei die Strafzumessung der Rechtsmittelinstanz von derjenigen der Vorinstanz abweichen kann) in wenigen Absätzen zusammen (zusammenfassung).
"""

        if pdf_bytes:
            prompt += "\nBitte analysiere das angehängte PDF-Dokument."
            contents = [
                types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type='application/pdf'
                ),
                prompt
            ]
        else:
            processed_text = _preprocess_urteil_text(volltext, max_length=40000)
            prompt += f"\n\nURTEILSTEXT:\n{processed_text}\n\nExtrahiere alle Informationen gemäss dem Schema. Verwende die numerischen Codes wie oben angegeben!"
            contents = prompt

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=BetmUrteilExtraction,
                temperature=0.2,
            )
        )

        try:
            extracted_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            raise Exception(
                f"Die API-Antwort konnte nicht als JSON geparst werden. "
                f"Fehler: {str(e)}. Antwort: {response.text[:500]}"
            )

        # Konvertiere das Datum von DD.MM.YYYY zu YYYY-MM-DD für Django
        if extracted_data.get('urteilsdatum'):
            import re
            date_str = extracted_data['urteilsdatum']
            match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', date_str.strip())
            if match:
                extracted_data['urteilsdatum'] = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"

        if pdf_url and not extracted_data.get('url_link'):
            extracted_data['url_link'] = pdf_url

        return extracted_data

    except ImportError:
        raise ImportError(
            "Das 'google-genai' Paket ist nicht installiert. "
            "Bitte installieren Sie es mit: pip install google-genai"
        )
    except Exception as e:
        error_message = str(e)
        if 'API key' in error_message or 'authentication' in error_message.lower():
            raise ValueError(
                "GOOGLE_API_KEY ist nicht konfiguriert oder ungültig."
            )
        raise Exception(f"Fehler bei der Gemini API-Anfrage: {error_message}")


def validate_betm_extracted_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validiert die extrahierten BetmUrteil-Daten.
    """
    errors = []

    # Pflichtfelder prüfen
    required_fields = ['gericht', 'fall_nr', 'geschlecht',
                       'nationalitaet', 'hauptsanktion', 'vollzug', 'verfahrensart', 'kanton', 'rolle']

    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"Pflichtfeld '{field}' fehlt oder ist leer")

    # Geschlecht validieren
    if data.get('geschlecht') not in ['0', '1']:
        errors.append(f"Geschlecht muss '0' oder '1' sein, ist: {data.get('geschlecht')}")

    # Nationalität validieren
    if data.get('nationalitaet') not in ['0', '1', '2']:
        errors.append(f"Nationalität muss '0', '1' oder '2' sein, ist: {data.get('nationalitaet')}")

    # Hauptsanktion validieren
    if data.get('hauptsanktion') not in ['0', '1', '2']:
        errors.append(f"Hauptsanktion muss '0', '1' oder '2' sein, ist: {data.get('hauptsanktion')}")

    # Vollzug validieren
    if data.get('vollzug') not in ['0', '1', '2']:
        errors.append(f"Vollzug muss '0', '1' oder '2' sein, ist: {data.get('vollzug')}")

    # Verfahrensart validieren
    if data.get('verfahrensart') not in ['0', '1']:
        errors.append(f"Verfahrensart muss '0' oder '1' sein, ist: {data.get('verfahrensart')}")

    # Rolle validieren
    valid_rollen = ['Transport', 'Kauf', 'Produktion', 'Handel', 'Handel von Konsumeinheiten',
                    'Handel von Grossmengen', 'Besitz/Aufbewahrung', 'Gehilfenschaft']
    if data.get('rolle') not in valid_rollen:
        errors.append(f"Rolle muss eine der folgenden sein: {', '.join(valid_rollen)}")

    # Logik-Checks
    if data.get('hauptsanktion') == '0' and data.get('freiheitsstrafe_in_monaten', 0) == 0:
        errors.append("Bei Freiheitsstrafe (Code '0') muss die Dauer in Monaten angegeben werden")

    if data.get('hauptsanktion') == '1' and data.get('anzahl_tagessaetze', 0) == 0:
        errors.append("Bei Geldstrafe (Code '1') muss die Anzahl Tagessätze angegeben werden")

    if data.get('vorbestraft_einschlaegig') and not data.get('vorbestraft'):
        errors.append("Vorbestraft einschlägig kann nur gesetzt sein, wenn auch vorbestraft gesetzt ist")

    # Datum validieren
    if data.get('urteilsdatum'):
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', data.get('urteilsdatum', '')):
            errors.append("Urteilsdatum muss im Format YYYY-MM-DD sein")

    return (len(errors) == 0, errors)


class SexualdeliktUrteilExtraction(BaseModel):
    """
    Pydantic Model für strukturierte Extraktion von Urteilsdaten im Bereich Sexualdelikte.
    """
    fall_nr: str = Field(
        description="Die Verfahrensnummer des Urteils, dem die Informationen entnommen sind."
    )
    gericht: str = Field(
        description="Das Gericht, welches das vorinstanzliche Urteil gefällt hat."
    )
    urteilsdatum: Optional[str] = Field(
        default=None,
        description="Das Datum, an welchem das vorinstanzliche Gericht das Urteil gefällt hat (im Format DD.MM.YYYY)."
    )
    kanton: str = Field(
        description="Abkürzung des Kantons, in welchem sich die befassten Gerichte befinden (z.B. 'ZH', 'BE', 'AG', 'SG')."
    )
    hauptdelikt: str = Field(
        description="Das Hauptdelikt, für welches die Einsatzstrafe gebildet wurde."
    )
    tatmittel: str = Field(
        description="Das Tatmittel, mit welchem das Hauptdelikt begangen wurde (bsp. Gewalt, Nötigung, psychischer Druck)."
    )
    mehrfache_tatbegehung: bool = Field(
        description="Ob die Verurteilung wegen mehrfacher Begehung des Hauptdelikts erfolgte (mehrfache Tatbegehung?)."
    )
    taeter_opfer_beziehung: str = Field(
        description="Beziehung zwischen Täter und Opfer. EXAKTE Werte: 'Ehegatte/Partner', 'Elternteil/Kind', 'entfernt verwandt', 'Bekannte', 'flüchtig Bekannt', 'Unbekannte', 'Beziehung unbekannt'."
    )
    opferalter: str = Field(
        description="Alter des (jüngsten) Opfers des Hauptdelikts (erste Begehung) in Jahren. EXAKTE Werte: 'unter 6', 'unter 10', 'unter 14', 'unter 16', 'unter 18', 'erwachsen', 'nicht bekannt'."
    )
    opfer_vorerfahrung: str = Field(
        description="Ob das Opfer im Tatzeitpunkt sexuelle Vorerfahrungen hatte. EXAKTE Werte: 'Ja', 'Nein', 'unbekannt'."
    )
    deliktsdauer_bekannt: bool = Field(
        description="Ob die Deliktsdauer des Hauptdelikts bekannt ist."
    )
    deliktsdauer_hauptdelikt_min: Optional[int] = Field(
        default=None,
        description="Die Deliktsdauer des Hauptdelikts in Minuten, soweit bekannt."
    )
    anzahl_vollendungen_hauptdelikt: Optional[int] = Field(
        default=None,
        description="Anzahl der Vollendungen des Hauptdelikts, sofern mehrfach begangen."
    )
    deliktsperiode_hauptdelikt_days: Optional[int] = Field(
        default=None,
        description="Periode, in welcher das Hauptdelikt mehrfach begangen wurde, in Tagen."
    )
    weitere_sexualdelikte: str = Field(
        description="Ob/Welche weiteren Sexualdelikte nebst dem Hauptdelikt im vorinstanzlichen Urteilsspruch verurteilte wurden."
    )
    nebenverurteilungsscore: int = Field(
        default=0,
        description="Anzahl der Schuldsprüche, welche die Vorinstanz neben den Sexualdelikten (Hauptdelikt und allfällige weitere Sexualdelikte) ausgesprochen hat. + 1 Punkt für jedes weitere Vergehen. + 2 Punkte für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher Begehung."
    )
    geschlecht: str = Field(
        description="Geschlecht des Täters. EXAKTE Werte: '0' für männlich, '1' für weiblich."
    )
    nationalitaet: str = Field(
        description="Nationalität des Täters. EXAKTE Werte: '0' für Schweizerin/Schweizer, '1' für Ausländer/Ausländerin, '2' für unbekannt."
    )
    vorbestraft: bool = Field(
        description="Ob Vorstrafen bestehen."
    )
    vorbestraft_einschlaegig: bool = Field(
        description="Ob einschlägige Vorverurteilungen bestehen."
    )
    besonderheiten: str = Field(
        description="Weitere für die Strafzumessung relevante Informationen/Umstände im Urteil (z.B. Strafrabatt wegen Geständnis oder Verletzung Beschleunigungsgebot)."
    )
    hauptsanktion: str = Field(
        description="Hauptsanktion, welche die Vorinstanz ausgesprochen hat. EXAKTE Werte: '0' für Freiheitsstrafe, '1' für Geldstrafe, '2' für Busse."
    )
    freiheitsstrafe_in_monaten: int = Field(
        default=0,
        description="Die Dauer der von der Vorinstanz ausgesprochenen Sanktion in Monaten, sofern eine Freiheitsstrafe ausgesprochen wurde."
    )
    anzahl_tagessaetze: int = Field(
        default=0,
        description="Die Zahl der von der Vorinstanz ausgesprochenen Tagessätze der Geldstrafe (sofern eine ausgesprochen wurde)."
    )
    vollzug: str = Field(
        description="Vollzugsart, welche von der Vorinstanz verhängt wurde. EXAKTE Werte: '0' für bedingt, '1' für teilbedingt, '2' für unbedingt."
    )
    verfahrensart: str = Field(
        description="Verfahrensart. EXAKTE Werte: '0' für ordentlich, '1' für abgekürzt."
    )
    zusammenfassung: str = Field(
        description="Zusammenfassung des Vorwurfs und der massgebenden Erwägungen der Strafzumessung in wenigen Absätzen (Erwähne besonders, wenn das Obergericht bezüglich der Strafzumessung zu anderen Ergebnissen gelangt, als die Vorinstanz)."
    )


def extract_sexualdelikt_urteil_data(volltext: str = "", pdf_url: str = "") -> dict:
    """
    Extrahiert Urteilsdaten für Sexualdelikte aus einem Volltext oder einer PDF-URL
    mittels Google Gemini API mit Structured Output.
    """
    pdf_bytes = None
    if pdf_url:
        import requests
        try:
            response = requests.get(pdf_url, timeout=20)
            response.raise_for_status()
            pdf_bytes = response.content
            if not pdf_bytes.startswith(b'%PDF'):
                raise ValueError("Die heruntergeladene Datei ist kein gültiges PDF.")
        except Exception as e:
            raise ValueError(f"Fehler beim Herunterladen des PDFs von '{pdf_url}': {str(e)}")
    else:
        MAX_LENGTH = 50000  # Absolute Obergrenze
        if len(volltext) > MAX_LENGTH:
            raise ValueError(
                f"Der Urteilstext ist zu lang ({len(volltext):,} Zeichen). "
                f"Maximale Länge: {MAX_LENGTH:,} Zeichen.\n\n"
                "Bitte fügen Sie nur die relevanten Teile ein."
            )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client()

        # Prompt für die Extraktion gemäss Vorgabe
        prompt = """Du bist ein Experte für Schweizer Strafrecht und spezialisiert auf die Analyse von Gerichtsurteilen im Bereich Sexualdelikte.

Nachfolgend bekommst du den Text eines Gerichtsurteils.

1. Extrahiere zunächst folgende Daten aus dem Urteil (nur soweit das Urteil Angaben dazu enthält) und fülle das Schema aus:
- fall_nr: Die Verfahrensnummer des Urteils, dem die Informationen entnommen sind.
- gericht: Das Gericht, welches das vorinstanzliche Urteil gefällt hat.
- urteilsdatum: Das Datum, an welchem das vorinstanzliche Gericht das Urteil gefällt hat (im Format DD.MM.YYYY).
- kanton: Abkürzung des Kantons, in welchem sich die befassten Gerichte befinden.
- hauptdelikt: Das Hauptdelikt, für welches die Einsatzstrafe gebildet wurde.
- tatmittel: Das Tatmittel, mit welchem das Hauptdelikt begangen wurde (bsp. Gewalt, Nötigung, psychischer Druck).
- mehrfache_tatbegehung: Ob die Verurteilung wegen mehrfacher Begehung des Hauptdelikts erfolgte (mehrfache Tatbegehung?).
- taeter_opfer_beziehung: Beziehung zwischen Täter und Opfer (Ehegatte/Partner, Elternteil/Kind, entfernt verwandt, Bekannte, flüchtig Bekannt, Unbekannte, Beziehung unbekannt).
- opferalter: Alter des (jüngsten) Opfers des Hauptdelikts (erste Begehung) in Jahren (unter 6, unter 10, unter 14, unter 16, unter 18, erwachsen, nicht bekannt).
- opfer_vorerfahrung: Ob das Opfer im Tatzeitpunkt sexuelle Vorerfahrungen hatte (Ja, Nein, unbekannt).
- deliktsdauer_bekannt: Ob die Deliktsdauer des Hauptdelikts bekannt ist.
- deliktsdauer_hauptdelikt_min: Die Deliktsdauer des Hauptdelikts in Minuten, soweit bekannt.
- anzahl_vollendungen_hauptdelikt: Anzahl der Vollendungen des Hauptdelikts, sofern mehrfach begangen.
- deliktsperiode_hauptdelikt_days: Periode, in welcher das Hauptdelikt mehrfach begangen wurde, in Tagen.
- weitere_sexualdelikte: Ob/Welche weiteren Sexualdelikte im vorinstanzlichen Urteilsspruch nebst dem Hauptdelikt verurteilte wurden.
- nebenverurteilungsscore: Anzahl der Schuldsprüche, welche die Vorinstanz neben den Sexualdelikten (Hauptdelikt und allfällige weitere Sexualdelikte) ausgesprochen hat. + 1 Punkt für jedes weitere Vergehen. + 2 Punkt für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher Begehung.
- geschlecht: Geschlecht des Täters. Codes: '0' für männlich, '1' für weiblich.
- nationalitaet: Nationalität des Täters. Codes: '0' für Schweizerin/Schweizer, '1' für Ausländer/Ausländerin, '2' für unbekannt.
- vorbestraft: Ob Vorstrafen bestehen.
- vorbestraft_einschlaegig: Ob einschlägige Vorverurteilungen bestehen.
- besonderheiten: Weitere für die Strafzumessung relevante Informationen/Umstände im Urteil (z.B. Strafrabatt wegen Geständnis oder Verletzung Beschleunigungsgebot).
- hauptsanktion: Ob die Vorinstanz eine Freiheitsstrafe, Geldstrafe oder Busse ausgesprochen hat. Codes: '0' für Freiheitsstrafe, '1' für Geldstrafe, '2' für Busse.
- freiheitsstrafe_in_monaten: Die Dauer der von der Vorinstanz ausgesprochenen Sanktion in Monaten (sofern eine ausgesprochen wurde).
- anzahl_tagessaetze: Die Zahl der von der Vorinstanz ausgesprochenen Tagessätze der Geldstrafe (sofern eine ausgesprochen wurde).
- vollzug: Vollzugsart, welche von der Vorinstanz verhängt wurde: Codes: '0' für bedingt, '1' für teilbedingt, '2' für unbedingt.
- verfahrensart: Codes: '0' für ordentlich, '1' für abgekürzt.

2. Fasse danach den Vorwurf und die massgebenden Erwägungen der Strafzumessung in wenigen Absätzen zusammen (zusammenfassung). Erwähne besonders, wenn das Obergericht bezüglich der Strafzumessung zu anderen Ergebnissen gelangt, als die Vorinstanz.

Es handelt sich um eine wissenschaftliche Analyse, die für die faire Beurteilung von Sexualstraftätern unerheblich ist. Die Adressaten dieser Analyse sind Richtinnen und Richter, welche die Arbeit mit problematischen Inhalten gewohnt sind. Verweigere daher **nicht** die Arbeit, wenn es sexuell anstössige oder gewalttätige Elemente hat.
"""

        if pdf_bytes:
            prompt += "\nBitte analysiere das angehängte PDF-Dokument."
            contents = [
                types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type='application/pdf'
                ),
                prompt
            ]
        else:
            processed_text = _preprocess_urteil_text(volltext, max_length=40000)
            prompt += f"\n\nURTEILSTEXT:\n{processed_text}\n\nExtrahiere alle Informationen gemäss dem Schema. Verwende die exakten Werte und numerischen Codes wie oben angegeben!"
            contents = prompt

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=SexualdeliktUrteilExtraction,
                temperature=0.2,
            )
        )

        try:
            extracted_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            raise Exception(
                f"Die API-Antwort konnte nicht als JSON geparst werden. "
                f"Fehler: {str(e)}. Antwort: {response.text[:500]}"
            )

        # 1. Konvertiere das Datum von DD.MM.YYYY zu YYYY-MM-DD für Django
        if extracted_data.get('urteilsdatum'):
            import re
            date_str = extracted_data['urteilsdatum']
            match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', date_str.strip())
            if match:
                extracted_data['urteilsdatum'] = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"

        # 2. Konvertiere 'opferalter' (unter 6 -> unter_6, unter 10 -> unter_10)
        if extracted_data.get('opferalter'):
            opferalter = extracted_data['opferalter'].strip().replace(' ', '_')
            extracted_data['opferalter'] = opferalter

        # 3. Mappe Pydantic keys zu den echten Django Modelfeldern
        django_data = {
            'fall_nr': extracted_data.get('fall_nr'),
            'gericht': extracted_data.get('gericht'),
            'urteilsdatum': extracted_data.get('urteilsdatum'),
            'kanton': extracted_data.get('kanton'),
            'hauptdelikt': extracted_data.get('hauptdelikt'),
            'hauptdelikt_tatmittel': extracted_data.get('tatmittel'),
            'hauptdelikt_mehrfachbegehung': extracted_data.get('mehrfache_tatbegehung'),
            'hauptdelikt_taeter_opfer_beziehung': extracted_data.get('taeter_opfer_beziehung'),
            'hauptdelikt_opferalter': extracted_data.get('opferalter'),
            'hauptdelikt_opfer_vorerfahrung': extracted_data.get('opfer_vorerfahrung'),
            'hauptdelikt_deliktsdauer_bekannt': extracted_data.get('deliktsdauer_bekannt'),
            'hauptdelikt_mehrfachbegehung_anzahl': extracted_data.get('anzahl_vollendungen_hauptdelikt'),
            'deliktsscore_uebrige_delikte': extracted_data.get('nebenverurteilungsscore'),
            'geschlecht': extracted_data.get('geschlecht'),
            'nationalitaet': extracted_data.get('nationalitaet'),
            'vorbestraft': extracted_data.get('vorbestraft'),
            'vorbestraft_einschlaegig': extracted_data.get('vorbestraft_einschlaegig'),
            'hauptsanktion': extracted_data.get('hauptsanktion'),
            'freiheitsstrafe_in_monaten': extracted_data.get('freiheitsstrafe_in_monaten'),
            'anzahl_tagessaetze': extracted_data.get('anzahl_tagessaetze'),
            'vollzug': extracted_data.get('vollzug'),
            'verfahrensart': extracted_data.get('verfahrensart'),
            'zusammenfassung': extracted_data.get('zusammenfassung'),
            # ManyToMany Text-Zwischenspeicher (für JS Messageboxen)
            'weitere_sexualdelikte': extracted_data.get('weitere_sexualdelikte'),
            'besonderheiten': extracted_data.get('besonderheiten'),
        }

        # 4. Formatiere Durations (timedelta in Django)
        if extracted_data.get('deliktsdauer_hauptdelikt_min') is not None:
            mins = int(extracted_data['deliktsdauer_hauptdelikt_min'])
            hours = mins // 60
            remaining_mins = mins % 60
            django_data['hautpdelikt_deliktsdauer_einfachbegehung'] = f"{hours:02d}:{remaining_mins:02d}:00"

        if extracted_data.get('deliktsperiode_hauptdelikt_days') is not None:
            days = int(extracted_data['deliktsperiode_hauptdelikt_days'])
            django_data['hauptdelikt_mehrfachbegehung_deliktsperiode'] = f"{days} 00:00:00"

        if pdf_url and not django_data.get('url_link'):
            django_data['url_link'] = pdf_url

        return django_data

    except ImportError:
        raise ImportError(
            "Das 'google-genai' Paket ist nicht installiert."
        )
    except Exception as e:
        error_message = str(e)
        if 'API key' in error_message or 'authentication' in error_message.lower():
            raise ValueError(
                "GOOGLE_API_KEY ist nicht konfiguriert oder ungültig."
            )
        raise Exception(f"Fehler bei der Gemini API-Anfrage: {error_message}")


def validate_sexualdelikt_extracted_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validiert die extrahierten SexualdeliktUrteil-Daten.
    """
    errors = []

    # Pflichtfelder prüfen
    required_fields = ['gericht', 'fall_nr', 'geschlecht',
                       'nationalitaet', 'hauptsanktion', 'vollzug', 'verfahrensart', 'kanton',
                       'hauptdelikt', 'hauptdelikt_tatmittel', 'hauptdelikt_taeter_opfer_beziehung',
                       'hauptdelikt_opferalter', 'hauptdelikt_opfer_vorerfahrung']

    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"Pflichtfeld '{field}' fehlt oder ist leer")

    # Geschlecht validieren
    if data.get('geschlecht') not in ['0', '1']:
        errors.append(f"Geschlecht muss '0' oder '1' sein, ist: {data.get('geschlecht')}")

    # Nationalität validieren
    if data.get('nationalitaet') not in ['0', '1', '2']:
        errors.append(f"Nationalität muss '0', '1' oder '2' sein, ist: {data.get('nationalitaet')}")

    # Hauptsanktion validieren
    if data.get('hauptsanktion') not in ['0', '1', '2']:
        errors.append(f"Hauptsanktion muss '0', '1' oder '2' sein, ist: {data.get('hauptsanktion')}")

    # Vollzug validieren
    if data.get('vollzug') not in ['0', '1', '2']:
        errors.append(f"Vollzug muss '0', '1' oder '2' sein, ist: {data.get('vollzug')}")

    # Verfahrensart validieren
    if data.get('verfahrensart') not in ['0', '1']:
        errors.append(f"Verfahrensart muss '0' oder '1' sein, ist: {data.get('verfahrensart')}")

    # Beziehung validieren
    valid_beziehungen = ['Ehegatte/Partner', 'Elternteil/Kind', 'entfernt verwandt', 'Bekannte',
                         'flüchtig Bekannt', 'Unbekannte', 'Beziehung unbekannt']
    if data.get('hauptdelikt_taeter_opfer_beziehung') not in valid_beziehungen:
        errors.append(f"Beziehung muss eine der folgenden sein: {', '.join(valid_beziehungen)}")

    # Opferalter validieren
    valid_alter = ['unter_6', 'unter_10', 'unter_14', 'unter_16', 'unter_18', 'erwachsen', 'nicht_bekannt', 'nicht bekannt']
    if data.get('hauptdelikt_opferalter') not in valid_alter:
        errors.append(f"Opferalter muss eines der folgenden sein: {', '.join(valid_alter)}")

    # Opfer Vorerfahrung
    if data.get('hauptdelikt_opfer_vorerfahrung') not in ['Ja', 'Nein', 'unbekannt']:
        errors.append(f"Sexuelle Vorerfahrung muss 'Ja', 'Nein' oder 'unbekannt' sein")

    # Logik-Checks
    if data.get('hauptsanktion') == '0' and data.get('freiheitsstrafe_in_monaten', 0) == 0:
        errors.append("Bei Freiheitsstrafe (Code '0') muss die Dauer in Monaten angegeben werden")

    if data.get('hauptsanktion') == '1' and data.get('anzahl_tagessaetze', 0) == 0:
        errors.append("Bei Geldstrafe (Code '1') muss die Anzahl Tagessätze angegeben werden")

    if data.get('vorbestraft_einschlaegig') and not data.get('vorbestraft'):
        errors.append("Vorbestraft einschlägig kann nur gesetzt sein, wenn auch vorbestraft gesetzt ist")

    # Datum validieren
    if data.get('urteilsdatum'):
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', data.get('urteilsdatum', '')):
            errors.append("Urteilsdatum muss im Format YYYY-MM-DD sein")

    return (len(errors) == 0, errors)


