"""Farbverlauf für die Darstellung der Strafmassprognose.

Statt die prognostizierten Zahlenwerte auszuschreiben, wird die Prognose als
Farbverlauf auf einer Monats- bzw. Tagessatzachse gezeigt: Der voll gefärbte
Kern entspricht exakt dem Intervall, das bisher ausgeschrieben wurde (siehe
`prognoseformatierung.prognosebereich_angeben`), nach beiden Seiten blendet der
Verlauf über `AUSBLENDUNG_IN_MONATEN` zur Seitenfarbe aus.

Die Berechnung ist eine reine Funktion des Prognosewerts – kein zusätzliches
Modell, keine zusätzliche Abhängigkeit. Das Ergebnis ist ein fertiger
CSS-`linear-gradient` samt Achsenbeschriftung, den das Template nur noch setzt.
"""

import math

# Breite der Ausblendung je Seite, in Monaten.
AUSBLENDUNG_IN_MONATEN = 3

# Tagessätze pro Monat – dieselbe Umrechnung, die auch das Urteilsmodell
# verwendet, wenn eine Geldstrafe als Zielwert dient.
TAGESSAETZE_PRO_MONAT = 30

# Sequenzielle Blau-Rampe, vom Kern nach aussen. Ein Farbton, hell werdend –
# eine Verlaufsachse darf keine Farbtöne wechseln, sonst liest sie sich als
# Kategorie statt als Intensität.
RAMPE = [
    "#184f95",
    "#256abf",
    "#3987e5",
    "#6da7ec",
    "#9ec5f4",
    "#cde2fb",
    "#ffffff",
]


def _erste_ziffer_nach_dem_komma(zahl):
    zahl = float(zahl)
    nachkommastelle = abs(zahl) % 1
    if nachkommastelle == 0:
        return 0
    return int(nachkommastelle * 10)


def kernintervall(prognose_float, geldstrafe=False):
    """Untere und obere Grenze des voll gefärbten Kerns.

    Entspricht exakt den Grenzen, die `prognosebereich_angeben` bzw.
    `prognosebereich_angeben_fuer_geldstrafe` bisher ausgeschrieben haben – bei
    einer Geldstrafe in Tagessätzen, sonst in Monaten. Die beiden Varianten
    runden in der Null-Nachkommastellen-Verzweigung unterschiedlich; das ist
    historisch so gewachsen und wird hier bewusst beibehalten, damit sich die
    ausgewiesenen Werte durch die Umstellung auf den Farbverlauf nicht ändern.
    """
    prognose_float = float(prognose_float)
    erste_ziffer = _erste_ziffer_nach_dem_komma(prognose_float)

    if erste_ziffer in (1, 2):
        untere, obere = math.floor(prognose_float - 2), math.ceil(prognose_float)
    elif erste_ziffer in (3, 4, 5, 6, 7):
        untere, obere = math.floor(prognose_float - 1), math.ceil(prognose_float + 1)
    elif erste_ziffer == 0:
        if geldstrafe:
            untere, obere = (
                math.floor(prognose_float - 1.5),
                math.ceil(prognose_float + 1.5),
            )
        else:
            untere, obere = (
                math.floor(prognose_float) - 1.5,
                math.ceil(prognose_float) + 1.5,
            )
    else:
        untere, obere = math.floor(prognose_float), math.ceil(prognose_float + 2)

    if geldstrafe:
        untere *= TAGESSAETZE_PRO_MONAT
        obere *= TAGESSAETZE_PRO_MONAT

    return untere, obere


def _achsenschritt(spanne):
    """Rundes Schrittmass, das die Achse mit etwa sechs Marken beschriftet."""
    roh = spanne / 6
    for kandidat in (1, 2, 3, 5, 10, 15, 30, 60, 90, 120, 180, 360):
        if roh <= kandidat:
            return kandidat
    return 360


def verlauf_erstellen(prognose_float, geldstrafe=False):
    """Baut den Farbverlauf samt Achse für eine Prognose.

    Gibt ein Dict mit den Schlüsseln `gradient` (fertiger CSS-Wert), `ticks`
    (Liste von `{"wert", "position"}` für die Achsenbeschriftung) und
    `achstitel` zurück – oder `None`, wenn sich aus dem Prognosewert kein
    sinnvoller Verlauf ableiten lässt.
    """
    try:
        prognose_float = float(prognose_float)
    except (TypeError, ValueError):
        return None

    if prognose_float <= 0:
        return None

    untere, obere = kernintervall(prognose_float, geldstrafe=geldstrafe)
    untere = max(untere, 0)
    if obere <= untere:
        return None

    ausblendung = AUSBLENDUNG_IN_MONATEN * (
        TAGESSAETZE_PRO_MONAT if geldstrafe else 1
    )
    links = max(untere - ausblendung, 0)
    rechts = obere + ausblendung
    spanne = rechts - links
    if spanne <= 0:
        return None

    def position(wert):
        """Wert auf der Achse in Prozent der Balkenbreite."""
        return (wert - links) / spanne * 100

    # Links weiss -> voll, Kern durchgehend voll, rechts voll -> weiss.
    stufen = len(RAMPE) - 1
    stops = []
    for i, farbe in enumerate(reversed(RAMPE)):
        stops.append(f"{farbe} {position(links + (untere - links) * i / stufen):.2f}%")
    stops.append(f"{RAMPE[0]} {position(obere):.2f}%")
    for i, farbe in enumerate(RAMPE):
        if i == 0:
            continue
        stops.append(f"{farbe} {position(obere + (rechts - obere) * i / stufen):.2f}%")

    schritt = _achsenschritt(spanne)
    ticks = []
    wert = math.ceil(links / schritt) * schritt
    while wert <= rechts:
        # Die Position geht als fertiger String ins Template: bei LANGUAGE_CODE
        # 'de-ch' würde Django eine Fliesskommazahl lokalisiert ausgeben und mit
        # einem Dezimalkomma den CSS-Wert zerstören.
        ticks.append({"wert": int(wert), "position": f"{position(wert):.2f}"})
        wert += schritt

    return {
        "gradient": "linear-gradient(90deg, " + ", ".join(stops) + ")",
        "ticks": ticks,
        "achstitel": (
            "Geldstrafe in Tagessätzen" if geldstrafe else "Freiheitsstrafe in Monaten"
        ),
    }
