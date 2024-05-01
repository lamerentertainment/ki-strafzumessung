from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.filter
def formatieren_und_illegitim_hervorheben(name_sachverhaltskriterium):
    capitalized_sachverhaltskriterium = name_sachverhaltskriterium.capitalize()
    if capitalized_sachverhaltskriterium == "Einschlaegig_vorbestraft":
        capitalized_sachverhaltskriterium = "einschlägige Vorstrafe"
    if capitalized_sachverhaltskriterium == "Bandenmaessig":
        capitalized_sachverhaltskriterium = "bandenmässige Qualifikation"
    if capitalized_sachverhaltskriterium == "Gewerbsmaessig":
        capitalized_sachverhaltskriterium = "gewerbsmaessige Qualifikation"
    if capitalized_sachverhaltskriterium == "Nationalitaet":
        capitalized_sachverhaltskriterium = "Nationalität"
    if capitalized_sachverhaltskriterium == "Geschlecht_weiblich":
        capitalized_sachverhaltskriterium = "Geschlecht"
    if capitalized_sachverhaltskriterium == "Menge betäubungsmittel":
        capitalized_sachverhaltskriterium = "Betäubungsmittelmenge"
    if capitalized_sachverhaltskriterium == "Mengenmaessig_true":
        capitalized_sachverhaltskriterium = "mengenmässige Qualifikation"
    if capitalized_sachverhaltskriterium == "Bandenmaessig_true":
        capitalized_sachverhaltskriterium = "bandenmässige Qualifikation"
    if capitalized_sachverhaltskriterium == "Gewerbsmaessig_true":
        capitalized_sachverhaltskriterium = "gewerbsmässige Qualifikation"
    if capitalized_sachverhaltskriterium == "Deliktsdauer_in_monaten":
        capitalized_sachverhaltskriterium = "Deliktsdauer in Monaten"
    if capitalized_sachverhaltskriterium == "Beschaffungskriminalitaet_true":
        capitalized_sachverhaltskriterium = "Beschaffungskriminalität"
    if capitalized_sachverhaltskriterium == "Vorbestraft_true":
        capitalized_sachverhaltskriterium = "Vorstrafe"
    if capitalized_sachverhaltskriterium == "Vorbestraft_einschlaegig_true":
        capitalized_sachverhaltskriterium = "einschlägige Vorstrafe"
    if capitalized_sachverhaltskriterium == "Mehrfach_true":
        capitalized_sachverhaltskriterium = "mehrfache Begehung"
    if capitalized_sachverhaltskriterium == "Anstaltentreffen_true":
        capitalized_sachverhaltskriterium = "Privilegierung Anstaltentreffen"
    if capitalized_sachverhaltskriterium in ["Nationalität", "Geschlecht", "Gericht"]:
        return mark_safe(f'<b>{capitalized_sachverhaltskriterium}</b>')
    else:
        return f'{capitalized_sachverhaltskriterium}'