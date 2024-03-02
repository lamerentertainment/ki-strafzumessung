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
    mengenmaessig = forms.BooleanField(initial=True, help_text='Verurteilung nach Art. 19 Abs. 2 lit. a BetmG', required=False)
    bandenmaessig = forms.BooleanField(help_text='Verurteilung nach Art. 19 Abs. 2 lit. b BetmG', required=False)
    gewerbsmaessig = forms.BooleanField(help_text='Verurteilung nach Art. 19 Abs. 2 lit. c BetmG', required=False)
    anstaltentreffen = forms.BooleanField(help_text='zur ganzen oder einen gewissen Menge Betm wurden lediglich Anstalten getroffen', required=False)
    beschaffungskriminalitaet = forms.BooleanField(help_text="Dem Täter wird in der Begründung ein Suchtdruck "
                                                             "attestiert. Die Anwendung des Privilegierungsgrunds "
                                                             "in Art. 19 Abs. 3 lit. b BetmG ist nicht erforderlich.",
                                                   required=False)
    nebenverurteilungsscore = forms.IntegerField(initial=0, required=False)
    mehrfach = forms.BooleanField(help_text="Verureilung wegen mehrfacher Begehungsweise", required=False)
    rolle = forms.ModelChoiceField(queryset=Rolle.objects.all())
    deliktsertrag = forms.IntegerField(initial=0, required=False)
    deliktsdauer_in_monaten = forms.IntegerField(initial=0, required=False)
    vorbestraft = forms.BooleanField(initial=False, required=False)
    vorbestraft_einschlaegig = forms.BooleanField(initial=False, required=False)
    betm1 = forms.ModelChoiceField(
        queryset=BetmArt.objects.all(), label="Betäubungsmittelart"
    )
    betm1_menge = forms.IntegerField(
        help_text="Menge in Gramm oder Einheiten", label="Menge"
    )
    betm1_rein = forms.BooleanField(initial=True, label="Rein?", required=False)
    betm2 = forms.ModelChoiceField(
        queryset=BetmArt.objects.all(),
        label="Betäubungsmittelart",
        required=False
    )
    betm2_menge = forms.IntegerField(
        help_text="Menge in Gramm oder Einheiten",
        label="Menge",
        required=False
    )
    betm2_rein = forms.BooleanField(initial=True,
                                    label="Rein?",
                                    required=False)
    betm3 = forms.ModelChoiceField(
        queryset=BetmArt.objects.all(),
        label="Betäubungsmittelart",
        required=False
    )
    betm3_menge = forms.IntegerField(
        help_text="Menge in Gramm oder Einheiten",
        label="Menge",
        required=False
    )
    betm3_rein = forms.BooleanField(initial=True,
                                    label="Rein?",
                                    required=False)


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
