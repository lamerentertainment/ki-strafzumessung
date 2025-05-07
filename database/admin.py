from django.contrib import admin
from .models import (Urteil, KIModelPickleFile, DiagrammSVG, BetmUrteil, BetmArt, Betm, Rolle, Kanton,
                     SexualdeliktUrteil, Besonderheiten, Hauptdelikt, ZusaetzlicheSexualdelikte, Tatmittel)

@admin.register(BetmUrteil)
class BetmUrteilAdmin(admin.ModelAdmin):
    list_display = ["fall_nr", "update_time", "urteilsdatum", "gericht", "freiheitsstrafe_in_monaten",
                    "anzahl_tagessaetze", "has_zusammenfassung"]
    ordering = ["-update_time"]

    def has_zusammenfassung(self, obj):
        return bool(obj.zusammenfassung)
    has_zusammenfassung.boolean = True
    has_zusammenfassung.short_description = "Zusammenfassung vorhanden"

@admin.register(Urteil)
class UrteilAdmin(admin.ModelAdmin):
    list_display = ["fall_nr", "update_time", "urteilsdatum", "gericht", "freiheitsstrafe_in_monaten",
                    "anzahl_tagessaetze", "has_zusammenfassung"]
    ordering = ["-update_time"]

    def has_zusammenfassung(self, obj):
        return bool(obj.zusammenfassung)
    has_zusammenfassung.boolean = True
    has_zusammenfassung.short_description = "Zusammenfassung vorhanden"

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
