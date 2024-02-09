import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from .models import Urteil, BetmUrteil, KIModelPickleFile, DiagrammSVG
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
    onehotx_und_y_erstellen,
    sortierte_features_importance_list_erstellen,
    kimodelle_neu_kalibrieren_und_abspeichern,
    sortierte_koeff_list_erstellen,
    vermoegensstrafrechts_urteile_codes_aufloesen,
    introspection_plot_und_lesehinweis_abspeichern,
)
from .db_utils import (
    deliktssumme_strafhoehe_png_scatterplot_erstellen,
    seaborn_statistik_erstellen,
    kategorie_scatterplot_erstellen,
)
from .aws_helpers import kimodell_von_pickle_file_aus_aws_bucket_laden
import pickle
from sklearn.model_selection import cross_val_score


# Database Views
def database(request):
    datenbank_scatterplots_aktualisieren()

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
def kimodel_evaluation(request):
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
            return render(request, "database/kimodel_evaluation.html", context)

    else:
        # kimodelle mit nur validen features laden
        val_rf_kimodel = KIModelPickleFile.objects.get(name="rf_regr_val")
        val_rf_clf_kimodel = KIModelPickleFile.objects.get(name="rf_clf_val")
        # kimodelle mit allen features laden
        all_rf_kimodel = KIModelPickleFile.objects.get(name="rf_regr_all")
        lr_kimodel = KIModelPickleFile.objects.get(name="lr_regr_all")

        introspection_plot = DiagrammSVG.objects.get(name="introspection_plot")

        # kontext füllen
        context = {
            "val_rf_kimodel": val_rf_kimodel,
            "val_rf_clf_kimodel": val_rf_clf_kimodel,
            "all_rf_kimodel": all_rf_kimodel,
            "introspection_plot": introspection_plot,
        }

    return render(request, "database/kimodel_evaluation.html", context)


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
            )
            y_train_df = Urteil.pandas.return_y_zielwerte()

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

            nachbar_pk, nachbar_pk2, knn_prediction = knn_pipeline(
                x_train_df, y_train_df, urteil_features_series
            )

            nachbar = Urteil.objects.get(pk=nachbar_pk)
            nachbar2 = Urteil.objects.get(pk=nachbar_pk2)

            # differenzen von eingabe und nachbarn berechnen, evt. mal auslagern
            def differenzengenerator(nachbarobjekt, formobjekt):
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
                return nachbarobjekt

            nachbar = differenzengenerator(nachbar, form)
            nachbar2 = differenzengenerator(nachbar2, form)

            return render(
                request,
                "database/prognose.html",
                {
                    "form": form,
                    "vorhersage_strafmass": vorhersage_strafmass[0],
                    "vorhersage_vollzug": vollzugsstring,
                    "vorhersage_sanktionsart": string_sanktionsart,
                    "knn_prediction": knn_prediction,
                    "nachbar": nachbar,
                    "nachbar2": nachbar2,
                },
            )

    # if a GET (or any other method) we'll create a blank form
    else:
        form = UrteilsEckpunkteAbfrageFormular()

    return render(request, "database/prognose.html", {"form": form})


def prognose_betm(request):
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
            )
            y_train_df = Urteil.pandas.return_y_zielwerte()

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

            nachbar_pk, nachbar_pk2, knn_prediction = knn_pipeline(
                x_train_df, y_train_df, urteil_features_series
            )

            nachbar = Urteil.objects.get(pk=nachbar_pk)
            nachbar2 = Urteil.objects.get(pk=nachbar_pk2)

            # differenzen von eingabe und nachbarn berechnen, evt. mal auslagern
            def differenzengenerator(nachbarobjekt, formobjekt):
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
                return nachbarobjekt

            nachbar = differenzengenerator(nachbar, form)
            nachbar2 = differenzengenerator(nachbar2, form)

            return render(
                request,
                "database/prognose.html",
                {
                    "form": form,
                    "vorhersage_strafmass": vorhersage_strafmass[0],
                    "vorhersage_vollzug": vollzugsstring,
                    "vorhersage_sanktionsart": string_sanktionsart,
                    "knn_prediction": knn_prediction,
                    "nachbar": nachbar,
                    "nachbar2": nachbar2,
                },
            )

    # if a GET (or any other method) we'll create a blank form
    else:
        form = BetmUrteilsEckpunkteAbfrageFormular()

    return render(request, "database/prognose_betm.html", {"form": form})


def csv_erstellen(request):
    csv_in_notebooks_speichern(Urteil)
    messages.success(request, "neues csv-file in notebooks abgespeichert")
    return redirect("dev")


@login_required
def dev(request):
    # kimodelle mit nur validen features laden
    val_rf_kimodel = KIModelPickleFile.objects.get(name="rf_regr_val")
    val_rf_clf_kimodel = KIModelPickleFile.objects.get(name="rf_clf_val")

    # Urteile mit bester und schlechtester Prognoseleistung laden, um im template darauf verlinken zu können
    # konformes_urteil = Urteil.objects.get(fall_nr=val_rf_kimodel.prognoseleistung_dict.beste_prognoseleistung_urteil)
    # unkonformes_urteil = Urteil.objects.get(fall_nr=val_rf_kimodel.prognoseleistung_dict.schlechteste_prognoseleistung_urteil)

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
        # 'unkonformes_urteil': unkonformes_urteil,
        # 'konformes_urteil': konformes_urteil,
    }
    return render(request, "database/dev.html", context)


@login_required
def dev_model_neu_kalibrieren(request):
    kimodelle_neu_kalibrieren_und_abspeichern()
    introspection_plot_und_lesehinweis_abspeichern()
    messages.success(request, "Die KI-Modelle wurden erfolgreich aktualisiert.")
    messages.success(request, "Der Introspection Plot wurde erfolgreich neu erstellt")
    return redirect("dev")


def text(request):
    context = {}
    return render(request, "database/text.html", context)


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
