from django.forms import ModelForm
from .models import Urteil


class UrteilModelForm(ModelForm):
    class Meta:
        model = Urteil
        exclude = ['verfahrensart']


class UrteilsEckpunkteAbfrageFormular(ModelForm):
    class Meta:
        model = Urteil
        fields = ['hauptdelikt', 'deliktssumme', 'nebenverurteilungsscore', 'mehrfach', 'gewerbsmaessig',
                  'bandenmaessig', 'vorbestraft', 'vorbestraft_einschlaegig']


class CeteribusParibusFormular(ModelForm):
    class Meta:
        model = Urteil
        fields = ['geschlecht', 'mehrfach', 'gewerbsmaessig', 'bandenmaessig',
                  'nebenverurteilungsscore', 'vorbestraft', 'vorbestraft_einschlaegig']