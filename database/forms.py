from django.forms import ModelForm
from django import forms
from .models import (
    Urteil,
    BetmUrteil,
    BetmArt,
    Rolle,
    SexualdeliktUrteil,
    Hauptdelikt,
    Tatmittel,
    ZusaetzlicheSexualdelikte,
    Besonderheiten,
)


class UrteilModelForm(ModelForm):
    class Meta:
        model = Urteil
        exclude = ["verfahrensart"]


class UrteilsEckpunkteAbfrageFormular(ModelForm):
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


class SexualdeliktUrteilsEckpunkteAbfrageFormular(forms.Form):
    hauptdelikt = forms.ModelChoiceField(
        # Nur im Datensatz vorkommende Hauptdelikte zulassen, sonst schlägt der OneHotEncoder
        # bei im Training unbekannten Kategorien fehl.
        queryset=Hauptdelikt.objects.filter(hauptdelikt__isnull=False).distinct(),
        label="Hauptdelikt",
        template_name="database/includes/prognose_form_field.html",
    )
    hauptdelikt_tatmittel = forms.ModelChoiceField(
        queryset=Tatmittel.objects.filter(
            hauptdelikt_tatmittel__isnull=False
        ).distinct(),
        label="Tatmittel",
        template_name="database/includes/prognose_form_field.html",
    )
    hauptdelikt_mehrfachbegehung = forms.BooleanField(
        initial=False,
        required=False,
        label="mehrfache Tatbegehung?",
        help_text="Verurteilung wegen mehrfacher Begehung des Hauptdelikts",
        template_name="database/includes/prognose_form_field.html",
    )
    hauptdelikt_mehrfachbegehung_anzahl = forms.IntegerField(
        initial=1,
        required=False,
        label="Anzahl Tatbegehungen",
        help_text="Anzahl der Vollendungen des Hauptdelikts (nur bei mehrfacher Begehung).",
        template_name="database/includes/prognose_form_field.html",
    )
    deliktsperiode_in_tagen = forms.IntegerField(
        initial=1,
        required=False,
        label="Deliktsperiode (Tage)",
        help_text="Periode, in welcher das Hauptdelikt mehrfach begangen wurde, in Tagen.",
        template_name="database/includes/prognose_form_field.html",
    )
    deliktsdauer_in_minuten = forms.IntegerField(
        initial=30,
        required=False,
        label="Deliktsdauer (Minuten)",
        help_text="Deliktsdauer einer einzelnen Tatbegehung des Hauptdelikts in Minuten, soweit bekannt.",
        template_name="database/includes/prognose_form_field.html",
    )
    deliktsscore_uebrige_delikte = forms.IntegerField(
        initial=0,
        required=False,
        label="Deliktsscore übrige Delikte",
        help_text="Anzahl der Schuldsprüche, welche neben den Sexualdelikten ausgesprochen wurden. "
        "+ 1 Punkt für jedes weitere Vergehen. + 2 Punkte für jedes weitere Verbrechen. "
        "+ 1 Punkt bei mehrfacher Begehung.",
        template_name="database/includes/prognose_form_field.html",
    )
    hauptdelikt_taeter_opfer_beziehung = forms.ChoiceField(
        choices=SexualdeliktUrteil.BEZIEHUNG_CHOICES,
        initial="Bekannte",
        label="Täter-Opfer-Beziehung",
        template_name="database/includes/prognose_form_field.html",
    )
    hauptdelikt_opferalter = forms.ChoiceField(
        choices=SexualdeliktUrteil.OPFERALTER_CHOICES,
        initial="erwachsen",
        label="Opferalter",
        template_name="database/includes/prognose_form_field.html",
    )
    hauptdelikt_opfer_vorerfahrung = forms.ChoiceField(
        choices=SexualdeliktUrteil.OPFERERFAHRUNG_CHOICES,
        initial="unbekannt",
        label="Sexuelle Vorerfahrung des Opfers?",
        template_name="database/includes/prognose_form_field.html",
    )
    geschlecht = forms.ChoiceField(
        choices=SexualdeliktUrteil.GESCHLECHT,
        initial="0",
        label="Geschlecht",
        template_name="database/includes/prognose_form_field.html",
    )
    nationalitaet = forms.ChoiceField(
        choices=SexualdeliktUrteil.NATIONALITAET,
        initial="2",
        label="Nationalität",
        template_name="database/includes/prognose_form_field.html",
    )
    vorbestraft = forms.BooleanField(
        initial=False,
        required=False,
        label="vorbestraft",
        template_name="database/includes/prognose_form_field.html",
    )
    vorbestraft_einschlaegig = forms.BooleanField(
        initial=False,
        required=False,
        label="einschlägig vorbestraft",
        template_name="database/includes/prognose_form_field.html",
    )
    sexualdelikte_zusaetzliche = forms.ModelMultipleChoiceField(
        queryset=ZusaetzlicheSexualdelikte.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="zusätzliche Sexualdelikte",
        template_name="database/includes/prognose_form_field.html",
    )
    besonderheiten = forms.ModelMultipleChoiceField(
        queryset=Besonderheiten.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Besonderheiten",
        template_name="database/includes/prognose_form_field.html",
    )
    gleiches_hauptdelikt = forms.BooleanField(
        initial=True,
        required=False,
        label="Nur Präjudizen anzeigen, die dasselbe Hauptdelikt aufweisen",
        help_text="Wenn aktiviert, werden nur Präjudizien mit demselben Hauptdelikt wie im Formular gewählt angezeigt.",
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


class StrafrechtlicherSachverhaltFormular(forms.Form):
    sachverhalt = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
        label="Strafrechtlicher Sachverhalt",
        help_text="Bitte geben Sie hier die Eckwerte des strafrechtlichen Sachverhalts ein.",
        required=True,
    )
