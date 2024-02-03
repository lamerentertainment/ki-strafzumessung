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
        fields = ['mengenmaessig',
                  'bandenmaessig',
                  'gewerbsmaessig',
                  'anstaltentreffen',
                  'mehrfach',
                  'beschaffungskriminalität']


class CeteribusParibusFormular(ModelForm):
    class Meta:
        model = Urteil
        fields = ['geschlecht', 'mehrfach', 'gewerbsmaessig', 'bandenmaessig',
                  'nebenverurteilungsscore', 'vorbestraft', 'vorbestraft_einschlaegig']