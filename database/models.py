import pandas as pd
from django.db import models
from datetime import timedelta


_DEUTSCHE_MONATSNAMEN = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


def datum_deutsch_formatieren(datum):
    """Formatiert ein Datum als 'd. Monatsname JJJJ' mit deutschen Monatsnamen,
    unabhängig davon, ob auf dem System eine de_CH-Locale installiert ist."""
    return f"{datum.day}. {_DEUTSCHE_MONATSNAMEN[datum.month]} {datum.year}"


class DataFrameExporter(models.Manager):
    def return_as_df(self, *fields, exclude_unmarked=False, kanton_filtern=None):
        """
        Gibt die Urteile in einer Datenbank als Pandas DataFrame aus
        *fields: auf welche Datenfelder es beschränkt sein soll
        exclude_unmarked: ob jene Einträge ausgelassen werden sollen, bei denen in_ki_modell=False ist
        kanton_filtern: um datenframe eines einzelne Kantons zu exportieren, kann man hier den Kürzels des Kantons angeben
        """
        if exclude_unmarked:
            alle_urteile = super().get_queryset().filter(in_ki_modell=True)
        else:
            alle_urteile = super().get_queryset().all()
        if isinstance(kanton_filtern, str):
            kanton = kanton_filtern
            alle_urteile = alle_urteile.filter(kanton__abk=kanton)
        if not fields:
            # Wenn keine Felder angegeben sind, alle Felder einschließen
            alle_urteile_als_dict = alle_urteile.values()
            return pd.DataFrame.from_records(alle_urteile_als_dict, index="id")
        else:
            # Andernfalls nur die angegebenen Felder einschließen, Datenbankeintrags-id ('pk') wird immer mitgeliefert
            alle_urteile_als_dict = alle_urteile.values("pk", *fields)
            # Datenbankeintrags-id ('pk') wird als index des DataFrames verwendet
            return pd.DataFrame.from_records(alle_urteile_als_dict, index="pk")

    def return_y_zielwerte(
        self, zielwert="freiheitsstrafe_in_monaten", exclude_unmarked=False
    ):
        """
        gibt ein Datenframe mit den Zielwerten aus
        zielwert: Zielwert als String
        exclude_unmarked: ob jene Einträge ausgelassen werden sollen, bei denen in_ki_modell=False ist
        """
        if exclude_unmarked:
            alle_urteile = super().get_queryset().filter(in_ki_modell=True)
        else:
            alle_urteile = super().get_queryset().all()
        alle_urteile_als_dict_mit_nur_einer_spalte = alle_urteile.values(zielwert)
        return pd.DataFrame.from_records(alle_urteile_als_dict_mit_nur_einer_spalte)


# Create your models here.
class Urteil(models.Model):
    # Managers
    objects = models.Manager()
    pandas = DataFrameExporter()

    # Datenfelder
    gericht = models.CharField(
        max_length=50,
        help_text="Das Gericht, welches das Urteil gefällt hat.",
        default="n/a",
    )
    urteilsdatum = models.DateField(
        blank=True,
        null=True,
        help_text="Das Datum, an welchem das Gericht das Urteil gefällt hat.",
    )
    kanton = models.ForeignKey(
        "Kanton",
        on_delete=models.CASCADE,
        help_text="Der Kanton des vorinstanzlichen Gerichts.",
    )
    fall_nr = models.CharField(
        max_length=15, unique=True, help_text="Die Verfahrensnummer des Urteils."
    )
    url_link = models.URLField(
        blank=True, help_text="Der URL-Link zum PDF des Urteils."
    )
    VERFAHRENSART = (("0", "ordentlich"), ("1", "abgekürzt"))
    verfahrensart = models.CharField(max_length=2, choices=VERFAHRENSART, default="0")
    GESCHLECHT = (("0", "männlich"), ("1", "weiblich"))
    geschlecht = models.CharField(max_length=2, choices=GESCHLECHT, default="0")
    NATIONALITAET = (
        ("0", "Schweizerin/Schweizer"),
        ("1", "Ausländer/Ausländerin"),
        ("2", "unbekannt"),
    )
    nationalitaet = models.CharField(max_length=2, choices=NATIONALITAET, default="2")
    HAUPTDELIKT = (
        ("Betrug", "Betrug"),
        ("Veruntreuung", "Veruntreuung"),
        ("ung. Geschäftsbesorgung", "ung. Geschäftsbesorgung"),
        ("betr. Missbrauch DVA", "betr. Missbrauch DVA"),
        ("Diebstahl", "Diebstahl"),
        ("Sachbeschädigung", "Sachbeschädigung"),
    )
    hauptdelikt = models.CharField(
        max_length=30,
        choices=HAUPTDELIKT,
        default="Betrug",
        help_text="Die Deliktsart, für welches die Einsatzsstrafe gebildet wurde.",
    )
    mehrfach = models.BooleanField(
        default=False,
        help_text="Ob das Delikt, für welches die Einsatzsstrafe gebildet wurde, mehrfach "
        "begangen wurde.",
    )
    gewerbsmaessig = models.BooleanField(
        default=False,
        verbose_name="gewerbsmässig/qualifizierte Begehungsweise",
        help_text="Ob das Delikt, für welches die Einsatzsstrafe gebildet wurde, "
        "gewerbsmässig bzw. (bei der Veruntreuung und der ungetreuen "
        "Geschäftsbesorgung) qualifiziert begangen wurde. Bei der ungetreuen "
        "Geschäftsbesorgung: Schuldspruch nach Art. 158 Ziff. 1 Abs. 3 StGB "
        "(Bereicherungsabsicht).",
    )
    bandenmaessig = models.BooleanField(
        default=False,
        help_text="Ob das Delikt, für welches die Einsatzsstrafe gebildet wurde, "
        "bandenmässig begangen wurde.",
    )
    deliktssumme = models.IntegerField(
        help_text="Die mit dem Delikt, für welches die Einsatzsstrafe gebildet wurde, "
        "erzielte Deliktssumme. Subsidiär die gesamthaft, mit allen "
        "Straftaten, erzielte Deliktssumme."
    )
    nebenverurteilungsscore = models.IntegerField(
        default=0,
        help_text="Anzahl der Schuldsprüche, welche neben dem "
        "Delikt, für welches die Einsatzsstrafe gebildet "
        "wurde, ausgesprochen wurden. + 1 Punkt für "
        "jedes weitere Vergehen. + 2 Punkt für jedes "
        "weitere Verbrechen. + 1 Punkt bei mehrfacher "
        "Begehung.",
    )
    vorbestraft = models.BooleanField(
        default=False,
        verbose_name="vorbestraft",
        help_text="Ob die verurteilte Person vorbestraft ist.",
    )
    vorbestraft_einschlaegig = models.BooleanField(
        default=False,
        verbose_name="einschlägig vorbestraft",
        help_text="Ob die verurteilte Person einschlägig vorbestraft ist.",
    )
    HAUPTSANKTION = (("0", "Freiheitsstrafe"), ("1", "Geldstrafe"), ("2", "Busse"))
    hauptsanktion = models.CharField(max_length=1, choices=HAUPTSANKTION, default="0")
    freiheitsstrafe_in_monaten = models.IntegerField(
        default=12,
        help_text="Die Dauer der ausgesprochenen Freiheitsstrafe in " "Monaten.",
    )
    anzahl_tagessaetze = models.IntegerField(
        default=0, help_text="Die Zahl der ausgesprochenen Tagessätze der Geldstrafe"
    )
    VOLLZUG = (("0", "bedingt"), ("1", "teilbedingt"), ("2", "unbedingt"))
    vollzug = models.CharField(max_length=20, choices=VOLLZUG, default="0")
    in_ki_modell = models.BooleanField(default=True)
    # private_geschaedigte fliesst in die ML-Prognose ein (ai_utils.VM_CAT_FTS);
    # besonderheiten, kurzsachverhalt und bemerkungen (noch) nicht.
    PRIVATE_GESCHAEDIGTE = (("ja", "ja"), ("nein", "nein"), ("unbekannt", "unbekannt"))
    private_geschaedigte = models.CharField(
        max_length=10,
        choices=PRIVATE_GESCHAEDIGTE,
        default="unbekannt",
        verbose_name="private Geschädigte",
        help_text="Ob durch das Hauptdelikt Privatpersonen in ihrem Vermögen geschädigt "
        "wurden. 'nein', wenn ausschliesslich der Staat oder juristische Personen "
        "geschädigt wurden.",
    )
    besonderheiten = models.ManyToManyField(
        "Besonderheiten",
        related_name="vermoegensdelikte",
        blank=True,
        help_text="Strafzumessungsrelevante Besonderheiten (z.B. Geständnis/Reue, "
        "Versuch, Gehilfenschaft, verminderte Schuldfähigkeit).",
    )
    kurzsachverhalt = models.TextField(
        blank=True,
        default="",
        help_text="Kurze Zusammenfassung des Sachverhalts (wird beim Hovern in der Urteilsliste angezeigt)",
    )
    zusammenfassung = models.TextField(
        blank=True,
        help_text="Die Zusammenfassung der massgebenden Erwägungen für die Strafzumessung",
    )
    bemerkungen = models.TextField(blank=True, help_text="Besondere Bemerkungen zum Fall")
    add_time = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )
    update_time = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
    )

    # Methoden
    def __str__(self):
        return f"{self.gericht}, Urteil vom {datum_deutsch_formatieren(self.urteilsdatum)} ({self.fall_nr})"

    class Meta:
        verbose_name_plural = "Vermögensdelikt-Urteile"
        ordering = ["urteilsdatum"]


class BetmUrteil(models.Model):
    # Managers
    objects = models.Manager()
    pandas = DataFrameExporter()

    # Datenfelder
    fall_nr = models.CharField(
        max_length=15,
        unique=True,
        help_text="Die Verfahrensnummer des Urteils, dem die Informationen entnommen sind.",
    )
    url_link = models.URLField(
        blank=True,
        help_text="Der URL-Link zum PDF des Urteils, dem die Informationen entnommen sind.",
    )
    gericht = models.CharField(
        max_length=50,
        help_text="Das Gericht, welches das Urteil gefällt hat.",
        default="n/a",
    )
    urteilsdatum = models.DateField(
        blank=True,
        null=True,
        help_text="Das Datum, an welchem das Gericht das Urteil gefällt hat.",
    )
    kanton = models.ForeignKey("Kanton", on_delete=models.CASCADE)
    mengenmaessig = models.BooleanField(
        default=True, help_text="Verurteilung nach Art. 19 Abs. 2 lit. a BetmG"
    )
    bandenmaessig = models.BooleanField(
        default=False, help_text="Verurteilung nach Art. 19 Abs. 2 lit. b BetmG"
    )
    gewerbsmaessig = models.BooleanField(
        default=False, help_text="Verurteilung nach Art. 19 Abs. 2 lit. c BetmG"
    )
    anstaltentreffen = models.BooleanField(
        default=False,
        help_text="zur ganzen oder einen gewissen Menge Betm wurden"
        "lediglich Anstalten getroffen",
    )
    mehrfach = models.BooleanField(default=False)
    beschaffungskriminalitaet = models.BooleanField(
        default=False,
        help_text="Dem Täter wird in der Begründung ein "
        "Suchtdruck attestiert. Die Anwendung des "
        "Privilegierungsgrunds in Art. 19 Abs. 3 "
        "lit. b BetmG ist nicht erforderlich.",
    )
    HAUPTSANKTION = (("0", "Freiheitsstrafe"), ("1", "Geldstrafe"), ("2", "Busse"))
    hauptsanktion = models.CharField(max_length=1, choices=HAUPTSANKTION, default="0")
    freiheitsstrafe_in_monaten = models.IntegerField(
        default=12, help_text="Die Dauer der ausgesprochenen Sanktion in Monaten."
    )
    anzahl_tagessaetze = models.IntegerField(
        default=0, help_text="Die Zahl der ausgesprochenen Tagessätze der Geldstrafe"
    )
    VOLLZUG = (("0", "bedingt"), ("1", "teilbedingt"), ("2", "unbedingt"))
    vollzug = models.CharField(max_length=20, choices=VOLLZUG, default="2")
    nebenverurteilungsscore = models.IntegerField(
        default=0,
        help_text="Anzahl der Schuldsprüche, welche neben dem "
        "Delikt, für welches die Einsatzsstrafe gebildet "
        "wurde, ausgesprochen wurden. + 1 Punkt für "
        "jedes weitere Vergehen. + 2 Punkt für jedes "
        "weitere Verbrechen. + 1 Punkt bei mehrfacher "
        "Begehung.",
    )
    VERFAHRENSART = (("0", "ordentlich"), ("1", "abgekürzt"))
    verfahrensart = models.CharField(max_length=2, choices=VERFAHRENSART, default="0")
    GESCHLECHT = (("0", "männlich"), ("1", "weiblich"))
    geschlecht = models.CharField(max_length=2, choices=GESCHLECHT, default="0")
    NATIONALITAET = (
        ("0", "Schweizerin/Schweizer"),
        ("1", "Ausländer/Ausländerin"),
        ("2", "unbekannt"),
    )
    nationalitaet = models.CharField(max_length=2, choices=NATIONALITAET, default="2")
    betm = models.ManyToManyField("Betm")
    rolle = models.ForeignKey("Rolle", on_delete=models.CASCADE)
    deliktsertrag = models.IntegerField(blank=True, null=True)
    deliktsdauer_in_monaten = models.IntegerField(blank=True, null=True)
    vorbestraft = models.BooleanField(
        default=False,
        verbose_name="vorbestraft",
        help_text="Ob die verurteilte Person vorbestraft ist.",
    )
    vorbestraft_einschlaegig = models.BooleanField(
        default=False,
        verbose_name="einschlägig vorbestraft",
        help_text="Ob die verurteilte Person einschlägig vorbestraft ist.",
    )
    besonderheiten = models.ManyToManyField(
        "Besonderheiten",
        related_name="betmdelikte",
        blank=True,
        help_text="Strafzumessungsrelevante Besonderheiten (z.B. Geständnis/Reue, "
        "verminderte Schuldfähigkeit, Verletzung des Beschleunigungsgebots, "
        "Strafempfindlichkeit).",
    )
    in_ki_modell = models.BooleanField(default=True)
    kurzsachverhalt = models.TextField(
        blank=True,
        default="",
        help_text="Kurze Zusammenfassung des Sachverhalts (wird beim Hovern in der Urteilsliste angezeigt)",
    )
    zusammenfassung = models.TextField(
        blank=True,
        help_text="Die Zusammenfassung der massgebenden Erwägungen für die Strafzumessung",
    )
    bemerkungen = models.TextField(blank=True, help_text="Besondere Bemerkungen zum Fall")
    add_time = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )
    update_time = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.gericht}, Urteil vom {datum_deutsch_formatieren(self.urteilsdatum)} ({self.fall_nr})"

    class Meta:
        verbose_name_plural = "Betäubungsmitteldelikt-Urteile"
        ordering = ["urteilsdatum"]


class Betm(models.Model):
    # Managers
    objects = models.Manager()
    pandas = DataFrameExporter()

    # Datenfelder
    art = models.ForeignKey("BetmArt", on_delete=models.CASCADE)
    menge_in_g = models.IntegerField()
    rein = models.BooleanField(default=True)

    def menge_anzeige(self):
        if self.menge_in_g >= 1000:
            kg = f"{self.menge_in_g / 1000:.1f}".rstrip("0").rstrip(".")
            return f"{kg}kg"
        return f"{self.menge_in_g}g"

    def __str__(self):
        return f'{self.art}, {self.menge_anzeige()}, {"rein" if self.rein else "gemisch"}'


class BetmArt(models.Model):
    # Managers
    objects = models.Manager()
    pandas = DataFrameExporter()

    # Datenfelder
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name


class Rolle(models.Model):
    # Managers
    objects = models.Manager()
    pandas = DataFrameExporter()

    # Datenfelder
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Kanton(models.Model):
    # Managers
    objects = models.Manager()
    pandas = DataFrameExporter()

    # Datenfelder
    abk = models.CharField(max_length=2, default="ZH")

    def __str__(self):
        return self.abk


class KIModelPickleFile(models.Model):
    name = models.CharField(max_length=80)
    file = models.FileField(upload_to="pickles/")
    encoder = models.FileField(upload_to="encoders/", blank=True)
    prognoseleistung_dict = models.JSONField()
    ft_importance_list = models.JSONField(blank=True, null=True)
    ft_importance_list_merged = models.JSONField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SexualdeliktUrteil(models.Model):
    fall_nr = models.CharField(
        max_length=15,
        unique=True,
        help_text="Die Verfahrensnummer des Urteils, dem die Informationen entnommen sind.",
    )
    url_link = models.URLField(
        blank=True,
        help_text="Der URL-Link zum PDF des Urteils, dem die Informationen entnommen sind.",
    )
    gericht = models.CharField(
        max_length=50,
        help_text="Das Gericht, welches das Urteil gefällt hat.",
        default="n/a",
    )
    urteilsdatum = models.DateField(
        blank=True,
        null=True,
        help_text="Das Datum, an welchem das Gericht das Urteil gefällt hat.",
    )
    kanton = models.ForeignKey("Kanton", on_delete=models.CASCADE)

    JA_NEIN_CHOICES = [
        (True, 'Ja'),
        (False, 'Nein'),
    ]

    hauptdelikt = models.ForeignKey('Hauptdelikt',
                                    on_delete=models.CASCADE,
                                    related_name='hauptdelikt',
                                    verbose_name="Hauptdelikt",
                                    help_text='Das Hauptdelikt, für welches die Einsatzstrafe gebildet wird.')
    hauptdelikt_tatmittel = models.ForeignKey('Tatmittel',
                                              related_name='hauptdelikt_tatmittel',
                                              on_delete=models.CASCADE,
                                              verbose_name="Tatmittel",
                                              help_text='Das Tatmittel, mit welchem das Hauptdelikt begangen wurde')
    hauptdelikt_mehrfachbegehung = models.BooleanField(
        choices=JA_NEIN_CHOICES,
        default=False,
        verbose_name="mehrfache Tatbegehung?",
        help_text="Verurteilung wegen mehrfacher Begehung des Hauptdelikts")
    BEZIEHUNG_CHOICES = [
        ('Ehegatte/Partner', 'Ehegatte/Partner'),
        ('Elternteil/Kind', 'Elternteil/Kind'),
        ('entfernt verwandt', 'entfernt verwandt'),
        ('Bekannte', 'Bekannte'),
        ('flüchtig Bekannt', 'flüchtig Bekannt'),
        ('Unbekannte', 'Unbekannte'),
        ('Beziehung unbekannt', 'Beziehung unbekannt'),
    ]
    hauptdelikt_taeter_opfer_beziehung = models.CharField(
        max_length=50,
        choices=BEZIEHUNG_CHOICES,
        verbose_name="Täter-Opfer-Beziehung",
        default='Bekannte',
        help_text="Beziehung zwischen Täter und Opfer. 'flüchtig bekannt' bedeutet, dass der Täter und das Opfer sich "
                  "bspw. am selben Abend kennengelernt haben.")
    OPFERALTER_CHOICES = [
        ('unter_6', 'Unter 6 Jahren'),
        ('unter_10', 'Unter 10 Jahren'),
        ('unter_14', 'Unter 14 Jahren'),
        ('unter_16', 'Unter 16 Jahren'),
        ('unter_18', 'Unter 18 Jahren'),
        ('erwachsen', 'Erwachsen'),
        ('nicht bekannt', 'nicht bekannt'),
    ]
    hauptdelikt_opferalter = models.CharField(
        max_length=20,
        choices=OPFERALTER_CHOICES,
        verbose_name="Opferalter",
        default='erwachsen',
        help_text="Alter des (jüngsten) Opfers des Hauptdelikts (erste Begehung) in Jahren."
    )
    OPFERERFAHRUNG_CHOICES = [
        ('Ja', 'Ja'),
        ('Nein', 'Nein'),
        ('unbekannt', 'unbekannt'),
    ]
    hauptdelikt_opfer_vorerfahrung = models.CharField(
        choices=OPFERERFAHRUNG_CHOICES,
        default='unbekannt',
        verbose_name="Sexuelle Vorerfahrung des Opfers?",
        help_text="Ob das Opfer im Tatzeitpunkt sexuelle Vorerfahrungen hatte")
    hauptdelikt_deliktsdauer_bekannt = models.BooleanField(
        choices=JA_NEIN_CHOICES,
        default=False,
    )
    hautpdelikt_deliktsdauer_einfachbegehung = models.DurationField(
        default=timedelta(minutes=30),
        blank=True,
        null=True,
        verbose_name="Deliktsdauer Hauptdelikt (min)",
        help_text="Die Deliktsdauer des Hauptdelikts in Minuten, soweit bekannt.")
    hauptdelikt_mehrfachbegehung_anzahl = models.IntegerField(blank=True,
                                                              null=True,
                                                              help_text="Anzahl der Vollendungen des Hauptdelikts")
    hauptdelikt_mehrfachbegehung_deliktsperiode = models.DurationField(
        default=timedelta(days=345),
        blank=True,
        null=True,
        verbose_name="Deliktsperiode Hauptdelikt",
        help_text="Periode, in welcher das Hauptdelikt mehrfach begangen wurde, in Tagen")
    sexualdelikte_zusaetzliche = models.ManyToManyField('ZusaetzlicheSexualdelikte',
                                                        related_name='sexualdelikte',
                                                        help_text="weitere Sexualdelikte im Urteilsspruch",
                                                        blank=True)
    deliktsscore_uebrige_delikte = models.IntegerField(
        blank=True,
        null=True,
        help_text="Anzahl der Schuldsprüche, welche neben den Sexualdelikten ausgesprochen wurden. "
                  "+ 1 Punkt für jedes weitere Vergehen. + 2 Punkt für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher "
                  "Begehung.",
    )
    NATIONALITAET = (
        ("0", "Schweizerin/Schweizer"),
        ("1", "Ausländer/Ausländerin"),
        ("2", "unbekannt"),
    )
    GESCHLECHT = (("0", "männlich"), ("1", "weiblich"))
    geschlecht = models.CharField(max_length=2,
                                  choices=GESCHLECHT,
                                  default="0",
                                  help_text="Geschlecht des Täters")
    nationalitaet = models.CharField(max_length=2,
                                     choices=NATIONALITAET,
                                     default="2",
                                     help_text="Nationalität des Täters")
    vorbestraft = models.BooleanField(
        choices=JA_NEIN_CHOICES,
        default=False,
        verbose_name="vorbestraft",
        help_text="Ob Vorstrafen bestehen")
    vorbestraft_einschlaegig = models.BooleanField(
        choices=JA_NEIN_CHOICES,
        default=False,
        verbose_name="einschlägig vorbestraft",
        help_text="Ob einschlägige Vorverurteilungen bestehen")
    besonderheiten = models.ManyToManyField('Besonderheiten',
                                            related_name='besonderheiten',
                                            blank=True)
    bemerkungen = models.TextField(blank=True, help_text="Besondere Bemerkungen zum Fall")
    kurzsachverhalt = models.TextField(
        blank=True,
        default="",
        help_text="Kurze Zusammenfassung des Sachverhalts (wird beim Hovern in der Urteilsliste angezeigt)",
    )
    zusammenfassung = models.TextField(
        blank=True,
        help_text="Die Zusammenfassung der massgebenden Erwägungen für die Strafzumessung",
    )

    HAUPTSANKTION = (("0", "Freiheitsstrafe"), ("1", "Geldstrafe"), ("2", "Busse"))
    hauptsanktion = models.CharField(max_length=1, choices=HAUPTSANKTION, default="0")
    freiheitsstrafe_in_monaten = models.IntegerField(
        default=12, help_text="Die Dauer der ausgesprochenen Sanktion in Monaten."
    )
    anzahl_tagessaetze = models.IntegerField(
        default=0, help_text="Die Zahl der ausgesprochenen Tagessätze der Geldstrafe"
    )
    VOLLZUG = (("0", "bedingt"), ("1", "teilbedingt"), ("2", "unbedingt"))
    vollzug = models.CharField(max_length=20, choices=VOLLZUG, default="2")

    VERFAHRENSART = (("0", "ordentlich"), ("1", "abgekürzt"))
    verfahrensart = models.CharField(max_length=2, choices=VERFAHRENSART, default="0")

    add_time = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )
    update_time = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.gericht}, Urteil vom {datum_deutsch_formatieren(self.urteilsdatum)} ({self.fall_nr})"

    class Meta:
        verbose_name_plural = "Sexualdelikt-Urteile"
        ordering = ["add_time"]


class Hauptdelikt(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Tatmittel(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ZusaetzlicheSexualdelikte(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Besonderheiten(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class GewaltdeliktUrteil(models.Model):
    """Erstinstanzliche Strafzumessungsentscheide zu Gewaltdelikten (Raub,
    Tötungsdelikte, Körperverletzung – je auch versucht). Aufbau analog zu
    SexualdeliktUrteil; das Hauptdelikt ist jenes, für welches die
    Einsatzstrafe gebildet wurde. Die Felder bilden – wie bei den übrigen
    Modellen – die VORINSTANZLICHE Verurteilung ab (vgl. CLAUDE.md)."""

    # Managers
    objects = models.Manager()
    pandas = DataFrameExporter()

    # Grunddaten
    fall_nr = models.CharField(
        max_length=25,
        unique=True,
        help_text="Die Verfahrensnummer des Urteils, dem die Informationen entnommen sind.",
    )
    url_link = models.URLField(
        blank=True,
        help_text="Der URL-Link zum PDF des Urteils, dem die Informationen entnommen sind.",
    )
    gericht = models.CharField(
        max_length=50,
        help_text="Das Gericht, welches das Urteil gefällt hat.",
        default="n/a",
    )
    urteilsdatum = models.DateField(
        blank=True,
        null=True,
        help_text="Das Datum, an welchem das Gericht das Urteil gefällt hat.",
    )
    kanton = models.ForeignKey("Kanton", on_delete=models.CASCADE)

    # Person
    GESCHLECHT = (("0", "männlich"), ("1", "weiblich"))
    geschlecht = models.CharField(
        max_length=2, choices=GESCHLECHT, default="0", help_text="Geschlecht des Täters"
    )
    NATIONALITAET = (
        ("0", "Schweizerin/Schweizer"),
        ("1", "Ausländer/Ausländerin"),
        ("2", "unbekannt"),
    )
    nationalitaet = models.CharField(
        max_length=2, choices=NATIONALITAET, default="2", help_text="Nationalität des Täters"
    )
    vorbestraft = models.BooleanField(
        default=False,
        verbose_name="vorbestraft",
        help_text="Ob die verurteilte Person vorbestraft ist.",
    )
    vorbestraft_einschlaegig = models.BooleanField(
        default=False,
        verbose_name="einschlägig vorbestraft",
        help_text="Ob die verurteilte Person einschlägig (Gewaltdelikt) vorbestraft ist.",
    )

    # Delikt
    HAUPTDELIKT = (
        ("Mord", "Mord (Art. 112 StGB)"),
        ("vorsätzliche Tötung", "vorsätzliche Tötung (Art. 111 StGB)"),
        ("Totschlag", "Totschlag (Art. 113 StGB)"),
        ("fahrlässige Tötung", "fahrlässige Tötung (Art. 117 StGB)"),
        ("schwere Körperverletzung", "schwere Körperverletzung (Art. 122 StGB)"),
        ("einfache Körperverletzung", "einfache Körperverletzung (Art. 123 StGB)"),
        ("fahrlässige Körperverletzung", "fahrlässige Körperverletzung (Art. 125 StGB)"),
        ("Tätlichkeiten", "Tätlichkeiten (Art. 126 StGB)"),
        ("Gefährdung des Lebens", "Gefährdung des Lebens (Art. 129 StGB)"),
        ("Angriff", "Angriff (Art. 134 StGB)"),
        ("Raufhandel", "Raufhandel (Art. 133 StGB)"),
        ("Raub", "Raub (Art. 140 StGB)"),
    )
    hauptdelikt = models.CharField(
        max_length=40,
        choices=HAUPTDELIKT,
        default="einfache Körperverletzung",
        help_text="Das Delikt, für welches die Einsatzstrafe gebildet wurde.",
    )
    versuch = models.BooleanField(
        default=False,
        verbose_name="Versuch",
        help_text="Ob das Hauptdelikt beim Versuch geblieben ist (Art. 22 StGB) – "
        "insb. bei Tötungsdelikten häufig.",
    )
    TATMITTEL = (
        ("unbekannt", "unbekannt/keine Angabe"),
        ("körperliche Gewalt", "körperliche Gewalt (Faustschläge/Tritte)"),
        ("Würgen", "Würgen/Drosseln"),
        ("Messer/Stichwaffe", "Messer/Stich-/Schnittwerkzeug (auch Glas/Flasche)"),
        ("Schusswaffe", "Schusswaffe"),
        ("stumpfer Gegenstand", "stumpfer/gefährlicher Gegenstand"),
        ("Fahrzeug/Motorfahrzeug", "Fahrzeug/Motorfahrzeug"),
        ("andere", "andere/mehrere"),
    )
    tatmittel = models.CharField(
        max_length=30,
        choices=TATMITTEL,
        default="unbekannt",
        help_text="Das beim Hauptdelikt eingesetzte Tatmittel. 'Messer/Stich-/"
        "Schnittwerkzeug' umfasst auch improvisierte scharfe Gegenstände "
        "(z.B. abgebrochene Flasche). Bei abgekürztem Verfahren oft nicht "
        "dokumentiert → 'unbekannt'.",
    )
    VORSATZFORM = (
        ("unbekannt", "unbekannt/keine Angabe"),
        ("eventualvorsatz", "Eventualvorsatz"),
        ("direktvorsatz", "direkter Vorsatz"),
        ("fahrlaessig", "Fahrlässigkeit"),
    )
    vorsatzform = models.CharField(
        max_length=20,
        choices=VORSATZFORM,
        default="unbekannt",
        verbose_name="Vorsatzform",
        help_text="Subjektiver Tatbestand des Hauptdelikts: Eventualvorsatz vs. "
        "direkter Vorsatz (bzw. Fahrlässigkeit, z.B. Art. 117 StGB). Bei "
        "Tötungs-/Körperverletzungsdelikten stark strafzumessungsrelevant.",
    )
    # Qualifikationsgründe (je ein Bool) – anwendbar auf Raub (Art. 140 Ziff. 2–4)
    # wie auch auf Körperverletzung/Tötungsdelikte. Nur setzen, wenn das Gericht
    # den jeweiligen qualifizierenden Umstand ausdrücklich bejaht.
    waffe_gefaehrlicher_gegenstand = models.BooleanField(
        default=False,
        verbose_name="Waffe/gefährlicher Gegenstand",
        help_text="Begehung mit Waffe oder gefährlichem Gegenstand "
        "(z.B. Raub Art. 140 Ziff. 2 StGB, KV Art. 123 Ziff. 2 StGB).",
    )
    bandenmaessig = models.BooleanField(
        default=False,
        help_text="Bandenmässige Begehung (z.B. Raub Art. 140 Ziff. 3 Abs. 2 StGB).",
    )
    besondere_gefaehrlichkeit = models.BooleanField(
        default=False,
        verbose_name="besondere Gefährlichkeit/Grausamkeit",
        help_text="Besondere Gefährlichkeit bzw. besonders skrupellose/grausame "
        "Begehung (z.B. Raub Art. 140 Ziff. 3 Abs. 3, Mord Art. 112 StGB).",
    )
    lebensgefahr = models.BooleanField(
        default=False,
        verbose_name="Lebensgefahr",
        help_text="Herbeiführung einer Lebensgefahr für das Opfer "
        "(z.B. Raub Art. 140 Ziff. 4 StGB, lebensgefährliche Körperverletzung).",
    )
    mehrfach = models.BooleanField(
        default=False,
        help_text="Ob das Hauptdelikt mehrfach begangen wurde.",
    )
    opferzahl = models.IntegerField(
        default=1, help_text="Anzahl der vom Hauptdelikt betroffenen Opfer."
    )
    BEZIEHUNG_CHOICES = (
        ("unbekannt", "Beziehung unbekannt"),
        ("Partner/Ex-Partner", "Partner/Ex-Partner (häusliche Gewalt)"),
        ("Familie", "Familienangehörige"),
        ("Bekannte", "Bekannte"),
        ("flüchtig bekannt", "flüchtig bekannt"),
        ("Unbekannte", "Unbekannte (Opfer war Fremder)"),
    )
    taeter_opfer_beziehung = models.CharField(
        max_length=30,
        choices=BEZIEHUNG_CHOICES,
        default="unbekannt",
        verbose_name="Täter-Opfer-Beziehung",
        help_text="Beziehung zwischen Täter und (Haupt-)Opfer. 'Unbekannte' = das "
        "Opfer war eine dem Täter fremde Person; 'unbekannt' = Beziehung nicht dokumentiert.",
    )
    VERLETZUNGSFOLGE = (
        ("unbekannt", "unbekannt/keine Angabe"),
        ("keine", "keine (z.B. reiner Raub/Versuch)"),
        ("Tätlichkeit", "geringfügig (Tätlichkeit)"),
        ("leicht", "leichte Verletzung"),
        ("erheblich", "erhebliche Verletzung"),
        ("schwer", "schwere/bleibende Verletzung"),
        ("lebensgefährlich", "lebensgefährliche Verletzung"),
        ("Tod", "Tod des Opfers"),
    )
    verletzungsfolge = models.CharField(
        max_length=20,
        choices=VERLETZUNGSFOLGE,
        default="unbekannt",
        help_text="Schwerste eingetretene Verletzungsfolge beim Opfer des Hauptdelikts.",
    )
    KOERPERTEIL = (
        ("unbekannt", "unbekannt/keine Angabe"),
        ("nicht betroffen", "nicht betroffen (z.B. reiner Raub)"),
        ("Kopf/Hals", "Kopf/Hals"),
        ("Rumpf", "Rumpf (Brust/Bauch/Rücken)"),
        ("Extremitäten", "Extremitäten (Arme/Beine)"),
        ("mehrere", "mehrere/ganzer Körper"),
    )
    angegriffenes_koerperteil = models.CharField(
        max_length=20,
        choices=KOERPERTEIL,
        default="unbekannt",
        verbose_name="angegriffenes Körperteil",
        help_text="Vom Angriff (haupt-)betroffene Körperregion des Opfers – "
        "relevant für die Gefährlichkeit bei KV/Tötungsdelikten.",
    )
    SUBSTANZEINFLUSS = (
        ("unbekannt", "unbekannt/keine Angabe"),
        ("nein", "kein Einfluss"),
        ("Alkohol", "Alkohol"),
        ("Drogen", "Drogen/Medikamente"),
        ("Alkohol+Drogen", "Alkohol und Drogen"),
    )
    substanzeinfluss = models.CharField(
        max_length=20,
        choices=SUBSTANZEINFLUSS,
        default="unbekannt",
        verbose_name="Substanzeinfluss",
        help_text="Ob der Täter im Tatzeitpunkt unter Alkohol-/Drogeneinfluss stand "
        "(strafzumessungsrelevant, Art. 19/47 StGB).",
    )
    deliktssumme = models.IntegerField(
        blank=True,
        null=True,
        help_text="Beute-/Deliktsbetrag – nur bei Raub relevant, bei Tötung/KV leer lassen.",
    )
    deliktsscore_uebrige_delikte = models.IntegerField(
        default=0,
        help_text="Anzahl der Schuldsprüche, welche neben dem Hauptdelikt "
        "ausgesprochen wurden. + 1 Punkt für jedes weitere Vergehen. + 2 Punkt "
        "für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher Begehung.",
    )
    besonderheiten = models.ManyToManyField(
        "Besonderheiten",
        related_name="gewaltdelikte",
        blank=True,
        help_text="Strafzumessungsrelevante Besonderheiten (z.B. verminderte "
        "Schuldfähigkeit, Affekt/entschuldbare Gemütsbewegung, Notwehr(-exzess), "
        "Geständnis/Reue, Provokation durch das Opfer).",
    )

    # Sanktion
    HAUPTSANKTION = (("0", "Freiheitsstrafe"), ("1", "Geldstrafe"), ("2", "Busse"))
    hauptsanktion = models.CharField(max_length=1, choices=HAUPTSANKTION, default="0")
    freiheitsstrafe_in_monaten = models.IntegerField(
        default=12, help_text="Die Dauer der ausgesprochenen Sanktion in Monaten."
    )
    anzahl_tagessaetze = models.IntegerField(
        default=0, help_text="Die Zahl der ausgesprochenen Tagessätze der Geldstrafe"
    )
    VOLLZUG = (("0", "bedingt"), ("1", "teilbedingt"), ("2", "unbedingt"))
    vollzug = models.CharField(max_length=20, choices=VOLLZUG, default="2")
    VERFAHRENSART = (("0", "ordentlich"), ("1", "abgekürzt"))
    verfahrensart = models.CharField(max_length=2, choices=VERFAHRENSART, default="0")

    # Weitere Informationen
    in_ki_modell = models.BooleanField(default=True)
    kurzsachverhalt = models.TextField(
        blank=True,
        default="",
        help_text="Kurze Zusammenfassung des Sachverhalts (wird beim Hovern in der Urteilsliste angezeigt)",
    )
    zusammenfassung = models.TextField(
        blank=True,
        help_text="Die Zusammenfassung der massgebenden Erwägungen für die Strafzumessung",
    )
    bemerkungen = models.TextField(blank=True, help_text="Besondere Bemerkungen zum Fall")
    add_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.gericht}, Urteil vom {datum_deutsch_formatieren(self.urteilsdatum)} ({self.fall_nr})"

    class Meta:
        verbose_name_plural = "Gewaltdelikt-Urteile"
        ordering = ["urteilsdatum"]


def _strafe_anzeige(monate, tagessaetze):
    """Kurzform einer Einsatz-/Einzelstrafe oder eines Zuschlags, z.B. «6 Mt.»
    oder «20 TS»; leer, wenn nicht beziffert."""
    if monate is not None:
        return f"{monate} Mt."
    if tagessaetze is not None:
        return f"{tagessaetze} TS"
    return ""


class Konkursdelikt(models.Model):
    """Katalog der Konkurs- und Betreibungsdelikte (Art. 163–169 StGB). Wird von
    KonkursdeliktUrteil sowohl für das Hauptdelikt als auch für die zusätzlichen
    (asperierten) Konkursdelikte verwendet."""

    name = models.CharField(max_length=100, unique=True)
    hoechststrafe_jahre = models.IntegerField(
        help_text="Höchstmass der angedrohten Freiheitsstrafe in Jahren "
        "(5 = Verbrechen, 3 = Vergehen)."
    )

    @property
    def bezeichnung(self):
        """«165, Misswirtschaft» → «Misswirtschaft (Art. 165 StGB)»."""
        artikel, _, titel = self.name.partition(", ")
        return f"{titel} (Art. {artikel} StGB)" if titel else self.name

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Konkursdelikte"
        ordering = ["name"]


class KonkursdeliktUrteil(models.Model):
    """Strafzumessungsentscheide zu Konkurs- und Betreibungsdelikten
    (Art. 163–169 StGB). Aufbau analog zu SexualdeliktUrteil: Hauptdelikt +
    zusätzliche Konkursdelikte + Score für die übrigen Delikte.

    Erfasst werden auch Urteile, in denen die Einsatzstrafe auf einem anderen
    Delikt beruht (z.B. ungetreue Geschäftsbesorgung) und die Konkursdelikte nur
    asperiert werden; dann bleibt `hauptdelikt` leer, `einsatzdelikt_uebriges`
    nennt das Einsatzdelikt, und die Konkursdelikte stehen samt Einzelstrafe und
    Asperationszuschlag in KonkursdeliktAsperation. Kein ML-Modell."""

    # Grunddaten
    fall_nr = models.CharField(
        max_length=25,
        unique=True,
        help_text="Die Verfahrensnummer des Urteils, dem die Informationen entnommen sind.",
    )
    url_link = models.URLField(
        blank=True,
        help_text="Der URL-Link zum PDF des Urteils, dem die Informationen entnommen sind.",
    )
    gericht = models.CharField(
        max_length=50,
        help_text="Das Gericht, welches das Urteil gefällt hat.",
        default="n/a",
    )
    urteilsdatum = models.DateField(
        blank=True,
        null=True,
        help_text="Das Datum, an welchem das Gericht das Urteil gefällt hat.",
    )
    kanton = models.ForeignKey("Kanton", on_delete=models.CASCADE)

    # Person
    GESCHLECHT = (("0", "männlich"), ("1", "weiblich"))
    geschlecht = models.CharField(
        max_length=2, choices=GESCHLECHT, default="0", help_text="Geschlecht des Täters"
    )
    NATIONALITAET = (
        ("0", "Schweizerin/Schweizer"),
        ("1", "Ausländer/Ausländerin"),
        ("2", "unbekannt"),
    )
    nationalitaet = models.CharField(
        max_length=2, choices=NATIONALITAET, default="2", help_text="Nationalität des Täters"
    )
    vorbestraft = models.BooleanField(
        default=False,
        verbose_name="vorbestraft",
        help_text="Ob die verurteilte Person vorbestraft ist.",
    )
    vorbestraft_einschlaegig = models.BooleanField(
        default=False,
        verbose_name="einschlägig vorbestraft",
        help_text="Ob die verurteilte Person wegen Betreibungs- oder Konkursdelikten "
        "vorbestraft ist (auch per Strafbefehl).",
    )

    # Einsatzdelikt
    hauptdelikt = models.ForeignKey(
        "Konkursdelikt",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="konkurs_urteile_hauptdelikt",
        help_text="Das Konkursdelikt, für welches die Einsatzstrafe gebildet wurde. "
        "Leer lassen, wenn die Einsatzstrafe auf einem anderen Delikt beruht "
        "(dann einsatzdelikt_uebriges ausfüllen).",
    )
    einsatzdelikt_uebriges = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Einsatzdelikt (kein Konkursdelikt)",
        help_text="Nur wenn die Einsatzstrafe nicht auf einem Konkursdelikt beruht, "
        "z.B. «ungetreue Geschäftsbesorgung (Art. 158 Ziff. 1 Abs. 3 StGB)».",
    )
    STRAFZUMESSUNG_QUELLE = (
        ("Vorinstanz", "Vorinstanz"),
        ("Berufungsinstanz", "Berufungsinstanz"),
    )
    strafzumessung_quelle = models.CharField(
        max_length=20,
        choices=STRAFZUMESSUNG_QUELLE,
        default="Vorinstanz",
        verbose_name="Quelle der Einsatz-/Einzelstrafen",
        help_text="Aus wessen Erwägungen Einsatzstrafe, Einzelstrafen und "
        "Asperationszuschläge stammen (die ausgesprochene Sanktion folgt stets "
        "dem Vorinstanz-Prinzip).",
    )
    einsatzstrafe_monate = models.IntegerField(
        blank=True,
        null=True,
        help_text="Einsatzstrafe für das Einsatzdelikt in Monaten (Tatkomponente, "
        "vor Asperation und Täterkomponente), soweit im Urteil beziffert.",
    )
    einsatzstrafe_tagessaetze = models.IntegerField(
        blank=True,
        null=True,
        help_text="Einsatzstrafe für das Einsatzdelikt in Tagessätzen (bzw. "
        "Strafeinheiten), soweit im Urteil beziffert.",
    )
    hauptdelikt_mehrfach = models.BooleanField(
        default=False,
        verbose_name="Hauptdelikt mehrfach",
        help_text="Nur wenn der Schuldspruch beim Hauptdelikt ausdrücklich auf «mehrfach» lautet.",
    )
    hauptdelikt_deliktssumme = models.IntegerField(
        blank=True,
        null=True,
        help_text="163: dem Zugriff entzogener Wert (nicht Verlustscheinsumme); "
        "164: entzogenes Haftungssubstrat; 165: Verschleppungsschaden; "
        "167: Bevorzugungsbetrag; 166: leer lassen.",
    )
    hauptdelikt_deliktsdauer_in_monaten = models.IntegerField(
        blank=True,
        null=True,
        help_text="165: Verschleppungsdauer; 166: Dauer der Unterlassung; "
        "163: Deliktszeitraum.",
    )
    hauptdelikt_anzahl_tathandlungen = models.IntegerField(
        blank=True,
        null=True,
        help_text="z.B. Zahl der Pfändungsvollzüge (163) oder Entzugshandlungen (164).",
    )

    # Weitere Delikte
    konkursdelikte_zusaetzliche = models.ManyToManyField(
        "Konkursdelikt",
        through="KonkursdeliktAsperation",
        related_name="konkurs_urteile_zusaetzlich",
        blank=True,
        help_text="Weitere bzw. asperierte Konkursdelikte im Urteilsspruch.",
    )
    deliktsscore_uebrige_delikte = models.IntegerField(
        default=0,
        help_text="Schuldsprüche neben den Konkursdelikten (ohne ein allfälliges "
        "Einsatzdelikt gemäss einsatzdelikt_uebriges). + 1 Punkt für jedes weitere "
        "Vergehen. + 2 Punkt für jedes weitere Verbrechen. + 1 Punkt bei mehrfacher "
        "Begehung.",
    )

    # Merkmale der Konkursdelikte
    VOLLSTRECKUNGSART = (
        ("unbekannt", "unbekannt"),
        ("Konkurs", "Konkurs"),
        ("Pfändung/Verlustschein", "Pfändung/Verlustschein"),
    )
    vollstreckungsart = models.CharField(
        max_length=25,
        choices=VOLLSTRECKUNGSART,
        default="unbekannt",
        help_text="Objektive Strafbarkeitsbedingung: Konkurseröffnung oder "
        "Verlustschein aus Pfändung.",
    )
    TAETERSTELLUNG = (
        ("unbekannt", "unbekannt"),
        ("Schuldner", "Schuldner (natürliche Person)"),
        ("Organ", "Organ (Art. 29 StGB)"),
        ("faktisches Organ", "faktisches Organ"),
        ("Dritter", "Dritter (Art. 163/164 Ziff. 2 StGB)"),
        ("Teilnehmer", "Teilnehmer ohne Sondereigenschaft (Art. 26 StGB)"),
    )
    taeterstellung = models.CharField(
        max_length=20, choices=TAETERSTELLUNG, default="unbekannt"
    )
    untergeordnete_rolle = models.BooleanField(
        default=False,
        help_text="Nur wenn das Urteil eine untergeordnete/nicht federführende Rolle feststellt.",
    )
    anzahl_gesellschaften = models.IntegerField(
        blank=True,
        null=True,
        help_text="Zahl der betroffenen Gesellschaften (v.a. bei 165/166).",
    )
    VORSATZFORM = (
        ("unbekannt", "unbekannt/keine Angabe"),
        ("eventualvorsatz", "Eventualvorsatz/-absicht"),
        ("direktvorsatz", "direkter Vorsatz/Absicht"),
    )
    vorsatzform = models.CharField(
        max_length=20, choices=VORSATZFORM, default="unbekannt"
    )
    BEWEGGRUND = (
        ("unbekannt", "unbekannt/keine Angabe"),
        ("Sanierungsversuch", "Sanierungsversuch"),
        ("Selbstbegünstigung", "Selbstbegünstigung/Bereicherung"),
        ("Firmenbestattung", "Firmenbestattung"),
        ("fremdnützig", "fremdnützig"),
    )
    beweggrund = models.CharField(
        max_length=20,
        choices=BEWEGGRUND,
        default="unbekannt",
        help_text="Bei 163/164 ist das finanzielle Motiv deliktsimmanent; dort nur "
        "Firmenbestattung oder fremdnützig setzen, sonst «unbekannt».",
    )
    konstrukt_machenschaften = models.BooleanField(
        default=False,
        verbose_name="Konstrukt/Machenschaften",
        help_text="Systematisches Vorgehen (Vertragskonstrukt, Kontokorrent, neue "
        "Konten u.Ä.) statt blosser Falschangabe – nur wenn vom Gericht festgestellt.",
    )
    notlage_oder_sucht = models.BooleanField(
        default=False,
        verbose_name="Notlage oder Sucht",
        help_text="Nur wenn das Urteil eine akute finanzielle Notlage oder eine "
        "Suchterkrankung ausdrücklich verschuldensmindernd berücksichtigt.",
    )
    buchfuehrung_fehlt_vollstaendig = models.BooleanField(
        blank=True,
        null=True,
        help_text="Nur bei einem Schuldspruch nach Art. 166 StGB: Ja = Buchhaltung "
        "fehlt ganz, Nein = nur unvollständig/mangelhaft; sonst leer.",
    )
    besonderheiten = models.ManyToManyField(
        "Besonderheiten",
        related_name="konkursdelikte",
        blank=True,
    )

    # Sanktion
    HAUPTSANKTION = (("0", "Freiheitsstrafe"), ("1", "Geldstrafe"), ("2", "Busse"))
    hauptsanktion = models.CharField(max_length=1, choices=HAUPTSANKTION, default="1")
    freiheitsstrafe_in_monaten = models.IntegerField(
        default=0, help_text="Die Dauer der ausgesprochenen Sanktion in Monaten."
    )
    anzahl_tagessaetze = models.IntegerField(
        default=0, help_text="Die Zahl der ausgesprochenen Tagessätze der Geldstrafe"
    )
    VOLLZUG = (("0", "bedingt"), ("1", "teilbedingt"), ("2", "unbedingt"))
    vollzug = models.CharField(max_length=20, choices=VOLLZUG, default="0")
    VERFAHRENSART = (("0", "ordentlich"), ("1", "abgekürzt"))
    verfahrensart = models.CharField(max_length=2, choices=VERFAHRENSART, default="0")

    # Weitere Informationen
    kurzsachverhalt = models.TextField(
        blank=True,
        default="",
        help_text="Kurze Zusammenfassung des Sachverhalts (wird beim Hovern in der Urteilsliste angezeigt)",
    )
    zusammenfassung = models.TextField(
        blank=True,
        help_text="Die Zusammenfassung der massgebenden Erwägungen für die Strafzumessung",
    )
    bemerkungen = models.TextField(blank=True, help_text="Besondere Bemerkungen zum Fall")
    add_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        fehler = {}
        if bool(self.hauptdelikt_id) == bool(self.einsatzdelikt_uebriges.strip()):
            fehler["einsatzdelikt_uebriges"] = (
                "Genau eines von «Hauptdelikt» und «Einsatzdelikt (kein "
                "Konkursdelikt)» ausfüllen."
            )
        if not self.hauptdelikt_id and (
            self.hauptdelikt_mehrfach
            or self.hauptdelikt_deliktssumme is not None
            or self.hauptdelikt_deliktsdauer_in_monaten is not None
            or self.hauptdelikt_anzahl_tathandlungen is not None
        ):
            fehler["hauptdelikt"] = (
                "Die hauptdelikt_*-Felder nur ausfüllen, wenn ein Konkursdelikt die "
                "Einsatzstrafe trägt; sonst gehören die Angaben in die Asperationszeilen."
            )
        if self.einsatzstrafe_monate is not None and self.einsatzstrafe_tagessaetze is not None:
            fehler["einsatzstrafe_tagessaetze"] = "Einsatzstrafe entweder in Monaten oder in Tagessätzen."
        if self.vorbestraft_einschlaegig and not self.vorbestraft:
            fehler["vorbestraft_einschlaegig"] = "Einschlägig vorbestraft setzt «vorbestraft» voraus."
        if fehler:
            raise ValidationError(fehler)

    @property
    def einsatzdelikt_anzeige(self):
        """Bezeichnung des Einsatzdelikts, gleich ob Konkursdelikt oder nicht."""
        if self.hauptdelikt_id:
            return self.hauptdelikt.bezeichnung
        return self.einsatzdelikt_uebriges

    @property
    def einsatzstrafe_anzeige(self):
        return _strafe_anzeige(self.einsatzstrafe_monate, self.einsatzstrafe_tagessaetze)

    def __str__(self):
        return f"{self.gericht}, Urteil vom {datum_deutsch_formatieren(self.urteilsdatum)} ({self.fall_nr})"

    class Meta:
        verbose_name = "Konkursdelikt-Urteil"
        verbose_name_plural = "Konkursdelikt-Urteile"
        ordering = ["urteilsdatum"]


class KonkursdeliktAsperation(models.Model):
    """Ein zusätzliches (asperiertes) Konkursdelikt eines KonkursdeliktUrteils mit
    isolierter Einzelstrafe und Asperationszuschlag. Derselbe Tatbestand darf
    mehrfach vorkommen, z.B. Misswirtschaft je Gesellschaft (Feld `bezeichnung`)."""

    urteil = models.ForeignKey(
        "KonkursdeliktUrteil", on_delete=models.CASCADE, related_name="asperationen"
    )
    delikt = models.ForeignKey("Konkursdelikt", on_delete=models.PROTECT)
    bezeichnung = models.CharField(
        max_length=100,
        blank=True,
        help_text="Präzisierung, z.B. betroffene Gesellschaft oder Tatkomplex.",
    )
    mehrfach = models.BooleanField(
        default=False,
        help_text="Nur wenn der Schuldspruch ausdrücklich auf «mehrfach» lautet.",
    )
    deliktssumme = models.IntegerField(blank=True, null=True)
    deliktsdauer_in_monaten = models.IntegerField(blank=True, null=True)
    einzelstrafe_monate = models.IntegerField(
        blank=True, null=True, help_text="Isoliert bemessene Einzelstrafe in Monaten."
    )
    einzelstrafe_tagessaetze = models.IntegerField(
        blank=True, null=True, help_text="Isoliert bemessene Einzelstrafe in Tagessätzen."
    )
    zuschlag_monate = models.IntegerField(
        blank=True, null=True, help_text="Asperationszuschlag auf die Einsatzstrafe in Monaten."
    )
    zuschlag_tagessaetze = models.IntegerField(
        blank=True, null=True, help_text="Asperationszuschlag auf die Einsatzstrafe in Tagessätzen."
    )

    def clean(self):
        from django.core.exceptions import ValidationError

        fehler = {}
        if self.einzelstrafe_monate is not None and self.einzelstrafe_tagessaetze is not None:
            fehler["einzelstrafe_tagessaetze"] = "Einzelstrafe entweder in Monaten oder in Tagessätzen."
        if self.zuschlag_monate is not None and self.zuschlag_tagessaetze is not None:
            fehler["zuschlag_tagessaetze"] = "Zuschlag entweder in Monaten oder in Tagessätzen."
        if fehler:
            raise ValidationError(fehler)

    @property
    def einzelstrafe_anzeige(self):
        return _strafe_anzeige(self.einzelstrafe_monate, self.einzelstrafe_tagessaetze)

    @property
    def zuschlag_anzeige(self):
        return _strafe_anzeige(self.zuschlag_monate, self.zuschlag_tagessaetze)

    def __str__(self):
        zusatz = f", {self.bezeichnung}" if self.bezeichnung else ""
        return f"{self.delikt.bezeichnung}{zusatz}"

    class Meta:
        verbose_name = "zusätzliches Konkursdelikt"
        verbose_name_plural = "zusätzliche Konkursdelikte (Asperation)"


class PraejudizensucheLog(models.Model):
    """Protokolliert jede Anfrage/Antwort des Präjudizensuche-Chats (Anthropic-API,
    öffentlich erreichbar) für Missbrauchs-Monitoring und Fehleranalyse."""

    created_at = models.DateTimeField(auto_now_add=True)
    conversation_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Client-seitig erzeugte UUID, gruppiert die Turns einer Konversation.",
    )
    turn_index = models.PositiveIntegerField(
        help_text="0-basierter Index dieser Nachricht innerhalb der Konversation."
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_message = models.TextField()
    assistant_reply = models.TextField(blank=True)
    tool_calls = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste von {name, input} der in diesem Turn aufgerufenen eigenen Tools "
        "(ohne volle Tool-Resultate).",
    )
    model_used = models.CharField(max_length=100, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    rate_limited = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Präjudizensuche-Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.conversation_id} #{self.turn_index} ({self.created_at:%Y-%m-%d %H:%M})"