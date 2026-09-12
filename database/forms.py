from django.forms import ModelForm
from django import forms
from .models import (
    Urteil,
    BetmUrteil,
    BetmArt,
    GewaltdeliktUrteil,
    Rolle,
    SexualdeliktUrteil,
)


class UrteilModelForm(ModelForm):
    class Meta:
        model = Urteil
        exclude = ["verfahrensart"]


class UrteilsEckpunkteAbfrageFormular(ModelForm):
    gleiches_hauptdelikt = forms.BooleanField(
        initial=True,
        required=False,
        label="Nur Präjudizen anzeigen, die dasselbe Hauptdelikt aufweisen",
        help_text="Wenn aktiviert, werden nur Präjudizien mit demselben Hauptdelikt wie "
                  "im Formular ausgewählt angezeigt.",
    )

    class Meta:
        model = Urteil
        fields = [
            "hauptdelikt",
            "deliktssumme",
            "nebenverurteilungsscore",
            "mehrfach",
            "gewerbsmaessig",
            "bandenmaessig",
            "vorbestraft",
            "vorbestraft_einschlaegig",
        ]


class BetmUrteilsEckpunkteAbfrageFormular(forms.Form):
    mengenmaessig = forms.BooleanField(
        initial=True,
        help_text="Verurteilung nach Art. 19 Abs. 2 lit. a BetmG",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    bandenmaessig = forms.BooleanField(
        help_text="Verurteilung nach Art. 19 Abs. 2 lit. b BetmG",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    gewerbsmaessig = forms.BooleanField(
        help_text="Verurteilung nach Art. 19 Abs. 2 lit. c BetmG",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    anstaltentreffen = forms.BooleanField(
        help_text="zur ganzen oder einen gewissen Menge Betm wurden lediglich Anstalten zum Handel getroffen.",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    beschaffungskriminalitaet = forms.BooleanField(
        help_text="Dem Täter wird in der Begründung ein Suchtdruck "
        "attestiert. Die Anwendung des Privilegierungsgrunds "
        "in Art. 19 Abs. 3 lit. b BetmG ist nicht erforderlich.",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    nebenverurteilungsscore = forms.IntegerField(
        initial=0,
        required=False,
        help_text="Anzahl der Schuldsprüche, welche neben dem "
        "Delikt, für welches die Einsatzsstrafe gebildet "
        "wurde, ausgesprochen wurden. + 1 Punkt für "
        "jedes weitere Vergehen. + 2 Punkt für jedes "
        "weitere Verbrechen. + 1 Punkt bei mehrfacher "
        "Begehung.",
        template_name="database/includes/prognose_form_field.html",
    )
    mehrfach = forms.BooleanField(
        help_text="Verureilung wegen mehrfacher Begehungsweise",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    rolle = forms.ModelChoiceField(
        queryset=Rolle.objects.all(),
        template_name="database/includes/prognose_form_field.html",
    )
    deliktsertrag = forms.IntegerField(
        initial=0,
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    deliktsdauer_in_monaten = forms.IntegerField(
        initial=0,
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    vorbestraft = forms.BooleanField(
        initial=False,
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    vorbestraft_einschlaegig = forms.BooleanField(
        initial=False,
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    betm1 = forms.ModelChoiceField(
        queryset=BetmArt.objects.all(),
        label="Betäubungsmittelart",
        template_name="database/includes/prognose_form_field.html",
    )
    betm1_menge = forms.IntegerField(
        help_text="Menge in Gramm oder Einheiten",
        label="Menge",
        template_name="database/includes/prognose_form_field.html",
    )
    betm1_rein = forms.BooleanField(initial=True,
                                    label="Rein?",
                                    required=False,
                                    template_name="database/includes/prognose_form_field.html")
    betm2 = forms.ModelChoiceField(
        queryset=BetmArt.objects.all(),
        label="Betäubungsmittelart",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    betm2_menge = forms.IntegerField(
        help_text="Menge in Gramm oder Einheiten",
        label="Menge",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    betm2_rein = forms.BooleanField(
        initial=True,
        label="Rein?",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    betm3 = forms.ModelChoiceField(
        queryset=BetmArt.objects.all(),
        label="Betäubungsmittelart",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    betm3_menge = forms.IntegerField(
        help_text="Menge in Gramm oder Einheiten",
        label="Menge",
        required=False,
        template_name="database/includes/prognose_form_field.html",
    )
    betm3_rein = forms.BooleanField(initial=True,
                                    label="Rein?",
                                    required=False,
                                    template_name="database/includes/prognose_form_field.html")
    gleiche_kategorie_betm1 = forms.BooleanField(
        initial=True,
        required=False,
        label="Nur Präjudizen anzeigen, die gleiche Betäubungsmittelart wie primäres Betäubungsmittel aufweisen",
        help_text="Wenn aktiviert, werden nur Präjudizien betreffend die gleiche Betäubungsmittelart wie "
                  "das primäre Betäubungsmittel angezeigt.",
        template_name="database/includes/prognose_form_field.html",
    )
    gleiche_rolle = forms.BooleanField(
        initial=False,
        required=False,
        label="Nur Präjudizen anzeigen, bei denen die Rolle mit der gewählten Rolle übereinstimmt",
        help_text="Wenn aktiviert, werden nur Präjudizien mit derselben Rolle wie im Formular ausgewählt angezeigt.",
        template_name="database/includes/prognose_form_field.html",
    )


class CeteribusParibusFormular(ModelForm):
    class Meta:
        model = Urteil
        fields = [
            "geschlecht",
            "mehrfach",
            "gewerbsmaessig",
            "bandenmaessig",
            "nebenverurteilungsscore",
            "vorbestraft",
            "vorbestraft_einschlaegig",
        ]


class BearbeitenModelForm(ModelForm):
    """Basis der Formulare, mit denen Superuser ein Urteil direkt auf dessen
    Detailansicht bearbeiten koennen.

    Anders als im Admin erscheinen die Felder im Bootstrap-Grid der Website,
    deshalb werden die Widgets hier mit den passenden Klassen versehen.
    `FELDGRUPPEN` bildet die Gliederung der Admin-Fieldsets nach; Felder, die
    dort nicht aufgefuehrt sind, landen in einer Auffanggruppe (siehe
    `gruppen()`), damit beim Erweitern eines Modells nichts unter den Tisch faellt.
    """

    FELDGRUPPEN = ()
    ISO_DATUM = "%Y-%m-%d"

    class Meta:
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for feld in self.fields.values():
            widget = feld.widget
            if isinstance(widget, forms.CheckboxInput):
                klasse = "form-check-input"
            elif isinstance(widget, forms.Select):
                klasse = "form-select"
            else:
                klasse = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {klasse}".strip()

            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 8)

            if isinstance(feld, forms.DateField):
                # <input type="date"> liefert und erwartet ISO-Daten; das
                # de-CH-Locale kennt dieses Format weder beim Rendern noch beim
                # Parsen, deshalb beides explizit ergaenzen.
                widget.input_type = "date"
                widget.format = self.ISO_DATUM
                feld.input_formats = [self.ISO_DATUM, *feld.input_formats]

    def gruppen(self):
        """Gibt `(titel, [BoundField, ...])` je Feldgruppe aus."""
        zugeteilt = set()
        for titel, feldnamen in self.FELDGRUPPEN:
            felder = [self[name] for name in feldnamen if name in self.fields]
            if not felder:
                continue
            zugeteilt.update(feld.name for feld in felder)
            yield titel, felder

        uebrige = [feld for feld in self if feld.name not in zugeteilt]
        if uebrige:
            yield "Weitere Felder", uebrige


class UrteilBearbeitenForm(BearbeitenModelForm):
    class Meta(BearbeitenModelForm.Meta):
        model = Urteil

    FELDGRUPPEN = (
        ("Grunddaten", ("fall_nr", "url_link", "gericht", "urteilsdatum", "verfahrensart")),
        ("Person", ("geschlecht", "nationalitaet", "vorbestraft", "vorbestraft_einschlaegig")),
        (
            "Delikt",
            (
                "hauptdelikt",
                "mehrfach",
                "gewerbsmaessig",
                "bandenmaessig",
                "deliktssumme",
                "nebenverurteilungsscore",
            ),
        ),
        ("Sanktion", ("hauptsanktion", "freiheitsstrafe_in_monaten", "anzahl_tagessaetze", "vollzug")),
        ("Weitere Informationen", ("zusammenfassung", "in_ki_modell")),
    )


class BetmUrteilBearbeitenForm(BearbeitenModelForm):
    class Meta(BearbeitenModelForm.Meta):
        model = BetmUrteil

    FELDGRUPPEN = (
        (
            "Grunddaten",
            ("fall_nr", "url_link", "gericht", "urteilsdatum", "kanton", "verfahrensart"),
        ),
        ("Person", ("geschlecht", "nationalitaet", "vorbestraft", "vorbestraft_einschlaegig")),
        (
            "Delikt & Rolle",
            (
                "mengenmaessig",
                "bandenmaessig",
                "gewerbsmaessig",
                "anstaltentreffen",
                "mehrfach",
                "beschaffungskriminalitaet",
                "rolle",
                "deliktsertrag",
                "deliktsdauer_in_monaten",
                "nebenverurteilungsscore",
                "betm",
            ),
        ),
        ("Sanktion", ("hauptsanktion", "freiheitsstrafe_in_monaten", "anzahl_tagessaetze", "vollzug")),
        ("Weitere Informationen", ("zusammenfassung", "in_ki_modell")),
    )


class SexualdeliktUrteilBearbeitenForm(BearbeitenModelForm):
    class Meta(BearbeitenModelForm.Meta):
        model = SexualdeliktUrteil

    FELDGRUPPEN = (
        (
            "Grunddaten",
            ("fall_nr", "url_link", "gericht", "urteilsdatum", "kanton", "verfahrensart"),
        ),
        ("Person", ("geschlecht", "nationalitaet", "vorbestraft", "vorbestraft_einschlaegig")),
        (
            "Deliktsangaben",
            (
                "hauptdelikt",
                "hauptdelikt_tatmittel",
                "hauptdelikt_mehrfachbegehung",
                "hauptdelikt_mehrfachbegehung_anzahl",
                "hauptdelikt_mehrfachbegehung_deliktsperiode",
                "hauptdelikt_deliktsdauer_bekannt",
                "hautpdelikt_deliktsdauer_einfachbegehung",
                "hauptdelikt_taeter_opfer_beziehung",
                "hauptdelikt_opferalter",
                "hauptdelikt_opfer_vorerfahrung",
                "deliktsscore_uebrige_delikte",
                "sexualdelikte_zusaetzliche",
                "besonderheiten",
            ),
        ),
        ("Sanktion", ("hauptsanktion", "freiheitsstrafe_in_monaten", "anzahl_tagessaetze", "vollzug")),
        ("Weitere Informationen", ("kurzsachverhalt", "zusammenfassung", "bemerkungen")),
    )


class GewaltdeliktUrteilBearbeitenForm(BearbeitenModelForm):
    class Meta(BearbeitenModelForm.Meta):
        model = GewaltdeliktUrteil

    FELDGRUPPEN = (
        (
            "Grunddaten",
            ("fall_nr", "url_link", "gericht", "urteilsdatum", "kanton", "verfahrensart"),
        ),
        ("Person", ("geschlecht", "nationalitaet", "vorbestraft", "vorbestraft_einschlaegig")),
        (
            "Delikt",
            (
                "hauptdelikt",
                "versuch",
                "vorsatzform",
                "tatmittel",
                "waffe_gefaehrlicher_gegenstand",
                "bandenmaessig",
                "besondere_gefaehrlichkeit",
                "lebensgefahr",
                "mehrfach",
                "opferzahl",
                "taeter_opfer_beziehung",
                "verletzungsfolge",
                "angegriffenes_koerperteil",
                "substanzeinfluss",
                "deliktssumme",
                "deliktsscore_uebrige_delikte",
                "besonderheiten",
            ),
        ),
        ("Sanktion", ("hauptsanktion", "freiheitsstrafe_in_monaten", "anzahl_tagessaetze", "vollzug")),
        ("Weitere Informationen", ("kurzsachverhalt", "zusammenfassung", "bemerkungen", "in_ki_modell")),
    )
