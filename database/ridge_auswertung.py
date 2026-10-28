"""
Empirische Auswertung der Strafhöhe mit einer Ridge-Regression, je Deliktsart.

Zweck: prüfen, welche erfassten Fallmerkmale in der Praxis mit der Strafhöhe
zusammenhängen, und daraus Werte je Kategorie ableiten - als Grundlage, um die
von Hand gesetzten Gewichte der geführten Präjudiziensuchen
(``praejudizfinder_sexual.js``/``praejudizfinder_gewalt.js``) empirisch zu
überprüfen. Die Methode ist für alle Deliktsarten dieselbe; was sich
unterscheidet (Merkmale, Gruppen, Suchkriterien), steht in einer Konfiguration
je Deliktsart (SEXUAL_KONFIG, GEWALT_KONFIG).

Die Auswertung läuft bei jedem Aufruf der Dev-Seite frisch auf dem aktuellen
Bestand (einige hundert Urteile, Rechenzeit rund eine Sekunde), damit sie neue
Einträge ohne separaten Kalibrierungsschritt berücksichtigt.

Herleitung in Kürze (ausführlich auf der Seite ``ridge_auswertung.html``):

- Zielgrösse ist der natürliche Logarithmus der Strafe in Monaten. Geldstrafen
  werden mit 30 Tagessätzen = 1 Monat umgerechnet (Art. 34 i.V.m. Art. 36 StGB).
  Der Logarithmus, weil Strafen rechtsschief verteilt sind und Merkmale eher
  proportional als additiv wirken (+20 % statt +6 Monate).
- Kategoriale Merkmale werden one-hot codiert; jede Kategorie erhält damit
  ihren eigenen Koeffizienten = ihren gelernten Wert.
- Ridge statt gewöhnlicher Regression, weil bei einigen hundert Urteilen und
  ~50 Merkmalsspalten seltene Kategorien sonst extreme Werte erhielten. Die
  Regularisierungsstärke alpha wird per Kreuzvalidierung gewählt.
"""

import math

import numpy as np
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.model_selection import RepeatedKFold, cross_val_predict

from django.urls import reverse

from .models import GewaltdeliktUrteil, SexualdeliktUrteil
from .praejudizfinder import artikel_aus_name

TAGESSAETZE_PRO_MONAT = 30
LEBENSLAENGLICH_PLATZHALTER = 999
ALPHAS = np.logspace(-2, 3, 30)
ZUFALLSSTARTWERT = 42
BOOTSTRAP_WIEDERHOLUNGEN = 300

# Kantone mit weniger Urteilen werden zu «übrige Kantone» zusammengefasst,
# sonst erhielte jeder Kleinkanton einen kaum belastbaren eigenen Koeffizienten.
MIN_URTEILE_KANTON = 20

ARTIKEL_TITEL = {
    "187": "Art. 187 Sex. Handlungen mit Kindern",
    "188": "Art. 188 Sex. Handlungen mit Abhängigen",
    "189": "Art. 189 Sexuelle Nötigung",
    "190": "Art. 190 Vergewaltigung",
    "191": "Art. 191 Schändung",
    "193": "Art. 193 Ausnützung einer Notlage",
    "196": "Art. 196 Sex. Handlungen mit Minderjährigen gegen Entgelt",
    "197": "Art. 197 Pornografie",
    "213": "Art. 213 Inzest",
}

OPFERALTER_LABEL = dict(SexualdeliktUrteil.OPFERALTER_CHOICES)

# Kriterien der Präjudiziensuchen werden über die Regressionsspalten
# abgebildet, die sie abdecken: (gruppe, None) = ganze Gruppe, (gruppe, label)
# = eine Spalte. Die Gewichte entsprechen dem Stand von PF_GEWICHTE bzw.
# PF_GEWALT_GEWICHTE und PF_BASIS_GEWICHTE in den JS-Komponenten und müssen
# bei einer Änderung dort von Hand nachgeführt werden.
BESONDERHEITEN_KRITERIEN = [
    {"titel": "verminderte Schuldfähigkeit", "gewicht": 5, "spalten": ("besonderheiten", "verminderte Schuldfähigkeit")},
    {"titel": "Geständnisrabatt", "gewicht": 5, "spalten": ("besonderheiten", "Geständnisrabatt")},
    {"titel": "jugendliche Täterschaft", "gewicht": 5, "spalten": ("besonderheiten", "jugendlicheR TäterIn")},
    {"titel": "Verletzung Beschleunigungsgebot", "gewicht": 5, "spalten": ("besonderheiten", "Verletzung Beschleunigungsgebot")},
]
# Kontrollvariablen: nur zur Einordnung, keine Suchkriterien. Nationalität und
# Geschlecht dürfen die Strafe rechtlich nicht beeinflussen (Art. 8 Abs. 2 BV);
# gerade deshalb stehen sie im Modell. Ein Unterschied bei sonst gleichen
# Merkmalen wäre ein Hinweis auf Ungleichbehandlung, und ohne sie könnte ein
# solcher Unterschied fälschlich verbundenen Merkmalen (Kanton, Vorstrafen)
# zugeschlagen werden.
KONTROLLE_KANTON = {"titel": "Kanton (Kontrollvariable, kein Suchkriterium)", "gewicht": None, "spalten": ("kanton", None)}
KONTROLLE_NATIONALITAET = {
    "titel": "Nationalität (Kontrollvariable, kein Suchkriterium)", "gewicht": None, "spalten": ("nationalitaet", None),
}
KONTROLLE_GESCHLECHT = {
    "titel": "Geschlecht (Kontrollvariable, kein Suchkriterium)", "gewicht": None, "spalten": ("geschlecht", None),
}
NATIONALITAET_LABEL = {"0": "Schweiz", "1": "Ausland", "2": "unbekannt"}
GESCHLECHT_LABEL = {"0": "männlich", "1": "weiblich"}


def _gemeinsame_merkmale(urteil, m, besonderheiten, kantone_einzeln):
    """
    Übrige Delikte, Vorstrafen, Besonderheiten und die Kontrollvariablen Kanton
    und Nationalität - bei allen Deliktsarten gleich. «unbekannt» ist eine
    eigene Kategorie: Die Nationalität wird nicht zufällig erwähnt (etwa bei der
    Prüfung einer Landesverweisung), darum wird sie nicht gedeutet.
    """
    m[("uebrige", "Deliktsscore (je Punkt)")] = urteil.deliktsscore_uebrige_delikte or 0
    if urteil.vorbestraft_einschlaegig:
        m[("vorstrafen", "einschlägig vorbestraft")] = 1
    elif urteil.vorbestraft:
        m[("vorstrafen", "nicht einschlägig vorbestraft")] = 1
    else:
        m[("vorstrafen", "nicht vorbestraft")] = 1
    namen = {b.name for b in urteil.besonderheiten.all()}
    for name in besonderheiten:
        m[("besonderheiten", name)] = int(name in namen)
    kanton = urteil.kanton.abk if urteil.kanton.abk in kantone_einzeln else "übrige Kantone"
    m[("kanton", kanton)] = 1
    m[("nationalitaet", NATIONALITAET_LABEL[urteil.nationalitaet])] = 1
    return m


# --- Sexualdelikte ---------------------------------------------------------------

SEXUAL_BESONDERHEITEN = (
    "Versuch",
    "verminderte Schuldfähigkeit",
    "Geständnisrabatt",
    "jugendlicheR TäterIn",
    "Verletzung Beschleunigungsgebot",
)


def _sexual_merkmale(urteil, kantone_einzeln):
    """
    Merkmale eines Sexualdelikt-Urteils als {(gruppe, spaltenlabel): wert}.

    Das Hauptdelikt wird nach Artikel zusammengefasst (alt- und neurechtliche
    Fassung gemeinsam), weil neurechtliche Urteile im Bestand noch zu selten
    sind, um einen eigenen Wert zu schätzen.
    """
    m = {}
    artikel = artikel_aus_name(urteil.hauptdelikt.name)
    m[("hauptdelikt", ARTIKEL_TITEL.get(artikel, f"Art. {artikel}"))] = 1
    m[("tatmittel", urteil.hauptdelikt_tatmittel.name)] = 1
    m[("opferalter", OPFERALTER_LABEL.get(urteil.hauptdelikt_opferalter, urteil.hauptdelikt_opferalter))] = 1
    m[("beziehung", urteil.hauptdelikt_taeter_opfer_beziehung)] = 1
    m[("mehrfach", "mehrfach begangen")] = int(urteil.hauptdelikt_mehrfachbegehung)
    for weitere in urteil.sexualdelikte_zusaetzliche.all():
        a = artikel_aus_name(weitere.name)
        m[("weitere", "zusätzlich " + ARTIKEL_TITEL.get(a, f"Art. {a}"))] = 1
    return _gemeinsame_merkmale(urteil, m, SEXUAL_BESONDERHEITEN, kantone_einzeln)


SEXUAL_KONFIG = {
    "key": "sexual",
    "titel": "Sexualdelikte",
    "queryset": lambda: SexualdeliktUrteil.objects.select_related(
        "hauptdelikt", "hauptdelikt_tatmittel", "kanton"
    ).prefetch_related("sexualdelikte_zusaetzliche", "besonderheiten"),
    "merkmale": _sexual_merkmale,
    "delikt_anzeige": lambda u: u.hauptdelikt.name + (", mehrfach" if u.hauptdelikt_mehrfachbegehung else ""),
    "detail_url": "sexualurteil_detail",
    "suche_url": "praejudizen_finden_sexual",
    "suche_js": "praejudizfinder_sexual.js",
    "suche_konstante": "PF_GEWICHTE",
    "gruppen": [
        {"key": "hauptdelikt", "titel": "Hauptdelikt"},
        {"key": "tatmittel", "titel": "Tatmittel"},
        {"key": "opferalter", "titel": "Opferalter"},
        {"key": "beziehung", "titel": "Täter-Opfer-Beziehung"},
        {"key": "mehrfach", "titel": "Mehrfache Begehung"},
        {"key": "weitere", "titel": "Weitere Sexualdelikte"},
        {"key": "uebrige", "titel": "Übrige Delikte (Deliktsscore)"},
        {"key": "vorstrafen", "titel": "Vorstrafen"},
        {"key": "besonderheiten", "titel": "Besonderheiten"},
        {"key": "kanton", "titel": "Kanton (Kontrollvariable)"},
        {"key": "nationalitaet", "titel": "Nationalität (Kontrollvariable)"},
    ],
    "kontrollen": [KONTROLLE_KANTON, KONTROLLE_NATIONALITAET],
    # Gruppen aus unabhängigen Ja/Nein- bzw. Zahlenmerkmalen: Wirkung gegenüber
    # «nein» bzw. je Einheit statt relativ zur mildesten Kategorie
    "nicht_kategorial": ("uebrige", "mehrfach", "besonderheiten", "weitere"),
    "suchkriterien": [
        {"titel": "Hauptdelikt", "gewicht": 30, "spalten": ("hauptdelikt", None)},
        {"titel": "Tatmittel", "gewicht": 15, "spalten": ("tatmittel", None)},
        {"titel": "Opferalter", "gewicht": 12, "spalten": ("opferalter", None)},
        {"titel": "Mehrfache Begehung", "gewicht": 9, "spalten": ("mehrfach", None)},
        {"titel": "Versuch", "gewicht": 9, "spalten": ("besonderheiten", "Versuch")},
        {"titel": "Vorstrafen", "gewicht": 8, "spalten": ("vorstrafen", None)},
        {"titel": "Täter-Opfer-Beziehung", "gewicht": 7, "spalten": ("beziehung", None)},
        {"titel": "Weitere Sexualdelikte", "gewicht": 7, "spalten": ("weitere", None)},
        {"titel": "Übrige Delikte (Deliktsscore)", "gewicht": 6, "spalten": ("uebrige", None)},
        *BESONDERHEITEN_KRITERIEN,
    ],
    "kreuztabelle": {
        "zeilen": "hauptdelikt",
        "spalten": "tatmittel",
        "titel": "Überlappung von Hauptdelikt und Tatmittel",
        "kopf": "Hauptdelikt \\ Tatmittel",
    },
    "kreuztabelle_text": "database/includes/ridge_kreuztabelle_sexual.html",
    "merkmale_text": "Hauptdelikt (nach Artikel, alt- und neurechtliche Fassung zusammengefasst, weil "
    "neurechtliche Urteile noch zu selten sind), Tatmittel, Opferalter, Täter-Opfer-Beziehung, mehrfache "
    "Begehung, weitere Sexualdelikte (je Artikel), Deliktsscore der übrigen Delikte, Vorstrafen (drei "
    "Stufen), fünf Besonderheiten (inkl. Versuch) sowie Kanton und Nationalität als Kontrollvariablen. "
    "Nicht verwendet sind die Verfahrensart (alle Urteile ordentlich) und das Geschlecht (fast ausschliesslich "
    "männliche Täter), weil sie im Bestand nicht variieren.",
    "interpretation": "database/includes/ridge_interpretation_sexual.html",
}


# --- Gewaltdelikte ---------------------------------------------------------------

BEUTE_SPALTE = "Beute (je Zehnerpotenz über dem Median)"

GEWALT_BESONDERHEITEN = (
    "verminderte Schuldfähigkeit",
    "Geständnisrabatt",
    "jugendlicheR TäterIn",
    "Verletzung Beschleunigungsgebot",
)


def _gewalt_merkmale(urteil, kantone_einzeln):
    """
    Merkmale eines Gewaltdelikt-Urteils als {(gruppe, spaltenlabel): wert}.

    Versuch ist hier ein eigenes Modellfeld (nicht eine Besonderheit). Die
    Beute fliesst als Zehnerlogarithmus ein und wird in daten_erstellen auf
    den Median der bezifferten Beuten zentriert (konfig["zentrieren"]), siehe
    dort.
    """
    m = {}
    m[("hauptdelikt", urteil.get_hauptdelikt_display())] = 1
    m[("versuch", "versucht")] = int(urteil.versuch)
    m[("vorsatzform", urteil.get_vorsatzform_display())] = 1
    m[("tatmittel", urteil.get_tatmittel_display())] = 1
    m[("qualifikationen", "Waffe/gefährlicher Gegenstand")] = int(urteil.waffe_gefaehrlicher_gegenstand)
    m[("qualifikationen", "besondere Gefährlichkeit")] = int(urteil.besondere_gefaehrlichkeit)
    m[("qualifikationen", "Lebensgefahr")] = int(urteil.lebensgefahr)
    m[("mehrfach", "mehrfach begangen")] = int(urteil.mehrfach)
    m[("opferzahl", "je weiteres Opfer")] = max(0, (urteil.opferzahl or 1) - 1)
    m[("beute", BEUTE_SPALTE)] = math.log10(urteil.deliktssumme) if urteil.deliktssumme and urteil.deliktssumme > 0 else 0
    m[("verletzungsfolge", urteil.get_verletzungsfolge_display())] = 1
    m[("koerperteil", urteil.get_angegriffenes_koerperteil_display())] = 1
    m[("beziehung", urteil.get_taeter_opfer_beziehung_display())] = 1
    m[("substanzeinfluss", urteil.get_substanzeinfluss_display())] = 1
    m[("geschlecht", GESCHLECHT_LABEL[urteil.geschlecht])] = 1
    return _gemeinsame_merkmale(urteil, m, GEWALT_BESONDERHEITEN, kantone_einzeln)


GEWALT_KONFIG = {
    "key": "gewalt",
    "titel": "Gewaltdelikte",
    "queryset": lambda: GewaltdeliktUrteil.objects.select_related("kanton").prefetch_related("besonderheiten"),
    "merkmale": _gewalt_merkmale,
    "delikt_anzeige": lambda u: u.get_hauptdelikt_display()
    + (", versucht" if u.versuch else "")
    + (", mehrfach" if u.mehrfach else ""),
    "detail_url": "gewalturteil_detail",
    "suche_url": "praejudizen_finden_gewalt",
    "suche_js": "praejudizfinder_gewalt.js",
    "suche_konstante": "PF_GEWALT_GEWICHTE",
    "gruppen": [
        {"key": "hauptdelikt", "titel": "Hauptdelikt"},
        {"key": "versuch", "titel": "Versuch"},
        {"key": "vorsatzform", "titel": "Vorsatzform"},
        {"key": "verletzungsfolge", "titel": "Verletzungsfolge"},
        {"key": "tatmittel", "titel": "Tatmittel"},
        {"key": "qualifikationen", "titel": "Qualifizierende Umstände"},
        {"key": "mehrfach", "titel": "Mehrfache Begehung"},
        {"key": "opferzahl", "titel": "Anzahl Opfer"},
        {"key": "beute", "titel": "Beute (Raub)"},
        {"key": "koerperteil", "titel": "Angegriffenes Körperteil"},
        {"key": "beziehung", "titel": "Täter-Opfer-Beziehung"},
        {"key": "substanzeinfluss", "titel": "Substanzeinfluss"},
        {"key": "uebrige", "titel": "Übrige Delikte (Deliktsscore)"},
        {"key": "vorstrafen", "titel": "Vorstrafen"},
        {"key": "besonderheiten", "titel": "Besonderheiten"},
        {"key": "kanton", "titel": "Kanton (Kontrollvariable)"},
        {"key": "nationalitaet", "titel": "Nationalität (Kontrollvariable)"},
        {"key": "geschlecht", "titel": "Geschlecht (Kontrollvariable)"},
    ],
    "kontrollen": [KONTROLLE_KANTON, KONTROLLE_NATIONALITAET, KONTROLLE_GESCHLECHT],
    "nicht_kategorial": ("versuch", "qualifikationen", "mehrfach", "opferzahl", "beute", "uebrige", "besonderheiten"),
    "zentrieren": [("beute", BEUTE_SPALTE)],
    "suchkriterien": [
        {"titel": "Hauptdelikt", "gewicht": 30, "spalten": ("hauptdelikt", None)},
        {"titel": "Versuch", "gewicht": 15, "spalten": ("versuch", None)},
        {"titel": "Verletzungsfolge", "gewicht": 15, "spalten": ("verletzungsfolge", None)},
        {"titel": "Vorsatzform", "gewicht": 8, "spalten": ("vorsatzform", None)},
        {"titel": "Tatmittel", "gewicht": 8, "spalten": ("tatmittel", None)},
        {"titel": "Vorstrafen", "gewicht": 8, "spalten": ("vorstrafen", None)},
        {"titel": "Lebensgefahr", "gewicht": 6, "spalten": ("qualifikationen", "Lebensgefahr")},
        {"titel": "besondere Gefährlichkeit", "gewicht": 6, "spalten": ("qualifikationen", "besondere Gefährlichkeit")},
        {"titel": "Mehrfache Begehung", "gewicht": 6, "spalten": ("mehrfach", None)},
        {"titel": "Übrige Delikte (Deliktsscore)", "gewicht": 6, "spalten": ("uebrige", None)},
        {"titel": "Täter-Opfer-Beziehung", "gewicht": 5, "spalten": ("beziehung", None)},
        {"titel": "Beute (nur Raub)", "gewicht": 5, "spalten": ("beute", None)},
        {"titel": "Waffe/gefährlicher Gegenstand", "gewicht": 4, "spalten": ("qualifikationen", "Waffe/gefährlicher Gegenstand")},
        {"titel": "Anzahl Opfer", "gewicht": 4, "spalten": ("opferzahl", None)},
        {"titel": "Angegriffenes Körperteil", "gewicht": 3, "spalten": ("koerperteil", None)},
        {"titel": "Substanzeinfluss", "gewicht": 3, "spalten": ("substanzeinfluss", None)},
        *BESONDERHEITEN_KRITERIEN,
    ],
    "kreuztabelle": {
        "zeilen": "hauptdelikt",
        "spalten": "verletzungsfolge",
        "titel": "Überlappung von Hauptdelikt und Verletzungsfolge",
        "kopf": "Hauptdelikt \\ Verletzungsfolge",
    },
    "kreuztabelle_text": "database/includes/ridge_kreuztabelle_gewalt.html",
    "merkmale_text": "Hauptdelikt (11 Tatbestände), Versuch, Vorsatzform, Verletzungsfolge, Tatmittel, drei "
    "qualifizierende Umstände (Waffe/gefährlicher Gegenstand, besondere Gefährlichkeit, Lebensgefahr), "
    "mehrfache Begehung, Anzahl Opfer, Beute (nur Raub, als Zehnerlogarithmus, zentriert auf die typische Beute), angegriffenes Körperteil, "
    "Täter-Opfer-Beziehung, Substanzeinfluss, Deliktsscore der übrigen Delikte, Vorstrafen (drei Stufen), "
    "vier Besonderheiten sowie Kanton, Nationalität und Geschlecht als Kontrollvariablen. Nicht verwendet sind die Verfahrensart (alle "
    "Urteile ordentlich), die Bandenmässigkeit (4 Urteile) und die Besonderheit «Verbindungsbusse», die keine "
    "Eigenschaft der Tat, sondern Teil der Sanktion ist.",
    "interpretation": "database/includes/ridge_interpretation_gewalt.html",
}

KONFIGURATIONEN = {k["key"]: k for k in (SEXUAL_KONFIG, GEWALT_KONFIG)}


def strafe_in_monaten(urteil):
    """Strafe in Monaten; Geldstrafe umgerechnet, Busse/lebenslänglich -> None."""
    if urteil.hauptsanktion == "0":
        if urteil.freiheitsstrafe_in_monaten in (None, LEBENSLAENGLICH_PLATZHALTER):
            return None
        return urteil.freiheitsstrafe_in_monaten
    if urteil.hauptsanktion == "1" and urteil.anzahl_tagessaetze:
        return urteil.anzahl_tagessaetze / TAGESSAETZE_PRO_MONAT
    return None


def daten_erstellen(konfig):
    """Design-Matrix X, Zielgrösse y (log Monate), Spalten und Urteile."""
    urteile = list(konfig["queryset"]().order_by("pk"))
    anzahl_je_kanton = {}
    for urteil in urteile:
        anzahl_je_kanton[urteil.kanton.abk] = anzahl_je_kanton.get(urteil.kanton.abk, 0) + 1
    kantone_einzeln = {k for k, n in anzahl_je_kanton.items() if n >= MIN_URTEILE_KANTON}

    zeilen, ziele, verwendet, ausgeschlossen = [], [], [], []
    for urteil in urteile:
        monate = strafe_in_monaten(urteil)
        if not monate:
            ausgeschlossen.append(urteil)
            continue
        zeilen.append(konfig["merkmale"](urteil, kantone_einzeln))
        ziele.append(math.log(monate))
        verwendet.append(urteil)

    gruppen_reihenfolge = [g["key"] for g in konfig["gruppen"]]
    spalten = sorted(
        {s for z in zeilen for s in z},
        key=lambda s: (gruppen_reihenfolge.index(s[0]), s[1]),
    )
    X = np.array([[z.get(s, 0) for s in spalten] for z in zeilen], dtype=float)

    # Zahlenmerkmale, die nur bei einem Teil der Urteile vorkommen (z.B. die
    # Beute beim Raub), auf den Median der vorhandenen Werte zentrieren. Sonst
    # wirkte die Spalte selbst wie ein Schalter «Raub ja/nein» und Ridge teilte
    # den Effekt des Hauptdelikts zwischen beiden Spalten auf. Zentriert misst
    # sie nur noch die Abweichung von einer typischen Beute; Urteile ohne
    # bezifferten Wert gelten als typisch (0).
    for spalte in konfig.get("zentrieren", ()):
        if spalte in spalten:
            j = spalten.index(spalte)
            vorhanden = X[:, j] != 0
            if vorhanden.any():
                X[vorhanden, j] -= np.median(X[vorhanden, j])
    return X, np.array(ziele), spalten, verwendet, ausgeschlossen


def _spaltenindizes(spalten, auswahl):
    gruppe, label = auswahl
    return [i for i, s in enumerate(spalten) if s[0] == gruppe and (label is None or s[1] == label)]


def effekt_bei_abweichung(X, koeffizienten, idx):
    """
    Wie stark unterscheidet sich die prognostizierte Strafe typischerweise
    zwischen zwei Urteilen, die in diesem Kriterium voneinander abweichen?

    Gebildet über alle Paare von Urteilen mit unterschiedlicher Ausprägung:
    Mittelwert von |Beitrag A - Beitrag B| auf der Log-Skala. Das entspricht
    der Frage, die ein Suchgewicht beantworten soll ("wie viel kostet eine
    Nichtübereinstimmung"), und hängt - anders als die Streuung im Bestand -
    nicht davon ab, wie häufig ein Merkmal vorkommt: Ein seltenes, aber
    starkes Merkmal (z.B. Versuch) erhält so sein volles Gewicht.

    Liefert (mittlerer Log-Abstand, Anteil abweichender Paare).
    """
    roh = X[:, idx]
    beitrag = roh @ koeffizienten[idx]
    _, codes = np.unique(roh, axis=0, return_inverse=True)
    codes = codes.ravel()
    abweichend = codes[:, None] != codes[None, :]
    if not abweichend.any():
        return 0.0, 0.0
    abstand = np.abs(beitrag[:, None] - beitrag[None, :])
    return float(abstand[abweichend].mean()), float(abweichend.mean())


def auswertung_erstellen(konfig):
    X, y, spalten, urteile, ausgeschlossen = daten_erstellen(konfig)
    n = len(y)

    # 1. Regularisierungsstärke per Kreuzvalidierung wählen
    ridge_cv = RidgeCV(alphas=ALPHAS).fit(X, y)
    alpha = float(ridge_cv.alpha_)
    modell = Ridge(alpha=alpha).fit(X, y)

    # 2. Prognoseleistung auf ungesehenen Urteilen: 5-fache Kreuzvalidierung,
    # 10-mal mit neuer Aufteilung wiederholt. cross_val_predict erlaubt nur
    # eine Partition, darum wird die Wiederholung von Hand gemittelt.
    cv = RepeatedKFold(n_splits=5, n_repeats=10, random_state=ZUFALLSSTARTWERT)
    prognosen = np.zeros((10, n))
    for wiederholung, (train_test) in enumerate(_partitionen(cv, n)):
        prognosen[wiederholung] = cross_val_predict(Ridge(alpha=alpha), X, y, cv=train_test)
    r2_werte = [_r2(y, p) for p in prognosen]
    prognose_mittel = prognosen.mean(axis=0)

    monate = np.exp(y)
    monate_prognose = np.exp(prognose_mittel)
    abweichung = np.abs(monate - monate_prognose)
    # Vergleichsbasis ohne Merkmale: immer der Median aller Strafen
    basis_abweichung = np.abs(monate - np.median(monate))
    faktor = np.exp(np.abs(y - prognose_mittel))

    # 3. Unsicherheit der Koeffizienten: Bootstrap (Urteile mit Zurücklegen ziehen)
    rng = np.random.default_rng(ZUFALLSSTARTWERT)
    boot = np.empty((BOOTSTRAP_WIEDERHOLUNGEN, X.shape[1]))
    for b in range(BOOTSTRAP_WIEDERHOLUNGEN):
        idx = rng.integers(0, n, n)
        boot[b] = Ridge(alpha=alpha).fit(X[idx], y[idx]).coef_
    unten, oben = np.percentile(boot, [5, 95], axis=0)

    # 4. Koeffizienten je Gruppe, als Faktor auf die Strafe ausgedrückt
    anzahl_je_spalte = (X != 0).sum(axis=0)
    gruppen = []
    for gruppe in konfig["gruppen"]:
        eintraege = []
        for i, (g, label) in enumerate(spalten):
            if g != gruppe["key"]:
                continue
            eintraege.append(
                {
                    "label": label,
                    "anzahl": int(anzahl_je_spalte[i]),
                    "koeffizient": float(modell.coef_[i]),
                    "prozent": _prozent(modell.coef_[i]),
                    "prozent_unten": _prozent(unten[i]),
                    "prozent_oben": _prozent(oben[i]),
                    "gesichert": bool(unten[i] > 0 or oben[i] < 0),
                    "relativ": None,
                }
            )
        if not eintraege:
            continue
        if gruppe["key"] not in konfig["nicht_kategorial"]:
            # Kategoriale Gruppen: Werte relativ zur mildesten Kategorie
            # darstellen. Bei one-hot-Codierung ist nur die Differenz zwischen
            # Kategorien bestimmt, nicht das absolute Niveau.
            basis = min(e["koeffizient"] for e in eintraege)
            for e in eintraege:
                e["relativ"] = _prozent(e["koeffizient"] - basis)
            eintraege.sort(key=lambda e: e["koeffizient"])
        gruppen.append({**gruppe, "eintraege": eintraege})

    # 5. Vergleich empirischer Effekt vs. Gewichte der Präjudiziensuche.
    # Abgeleitetes Gewicht = empirischer Anteil, auf die heutige Gewichtssumme
    # skaliert, damit die Zahlen direkt neben PF_GEWICHTE gelesen werden können.
    vergleich = []
    for kriterium in konfig["suchkriterien"] + konfig["kontrollen"]:
        effekt, anteil_paare = effekt_bei_abweichung(
            X, modell.coef_, _spaltenindizes(spalten, kriterium["spalten"])
        )
        vergleich.append(
            {
                "titel": kriterium["titel"],
                "gewicht": kriterium["gewicht"],
                "effekt": effekt,
                "effekt_prozent": _prozent(effekt),
                "anteil_paare": anteil_paare,
            }
        )
    such = [v for v in vergleich if v["gewicht"] is not None]
    summe_effekt = sum(v["effekt"] for v in such)
    summe_gewicht = sum(v["gewicht"] for v in such)
    for v in vergleich:
        v["anteil_empirisch"] = 100 * v["effekt"] / summe_effekt if summe_effekt else 0
        if v["gewicht"] is not None:
            v["anteil_heute"] = 100 * v["gewicht"] / summe_gewicht
            v["gewicht_abgeleitet"] = round(summe_gewicht * v["effekt"] / summe_effekt) if summe_effekt else 0
            v["differenz"] = v["anteil_empirisch"] - v["anteil_heute"]
            v["breite_heute"] = f"{v['anteil_heute']:.1f}"
        # Fuer style="width: ...%" unlokalisiert (de-ch wuerde sonst ein
        # Dezimalkomma ausgeben, das CSS nicht versteht)
        v["breite_empirisch"] = f"{v['anteil_empirisch']:.1f}"

    # 6. Grösste Ausreisser: Urteile, die das Modell am schlechtesten erklärt
    ausreisser_idx = np.argsort(-np.abs(y - prognose_mittel))[:10]
    ausreisser = [
        {
            "urteil": urteile[i],
            "url": reverse(konfig["detail_url"], args=[urteile[i].pk]),
            "delikt": konfig["delikt_anzeige"](urteile[i]),
            "strafe": _strafe_anzeige(urteile[i]),
            "tatsaechlich": float(monate[i]),
            "prognose": float(monate_prognose[i]),
            "faktor": float(math.exp(y[i] - prognose_mittel[i])),
        }
        for i in ausreisser_idx
    ]

    return {
        "n": n,
        "n_ausgeschlossen": len(ausgeschlossen),
        "n_geldstrafen": sum(1 for u in urteile if u.hauptsanktion == "1"),
        "n_spalten": X.shape[1],
        "alpha": alpha,
        "r2_mittel": float(np.mean(r2_werte)),
        "r2_min": float(np.min(r2_werte)),
        "r2_max": float(np.max(r2_werte)),
        "r2_training": float(modell.score(X, y)),
        "mae_monate": float(np.mean(abweichung)),
        "median_abweichung_monate": float(np.median(abweichung)),
        "mae_basis_monate": float(np.mean(basis_abweichung)),
        "median_faktor": float(np.median(faktor)),
        "anteil_innert_faktor_1_5": float(np.mean(faktor <= 1.5)),
        "median_strafe": float(np.median(monate)),
        "achsenabschnitt_monate": float(math.exp(modell.intercept_)),
        "gruppen": gruppen,
        "vergleich": vergleich,
        "ausreisser": ausreisser,
        "streudiagramm": streudiagramm_erstellen(urteile, monate, monate_prognose, konfig["detail_url"]),
        "kreuztabelle": kreuztabelle_erstellen(X, spalten, konfig["kreuztabelle"]),
        "bootstrap_wiederholungen": BOOTSTRAP_WIEDERHOLUNGEN,
    }


def _strafe_anzeige(urteil):
    """Strafe in der ausgesprochenen Einheit, z.B. «18 Mt.» oder «20 TS»."""
    if urteil.hauptsanktion == "1":
        return f"{urteil.anzahl_tagessaetze} TS"
    return f"{urteil.freiheitsstrafe_in_monaten} Mt."


def _partitionen(cv, n):
    """Teilt die Folds von RepeatedKFold in die einzelnen Wiederholungen auf."""
    folds = list(cv.split(np.zeros(n)))
    pro_wiederholung = cv.cvargs["n_splits"]
    for start in range(0, len(folds), pro_wiederholung):
        yield folds[start:start + pro_wiederholung]


def _r2(y, p):
    return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)


def _prozent(koeffizient):
    """Log-Koeffizient als prozentuale Veränderung der Strafe."""
    return 100 * (math.exp(koeffizient) - 1)


# --- Darstellung -------------------------------------------------------------

DIAGRAMM = {"breite": 560, "hoehe": 420, "links": 52, "rechts": 14, "oben": 14, "unten": 44}
ACHSE_MIN, ACHSE_MAX = 1, 240  # Monate, logarithmisch
ACHSE_TICKS = (1, 3, 6, 12, 24, 48, 96, 180)


def _skala(wert, laenge):
    wert = min(max(wert, ACHSE_MIN), ACHSE_MAX)
    return laenge * (math.log(wert) - math.log(ACHSE_MIN)) / (math.log(ACHSE_MAX) - math.log(ACHSE_MIN))


def _k(wert):
    """SVG-Koordinate als String mit Dezimalpunkt (unabhängig von der Lokalisierung)."""
    return f"{wert:.1f}"


def streudiagramm_erstellen(urteile, monate, prognose, detail_url):
    """
    SVG-Geometrie für «Prognose (Kreuzvalidierung) vs. tatsächliche Strafe».
    Beide Achsen logarithmisch, weil das Modell auf der Log-Skala rechnet und
    eine Abweichung um Faktor 1.5 so überall gleich breit erscheint.
    """
    d = DIAGRAMM
    innen_b = d["breite"] - d["links"] - d["rechts"]
    innen_h = d["hoehe"] - d["oben"] - d["unten"]

    def px(x):
        return d["links"] + _skala(x, innen_b)

    def py(y):
        return d["oben"] + innen_h - _skala(y, innen_h)

    punkte = []
    for urteil, tatsaechlich, geschaetzt in zip(urteile, monate, prognose):
        punkte.append(
            {
                "cx": _k(px(geschaetzt)),
                "cy": _k(py(tatsaechlich)),
                "klasse": f"sanktion-{urteil.hauptsanktion} vollzug-{urteil.vollzug}",
                "titel": f"{urteil.fall_nr}: tatsächlich {tatsaechlich:.0f} Mt., Prognose {geschaetzt:.0f} Mt.",
                "url": reverse(detail_url, args=[urteil.pk]),
            }
        )

    def linie(faktor):
        # Gerade y = faktor * x, auf den sichtbaren Bereich beider Achsen beschnitten
        x1 = max(ACHSE_MIN, ACHSE_MIN / faktor)
        x2 = min(ACHSE_MAX, ACHSE_MAX / faktor)
        return {
            "x1": _k(px(x1)), "y1": _k(py(x1 * faktor)),
            "x2": _k(px(x2)), "y2": _k(py(x2 * faktor)),
        }

    return {
        **d,
        "innen_b": innen_b,
        "innen_h": innen_h,
        "unten_y": d["oben"] + innen_h,
        "rechts_x": d["links"] + innen_b,
        "punkte": punkte,
        "diagonale": linie(1),
        "band_oben": linie(1.5),
        "band_unten": linie(1 / 1.5),
        "ticks": [{"wert": t, "x": _k(px(t)), "y": _k(py(t))} for t in ACHSE_TICKS],
    }


def kreuztabelle_erstellen(X, spalten, kreuz):
    """Anzahl Urteile je Kategorie zweier one-hot-Gruppen (z.B. Hauptdelikt × Tatmittel)."""
    zeilen = [(i, s[1]) for i, s in enumerate(spalten) if s[0] == kreuz["zeilen"]]
    kolonnen = [(i, s[1]) for i, s in enumerate(spalten) if s[0] == kreuz["spalten"]]
    return {
        "titel": kreuz["titel"],
        "spalten": [label for _, label in kolonnen],
        "zeilen": [
            {
                "label": label_z,
                "werte": [int(((X[:, i_z] == 1) & (X[:, i_k] == 1)).sum()) for i_k, _ in kolonnen],
            }
            for i_z, label_z in zeilen
        ],
    }
