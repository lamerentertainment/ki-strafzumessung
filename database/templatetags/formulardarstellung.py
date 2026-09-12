from django import forms
from django import template

register = template.Library()


@register.filter
def widget_typ(bound_field):
    """Grobe Widget-Kategorie eines Formularfelds fuer die Template-Darstellung.

    Bootstrap braucht je nach Eingabetyp anderes Markup (Checkbox mit
    nachgestelltem Label, Textarea und Mehrfachauswahl ueber die volle Breite);
    im Template selbst laesst sich der Widget-Typ nicht zuverlaessig abfragen.
    """
    widget = bound_field.field.widget
    if isinstance(widget, forms.CheckboxInput):
        return "checkbox"
    if isinstance(widget, forms.Textarea):
        return "textarea"
    if isinstance(widget, forms.SelectMultiple):
        return "mehrfachauswahl"
    return "eingabe"
