from django.contrib import admin
from .models import Urteil, KIModelPickleFile, DiagrammSVG, BetmUrteil, BetmArt, Betm, Rolle, Kanton

# Register your models here.
admin.site.register(Urteil)
admin.site.register(KIModelPickleFile)
admin.site.register(DiagrammSVG)
admin.site.register(BetmUrteil)
admin.site.register(BetmArt)
admin.site.register(Betm),
admin.site.register(Rolle),
admin.site.register(Kanton)
