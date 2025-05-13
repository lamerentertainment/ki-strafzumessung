import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.core.files.base import ContentFile
from .models import Urteil, BetmUrteil, BetmArt, KIModelPickleFile, DiagrammSVG
from .forms import (
    UrteilModelForm,
    UrteilsEckpunkteAbfrageFormular,
    CeteribusParibusFormular,
    BetmUrteilsEckpunkteAbfrageFormular,
)
from django.views import generic
from django.urls import reverse_lazy
from .ai_utils import (
    formulareingaben_in_abfragesample_konvertieren,
    y_und_x_erstellen,
    preprocessing_x,
    knn_pipeline,
    introspection_plot_und_lesehinweis_ausgeben,
    kimodelle_neu_kalibrieren_und_abspeichern,
    sortierte_koeff_list_erstellen,
    vermoegensstrafrechts_urteile_codes_aufloesen,
    introspection_plot_und_lesehinweis_abspeichern,
    betmurteile_onehotencoding,
    betmurteile_zusammenfuegen,
    betmurteile_fehlende_werte_auffuellen,
    betm_nachbarobjekt_mit_sanktionsbewertung_anreichern,
    onehotx_und_y_erstellen_from_dataframe,
    merkmalswichtigkeitslistegenerator,
    merkmale_in_merkmalswichtigkeitsliste_zusammenfassen,
    betm_urteile_dataframe_erzeugen,
    nachbar_mit_sanktionsbewertung_anreichern,
)
from .db_utils import (
    kategorie_scatterplot_erstellen,
)
from .aws_helpers import (
    kimodell_von_pickle_file_aus_aws_bucket_laden,
    ki_modell_als_pickle_file_speichern,
)
import pickle
from sklearn.model_selection import cross_val_score


def homepage(request):
    context = {}
    return render(request, "database/homepage.html", context)


# Database Views
def database(request):
    vollzug_scatterplot_1000000 = DiagrammSVG.objects.get(
        name="vollzug_scatterplot_1000000"
    )
    vollzug_scatterplot_200000 = DiagrammSVG.objects.get(
        name="vollzug_scatterplot_200000"
    )
    hauptdelikt_scatterplot_1000000 = DiagrammSVG.objects.get(
        name="hauptdelikt_scatterplot_1000000"
    )
    hauptdelikt_scatterplot_200000 = DiagrammSVG.objects.get(
        name="hauptdelikt_scatterplot_200000"
    )

    context = {
        "urteile": Urteil.objects.all(),
        "vollzug_scatterplot_200000": vollzug_scatterplot_200000,
        "vollzug_scatterplot_1000000": vollzug_scatterplot_1000000,
        "hauptdelikt_scatterplot_200000": hauptdelikt_scatterplot_200000,
        "hauptdelikt_scatterplot_1000000": hauptdelikt_scatterplot_1000000,
    }
    return render(request, "database/database.html", context)


def ws_db_scatterplots_aktualisieren(request):
    datenbank_scatterplots_aktualisieren()
    messages.success(
        request,
        "Die Datenbank Scatterplots für Wirtschafsdelikte wurden erfolgreich neu erstellt",
    )
    return redirect("dev")


class UrteilErstellenView(LoginRequiredMixin, generic.CreateView):
    model = Urteil
    form_class = UrteilModelForm
    success_url = reverse_lazy("database")
    template_name_suffix = "_erstellen"
    extra_context = {"urteile": Urteil.objects.all()}


class UrteilUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Urteil
    fields = "__all__"
    success_url = reverse_lazy("database")
    template_name_suffix = "_update"


class BetmUrteilListView(ListView):
    model = BetmUrteil
    context_object_name = "betm_urteile"
    template_name = "database/betmurteil_list.html"


class BetmUrteilDetailView(DetailView):
    model = BetmUrteil
    template_name = "database/betmurteil_detail.html"


# KI-Model Views:
def ws_evaluation(request):
    if request.method == "POST":
        form = CeteribusParibusFormular(request.POST)

        if form.is_valid():
            # strafhöhe-ki-modell
            loaded_model = pickle.load(open("database/ai-model/model.pkl", "rb"))
            y, x = y_und_x_erstellen(urteil_model=Urteil, zielwert="hoehe_strafe")
            x = preprocessing_x(x)
            scores1 = -1 * cross_val_score(
                loaded_model, x, y, cv=5, scoring="neg_mean_absolute_error"
            )

            # strafhöhe-ki-modell features wichtigkeitsliste erstellen
            zip_liste_mit_feauture_wichtigkeit_tuples = list(
                zip(loaded_model.feature_names_in_, loaded_model.feature_importances_)
            )
            sortierte_feature_wichtigkeit_tuple_liste = sorted(
                zip_liste_mit_feauture_wichtigkeit_tuples,
                key=lambda tup: tup[1],
                reverse=True,
            )
            sortierte_feature_wichtigkeit_tuple_liste_in_prozenten = [
                (tup[0], tup[1] * 100)
                for tup in sortierte_feature_wichtigkeit_tuple_liste
            ]

            # vollzugs-ki-modell features wichtigkeitsliste erstellen
            loaded_vollzugsmodel = pickle.load(
                open("database/ai-model/model2.pkl", "rb")
            )
            zip_liste_mit_feauture_wichtigkeit_tuples_vollzugsmodel = list(
                zip(
                    loaded_vollzugsmodel.feature_names_in_,
                    loaded_vollzugsmodel.feature_importances_,
                )
            )
            sortierte_feature_wichtigkeit_tuple_liste_vollzugsmodel = sorted(
                zip_liste_mit_feauture_wichtigkeit_tuples_vollzugsmodel,
                key=lambda tup: tup[1],
                reverse=True,
            )
            sortierte_feature_wichtigkeit_tuple_liste_in_prozenten_vollzugsmodel = [
                (tup[0], tup[1] * 100)
                for tup in sortierte_feature_wichtigkeit_tuple_liste_vollzugsmodel
            ]

            # introspection plot
            (
                introspection_plot,
                lesehinweis,
            ) = introspection_plot_und_lesehinweis_ausgeben(
                Urteil,
                xlim=200000,
                titel="Prognose (Deliktssumme bis Fr. 200'000)",
                cleaned_data_dict=form.cleaned_data,
            )
            (
                introspection_plot2,
                lesehinweis2,
            ) = introspection_plot_und_lesehinweis_ausgeben(
                Urteil,
                xlim=1000000,
                titel="Prognose (Deliktssumme bis Fr. 1'000'000)",
                cleaned_data_dict=form.cleaned_data,
            )

            # kontext füllen
            context = {
                "mae": scores1,
                "durchschnittliche_fehlerquote": round(sum(scores1) / 5, 2),
                "zip": sortierte_feature_wichtigkeit_tuple_liste_in_prozenten,
                "zip_vollzugsmodel": sortierte_feature_wichtigkeit_tuple_liste_in_prozenten_vollzugsmodel,
                "introspection_plot": introspection_plot,
                "introspection_plot2": introspection_plot2,
                "lesehinweis": lesehinweis,
                "form": form,
            }
            return render(request, "database/ws_evaluation.html", context)

    else:
        # kimodelle mit nur validen features laden
        val_rf_kimodel = KIModelPickleFile.objects.get(name="rf_regr_val")
        val_rf_clf_kimodel_vollzugsart = KIModelPickleFile.objects.get(
            name="rf_clf_val"
        )
        val_rf_clf_kimodel_sanktionsart = KIModelPickleFile.objects.get(
            name="rf_clf_sanktionsart_val"
        )

        # Urteile mit bester und schlechtester Prognoseleistung laden, um im template darauf verlinken zu können
        konformes_urteil = Urteil.objects.get(
            fall_nr=val_rf_kimodel.prognoseleistung_dict[
                "beste_prognoseleistung_urteil"
            ]
        )
        unkonformes_urteil = Urteil.objects.get(
            fall_nr=val_rf_kimodel.prognoseleistung_dict[
                "schlechteste_prognoseleistung_urteil"
            ]
        )

        # kimodelle mit allen features laden
        all_rf_kimodel = KIModelPickleFile.objects.get(name="rf_regr_all")
        lr_kimodel = KIModelPickleFile.objects.get(name="lr_regr_all")

        introspection_plot = DiagrammSVG.objects.get(name="introspection_plot")

        # kontext füllen
        context = {
            "val_rf_kimodel": val_rf_kimodel,
            "val_rf_clf_kimodel_vollzugsart": val_rf_clf_kimodel_vollzugsart,
            "val_rf_clf_kimodel_sanktionsart": val_rf_clf_kimodel_sanktionsart,
            "all_rf_kimodel": all_rf_kimodel,
            "introspection_plot": introspection_plot,
            "konformes_urteil": konformes_urteil,
            "unkonformes_urteil": unkonformes_urteil,
        }

    return render(request, "database/ws_evaluation.html", context)


# Prognose Views:
def prognose(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = UrteilsEckpunkteAbfrageFormular(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            sample_pandas_dataframe = formulareingaben_in_abfragesample_konvertieren(
                form.cleaned_data
            )

            # give prediction response Strafmass
            strafmass_model = kimodell_von_pickle_file_aus_aws_bucket_laden(
                "pickles/random_forest_regressor_val_fts.pkl"
            )
            vorhersage_strafmass = strafmass_model.predict(sample_pandas_dataframe)

            # give prediction response Vollzug
            vollzugs_model = kimodell_von_pickle_file_aus_aws_bucket_laden(
                "pickles/random_forest_classifier_val_fts.pkl"
            )
            vorhersage_vollzug = vollzugs_model.predict(sample_pandas_dataframe)

            # give prediction response Sanktionsart
            sanktionsart_model = kimodell_von_pickle_file_aus_aws_bucket_laden(
                "pickles/rf_classifier_fuer_sanktionsart_val_fts.pkl"
            )
            vorhersage_sanktionsart = sanktionsart_model.predict(
                sample_pandas_dataframe
            )

            vollzugsstring = "empty"

            if vorhersage_vollzug[0] == "0":
                vollzugsstring = "bedingte"
            elif vorhersage_vollzug[0] == "1":
                vollzugsstring = "teilbedingte"
            elif vorhersage_vollzug[0] == "2":
                vollzugsstring = "unbedingte"

            string_sanktionsart = "empty"

            if vorhersage_sanktionsart[0] == "0":
                string_sanktionsart = "Freiheitsstrafe"
            elif vorhersage_sanktionsart[0] == "1":
                string_sanktionsart = "Geldstrafe"
            elif vorhersage_sanktionsart[0] == "2":
                string_sanktionsart = "Busse"

            # knn model errechnen
            x_train_df = Urteil.pandas.return_as_df(
                "deliktssumme",
                "nebenverurteilungsscore",
                "gewerbsmaessig",
                "vorbestraft",
                "vorbestraft_einschlaegig",
                "hauptdelikt",
                exclude_unmarked=True,
            )
            y_train_df = Urteil.pandas.return_y_zielwerte(exclude_unmarked=True)

            deliktssumme = form.cleaned_data["deliktssumme"]
            nebenverurteilungsscore = form.cleaned_data["nebenverurteilungsscore"]
            hauptdelikt = form.cleaned_data["hauptdelikt"]
            gewerbsmaessig = form.cleaned_data["gewerbsmaessig"]
            vorbestraft = form.cleaned_data["vorbestraft"]
            vorbestraft_einschlaegig = form.cleaned_data["vorbestraft_einschlaegig"]

            urteil_features_list = [
                gewerbsmaessig,
                hauptdelikt,
                vorbestraft_einschlaegig,
                vorbestraft,
                deliktssumme,
                nebenverurteilungsscore,
            ]
            urteil_features_series = pd.Series(urteil_features_list)

            nachbar_pk, nachbar_pk2, knn_prediction, nachbar_pks, distances, last_neighbor_distance = knn_pipeline(
                x_train_df, y_train_df, urteil_features_series
            )

            nachbar = Urteil.objects.get(pk=nachbar_pk)
            nachbar2 = Urteil.objects.get(pk=nachbar_pk2)

            # Get the next two neighbors if available
            if len(nachbar_pks) > 2:
                nachbar3 = Urteil.objects.get(pk=nachbar_pks[2])
                if len(nachbar_pks) > 3:
                    nachbar4 = Urteil.objects.get(pk=nachbar_pks[3])
                else:
                    nachbar4 = None
            else:
                nachbar3 = None
                nachbar4 = None

            # differenzen von eingabe und nachbarn berechnen, evt. mal auslagern
            def differenzengenerator(nachbarobjekt, formobjekt, index=None):
                """legt im Nachbarobjekt die Differenzen zu den Formulareingaben als Attribute ab"""
                nachbarobjekt.ds_diff = (
                    nachbarobjekt.deliktssumme - form.cleaned_data["deliktssumme"]
                )
                nachbarobjekt.nvs_diff = (
                    nachbarobjekt.nebenverurteilungsscore
                    - form.cleaned_data["nebenverurteilungsscore"]
                )
                nachbarobjekt.entsprechung_hauptdelikt = (
                    True
                    if nachbarobjekt.hauptdelikt == form.cleaned_data["hauptdelikt"]
                    else False
                )
                nachbarobjekt.entsprechung_gewerbsmaessig = (
                    True
                    if nachbarobjekt.gewerbsmaessig
                    == form.cleaned_data["gewerbsmaessig"]
                    else False
                )
                nachbarobjekt.entsprechung_vorbestraft_einschlaegig = (
                    True
                    if nachbarobjekt.vorbestraft_einschlaegig
                    == form.cleaned_data["vorbestraft_einschlaegig"]
                    else False
                )
                nachbarobjekt.zusammenfassung = nachbarobjekt.zusammenfassung

                # Vergleichbarkeitsscore berechnen, wenn index vorhanden
                if index is not None and len(distances) > 0:
                    # Distanz des aktuellen Nachbarn
                    current_distance = distances[index]
                    # Distanz des am weitesten entfernten Nachbarn
                    max_distance = last_neighbor_distance[0]
                    # Vergleichbarkeitsscore: 1 - (aktuelle Distanz / maximale Distanz)
                    # Ein Wert von 1 bedeutet perfekte Übereinstimmung, 0 bedeutet maximale Distanz
                    if max_distance > 0:  # Vermeidung von Division durch Null
                        nachbarobjekt.vergleichbarkeitsscore = round((1 - current_distance/(max_distance/100)) * 100)
                    else:
                        nachbarobjekt.vergleichbarkeitsscore = 100  # Wenn alle Distanzen 0 sind

                return nachbarobjekt

            nachbar = differenzengenerator(nachbar, form, 0)
            nachbar2 = differenzengenerator(nachbar2, form, 1)

            # Apply differenzengenerator to nachbar3 and nachbar4 if they exist
            if nachbar3:
                nachbar3 = differenzengenerator(nachbar3, form, 2)
            if nachbar4:
                nachbar4 = differenzengenerator(nachbar4, form, 3)

            nachbar = nachbar_mit_sanktionsbewertung_anreichern(
                nachbar,
                strafmass_estimator=strafmass_model,
                hauptsanktion_estimator=sanktionsart_model,
                vollzug_estimator=vollzugs_model,
            )
            nachbar2 = nachbar_mit_sanktionsbewertung_anreichern(
                nachbar2,
                strafmass_estimator=strafmass_model,
                hauptsanktion_estimator=sanktionsart_model,
                vollzug_estimator=vollzugs_model,
            )

            # Apply nachbar_mit_sanktionsbewertung_anreichern to nachbar3 and nachbar4 if they exist
            if nachbar3:
                nachbar3 = nachbar_mit_sanktionsbewertung_anreichern(
                    nachbar3,
                    strafmass_estimator=strafmass_model,
                    hauptsanktion_estimator=sanktionsart_model,
                    vollzug_estimator=vollzugs_model,
                )
            if nachbar4:
                nachbar4 = nachbar_mit_sanktionsbewertung_anreichern(
                    nachbar4,
                    strafmass_estimator=strafmass_model,
                    hauptsanktion_estimator=sanktionsart_model,
                    vollzug_estimator=vollzugs_model,
                )

            return render(
                request,
                "database/prognose.html",
                {
                    "form": form,
                    "display_eingabeformular_button": "d-inline-flex",
                    "eingabeformular_anzeigen": "",
                    "vorhersage_strafmass": vorhersage_strafmass[0],
                    "vorhersage_vollzug": vollzugsstring,
                    "vorhersage_sanktionsart": string_sanktionsart,
                    "knn_prediction": knn_prediction,
                    "nachbar": nachbar,
                    "nachbar2": nachbar2,
                    "nachbar3": nachbar3,
                    "nachbar4": nachbar4,
                    "has_more_nachbarn": nachbar3 is not None,
                },
            )

    # if a GET (or any other method) we'll create a blank form
    else:
        form = UrteilsEckpunkteAbfrageFormular()

    context = {
        "form": form,
        "display_eingabeformular_button": "d-none",
        "eingabeformular_anzeigen": "show"
    }

    return render(request, "database/prognose.html", context=context)


def betm_prognose(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = BetmUrteilsEckpunkteAbfrageFormular(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            allgemeine_prognosemerkmale = {
                "fall_nr": "neuer Fall",
                "mengenmaessig": form.cleaned_data["mengenmaessig"],
                "bandenmaessig": form.cleaned_data["bandenmaessig"],
                "gewerbsmaessig": form.cleaned_data["gewerbsmaessig"],
                "anstaltentreffen": form.cleaned_data["anstaltentreffen"],
                "mehrfach": form.cleaned_data["mehrfach"],
                "beschaffungskriminalitaet": form.cleaned_data[
                    "beschaffungskriminalitaet"
                ],
                "deliktsdauer_in_monaten": form.cleaned_data["deliktsdauer_in_monaten"],
                "nebenverurteilungsscore": form.cleaned_data["nebenverurteilungsscore"],
                "vorbestraft": form.cleaned_data["vorbestraft"],
                "vorbestraft_einschlaegig": form.cleaned_data[
                    "vorbestraft_einschlaegig"
                ],
                "deliktsertrag": form.cleaned_data["deliktsertrag"],
                "rolle": form.cleaned_data["rolle"],
            }

            # wenn die typen nicht string gibt, gibt es später probleme beim groupby agg
            def _convert_django_types_to_string(dict_):
                for key, value in dict_.items():
                    if value is not None and not isinstance(
                        value, (bool, float, str, int)
                    ):
                        dict_[key] = value.name
                return dict_

            allgemeine_prognosemerkmale = _convert_django_types_to_string(
                allgemeine_prognosemerkmale
            )

            betm_1 = {
                "betm_art": form.cleaned_data["betm1"],
                "menge_in_g": form.cleaned_data["betm1_menge"],
                "rein": form.cleaned_data["betm1_rein"],
            }
            betm_2 = {
                "betm_art": form.cleaned_data["betm2"],
                "menge_in_g": form.cleaned_data["betm2_menge"],
                "rein": form.cleaned_data["betm2_rein"],
            }
            betm_3 = {
                "betm_art": form.cleaned_data["betm3"],
                "menge_in_g": form.cleaned_data["betm3_menge"],
                "rein": form.cleaned_data["betm3_rein"],
            }

            betm_1 = _convert_django_types_to_string(betm_1)
            betm_2 = _convert_django_types_to_string(betm_2)
            betm_3 = _convert_django_types_to_string(betm_3)

            list_betm = [betm_1, betm_2, betm_3]
            urteilszeilen = dict()
            for i, dict_betm in enumerate(list_betm):
                prognosemerkmale = allgemeine_prognosemerkmale.copy()
                prognosemerkmale.update(dict_betm)
                urteilszeilen[i] = prognosemerkmale

            liste_mit_urteilszeilen = [value for value in urteilszeilen.values()]
            pd_df_mit_prognosewerten = pd.DataFrame(liste_mit_urteilszeilen)

            # damit alle spalten für ohe-betm-arten erstellt werden, musste die liste_der_betmarten
            # von der ursprünglichen pandas df genommen werden, danach in strings konvertieren
            liste_der_betmarten = list(BetmArt.objects.all())
            liste_der_betmarten_strings = [
                betmart.name for betmart in liste_der_betmarten
            ]

            df_prognosewerte_ohe, list_ohe_betm_columns = betmurteile_onehotencoding(
                pd_df_mit_prognosewerten,
                liste_der_betmarten=liste_der_betmarten_strings,
            )
            df_prognosewerte_ohe.drop(
                labels=["betm_art", "menge_in_g"], axis=1, inplace=True
            )
            df_prognosewerte_ohe_grouped = betmurteile_zusammenfuegen(
                pd_df=df_prognosewerte_ohe,
                liste_aller_ohe_betm_spalten=list_ohe_betm_columns,
            )

            # onehotencoding
            encoder = kimodell_von_pickle_file_aus_aws_bucket_laden(
                "encoders/betm_encoder.pkl"
            )
            liste_kategoriale_prognosemerkmale = KIModelPickleFile.objects.get(
                name="betm_rf_classifier_vollzugsart"
            ).prognoseleistung_dict["liste_kategoriale_prognosemerkmale"]
            liste_numerische_prognosemerkmale = KIModelPickleFile.objects.get(
                name="betm_rf_classifier_vollzugsart"
            ).prognoseleistung_dict["liste_numerische_prognosemerkmale"]

            cat_fts_onehot = encoder.transform(
                df_prognosewerte_ohe_grouped[liste_kategoriale_prognosemerkmale]
            )
            enc_cat_fts_names = encoder.get_feature_names_out(
                liste_kategoriale_prognosemerkmale
            )
            df_cat_fts = pd.DataFrame(cat_fts_onehot, columns=enc_cat_fts_names)

            df_num_fts = (
                df_prognosewerte_ohe_grouped[liste_numerische_prognosemerkmale]
                .reset_index()
                .drop(["fall_nr"], axis=1)
            )

            prognosemerkmale_df_preprocessed = pd.concat(
                [df_cat_fts, df_num_fts], axis=1
            )
            # Hauptsanktion-Prädiktor laden und Prognose machen
            hauptsanktions_modell = kimodell_von_pickle_file_aus_aws_bucket_laden(
                "pickles/betm_rf_classifier_sanktion.pkl"
            )
            vorhersage_hauptsanktion = hauptsanktions_modell.predict(
                prognosemerkmale_df_preprocessed
            )[0]

            if vorhersage_hauptsanktion == "0":
                vorhersage_hauptsanktion = "Freiheitsstrafe"
            elif vorhersage_hauptsanktion == "1":
                vorhersage_hauptsanktion = "Geldstrafe"
            elif vorhersage_hauptsanktion == "2":
                vorhersage_hauptsanktion = "Busse"

            # Vollzugs-Prädiktor laden und Prognose machen
            vollzugs_modell = kimodell_von_pickle_file_aus_aws_bucket_laden(
                "pickles/betm_rf_classifier_vollzugsart.pkl"
            )
            vorhersage_vollzug = vollzugs_modell.predict(
                prognosemerkmale_df_preprocessed
            )[0]

            if vorhersage_vollzug == "bedingt":
                vorhersage_vollzug = "bedingte"
            elif vorhersage_vollzug == "teilbedingt":
                vorhersage_vollzug = "teilbedingte"
            elif vorhersage_vollzug == "unbedingt":
                vorhersage_vollzug = "unbedingte"

            # Strafmass-Prädiktor laden und Prognose machen
            strafmass_modell = kimodell_von_pickle_file_aus_aws_bucket_laden(
                "pickles/betm_rf_regressor_strafmass.pkl"
            )
            vorhersage_strafmass = strafmass_modell.predict(
                prognosemerkmale_df_preprocessed
            )[0]

            # nearest neighbors
            df_urteile, liste_aller_ohe_betm_spalten = betm_urteile_dataframe_erzeugen()

            # Prognosemerkmale definieren, auf welche die Prädiktoren abstützen dürfen
            liste_kategoriale_prognosemerkmale = [
                "mengenmaessig",
                "bandenmaessig",
                "gewerbsmaessig",
                "anstaltentreffen",
                "mehrfach",
                "beschaffungskriminalitaet",
                "vorbestraft",
                "vorbestraft_einschlaegig",
                "rolle",
            ]
            liste_numerische_prognosemerkmale = [
                "nebenverurteilungsscore",
                "deliktsertrag",
                "deliktsdauer_in_monaten",
            ]
            liste_numerische_prognosemerkmale.extend(liste_aller_ohe_betm_spalten)

            X_ohe, y_strafmass = onehotx_und_y_erstellen_from_dataframe(
                pandas_dataframe=df_urteile,
                categorial_ft_dbfields=liste_kategoriale_prognosemerkmale,
                numerical_ft_dbfields=liste_numerische_prognosemerkmale,
                target_dbfields=["freiheitsstrafe_in_monaten"],
                return_encoder=False,
            )

            y_strafmass = (
                (df_urteile["anzahl_tagessaetze"] / 30)
                .where(
                    df_urteile["freiheitsstrafe_in_monaten"] == 0,
                    df_urteile["freiheitsstrafe_in_monaten"],
                )
                .values.ravel()
            )

            from sklearn.preprocessing import MinMaxScaler

            scaler = MinMaxScaler()
            x_onehot_scaled = scaler.fit_transform(X_ohe)
            df_X_ohe_scaled = pd.DataFrame(
                x_onehot_scaled, columns=scaler.feature_names_in_
            )

            def gewichte_dict_ausgeben(liste_mit_prognosekriterium_wichtigkeits_tuples):
                """für spätere Gewichtung der Werte bei einem späteren knn-neighbor Prädiktor"""
                gewichtungs_dict = {}
                for t in liste_mit_prognosekriterium_wichtigkeits_tuples:
                    gewichtungs_dict[t[0]] = t[1]
                return gewichtungs_dict

            prognoseleistung_dict_strafmass = KIModelPickleFile.objects.get(
                name="betm_rf_regressor_strafmass"
            ).prognoseleistung_dict

            merkmalswichtigkeit_fuer_prognose_strafmass = (
                prognoseleistung_dict_strafmass[
                    "merkmalswichtigkeit_fuer_prognose_strafmass"
                ]
            )

            gewichtungs_dict_strafmass_regressor = gewichte_dict_ausgeben(
                merkmalswichtigkeit_fuer_prognose_strafmass
            )

            def pandas_df_mit_gewichtungs_dict_gewichten(pd_df, gewichtungs_dict):
                for prognosemerkmal, gewichtung in gewichtungs_dict.items():
                    if prognosemerkmal in pd_df.columns:
                        pd_df[prognosemerkmal] = pd_df[prognosemerkmal] * gewichtung
                return pd_df

            df_x_onehot_scaled_gewichtet = pandas_df_mit_gewichtungs_dict_gewichten(
                df_X_ohe_scaled, gewichtungs_dict_strafmass_regressor
            )

            from sklearn.neighbors import KNeighborsRegressor

            neigh = KNeighborsRegressor(n_neighbors=5)
            neigh.fit(df_x_onehot_scaled_gewichtet, y_strafmass)
            prognosemerkmale_df_preprocessed_scaled = scaler.transform(
                prognosemerkmale_df_preprocessed
            )
            df_prognosemerkmale_df_preprocessed_scaled = pd.DataFrame(
                prognosemerkmale_df_preprocessed_scaled,
                columns=scaler.feature_names_in_,
            )
            df_prognosemerkmale_df_preprocessed_scaled_gewichtet = (
                pandas_df_mit_gewichtungs_dict_gewichten(
                    df_prognosemerkmale_df_preprocessed_scaled,
                    gewichtungs_dict_strafmass_regressor,
                )
            )

            # Get distances and indices
            distances, indices = neigh.kneighbors(df_prognosemerkmale_df_preprocessed_scaled_gewichtet)
            aehnlichstes_uerteile_gemaess_gewichtetem_kneighbormodell = df_urteile.iloc[
                indices[0]
            ]

            nachbarliste = (
                aehnlichstes_uerteile_gemaess_gewichtetem_kneighbormodell.index.tolist()
            )

            nachbar1 = BetmUrteil.objects.get(fall_nr=nachbarliste[0])
            nachbar2 = BetmUrteil.objects.get(fall_nr=nachbarliste[1])
            nachbar3 = BetmUrteil.objects.get(fall_nr=nachbarliste[2])
            nachbar4 = BetmUrteil.objects.get(fall_nr=nachbarliste[3])

            nachbar1 = betm_nachbarobjekt_mit_sanktionsbewertung_anreichern(
                nachbar1,
                strafmass_estimator=strafmass_modell,
                hauptsanktion_estimator=hauptsanktions_modell,
                vollzug_estimator=vollzugs_modell,
            )
            nachbar2 = betm_nachbarobjekt_mit_sanktionsbewertung_anreichern(
                nachbar2,
                strafmass_estimator=strafmass_modell,
                hauptsanktion_estimator=hauptsanktions_modell,
                vollzug_estimator=vollzugs_modell,
            )
            nachbar3 = betm_nachbarobjekt_mit_sanktionsbewertung_anreichern(
                nachbar3,
                strafmass_estimator=strafmass_modell,
                hauptsanktion_estimator=hauptsanktions_modell,
                vollzug_estimator=vollzugs_modell,
            )
            nachbar4 = betm_nachbarobjekt_mit_sanktionsbewertung_anreichern(
                nachbar4,
                strafmass_estimator=strafmass_modell,
                hauptsanktion_estimator=hauptsanktions_modell,
                vollzug_estimator=vollzugs_modell,
            )

            # differenzen von eingabe und nachbarn berechnen, evt. mal auslagern
            def differenzengenerator(nachbarobjekt, formobjekt, index=None):
                """legt im Nachbarobjekt die Differenzen zu den Formulareingaben als Attribute ab"""
                nachbarobjekt.entsprechung_rolle = (
                    True
                    if nachbarobjekt.rolle == formobjekt.cleaned_data["rolle"]
                    else False
                )
                nachbarobjekt.nvs_diff = (
                    nachbarobjekt.nebenverurteilungsscore
                    - formobjekt.cleaned_data["nebenverurteilungsscore"]
                )
                nachbarobjekt.entsprechung_mengenmaessig = (
                    True
                    if nachbarobjekt.mengenmaessig
                    == formobjekt.cleaned_data["mengenmaessig"]
                    else False
                )
                nachbarobjekt.entsprechung_gewerbsmaessig = (
                    True
                    if nachbarobjekt.gewerbsmaessig
                    == formobjekt.cleaned_data["gewerbsmaessig"]
                    else False
                )
                nachbarobjekt.entsprechung_bandenmaessig = (
                    True
                    if nachbarobjekt.bandenmaessig
                    == formobjekt.cleaned_data["bandenmaessig"]
                    else False
                )
                nachbarobjekt.entsprechung_vorbestraft_einschlaegig = (
                    True
                    if nachbarobjekt.vorbestraft_einschlaegig
                    == formobjekt.cleaned_data["vorbestraft_einschlaegig"]
                    else False
                )
                # Da deliktsdauer_in_monaten und deliktsertrag nicht zwingend ausgefüllt sein müssen, zuerst auf 0 setzen
                if nachbarobjekt.deliktsdauer_in_monaten is None:
                    nachbarobjekt.deliktsdauer_in_monaten = 0
                nachbarobjekt.deliktsdauer_diff = (
                    nachbarobjekt.deliktsdauer_in_monaten
                    - formobjekt.cleaned_data["deliktsdauer_in_monaten"]
                )
                if nachbarobjekt.deliktsertrag is None:
                    nachbarobjekt.deliktsertrag = 0
                nachbarobjekt.deliktsertrag_diff = (
                    nachbarobjekt.deliktsertrag
                    - formobjekt.cleaned_data["deliktsertrag"]
                )
                nachbarobjekt.zusammenfassung = nachbarobjekt.zusammenfassung

                # Zweiter Pass mit allen Trainingsdaten als Nachbarn, um die Distanz zum am weitesten entfernten Sample zu ermitteln
                total_samples = len(
                    df_x_onehot_scaled_gewichtet)  # Verwende die bereits transformierten und gewichteten Trainingsdaten
                all_neighbors_knn = KNeighborsRegressor(n_neighbors=total_samples)
                all_neighbors_knn.fit(df_x_onehot_scaled_gewichtet,
                                      y_strafmass)  # Diese Variablen sind bereits definiert
                all_differences, all_indexes = all_neighbors_knn.kneighbors(
                    df_prognosemerkmale_df_preprocessed_scaled_gewichtet)  # Verwende die transformierten Features der aktuellen Anfrage
                # Distanz zum am weitesten entfernten Sample im gesamten Trainingsdatensatz
                furthest_sample_distance = all_differences[:, -1][0]
                # Vergleichbarkeitsscore berechnen, wenn index vorhanden
                if index is not None and len(distances) > 0:
                    # Distanz des aktuellen Nachbarn
                    current_distance = distances[0][index]
                    # Distanz des am weitesten entfernten Nachbarn
                    max_distance = furthest_sample_distance
                    # Vergleichbarkeitsscore: 1 - (aktuelle Distanz / maximale Distanz)
                    # Ein Wert von 1 bedeutet perfekte Übereinstimmung, 0 bedeutet maximale Distanz
                    if max_distance > 0:  # Vermeidung von Division durch Null
                        nachbarobjekt.vergleichbarkeitsscore = (
                            round((1 - (current_distance / (max_distance/20))) * 100))
                    else:
                        nachbarobjekt.vergleichbarkeitsscore = 100  # Wenn alle Distanzen 0 sind

                return nachbarobjekt

            nachbar1 = differenzengenerator(nachbar1, form, 0)
            nachbar2 = differenzengenerator(nachbar2, form, 1)
            nachbar3 = differenzengenerator(nachbar3, form, 2)
            nachbar4 = differenzengenerator(nachbar4, form, 3)

            context = {
                "form": form,
                "display_eingabeformular_button": "d-inline-flex",
                "eingabeformular_anzeigen": "",
                "vorhersage_vollzug": vorhersage_vollzug,
                "vorhersage_hauptsanktion": vorhersage_hauptsanktion,
                "vorhersage_strafmass": vorhersage_strafmass,
                "nachbar1": nachbar1,
                "nachbar2": nachbar2,
                "nachbar3": nachbar3,
                "nachbar4": nachbar4,
            }

            return render(
                request,
                "database/betm_prognose.html",
                context=context,
            )

    # if a GET (or any other method) we'll create a blank form
    else:
        form = BetmUrteilsEckpunkteAbfrageFormular()

    context = {
        "form": form,
        "display_eingabeformular_button": "d-none",
        "eingabeformular_anzeigen": "show",
    }

    return render(request, "database/betm_prognose.html", context=context)


# Dev views
@login_required
def dev(request):
    # kimodelle mit nur validen features laden
    val_rf_kimodel = KIModelPickleFile.objects.get(name="rf_regr_val")
    val_rf_clf_kimodel = KIModelPickleFile.objects.get(name="rf_clf_val")

    # Urteile mit bester und schlechtester Prognoseleistung laden, um im template darauf verlinken zu können
    konformes_urteil = Urteil.objects.get(
        fall_nr=val_rf_kimodel.prognoseleistung_dict["beste_prognoseleistung_urteil"]
    )
    unkonformes_urteil = Urteil.objects.get(
        fall_nr=val_rf_kimodel.prognoseleistung_dict[
            "schlechteste_prognoseleistung_urteil"
        ]
    )

    # kimodelle mit allen features laden
    all_rf_kimodel = KIModelPickleFile.objects.get(name="rf_regr_all")
    lr_kimodel = KIModelPickleFile.objects.get(name="lr_regr_all")
    linear_regression_regressor = kimodell_von_pickle_file_aus_aws_bucket_laden(
        filepath=lr_kimodel.file.name
    )
    koeffizientenliste = sortierte_koeff_list_erstellen(linear_regression_regressor)

    introspection_plot = DiagrammSVG.objects.get(name="introspection_plot")

    context = {
        "val_rf_kimodel": val_rf_kimodel,
        "val_rf_clf_kimodel": val_rf_clf_kimodel,
        "all_rf_kimodel": all_rf_kimodel,
        "lr_kimodel": lr_kimodel,
        "koeff_liste": koeffizientenliste,
        "introspection_plot": introspection_plot,
        "unkonformes_urteil": unkonformes_urteil,
        "konformes_urteil": konformes_urteil,
    }
    return render(request, "database/dev.html", context)


@login_required
def ws_kimodelle_neu_generieren(request):
    kimodelle_neu_kalibrieren_und_abspeichern()
    introspection_plot_und_lesehinweis_abspeichern()
    messages.success(request, "Die KI-Modelle wurden erfolgreich aktualisiert.")
    messages.success(request, "Der Introspection Plot wurde erfolgreich neu erstellt")
    return redirect("dev")


@login_required
def betm_kimodelle_neu_generieren(request):
    df_urteile, liste_aller_ohe_betm_spalten = betm_urteile_dataframe_erzeugen()

    # Prognosemerkmale definieren, auf welche die Prädiktoren abstützen dürfen
    liste_kategoriale_prognosemerkmale = [
        "mengenmaessig",
        "bandenmaessig",
        "gewerbsmaessig",
        "anstaltentreffen",
        "mehrfach",
        "beschaffungskriminalitaet",
        "vorbestraft",
        "vorbestraft_einschlaegig",
        "rolle",
    ]
    liste_numerische_prognosemerkmale = [
        "nebenverurteilungsscore",
        "deliktsertrag",
        "deliktsdauer_in_monaten",
    ]
    liste_numerische_prognosemerkmale.extend(liste_aller_ohe_betm_spalten)

    X_ohe, y_vollzugsart, encoder = onehotx_und_y_erstellen_from_dataframe(
        pandas_dataframe=df_urteile,
        categorial_ft_dbfields=liste_kategoriale_prognosemerkmale,
        numerical_ft_dbfields=liste_numerische_prognosemerkmale,
        target_dbfields=["vollzug"],
        return_encoder=True,
    )
    # Classifier für HAUPTSANKTION-Prognose erstellen
    from sklearn.ensemble import RandomForestClassifier

    classifier_fuer_hauptsanktion = RandomForestClassifier(oob_score=True)
    y_hauptsanktion = df_urteile[["hauptsanktion"]].values.ravel()
    classifier_fuer_hauptsanktion.fit(X_ohe, y_hauptsanktion)

    merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
        merkmalswichtigkeitslistegenerator(classifier_fuer_hauptsanktion)
    )

    zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
        merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
            merkmalswichtigkeit_fuer_prognose_hauptsanktion,
            liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
        )
    )
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
        merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
            zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion,
            liste_mit_zusammenfassenden_merkmalen=[
                f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
            ],
            neuer_merkmalsname="Rolle",
        )
    )

    oob_score_hauptsanktion = f"OOB-Score für Hauptsanktion-Prädiktor: {round(classifier_fuer_hauptsanktion.oob_score_*100, 1)}%"

    prognoseleistung_dict_hauptsanktion = dict()
    prognoseleistung_dict_hauptsanktion[
        "oob_score_class_hauptsanktion"
    ] = oob_score_hauptsanktion
    prognoseleistung_dict_hauptsanktion[
        "merkmalswichtigkeit_fuer_prognose_hauptsanktion"
    ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion
    prognoseleistung_dict_hauptsanktion[
        "liste_kategoriale_prognosemerkmale"
    ] = liste_kategoriale_prognosemerkmale
    prognoseleistung_dict_hauptsanktion[
        "liste_numerische_prognosemerkmale"
    ] = liste_numerische_prognosemerkmale

    # kimodell als pickle file speichern
    ki_modell_als_pickle_file_speichern(
        instanziertes_kimodel=classifier_fuer_hauptsanktion,
        name="betm_rf_classifier_sanktion",
        filename="betm_rf_classifier_sanktion.pkl",
        prognoseleistung_dict=prognoseleistung_dict_hauptsanktion,
    )

    # Classifier für VOLLZUGSART-Prognose erstellen
    classifier_fuer_vollzugsart = RandomForestClassifier(oob_score=True)
    classifier_fuer_vollzugsart.fit(X_ohe, y_vollzugsart)

    merkmalswichtigkeit_fuer_prognose_vollzugsart = merkmalswichtigkeitslistegenerator(
        classifier_fuer_vollzugsart
    )

    zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart = (
        merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
            merkmalswichtigkeit_fuer_prognose_vollzugsart,
            liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
        )
    )
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart = (
        merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
            zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart,
            liste_mit_zusammenfassenden_merkmalen=[
                f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
            ],
            neuer_merkmalsname="Rolle",
        )
    )

    oob_score = f"OOB-Score für Vollzugsart-Prädiktor: {round(classifier_fuer_vollzugsart.oob_score_*100, 1)}%"

    prognoseleistung_dict = dict()
    prognoseleistung_dict["oob_score_class_vollzugsart"] = oob_score
    prognoseleistung_dict[
        "merkmalswichtigkeit_fuer_prognose_vollzugsart"
    ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart
    prognoseleistung_dict[
        "liste_kategoriale_prognosemerkmale"
    ] = liste_kategoriale_prognosemerkmale
    prognoseleistung_dict[
        "liste_numerische_prognosemerkmale"
    ] = liste_numerische_prognosemerkmale

    # kimodell als pickle file speichern
    ki_modell_als_pickle_file_speichern(
        instanziertes_kimodel=classifier_fuer_vollzugsart,
        name="betm_rf_classifier_vollzugsart",
        filename="betm_rf_classifier_vollzugsart.pkl",
        prognoseleistung_dict=prognoseleistung_dict,
    )

    # Regressor für STRAFMASS-Prognose erstellen
    y_strafmass = (
        (df_urteile["anzahl_tagessaetze"] / 30)
        .where(
            df_urteile["freiheitsstrafe_in_monaten"] == 0,
            df_urteile["freiheitsstrafe_in_monaten"],
        )
        .values.ravel()
    )

    from sklearn.ensemble import RandomForestRegressor

    regressor_fuer_strafmass = RandomForestRegressor(oob_score=True)
    regressor_fuer_strafmass.fit(X_ohe, y_strafmass)

    def durchschnittlicher_fehler_berechnen(regressor, y):
        liste_mit_zielwert_prognose_tuples = list(zip(y, regressor.oob_prediction_))
        liste_mit_fehler = []
        for t in liste_mit_zielwert_prognose_tuples:
            fehler = abs(t[0] - t[1])
            liste_mit_fehler.append(fehler)
        durchschnittswert = sum(liste_mit_fehler) / len(liste_mit_fehler)
        return durchschnittswert

    durchschnittlicher_fehler = durchschnittlicher_fehler_berechnen(
        regressor_fuer_strafmass, y_strafmass
    )
    prognoseleistung_dict_regressor = dict()
    prognoseleistung_dict_regressor[
        "durchschnittlicher_fehler"
    ] = f"Der durchnittliche Strafmassprognosefehler bei einer Prognose jeweils mit dem OOB-leftout beträgt {round(durchschnittlicher_fehler,2)} Monate."

    merkmalswichtigkeit_fuer_prognose_strafmass = merkmalswichtigkeitslistegenerator(
        regressor_fuer_strafmass
    )

    prognoseleistung_dict_regressor[
        "merkmalswichtigkeit_fuer_prognose_strafmass"
    ] = merkmalswichtigkeit_fuer_prognose_strafmass

    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
        merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
            merkmalswichtigkeit_fuer_prognose_strafmass,
            liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
        )
    )
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
        merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
            zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass,
            liste_mit_zusammenfassenden_merkmalen=[
                f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
            ],
            neuer_merkmalsname="Rolle",
        )
    )

    prognoseleistung_dict_regressor[
        "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
    ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass

    prognoseleistung_dict_regressor["urteilsbasis"] = len(y_strafmass)

    # kimodell als pickle file speichern
    ki_modell_als_pickle_file_speichern(
        instanziertes_kimodel=regressor_fuer_strafmass,
        name="betm_rf_regressor_strafmass",
        filename="betm_rf_regressor_strafmass.pkl",
        prognoseleistung_dict=prognoseleistung_dict_regressor,
    )

    # den onehotencoder für späteren transform der eingeabwerte abspeichern
    kimodell = KIModelPickleFile.objects.get(name="betm_rf_classifier_vollzugsart")
    content = pickle.dumps(encoder)
    content_file = ContentFile(content)
    kimodell.encoder.save("betm_encoder.pkl", content_file)
    content_file.close()

    messages.success(
        request, "Die KI-Modelle für Betm-Strafrecht wurden erfolgreich aktualisiert."
    )
    return redirect("betm_dev")


@login_required
def betm_evaluations_kimodelle_neu_generieren(request):
    kantone = ["ZH", "BE"]
    for kanton in kantone:
        df_urteile, liste_aller_ohe_betm_spalten = betm_urteile_dataframe_erzeugen(
            kanton_filtern=kanton
        )

        # Prognosemerkmale definieren, auf welche die Prädiktoren abstützen dürfen
        liste_kategoriale_prognosemerkmale = [
            "mengenmaessig",
            "bandenmaessig",
            "gewerbsmaessig",
            "anstaltentreffen",
            "mehrfach",
            "beschaffungskriminalitaet",
            "vorbestraft",
            "vorbestraft_einschlaegig",
            "rolle",
        ]
        liste_numerische_prognosemerkmale = [
            "nebenverurteilungsscore",
            "deliktsertrag",
            "deliktsdauer_in_monaten",
        ]
        liste_numerische_prognosemerkmale.extend(liste_aller_ohe_betm_spalten)

        X_ohe, y_vollzugsart, encoder = onehotx_und_y_erstellen_from_dataframe(
            pandas_dataframe=df_urteile,
            categorial_ft_dbfields=liste_kategoriale_prognosemerkmale,
            numerical_ft_dbfields=liste_numerische_prognosemerkmale,
            target_dbfields=["vollzug"],
            return_encoder=True,
        )
        # Classifier für HAUPTSANKTION-Prognose erstellen
        from sklearn.ensemble import RandomForestClassifier

        classifier_fuer_hauptsanktion = RandomForestClassifier(oob_score=True)
        y_hauptsanktion = df_urteile[["hauptsanktion"]].values.ravel()
        classifier_fuer_hauptsanktion.fit(X_ohe, y_hauptsanktion)

        merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
            merkmalswichtigkeitslistegenerator(classifier_fuer_hauptsanktion)
        )

        zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                merkmalswichtigkeit_fuer_prognose_hauptsanktion,
                liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
            )
        )
        zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion,
                liste_mit_zusammenfassenden_merkmalen=[
                    f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
                ],
                neuer_merkmalsname="Rolle",
            )
        )

        oob_score_hauptsanktion = f"OOB-Score für Hauptsanktion-Prädiktor: {round(classifier_fuer_hauptsanktion.oob_score_*100, 1)}%"

        prognoseleistung_dict_hauptsanktion = dict()
        prognoseleistung_dict_hauptsanktion[
            "oob_score_class_hauptsanktion"
        ] = oob_score_hauptsanktion
        prognoseleistung_dict_hauptsanktion[
            "merkmalswichtigkeit_fuer_prognose_hauptsanktion"
        ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion
        prognoseleistung_dict_hauptsanktion[
            "liste_kategoriale_prognosemerkmale"
        ] = liste_kategoriale_prognosemerkmale
        prognoseleistung_dict_hauptsanktion[
            "liste_numerische_prognosemerkmale"
        ] = liste_numerische_prognosemerkmale
        prognoseleistung_dict_hauptsanktion["anzahl_urteile"] = df_urteile.shape[0]

        # kimodell als pickle file speichern
        ki_modell_als_pickle_file_speichern(
            instanziertes_kimodel=classifier_fuer_hauptsanktion,
            name=f"betm_sanktion_nur_{kanton}",
            filename=f"betm_sanktion_nur_{kanton}.pkl",
            prognoseleistung_dict=prognoseleistung_dict_hauptsanktion,
        )

        # Classifier für VOLLZUGSART-Prognose erstellen
        classifier_fuer_vollzugsart = RandomForestClassifier(oob_score=True)
        classifier_fuer_vollzugsart.fit(X_ohe, y_vollzugsart)

        merkmalswichtigkeit_fuer_prognose_vollzugsart = (
            merkmalswichtigkeitslistegenerator(classifier_fuer_vollzugsart)
        )

        zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                merkmalswichtigkeit_fuer_prognose_vollzugsart,
                liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
            )
        )
        zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart,
                liste_mit_zusammenfassenden_merkmalen=[
                    f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
                ],
                neuer_merkmalsname="Rolle",
            )
        )

        oob_score = f"OOB-Score für Vollzugsart-Prädiktor: {round(classifier_fuer_vollzugsart.oob_score_*100, 1)}%"

        prognoseleistung_dict = dict()
        prognoseleistung_dict["oob_score_class_vollzugsart"] = oob_score
        prognoseleistung_dict[
            "merkmalswichtigkeit_fuer_prognose_vollzugsart"
        ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart
        prognoseleistung_dict[
            "liste_kategoriale_prognosemerkmale"
        ] = liste_kategoriale_prognosemerkmale
        prognoseleistung_dict[
            "liste_numerische_prognosemerkmale"
        ] = liste_numerische_prognosemerkmale
        prognoseleistung_dict_hauptsanktion["anzahl_urteile"] = df_urteile.shape[0]

        # kimodell als pickle file speichern
        ki_modell_als_pickle_file_speichern(
            instanziertes_kimodel=classifier_fuer_vollzugsart,
            name=f"betm_vollzugsart_nur_{kanton}",
            filename=f"betm_vollzugsart_nur_{kanton}.pkl",
            prognoseleistung_dict=prognoseleistung_dict,
        )

        # Regressor für STRAFMASS-Prognose erstellen
        y_strafmass = (
            (df_urteile["anzahl_tagessaetze"] / 30)
            .where(
                df_urteile["freiheitsstrafe_in_monaten"] == 0,
                df_urteile["freiheitsstrafe_in_monaten"],
            )
            .values.ravel()
        )

        from sklearn.ensemble import RandomForestRegressor

        regressor_fuer_strafmass = RandomForestRegressor(oob_score=True)
        regressor_fuer_strafmass.fit(X_ohe, y_strafmass)

        def durchschnittlicher_fehler_berechnen(regressor, y):
            liste_mit_zielwert_prognose_tuples = list(zip(y, regressor.oob_prediction_))
            liste_mit_fehler = []
            for t in liste_mit_zielwert_prognose_tuples:
                fehler = abs(t[0] - t[1])
                liste_mit_fehler.append(fehler)
            durchschnittswert = sum(liste_mit_fehler) / len(liste_mit_fehler)
            return durchschnittswert

        durchschnittlicher_fehler = durchschnittlicher_fehler_berechnen(
            regressor_fuer_strafmass, y_strafmass
        )
        prognoseleistung_dict_regressor = dict()
        prognoseleistung_dict_regressor[
            "durchschnittlicher_fehler_string"
        ] = f"Der durchnittliche Strafmassprognosefehler bei einer Prognose jeweils mit dem OOB-leftout beträgt {round(durchschnittlicher_fehler,2)} Monate."
        prognoseleistung_dict_regressor[
            "durchschnittlicher_fehler"
        ] = durchschnittlicher_fehler

        merkmalswichtigkeit_fuer_prognose_strafmass = (
            merkmalswichtigkeitslistegenerator(regressor_fuer_strafmass)
        )

        prognoseleistung_dict_regressor[
            "merkmalswichtigkeit_fuer_prognose_strafmass"
        ] = merkmalswichtigkeit_fuer_prognose_strafmass

        zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                merkmalswichtigkeit_fuer_prognose_strafmass,
                liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
            )
        )
        zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass,
                liste_mit_zusammenfassenden_merkmalen=[
                    f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
                ],
                neuer_merkmalsname="Rolle",
            )
        )

        prognoseleistung_dict_regressor[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass

        prognoseleistung_dict_regressor["urteilsbasis"] = len(y_strafmass)

        # kimodell als pickle file speichern
        ki_modell_als_pickle_file_speichern(
            instanziertes_kimodel=regressor_fuer_strafmass,
            name=f"betm_strafmass_nur_{kanton}",
            filename=f"betm_strafmass_nur_{kanton}.pkl",
            prognoseleistung_dict=prognoseleistung_dict_regressor,
        )

        # Nun alle Prädiktoren unter Beizug illegitimer Features trainieren
        liste_kategoriale_prognosemerkmale = [
            "mengenmaessig",
            "bandenmaessig",
            "gewerbsmaessig",
            "anstaltentreffen",
            "mehrfach",
            "beschaffungskriminalitaet",
            "vorbestraft",
            "vorbestraft_einschlaegig",
            "rolle",
            # illegtime
            "geschlecht",
            "nationalitaet",
            "gericht",
        ]
        liste_numerische_prognosemerkmale = [
            "nebenverurteilungsscore",
            "deliktsertrag",
            "deliktsdauer_in_monaten",
        ]
        liste_numerische_prognosemerkmale.extend(liste_aller_ohe_betm_spalten)

        X_ohe, y_vollzugsart, encoder = onehotx_und_y_erstellen_from_dataframe(
            pandas_dataframe=df_urteile,
            categorial_ft_dbfields=liste_kategoriale_prognosemerkmale,
            numerical_ft_dbfields=liste_numerische_prognosemerkmale,
            target_dbfields=["vollzug"],
            return_encoder=True,
        )
        # Classifier für HAUPTSANKTION-Prognose erstellen
        from sklearn.ensemble import RandomForestClassifier

        classifier_fuer_hauptsanktion = RandomForestClassifier(oob_score=True)
        y_hauptsanktion = df_urteile[["hauptsanktion"]].values.ravel()
        classifier_fuer_hauptsanktion.fit(X_ohe, y_hauptsanktion)

        merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
            merkmalswichtigkeitslistegenerator(classifier_fuer_hauptsanktion)
        )

        zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                merkmalswichtigkeit_fuer_prognose_hauptsanktion,
                liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
            )
        )
        zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion,
                liste_mit_zusammenfassenden_merkmalen=[
                    f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
                ],
                neuer_merkmalsname="Rolle",
            )
        )

        oob_score_hauptsanktion = f"OOB-Score für Hauptsanktion-Prädiktor: {round(classifier_fuer_hauptsanktion.oob_score_*100, 1)}%"

        prognoseleistung_dict_hauptsanktion = dict()
        prognoseleistung_dict_hauptsanktion[
            "oob_score_class_hauptsanktion"
        ] = oob_score_hauptsanktion
        prognoseleistung_dict_hauptsanktion[
            "merkmalswichtigkeit_fuer_prognose_hauptsanktion"
        ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_hauptsanktion
        prognoseleistung_dict_hauptsanktion[
            "liste_kategoriale_prognosemerkmale"
        ] = liste_kategoriale_prognosemerkmale
        prognoseleistung_dict_hauptsanktion[
            "liste_numerische_prognosemerkmale"
        ] = liste_numerische_prognosemerkmale
        prognoseleistung_dict_hauptsanktion["anzahl_urteile"] = df_urteile.shape[0]

        # kimodell als pickle file speichern
        ki_modell_als_pickle_file_speichern(
            instanziertes_kimodel=classifier_fuer_hauptsanktion,
            name=f"betm_sanktion_nur_{kanton}_illegitim",
            filename=f"betm_sanktion_nur_{kanton}_illegitim.pkl",
            prognoseleistung_dict=prognoseleistung_dict_hauptsanktion,
        )

        # Classifier für VOLLZUGSART-Prognose erstellen
        classifier_fuer_vollzugsart = RandomForestClassifier(oob_score=True)
        classifier_fuer_vollzugsart.fit(X_ohe, y_vollzugsart)

        merkmalswichtigkeit_fuer_prognose_vollzugsart = (
            merkmalswichtigkeitslistegenerator(classifier_fuer_vollzugsart)
        )

        zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                merkmalswichtigkeit_fuer_prognose_vollzugsart,
                liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
            )
        )
        zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart,
                liste_mit_zusammenfassenden_merkmalen=[
                    f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
                ],
                neuer_merkmalsname="Rolle",
            )
        )

        oob_score = f"OOB-Score für Vollzugsart-Prädiktor: {round(classifier_fuer_vollzugsart.oob_score_*100, 1)}%"

        prognoseleistung_dict = dict()
        prognoseleistung_dict["oob_score_class_vollzugsart"] = oob_score
        prognoseleistung_dict[
            "merkmalswichtigkeit_fuer_prognose_vollzugsart"
        ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_vollzugsart
        prognoseleistung_dict[
            "liste_kategoriale_prognosemerkmale"
        ] = liste_kategoriale_prognosemerkmale
        prognoseleistung_dict[
            "liste_numerische_prognosemerkmale"
        ] = liste_numerische_prognosemerkmale
        prognoseleistung_dict_hauptsanktion["anzahl_urteile"] = df_urteile.shape[0]

        # kimodell als pickle file speichern
        ki_modell_als_pickle_file_speichern(
            instanziertes_kimodel=classifier_fuer_vollzugsart,
            name=f"betm_vollzugsart_nur_{kanton}_illegitim",
            filename=f"betm_vollzugsart_nur_{kanton}_illegitim.pkl",
            prognoseleistung_dict=prognoseleistung_dict,
        )

        # Regressor für STRAFMASS-Prognose erstellen
        y_strafmass = (
            (df_urteile["anzahl_tagessaetze"] / 30)
            .where(
                df_urteile["freiheitsstrafe_in_monaten"] == 0,
                df_urteile["freiheitsstrafe_in_monaten"],
            )
            .values.ravel()
        )

        from sklearn.ensemble import RandomForestRegressor

        regressor_fuer_strafmass = RandomForestRegressor(oob_score=True)
        regressor_fuer_strafmass.fit(X_ohe, y_strafmass)

        def durchschnittlicher_fehler_berechnen(regressor, y):
            liste_mit_zielwert_prognose_tuples = list(zip(y, regressor.oob_prediction_))
            liste_mit_fehler = []
            for t in liste_mit_zielwert_prognose_tuples:
                fehler = abs(t[0] - t[1])
                liste_mit_fehler.append(fehler)
            durchschnittswert = sum(liste_mit_fehler) / len(liste_mit_fehler)
            return durchschnittswert

        durchschnittlicher_fehler = durchschnittlicher_fehler_berechnen(
            regressor_fuer_strafmass, y_strafmass
        )
        prognoseleistung_dict_regressor = dict()
        prognoseleistung_dict_regressor[
            "durchschnittlicher_fehler_string"
        ] = f"Der durchnittliche Strafmassprognosefehler bei einer Prognose jeweils mit dem OOB-leftout beträgt {round(durchschnittlicher_fehler,2)} Monate."
        prognoseleistung_dict_regressor[
            "durchschnittlicher_fehler"
        ] = durchschnittlicher_fehler

        merkmalswichtigkeit_fuer_prognose_strafmass = (
            merkmalswichtigkeitslistegenerator(regressor_fuer_strafmass)
        )

        prognoseleistung_dict_regressor[
            "merkmalswichtigkeit_fuer_prognose_strafmass"
        ] = merkmalswichtigkeit_fuer_prognose_strafmass

        zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                merkmalswichtigkeit_fuer_prognose_strafmass,
                liste_mit_zusammenfassenden_merkmalen=liste_aller_ohe_betm_spalten,
            )
        )
        zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass,
                liste_mit_zusammenfassenden_merkmalen=[
                    f"rolle_{rolle}" for rolle in df_urteile.rolle.unique()
                ],
                neuer_merkmalsname="Rolle",
            )
        )
        zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
            merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
                zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass,
                liste_mit_zusammenfassenden_merkmalen=[
                    "nationalitaet_Schweizerin/Schweizer",
                    "nationalitaet_Ausländerin/Ausländer",
                    "nationalitaet_unbekannt",
                ],
                neuer_merkmalsname="Nationalität",
            )
        )
        zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
            zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass,
            liste_mit_zusammenfassenden_merkmalen=[
                # Liste der Zürcher Gerichte
                "gericht_Bezirksgericht Zürich",
                "gericht_Bezirksgericht Winterthur",
                "gericht_Bezirksgericht Bülach",
                "gericht_Bezirksgericht Uster",
                "gericht_Bezirksgericht Dielsdorf",
                "gericht_Bezirksgericht Dietikon",
                "gericht_Bezirksgericht Horgen",
                "gericht_Bezirksgericht Meilen",
                # Liste der Berner Gerichte
                "gericht_Regionalgericht Bern-Mittelland",
                "gericht_Regionalgericht Berner Jura-Seeland",
                "gericht_Regionalgericht Emmental-Oberaargau",
                "gericht_Regionalgericht Oberland",
            ],
            neuer_merkmalsname="Gericht",
        )

        prognoseleistung_dict_regressor[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ] = zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass

        prognoseleistung_dict_regressor["urteilsbasis"] = len(y_strafmass)

        # kimodell als pickle file speichern
        ki_modell_als_pickle_file_speichern(
            instanziertes_kimodel=regressor_fuer_strafmass,
            name=f"betm_strafmass_{kanton}_illegitim",
            filename=f"betm_strafmass_{kanton}_illegitim.pkl",
            prognoseleistung_dict=prognoseleistung_dict_regressor,
        )

    messages.success(
        request,
        "Die KI-Evaluations-Modelle für Betm-Strafrecht wurden erfolgreich aktualisiert.",
    )
    return redirect("betm_dev")


@login_required
def betm_dev(request):
    prognoseleistung_dict_vollzugsart = KIModelPickleFile.objects.get(
        name="betm_rf_classifier_vollzugsart"
    ).prognoseleistung_dict

    oob_score_vollzugsart = prognoseleistung_dict_vollzugsart[
        "oob_score_class_vollzugsart"
    ]
    merkmalswichtigkeit_fuer_prognose_vollzugsart = prognoseleistung_dict_vollzugsart[
        "merkmalswichtigkeit_fuer_prognose_vollzugsart"
    ]

    prognoseleistung_dict_hauptsanktion = KIModelPickleFile.objects.get(
        name="betm_rf_classifier_sanktion"
    ).prognoseleistung_dict

    oob_score_hauptsanktion = prognoseleistung_dict_hauptsanktion[
        "oob_score_class_hauptsanktion"
    ]
    merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
        prognoseleistung_dict_hauptsanktion[
            "merkmalswichtigkeit_fuer_prognose_hauptsanktion"
        ]
    )

    prognoseleistung_dict_strafmass = KIModelPickleFile.objects.get(
        name="betm_rf_regressor_strafmass"
    ).prognoseleistung_dict

    durchschnittlicher_fehler = prognoseleistung_dict_strafmass[
        "durchschnittlicher_fehler"
    ]
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
        prognoseleistung_dict_strafmass[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ]
    )

    # Kantonsspezifische Prädiktoren laden
    prognoseleistung_dict_strafmass_nur_zh = KIModelPickleFile.objects.get(
        name="betm_strafmass_nur_ZH"
    ).prognoseleistung_dict

    durchschnittlicher_fehler_nur_zh = prognoseleistung_dict_strafmass_nur_zh[
        "durchschnittlicher_fehler"
    ]
    urteilsbasis_zh = prognoseleistung_dict_strafmass_nur_zh["urteilsbasis"]
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_zh = (
        prognoseleistung_dict_strafmass_nur_zh[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ]
    )

    context = {
        "string_oob_vollzugsart": oob_score_vollzugsart,
        "merkmalswichtigkeit_prognose_vollzugsart": merkmalswichtigkeit_fuer_prognose_vollzugsart,
        "string_oob_hauptsanktion": oob_score_hauptsanktion,
        "merkmalswichtigkeit_prognose_hauptsanktion": merkmalswichtigkeit_fuer_prognose_hauptsanktion,
        "durchschnittlicher_fehler": durchschnittlicher_fehler,
        "durchschnittlicher_fehler_nur_zh": durchschnittlicher_fehler_nur_zh,
        "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass": zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass,
        "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_zh": zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_zh,
        "urteilsbasis_zh": urteilsbasis_zh,
    }
    return render(request, "database/betm_dev.html", context=context)


def betm_evaluation(request):
    prognoseleistung_dict_vollzugsart = KIModelPickleFile.objects.get(
        name="betm_rf_classifier_vollzugsart"
    ).prognoseleistung_dict

    oob_score_vollzugsart = prognoseleistung_dict_vollzugsart[
        "oob_score_class_vollzugsart"
    ]
    merkmalswichtigkeit_fuer_prognose_vollzugsart = prognoseleistung_dict_vollzugsart[
        "merkmalswichtigkeit_fuer_prognose_vollzugsart"
    ]

    prognoseleistung_dict_hauptsanktion = KIModelPickleFile.objects.get(
        name="betm_rf_classifier_sanktion"
    ).prognoseleistung_dict

    oob_score_hauptsanktion = prognoseleistung_dict_hauptsanktion[
        "oob_score_class_hauptsanktion"
    ]
    merkmalswichtigkeit_fuer_prognose_hauptsanktion = (
        prognoseleistung_dict_hauptsanktion[
            "merkmalswichtigkeit_fuer_prognose_hauptsanktion"
        ]
    )

    prognoseleistung_dict_strafmass = KIModelPickleFile.objects.get(
        name="betm_rf_regressor_strafmass"
    ).prognoseleistung_dict

    durchschnittlicher_fehler = prognoseleistung_dict_strafmass[
        "durchschnittlicher_fehler"
    ]
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass = (
        prognoseleistung_dict_strafmass[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ]
    )
    last_updated = KIModelPickleFile.objects.get(
        name="betm_rf_regressor_strafmass"
    ).last_updated

    urteilsbasis = prognoseleistung_dict_strafmass["urteilsbasis"]

    # Kantonsspezifische Prädiktoren laden
    # Zürich legitime Kriterien
    prognoseleistung_dict_strafmass_nur_zh = KIModelPickleFile.objects.get(
        name="betm_strafmass_nur_ZH"
    ).prognoseleistung_dict

    durchschnittlicher_fehler_nur_zh = prognoseleistung_dict_strafmass_nur_zh[
        "durchschnittlicher_fehler"
    ]
    urteilsbasis_zh = prognoseleistung_dict_strafmass_nur_zh["urteilsbasis"]
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_zh = (
        prognoseleistung_dict_strafmass_nur_zh[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ]
    )

    # Bern legitime Kriterien
    prognoseleistung_dict_strafmass_nur_be = KIModelPickleFile.objects.get(
        name="betm_strafmass_nur_BE"
    ).prognoseleistung_dict

    durchschnittlicher_fehler_nur_be = prognoseleistung_dict_strafmass_nur_be[
        "durchschnittlicher_fehler"
    ]
    urteilsbasis_be = prognoseleistung_dict_strafmass_nur_be["urteilsbasis"]
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_be = (
        prognoseleistung_dict_strafmass_nur_be[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ]
    )

    # Zürich illegitime Kriterien
    prognoseleistung_dict_strafmass_nur_zh_illegitim = KIModelPickleFile.objects.get(
        name="betm_strafmass_ZH_illegitim"
    ).prognoseleistung_dict

    durchschnittlicher_fehler_nur_zh_illegitim = (
        prognoseleistung_dict_strafmass_nur_zh_illegitim["durchschnittlicher_fehler"]
    )
    urteilsbasis_zh_illegitim = prognoseleistung_dict_strafmass_nur_zh_illegitim[
        "urteilsbasis"
    ]
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_zh_illegitim = (
        prognoseleistung_dict_strafmass_nur_zh_illegitim[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ]
    )

    # Bern illegitime Kriterien
    prognoseleistung_dict_strafmass_nur_be_illegitim = KIModelPickleFile.objects.get(
        name="betm_strafmass_BE_illegitim"
    ).prognoseleistung_dict

    durchschnittlicher_fehler_nur_be_illegitim = (
        prognoseleistung_dict_strafmass_nur_be_illegitim["durchschnittlicher_fehler"]
    )
    urteilsbasis_be_illegitim = prognoseleistung_dict_strafmass_nur_be_illegitim[
        "urteilsbasis"
    ]
    zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_be_illegitim = (
        prognoseleistung_dict_strafmass_nur_be_illegitim[
            "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass"
        ]
    )

    context = {
        "string_oob_vollzugsart": oob_score_vollzugsart,
        "merkmalswichtigkeit_prognose_vollzugsart": merkmalswichtigkeit_fuer_prognose_vollzugsart,
        "string_oob_hauptsanktion": oob_score_hauptsanktion,
        "merkmalswichtigkeit_prognose_hauptsanktion": merkmalswichtigkeit_fuer_prognose_hauptsanktion,
        "durchschnittlicher_fehler": durchschnittlicher_fehler,
        "zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass": zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass,
        "last_updated": last_updated,
        "urteilsbasis": urteilsbasis,
        # Kantonsspezifische Prädiktoren für Evaluation der Rechtsprechung
        "durschnittlicher_fehler_zh": durchschnittlicher_fehler_nur_zh,
        "urteilsbasis_zh": urteilsbasis_zh,
        "merkmalswichtigkeit_strafmass_nur_zh": zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_zh,
        "durschnittlicher_fehler_be": durchschnittlicher_fehler_nur_be,
        "urteilsbasis_be": urteilsbasis_be,
        "merkmalswichtigkeit_strafmass_nur_be": zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_be,
        "durschnittlicher_fehler_zh_illegitim": durchschnittlicher_fehler_nur_zh_illegitim,
        "urteilsbasis_zh_illegitim": urteilsbasis_zh_illegitim,
        "merkmalswichtigkeit_strafmass_nur_zh_illegitim": zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_zh_illegitim,
        "durschnittlicher_fehler_be_illegitim": durchschnittlicher_fehler_nur_be_illegitim,
        "urteilsbasis_be_illegitim": urteilsbasis_be_illegitim,
        "merkmalswichtigkeit_strafmass_nur_be_illegitim": zusammengefasste_merkmalswichtigkeit_fuer_prognose_strafmass_nur_be_illegitim,
    }
    return render(request, "database/betm_evaluation.html", context=context)


# Science Views
def text_funktionsweise(request):
    context = {}
    return render(request, "database/funktionsweise.html", context)


def text_strafzumessung_mit_hilfe_von_ki(request):
    context = {}
    return render(request, "database/strafzumessung_mit_hilfe_von_ki.html", context)


# helper functions
def csv_in_notebooks_speichern(dbmodel):
    # Datenframe erstellen, db-id als index
    df = pd.DataFrame.from_records(dbmodel.objects.all().values())

    # kodiert abgespeicherte Variablen paraphrasieren
    df = vermoegensstrafrechts_urteile_codes_aufloesen(df)
    df.to_csv("notebooks/urteile.csv")


def datenbank_scatterplots_aktualisieren():
    kategorie_scatterplot_erstellen(
        Urteil,
        kategorie_feld="vollzug",
        titel="Deliktsumme/Strafhöhe Gegenüberstellung nach Vollzug",
        xlim=1000000,
    )
    kategorie_scatterplot_erstellen(
        Urteil,
        kategorie_feld="vollzug",
        titel="Deliktsumme/Strafhöhe Gegenüberstellung nach Vollzug (bis Fr. 200'000.--)",
        xlim=200000,
    )
    kategorie_scatterplot_erstellen(
        Urteil,
        kategorie_feld="hauptdelikt",
        titel="Deliktsumme/Strafhöhe Gegenüberstellung nach Deliktsart",
        xlim=1000000,
    )
    kategorie_scatterplot_erstellen(
        Urteil,
        kategorie_feld="hauptdelikt",
        titel="Deliktsumme/Strafhöhe Gegenüberstellung nach Deliktsart (bis Fr. 200'000.--)",
        xlim=200000,
    )


def csv_erstellen(request):
    csv_in_notebooks_speichern(Urteil)
    messages.success(request, "neues csv-file in notebooks abgespeichert")
    return redirect("dev")
