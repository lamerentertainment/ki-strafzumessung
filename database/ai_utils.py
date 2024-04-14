import pickle
from io import StringIO, BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from django.core.files.base import ContentFile
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .aws_helpers import (
    kimodell_von_pickle_file_aus_aws_bucket_laden,
    ki_modell_als_pickle_file_speichern,
)
from .models import (
    Urteil,
    BetmUrteil,
    Betm,
    BetmArt,
    Kanton,
    Rolle,
    KIModelPickleFile,
    DiagrammSVG,
)


def onehotx_und_y_erstellen(
    dbmodel,
    categorial_ft_dbfields=None,
    numerical_ft_dbfields=None,
    target_dbfields=None,
    return_encoder=False,
    csv_erstellen=False,
):
    """
    :param return_encoder: gibt encoder zurück, um diesen bei einem ki-modell abzuspeichern
    :param dbmodel: ein Django Datenbank-Urteilsmodel
    :param categorial_ft_dbfields: eine Liste mit den kategorialen Datenbank-Feldern
    :param numerical_ft_dbfields: eine Liste mit den numerischen Datenbank-Feldern
    :param target_dbfields: eine Liste mit der Zielvariable(n)
    :param csv_erstellen: Bool, ob - im notbooks Ordner - ein neuer CSV vom Datensatz erstellt werden soll
    :return: x (df, 1hot encoded), y (np_array)
    """

    # Mutable Default Parameter Werte definieren
    if target_dbfields is None:
        target_dbfields = ["freiheitsstrafe_in_monaten"]
    if numerical_ft_dbfields is None:
        numerical_ft_dbfields = [
            "deliktssumme",
            "nebenverurteilungsscore",
            "urteilsjahr",
        ]
    if categorial_ft_dbfields is None:
        categorial_ft_dbfields = [
            "hauptdelikt",
            "geschlecht",
            "nationalitaet",
            "gericht",
            "mehrfach",
            "gewerbsmaessig",
            "vorbestraft",
            "vorbestraft_einschlaegig",
        ]

    # Queryset aller Urteile holen, welche in_ki_modell True haben
    alle_zu_beruecksichtigenden_urteile = dbmodel.objects.filter(in_ki_modell=True)

    # Datenframe erstellen
    df = pd.DataFrame.from_records(alle_zu_beruecksichtigenden_urteile.values())

    # kodiert abgespeicherte Variablen paraphrasieren
    df = vermoegensstrafrechts_urteile_codes_aufloesen(df)

    if csv_erstellen:
        df.to_csv("notebooks/urteile.csv")

    # Urteilsdatum in Urteilsjahr konvertieren
    df["urteilsdatum"] = pd.to_datetime(df["urteilsdatum"])
    df["urteilsdatum"] = df["urteilsdatum"].map(lambda a: a.year)
    df.rename(columns={"urteilsdatum": "urteilsjahr"}, inplace=True)

    # 1hot encoding der kategorialen variablen
    encoder = OneHotEncoder(sparse_output=False)
    encoder.fit(df[categorial_ft_dbfields])
    categorical_1hot = encoder.transform(df[categorial_ft_dbfields])
    encoder_categorical_ft_names = encoder.get_feature_names_out(categorial_ft_dbfields)
    df_categorical_1hot = pd.DataFrame(
        categorical_1hot, columns=encoder_categorical_ft_names
    )

    # df der 1hot-kodierten features mit df der numerischen features zusammenfügen
    x = pd.concat([df_categorical_1hot, df[numerical_ft_dbfields]], axis=1)

    # y erstellen
    if target_dbfields == ["freiheitsstrafe_in_monaten"]:
        # wenn freiheitsstrafe in monaten 0 ist, sollte der wert anzahl_tagessaetze / 30 als zielwert genommen werden
        y = (
            (df["anzahl_tagessaetze"] / 30)
            .where(
                df["freiheitsstrafe_in_monaten"] == 0, df["freiheitsstrafe_in_monaten"]
            )
            .values.ravel()
        )
    else:
        y = df[target_dbfields].values.ravel()

    if return_encoder:
        return x, y, encoder
    else:
        return x, y


def vermoegensstrafrechts_urteile_codes_aufloesen(dataframe):
    # kodiert abgespeicherte Variablen paraphrasieren
    if "geschlecht" in dataframe.columns:
        dataframe["geschlecht"].replace(
            {"0": "männlich", "1": "weiblich"}, inplace=True
        )
    if "nationalitaet" in dataframe.columns:
        dataframe["nationalitaet"].replace(
            {
                "0": "Schweizerin/Schweizer",
                "1": "Ausländerin/Ausländer",
                "2": "unbekannt",
            },
            inplace=True,
        )
    if "vollzug" in dataframe.columns:
        dataframe["vollzug"].replace(
            {"0": "bedingt", "1": "teilbedingt", "2": "unbedingt"}
        )
    return dataframe


def random_forest_regressor_erstellen(x, y):
    random_forest_regressor = RandomForestRegressor(
        random_state=42,
        max_depth=110,
        min_samples_split=2,
        min_samples_leaf=4,
        n_estimators=10,
    )
    random_forest_regressor.fit(x, y)
    return random_forest_regressor


def linear_regression_regressor_erstellen(x, y):
    linear_regression_regressor = LinearRegression()
    linear_regression_regressor.fit(x, y)
    return linear_regression_regressor


def sortierte_features_importance_list_erstellen(
    instanziertes_kimodel, categorial_ft_dbfields=None
):
    if categorial_ft_dbfields is None:
        categorial_ft_dbfields = [
            "geschlecht",
            "nationalitaet",
            "gericht",
            "mehrfach",
            "gewerbsmaessig",
            "bandenmaessig",
            "vorbestraft",
            "vorbestraft_einschlaegig",
            "hauptdelikt",
        ]

    # sortierte Liste mit Kriteriengewichtigkeit erstellen
    list_of_zipped_importance_feature_tuples = list(
        zip(
            instanziertes_kimodel.feature_importances_,
            instanziertes_kimodel.feature_names_in_,
        )
    )

    # nach Wichtigkeit sortieren
    list_of_zipped_importance_feature_tuples = sorted(
        list_of_zipped_importance_feature_tuples,
        key=lambda importance_ft_tup: importance_ft_tup[0],
        reverse=True,
    )

    zusammenfassende_list_of_zipped_importance_features_tuples = (
        list_of_zipped_importance_feature_tuples.copy()
    )

    # problem beheben, dass vorbestraft_einschlaegig und vorbestraft gleich beginnen:
    for i, imp_ft_tuple in enumerate(
        zusammenfassende_list_of_zipped_importance_features_tuples
    ):
        if imp_ft_tuple[1].startswith("vorbestraft_einschlaegig"):
            zusammenfassende_list_of_zipped_importance_features_tuples[i] = (
                imp_ft_tuple[0],
                "einschlaegig_vorbestraft",
            )

    zusammenfassende_kategorien = categorial_ft_dbfields.copy()
    zusammenfassende_kategorien.append("einschlaegig_vorbestraft")
    zusammenfassende_kategorien.remove("vorbestraft_einschlaegig")

    # 1hot kategorisierte kategoriale Variablen wieder zusammenrechnen
    for kategorie in zusammenfassende_kategorien:
        importance = 0
        tuples_for_deletion = []
        for imp_ft_tuple in zusammenfassende_list_of_zipped_importance_features_tuples:
            if imp_ft_tuple[1].startswith(kategorie):
                importance += imp_ft_tuple[0]
                tuples_for_deletion.append(imp_ft_tuple)
        zusammenfassende_list_of_zipped_importance_features_tuples.append(
            (importance, kategorie)
        )
        zusammenfassende_list_of_zipped_importance_features_tuples = [
            x
            for x in zusammenfassende_list_of_zipped_importance_features_tuples
            if x not in tuples_for_deletion
        ]

    # erstes Element im Tuple mit 100 Multiplizieren, um % Darstellung vorzubereiten
    result_list = []
    for tup in list_of_zipped_importance_feature_tuples:
        new_tup = (tup[0] * 100, tup[1])
        result_list.append(new_tup)
    list_of_zipped_importance_feature_tuples = result_list
    result_list = []
    for tup in zusammenfassende_list_of_zipped_importance_features_tuples:
        new_tup = (tup[0] * 100, tup[1])
        result_list.append(new_tup)
    zusammenfassende_list_of_zipped_importance_features_tuples = result_list

    # nochmals sortieren, da zusammenfassung sortierung durcheinander gebracht hat
    zusammenfassende_list_of_zipped_importance_features_tuples = sorted(
        zusammenfassende_list_of_zipped_importance_features_tuples,
        key=lambda importance_feature_tuple: importance_feature_tuple[0],
        reverse=True,
    )

    return (
        list_of_zipped_importance_feature_tuples,
        zusammenfassende_list_of_zipped_importance_features_tuples,
    )


def sortierte_koeff_list_erstellen(instanziiertes_lr_kimodel):
    coeff_features_list = list(
        zip(
            instanziiertes_lr_kimodel.coef_, instanziiertes_lr_kimodel.feature_names_in_
        )
    )
    koeff_liste = sorted(coeff_features_list, key=lambda tup: tup[0])
    return koeff_liste


def prognoseleistung_dict_ausgeben(instanziertes_kimodel, x, y):
    loo = LeaveOneOut()
    prognoseleistung_dict = {}
    liste_der_abweichungen = []
    beste_prognoseleistung_index = None
    schlechteste_prognoseleistung_index = None
    for train, test in loo.split(x):
        instanziertes_kimodel.fit(x.iloc[train], y[train])
        vorhersage = instanziertes_kimodel.predict(x.iloc[test])
        tatsächliches_strafmass = y[test]
        differenz = abs(vorhersage[0] - tatsächliches_strafmass)
        liste_der_abweichungen.append(differenz)
        if (
            beste_prognoseleistung_index is None
            or differenz < liste_der_abweichungen[beste_prognoseleistung_index]
        ):
            beste_prognoseleistung_index = (
                len(liste_der_abweichungen) - 1
            )  # store new index
        if (
            schlechteste_prognoseleistung_index is None
            or differenz > liste_der_abweichungen[schlechteste_prognoseleistung_index]
        ):
            schlechteste_prognoseleistung_index = len(liste_der_abweichungen) - 1
    durchschnittlicher_fehler = np.mean(liste_der_abweichungen)
    standardabweichung = np.std(liste_der_abweichungen)
    prognoseleistung_dict["durchschnittlicher_fehler"] = round(
        durchschnittlicher_fehler, 2
    )
    prognoseleistung_dict["standardabweichung"] = round(standardabweichung, 2)
    prognoseleistung_dict["beste_prognoseleistung"] = round(
        np.min(liste_der_abweichungen), 2
    )
    prognoseleistung_dict[
        "beste_prognoseleistung_index"
    ] = beste_prognoseleistung_index  # store index
    prognoseleistung_dict["schlechteste_prognoseleistung"] = round(
        np.max(liste_der_abweichungen), 2
    )
    prognoseleistung_dict[
        "schlechteste_prognoseleistung_index"
    ] = schlechteste_prognoseleistung_index  # store index

    for differenz in liste_der_abweichungen:
        if (
            differenz < durchschnittlicher_fehler - standardabweichung
            or differenz > durchschnittlicher_fehler + standardabweichung
        ):
            index = liste_der_abweichungen.index(differenz)
            liste_der_abweichungen[index] = "ausserhalb"
    ausserhalb_standardabweichung = liste_der_abweichungen.count("ausserhalb")
    prognoseleistung_dict[
        "standardabweichung_string"
    ] = f"{round((len(liste_der_abweichungen) - ausserhalb_standardabweichung) / len(liste_der_abweichungen) * 100, 2)}% aller Prognosen weisen einen Fehler zwischen {round(durchschnittlicher_fehler - standardabweichung, 2)} und {round(durchschnittlicher_fehler + standardabweichung, 2)} Monaten auf"

    return prognoseleistung_dict


def kimodelle_neu_kalibrieren_und_abspeichern():
    # nur valide features verwenden
    categorial_ft_dbfields = [
        "hauptdelikt",
        "mehrfach",
        "gewerbsmaessig",
        "bandenmaessig",
        "vorbestraft",
        "vorbestraft_einschlaegig",
    ]
    x_val, y, onehot_encoder_val = onehotx_und_y_erstellen(
        Urteil,
        categorial_ft_dbfields=categorial_ft_dbfields,
        numerical_ft_dbfields=["deliktssumme", "nebenverurteilungsscore"],
        return_encoder=True,
    )

    # random forest REGRESSOR mit ausschliesslich validen features
    random_forest_regressor_val_fts = random_forest_regressor_erstellen(x_val, y)
    prognoseleistung_dict = prognoseleistung_dict_ausgeben(
        random_forest_regressor_val_fts, x_val, y
    )

    # urteils df generieren, um mit erzieltem index bestes und schlechtes hervorgesagtes Urteil zu finden
    df = pd.DataFrame.from_records(Urteil.objects.all().values())
    prognoseleistung_dict["beste_prognoseleistung_urteil"] = df.loc[
        prognoseleistung_dict["beste_prognoseleistung_index"]
    ].fall_nr
    prognoseleistung_dict["schlechteste_prognoseleistung_urteil"] = df.loc[
        prognoseleistung_dict["schlechteste_prognoseleistung_index"]
    ].fall_nr

    (
        list_of_zipped_importance_feature_tuples,
        zusammenfassende_list_of_zipped_importance_features_tuples,
    ) = sortierte_features_importance_list_erstellen(
        random_forest_regressor_val_fts, categorial_ft_dbfields=categorial_ft_dbfields
    )
    # kimodell als pickle file speichern
    ki_modell_als_pickle_file_speichern(
        instanziertes_kimodel=random_forest_regressor_val_fts,
        name="rf_regr_val",
        filename="random_forest_regressor_val_fts.pkl",
        prognoseleistung_dict=prognoseleistung_dict,
        ft_importance_list=list_of_zipped_importance_feature_tuples,
        ft_importance_list_merged=zusammenfassende_list_of_zipped_importance_features_tuples,
    )

    # bei validem regressor noch den onehotencoder für späteren transform der eingeabwerte abspeichern
    kimodell = KIModelPickleFile.objects.get(name="rf_regr_val")
    content = pickle.dumps(onehot_encoder_val)
    content_file = ContentFile(content)
    kimodell.encoder.save("one_hot_encoder_fuer_rf_regr_val.pkl", content_file)
    content_file.close()

    # random forest CLASSIFIER mit ausschliesslich validen features, VOLLZUGSART als zielvariable
    y = Urteil.pandas.return_y_zielwerte(zielwert="vollzug", exclude_unmarked=True)
    random_forest_classifier_val_fts = RandomForestClassifier(oob_score=True)
    random_forest_classifier_val_fts.fit(x_val, y)
    gerundeter_oob_score_vollzugsart = round(
        random_forest_classifier_val_fts.oob_score_ * 100, 1
    )
    prognoseleistung_dict = {"oob_score": gerundeter_oob_score_vollzugsart}
    # merkmalwchtigkeitslisten erstellen
    (
        list_of_zipped_importance_feature_tuples,
        zusammenfassende_list_of_zipped_importance_features_tuples,
    ) = sortierte_features_importance_list_erstellen(
        random_forest_classifier_val_fts, categorial_ft_dbfields=categorial_ft_dbfields
    )
    # kimodell als pickle file speichern
    ki_modell_als_pickle_file_speichern(
        instanziertes_kimodel=random_forest_classifier_val_fts,
        name="rf_clf_val",
        filename="random_forest_classifier_val_fts.pkl",
        prognoseleistung_dict=prognoseleistung_dict,
        ft_importance_list=list_of_zipped_importance_feature_tuples,
        ft_importance_list_merged=zusammenfassende_list_of_zipped_importance_features_tuples,
    )

    # random forest CLASSIFIER mit ausschliesslich validen features, SANKTIONSART als zielvariable
    y = Urteil.pandas.return_y_zielwerte(
        zielwert="hauptsanktion", exclude_unmarked=True
    )
    rf_classifier_fuer_sanktionsart_val_fts = RandomForestClassifier(oob_score=True)
    rf_classifier_fuer_sanktionsart_val_fts.fit(x_val, y)
    gerundeter_oob_score_sanktionsart = round(
        rf_classifier_fuer_sanktionsart_val_fts.oob_score_ * 100, 1
    )
    prognoseleistung_dict = {"oob_score": gerundeter_oob_score_sanktionsart}
    # merkmalwchtigkeitslisten erstellen
    (
        list_of_zipped_importance_feature_tuples,
        zusammenfassende_list_of_zipped_importance_features_tuples,
    ) = sortierte_features_importance_list_erstellen(
        rf_classifier_fuer_sanktionsart_val_fts,
        categorial_ft_dbfields=categorial_ft_dbfields,
    )
    # kimodell als pickle file speichern
    ki_modell_als_pickle_file_speichern(
        instanziertes_kimodel=rf_classifier_fuer_sanktionsart_val_fts,
        name="rf_clf_sanktionsart_val",
        filename="rf_classifier_fuer_sanktionsart_val_fts.pkl",
        prognoseleistung_dict=prognoseleistung_dict,
        ft_importance_list=list_of_zipped_importance_feature_tuples,
        ft_importance_list_merged=zusammenfassende_list_of_zipped_importance_features_tuples,
    )

    # alle features verwenden
    x, y = onehotx_und_y_erstellen(Urteil)

    # random forest REGRESSOR mit allen features
    random_forest_regressor_all_fts = random_forest_regressor_erstellen(x, y)
    prognoseleistung_dict = prognoseleistung_dict_ausgeben(
        random_forest_regressor_all_fts, x, y
    )
    (
        list_of_zipped_importance_feature_tuples,
        zusammenfassende_list_of_zipped_importance_features_tuples,
    ) = sortierte_features_importance_list_erstellen(random_forest_regressor_all_fts)
    # kimodell als pickle file speichern
    ki_modell_als_pickle_file_speichern(
        instanziertes_kimodel=random_forest_regressor_all_fts,
        name="rf_regr_all",
        filename="random_forest_regressor_all_fts.pkl",
        prognoseleistung_dict=prognoseleistung_dict,
        ft_importance_list=list_of_zipped_importance_feature_tuples,
        ft_importance_list_merged=zusammenfassende_list_of_zipped_importance_features_tuples,
    )

    # LINEAR regression REGRESSOR
    linear_regression_regressor_all_fts = linear_regression_regressor_erstellen(x, y)
    prognoseleistung_dict = prognoseleistung_dict_ausgeben(
        linear_regression_regressor_all_fts, x, y
    )
    ki_modell_als_pickle_file_speichern(
        instanziertes_kimodel=linear_regression_regressor_all_fts,
        name="lr_regr_all",
        filename="linear_regression_regressor_all_fts.pkl",
        prognoseleistung_dict=prognoseleistung_dict,
    )


# ALTE FUNKTIONEN


def y_und_x_erstellen(urteil_model, zielwert):
    """nimmt das Urteilsmodel als Parameter und gibt die zielwerte y und X für ai-model-fitting zurück:
    y_zielwerte ist eine Liste mit der Anzahl Freiheitsstrafe als Elemente
    X_urteilsmerkmale ist ein pandas dataframe mit Urteilsmerkmalen Verfahrensart, Geschlecht etc. als Columns
    """
    urteil_queryset = urteil_model.objects.all()

    if zielwert == "hoehe_strafe" or "knn":
        y_zielwerte = [urteil.freiheitsstrafe_in_monaten for urteil in urteil_queryset]
        print("y-zielwerte hoehe_strafe angewählt")
    elif zielwert == "vollzug":
        print("hallo?")
        y_zielwerte = [urteil.vollzug for urteil in urteil_queryset]
        # transformation in string kategorie
        for i in range(len(y_zielwerte)):
            if y_zielwerte[i] == "0":
                y_zielwerte[i] = 0
            elif y_zielwerte[i] == "1":
                y_zielwerte[i] = 1
            elif y_zielwerte[i] == "2":
                y_zielwerte[i] = 2

    print(y_zielwerte)

    liste_mit_urteilslisten = [
        [
            urteil.geschlecht,
            urteil.hauptdelikt,
            urteil.mehrfach,
            urteil.gewerbsmaessig,
            urteil.bandenmaessig,
            urteil.deliktssumme,
            urteil.nebenverurteilungsscore,
            urteil.vorbestraft,
            urteil.vorbestraft_einschlaegig,
        ]
        for urteil in Urteil.objects.all()
    ]

    x_werte = pd.DataFrame(
        np.array(liste_mit_urteilslisten),
        columns=[
            "Geschlecht",
            "Hauptdelikt",
            "mehrfach",
            "gewerbsmaessig",
            "bandenmaessig",
            "Deliktssumme",
            "Nebenverurteilungsscore",
            "vorbestraft",
            "einschlaegig vorbestraft",
        ],
    )

    return y_zielwerte, x_werte


# preprocessing
def preprocessing_x(pd_df_x):
    """nimmt ein pandas-df als argument und gibt eine preprocessed-pandas-df (boolean-Werte zu 0/1; one-hot-encoder für
    hauptdelikt zurück"""
    # one-hot-encode hauptdelikt
    pd_df_x["Hauptdelikt.Betrug"] = [
        1 if eintrag == "Betrug" else 0 for eintrag in pd_df_x["Hauptdelikt"]
    ]
    pd_df_x["Hauptdelikt.DVA"] = [
        1 if eintrag == "betr. Missbrauch DVA" else 0
        for eintrag in pd_df_x["Hauptdelikt"]
    ]
    pd_df_x["Hauptdelikt.Veruntreuung"] = [
        1 if eintrag == "Veruntreuung" else 0 for eintrag in pd_df_x["Hauptdelikt"]
    ]
    pd_df_x["Hauptdelikt.ungGB"] = [
        1 if eintrag == "ung. Geschäftsbesorgung" else 0
        for eintrag in pd_df_x["Hauptdelikt"]
    ]
    pd_df_x["Hauptdelikt.Diebstahl"] = [
        1 if eintrag == "Diebstahl" else 0 for eintrag in pd_df_x["Hauptdelikt"]
    ]
    pd_df_x["Hauptdelikt.SachB"] = [
        1 if eintrag == "Sachbeschädigung" else 0 for eintrag in pd_df_x["Hauptdelikt"]
    ]
    pd_df_x = pd_df_x.drop("Hauptdelikt", axis=1)

    # boolean auf 0/1
    pd_df_x["mehrfach"] = [
        1 if eintrag == "True" else 0 for eintrag in pd_df_x["mehrfach"]
    ]
    pd_df_x["gewerbsmaessig"] = [
        1 if eintrag == "True" else 0 for eintrag in pd_df_x["gewerbsmaessig"]
    ]
    pd_df_x["bandenmaessig"] = [
        1 if eintrag == "True" else 0 for eintrag in pd_df_x["bandenmaessig"]
    ]
    pd_df_x["vorbestraft"] = [
        1 if eintrag == "True" else 0 for eintrag in pd_df_x["vorbestraft"]
    ]
    pd_df_x["einschlaegig vorbestraft"] = [
        1 if eintrag == "True" else 0 for eintrag in pd_df_x["einschlaegig vorbestraft"]
    ]

    return pd_df_x


def formulareingaben_in_abfragesample_konvertieren(cleaned_data_dict):
    """nimmt die Formulareingaben, erstellt davon ein pandas dataframe und macht das preprocessing, um ein
    estimate abfragesample zu generieren"""
    cat_fts = [
        "hauptdelikt",
        "mehrfach",
        "gewerbsmaessig",
        "bandenmaessig",
        "vorbestraft",
        "vorbestraft_einschlaegig",
    ]
    num_fts = ["deliktssumme", "nebenverurteilungsscore"]

    hauptdelikt = cleaned_data_dict["hauptdelikt"]
    mehrfach = cleaned_data_dict["mehrfach"]
    gewerbsmaessig = cleaned_data_dict["gewerbsmaessig"]
    bandenmaessig = cleaned_data_dict["bandenmaessig"]
    deliktssumme = cleaned_data_dict["deliktssumme"]
    nebenverurteilungsscore = cleaned_data_dict["nebenverurteilungsscore"]
    vorbestraft = cleaned_data_dict["vorbestraft"]
    vorbestraft_einschlaegig = cleaned_data_dict["vorbestraft_einschlaegig"]

    liste_mit_urteilsmerkmalen = [
        hauptdelikt,
        mehrfach,
        gewerbsmaessig,
        bandenmaessig,
        deliktssumme,
        nebenverurteilungsscore,
        vorbestraft,
        vorbestraft_einschlaegig,
    ]

    urteilsmerkmale_als_pandas_df = pd.DataFrame(
        [liste_mit_urteilsmerkmalen],
        columns=[
            "hauptdelikt",
            "mehrfach",
            "gewerbsmaessig",
            "bandenmaessig",
            "deliktssumme",
            "nebenverurteilungsscore",
            "vorbestraft",
            "vorbestraft_einschlaegig",
        ],
    )
    urteilsmerkmale_als_pandas_df = vermoegensstrafrechts_urteile_codes_aufloesen(
        urteilsmerkmale_als_pandas_df
    )
    encoder = kimodell_von_pickle_file_aus_aws_bucket_laden(
        "encoders/one_hot_encoder_fuer_rf_regr_val.pkl"
    )
    cat_fts_onehot = encoder.transform(urteilsmerkmale_als_pandas_df[cat_fts])
    enc_cat_fts_names = encoder.get_feature_names_out(cat_fts)
    df_cat_fts = pd.DataFrame(cat_fts_onehot, columns=enc_cat_fts_names)
    urteilsmerkmale_df_preprocessed = pd.concat(
        [df_cat_fts, urteilsmerkmale_als_pandas_df[num_fts]], axis=1
    )
    return urteilsmerkmale_df_preprocessed


def knn_pipeline(train_X_df, train_y_df, urteil_features_series, skalenausgleich=1.2):
    """nimmt als Input ein Pandas DF der merkmale und der zielwerte"""
    cat_ohe_step = ("ohe", OneHotEncoder(drop="if_binary"))
    cat_steps = [cat_ohe_step]
    cat_pipe = Pipeline(cat_steps)
    cat_features = [
        "gewerbsmaessig",
        "hauptdelikt",
        "vorbestraft_einschlaegig",
        "vorbestraft",
    ]

    num_mm_step = ("mm", StandardScaler())
    num_steps = [num_mm_step]
    num_pipe = Pipeline(num_steps)
    num_features = ["deliktssumme", "nebenverurteilungsscore"]

    transformers = [("cat", cat_pipe, cat_features), ("num", num_pipe, num_features)]
    ct = ColumnTransformer(transformers=transformers)

    x_transformed = ct.fit_transform(train_X_df)
    feature_names = ct.get_feature_names_out()
    x_transformed = pd.DataFrame(x_transformed, columns=feature_names)

    # aktuelle gewichte aus dem validen rf kimodell laden
    ft_importances_list = KIModelPickleFile.objects.get(
        name="rf_regr_val"
    ).ft_importance_list_merged

    x_transformed_gewichtet = x_transformed.copy()
    for imp_ft_tuple in ft_importances_list:
        # beim feature Deliktssumme soll zusätzlich ein Ausgleich der unterschiedlichen Skalenweiten erfolgen
        if imp_ft_tuple[1] == "deliktssumme":
            x_transformed_gewichtet["num__deliktssumme"] = (
                imp_ft_tuple[0]
                * x_transformed_gewichtet["num__deliktssumme"]
                * skalenausgleich
            )
        # beim feature einschlägig vorbestraft muss vorerst das gewicht angepasst werden, ansonsten das Gewicht für vorbestraft (das im Namen einschlaegig_vorbestraft enthalten ist) hier "verbraucht" wird
        if imp_ft_tuple[1] == "einschlaegig_vorbestraft":
            x_transformed_gewichtet["cat__vorbestraft_einschlaegig_True"] = (
                imp_ft_tuple[0]
                * x_transformed_gewichtet["cat__vorbestraft_einschlaegig_True"]
            )
        # wo feature name in spaltenname der ft_importances_list enthalten ist, soll die importance multipliziert werden
        for column_name in x_transformed_gewichtet.columns:
            if imp_ft_tuple[1] in column_name:
                x_transformed_gewichtet[column_name] = (
                    imp_ft_tuple[0] * x_transformed_gewichtet[column_name]
                )

    knn = KNeighborsRegressor()
    knn.fit(x_transformed_gewichtet, train_y_df)
    urteil_features_df = urteil_features_series.to_frame().transpose()
    urteil_features_df.columns = [
        "gewerbsmaessig",
        "hauptdelikt",
        "vorbestraft_einschlaegig",
        "vorbestraft",
        "deliktssumme",
        "nebenverurteilungsscore",
    ]
    urteil_features_transformed = ct.transform(urteil_features_df)
    feature_names = ct.get_feature_names_out()
    urteil_features_transformed_df = pd.DataFrame(
        urteil_features_transformed, columns=feature_names
    )
    urteil_features_transformed_df_gewichtet = urteil_features_transformed_df.copy()
    for imp_ft_tuple in ft_importances_list:
        # beim feature Deliktssumme soll zusätzlich ein Ausgleich der unterschiedlichen Skalenweiten erfolgen
        if imp_ft_tuple[1] == "deliktssumme":
            urteil_features_transformed_df_gewichtet["num__deliktssumme"] = (
                imp_ft_tuple[0]
                * urteil_features_transformed_df_gewichtet["num__deliktssumme"]
                * skalenausgleich
            )
        # beim feature einschlägig vorbestraft muss vorerst das gewicht angepasst werden, ansonsten das Gewicht für vorbestraft (das im Namen einschlaegig_vorbestraft enthalten ist) hier "verbraucht" wird
        if imp_ft_tuple[1] == "einschlaegig_vorbestraft":
            urteil_features_transformed_df_gewichtet[
                "cat__vorbestraft_einschlaegig_True"
            ] = (
                imp_ft_tuple[0]
                * urteil_features_transformed_df_gewichtet[
                    "cat__vorbestraft_einschlaegig_True"
                ]
            )
        # wo feature name in spaltenname der ft_importances_list enthalten ist, soll die importance multipliziert werden
        for column_name in urteil_features_transformed_df_gewichtet.columns:
            if imp_ft_tuple[1] in column_name:
                urteil_features_transformed_df_gewichtet[column_name] = (
                    imp_ft_tuple[0]
                    * urteil_features_transformed_df_gewichtet[column_name]
                )

    differences, indexes = knn.kneighbors(urteil_features_transformed_df_gewichtet)
    knn_prediction = knn.predict(urteil_features_transformed_df_gewichtet)[0][0]

    nachbar_pk = train_X_df.iloc[indexes[0, 0]].name
    nachbar_pk2 = train_X_df.iloc[indexes[0, 1]].name

    return nachbar_pk, nachbar_pk2, knn_prediction


def nachbar_mit_sanktionsbewertung_anreichern(
    nachbarobjekt, strafmass_estimator, hauptsanktion_estimator, vollzug_estimator
):
    cat_fts = [
        "hauptdelikt",
        "mehrfach",
        "gewerbsmaessig",
        "bandenmaessig",
        "vorbestraft",
        "vorbestraft_einschlaegig",
    ]
    num_fts = ["deliktssumme", "nebenverurteilungsscore"]

    hauptdelikt = nachbarobjekt.hauptdelikt
    mehrfach = nachbarobjekt.mehrfach
    gewerbsmaessig = nachbarobjekt.gewerbsmaessig
    bandenmaessig = nachbarobjekt.bandenmaessig
    deliktssumme = nachbarobjekt.deliktssumme
    nebenverurteilungsscore = nachbarobjekt.nebenverurteilungsscore
    vorbestraft = nachbarobjekt.vorbestraft
    vorbestraft_einschlaegig = nachbarobjekt.vorbestraft_einschlaegig

    liste_mit_urteilsmerkmalen = [
        hauptdelikt,
        mehrfach,
        gewerbsmaessig,
        bandenmaessig,
        deliktssumme,
        nebenverurteilungsscore,
        vorbestraft,
        vorbestraft_einschlaegig,
    ]

    urteilsmerkmale_als_pandas_df = pd.DataFrame(
        [liste_mit_urteilsmerkmalen],
        columns=[
            "hauptdelikt",
            "mehrfach",
            "gewerbsmaessig",
            "bandenmaessig",
            "deliktssumme",
            "nebenverurteilungsscore",
            "vorbestraft",
            "vorbestraft_einschlaegig",
        ],
    )
    urteilsmerkmale_als_pandas_df = vermoegensstrafrechts_urteile_codes_aufloesen(
        urteilsmerkmale_als_pandas_df
    )
    encoder = kimodell_von_pickle_file_aus_aws_bucket_laden(
        "encoders/one_hot_encoder_fuer_rf_regr_val.pkl"
    )
    cat_fts_onehot = encoder.transform(urteilsmerkmale_als_pandas_df[cat_fts])
    enc_cat_fts_names = encoder.get_feature_names_out(cat_fts)
    df_cat_fts = pd.DataFrame(cat_fts_onehot, columns=enc_cat_fts_names)
    urteilsmerkmale_df_preprocessed = pd.concat(
        [df_cat_fts, urteilsmerkmale_als_pandas_df[num_fts]], axis=1
    )

    nachbarobjekt.vorhersage_strafmass = strafmass_estimator.predict(
        urteilsmerkmale_df_preprocessed
    )[0]

    sanktion_des_prajudiz = (
        nachbarobjekt.freiheitsstrafe_in_monaten
        if nachbarobjekt.freiheitsstrafe_in_monaten > 0
        else (nachbarobjekt.anzahl_tagessaetze / 30)
    )

    differenz = sanktion_des_prajudiz - nachbarobjekt.vorhersage_strafmass
    if 3 > differenz > -3:
        nachbarobjekt.sanktionsbewertung = (
            "Die KI hält die Sanktion des Präjudiz für angemessen."
        )
    elif -10 <= differenz <= -3:
        nachbarobjekt.sanktionsbewertung = (
            "Die KI hält die Sanktion des Präjudiz für leicht zu mild."
        )
    elif differenz <= -10:
        nachbarobjekt.sanktionsbewertung = (
            "Die KI hält die Sanktion des Präjudiz für erheblich zu mild."
        )
    elif 3 <= differenz <= 10:
        nachbarobjekt.sanktionsbewertung = (
            "Die KI hält die Sanktion des Präjudiz für leicht zu streng."
        )
    elif differenz > 10:
        nachbarobjekt.sanktionsbewertung = (
            "Die KI hält die Sanktion des Präjudiz für erheblich zu streng."
        )

    nachbarobjekt.vorhersage_vollzug = vollzug_estimator.predict(
        urteilsmerkmale_df_preprocessed
    )

    nachbarobjekt.vorhersage_sanktionsart = hauptsanktion_estimator.predict(
        urteilsmerkmale_df_preprocessed
    )

    nachbarobjekt.vollzugsstring = "empty"

    if nachbarobjekt.vorhersage_vollzug[0] == "0":
        nachbarobjekt.vollzugsstring = "bedingte"
    elif nachbarobjekt.vorhersage_vollzug[0] == "1":
        nachbarobjekt.vollzugsstring = "teilbedingte"
    elif nachbarobjekt.vorhersage_vollzug[0] == "2":
        nachbarobjekt.vollzugsstring = "unbedingte"

    nachbarobjekt.string_sanktionsart = "empty"

    if nachbarobjekt.vorhersage_sanktionsart[0] == "0":
        nachbarobjekt.string_sanktionsart = "Freiheitsstrafe"
    elif nachbarobjekt.vorhersage_sanktionsart[0] == "1":
        nachbarobjekt.string_sanktionsart = "Geldstrafe"
    elif nachbarobjekt.vorhersage_sanktionsart[0] == "2":
        nachbarobjekt.string_sanktionsart = "Busse"

    return nachbarobjekt


def betm_nachbarobjekt_mit_sanktionsbewertung_anreichern(
    nachbarobjekt, strafmass_estimator, hauptsanktion_estimator, vollzug_estimator
):
    allgemeine_prognosemerkmale = {
        "fall_nr": nachbarobjekt.fall_nr,
        "mengenmaessig": nachbarobjekt.mengenmaessig,
        "bandenmaessig": nachbarobjekt.bandenmaessig,
        "gewerbsmaessig": nachbarobjekt.gewerbsmaessig,
        "anstaltentreffen": nachbarobjekt.anstaltentreffen,
        "mehrfach": nachbarobjekt.mehrfach,
        "beschaffungskriminalitaet": nachbarobjekt.beschaffungskriminalitaet,
        "deliktsdauer_in_monaten": nachbarobjekt.deliktsdauer_in_monaten,
        "nebenverurteilungsscore": nachbarobjekt.nebenverurteilungsscore,
        "vorbestraft": nachbarobjekt.vorbestraft,
        "vorbestraft_einschlaegig": nachbarobjekt.vorbestraft_einschlaegig,
        "deliktsertrag": nachbarobjekt.deliktsertrag,
        "rolle": nachbarobjekt.rolle,
    }

    # wenn die typen nicht string gibt, gibt es später probleme beim groupby agg
    def _convert_django_types_to_string(dict_):
        for key, value in dict_.items():
            if value is not None and not isinstance(value, (bool, float, str, int)):
                dict_[key] = value.name
        return dict_

    allgemeine_prognosemerkmale = _convert_django_types_to_string(
        allgemeine_prognosemerkmale
    )

    # Get all related Betm objects for nachbarobjekt
    related_betms = nachbarobjekt.betm.all()

    _betm_dict = {}
    for i, betm_eintrag in enumerate(related_betms):
        _betm_dict[i] = {
            "betm_art": betm_eintrag.art,
            "menge_in_g": betm_eintrag.menge_in_g,
            "rein": betm_eintrag.rein,
        }

    _betm_dict[0] = _convert_django_types_to_string(_betm_dict[0])
    if 1 in _betm_dict:
        _betm_dict[1] = _convert_django_types_to_string(_betm_dict[1])
    if 2 in _betm_dict:
        _betm_dict[2] = _convert_django_types_to_string(_betm_dict[2])

    # weitermachen TODO
    list_betm = []
    for entry in _betm_dict.values():
        list_betm.append(entry)
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
    liste_der_betmarten_strings = [betmart.name for betmart in liste_der_betmarten]

    df_prognosewerte_ohe, list_ohe_betm_columns = betmurteile_onehotencoding(
        pd_df_mit_prognosewerten,
        liste_der_betmarten=liste_der_betmarten_strings,
    )
    df_prognosewerte_ohe.drop(labels=["betm_art", "menge_in_g"], axis=1, inplace=True)
    df_prognosewerte_ohe_grouped = betmurteile_zusammenfuegen(
        pd_df=df_prognosewerte_ohe,
        liste_aller_ohe_betm_spalten=list_ohe_betm_columns,
    )

    # onehotencoding
    encoder = kimodell_von_pickle_file_aus_aws_bucket_laden("encoders/betm_encoder.pkl")
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

    prognosemerkmale_df_preprocessed = pd.concat([df_cat_fts, df_num_fts], axis=1)
    # Hauptsanktion-Prädiktor laden und Prognose machen
    vorhersage_hauptsanktion = hauptsanktion_estimator.predict(
        prognosemerkmale_df_preprocessed
    )[0]

    if vorhersage_hauptsanktion == "0":
        vorhersage_hauptsanktion = "Freiheitsstrafe"
    elif vorhersage_hauptsanktion == "1":
        vorhersage_hauptsanktion = "Geldstrafe"
    elif vorhersage_hauptsanktion == "2":
        vorhersage_hauptsanktion = "Busse"

    nachbarobjekt.vorhersage_hauptsanktion = vorhersage_hauptsanktion

    # Vollzugs-Prädiktor laden und Prognose machen

    vorhersage_vollzug = vollzug_estimator.predict(prognosemerkmale_df_preprocessed)[0]

    if vorhersage_vollzug == "bedingt":
        vorhersage_vollzug = "bedingte"
    elif vorhersage_vollzug == "teilbedingt":
        vorhersage_vollzug = "teilbedingte"
    elif vorhersage_vollzug == "unbedingt":
        vorhersage_vollzug = "unbedingte"

    nachbarobjekt.vorhersage_vollzug = vorhersage_vollzug


    # Strafmass-Prädiktor laden und Prognose machen
    vorhersage_strafmass = strafmass_estimator.predict(prognosemerkmale_df_preprocessed)[0]
    nachbarobjekt.vorhersage_strafmass = vorhersage_strafmass

    return nachbarobjekt


def introspection_plot_und_lesehinweis_ausgeben(
    db_model=Urteil, xlim=1000000, titel="Prognose", cleaned_data_dict=None
):
    def qs_to_df(db_model=Urteil):
        qs = db_model.objects.all()
        q = qs.values()
        df = pd.DataFrame.from_records(q)
        return df

    urteile_df = qs_to_df(db_model)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(
        data=urteile_df[urteile_df["hauptdelikt"] == "Betrug"],
        x="deliktssumme",
        y="freiheitsstrafe_in_monaten",
        label="Urteile Betrug",
        alpha=0.3,
    )
    ax.scatter(
        data=urteile_df[urteile_df["hauptdelikt"] == "Veruntreuung"],
        x="deliktssumme",
        y="freiheitsstrafe_in_monaten",
        label="Urteile Veruntreuung",
        alpha=0.3,
    )
    ax.scatter(
        data=urteile_df[urteile_df["hauptdelikt"] == "ung. Geschäftsbesorgung"],
        x="deliktssumme",
        y="freiheitsstrafe_in_monaten",
        label="Urteile ung. Geschäftsbesorgung",
        alpha=0.3,
    )
    ax.scatter(
        data=urteile_df[urteile_df["hauptdelikt"] == "betr. Missbrauch DVA"],
        x="deliktssumme",
        y="freiheitsstrafe_in_monaten",
        label="Urteile betr. Missbrauch DVA",
        alpha=0.3,
    )
    ax.scatter(
        data=urteile_df[urteile_df["hauptdelikt"] == "Diebstahl"],
        x="deliktssumme",
        y="freiheitsstrafe_in_monaten",
        label="Diebstahl",
        alpha=0.3,
    )

    ax.set_xlabel("Deliktssumme in Fr.")
    ax.set_xlim([-10000, xlim])
    ax.set_xticks(np.arange(0, xlim, (xlim / 10)))
    ax.set_ylabel("(prognostiziertes) Strafmass in Monaten")
    ax.set_title(titel)

    if cleaned_data_dict is None:
        geschlecht = 0
        mehrfach = False
        gewerbsmaessig = False
        bandenmaessig = False
        nebenverurteilungsscore = 0
        vorbestraft = False
        vorbestraft_einschlaegig = False

    else:
        geschlecht = cleaned_data_dict["geschlecht"]
        mehrfach = cleaned_data_dict["mehrfach"]
        gewerbsmaessig = cleaned_data_dict["gewerbsmaessig"]
        bandenmaessig = cleaned_data_dict["bandenmaessig"]
        nebenverurteilungsscore = cleaned_data_dict["nebenverurteilungsscore"]
        vorbestraft = cleaned_data_dict["vorbestraft"]
        vorbestraft_einschlaegig = cleaned_data_dict["vorbestraft_einschlaegig"]

    strafmass_model = pickle.load(open("database/ai-model/model.pkl", "rb"))

    def prognosen_generator(hauptdelikt="Betrug"):
        prognosen = []
        for deliktssumme in np.arange(1, stop=xlim, step=xlim / 50):
            liste_mit_urteilsmerkmalen = [
                geschlecht,
                hauptdelikt,
                mehrfach,
                gewerbsmaessig,
                bandenmaessig,
                deliktssumme,
                nebenverurteilungsscore,
                vorbestraft,
                vorbestraft_einschlaegig,
            ]
            urteilsmerkmale_als_pandas_df = pd.DataFrame(
                np.array([liste_mit_urteilsmerkmalen]),
                columns=[
                    "Geschlecht",
                    "Hauptdelikt",
                    "mehrfach",
                    "gewerbsmaessig",
                    "bandenmaessig",
                    "Deliktssumme",
                    "Nebenverurteilungsscore",
                    "vorbestraft",
                    "einschlaegig vorbestraft",
                ],
            )
            urteilsmerkmale_df_preprocessed = preprocessing_x(
                urteilsmerkmale_als_pandas_df
            )
            vorhersage_strafmass = strafmass_model.predict(
                urteilsmerkmale_df_preprocessed
            )
            prognosen.append(vorhersage_strafmass)
        return prognosen

    def lesehinweis_generator(
        mehrfach=mehrfach,
        gewerbsmaessig=gewerbsmaessig,
        bandenmaessig=bandenmaessig,
        nebenverurteilungsscore=nebenverurteilungsscore,
        vorbestraft=vorbestraft,
        vorbestraft_einschlaegig=vorbestraft_einschlaegig,
    ):
        html_string = (
            f"<p>Der Liniengraph bzw. Prognose-Plot bildet die Prognose bei unterschiedlichen Deliktssummen ab, wenn die übrigen "
            f"Sachverhaltsmerkmale – ceteribus paribus – wie folgt bestehen bleiben: </p>"
            f"<li>mehrfache Tatbegehung: "
            f'{"zutreffend" if mehrfach is True else "nicht zutreffend"}, </li>'
            f"<li>gewerbsmässige Tatbegehung: "
            f'{"zutreffend" if gewerbsmaessig is True else "nicht zutreffend"}, </li>'
            f"<li>bandenmässige Tatbegehung: "
            f'{"zutreffend" if bandenmaessig is True else "nicht zutreffend"}, </li>'
            f"<li>Nebenverurteilungsscore: "
            f"{str(nebenverurteilungsscore)}, </li>"
            f"<li>Vorbestraft: "
            f'{"zutreffend" if vorbestraft is True else "nicht zutreffend"}, </li>'
            f"<li>Einschlägig vorbestraft: "
            f'{"zutreffend" if vorbestraft_einschlaegig is True else "nicht zutreffend"} </li></ul>'
        )
        return html_string

    lesehinweis = lesehinweis_generator(
        mehrfach=mehrfach,
        gewerbsmaessig=gewerbsmaessig,
        bandenmaessig=bandenmaessig,
        nebenverurteilungsscore=nebenverurteilungsscore,
        vorbestraft=vorbestraft,
        vorbestraft_einschlaegig=vorbestraft_einschlaegig,
    )

    prognosen_betrugsdelikt = prognosen_generator(hauptdelikt="Betrug")
    prognosen_veruntreuungsdelikt = prognosen_generator(hauptdelikt="Veruntreuung")
    prognosen_gbdelikt = prognosen_generator(hauptdelikt="ung. Geschäftsbesorgung")
    prognosen_dva = prognosen_generator(hauptdelikt="betr. Missbrauch DVA")
    prognosen_diebstahl = prognosen_generator(hauptdelikt="Diebstahl")
    ax.plot(
        np.arange(1, stop=xlim, step=xlim / 50),
        prognosen_betrugsdelikt,
        label="Prognose Betrug",
    )
    ax.plot(
        np.arange(1, stop=xlim, step=xlim / 50),
        prognosen_veruntreuungsdelikt,
        label="Prognose Veruntreuung",
    )
    ax.plot(
        np.arange(1, stop=xlim, step=xlim / 50),
        prognosen_gbdelikt,
        label="Prognose ung. Geschäftsbesorgung",
    )
    ax.plot(
        np.arange(1, stop=xlim, step=xlim / 50),
        prognosen_dva,
        label="Prognosen betr. Missbrauch DVA",
    )
    ax.plot(
        np.arange(1, stop=xlim, step=xlim / 50),
        prognosen_diebstahl,
        label="Prognosen Diebstahl",
    )
    ax.legend(loc="best")

    imgdata = StringIO()
    fig.savefig(imgdata, format="svg")
    imgdata.seek(0)

    data = imgdata.getvalue()
    return data, lesehinweis


def introspection_plot_und_lesehinweis_abspeichern(
    db_model=Urteil, xlim=1000000, titel="Prognose", cleaned_data_dict=None
):
    def qs_to_df(db_model=Urteil):
        qs = db_model.objects.all()
        q = qs.values()
        df = pd.DataFrame.from_records(q)
        return df

    urteile_df = qs_to_df(db_model)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(
        data=urteile_df[urteile_df["hauptdelikt"] == "Betrug"],
        x="deliktssumme",
        y="freiheitsstrafe_in_monaten",
        label="Urteile Betrug",
        alpha=0.3,
    )
    # ax.scatter(data=urteile_df[urteile_df['hauptdelikt'] == 'Veruntreuung'], x='deliktssumme',
    #            y='freiheitsstrafe_in_monaten', label='Urteile Veruntreuung', alpha=0.3)
    # ax.scatter(data=urteile_df[urteile_df['hauptdelikt'] == 'ung. Geschäftsbesorgung'], x='deliktssumme',
    #            y='freiheitsstrafe_in_monaten', label='Urteile ung. Geschäftsbesorgung', alpha=0.3)
    # ax.scatter(data=urteile_df[urteile_df['hauptdelikt'] == 'betr. Missbrauch DVA'], x='deliktssumme',
    #            y='freiheitsstrafe_in_monaten', label='Urteile betr. Missbrauch DVA', alpha=0.3)
    ax.scatter(
        data=urteile_df[urteile_df["hauptdelikt"] == "Diebstahl"],
        x="deliktssumme",
        y="freiheitsstrafe_in_monaten",
        label="Diebstahl",
        alpha=0.3,
    )

    ax.set_xlabel("Deliktssumme in Fr.")
    ax.set_xlim([-10000, xlim])
    ax.set_xticks(np.arange(0, xlim, (xlim / 10)))
    ax.set_ylabel("Strafmass in Monaten")
    ax.set_title(titel)

    if cleaned_data_dict is None:
        geschlecht = 0
        mehrfach = False
        gewerbsmaessig = False
        bandenmaessig = False
        nebenverurteilungsscore = 0
        vorbestraft = False
        vorbestraft_einschlaegig = False

    else:
        geschlecht = cleaned_data_dict["geschlecht"]
        mehrfach = cleaned_data_dict["mehrfach"]
        gewerbsmaessig = cleaned_data_dict["gewerbsmaessig"]
        bandenmaessig = cleaned_data_dict["bandenmaessig"]
        nebenverurteilungsscore = cleaned_data_dict["nebenverurteilungsscore"]
        vorbestraft = cleaned_data_dict["vorbestraft"]
        vorbestraft_einschlaegig = cleaned_data_dict["vorbestraft_einschlaegig"]

    strafmass_model = kimodell_von_pickle_file_aus_aws_bucket_laden(
        "pickles/random_forest_regressor_val_fts.pkl"
    )

    step = xlim / 25

    def prognosen_generator(hauptdelikt="Betrug", nebenverurteilungsscore=0):
        prognosen = []
        for deliktssumme in np.arange(1, stop=xlim, step=step):
            fts_dict = {
                "geschlecht": geschlecht,
                "mehrfach": mehrfach,
                "gewerbsmaessig": gewerbsmaessig,
                "bandenmaessig": bandenmaessig,
                "deliktssumme": deliktssumme,
                "nebenverurteilungsscore": nebenverurteilungsscore,
                "vorbestraft": vorbestraft,
                "vorbestraft_einschlaegig": vorbestraft_einschlaegig,
                "hauptdelikt": hauptdelikt,
            }
            urteilsmerkmale_als_pandas_df_ohe = (
                formulareingaben_in_abfragesample_konvertieren(fts_dict)
            )
            vorhersage_strafmass = strafmass_model.predict(
                urteilsmerkmale_als_pandas_df_ohe
            )
            prognosen.append(vorhersage_strafmass)
        return prognosen

    def lesehinweis_generator(
        mehrfach=mehrfach,
        gewerbsmaessig=gewerbsmaessig,
        bandenmaessig=bandenmaessig,
        nebenverurteilungsscore=nebenverurteilungsscore,
        vorbestraft=vorbestraft,
        vorbestraft_einschlaegig=vorbestraft_einschlaegig,
    ):
        html_string = (
            f"<p>Der Liniengraph bildet die Prognose bei unterschiedlichen Deliktssummen ab, wenn die übrigen "
            f"Sachverhaltsmerkmale – ceteribus paribus – wie folgt bestehen bleiben: </p>"
            f"<ul>"
            f"<li>mehrfache Tatbegehung: "
            f'{"zutreffend" if mehrfach is True else "nicht zutreffend"}, </li>'
            f"<li>gewerbsmässige Tatbegehung: "
            f'{"zutreffend" if gewerbsmaessig is True else "nicht zutreffend"}, </li>'
            f"<li>bandenmässige Tatbegehung: "
            f'{"zutreffend" if bandenmaessig is True else "nicht zutreffend"}, </li>'
            f"<li>Nebenverurteilungsscore: "
            f"{str(nebenverurteilungsscore)}, </li>"
            f"<li>Vorbestraft: "
            f'{"zutreffend" if vorbestraft is True else "nicht zutreffend"}, </li>'
            f"<li>Einschlägig vorbestraft: "
            f'{"zutreffend" if vorbestraft_einschlaegig is True else "nicht zutreffend"} </li></ul>'
        )

        return html_string

    lesehinweis = lesehinweis_generator(
        mehrfach=mehrfach,
        gewerbsmaessig=gewerbsmaessig,
        bandenmaessig=bandenmaessig,
        nebenverurteilungsscore=nebenverurteilungsscore,
        vorbestraft=vorbestraft,
        vorbestraft_einschlaegig=vorbestraft_einschlaegig,
    )

    prognosen_betrugsdelikt = prognosen_generator(hauptdelikt="Betrug")
    prognosen_betrugsdelikt_6 = prognosen_generator(
        hauptdelikt="Betrug", nebenverurteilungsscore=6
    )
    # prognosen_veruntreuungsdelikt = prognosen_generator(hauptdelikt='Veruntreuung')
    # prognosen_gbdelikt = prognosen_generator(hauptdelikt='ung. Geschäftsbesorgung')
    # prognosen_dva = prognosen_generator(hauptdelikt='betr. Missbrauch DVA')
    prognosen_diebstahl = prognosen_generator(hauptdelikt="Diebstahl")
    prognosen_diebstahl_6 = prognosen_generator(
        hauptdelikt="Diebstahl", nebenverurteilungsscore=6
    )
    ax.plot(
        np.arange(1, stop=xlim, step=step),
        prognosen_betrugsdelikt,
        label="Prognose Betrug",
    )
    ax.plot(
        np.arange(1, stop=xlim, step=step),
        prognosen_betrugsdelikt_6,
        label="Prognose Betrug (NVS 6)",
    )
    # ax.plot(np.arange(1, stop=xlim, step=xlim/50), prognosen_veruntreuungsdelikt, label='Prognose Veruntreuung')
    # ax.plot(np.arange(1, stop=xlim, step=xlim/50), prognosen_gbdelikt, label='Prognose ung. Geschäftsbesorgung')
    # ax.plot(np.arange(1, stop=xlim, step=xlim/50), prognosen_dva, label='Prognosen betr. Missbrauch DVA')
    ax.plot(
        np.arange(1, stop=xlim, step=step),
        prognosen_diebstahl,
        label="Prognosen Diebstahl",
    )
    ax.plot(
        np.arange(1, stop=xlim, step=step),
        prognosen_diebstahl_6,
        label="Prognosen Diebstahl (NVS 6)",
    )
    ax.legend(loc="best")

    imgdata = BytesIO()
    fig.savefig(imgdata, format="svg")
    content_file = ContentFile(imgdata.getvalue())
    obj, created = DiagrammSVG.objects.get_or_create(name=f"introspection_plot")
    obj.file.save(f"introspection_plot.svg", content_file)
    obj.lesehinweis = lesehinweis
    obj.save()


# Betm-Pipeline
def betm_urteile_dataframe_erzeugen():
    """erzeugt ein pandas datenframe mit den in der BetmUrteil abgelegten Daten"""
    df_joined = betm_db_zusammenfuegen()
    df_joined = urteilcodes_aufloesen(df_joined)
    df_joined = urteilsdatum_in_urteilsjahr_konvertieren(df_joined)
    df_joined, liste_aller_ohe_betm_spalten = betmurteile_onehotencoding(df_joined)
    df_urteile = betmurteile_zusammenfuegen(
        df_joined, liste_aller_ohe_betm_spalten=liste_aller_ohe_betm_spalten
    )
    df_urteile = betmurteile_fehlende_werte_auffuellen(df_urteile)

    return df_urteile, liste_aller_ohe_betm_spalten


def betm_db_zusammenfuegen():
    """fügt alle datenbanken betreffend Betm-Urteile zusammen"""
    df_betmurteil = BetmUrteil.pandas.return_as_df(exclude_unmarked=False)
    df_betmurteil["betmurteil_id"] = df_betmurteil.index
    df_betmurteil_betm = pd.DataFrame(list(BetmUrteil.betm.through.objects.values()))
    df_betm = Betm.pandas.return_as_df()
    df_betmart = BetmArt.pandas.return_as_df()
    df_kanton = Kanton.pandas.return_as_df()
    df_rolle = Rolle.pandas.return_as_df()
    df_joined = df_betmurteil.merge(df_betmurteil_betm, on="betmurteil_id")
    df_joined = df_joined.drop(columns="id")
    df_joined = df_joined.merge(df_betm, left_on="betm_id", right_index=True)
    df_joined = df_joined.merge(df_betmart, left_on="art_id", right_index=True)
    df_joined = df_joined.merge(df_rolle, left_on="rolle_id", right_index=True)
    df_joined = df_joined.merge(df_kanton, left_on="kanton_id", right_index=True)

    df_joined = df_joined.drop(
        ["art_id", "betm_id", "rolle_id", "kanton_id"],
        axis=1,
    )
    umbenennungsdict = {"name_x": "betm_art", "name_y": "rolle", "abk": "kanton"}

    df_joined = df_joined.rename(columns=umbenennungsdict)
    df_joined.index = df_joined["betmurteil_id"]

    return df_joined


def urteilcodes_aufloesen(dataframe):
    """Paraphrasiert codiert abgespeicherte Variablen"""
    if "geschlecht" in dataframe.columns:
        dataframe.replace(
            {"geschlecht": {"0": "männlich", "1": "weiblich"}}, inplace=True
        )
    if "nationalitaet" in dataframe.columns:
        dataframe.replace(
            {
                "nationalitaet": {
                    "0": "Schweizerin/Schweizer",
                    "1": "Ausländerin/Ausländer",
                    "2": "unbekannt",
                }
            },
            inplace=True,
        )
    if "vollzug" in dataframe.columns:
        dataframe.replace(
            {"vollzug": {"0": "bedingt", "1": "teilbedingt", "2": "unbedingt"}},
            inplace=True,
        )

    if "hauptsanktion" in dataframe.columns:
        dataframe.replace(
            {
                "hauptsanktion": {
                    "0": "Freiheitsstrafe",
                    "1": "Geldstrafe",
                    "2": "Busse",
                }
            },
            inplace=True,
        )
    return dataframe


def urteilsdatum_in_urteilsjahr_konvertieren(dataframe: pd.DataFrame) -> pd.DataFrame:
    """urteilsjahr ist eine brauchbarere Variable als Urteilsjahr"""
    if "urteilsdatum" in dataframe.columns:
        dataframe["urteilsdatum"] = pd.to_datetime(dataframe["urteilsdatum"])
        dataframe["urteilsdatum"] = dataframe["urteilsdatum"].map(lambda a: a.year)
        dataframe = dataframe.rename(columns={"urteilsdatum": "urteilsjahr"})
    return dataframe


def betmurteile_onehotencoding(pd_df, liste_der_betmarten=None):
    """
    pd_df: pandas Datenframe
    liste_der_betmarten: muss ein einzelnes (Abfrage-)sample konvertiert werden muss die Liste aller
        Betäubungsmittelarten mitgegeben werden, um das Sample deckungsgleich wie die Trainingswerte zu machen.
        wenn für liste_der_betmarten keine Liste eingegeben wird, wird eine solche anhand der spalte "betm_art" des
        pandas datenframe erstellt
    """
    _liste_aller_onehotencoded_betm_spalten = []
    if liste_der_betmarten is None:
        liste_der_betmarten = pd_df.betm_art.unique()
    else:
        liste_der_betmarten = liste_der_betmarten
    for betmart in liste_der_betmarten:
        # neue Spalten erstellen
        pd_df[f"{betmart}_gemisch"] = 0
        # folgende Spalte auskommentiert, weil diese gemisch spalte bei aggregate_faelle wieder gelöscht wird
        # _liste_aller_onehotencoded_betm_spalten.append(f'{betmart}_gemisch')
        pd_df[f"{betmart}_rein"] = 0
        _liste_aller_onehotencoded_betm_spalten.append(f"{betmart}_rein")

        for index, row in pd_df.iterrows():
            if row["betm_art"] == betmart and row["rein"] is True:
                pd_df.at[index, f"{betmart}_rein"] = row["menge_in_g"]

            if row["betm_art"] == betmart and row["rein"] is False:
                pd_df.at[index, f"{betmart}_gemisch"] = row["menge_in_g"]
    return pd_df, _liste_aller_onehotencoded_betm_spalten


def betmurteile_zusammenfuegen(pd_df, liste_aller_ohe_betm_spalten):
    """Urteile, die mehrere Betmarten zum Gegenstand haben, werden aus der Datenbank mit mehreren Zeilen ausgegeben.
    Diese müssen zusammengefügt werden."""
    # dict erstellen, welches jeder spalte einzeln die aggreggierungsfunktion zuweist
    _agg_dict = {}
    restliche_spalten = [
        i for i in pd_df.columns if i not in liste_aller_ohe_betm_spalten
    ]
    for ohe_betm_spalte in liste_aller_ohe_betm_spalten:
        _agg_dict[ohe_betm_spalte] = "sum"
    for column_name in restliche_spalten:
        _agg_dict[column_name] = "max"
    dtypes = pd_df.dtypes
    # agg funktion macht nur einen summenmässige aggregation auf den columns, die im _agg_dict bezeichnet worden sind
    grouped_pd_df = pd_df.groupby(["fall_nr"]).agg(_agg_dict)
    # gemisch zu 1/3 auf rein aufrechnen, gemisch Spalte löschen
    if "betm_art" in pd_df:
        for betmart in pd_df.betm_art.unique():
            grouped_pd_df[f"{betmart}_rein"] = (
                grouped_pd_df[f"{betmart}_rein"]
                + grouped_pd_df[f"{betmart}_gemisch"] / 3
            )
            grouped_pd_df.drop([f"{betmart}_gemisch"], axis=1, inplace=True)
    else:
        # split('_')[0] gibt alles vor dem underscore aus
        # dieses else ist für die prognosesamples nötig, weil die spalte betm_art vorher gelöscht wurde, da es mit
        # dieser Spalte mutmasslich Probleme beim aggreggieren gab (unterschiedliche typen)
        betmart_liste = [entry.split("_")[0] for entry in liste_aller_ohe_betm_spalten]
        for betmart in betmart_liste:
            grouped_pd_df[f"{betmart}_rein"] = (
                grouped_pd_df[f"{betmart}_rein"]
                + grouped_pd_df[f"{betmart}_gemisch"] / 3
            )
            grouped_pd_df.drop([f"{betmart}_gemisch"], axis=1, inplace=True)
    return grouped_pd_df


def betmurteile_fehlende_werte_auffuellen(pd_df, spalten_mit_fehlenden_werten=None):
    """Die prognosmerkmale 'Deliktsdauer_in_monaten' und "deliktsertrag" sind grösstenteils nicht bekannt,
    bei fehlenden werten mit 1 auffüllen.
    (da die Deliktsdauer und der Deliktsertrag offensichtlich nicht nennenswert waren)
    pd_df: Pandas Datenframe
    spalten_mit_fehlenden_werten: liste der Spalten, bei denen fehlende Werte auf 1 aufgefüllt werden sollen, default=
    ["deliktdauer_in_monaten", "deliktsertrag"]
    return: Pandas Datenframe mit aufgefüllten Werten
    """
    if spalten_mit_fehlenden_werten is None:
        spalten_mit_fehlenden_werten = ["deliktsdauer_in_monaten", "deliktsertrag"]

    from sklearn.impute import SimpleImputer

    imputer = SimpleImputer(missing_values=np.nan, strategy="constant", fill_value=1)
    pd_df[spalten_mit_fehlenden_werten] = imputer.fit_transform(
        pd_df[spalten_mit_fehlenden_werten]
    )

    return pd_df


def onehotx_und_y_erstellen_from_dataframe(
    pandas_dataframe,
    categorial_ft_dbfields=None,
    numerical_ft_dbfields=None,
    target_dbfields=None,
    return_encoder=False,
):
    """
    :param pandas_dataframe: ein Pandas Datenframe
    :param categorial_ft_dbfields: eine Liste mit den kategorialen Datenbank-Feldern
    :param numerical_ft_dbfields: eine Liste mit den numerischen Datenbank-Feldern
    :param target_dbfields: eine Liste mit der Zielvariable(n)
    :param return_encoder: gibt encoder zurück, um diesen bei einem ki-modell abzuspeichern
    :return: x (Pandas-Datenframe, 1hot encoded), y (np_array)
    """

    fall_nr_index = pandas_dataframe.index

    # 1hot encoding der kategorialen variablen
    encoder = OneHotEncoder(drop="if_binary", sparse_output=False)
    encoder.fit(pandas_dataframe[categorial_ft_dbfields])
    categorical_1hot = encoder.transform(pandas_dataframe[categorial_ft_dbfields])
    encoder_categorical_ft_names = encoder.get_feature_names_out(categorial_ft_dbfields)
    df_categorical_1hot = pd.DataFrame(
        categorical_1hot, columns=encoder_categorical_ft_names, index=fall_nr_index
    )

    # für numerische features eine pandas df mit selbem index kreieren
    dataframe_mit_numerischen_werten_und_fallnr_index = pd.DataFrame(
        pandas_dataframe[numerical_ft_dbfields], index=fall_nr_index
    )

    # df der 1hot-kodierten features mit df der numerischen features zusammenfügen
    x = pd.concat(
        [df_categorical_1hot, dataframe_mit_numerischen_werten_und_fallnr_index], axis=1
    )

    # y erstellen
    if len(target_dbfields) == 1:
        # TODO bei freiheitsstrafe_in_monaten == 0 muss wert der anzahl_tagessaetze genommen werden
        y = pandas_dataframe[target_dbfields].values.ravel()
    elif len(target_dbfields) > 1:
        y = pandas_dataframe[target_dbfields]

    if return_encoder:
        return x, y, encoder
    else:
        return x, y


def merkmalswichtigkeitslistegenerator(instanzierter_estimator):
    """Gibt eine sortierte Liste mit der vom KI-Modell eruierten Merkmalswichtigkeit aus"""
    _liste_mit_merkmalswichtigkeiten = list(
        zip(
            instanzierter_estimator.feature_names_in_,
            instanzierter_estimator.feature_importances_,
        )
    )
    _sortierte_liste_mit_merkmalswichtigkeiten = sorted(
        _liste_mit_merkmalswichtigkeiten,
        key=lambda merkmal_wichtigkeit_tuple: merkmal_wichtigkeit_tuple[1],
        reverse=True,
    )
    _sortierte_liste_mit_merkmalswichtigkeiten = [
        (merkmal_wichtigkeit_tuple[0], round(merkmal_wichtigkeit_tuple[1] * 100, 3))
        for merkmal_wichtigkeit_tuple in _sortierte_liste_mit_merkmalswichtigkeiten
    ]
    return _sortierte_liste_mit_merkmalswichtigkeiten


def merkmale_in_merkmalswichtigkeitsliste_zusammenfassen(
    merkmalswichtigkeitsliste,
    liste_mit_zusammenfassenden_merkmalen,
    neuer_merkmalsname="Menge Betäubungsmittel",
):
    dict_mit_zusammengefasster_wichtigkeit = {neuer_merkmalsname: 0}
    for tuple_ in merkmalswichtigkeitsliste.copy():
        if tuple_[0] in liste_mit_zusammenfassenden_merkmalen:
            dict_mit_zusammengefasster_wichtigkeit[neuer_merkmalsname] += tuple_[1]
    merkmalswichtigkeitsliste.append(
        (neuer_merkmalsname, dict_mit_zusammengefasster_wichtigkeit[neuer_merkmalsname])
    )
    # neue Liste erstellen, in welche die zuvor zusammengefassten Merkmale nicht mitübernommen werden
    _zusammengefasste_merkmalswichtigkeitsliste = []
    for tuple_ in merkmalswichtigkeitsliste:
        if tuple_[0] not in liste_mit_zusammenfassenden_merkmalen:
            _zusammengefasste_merkmalswichtigkeitsliste.append(tuple_)
    # neu sortieren
    _sortierte_zusammengefasste_merkmalswichtigkeitsliste = sorted(
        _zusammengefasste_merkmalswichtigkeitsliste,
        key=lambda merkmal_wichtigkeit_tuple: merkmal_wichtigkeit_tuple[1],
        reverse=True,
    )
    # runden
    _sortierte_zusammengefasste_merkmalswichtigkeitsliste = [
        (merkmal_string, round(wichtigkeit, 2))
        for (
            merkmal_string,
            wichtigkeit,
        ) in _sortierte_zusammengefasste_merkmalswichtigkeitsliste
    ]
    return _sortierte_zusammengefasste_merkmalswichtigkeitsliste
