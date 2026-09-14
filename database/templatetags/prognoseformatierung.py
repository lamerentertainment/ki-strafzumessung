from django import template

from database.prognoseverlauf import kernintervall

register = template.Library()


def _zahl_formatieren(wert):
    """Ganze Zahlen ohne Nachkommastelle, halbe mit – wie bisher ausgegeben."""
    if float(wert) == int(wert):
        return str(int(wert))
    return str(wert)


@register.filter
def prognosebereich_angeben(prognose_float):
    untere, obere = kernintervall(prognose_float)
    return f"zwischen {_zahl_formatieren(untere)} und {_zahl_formatieren(obere)}"


@register.filter
def prognosebereich_angeben_fuer_geldstrafe(prognose_float):
    """Die Prognosewerte werden mit 30 multipliziert, wenn eine Geldstrafe prognostiziert wird"""
    untere, obere = kernintervall(prognose_float, geldstrafe=True)
    return f"zwischen {_zahl_formatieren(untere)} und {_zahl_formatieren(obere)}"
