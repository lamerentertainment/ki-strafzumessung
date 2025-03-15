from django.contrib import admin
from .models import Urteil, KIModelPickleFile, DiagrammSVG, BetmUrteil, BetmArt, Betm, Rolle, Kanton

@admin.register(BetmUrteil)
class BetmUrteilAdmin(admin.ModelAdmin):
    list_display = ["fall_nr", "add_time", "urteilsdatum", "gericht", "freiheitsstrafe_in_monaten",
                    "anzahl_tagessaetze"]

@admin.register(Urteil)
class UrteilAdmin(admin.ModelAdmin):
    list_display = ["fall_nr", "add_time", "urteilsdatum", "gericht", "freiheitsstrafe_in_monaten",
                    "anzahl_tagessaetze"]

# Register your models here.
admin.site.register(KIModelPickleFile)
admin.site.register(DiagrammSVG)
admin.site.register(BetmArt)
admin.site.register(Betm),
admin.site.register(Rolle),
admin.site.register(Kanton)
