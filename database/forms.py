from django.forms import ModelForm
from django import forms
from .models import Urteil, BetmUrteil, BetmArt, Rolle


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
