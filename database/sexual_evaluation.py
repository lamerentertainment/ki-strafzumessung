"""
Empirische Auswertung der Sexualdelikt-Urteile mit einer Ridge-Regression.

Zweck: prüfen, welche erfassten Fallmerkmale in der Praxis mit der Strafhöhe
zusammenhängen, und daraus Werte je Kategorie ableiten - als Grundlage, um die
von Hand gesetzten Gewichte der geführten Präjudiziensuche
(``praejudizfinder_sexual.js``, ``PF_GEWICHTE``) empirisch zu überprüfen.

Die Auswertung läuft bei jedem Aufruf der Dev-Seite frisch auf dem aktuellen
Bestand (rund 300 Urteile, Rechenzeit unter einer Sekunde), damit sie neue
Einträge ohne separaten Kalibrierungsschritt berücksichtigt.

Herleitung in Kürze (ausführlich auf der Seite ``sexual_evaluation.html``):

- Zielgrösse ist der natürliche Logarithmus der Strafe in Monaten. Geldstrafen
  werden mit 30 Tagessätzen = 1 Monat umgerechnet (Art. 34 i.V.m. Art. 36 StGB).
  Der Logarithmus, weil Strafen rechtsschief verteilt sind und Merkmale eher
  proportional als additiv wirken (+20 % statt +6 Monate).
- Kategoriale Merkmale werden one-hot codiert; jede Kategorie erhält damit
  ihren eigenen Koeffizienten = ihren gelernten Wert.
- Ridge statt gewöhnlicher Regression, weil bei ~300 Urteilen und ~40
  Merkmalsspalten seltene Kategorien sonst extreme Werte erhielten. Die
  Regularisierungsstärke alpha wird per Kreuzvalidierung gewählt.
"""

import math

import numpy as np
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.model_selection import RepeatedKFold, cross_val_predict

from django.urls import reverse

from .models import SexualdeliktUrteil
from .praejudizfinder import artikel_aus_name

TAGESSAETZE_PRO_MONAT = 30
LEBENSLAENGLICH_PLATZHALTER = 999
ALPHAS = np.logspace(-2, 3, 30)
ZUFALLSSTARTWERT = 42
BOOTSTRAP_WIEDERHOLUNGEN = 300

# Kantone mit wenigen Urteilen werden zusammengefasst, sonst erhielte jeder
# Kleinkanton einen kaum belastbaren eigenen Koeffizienten.
KANTONE_EINZELN = ("ZH", "GE", "VD", "FR", "BE")

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

# Merkmalsgruppen der Regression in der Reihenfolge der Seite.
GRUPPEN = [
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
]

# Kriterien der Präjudiziensuche mit ihren heutigen Gewichten (Stand
# praejudizfinder_sexual.js, PF_GEWICHTE) und den Regressionsspalten, die sie
# abdecken: (gruppe, None) = ganze Gruppe, (gruppe, label) = eine Spalte.
SUCHKRITERIEN = [
    {"titel": "Hauptdelikt", "gewicht": 30, "spalten": ("hauptdelikt", None)},
    {"titel": "Tatmittel", "gewicht": 15, "spalten": ("tatmittel", None)},
    {"titel": "Opferalter", "gewicht": 12, "spalten": ("opferalter", None)},
    {"titel": "Mehrfache Begehung", "gewicht": 9, "spalten": ("mehrfach", None)},
    {"titel": "Versuch", "gewicht": 9, "spalten": ("besonderheiten", "Versuch")},
    {"titel": "Vorstrafen", "gewicht": 8, "spalten": ("vorstrafen", None)},
    {"titel": "Täter-Opfer-Beziehung", "gewicht": 7, "spalten": ("beziehung", None)},
    {"titel": "Weitere Sexualdelikte", "gewicht": 7, "spalten": ("weitere", None)},
    {"titel": "Übrige Delikte (Deliktsscore)", "gewicht": 6, "spalten": ("uebrige", None)},
    {"titel": "verminderte Schuldfähigkeit", "gewicht": 5, "spalten": ("besonderheiten", "verminderte Schuldfähigkeit")},
    {"titel": "Geständnisrabatt", "gewicht": 5, "spalten": ("besonderheiten", "Geständnisrabatt")},
    {"titel": "jugendliche Täterschaft", "gewicht": 5, "spalten": ("besonderheiten", "jugendlicheR TäterIn")},
    {"titel": "Verletzung Beschleunigungsgebot", "gewicht": 5, "spalten": ("besonderheiten", "Verletzung Beschleunigungsgebot")},
]
# Nur zur Einordnung, kein Suchkriterium
KONTROLLE = {"titel": "Kanton (Kontrollvariable, kein Suchkriterium)", "gewicht": None, "spalten": ("kanton", None)}

BESONDERHEITEN = (
    "Versuch",
    "verminderte Schuldfähigkeit",
    "Geständnisrabatt",
    "jugendlicheR TäterIn",
    "Verletzung Beschleunigungsgebot",
)


def strafe_in_monaten(urteil):
    """Strafe in Monaten; Geldstrafe umgerechnet, Busse/lebenslänglich -> None."""
    if urteil.hauptsanktion == "0":
        if urteil.freiheitsstrafe_in_monaten in (None, LEBENSLAENGLICH_PLATZHALTER):
            return None
        return urteil.freiheitsstrafe_in_monaten
    if urteil.hauptsanktion == "1" and urteil.anzahl_tagessaetze:
        return urteil.anzahl_tagessaetze / TAGESSAETZE_PRO_MONAT
    return None


def _merkmale(urteil):
    """
    Merkmale eines Urteils als {(gruppe, spaltenlabel): wert}.

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
    m[("uebrige", "Deliktsscore (je Punkt)")] = urteil.deliktsscore_uebrige_delikte or 0
    if urteil.vorbestraft_einschlaegig:
        m[("vorstrafen", "einschlägig vorbestraft")] = 1
    elif urteil.vorbestraft:
        m[("vorstrafen", "nicht einschlägig vorbestraft")] = 1
    else:
        m[("vorstrafen", "nicht vorbestraft")] = 1
    namen = {b.name for b in urteil.besonderheiten.all()}
    for name in BESONDERHEITEN:
        m[("besonderheiten", name)] = int(name in namen)
    kanton = urteil.kanton.abk if urteil.kanton.abk in KANTONE_EINZELN else "übrige Kantone"
    m[("kanton", kanton)] = 1
    return m


def daten_erstellen():
    """Design-Matrix X, Zielgrösse y (log Monate), Spalten und Urteile."""
    urteile = (
        SexualdeliktUrteil.objects.select_related("hauptdelikt", "hauptdelikt_tatmittel", "kanton")
        .prefetch_related("sexualdelikte_zusaetzliche", "besonderheiten")
        .order_by("pk")
    )
    zeilen, ziele, verwendet, ausgeschlossen = [], [], [], []
    for urteil in urteile:
        monate = strafe_in_monaten(urteil)
        if not monate:
            ausgeschlossen.append(urteil)
            continue
        zeilen.append(_merkmale(urteil))
        ziele.append(math.log(monate))
        verwendet.append(urteil)

    gruppen_reihenfolge = [g["key"] for g in GRUPPEN]
    spalten = sorted(
        {s for z in zeilen for s in z},
        key=lambda s: (gruppen_reihenfolge.index(s[0]), s[1]),
    )
    X = np.array([[z.get(s, 0) for s in spalten] for z in zeilen], dtype=float)
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


def auswertung_erstellen():
    X, y, spalten, urteile, ausgeschlossen = daten_erstellen()
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
    for gruppe in GRUPPEN:
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
        if gruppe["key"] not in ("uebrige", "mehrfach", "besonderheiten", "weitere"):
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
    for kriterium in SUCHKRITERIEN + [KONTROLLE]:
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
        "streudiagramm": streudiagramm_erstellen(urteile, monate, monate_prognose),
        "kreuztabelle": kreuztabelle_erstellen(X, spalten),
        "bootstrap_wiederholungen": BOOTSTRAP_WIEDERHOLUNGEN,
    }


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


def streudiagramm_erstellen(urteile, monate, prognose):
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
                "url": reverse("sexualurteil_detail", args=[urteil.pk]),
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


def kreuztabelle_erstellen(X, spalten):
    """Anzahl Urteile je Hauptdelikt (Zeilen) und Tatmittel (Spalten)."""
    hd = [(i, s[1]) for i, s in enumerate(spalten) if s[0] == "hauptdelikt"]
    tm = [(i, s[1]) for i, s in enumerate(spalten) if s[0] == "tatmittel"]
    return {
        "spalten": [label for _, label in tm],
        "zeilen": [
            {
                "label": label_hd,
                "werte": [int(((X[:, i_hd] == 1) & (X[:, i_tm] == 1)).sum()) for i_tm, _ in tm],
            }
            for i_hd, label_hd in hd
        ],
    }
