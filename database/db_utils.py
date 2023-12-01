from io import BytesIO, StringIO
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from .models import Urteil, DiagrammSVG
from django.core.files.base import ContentFile


def qs_to_df(model=Urteil):
    qs = model.objects.all()
    q = qs.values()
    df = pd.DataFrame.from_records(q)
    return df


def seaborn_statistik_erstellen(model=Urteil):
    df = qs_to_df(model)
    sns.set_theme()
    fig, ax = plt.subplots()
    sns_plot = sns.scatterplot(
                    data=df,
                    ax=ax,
                    x='deliktssumme',
                    y='freiheitsstrafe_in_monaten',
                    size='nebenverurteilungsscore'
                )
    ax.set_xlim([-2000, 100000])

    imgdata = StringIO()
    fig = sns_plot.get_figure()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)

    data = imgdata.getvalue()
    return data


def deliktssumme_strafhoehe_png_scatterplot_erstellen(model=Urteil, titel='Deliktssumme/Strafmass-Gegenüberstellung', xlim=1000000):
    urteile_bedingt = model.objects.filter(vollzug='0')
    urteile_teilbedingt = model.objects.filter(vollzug='1')
    urteile_unbedingt = model.objects.filter(vollzug='2')
    liste_mit_urteilshoehen_bedingt = [urteil.freiheitsstrafe_in_monaten for urteil in urteile_bedingt]
    liste_mit_deliktssummen_bedingt = [urteil.deliktssumme for urteil in urteile_bedingt]
    liste_mit_urteilshoehen_teilbedingt = [urteil.freiheitsstrafe_in_monaten for urteil in urteile_teilbedingt]
    liste_mit_deliktssummen_teilbedingt = [urteil.deliktssumme for urteil in urteile_teilbedingt]
    liste_mit_urteilshoehen_unbedingt = [urteil.freiheitsstrafe_in_monaten for urteil in urteile_unbedingt]
    liste_mit_deliktssummen_unbedingt = [urteil.deliktssumme for urteil in urteile_unbedingt]

    cmap = plt.get_cmap('tab20')
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(liste_mit_deliktssummen_bedingt, liste_mit_urteilshoehen_bedingt, color=cmap(2), label='bedingte Urteile')
    ax.scatter(liste_mit_deliktssummen_unbedingt, liste_mit_urteilshoehen_unbedingt, color=cmap(1), label='unbedingte Urteile')
    ax.scatter(liste_mit_deliktssummen_teilbedingt, liste_mit_urteilshoehen_teilbedingt, color=cmap(3), label='teilbedingte Urteile')
    ax.set_xlabel('Deliktssumme in Fr.')
    ax.set_xlim([-10000, xlim])
    ax.set_xticks(np.arange(0, xlim, (xlim/10)))
    ax.set_ylabel('Strafmass in Monaten')
    ax.set_title(titel)
    ax.legend(loc='lower right')

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)

    data = imgdata.getvalue()
    return data


def kategorie_scatterplot_erstellen(model=Urteil,
                                    kategorie_feld='vollzug',
                                    titel='Deliktssumme/Strafmass-Gegenüberstellung',
                                    xlim=1000000):
    df = model.pandas.return_as_df('deliktssumme', 'freiheitsstrafe_in_monaten', 'vorbestraft_einschlaegig', kategorie_feld)
    if kategorie_feld == 'nationalitaet':
        df['nationalitaet'].replace({'0': 'Schweizerin/Schweizer',
                                     '1': 'Ausländerin/Ausländer',
                                     '2': 'unbekannt'}, inplace=True)
    if kategorie_feld == 'geschlecht':
        df['geschlecht'].replace({'0': 'männlich',
                                  '1': 'weiblich'}, inplace=True)
    if kategorie_feld == 'vollzug':
        df['vollzug'].replace({'0': 'bedingt',
                               '1': 'teilbedingt',
                               '2': 'unbedingt'}, inplace=True)
    hauptdelikt_kategorien = list(df[kategorie_feld].value_counts().index)
    kat_dict = dict()
    for kategorie in hauptdelikt_kategorien:
        kat_dict[kategorie] = df[df[kategorie_feld] == kategorie]
    kat_dict.keys()

    markers = ["v", "^", "<", ">", "s", "*"]

    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(10, 5))

    for kategorie, marker in zip(kat_dict.keys(), markers[:len(kat_dict.keys())]):
        print(['red' if row else 'blue' for row in kat_dict[kategorie]['vorbestraft_einschlaegig']])
        ax.scatter(x=kat_dict[kategorie]['deliktssumme'],
                   y=kat_dict[kategorie]['freiheitsstrafe_in_monaten'],
                   #c=['red' if row else 'blue' for row in kat_dict[kategorie]['vorbestraft_einschlaegig']],
                   marker=marker,
                   label=kategorie)
    if kategorie_feld == 'vollzug':
        ax.hlines([24, 36], -10000, xlim, linestyles='dashed')
    ax.set_xlabel('Deliktssumme in Fr.')
    ax.set_xlim([-10000, xlim])
    ax.set_xticks(np.arange(0, xlim, (xlim / 10)))
    ax.set_ylabel('Strafmass in Monaten')
    ax.set_title(titel)
    ax.legend(loc='best')

    imgdata = BytesIO()
    fig.savefig(imgdata, format='svg')
    content_file = ContentFile(imgdata.getvalue())
    obj, created = DiagrammSVG.objects.get_or_create(name=f'{kategorie_feld}_scatterplot_{xlim}')
    obj.file.save(f'{kategorie_feld}_scatterplot_{xlim}.svg', content_file)
    obj.save()
    plt.close(fig)


