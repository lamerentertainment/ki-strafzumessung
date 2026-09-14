"""Farbverlauf für die Darstellung der Strafmassprognose.

Statt die prognostizierten Zahlenwerte auszuschreiben, wird die Prognose als
Farbverlauf auf einer Monats- bzw. Tagessatzachse gezeigt: Der voll gefärbte
Kern liegt mittig über dem Prognosewert und ist `KERNBREITE_IN_MONATEN` breit,
nach beiden Seiten blendet der Verlauf über `AUSBLENDUNG_IN_MONATEN` zur
Seitenfarbe aus.

Die Herleitung des Bereichs aus der ersten Nachkommastelle des Prognosewerts
gilt nur noch für die Einschätzung der Präjudizien; sie lebt dort in
`ai_utils.nachbar_mit_sanktionsbewertung_anreichern` bzw.
`ai_utils.betm_nachbarobjekt_mit_sanktionsbewertung_anreichern` und hat mit
diesem Modul nichts zu tun.

Die Berechnung ist eine reine Funktion des Prognosewerts – kein zusätzliches
Modell, keine zusätzliche Abhängigkeit. Das Ergebnis ist ein fertiger
CSS-`linear-gradient` samt Achsenbeschriftung, den das Template nur noch setzt.
"""

import math

# Breite des voll gefärbten Kerns und der Ausblendung je Seite, in Monaten.
# Der Kern liegt mittig über dem Prognosewert.
KERNBREITE_IN_MONATEN = 3
AUSBLENDUNG_IN_MONATEN = 3

# Betäubungsmitteldelikte: Der Ermessensspielraum ist dort grösser und die
# erfasste Rechtsprechung streut stärker, deshalb ein breiterer Kern und eine
# breitere Ausblendung als bei den Vermögensdelikten.
BETM_KERNBREITE_IN_MONATEN = 4
BETM_AUSBLENDUNG_IN_MONATEN = 4

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


def _achsenschritt(spanne):
    """Rundes Schrittmass, das die Achse mit etwa sechs Marken beschriftet."""
    roh = spanne / 6
    for kandidat in (1, 2, 3, 5, 10, 15, 30, 60, 90, 120, 180, 360):
        if roh <= kandidat:
            return kandidat
    return 360


def verlauf_erstellen(
    prognose_float,
    geldstrafe=False,
    kernbreite_in_monaten=KERNBREITE_IN_MONATEN,
    ausblendung_in_monaten=AUSBLENDUNG_IN_MONATEN,
):
    """Baut den Farbverlauf samt Achse für eine Prognose.

    Der voll gefärbte Kern ist `kernbreite_in_monaten` breit und liegt mittig
    über dem Prognosewert; nach beiden Seiten blendet der Verlauf über
    `ausblendung_in_monaten` aus. Betäubungsmitteldelikte verwenden breitere
    Werte, weil der Ermessensspielraum dort grösser ist.

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

    faktor = TAGESSAETZE_PRO_MONAT if geldstrafe else 1
    mitte = prognose_float * faktor
    halbe_breite = kernbreite_in_monaten * faktor / 2
    untere, obere = mitte - halbe_breite, mitte + halbe_breite

    untere = max(untere, 0)
    if obere <= untere:
        return None

    ausblendung = ausblendung_in_monaten * faktor
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
