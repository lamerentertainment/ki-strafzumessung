from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.filter
def illegitim_hervorheben(name_sachverhaltskriterium):
    capitalized_sachverhaltskrtierium = name_sachverhaltskriterium.capitalize()
    if capitalized_sachverhaltskrtierium == "Einschlaegig_vorbestraft":
        capitalized_sachverhaltskrtierium = "einschlägig vorbestraft"
    if capitalized_sachverhaltskrtierium == "Bandenmaessig":
        capitalized_sachverhaltskrtierium = "bandenmässig"
    if capitalized_sachverhaltskrtierium == "Gewerbsmaessig":
        capitalized_sachverhaltskrtierium = "gewerbsmaessig"
    if capitalized_sachverhaltskrtierium == "Nationalitaet":
        capitalized_sachverhaltskrtierium = "Nationalität"
    if capitalized_sachverhaltskrtierium in ["Nationalität", "Geschlecht", "Gericht"]:
        return mark_safe(f'<b>{capitalized_sachverhaltskrtierium}</b>')
    else:
        return f'{capitalized_sachverhaltskrtierium}'