from datetime import date, timedelta

from django.test import TestCase, override_settings
from django.urls import reverse

from .filterspec import (
    BETM_FILTER_CONFIG,
    GEWALTDELIKT_FILTER_CONFIG,
    SEXUALDELIKT_FILTER_CONFIG,
    URTEIL_FILTER_CONFIG,
    datensaetze_erstellen,
    filterspezifikation_erstellen,
)
from .models import (
    Besonderheiten,
    Betm,
    BetmArt,
    BetmUrteil,
    DiagrammSVG,
    GewaltdeliktUrteil,
    Hauptdelikt,
    Kanton,
    Rolle,
    SexualdeliktUrteil,
    Tatmittel,
    Urteil,
    ZusaetzlicheSexualdelikte,
)

ALLE_KONFIGURATIONEN = (
    (Urteil, URTEIL_FILTER_CONFIG),
    (BetmUrteil, BETM_FILTER_CONFIG),
    (SexualdeliktUrteil, SEXUALDELIKT_FILTER_CONFIG),
    (GewaltdeliktUrteil, GEWALTDELIKT_FILTER_CONFIG),
)


class FilterspezifikationTest(TestCase):
    """Serverseitige Haelfte der Datenbankfilterung (database/filterspec.py)."""

    @classmethod
    def setUpTestData(cls):
        kanton = Kanton.objects.create(abk="ZH")
        vergewaltigung = Hauptdelikt.objects.create(name="Art. 190, Vergewaltigung")
        schaendung = Hauptdelikt.objects.create(name="Art. 191, Schändung")
        gewalt = Tatmittel.objects.create(name="Gewalt")
        druck = Tatmittel.objects.create(name="psychischer Druck")
        gestaendnis = Besonderheiten.objects.create(name="Geständnisrabatt")

        cls.erstes = SexualdeliktUrteil.objects.create(
            fall_nr="SB240001",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 3, 1),
            kanton=kanton,
            hauptdelikt=vergewaltigung,
            hauptdelikt_tatmittel=gewalt,
            vorbestraft=True,
            freiheitsstrafe_in_monaten=48,
            zusammenfassung="Der Beschuldigte handelte mit erheblicher Gewalt.",
        )
        cls.erstes.besonderheiten.set([gestaendnis])

        SexualdeliktUrteil.objects.create(
            fall_nr="SB240002",
            gericht="Bezirksgericht Winterthur",
            urteilsdatum=date(2025, 6, 1),
            kanton=kanton,
            hauptdelikt=schaendung,
            hauptdelikt_tatmittel=druck,
            vorbestraft=False,
            freiheitsstrafe_in_monaten=24,
        )

    def spezifikation(self):
        return filterspezifikation_erstellen(
            SexualdeliktUrteil, SEXUALDELIKT_FILTER_CONFIG, SexualdeliktUrteil.objects.all()
        )

    def feld(self, name):
        return next(
            feld for feld in self.spezifikation()["felder"] if feld["name"] == name
        )

    def test_feldtypen_werden_aus_dem_modell_abgeleitet(self):
        self.assertEqual(self.feld("hauptdelikt")["typ"], "choice")
        self.assertEqual(self.feld("vorbestraft")["typ"], "bool")
        self.assertEqual(self.feld("besonderheiten")["typ"], "multi")
        self.assertEqual(self.feld("urteilsdatum")["typ"], "date")
        self.assertEqual(self.feld("freiheitsstrafe_in_monaten")["typ"], "number")

    def test_nur_im_bestand_vorkommende_auswahlwerte(self):
        werte = [option["value"] for option in self.feld("hauptdelikt")["optionen"]]
        self.assertEqual(werte, ["Art. 190, Vergewaltigung", "Art. 191, Schändung"])

    def test_felder_ohne_filterwirkung_entfallen(self):
        # kanton kennt im Bestand nur einen Wert und taugt daher nicht als Filter
        namen = [feld["name"] for feld in self.spezifikation()["felder"]]
        self.assertNotIn("kanton", namen)
        self.assertIn("hauptdelikt", namen)

    def test_grenzwerte_von_zahlen_und_daten(self):
        self.assertEqual(self.feld("freiheitsstrafe_in_monaten")["min"], 24)
        self.assertEqual(self.feld("freiheitsstrafe_in_monaten")["max"], 48)
        self.assertEqual(self.feld("urteilsdatum")["min"], "2024-03-01")
        self.assertEqual(self.feld("urteilsdatum")["max"], "2025-06-01")

    def test_datensaetze_sind_normalisiert(self):
        spezifikation = self.spezifikation()
        datensaetze = datensaetze_erstellen(
            SexualdeliktUrteil,
            SEXUALDELIKT_FILTER_CONFIG,
            SexualdeliktUrteil.objects.all(),
            spezifikation,
        )
        datensatz = datensaetze[str(self.erstes.pk)]
        self.assertEqual(datensatz["hauptdelikt"], "Art. 190, Vergewaltigung")
        self.assertEqual(datensatz["besonderheiten"], ["Geständnisrabatt"])
        self.assertIs(datensatz["vorbestraft"], True)
        self.assertEqual(datensatz["urteilsdatum"], "2024-03-01")
        # Sortierfelder muessen ebenfalls mitgeliefert werden
        self.assertEqual(datensatz["fall_nr"], "SB240001")

    def test_dauerfelder_werden_in_die_anzeigeeinheit_umgerechnet(self):
        self.erstes.hautpdelikt_deliktsdauer_einfachbegehung = timedelta(minutes=45)
        self.erstes.hauptdelikt_mehrfachbegehung_deliktsperiode = timedelta(days=200)
        self.erstes.save()
        spezifikation = self.spezifikation()
        datensaetze = datensaetze_erstellen(
            SexualdeliktUrteil,
            SEXUALDELIKT_FILTER_CONFIG,
            SexualdeliktUrteil.objects.all(),
            spezifikation,
        )
        datensatz = datensaetze[str(self.erstes.pk)]
        self.assertEqual(datensatz["hautpdelikt_deliktsdauer_einfachbegehung"], 45)
        self.assertEqual(datensatz["hauptdelikt_mehrfachbegehung_deliktsperiode"], 200)

    def test_volltextblob_enthaelt_die_konfigurierten_felder(self):
        spezifikation = self.spezifikation()
        datensaetze = datensaetze_erstellen(
            SexualdeliktUrteil,
            SEXUALDELIKT_FILTER_CONFIG,
            SexualdeliktUrteil.objects.all(),
            spezifikation,
        )
        blob = datensaetze[str(self.erstes.pk)]["_t"]
        self.assertIn("sb240001", blob)
        self.assertIn("bezirksgericht zürich", blob)
        self.assertIn("erheblicher gewalt", blob)


# Die Ansicht bindet database/filter.js per {% static %} ein. Im Test soll das
# nicht von einem vorgaengigen collectstatic-Lauf abhaengen.
@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
class SexualdeliktListViewTest(TestCase):
    def test_ansicht_liefert_spezifikation_und_datensaetze(self):
        kanton = Kanton.objects.create(abk="ZH")
        urteil = SexualdeliktUrteil.objects.create(
            fall_nr="SB240003",
            gericht="Bezirksgericht Uster",
            urteilsdatum=date(2024, 9, 9),
            kanton=kanton,
            hauptdelikt=Hauptdelikt.objects.create(name="Art. 189, sexuelle Nötigung"),
            hauptdelikt_tatmittel=Tatmittel.objects.create(name="Gewalt"),
        )
        antwort = self.client.get("/sexualdatabase")
        self.assertEqual(antwort.status_code, 200)
        self.assertIn("filter_spec", antwort.context)
        self.assertIn(str(urteil.pk), antwort.context["filter_records"])
        self.assertContains(antwort, 'id="filter-spec"')
        self.assertContains(antwort, f'data-pk="{urteil.pk}"')


class FilterkonfigurationenTest(TestCase):
    """
    Prüft die vier Modellkonfigurationen gegen das jeweilige Modell. Der
    häufigste Fehler beim Nachführen ist ein Feldname, den es nicht (mehr) gibt
    - der fällt hier auf, nicht erst beim Seitenaufruf.
    """

    def test_alle_konfigurierten_feldnamen_existieren(self):
        for model, config in ALLE_KONFIGURATIONEN:
            gruppierte = [
                feldname
                for _, feldnamen in config["gruppen"]
                for feldname in feldnamen
            ]
            # Abhängige Spannen und abgeleitete Felder sind keine Modellfelder.
            abhaengige = config.get("abhaengige_spannen", {})
            abgeleitete = config.get("abgeleitete_felder", {})
            with self.subTest(model=model.__name__):
                for feldname in gruppierte:
                    if feldname not in abhaengige and feldname not in abgeleitete:
                        model._meta.get_field(feldname)
                for feldname in config.get("labels", {}):
                    model._meta.get_field(feldname)
                for feldname in config.get("einheiten", {}):
                    model._meta.get_field(feldname)
                for sortierfeld in config["sortierfelder"]:
                    model._meta.get_field(sortierfeld["name"])
                for feldname in config["primaer"]:
                    self.assertIn(feldname, gruppierte)
                for feldname, abgeleitet in abgeleitete.items():
                    self.assertIn(feldname, gruppierte)
                    self.assertTrue(callable(abgeleitet["wert"]))
                    werte = {wert for wert, _ in abgeleitet["choices"]}
                    self.assertTrue(werte)
                for feldname, spanne in abhaengige.items():
                    self.assertIn(feldname, gruppierte)
                    quellfeld = model._meta.get_field(spanne["quelle"])
                    self.assertIn(spanne["quelle"], gruppierte)
                    # Wert- und Basisfeld liegen im verknüpften Modell
                    quellfeld.related_model._meta.get_field(spanne["wertfeld"])
                    quellfeld.related_model._meta.get_field(spanne["basisfeld"])
                self.assertEqual(len(gruppierte), len(set(gruppierte)))

    def test_spezifikation_auf_leerem_bestand(self):
        # Ohne Datensätze hat kein Feld Filterwirkung; das darf nicht scheitern.
        for model, config in ALLE_KONFIGURATIONEN:
            with self.subTest(model=model.__name__):
                spezifikation = filterspezifikation_erstellen(
                    model, config, model.objects.none()
                )
                self.assertEqual(spezifikation["felder"], [])
                self.assertEqual(spezifikation["gruppen"], [])

    def test_hauptsanktion_und_vollzug_nicht_in_primaer(self):
        for model, config in ALLE_KONFIGURATIONEN:
            with self.subTest(model=model.__name__):
                primaer = config.get("primaer", [])
                self.assertNotIn("hauptsanktion", primaer)
                self.assertNotIn("vollzug", primaer)

    def test_gewaltdelikt_versuch_in_primaer(self):
        self.assertIn("versuch", GEWALTDELIKT_FILTER_CONFIG.get("primaer", []))

    def test_sexualdelikt_tatmittel_in_primaer(self):
        self.assertIn(
            "hauptdelikt_tatmittel", SEXUALDELIKT_FILTER_CONFIG.get("primaer", [])
        )


class BetmBeziehungspfadTest(TestCase):
    """BetmUrteil.betm wird über die Substanz gefiltert, nicht über den
    (durch die Menge einmaligen) Betm-Datensatz."""

    @classmethod
    def setUpTestData(cls):
        kanton = Kanton.objects.create(abk="ZH")
        rolle = Rolle.objects.create(name="Transport")
        kokain = BetmArt.objects.create(name="Kokain")
        heroin = BetmArt.objects.create(name="Heroin")
        cls.urteil = BetmUrteil.objects.create(
            fall_nr="SB240010",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 5, 5),
            kanton=kanton,
            rolle=rolle,
            freiheitsstrafe_in_monaten=30,
        )
        cls.urteil.betm.set(
            [
                Betm.objects.create(art=kokain, menge_in_g=250, rein=True),
                Betm.objects.create(art=kokain, menge_in_g=90, rein=False),
                Betm.objects.create(art=heroin, menge_in_g=40, rein=True),
            ]
        )

    def test_auswahlwerte_sind_substanzen(self):
        spezifikation = filterspezifikation_erstellen(
            BetmUrteil, BETM_FILTER_CONFIG, BetmUrteil.objects.all()
        )
        betm = next(f for f in spezifikation["felder"] if f["name"] == "betm")
        self.assertEqual(
            [option["value"] for option in betm["optionen"]], ["Heroin", "Kokain"]
        )

    def test_datensatz_fuehrt_substanzen_ohne_dubletten(self):
        spezifikation = filterspezifikation_erstellen(
            BetmUrteil, BETM_FILTER_CONFIG, BetmUrteil.objects.all()
        )
        datensaetze = datensaetze_erstellen(
            BetmUrteil, BETM_FILTER_CONFIG, BetmUrteil.objects.all(), spezifikation
        )
        # zwei Kokain-Positionen, aber nur ein Auswahlwert
        self.assertEqual(
            datensaetze[str(self.urteil.pk)]["betm"], ["Heroin", "Kokain"]
        )


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
class FilterbareAnsichtenTest(TestCase):
    """Alle vier Datenbankansichten liefern Spezifikation und Datensätze."""

    @classmethod
    def setUpTestData(cls):
        cls.kanton = Kanton.objects.create(abk="ZH")
        for name in (
            "vollzug_scatterplot_200000",
            "vollzug_scatterplot_1000000",
            "hauptdelikt_scatterplot_200000",
            "hauptdelikt_scatterplot_1000000",
        ):
            DiagrammSVG.objects.create(name=name, file="diagramme/platzhalter.svg")

    def ansicht_pruefen(self, pfad, objekt):
        antwort = self.client.get(pfad)
        self.assertEqual(antwort.status_code, 200)
        self.assertIn("filter_spec", antwort.context)
        self.assertIn(str(objekt.pk), antwort.context["filter_records"])
        self.assertContains(antwort, 'id="filter-records"')
        self.assertContains(antwort, f'data-pk="{objekt.pk}"')
        self.assertContains(antwort, "data-urteilsliste")
        return antwort

    def test_vermoegensdelikte(self):
        urteil = Urteil.objects.create(
            fall_nr="SB240020",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 2, 2),
            deliktssumme=15000,
        )
        self.ansicht_pruefen("/database", urteil)

    def test_betaeubungsmittel(self):
        urteil = BetmUrteil.objects.create(
            fall_nr="SB240021",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 2, 2),
            kanton=self.kanton,
            rolle=Rolle.objects.create(name="Transport"),
        )
        urteil.betm.set(
            [Betm.objects.create(art=BetmArt.objects.create(name="Kokain"), menge_in_g=50)]
        )
        self.ansicht_pruefen("/betmdatabase", urteil)

    def test_gewaltdelikte(self):
        urteil = GewaltdeliktUrteil.objects.create(
            fall_nr="SB240022",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 2, 2),
            kanton=self.kanton,
            hauptdelikt="Raub",
            hauptsanktion="0",
            freiheitsstrafe_in_monaten=36,
            vollzug="2",
            kurzsachverhalt="Überfall auf eine Tankstelle mit vorgehaltener Schusswaffe.",
        )
        antwort = self.ansicht_pruefen("/gewaltdatabase", urteil)
        # Volltext-Suche in filter_records soll kurzsachverhalt enthalten
        records = antwort.context["filter_records"]
        self.assertIn("tankstelle", records[str(urteil.pk)]["_t"])
        # HTML soll data-kurzsachverhalt und SV-Badge enthalten
        self.assertContains(antwort, 'data-kurzsachverhalt="Überfall auf eine Tankstelle mit vorgehaltener Schusswaffe."')
        self.assertContains(antwort, 'title="Kurzsachverhalt vorhanden (Hover für Vorschau)"')
        # Sanktion und Vollzug-Badge sowie Vollzug-Sortierung
        self.assertContains(antwort, "Freiheitsstrafe")
        self.assertContains(antwort, "unbedingt")
        self.assertContains(antwort, "sortieren('vollzug')")
        # Detailansicht soll Kurzsachverhalt anzeigen
        detail_antwort = self.client.get(reverse("gewalturteil_detail", kwargs={"pk": urteil.pk}))
        self.assertEqual(detail_antwort.status_code, 200)
        self.assertContains(detail_antwort, "Kurzsachverhalt")
        self.assertContains(detail_antwort, "Überfall auf eine Tankstelle mit vorgehaltener Schusswaffe.")

    def test_gewaltdelikte_fahrlaessige_koerperverletzung(self):
        urteil = GewaltdeliktUrteil.objects.create(
            fall_nr="SB240099",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 3, 1),
            kanton=self.kanton,
            hauptdelikt="fahrlässige Körperverletzung",
            tatmittel="Fahrzeug/Motorfahrzeug",
            vorsatzform="fahrlaessig",
            verletzungsfolge="schwer",
            kurzsachverhalt="Kollision mit Fussgänger beim Abbiegen.",
        )
        urteil.full_clean()
        antwort = self.ansicht_pruefen("/gewaltdatabase", urteil)
        self.assertContains(antwort, "fahrlässige Körperverletzung (Art. 125 StGB)")
        self.assertContains(antwort, "Fahrzeug/Motorfahrzeug")
        detail_antwort = self.client.get(reverse("gewalturteil_detail", kwargs={"pk": urteil.pk}))
        self.assertEqual(detail_antwort.status_code, 200)
        self.assertContains(detail_antwort, "fahrlässige Körperverletzung (Art. 125 StGB)")
        self.assertContains(detail_antwort, "Fahrzeug/Motorfahrzeug")

    def test_sexualdelikte(self):
        urteil = SexualdeliktUrteil.objects.create(
            fall_nr="SB240023",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 2, 2),
            kanton=self.kanton,
            hauptdelikt=Hauptdelikt.objects.create(name="Art. 190, Vergewaltigung"),
            hauptdelikt_tatmittel=Tatmittel.objects.create(name="Gewalt"),
            hauptsanktion="0",
            freiheitsstrafe_in_monaten=36,
            vollzug="2",
            kurzsachverhalt="Test-Kurzsachverhalt für Sexualdelikt unter Anwendung von körperlicher Gewalt.",
        )
        antwort = self.ansicht_pruefen("/sexualdatabase", urteil)
        records = antwort.context["filter_records"]
        self.assertIn("körperlicher", records[str(urteil.pk)]["_t"])
        self.assertContains(antwort, 'data-kurzsachverhalt="Test-Kurzsachverhalt für Sexualdelikt unter Anwendung von körperlicher Gewalt."')
        self.assertContains(antwort, 'title="Kurzsachverhalt vorhanden (Hover für Vorschau)"')
        # Sanktion und Vollzug-Badge sowie Vollzug-Sortierung
        self.assertContains(antwort, "Freiheitsstrafe")
        self.assertContains(antwort, "unbedingt")
        self.assertContains(antwort, "sortieren('vollzug')")
        detail_antwort = self.client.get(reverse("sexualurteil_detail", kwargs={"pk": urteil.pk}))
        self.assertEqual(detail_antwort.status_code, 200)
        self.assertContains(detail_antwort, "Kurzsachverhalt")
        self.assertContains(detail_antwort, "Test-Kurzsachverhalt für Sexualdelikt unter Anwendung von körperlicher Gewalt.")


class MengenspanneTest(TestCase):
    """
    Abhängige Mengenspanne der Betäubungsmittel-Urteile: Summen je Substanz,
    getrennt nach reiner Wirkstoff- und Bruttomenge.
    """

    @classmethod
    def setUpTestData(cls):
        kanton = Kanton.objects.create(abk="ZH")
        rolle = Rolle.objects.create(name="Transport")
        kokain = BetmArt.objects.create(name="Kokain")
        heroin = BetmArt.objects.create(name="Heroin")
        cls.urteil = BetmUrteil.objects.create(
            fall_nr="SB240030",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 6, 6),
            kanton=kanton,
            rolle=rolle,
        )
        cls.urteil.betm.set(
            [
                Betm.objects.create(art=kokain, menge_in_g=250, rein=True),
                Betm.objects.create(art=kokain, menge_in_g=90, rein=True),
                Betm.objects.create(art=kokain, menge_in_g=400, rein=False),
                Betm.objects.create(art=heroin, menge_in_g=40, rein=True),
            ]
        )
        # zweites Urteil, damit betm mehr als einen Auswahlwert hat
        cls.zweites = BetmUrteil.objects.create(
            fall_nr="SB240031",
            gericht="Bezirksgericht Uster",
            urteilsdatum=date(2024, 7, 7),
            kanton=kanton,
            rolle=rolle,
        )
        cls.zweites.betm.set(
            [Betm.objects.create(art=heroin, menge_in_g=1200, rein=False)]
        )

    def spezifikation(self):
        return filterspezifikation_erstellen(
            BetmUrteil, BETM_FILTER_CONFIG, BetmUrteil.objects.all()
        )

    def datensaetze(self):
        spezifikation = self.spezifikation()
        return datensaetze_erstellen(
            BetmUrteil, BETM_FILTER_CONFIG, BetmUrteil.objects.all(), spezifikation
        )

    def test_spezifikationseintrag(self):
        feld = next(
            f for f in self.spezifikation()["felder"] if f["name"] == "betm_menge"
        )
        self.assertEqual(feld["typ"], "abhaengige_spanne")
        self.assertEqual(feld["quelle"], "betm")
        self.assertEqual(feld["basis_labels"], ["rein", "Gemisch"])
        self.assertEqual(feld["einheit"], "g")
        self.assertEqual(feld["einheiten_je_schluessel"]["LSD Trips"], "Stk.")

    def test_summen_je_substanz_und_grundlage(self):
        mengen = self.datensaetze()[str(self.urteil.pk)]["betm_menge"]
        # 250 + 90 rein, 400 gemisch - nie über die Grundlage hinweg addiert
        self.assertEqual(mengen["Kokain"], {"rein": 340, "gemisch": 400})
        self.assertEqual(mengen["Heroin"], {"rein": 40})

    def test_spanne_entfaellt_ohne_bedienbares_quellfeld(self):
        # Ein M2M-Feld mit einem einzigen Wert bleibt bedienbar ("hat Heroin /
        # hat nicht"); erst ohne jede Position verliert betm die Filterwirkung -
        # und mit ihm die daran hängende Mengenspanne, die sonst ins Leere liefe.
        namen = [feld["name"] for feld in self.spezifikation()["felder"]]
        self.assertIn("betm_menge", namen)

        for urteil in BetmUrteil.objects.all():
            urteil.betm.clear()
        namen = [feld["name"] for feld in self.spezifikation()["felder"]]
        self.assertNotIn("betm", namen)
        self.assertNotIn("betm_menge", namen)


class NurHauptdeliktTest(TestCase):
    """
    Abgeleitetes Feld "nur Hauptdelikt": bestimmt allein das Hauptdelikt die
    Strafe? Ein nicht erfasster Deliktsscore ist dabei keine Null.
    """

    @classmethod
    def setUpTestData(cls):
        cls.kanton = Kanton.objects.create(abk="ZH")
        cls.hauptdelikt = Hauptdelikt.objects.create(name="Art. 190, Vergewaltigung")
        cls.tatmittel = Tatmittel.objects.create(name="Gewalt")
        cls.weiteres = ZusaetzlicheSexualdelikte.objects.create(
            name="Art. 189, sexuelle Nötigung"
        )

    def sexualurteil(self, fall_nr, score, zusaetzliche=()):
        urteil = SexualdeliktUrteil.objects.create(
            fall_nr=fall_nr,
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 1, 1),
            kanton=self.kanton,
            hauptdelikt=self.hauptdelikt,
            hauptdelikt_tatmittel=self.tatmittel,
            deliktsscore_uebrige_delikte=score,
        )
        urteil.sexualdelikte_zusaetzliche.set(zusaetzliche)
        return urteil

    def werte(self, model, config, queryset):
        spezifikation = filterspezifikation_erstellen(model, config, queryset)
        datensaetze = datensaetze_erstellen(
            model, config, queryset, spezifikation
        )
        return {
            fall: datensaetze[str(pk)]["nur_hauptdelikt"]
            for pk, fall in queryset.values_list("pk", "fall_nr")
        }

    def test_sexualdelikt_dreiwertig(self):
        self.sexualurteil("A-ja", 0)
        self.sexualurteil("B-score", 3)
        self.sexualurteil("C-weiteres", 0, [self.weiteres])
        self.sexualurteil("D-unerfasst", None)
        # nicht erfasster Score, aber weiteres Sexualdelikt: eindeutig nein
        self.sexualurteil("E-null-weit", None, [self.weiteres])

        werte = self.werte(
            SexualdeliktUrteil,
            SEXUALDELIKT_FILTER_CONFIG,
            SexualdeliktUrteil.objects.prefetch_related("sexualdelikte_zusaetzliche"),
        )
        self.assertEqual(werte["A-ja"], "ja")
        self.assertEqual(werte["B-score"], "nein")
        self.assertEqual(werte["C-weiteres"], "nein")
        self.assertEqual(werte["D-unerfasst"], "nicht erfasst")
        self.assertEqual(werte["E-null-weit"], "nein")

    def test_vermoegensdelikt_zweiwertig(self):
        Urteil.objects.create(
            fall_nr="V-ja",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 1, 1),
            deliktssumme=1000,
            nebenverurteilungsscore=0,
        )
        Urteil.objects.create(
            fall_nr="V-nein",
            gericht="Bezirksgericht Zürich",
            urteilsdatum=date(2024, 1, 1),
            deliktssumme=2000,
            nebenverurteilungsscore=2,
        )
        werte = self.werte(Urteil, URTEIL_FILTER_CONFIG, Urteil.objects.all())
        self.assertEqual(werte, {"V-ja": "ja", "V-nein": "nein"})

    def test_nur_vorkommende_auswahlwerte(self):
        # Ohne "nicht erfasst" im Bestand erscheint die Option auch nicht.
        self.sexualurteil("A-ja", 0)
        self.sexualurteil("B-nein", 3)
        spezifikation = filterspezifikation_erstellen(
            SexualdeliktUrteil,
            SEXUALDELIKT_FILTER_CONFIG,
            SexualdeliktUrteil.objects.prefetch_related("sexualdelikte_zusaetzliche"),
        )
        feld = next(
            f for f in spezifikation["felder"] if f["name"] == "nur_hauptdelikt"
        )
        self.assertEqual(
            [option["value"] for option in feld["optionen"]], ["ja", "nein"]
        )
        self.assertTrue(feld["inline"])
