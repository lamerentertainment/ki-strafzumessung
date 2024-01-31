from django import template
import math

register = template.Library()


@register.filter
def prognosebereich_angeben(prognose_float):

    def erste_ziffer_nach_dem_komma(zahl):
        zahl = float(zahl)
        nachkommastelle = abs(zahl) % 1  # Extrahiere die Nachkommastelle (nur positive Werte verwenden)
        if nachkommastelle == 0:
            return 0  # Keine Ziffer nach dem Komma
        else:
            nachkommastelle *= 10
            erste_ziffer = int(nachkommastelle)
            return erste_ziffer

    if erste_ziffer_nach_dem_komma(prognose_float) in [1, 2]:
        return f'zwischen {str(math.floor(prognose_float-2))} und {str(math.ceil(prognose_float))}'

    elif erste_ziffer_nach_dem_komma(prognose_float) in [3, 4, 5, 6, 7]:
        return f'zwischen {str(math.floor(prognose_float-1))} und {str(math.ceil(prognose_float+1))}'

    elif erste_ziffer_nach_dem_komma(prognose_float) is 0:
        return f'zwischen {str(math.floor(prognose_float)-1.5)} und {str(math.ceil(prognose_float)+1.5)}'

    elif erste_ziffer_nach_dem_komma(prognose_float) in [8, 9]:
        return f'zwischen {str(math.floor(prognose_float))} und {str(math.ceil(prognose_float+2))}'

@register.filter
def prognosebereich_angeben_fuer_geldstrafe(prognose_float):
    """Die Prognosewerte werden mit 30 multipliziert, wenn eine Geldstrafe prognostiziert wird"""

    def erste_ziffer_nach_dem_komma(zahl):
        zahl = float(zahl)
        nachkommastelle = abs(zahl) % 1  # Extrahiere die Nachkommastelle (nur positive Werte verwenden)
        if nachkommastelle == 0:
            return 0  # Keine Ziffer nach dem Komma
        else:
            nachkommastelle *= 10
            erste_ziffer = int(nachkommastelle)
            return erste_ziffer

    if erste_ziffer_nach_dem_komma(prognose_float) in [1, 2]:
        return f'zwischen {str(math.floor(prognose_float-2)*30)} und {str(math.ceil(prognose_float)*30)}'

    elif erste_ziffer_nach_dem_komma(prognose_float) in [3, 4, 5, 6, 7]:
        return f'zwischen {str(math.floor(prognose_float-1)*30)} und {str(math.ceil(prognose_float+1)*30)}'

    elif erste_ziffer_nach_dem_komma(prognose_float) is 0:
        return f'zwischen {str(math.floor(prognose_float)-1.5*30)} und {str(math.ceil(prognose_float)+1.5*30)}'

    elif erste_ziffer_nach_dem_komma(prognose_float) in [8, 9]:
        return f'zwischen {str(math.floor(prognose_float)*30)} und {str(math.ceil(prognose_float+2)*30)}'
