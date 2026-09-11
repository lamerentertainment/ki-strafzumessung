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

from django.db import models

# Feldtypen, die das Frontend kennt
TYP_CHOICE = "choice"  # Chip-Reihe, Mehrfachauswahl (ODER)
TYP_BOOL = "bool"  # Dreizustands-Schalter egal/ja/nein
TYP_NUMBER = "number"  # Von/Bis-Zahlenpaar
TYP_DATE = "date"  # Von/Bis-Datumspaar
TYP_MULTI = "multi"  # M2M, Chips, "enthaelt mindestens eines"


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


def _optionen(model, feld, queryset):
    """Auswahlwerte eines Chip-Feldes, immer nur die im Bestand vorkommenden."""
    if feld.choices:
        vorhanden = set(queryset.values_list(feld.name, flat=True))
        return [
            {"value": str(wert), "label": str(bezeichnung)}
            for wert, bezeichnung in feld.choices
            if wert in vorhanden
        ]
    if isinstance(feld, (models.ForeignKey, models.ManyToManyField)):
        related = feld.related_model
        namensfeld = "abk" if hasattr(related, "abk") else "name"
        werte = queryset.values_list(f"{feld.name}__{namensfeld}", flat=True)
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


def _ohne_filterwirkung(eintrag):
    """Trifft zu, wenn ein Feld im Bestand keine Unterscheidung erlaubt."""
    if eintrag["typ"] == TYP_CHOICE:
        return len(eintrag["optionen"]) < 2
    if eintrag["typ"] == TYP_MULTI:
        return len(eintrag["optionen"]) == 0
    if eintrag["typ"] in (TYP_NUMBER, TYP_DATE):
        return eintrag["min"] is None or eintrag["min"] == eintrag["max"]
    return False


def filterspezifikation_erstellen(model, config, queryset=None):
    """Baut die Gruppen-/Feldstruktur fuer das Filterpanel."""
    queryset = model.objects.all() if queryset is None else queryset
    labels = config.get("labels", {})
    einheiten = config.get("einheiten", {})
    primaer = config.get("primaer", [])

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
                eintrag["optionen"] = _optionen(model, feld, queryset)
            if typ in (TYP_NUMBER, TYP_DATE):
                eintrag["min"], eintrag["max"] = _grenzwerte(feld, queryset)
            if config.get("einwertige_ausblenden", True) and _ohne_filterwirkung(
                eintrag
            ):
                # Felder, die im Bestand nur einen einzigen Wert kennen (oder
                # durchwegs leer sind), taugen nicht als Filter und wuerden das
                # Panel nur aufblaehen.
                continue
            felder.append(eintrag)
            alle_felder[feldname] = eintrag
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


def _feldwert(objekt, feld):
    """Normalisiert einen Feldwert fuer die JSON-Uebergabe ans Frontend."""
    wert = getattr(objekt, feld.name, None)
    if isinstance(feld, models.ManyToManyField):
        return sorted(str(eintrag) for eintrag in wert.all())
    if isinstance(feld, models.ForeignKey):
        return str(wert) if wert is not None else None
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
    for sortierfeld in spezifikation.get("sortierfelder", []):
        if sortierfeld["name"] not in feldnamen:
            feldnamen.append(sortierfeld["name"])
    felder = [model._meta.get_field(name) for name in feldnamen]
    volltextfelder = config.get("volltextfelder", [])

    datensaetze = {}
    for objekt in queryset:
        werte = {feld.name: _feldwert(objekt, feld) for feld in felder}
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
