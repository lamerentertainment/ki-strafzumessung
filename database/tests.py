from datetime import date, timedelta

from django.test import TestCase, override_settings

from .filterspec import (
    SEXUALDELIKT_FILTER_CONFIG,
    datensaetze_erstellen,
    filterspezifikation_erstellen,
)
from .models import (
    Besonderheiten,
    Hauptdelikt,
    Kanton,
    SexualdeliktUrteil,
    Tatmittel,
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
