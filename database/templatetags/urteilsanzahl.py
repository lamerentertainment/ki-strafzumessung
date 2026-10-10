from django import template

from database.models import BetmUrteil, Urteil

register = template.Library()

_MODELLE = {"betm": BetmUrteil, "vermoegen": Urteil}


@register.simple_tag
def anzahl_ki_urteile(deliktsbereich):
    """
    Anzahl Urteile, die ins KI-Modell des Deliktsbereichs ("betm" bzw.
    "vermoegen") einfliessen (in_ki_modell=True). Als Template-Tag, weil die
    Prognose-Views das Template aus mehreren Zweigen mit je eigenem Kontext
    rendern.
    """
    return _MODELLE[deliktsbereich].objects.filter(in_ki_modell=True).count()
