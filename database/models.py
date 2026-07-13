import pandas as pd
from django.db import models
import locale
from datetime import timedelta



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
        "gewerbsmässig bzw. (bei der Veruntreuung) qualifiziert begangen wurde.",
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
    zusammenfassung = models.TextField(
        blank=True,
        help_text="Die Zusammenfassung der massgebenden Erwägungen für die Strafzumessung",
    )
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
        try:
            locale.setlocale(locale.LC_TIME, "de_CH")
        except:
            locale.setlocale(locale.LC_ALL, "")
        return f"{self.gericht}, Urteil vom {self.urteilsdatum.strftime('%d. %B %Y')} ({self.fall_nr})"

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
    in_ki_modell = models.BooleanField(default=True)
    zusammenfassung = models.TextField(
        blank=True,
        help_text="Die Zusammenfassung der massgebenden Erwägungen für die Strafzumessung",
    )
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
        return f"{self.gericht}, Urteil vom {self.urteilsdatum.strftime('%d. %B %Y')} ({self.fall_nr})"

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

    def __str__(self):
        return (
            f'{self.art}, {str(self.menge_in_g)}g, {"rein" if self.rein else "gemisch"}'
        )


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


class DiagrammSVG(models.Model):
    name = models.CharField(max_length=50)
    file = models.ImageField(upload_to="diagramme/")
    lesehinweis = models.CharField(max_length=1000, blank=True, null=True)
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
        try:
            locale.setlocale(locale.LC_TIME, "de_CH")
        except:
            locale.setlocale(locale.LC_ALL, "")
        return f"{self.gericht}, Urteil vom {self.urteilsdatum.strftime('%d. %B %Y')} ({self.fall_nr})"

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
    zusammenfassung = models.TextField(
        blank=True,
        help_text="Die Zusammenfassung der massgebenden Erwägungen für die Strafzumessung",
    )
    bemerkungen = models.TextField(blank=True, help_text="Besondere Bemerkungen zum Fall")
    add_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        try:
            locale.setlocale(locale.LC_TIME, "de_CH")
        except:
            locale.setlocale(locale.LC_ALL, "")
        return f"{self.gericht}, Urteil vom {self.urteilsdatum.strftime('%d. %B %Y')} ({self.fall_nr})"

    class Meta:
        verbose_name_plural = "Gewaltdelikt-Urteile"
        ordering = ["urteilsdatum"]