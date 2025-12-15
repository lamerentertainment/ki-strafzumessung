from django.contrib import admin
from django import forms
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import (Urteil, KIModelPickleFile, DiagrammSVG, BetmUrteil, BetmArt, Betm, Rolle, Kanton,
                     SexualdeliktUrteil, Besonderheiten, Hauptdelikt, ZusaetzlicheSexualdelikte, Tatmittel)
from .services.urteil_extractor import extract_urteil_data, validate_extracted_data

@admin.register(BetmUrteil)
class BetmUrteilAdmin(admin.ModelAdmin):
    list_display = ["fall_nr", "update_time", "urteilsdatum", "gericht", "freiheitsstrafe_in_monaten",
                    "anzahl_tagessaetze", "has_zusammenfassung"]
    ordering = ["-update_time"]

    def has_zusammenfassung(self, obj):
        return bool(obj.zusammenfassung)
    has_zusammenfassung.boolean = True
    has_zusammenfassung.short_description = "Zusammenfassung vorhanden"

class UrteilAdminForm(forms.ModelForm):
    """Custom Admin Form mit KI-Assistenz für automatisches Ausfüllen."""

    volltext_input = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 12,
            'cols': 100,
            'placeholder': 'Volltext des Urteils hier einfügen und auf "Formular automatisch ausfüllen" klicken...',
            'class': 'vLargeTextField',
            'style': 'font-family: monospace; font-size: 12px;'
        }),
        required=False,
        label='🤖 KI-Assistenz: Volltext des Urteils',
        help_text='Fügen Sie den kompletten Urteilstext ein. Die KI wird automatisch alle Felder analysieren und ausfüllen.'
    )

    class Meta:
        model = Urteil
        fields = '__all__'

    class Media:
        js = ('admin/js/urteil_auto_fill.js',)


@admin.register(Urteil)
class UrteilAdmin(admin.ModelAdmin):
    form = UrteilAdminForm
    list_display = ["fall_nr", "update_time", "urteilsdatum", "gericht", "freiheitsstrafe_in_monaten",
                    "anzahl_tagessaetze", "has_zusammenfassung"]
    ordering = ["-update_time"]

    # Fieldsets für bessere Übersicht
    fieldsets = (
        ('🤖 KI-Assistenz', {
            'fields': ('volltext_input',),
            'classes': ('wide',),
            'description': 'Fügen Sie hier den Volltext des Urteils ein und klicken Sie auf "Formular automatisch ausfüllen".'
        }),
        ('Grunddaten', {
            'fields': ('fall_nr', 'url_link', 'gericht', 'urteilsdatum'),
        }),
        ('Person', {
            'fields': ('geschlecht', 'nationalitaet', 'vorbestraft', 'vorbestraft_einschlaegig'),
        }),
        ('Delikt', {
            'fields': ('hauptdelikt', 'mehrfach', 'gewerbsmaessig', 'bandenmaessig',
                      'deliktssumme', 'nebenverurteilungsscore'),
        }),
        ('Sanktion', {
            'fields': ('hauptsanktion', 'freiheitsstrafe_in_monaten', 'anzahl_tagessaetze', 'vollzug'),
        }),
        ('Weitere Informationen', {
            'fields': ('zusammenfassung', 'in_ki_modell'),
        }),
    )

    def has_zusammenfassung(self, obj):
        return bool(obj.zusammenfassung)
    has_zusammenfassung.boolean = True
    has_zusammenfassung.short_description = "Zusammenfassung vorhanden"

    def get_urls(self):
        """Fügt Custom URL für Auto-Fill API hinzu."""
        urls = super().get_urls()
        custom_urls = [
            path('auto-fill/', self.admin_site.admin_view(self.auto_fill_view), name='urteil-auto-fill'),
        ]
        return custom_urls + urls

    @require_http_methods(["POST"])
    def auto_fill_view(self, request):
        """API-Endpoint für automatisches Ausfüllen des Formulars."""
        try:
            # Request Body parsen
            data = json.loads(request.body)
            volltext = data.get('volltext', '')

            if not volltext or len(volltext.strip()) < 100:
                return JsonResponse({
                    'success': False,
                    'error': 'Der Volltext ist zu kurz. Bitte fügen Sie den kompletten Urteilstext ein.'
                }, status=400)

            # Daten extrahieren
            extracted_data = extract_urteil_data(volltext)

            # Validieren
            is_valid, errors = validate_extracted_data(extracted_data)

            if not is_valid:
                return JsonResponse({
                    'success': True,
                    'data': extracted_data,
                    'warnings': errors,
                    'message': 'Daten wurden extrahiert, aber es gibt Validierungswarnungen. Bitte überprüfen Sie die Felder.'
                })

            return JsonResponse({
                'success': True,
                'data': extracted_data,
                'message': 'Formular erfolgreich ausgefüllt. Bitte überprüfen Sie alle Felder vor dem Speichern.'
            })

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Fehler bei der Verarbeitung: {str(e)}'
            }, status=500)

@admin.register(SexualdeliktUrteil)
class SexualdeliktUrteilAdmin(admin.ModelAdmin):
    list_display = ["fall_nr", "update_time", "urteilsdatum", "gericht", "freiheitsstrafe_in_monaten",
                    "anzahl_tagessaetze", "has_zusammenfassung"]
    ordering = ["-update_time"]

    def has_zusammenfassung(self, obj):
        return bool(obj.zusammenfassung)
    has_zusammenfassung.boolean = True
    has_zusammenfassung.short_description = "Zusammenfassung vorhanden"

# Register your models here.
admin.site.register(KIModelPickleFile)
admin.site.register(DiagrammSVG)
admin.site.register(BetmArt)
admin.site.register(Betm),
admin.site.register(Rolle),
admin.site.register(Kanton)
admin.site.register(Hauptdelikt)
admin.site.register(Tatmittel)
admin.site.register(ZusaetzlicheSexualdelikte)
admin.site.register(Besonderheiten)
