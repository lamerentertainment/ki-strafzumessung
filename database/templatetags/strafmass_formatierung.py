from django import template

register = template.Library()

# Platzhalterwert fuer freiheitsstrafe_in_monaten, mit dem eine lebenslaengliche
# Freiheitsstrafe codiert wird (das Feld selbst kennt keinen eigenen Wert dafuer).
LEBENSLAENGLICH_PLATZHALTER = 999


@register.filter
def positives_vorzeichen(wert):
    """
    Liefert "+" für positive Zahlen, sonst einen leeren String (negative Zahlen
    tragen ihr Minus bereits selbst). Für Differenzanzeigen wie
    "Differenz: {{ diff|positives_vorzeichen }} {{ diff }}" gedacht.
    """
    try:
        return "+" if wert is not None and wert > 0 else ""
    except TypeError:
        return ""


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
    angepasste_einheit = "Monat" if einheit == "Monate" and monate_int == 1 else einheit
    return f"{monate_int} {angepasste_einheit}"


@register.filter
def freiheitsstrafe_detail_anzeige(monate):
    """
    Formatiert einen freiheitsstrafe_in_monaten-Wert fuer die Detailansicht.

    Stehen bei der Sanktionsdauer ueber 12 Monate, wird in einer Klammerbemerkung
    die Anzahl Jahre und Monate angezeigt (unter Wiederverwendung von
    freiheitsstrafe_jahre_monate_anzeige aus der Listenansicht).
    - 18  -> "18 Monate (1 Jahr 6 Monate)"
    - 24  -> "24 Monate (2 Jahre)"
    - 12  -> "12 Monate"
    - 6   -> "6 Monate"
    - 1   -> "1 Monat"
    - 999 -> "lebenslänglich"
    """
    if monate is None:
        return ""
    try:
        monate_int = int(monate)
    except (TypeError, ValueError):
        return f"{monate} Monate"
    if monate_int == LEBENSLAENGLICH_PLATZHALTER:
        return "lebenslänglich"
    einheit = "Monat" if monate_int == 1 else "Monate"
    basis = f"{monate_int} {einheit}"
    if monate_int > 12:
        return f"{basis} ({freiheitsstrafe_jahre_monate_anzeige(monate_int)})"
    return basis


@register.filter
def freiheitsstrafe_jahre_monate_anzeige(monate):
    """
    Formatiert einen freiheitsstrafe_in_monaten-Wert als "X Jahre Y Monate"
    (Tabellenanzeige, Umkehrung von freiheitsstrafe_anzeige: dort steht die
    Monatszahl im Vordergrund und Jahre/Monate im Tooltip, hier umgekehrt).

    Unter 12 Monaten liefert es schlicht "X Monate" (Jahre wären 0), der
    Platzhalter 999 weiterhin "lebenslänglich".
    """
    if monate is None:
        return ""
    try:
        monate_int = int(monate)
    except (TypeError, ValueError):
        return str(monate)
    if monate_int == LEBENSLAENGLICH_PLATZHALTER:
        return "lebenslänglich"
    if monate_int < 12:
        return f"{monate_int} {'Monat' if monate_int == 1 else 'Monate'}"
    jahre, rest = divmod(monate_int, 12)
    teile = [f"{jahre} {'Jahr' if jahre == 1 else 'Jahre'}"]
    if rest:
        teile.append(f"{rest} {'Monat' if rest == 1 else 'Monate'}")
    return " ".join(teile)


@register.filter
def freiheitsstrafe_monate_tooltip(monate):
    """
    Liefert den data-tt-Tooltiptext mit der Monats-Gesamtzahl, als Gegenstueck
    zu freiheitsstrafe_jahre_monate_anzeige. Nur ab 12 Monaten nicht-leer, da
    die Jahre/Monate-Anzeige darunter ohnehin schon die Monatszahl zeigt
    (analog zur Schwelle von jahreMonateTitel() in filter.js).
    """
    if monate is None:
        return ""
    try:
        monate_int = int(monate)
    except (TypeError, ValueError):
        return ""
    if monate_int == LEBENSLAENGLICH_PLATZHALTER or monate_int < 12:
        return ""
    return f"{monate_int} Monate"
