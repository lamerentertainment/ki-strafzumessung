from django import template

register = template.Library()

# Platzhalterwert fuer freiheitsstrafe_in_monaten, mit dem eine lebenslaengliche
# Freiheitsstrafe codiert wird (das Feld selbst kennt keinen eigenen Wert dafuer).
LEBENSLAENGLICH_PLATZHALTER = 999


@register.filter
def freiheitsstrafe_anzeige(monate, einheit="Monate"):
    """
    Formatiert einen freiheitsstrafe_in_monaten-Wert fuer die Anzeige.

    Der Platzhalterwert 999 steht konventionsgemaess fuer eine lebenslaengliche
    Freiheitsstrafe und wird unabhaengig von der Einheit als "lebenslänglich"
    statt als z.B. "999 Monate" ausgegeben.

    Nutzung: {{ urteil.freiheitsstrafe_in_monaten|freiheitsstrafe_anzeige }}
    liefert "18 Monate" bzw. "lebenslänglich"; mit abweichender Grammatik
    (z.B. Dativ) laesst sich die Einheit ueberschreiben:
    {{ nachbar.freiheitsstrafe_in_monaten|freiheitsstrafe_anzeige:"Monaten" }}
    """
    if monate is None:
        return ""
    try:
        monate_int = int(monate)
    except (TypeError, ValueError):
        return f"{monate} {einheit}"
    if monate_int == LEBENSLAENGLICH_PLATZHALTER:
        return "lebenslänglich"
    return f"{monate_int} {einheit}"
