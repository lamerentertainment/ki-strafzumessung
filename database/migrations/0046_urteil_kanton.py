import re

import django.db.models.deletion
from django.db import migrations, models

# Zuordnung des vorinstanzlichen Gerichts (Feld `gericht`) zum Kanton. Die Reihenfolge
# ist massgebend: spezifischere Muster zuerst (z.B. "Basel-Landschaft" vor "Basel",
# "Emmental-Oberaargau" (BE) vor "Aargau").
GERICHT_KANTON_MUSTER = [
    ("BL", r"Basel-Landschaft|Basel-Land\b"),
    ("BS", r"Basel-Stadt|Basel\b"),
    ("BE", r"\bBern(?!ina)|Oberland|Emmental|Oberaargau|Jura-Seeland"),
    ("GE", r"Gen[eè]v|\bGenf"),
    ("VD", r"Lausanne|vaudois|Vaud|Waadt"),
    ("FR", r"Gruy[eè]re|Sarine|arrondissement du Lac|Freiburg|Fribourg|Glâne|Singine|\bSense\b|Veveyse"),
    ("GR", r"Plessur|Imboden|Maloja|Graub[üu]nden|Landquart|Prättigau|Surselva|Albula|Bernina|Engiadina|Moesa|Viamala"),
    ("SO", r"Solothurn|Bucheggberg|Wasseramt|Olten|Gösgen|Thal-Gäu|Lebern|Dorneck|Thierstein"),
    ("SZ", r"Schwyz|\bHöfe\b|\bMarch\b|Einsiedeln|Küssnacht|Gersau"),
    ("ZG", r"\bZug\b"),
    ("LU", r"Luzern"),
    ("SH", r"Schaffhausen"),
    ("NE", r"Neuch[aâ]tel|Neuenburg"),
    ("UR", r"\bUri\b"),
    ("NW", r"Nidwalden"),
    ("AR", r"Appenzell Ausserrhoden"),
    ("AG", r"Aargau|Aarau|\bBaden\b|\bMuri\b|Zurzach|Zofingen|\bKulm\b|Bremgarten|Brugg|Lenzburg|Laufenburg|Rheinfelden"),
    ("ZH", r"Zürich|Bülach|Winterthur|Dietikon|\bUster\b|Meilen|Horgen|Hinwil|Dielsdorf|Pf?äffikon|Affoltern|Andelfingen"),
]


def kanton_aus_gericht(gericht):
    for abk, muster in GERICHT_KANTON_MUSTER:
        if re.search(muster, gericht or ""):
            return abk
    return None


def kanton_zuordnen(apps, schema_editor):
    Urteil = apps.get_model("database", "Urteil")
    Kanton = apps.get_model("database", "Kanton")

    nicht_zuordenbar = set()
    for urteil in Urteil.objects.all():
        abk = kanton_aus_gericht(urteil.gericht)
        if abk is None:
            nicht_zuordenbar.add(urteil.gericht)
            continue
        kanton = Kanton.objects.filter(abk=abk).order_by("id").first()
        if kanton is None:
            kanton = Kanton.objects.create(abk=abk)
        urteil.kanton = kanton
        urteil.save(update_fields=["kanton"])

    if nicht_zuordenbar:
        raise RuntimeError(
            "Kein Kanton zuordenbar für folgende Gerichte (Muster in 0046_urteil_kanton "
            f"ergänzen): {sorted(nicht_zuordenbar)}"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("database", "0045_urteil_besonderheiten_kurzsachverhalt_bemerkungen_private_geschaedigte"),
    ]

    operations = [
        migrations.AddField(
            model_name="urteil",
            name="kanton",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="database.kanton",
            ),
        ),
        migrations.RunPython(kanton_zuordnen, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="urteil",
            name="kanton",
            field=models.ForeignKey(
                help_text="Der Kanton des vorinstanzlichen Gerichts.",
                on_delete=django.db.models.deletion.CASCADE,
                to="database.kanton",
            ),
        ),
    ]
