from django.forms import ModelForm
from .models import Urteil, BetmUrteil


class UrteilModelForm(ModelForm):
    class Meta:
        model = Urteil
        exclude = ['verfahrensart']


class UrteilsEckpunkteAbfrageFormular(ModelForm):
    class Meta:
        model = Urteil
        fields = ['hauptdelikt', 'deliktssumme', 'nebenverurteilungsscore', 'mehrfach', 'gewerbsmaessig',
                  'bandenmaessig', 'vorbestraft', 'vorbestraft_einschlaegig']


class BetmUrteilsEckpunkteAbfrageFormular(ModelForm):
    class Meta:
        model = BetmUrteil
        fields = ['mengemaessig',
                  'bandenmaessig',
                  'gewerbsmaessig',
                  'anstaltentreffen',
                  'mehrfach',
                  'beschaffungskriminalitaet',
                  'nebenverurteilungsscore',
                  'betm',
                  'rolle',
                  'deliktsertrag',
                  'deliktsdauer_in_monaten',
                  'vorbestraft',
                  'vorbestraft_einschlaegig',
                  ]


class CeteribusParibusFormular(ModelForm):
    class Meta:
        model = Urteil
        fields = ['geschlecht', 'mehrfach', 'gewerbsmaessig', 'bandenmaessig',
                  'nebenverurteilungsscore', 'vorbestraft', 'vorbestraft_einschlaegig']