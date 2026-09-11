"""
Function-Calling-Tools für die Präjudizensuche: durchsuchen die eigene kuratierte
Urteilsdatenbank (Urteil/BetmUrteil/SexualdeliktUrteil/GewaltdeliktUrteil). Tool-*Definitionen* (JSON-Schema
für die Anthropic Messages API) und Tool-*Ausführung* (Django-ORM) leben bewusst in einem
Modul, aber als getrennte Funktionen, damit die Ausführung ohne Anthropic-Client testbar ist.
"""
from django.urls import reverse

from database.models import BetmUrteil, GewaltdeliktUrteil, SexualdeliktUrteil, Urteil

MAX_LIMIT = 20
DEFAULT_LIMIT = 15
ZUSAMMENFASSUNG_MAX_CHARS = 600

HAUPTSANKTION_CODES = {"Freiheitsstrafe": "0", "Geldstrafe": "1", "Busse": "2"}
VOLLZUG_CODES = {"bedingt": "0", "teilbedingt": "1", "unbedingt": "2"}


def _clamp_limit(limit) -> int:
    if not limit:
        return DEFAULT_LIMIT
    return max(1, min(int(limit), MAX_LIMIT))


def _apply_bool_filters(qs, params: dict, fields: list[str]):
    for field in fields:
        value = params.get(field)
        if value is not None:
            qs = qs.filter(**{field: value})
    return qs


def _apply_sanktion_filters(qs, params: dict):
    if params.get("hauptsanktion"):
        code = HAUPTSANKTION_CODES.get(params["hauptsanktion"])
        if code is not None:
            qs = qs.filter(hauptsanktion=code)
    if params.get("vollzug"):
        code = VOLLZUG_CODES.get(params["vollzug"])
        if code is not None:
            qs = qs.filter(vollzug=code)
    return qs


# --- search_vermoegensdelikt_urteile -----------------------------------------------------

SEARCH_VERMOEGENSDELIKT_TOOL = {
    "name": "search_vermoegensdelikt_urteile",
    "description": (
        "Durchsucht die kuratierte Datenbank erstinstanzlicher Strafzumessungsentscheide zu "
        "Vermögensdelikten (Betrug, Veruntreuung, ungetreue Geschäftsbesorgung, betrügerischer "
        "Missbrauch einer Datenverarbeitungsanlage, Diebstahl, Sachbeschädigung). Liefert "
        "konkrete, dokumentierte Präjudizien mit ausgesprochener Sanktion. Nutze dieses Tool "
        "IMMER, wenn die Anfrage eines dieser Delikte betrifft."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "hauptdelikt": {
                "type": "string",
                "enum": [
                    "Betrug",
                    "Veruntreuung",
                    "ung. Geschäftsbesorgung",
                    "betr. Missbrauch DVA",
                    "Diebstahl",
                    "Sachbeschädigung",
                ],
                "description": "Das Delikt, für welches die Einsatzstrafe gebildet wurde.",
            },
            "deliktssumme_min": {"type": "integer", "description": "Deliktssumme in CHF, untere Grenze."},
            "deliktssumme_max": {"type": "integer", "description": "Deliktssumme in CHF, obere Grenze."},
            "mehrfach": {"type": "boolean"},
            "gewerbsmaessig": {"type": "boolean"},
            "bandenmaessig": {"type": "boolean"},
            "vorbestraft": {"type": "boolean"},
            "vorbestraft_einschlaegig": {"type": "boolean"},
            "hauptsanktion": {"type": "string", "enum": ["Freiheitsstrafe", "Geldstrafe", "Busse"]},
            "vollzug": {"type": "string", "enum": ["bedingt", "teilbedingt", "unbedingt"]},
            "limit": {
                "type": "integer",
                "description": f"Max. Trefferzahl, Default {DEFAULT_LIMIT}, Maximum {MAX_LIMIT}.",
            },
        },
    },
}


def execute_search_vermoegensdelikt_urteile(params: dict) -> dict:
    qs = Urteil.objects.all()
    if params.get("hauptdelikt"):
        qs = qs.filter(hauptdelikt=params["hauptdelikt"])
    if params.get("deliktssumme_min") is not None:
        qs = qs.filter(deliktssumme__gte=params["deliktssumme_min"])
    if params.get("deliktssumme_max") is not None:
        qs = qs.filter(deliktssumme__lte=params["deliktssumme_max"])
    qs = _apply_bool_filters(
        qs, params, ["mehrfach", "gewerbsmaessig", "bandenmaessig", "vorbestraft", "vorbestraft_einschlaegig"]
    )
    qs = _apply_sanktion_filters(qs, params)

    total = qs.count()
    limit = _clamp_limit(params.get("limit"))
    urteile = [
        {
            "id": u.id,
            "gericht": u.gericht,
            "urteilsdatum": str(u.urteilsdatum) if u.urteilsdatum else None,
            "fall_nr": u.fall_nr,
            "hauptdelikt": u.hauptdelikt,
            "deliktssumme": u.deliktssumme,
            "mehrfach": u.mehrfach,
            "gewerbsmaessig": u.gewerbsmaessig,
            "bandenmaessig": u.bandenmaessig,
            "vorbestraft": u.vorbestraft,
            "vorbestraft_einschlaegig": u.vorbestraft_einschlaegig,
            "hauptsanktion": u.get_hauptsanktion_display(),
            "freiheitsstrafe_in_monaten": u.freiheitsstrafe_in_monaten,
            "anzahl_tagessaetze": u.anzahl_tagessaetze,
            "vollzug": u.get_vollzug_display(),
            "zusammenfassung": u.zusammenfassung[:ZUSAMMENFASSUNG_MAX_CHARS],
            "detail_url": reverse("vmurteil_detail", args=[u.id]),
        }
        for u in qs.order_by("-urteilsdatum")[:limit]
    ]
    return {"total_treffer": total, "angezeigt": len(urteile), "urteile": urteile}


# --- search_betm_urteile ------------------------------------------------------------------

SEARCH_BETM_TOOL = {
    "name": "search_betm_urteile",
    "description": (
        "Durchsucht die kuratierte Datenbank erstinstanzlicher Strafzumessungsentscheide zu "
        "Betäubungsmitteldelikten (Art. 19 BetmG). Liefert konkrete, dokumentierte Präjudizien "
        "mit ausgesprochener Sanktion. Nutze dieses Tool IMMER, wenn die Anfrage ein "
        "Betäubungsmitteldelikt betrifft."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "mengenmaessig": {"type": "boolean", "description": "Art. 19 Abs. 2 lit. a BetmG (mengenmässig schwerer Fall)."},
            "bandenmaessig": {"type": "boolean", "description": "Art. 19 Abs. 2 lit. b BetmG."},
            "gewerbsmaessig": {"type": "boolean", "description": "Art. 19 Abs. 2 lit. c BetmG."},
            "anstaltentreffen": {"type": "boolean"},
            "mehrfach": {"type": "boolean"},
            "beschaffungskriminalitaet": {
                "type": "boolean",
                "description": "Täter wird im Urteil explizit Suchtdruck/eigene Konsumabhängigkeit attestiert.",
            },
            "betm_art": {
                "type": "string",
                "description": "Name der Betäubungsmittel-Art (z.B. 'Kokain', 'Heroin', 'Marihuana') - Teilstring-Suche.",
            },
            "vorbestraft": {"type": "boolean"},
            "vorbestraft_einschlaegig": {"type": "boolean"},
            "hauptsanktion": {"type": "string", "enum": ["Freiheitsstrafe", "Geldstrafe", "Busse"]},
            "vollzug": {"type": "string", "enum": ["bedingt", "teilbedingt", "unbedingt"]},
            "limit": {
                "type": "integer",
                "description": f"Max. Trefferzahl, Default {DEFAULT_LIMIT}, Maximum {MAX_LIMIT}.",
            },
        },
    },
}


def execute_search_betm_urteile(params: dict) -> dict:
    qs = BetmUrteil.objects.all()
    if params.get("betm_art"):
        qs = qs.filter(betm__art__name__icontains=params["betm_art"])
    qs = _apply_bool_filters(
        qs,
        params,
        [
            "mengenmaessig",
            "bandenmaessig",
            "gewerbsmaessig",
            "anstaltentreffen",
            "mehrfach",
            "beschaffungskriminalitaet",
            "vorbestraft",
            "vorbestraft_einschlaegig",
        ],
    )
    qs = _apply_sanktion_filters(qs, params)
    qs = qs.distinct()

    total = qs.count()
    limit = _clamp_limit(params.get("limit"))
    urteile = [
        {
            "id": u.id,
            "gericht": u.gericht,
            "urteilsdatum": str(u.urteilsdatum) if u.urteilsdatum else None,
            "fall_nr": u.fall_nr,
            "kanton": u.kanton.abk,
            "betm": [f"{b.art.name} ({b.menge_in_g}g{', rein' if b.rein else ''})" for b in u.betm.all()],
            "rolle": u.rolle.name,
            "mengenmaessig": u.mengenmaessig,
            "bandenmaessig": u.bandenmaessig,
            "gewerbsmaessig": u.gewerbsmaessig,
            "anstaltentreffen": u.anstaltentreffen,
            "mehrfach": u.mehrfach,
            "beschaffungskriminalitaet": u.beschaffungskriminalitaet,
            "deliktsertrag": u.deliktsertrag,
            "deliktsdauer_in_monaten": u.deliktsdauer_in_monaten,
            "vorbestraft": u.vorbestraft,
            "vorbestraft_einschlaegig": u.vorbestraft_einschlaegig,
            "hauptsanktion": u.get_hauptsanktion_display(),
            "freiheitsstrafe_in_monaten": u.freiheitsstrafe_in_monaten,
            "anzahl_tagessaetze": u.anzahl_tagessaetze,
            "vollzug": u.get_vollzug_display(),
            "zusammenfassung": u.zusammenfassung[:ZUSAMMENFASSUNG_MAX_CHARS],
            "detail_url": reverse("betmurteil_detail", args=[u.id]),
        }
        for u in qs.order_by("-urteilsdatum")[:limit]
    ]
    return {"total_treffer": total, "angezeigt": len(urteile), "urteile": urteile}


# --- search_sexualdelikt_urteile -----------------------------------------------------------

SEARCH_SEXUALDELIKT_TOOL = {
    "name": "search_sexualdelikt_urteile",
    "description": (
        "Durchsucht die kuratierte Datenbank erstinstanzlicher Strafzumessungsentscheide zu "
        "Sexualdelikten. Liefert konkrete, dokumentierte Präjudizien mit ausgesprochener "
        "Sanktion. Nutze dieses Tool IMMER, wenn die Anfrage ein Sexualdelikt betrifft."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "hauptdelikt": {
                "type": "string",
                "description": "Name des Hauptdelikts (z.B. 'Vergewaltigung', 'sexuelle Nötigung') - Teilstring-Suche.",
            },
            "hauptdelikt_tatmittel": {
                "type": "string",
                "description": "Name des Tatmittels - Teilstring-Suche.",
            },
            "hauptdelikt_mehrfachbegehung": {"type": "boolean"},
            "hauptdelikt_taeter_opfer_beziehung": {
                "type": "string",
                "enum": [
                    "Ehegatte/Partner",
                    "Elternteil/Kind",
                    "entfernt verwandt",
                    "Bekannte",
                    "flüchtig Bekannt",
                    "Unbekannte",
                    "Beziehung unbekannt",
                ],
            },
            "hauptdelikt_opferalter": {
                "type": "string",
                "enum": ["unter_6", "unter_10", "unter_14", "unter_16", "unter_18", "erwachsen", "nicht bekannt"],
                "description": "Altersschwelle des (jüngsten) Opfers, z.B. 'unter_14' = unter 14 Jahren.",
            },
            "vorbestraft": {"type": "boolean"},
            "vorbestraft_einschlaegig": {"type": "boolean"},
            "hauptsanktion": {"type": "string", "enum": ["Freiheitsstrafe", "Geldstrafe", "Busse"]},
            "vollzug": {"type": "string", "enum": ["bedingt", "teilbedingt", "unbedingt"]},
            "limit": {
                "type": "integer",
                "description": f"Max. Trefferzahl, Default {DEFAULT_LIMIT}, Maximum {MAX_LIMIT}.",
            },
        },
    },
}


def execute_search_sexualdelikt_urteile(params: dict) -> dict:
    qs = SexualdeliktUrteil.objects.all()
    if params.get("hauptdelikt"):
        qs = qs.filter(hauptdelikt__name__icontains=params["hauptdelikt"])
    if params.get("hauptdelikt_tatmittel"):
        qs = qs.filter(hauptdelikt_tatmittel__name__icontains=params["hauptdelikt_tatmittel"])
    if params.get("hauptdelikt_taeter_opfer_beziehung"):
        qs = qs.filter(hauptdelikt_taeter_opfer_beziehung=params["hauptdelikt_taeter_opfer_beziehung"])
    if params.get("hauptdelikt_opferalter"):
        qs = qs.filter(hauptdelikt_opferalter=params["hauptdelikt_opferalter"])
    qs = _apply_bool_filters(
        qs, params, ["hauptdelikt_mehrfachbegehung", "vorbestraft", "vorbestraft_einschlaegig"]
    )
    qs = _apply_sanktion_filters(qs, params)

    total = qs.count()
    limit = _clamp_limit(params.get("limit"))
    urteile = [
        {
            "id": u.id,
            "gericht": u.gericht,
            "urteilsdatum": str(u.urteilsdatum) if u.urteilsdatum else None,
            "fall_nr": u.fall_nr,
            "kanton": u.kanton.abk,
            "hauptdelikt": u.hauptdelikt.name,
            "hauptdelikt_tatmittel": u.hauptdelikt_tatmittel.name,
            "hauptdelikt_mehrfachbegehung": u.hauptdelikt_mehrfachbegehung,
            "hauptdelikt_taeter_opfer_beziehung": u.hauptdelikt_taeter_opfer_beziehung,
            "hauptdelikt_opferalter": u.hauptdelikt_opferalter,
            "hauptdelikt_opfer_vorerfahrung": u.hauptdelikt_opfer_vorerfahrung,
            "vorbestraft": u.vorbestraft,
            "vorbestraft_einschlaegig": u.vorbestraft_einschlaegig,
            "hauptsanktion": u.get_hauptsanktion_display(),
            "freiheitsstrafe_in_monaten": u.freiheitsstrafe_in_monaten,
            "anzahl_tagessaetze": u.anzahl_tagessaetze,
            "vollzug": u.get_vollzug_display(),
            "zusammenfassung": u.zusammenfassung[:ZUSAMMENFASSUNG_MAX_CHARS],
            "detail_url": u.url_link or reverse("sexualurteil_detail", args=[u.id]),
        }
        for u in qs.order_by("-urteilsdatum")[:limit]
    ]
    return {"total_treffer": total, "angezeigt": len(urteile), "urteile": urteile}


# --- search_gewaltdelikt_urteile ------------------------------------------------------------

# Die Choice-Werte werden direkt aus dem Modell abgeleitet, damit Tool-Schema und DB nicht
# auseinanderlaufen (GewaltdeliktUrteil hat sieben Choice-Felder).
def _choices(field_choices) -> list[str]:
    return [value for value, _label in field_choices]


SEARCH_GEWALTDELIKT_TOOL = {
    "name": "search_gewaltdelikt_urteile",
    "description": (
        "Durchsucht die kuratierte Datenbank erstinstanzlicher Strafzumessungsentscheide zu "
        "Gewaltdelikten (Mord, vorsätzliche Tötung, Totschlag, fahrlässige Tötung, schwere "
        "und einfache Körperverletzung, Tätlichkeiten, Gefährdung des Lebens, Angriff, "
        "Raufhandel, Raub - je auch versucht). Liefert konkrete, dokumentierte Präjudizien "
        "mit ausgesprochener Sanktion. Nutze dieses Tool IMMER, wenn die Anfrage eines dieser "
        "Delikte betrifft."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "hauptdelikt": {
                "type": "string",
                "enum": _choices(GewaltdeliktUrteil.HAUPTDELIKT),
                "description": "Das Delikt, für welches die Einsatzstrafe gebildet wurde.",
            },
            "versuch": {
                "type": "boolean",
                "description": "Ob das Hauptdelikt beim Versuch geblieben ist (Art. 22 StGB).",
            },
            "tatmittel": {
                "type": "string",
                "enum": _choices(GewaltdeliktUrteil.TATMITTEL),
                "description": "Das beim Hauptdelikt eingesetzte Tatmittel.",
            },
            "vorsatzform": {
                "type": "string",
                "enum": _choices(GewaltdeliktUrteil.VORSATZFORM),
                "description": "Subjektiver Tatbestand des Hauptdelikts.",
            },
            "taeter_opfer_beziehung": {
                "type": "string",
                "enum": _choices(GewaltdeliktUrteil.BEZIEHUNG_CHOICES),
                "description": (
                    "Beziehung zwischen Täter und Opfer. 'Unbekannte' = das Opfer war eine "
                    "fremde Person; 'unbekannt' = Beziehung nicht dokumentiert."
                ),
            },
            "verletzungsfolge": {
                "type": "string",
                "enum": _choices(GewaltdeliktUrteil.VERLETZUNGSFOLGE),
                "description": "Schwerste eingetretene Verletzungsfolge beim Opfer.",
            },
            "angegriffenes_koerperteil": {
                "type": "string",
                "enum": _choices(GewaltdeliktUrteil.KOERPERTEIL),
                "description": "Vom Angriff hauptbetroffene Körperregion des Opfers.",
            },
            "substanzeinfluss": {
                "type": "string",
                "enum": _choices(GewaltdeliktUrteil.SUBSTANZEINFLUSS),
                "description": "Ob der Täter im Tatzeitpunkt unter Alkohol-/Drogeneinfluss stand.",
            },
            "opferzahl_min": {
                "type": "integer",
                "description": "Mindestzahl der vom Hauptdelikt betroffenen Opfer.",
            },
            "deliktssumme_min": {
                "type": "integer",
                "description": "Beutebetrag in CHF (nur bei Raub relevant), untere Grenze.",
            },
            "deliktssumme_max": {
                "type": "integer",
                "description": "Beutebetrag in CHF (nur bei Raub relevant), obere Grenze.",
            },
            "mehrfach": {"type": "boolean"},
            "waffe_gefaehrlicher_gegenstand": {
                "type": "boolean",
                "description": "Begehung mit Waffe oder gefährlichem Gegenstand.",
            },
            "bandenmaessig": {"type": "boolean"},
            "besondere_gefaehrlichkeit": {
                "type": "boolean",
                "description": "Besonders skrupellose/grausame Begehung.",
            },
            "lebensgefahr": {
                "type": "boolean",
                "description": "Herbeiführung einer Lebensgefahr für das Opfer.",
            },
            "vorbestraft": {"type": "boolean"},
            "vorbestraft_einschlaegig": {"type": "boolean"},
            "hauptsanktion": {"type": "string", "enum": ["Freiheitsstrafe", "Geldstrafe", "Busse"]},
            "vollzug": {"type": "string", "enum": ["bedingt", "teilbedingt", "unbedingt"]},
            "limit": {
                "type": "integer",
                "description": f"Max. Trefferzahl, Default {DEFAULT_LIMIT}, Maximum {MAX_LIMIT}.",
            },
        },
    },
}

GEWALTDELIKT_CHOICE_FILTER_FIELDS = [
    "hauptdelikt",
    "tatmittel",
    "vorsatzform",
    "taeter_opfer_beziehung",
    "verletzungsfolge",
    "angegriffenes_koerperteil",
    "substanzeinfluss",
]

GEWALTDELIKT_BOOL_FILTER_FIELDS = [
    "versuch",
    "mehrfach",
    "waffe_gefaehrlicher_gegenstand",
    "bandenmaessig",
    "besondere_gefaehrlichkeit",
    "lebensgefahr",
    "vorbestraft",
    "vorbestraft_einschlaegig",
]


def execute_search_gewaltdelikt_urteile(params: dict) -> dict:
    qs = GewaltdeliktUrteil.objects.all()
    for field in GEWALTDELIKT_CHOICE_FILTER_FIELDS:
        if params.get(field):
            qs = qs.filter(**{field: params[field]})
    if params.get("opferzahl_min") is not None:
        qs = qs.filter(opferzahl__gte=params["opferzahl_min"])
    if params.get("deliktssumme_min") is not None:
        qs = qs.filter(deliktssumme__gte=params["deliktssumme_min"])
    if params.get("deliktssumme_max") is not None:
        qs = qs.filter(deliktssumme__lte=params["deliktssumme_max"])
    qs = _apply_bool_filters(qs, params, GEWALTDELIKT_BOOL_FILTER_FIELDS)
    qs = _apply_sanktion_filters(qs, params)

    total = qs.count()
    limit = _clamp_limit(params.get("limit"))
    urteile = [
        {
            "id": u.id,
            "gericht": u.gericht,
            "urteilsdatum": str(u.urteilsdatum) if u.urteilsdatum else None,
            "fall_nr": u.fall_nr,
            "kanton": u.kanton.abk,
            "hauptdelikt": u.get_hauptdelikt_display(),
            "versuch": u.versuch,
            "tatmittel": u.get_tatmittel_display(),
            "vorsatzform": u.get_vorsatzform_display(),
            "mehrfach": u.mehrfach,
            "opferzahl": u.opferzahl,
            "taeter_opfer_beziehung": u.get_taeter_opfer_beziehung_display(),
            "verletzungsfolge": u.get_verletzungsfolge_display(),
            "angegriffenes_koerperteil": u.get_angegriffenes_koerperteil_display(),
            "substanzeinfluss": u.get_substanzeinfluss_display(),
            "waffe_gefaehrlicher_gegenstand": u.waffe_gefaehrlicher_gegenstand,
            "bandenmaessig": u.bandenmaessig,
            "besondere_gefaehrlichkeit": u.besondere_gefaehrlichkeit,
            "lebensgefahr": u.lebensgefahr,
            "deliktssumme": u.deliktssumme,
            "deliktsscore_uebrige_delikte": u.deliktsscore_uebrige_delikte,
            "vorbestraft": u.vorbestraft,
            "vorbestraft_einschlaegig": u.vorbestraft_einschlaegig,
            "hauptsanktion": u.get_hauptsanktion_display(),
            "freiheitsstrafe_in_monaten": u.freiheitsstrafe_in_monaten,
            "anzahl_tagessaetze": u.anzahl_tagessaetze,
            "vollzug": u.get_vollzug_display(),
            "kurzsachverhalt": u.kurzsachverhalt or None,
            "zusammenfassung": u.zusammenfassung[:ZUSAMMENFASSUNG_MAX_CHARS],
            "detail_url": reverse("gewalturteil_detail", args=[u.id]),
            "pdf_url": u.url_link or None,
        }
        for u in qs.order_by("-urteilsdatum")[:limit]
    ]
    return {"total_treffer": total, "angezeigt": len(urteile), "urteile": urteile}


CUSTOM_TOOLS = [
    SEARCH_VERMOEGENSDELIKT_TOOL,
    SEARCH_BETM_TOOL,
    SEARCH_SEXUALDELIKT_TOOL,
    SEARCH_GEWALTDELIKT_TOOL,
]

TOOL_EXECUTORS = {
    "search_vermoegensdelikt_urteile": execute_search_vermoegensdelikt_urteile,
    "search_betm_urteile": execute_search_betm_urteile,
    "search_sexualdelikt_urteile": execute_search_sexualdelikt_urteile,
    "search_gewaltdelikt_urteile": execute_search_gewaltdelikt_urteile,
}
