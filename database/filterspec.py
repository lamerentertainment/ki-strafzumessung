"""
Generierung der Filterspezifikation fuer die Datenbankansichten.

Die Spezifikation wird aus dem Modell-``_meta`` abgeleitet und pro Modell nur
noch durch eine kleine Konfiguration (Gruppierung, Labels, Ausschluesse)
ergaenzt. Neue Modellfelder erscheinen dadurch automatisch im Filterpanel,
sobald sie in einer Gruppe aufgefuehrt werden.

Die eigentliche Filterung geschieht clientseitig (Alpine.js, siehe
``database/static/database/filter.js``); hier werden lediglich die
Bedienelemente beschrieben und die Datensaetze in eine schlanke
JSON-Struktur normalisiert.
"""

from django.core.exceptions import FieldDoesNotExist
from django.db import models

# Feldtypen, die das Frontend kennt
TYP_CHOICE = "choice"  # Chip-Reihe, Mehrfachauswahl (ODER)
TYP_BOOL = "bool"  # Dreizustands-Schalter egal/ja/nein
TYP_NUMBER = "number"  # Von/Bis-Zahlenpaar
TYP_DATE = "date"  # Von/Bis-Datumspaar
TYP_MULTI = "multi"  # M2M, Chips, "enthaelt mindestens eines"


# Felder, welche die Kennzahlenleiste im Frontend auswertet (filter.js,
# kennzahlen()). Sie muessen in den Datensaetzen enthalten sein, auch wenn sie
# als Filter entfallen, weil sie im Bestand nur einen Wert kennen.
KENNZAHLENFELDER = ("hauptsanktion", "freiheitsstrafe_in_monaten", "vollzug")


def _hat_feld(model, feldname):
    try:
        model._meta.get_field(feldname)
        return True
    except FieldDoesNotExist:
        return False


def _ist_bool(feld):
    return isinstance(feld, models.BooleanField)


def _typ_ermitteln(feld):
    if _ist_bool(feld):
        return TYP_BOOL
    if isinstance(feld, models.ManyToManyField):
        return TYP_MULTI
    if isinstance(feld, models.DateField) and not isinstance(
        feld, models.DateTimeField
    ):
        return TYP_DATE
    if isinstance(feld, (models.IntegerField, models.FloatField, models.DurationField)):
        return TYP_NUMBER
    # CharField mit und ohne choices sowie ForeignKey werden als Chipreihe angeboten
    return TYP_CHOICE


def _label(feld, labels):
    if feld.name in labels:
        return labels[feld.name]
    if getattr(feld, "verbose_name", None) and feld.verbose_name != feld.name:
        return str(feld.verbose_name)
    return feld.name.replace("_", " ").capitalize()


def _beziehungspfad(feld, pfade):
    """
    Pfad innerhalb des verknuepften Modells, aus dem Auswahlwert und Anzeige
    stammen. Konfigurierbar, weil das verknuepfte Modell nicht immer selbst die
    sinnvolle Facette traegt: Bei ``BetmUrteil.betm`` ist jeder Datensatz durch
    die Menge einmalig, gefiltert werden soll aber nach der Substanz
    (``art__name``).
    """
    if feld.name in pfade:
        return pfade[feld.name]
    return "abk" if hasattr(feld.related_model, "abk") else "name"


def _optionen(model, feld, queryset, pfade):
    """Auswahlwerte eines Chip-Feldes, immer nur die im Bestand vorkommenden."""
    if feld.choices:
        vorhanden = set(queryset.values_list(feld.name, flat=True))
        return [
            {"value": str(wert), "label": str(bezeichnung)}
            for wert, bezeichnung in feld.choices
            if wert in vorhanden
        ]
    if isinstance(feld, (models.ForeignKey, models.ManyToManyField)):
        pfad = _beziehungspfad(feld, pfade)
        werte = queryset.values_list(f"{feld.name}__{pfad}", flat=True)
        werte = sorted({w for w in werte if w})
        return [{"value": w, "label": w} for w in werte]
    werte = sorted({w for w in queryset.values_list(feld.name, flat=True) if w})
    return [{"value": w, "label": w} for w in werte]


def _grenzwerte(feld, queryset):
    aggregat = queryset.aggregate(
        min=models.Min(feld.name), max=models.Max(feld.name)
    )
    minimum, maximum = aggregat["min"], aggregat["max"]
    if isinstance(feld, models.DurationField):
        minimum = _dauer_in_einheit(minimum, feld)
        maximum = _dauer_in_einheit(maximum, feld)
    if isinstance(feld, models.DateField) and not isinstance(feld, models.DateTimeField):
        minimum = minimum.isoformat() if minimum else None
        maximum = maximum.isoformat() if maximum else None
    return minimum, maximum


def _dauer_in_einheit(wert, feld):
    """DurationFields werden je nach Feld in Minuten oder Tagen dargestellt."""
    if wert is None:
        return None
    if "deliktsperiode" in feld.name:
        return round(wert.total_seconds() / 86400)
    return round(wert.total_seconds() / 60)


def _einheit(feld, einheiten):
    if feld.name in einheiten:
        return einheiten[feld.name]
    if isinstance(feld, models.DurationField):
        return "Tage" if "deliktsperiode" in feld.name else "Min."
    return ""


def _ohne_filterwirkung(eintrag, feld, queryset):
    """Trifft zu, wenn ein Feld im Bestand keine Unterscheidung erlaubt."""
    if eintrag["typ"] == TYP_CHOICE:
        return len(eintrag["optionen"]) < 2
    if eintrag["typ"] == TYP_MULTI:
        return len(eintrag["optionen"]) == 0
    if eintrag["typ"] in (TYP_NUMBER, TYP_DATE):
        return eintrag["min"] is None or eintrag["min"] == eintrag["max"]
    if eintrag["typ"] == TYP_BOOL:
        return len(set(queryset.values_list(feld.name, flat=True))) < 2
    return False


def filterspezifikation_erstellen(model, config, queryset=None):
    """Baut die Gruppen-/Feldstruktur fuer das Filterpanel."""
    queryset = model.objects.all() if queryset is None else queryset
    labels = config.get("labels", {})
    einheiten = config.get("einheiten", {})
    primaer = config.get("primaer", [])
    pfade = config.get("beziehungspfade", {})

    gruppen = []
    alle_felder = {}
    for gruppentitel, feldnamen in config["gruppen"]:
        felder = []
        for feldname in feldnamen:
            feld = model._meta.get_field(feldname)
            typ = _typ_ermitteln(feld)
            eintrag = {
                "name": feldname,
                "label": _label(feld, labels),
                "typ": typ,
                "hilfetext": str(getattr(feld, "help_text", "") or ""),
                "einheit": _einheit(feld, einheiten),
                "gruppe": gruppentitel,
            }
            if typ in (TYP_CHOICE, TYP_MULTI):
                eintrag["optionen"] = _optionen(model, feld, queryset, pfade)
                eintrag["pfad"] = _beziehungspfad(feld, pfade) if feld.is_relation else None
            if typ in (TYP_NUMBER, TYP_DATE):
                eintrag["min"], eintrag["max"] = _grenzwerte(feld, queryset)
            if config.get("einwertige_ausblenden", True) and _ohne_filterwirkung(
                eintrag, feld, queryset
            ):
                # Felder, die im Bestand nur einen einzigen Wert kennen (oder
                # durchwegs leer sind), taugen nicht als Filter und wuerden das
                # Panel nur aufblaehen.
                continue
            felder.append(eintrag)
            alle_felder[feldname] = eintrag
        if felder:
            # Gruppen, deren Felder saemtlich ohne Filterwirkung sind, entfallen
            gruppen.append({"titel": gruppentitel, "felder": felder})

    return {
        "gruppen": gruppen,
        "felder": list(alle_felder.values()),
        "primaer": [alle_felder[name] for name in primaer if name in alle_felder],
        "suchfelder_label": config.get(
            "suchfelder_label", "Fall-Nr., Gericht, Zusammenfassung"
        ),
        "sortierfelder": config.get("sortierfelder", []),
    }


def _durchlaufen(objekt, pfad):
    """Folgt einem ``a__b__c``-Pfad und gibt den Endwert als String zurueck."""
    ziel = objekt
    for teil in pfad.split("__"):
        ziel = getattr(ziel, teil, None) if ziel is not None else None
    return str(ziel) if ziel is not None else None


def _feldwert(objekt, feld, pfade):
    """Normalisiert einen Feldwert fuer die JSON-Uebergabe ans Frontend."""
    wert = getattr(objekt, feld.name, None)
    if isinstance(feld, models.ManyToManyField):
        pfad = _beziehungspfad(feld, pfade)
        werte = {_durchlaufen(eintrag, pfad) for eintrag in wert.all()}
        return sorted(w for w in werte if w is not None)
    if isinstance(feld, models.ForeignKey):
        if wert is None:
            return None
        return _durchlaufen(wert, _beziehungspfad(feld, pfade))
    if _ist_bool(feld):
        return bool(wert)
    if isinstance(feld, models.DurationField):
        return _dauer_in_einheit(wert, feld)
    if isinstance(feld, models.DateField) and not isinstance(feld, models.DateTimeField):
        return wert.isoformat() if wert else None
    if isinstance(feld, (models.IntegerField, models.FloatField)):
        return wert
    return str(wert) if wert is not None else None


def datensaetze_erstellen(model, config, queryset, spezifikation):
    """Erzeugt ``{pk: {feld: wert, ..., '_t': 'volltextblob'}}`` fuer Alpine."""
    feldnamen = [feld["name"] for feld in spezifikation["felder"]]
    zusaetzlich = [
        feld["name"] for feld in spezifikation.get("sortierfelder", [])
    ] + list(KENNZAHLENFELDER)
    for feldname in zusaetzlich:
        if feldname not in feldnamen and _hat_feld(model, feldname):
            feldnamen.append(feldname)
    felder = [model._meta.get_field(name) for name in feldnamen]
    volltextfelder = config.get("volltextfelder", [])
    pfade = config.get("beziehungspfade", {})

    datensaetze = {}
    for objekt in queryset:
        werte = {feld.name: _feldwert(objekt, feld, pfade) for feld in felder}
        textteile = []
        for pfad in volltextfelder:
            ziel = objekt
            for teil in pfad.split("__"):
                ziel = getattr(ziel, teil, None) if ziel is not None else None
            if ziel:
                textteile.append(str(ziel))
        werte["_t"] = " ".join(textteile).lower()
        datensaetze[str(objekt.pk)] = werte
    return datensaetze


# --- Konfiguration pro Modell -------------------------------------------------

SEXUALDELIKT_FILTER_CONFIG = {
    "primaer": ["hauptdelikt", "hauptsanktion", "vollzug"],
    "gruppen": [
        (
            "Fall & Gericht",
            ["gericht", "kanton", "urteilsdatum", "verfahrensart"],
        ),
        (
            "Täter",
            ["geschlecht", "nationalitaet", "vorbestraft", "vorbestraft_einschlaegig"],
        ),
        (
            "Hauptdelikt",
            [
                "hauptdelikt",
                "hauptdelikt_tatmittel",
                "hauptdelikt_mehrfachbegehung",
                "hauptdelikt_mehrfachbegehung_anzahl",
                "hauptdelikt_mehrfachbegehung_deliktsperiode",
                "hauptdelikt_deliktsdauer_bekannt",
                "hautpdelikt_deliktsdauer_einfachbegehung",
            ],
        ),
        (
            "Opfer",
            [
                "hauptdelikt_taeter_opfer_beziehung",
                "hauptdelikt_opferalter",
                "hauptdelikt_opfer_vorerfahrung",
            ],
        ),
        (
            "Weitere Delikte & Besonderheiten",
            [
                "sexualdelikte_zusaetzliche",
                "deliktsscore_uebrige_delikte",
                "besonderheiten",
            ],
        ),
        (
            "Sanktion",
            [
                "hauptsanktion",
                "freiheitsstrafe_in_monaten",
                "anzahl_tagessaetze",
                "vollzug",
            ],
        ),
    ],
    "labels": {
        "gericht": "Gericht",
        "kanton": "Kanton",
        "urteilsdatum": "Urteilsdatum",
        "verfahrensart": "Verfahrensart",
        "geschlecht": "Geschlecht Täter",
        "nationalitaet": "Nationalität Täter",
        "hauptdelikt_mehrfachbegehung_anzahl": "Anzahl Tatbegehungen",
        "hauptdelikt_mehrfachbegehung_deliktsperiode": "Deliktsperiode",
        "hauptdelikt_deliktsdauer_bekannt": "Deliktsdauer bekannt?",
        "hautpdelikt_deliktsdauer_einfachbegehung": "Deliktsdauer Einzeltat",
        "sexualdelikte_zusaetzliche": "Weitere Sexualdelikte",
        "deliktsscore_uebrige_delikte": "Deliktsscore übrige Delikte",
        "besonderheiten": "Besonderheiten",
        "hauptsanktion": "Hauptsanktion",
        "freiheitsstrafe_in_monaten": "Freiheitsstrafe",
        "anzahl_tagessaetze": "Geldstrafe",
        "vollzug": "Vollzug",
    },
    "einheiten": {
        "freiheitsstrafe_in_monaten": "Monate",
        "anzahl_tagessaetze": "Tagessätze",
        "hauptdelikt_mehrfachbegehung_anzahl": "Taten",
    },
    "volltextfelder": [
        "fall_nr",
        "gericht",
        "hauptdelikt__name",
        "hauptdelikt_tatmittel__name",
        "zusammenfassung",
        "bemerkungen",
    ],
    "suchfelder_label": "Fall-Nr., Gericht, Delikt, Zusammenfassung, Bemerkungen",
    "sortierfelder": [
        {"name": "fall_nr", "label": "Fall-Nr."},
        {"name": "urteilsdatum", "label": "Urteilsdatum"},
        {"name": "hauptdelikt", "label": "Hauptdelikt"},
        {"name": "freiheitsstrafe_in_monaten", "label": "Freiheitsstrafe"},
    ],
}


URTEIL_FILTER_CONFIG = {
    "primaer": ["hauptdelikt", "hauptsanktion", "vollzug"],
    "gruppen": [
        ("Fall & Gericht", ["gericht", "urteilsdatum", "verfahrensart"]),
        (
            "Täter",
            ["geschlecht", "nationalitaet", "vorbestraft", "vorbestraft_einschlaegig"],
        ),
        (
            "Hauptdelikt",
            [
                "hauptdelikt",
                "mehrfach",
                "gewerbsmaessig",
                "bandenmaessig",
                "deliktssumme",
            ],
        ),
        ("Weitere Delikte", ["nebenverurteilungsscore"]),
        (
            "Sanktion",
            [
                "hauptsanktion",
                "freiheitsstrafe_in_monaten",
                "anzahl_tagessaetze",
                "vollzug",
            ],
        ),
        ("Datenbank", ["in_ki_modell"]),
    ],
    "labels": {
        "gericht": "Gericht",
        "urteilsdatum": "Urteilsdatum",
        "verfahrensart": "Verfahrensart",
        "geschlecht": "Geschlecht Täter",
        "nationalitaet": "Nationalität Täter",
        "hauptdelikt": "Hauptdelikt",
        "mehrfach": "mehrfache Begehung",
        "bandenmaessig": "bandenmässig",
        "deliktssumme": "Deliktssumme",
        "nebenverurteilungsscore": "Nebenverurteilungsscore",
        "hauptsanktion": "Hauptsanktion",
        "freiheitsstrafe_in_monaten": "Freiheitsstrafe",
        "anzahl_tagessaetze": "Geldstrafe",
        "vollzug": "Vollzug",
        "in_ki_modell": "im KI-Modell berücksichtigt",
    },
    "einheiten": {
        "deliktssumme": "CHF",
        "freiheitsstrafe_in_monaten": "Monate",
        "anzahl_tagessaetze": "Tagessätze",
    },
    "volltextfelder": ["fall_nr", "gericht", "hauptdelikt", "zusammenfassung"],
    "suchfelder_label": "Fall-Nr., Gericht, Delikt, Zusammenfassung",
    "sortierfelder": [
        {"name": "fall_nr", "label": "Fall-Nr."},
        {"name": "urteilsdatum", "label": "Urteilsdatum"},
        {"name": "hauptdelikt", "label": "Hauptdelikt"},
        {"name": "deliktssumme", "label": "Deliktssumme"},
        {"name": "freiheitsstrafe_in_monaten", "label": "Freiheitsstrafe"},
    ],
}


BETM_FILTER_CONFIG = {
    "primaer": ["betm", "rolle", "vollzug"],
    "gruppen": [
        ("Fall & Gericht", ["gericht", "kanton", "urteilsdatum", "verfahrensart"]),
        (
            "Täter",
            [
                "geschlecht",
                "nationalitaet",
                "vorbestraft",
                "vorbestraft_einschlaegig",
                "beschaffungskriminalitaet",
            ],
        ),
        (
            "Betäubungsmittel & Tatbeitrag",
            ["betm", "rolle", "deliktsertrag", "deliktsdauer_in_monaten"],
        ),
        (
            "Qualifikationen",
            [
                "mengenmaessig",
                "bandenmaessig",
                "gewerbsmaessig",
                "anstaltentreffen",
                "mehrfach",
            ],
        ),
        ("Weitere Delikte", ["nebenverurteilungsscore"]),
        (
            "Sanktion",
            [
                "hauptsanktion",
                "freiheitsstrafe_in_monaten",
                "anzahl_tagessaetze",
                "vollzug",
            ],
        ),
        ("Datenbank", ["in_ki_modell"]),
    ],
    # Jeder Betm-Datensatz ist durch seine Menge einmalig; gefiltert wird nach
    # der Substanz.
    "beziehungspfade": {"betm": "art__name"},
    "labels": {
        "gericht": "Gericht",
        "kanton": "Kanton",
        "urteilsdatum": "Urteilsdatum",
        "verfahrensart": "Verfahrensart",
        "geschlecht": "Geschlecht Täter",
        "nationalitaet": "Nationalität Täter",
        "beschaffungskriminalitaet": "Beschaffungskriminalität",
        "betm": "Betäubungsmittel",
        "rolle": "Rolle im Handel",
        "deliktsertrag": "Deliktsertrag",
        "deliktsdauer_in_monaten": "Deliktsdauer",
        "mengenmaessig": "mengenmässig (Art. 19 II a)",
        "bandenmaessig": "bandenmässig (Art. 19 II b)",
        "gewerbsmaessig": "gewerbsmässig (Art. 19 II c)",
        "anstaltentreffen": "Anstaltentreffen",
        "mehrfach": "mehrfache Begehung",
        "nebenverurteilungsscore": "Nebenverurteilungsscore",
        "hauptsanktion": "Hauptsanktion",
        "freiheitsstrafe_in_monaten": "Freiheitsstrafe",
        "anzahl_tagessaetze": "Geldstrafe",
        "vollzug": "Vollzug",
        "in_ki_modell": "im KI-Modell berücksichtigt",
    },
    "einheiten": {
        "deliktsertrag": "CHF",
        "deliktsdauer_in_monaten": "Monate",
        "freiheitsstrafe_in_monaten": "Monate",
        "anzahl_tagessaetze": "Tagessätze",
    },
    "volltextfelder": ["fall_nr", "gericht", "rolle__name", "zusammenfassung"],
    "suchfelder_label": "Fall-Nr., Gericht, Rolle, Zusammenfassung",
    "sortierfelder": [
        {"name": "fall_nr", "label": "Fall-Nr."},
        {"name": "urteilsdatum", "label": "Urteilsdatum"},
        {"name": "rolle", "label": "Rolle"},
        {"name": "freiheitsstrafe_in_monaten", "label": "Freiheitsstrafe"},
    ],
}


GEWALTDELIKT_FILTER_CONFIG = {
    "primaer": ["hauptdelikt", "hauptsanktion", "vollzug"],
    "gruppen": [
        ("Fall & Gericht", ["gericht", "kanton", "urteilsdatum", "verfahrensart"]),
        (
            "Täter",
            [
                "geschlecht",
                "nationalitaet",
                "vorbestraft",
                "vorbestraft_einschlaegig",
                "substanzeinfluss",
            ],
        ),
        (
            "Hauptdelikt",
            ["hauptdelikt", "versuch", "tatmittel", "vorsatzform", "mehrfach"],
        ),
        (
            "Qualifikationen",
            [
                "waffe_gefaehrlicher_gegenstand",
                "bandenmaessig",
                "besondere_gefaehrlichkeit",
                "lebensgefahr",
            ],
        ),
        (
            "Opfer",
            [
                "taeter_opfer_beziehung",
                "opferzahl",
                "verletzungsfolge",
                "angegriffenes_koerperteil",
            ],
        ),
        (
            "Weitere Delikte & Besonderheiten",
            ["deliktssumme", "deliktsscore_uebrige_delikte", "besonderheiten"],
        ),
        (
            "Sanktion",
            [
                "hauptsanktion",
                "freiheitsstrafe_in_monaten",
                "anzahl_tagessaetze",
                "vollzug",
            ],
        ),
        ("Datenbank", ["in_ki_modell"]),
    ],
    "labels": {
        "gericht": "Gericht",
        "kanton": "Kanton",
        "urteilsdatum": "Urteilsdatum",
        "verfahrensart": "Verfahrensart",
        "geschlecht": "Geschlecht Täter",
        "nationalitaet": "Nationalität Täter",
        "hauptdelikt": "Hauptdelikt",
        "tatmittel": "Tatmittel",
        "mehrfach": "mehrfache Begehung",
        "bandenmaessig": "bandenmässig",
        "opferzahl": "Anzahl Opfer",
        "verletzungsfolge": "Verletzungsfolge",
        "deliktssumme": "Deliktssumme/Beute",
        "deliktsscore_uebrige_delikte": "Deliktsscore übrige Delikte",
        "besonderheiten": "Besonderheiten",
        "hauptsanktion": "Hauptsanktion",
        "freiheitsstrafe_in_monaten": "Freiheitsstrafe",
        "anzahl_tagessaetze": "Geldstrafe",
        "vollzug": "Vollzug",
        "in_ki_modell": "im KI-Modell berücksichtigt",
    },
    "einheiten": {
        "deliktssumme": "CHF",
        "freiheitsstrafe_in_monaten": "Monate",
        "anzahl_tagessaetze": "Tagessätze",
        "opferzahl": "Opfer",
    },
    "volltextfelder": [
        "fall_nr",
        "gericht",
        "hauptdelikt",
        "zusammenfassung",
        "bemerkungen",
    ],
    "suchfelder_label": "Fall-Nr., Gericht, Delikt, Zusammenfassung, Bemerkungen",
    "sortierfelder": [
        {"name": "fall_nr", "label": "Fall-Nr."},
        {"name": "urteilsdatum", "label": "Urteilsdatum"},
        {"name": "hauptdelikt", "label": "Hauptdelikt"},
        {"name": "freiheitsstrafe_in_monaten", "label": "Freiheitsstrafe"},
    ],
}
