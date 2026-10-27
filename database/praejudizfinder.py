"""
Geführte Präjudiziensuche ("Präjudizen finden") für Sexual- und Gewaltdelikte.

Die Seite führt Schritt für Schritt durch die strafzumessungsrelevanten
Merkmale (Hauptdelikt, Tatmittel, Opfer, Tatbegehung, weitere Delikte, Täter)
und schlägt am Ende die ähnlichsten Urteile aus der Datenbank vor.

Hier stehen nur die Schrittdefinitionen mit ihren Erläuterungen sowie die
Normalisierung der Urteile in eine schlanke JSON-Struktur. Die eigentliche
Ähnlichkeitsbewertung geschieht clientseitig (siehe
``database/static/database/praejudizfinder_basis.js`` und die deliktspezifischen
``praejudizfinder_sexual.js``/``praejudizfinder_gewalt.js``), damit jede Antwort
sofort auf die Trefferzahl durchschlägt, ohne Roundtrip - wie bei den
Filteransichten (``filterspec.py``).
"""

import re

from django.urls import reverse

from .models import (
    Besonderheiten,
    GewaltdeliktUrteil,
    Hauptdelikt,
    SexualdeliktUrteil,
    Tatmittel,
    ZusaetzlicheSexualdelikte,
)

# Inkrafttreten des revidierten Sexualstrafrechts (BG vom 16. Juni 2023)
STICHTAG_NEUES_RECHT = "1. Juli 2024"


def artikel_aus_name(name):
    """
    Artikelnummer aus einem Katalogwert, z.B. "a190, Vergewaltigung,
    altrechtlich" -> "190". Alt- und neurechtliche Werte desselben Artikels
    werden so vergleichbar.
    """
    treffer = re.match(r"\s*a?(\d+\w?)", name or "")
    return treffer.group(1) if treffer else ""


def _altrechtlich(name):
    return "altrechtlich" in (name or "")


# --- Erläuterungen ------------------------------------------------------------
#
# Bewusst ausführlicher als die Tooltips der Datenbankansicht: Die Seite richtet
# sich auch an Nutzer, die einen Fall erst einordnen müssen. Strafrahmen gemäss
# Fedlex (SR 311.0), altrechtlich in der Fassung bis 30. Juni 2024.

HAUPTDELIKT_ERLAEUTERUNGEN = {
    ("187", True): {
        "titel": "Sexuelle Handlungen mit Kindern (altrechtlich)",
        "text": "Sexuelle Handlung mit einem Kind unter 16 Jahren, Verleiten oder Einbeziehen "
        "eines Kindes in eine sexuelle Handlung. Nicht strafbar bei einem Altersunterschied "
        "von höchstens drei Jahren. Eine Nötigung ist nicht vorausgesetzt - auch eine "
        "«einvernehmliche» Handlung ist strafbar.",
        "strafrahmen": "Freiheitsstrafe bis zu 5 Jahren oder Geldstrafe",
    },
    ("187", False): {
        "titel": "Sexuelle Handlungen mit Kindern (neues Recht)",
        "text": "Wie bisher Schutzalter 16. Neu ist Ziff. 1bis: Hat das Kind das 12. Altersjahr "
        "noch nicht vollendet und nimmt der Täter mit ihm eine sexuelle Handlung vor, gilt "
        "eine Mindeststrafe von einem Jahr Freiheitsstrafe.",
        "strafrahmen": "Freiheitsstrafe bis zu 5 Jahren oder Geldstrafe; Ziff. 1bis: 1 bis 5 Jahre",
    },
    ("188", True): {
        "titel": "Sexuelle Handlungen mit Abhängigen (altrechtlich)",
        "text": "Sexuelle Handlung mit einer minderjährigen Person über 16 Jahren unter Ausnützung "
        "eines Erziehungs-, Betreuungs- oder Arbeitsverhältnisses (z.B. Lehrperson, "
        "Lehrmeister, Trainer).",
        "strafrahmen": "Freiheitsstrafe bis zu 3 Jahren oder Geldstrafe",
    },
    ("188", False): {
        "titel": "Sexuelle Handlungen mit Abhängigen (neues Recht)",
        "text": "Wie bisher, gilt neu aber bereits ab 16 Jahren («von mindestens 16 Jahren»); der "
        "Strafrahmen wurde angehoben.",
        "strafrahmen": "Freiheitsstrafe bis zu 5 Jahren oder Geldstrafe",
    },
    ("189", True): {
        "titel": "Sexuelle Nötigung (altrechtlich)",
        "text": "Der Täter nötigt das Opfer zur Duldung einer beischlafsähnlichen oder einer "
        "anderen sexuellen Handlung - durch Drohung, Gewalt, psychischen Druck oder indem er "
        "es zum Widerstand unfähig macht. Erfasst alle sexuellen Handlungen ausser dem "
        "vaginalen Beischlaf, also z.B. Oral- und Analverkehr oder Berührungen im "
        "Intimbereich. Ohne Nötigungsmittel keine Strafbarkeit nach dieser Bestimmung.",
        "strafrahmen": "Freiheitsstrafe bis zu 10 Jahren oder Geldstrafe; grausam/mit gefährlicher "
        "Waffe: nicht unter 3 Jahren",
    },
    ("189", False): {
        "titel": "Sexueller Übergriff und sexuelle Nötigung (neues Recht)",
        "text": "Abs. 1 (sexueller Übergriff) genügt neu, dass die Handlung gegen den Willen des "
        "Opfers erfolgt («Nein heisst Nein», inkl. Ausnützen eines Schockzustands, sog. "
        "Freezing) - ein Nötigungsmittel ist nicht erforderlich. Abs. 2 (sexuelle Nötigung) "
        "entspricht dem bisherigen Tatbestand mit Nötigungsmittel.",
        "strafrahmen": "Abs. 1: bis 3 Jahre oder Geldstrafe; Abs. 2: bis 10 Jahre oder Geldstrafe; "
        "Abs. 3: nicht unter 1 Jahr",
    },
    ("190", True): {
        "titel": "Vergewaltigung (altrechtlich)",
        "text": "Der Täter nötigt eine Person weiblichen Geschlechts zur Duldung des Beischlafs "
        "(vaginale Penetration) - durch Drohung, Gewalt, psychischen Druck oder indem er sie "
        "zum Widerstand unfähig macht. Andere Penetrationsformen und männliche Opfer fallen "
        "altrechtlich unter die sexuelle Nötigung.",
        "strafrahmen": "Freiheitsstrafe von 1 bis 10 Jahren; grausam/mit gefährlicher Waffe: nicht "
        "unter 3 Jahren",
    },
    ("190", False): {
        "titel": "Vergewaltigung (neues Recht)",
        "text": "Geschlechtsneutral; erfasst den Beischlaf und jede beischlafsähnliche Handlung, "
        "die mit einem Eindringen in den Körper verbunden ist. Abs. 1: gegen den Willen des "
        "Opfers bzw. unter Ausnützung eines Schockzustands, ohne Nötigungsmittel. Abs. 2: mit "
        "Nötigungsmittel (Drohung, Gewalt, psychischer Druck, Widerstandsunfähigmachen).",
        "strafrahmen": "Abs. 1: bis 5 Jahre Freiheitsstrafe; Abs. 2: 1 bis 10 Jahre; Abs. 3: nicht "
        "unter 3 Jahren",
    },
    ("191", True): {
        "titel": "Schändung (altrechtlich)",
        "text": "Der Täter missbraucht eine urteilsunfähige oder zum Widerstand unfähige Person in "
        "Kenntnis ihres Zustandes zu einer sexuellen Handlung - etwa eine schlafende, "
        "bewusstlose, stark berauschte oder geistig schwer beeinträchtigte Person. Der Täter "
        "muss den Zustand nicht selbst herbeigeführt haben; er nützt ihn aus.",
        "strafrahmen": "Freiheitsstrafe bis zu 10 Jahren oder Geldstrafe",
    },
    ("191", False): {
        "titel": "Missbrauch einer urteilsunfähigen oder zum Widerstand unfähigen Person (neues Recht)",
        "text": "Entspricht inhaltlich der bisherigen Schändung.",
        "strafrahmen": "Freiheitsstrafe bis zu 10 Jahren oder Geldstrafe",
    },
    ("193", False): {
        "titel": "Ausnützung einer Notlage oder Abhängigkeit",
        "text": "Der Täter veranlasst eine Person zu einer sexuellen Handlung, indem er eine "
        "Notlage oder eine durch ein Arbeitsverhältnis oder anderweitig begründete "
        "Abhängigkeit ausnützt - ohne dass ein eigentliches Nötigungsmittel vorliegt.",
        "strafrahmen": "Freiheitsstrafe bis zu 5 Jahren oder Geldstrafe",
    },
}

TATMITTEL_ERLAEUTERUNGEN = {
    "Gewalt": {
        "kurz": "Körperliche Einwirkung, um den Widerstand des Opfers zu brechen.",
        "text": "Der Täter setzt physische Kraft ein, die über das zur Vornahme der sexuellen "
        "Handlung Notwendige hinausgeht: Festhalten, Niederdrücken, Fixieren mit dem "
        "Körpergewicht, Auseinanderdrücken der Beine, Schläge, Würgen. Verletzungen sind "
        "nicht vorausgesetzt. Hierher gehört auch die Drohung mit Gewalt.",
        "beispiele": [
            "Täter drückt das Opfer auf das Bett und hält dessen Arme fest",
            "Täter schlägt oder würgt das Opfer, als es sich wehrt",
        ],
    },
    "psychischer Druck": {
        "kurz": "Nötigung ohne körperliche Gewalt, durch eine ausweglose Zwangslage.",
        "text": "Der Täter schafft oder nützt eine Situation aus, in der dem Opfer ein Widerstand "
        "nicht zuzumuten ist. Die Zwangslage muss eine erhebliche Intensität aufweisen; ein "
        "blosses Ausnützen einer Überlegenheit genügt nicht. Typisch sind Drohungen (z.B. mit "
        "Trennung, Bekanntmachung, Wegweisung), Einschüchterung, das Ausnützen von "
        "Autorität sowie emotionaler oder sozialer Abhängigkeit. Bei Kindern im familiären "
        "Umfeld stellt die Rechtsprechung geringere Anforderungen («strukturelle Gewalt»): Das "
        "Kind ist dem Täter kognitiv und emotional unterlegen und kann sich ihm kaum "
        "entziehen.",
        "beispiele": [
            "Stiefvater nützt über Jahre das Abhängigkeits- und Vertrauensverhältnis zum Kind aus",
            "Täter droht, intime Bilder zu veröffentlichen",
            "Opfer wird an einem abgelegenen Ort überrascht und eingeschüchtert",
        ],
    },
    "Widerstandsunfähigkeit": {
        "kurz": "Das Opfer konnte sich nicht wehren (Schlaf, Rausch, Bewusstlosigkeit u.ä.).",
        "text": "Das Opfer war urteils- oder widerstandsunfähig, und der Täter hat diesen Zustand "
        "ausgenützt oder (z.B. durch K.O.-Tropfen) selbst herbeigeführt. Typisch für die "
        "Schändung (Art. 191 StGB). Wird das Opfer gezielt widerstandsunfähig gemacht, kommt "
        "auch eine sexuelle Nötigung oder Vergewaltigung in Frage.",
        "beispiele": [
            "Opfer schläft oder ist stark alkoholisiert",
            "Täter verabreicht dem Opfer heimlich Betäubungsmittel",
            "Opfer ist geistig schwer beeinträchtigt",
        ],
    },
    "einvernehmlich": {
        "kurz": "Kein Zwang - strafbar wegen Schutzalter oder Abhängigkeit.",
        "text": "Die sexuelle Handlung erfolgte ohne Nötigungsmittel und mit dem (rechtlich "
        "unbeachtlichen) Einverständnis des Opfers. Strafbar ist sie, weil das Opfer das "
        "Schutzalter von 16 Jahren noch nicht erreicht hat (Art. 187 StGB) oder vom Täter "
        "abhängig war (Art. 188 StGB). Für die Strafzumessung ist die Einvernehmlichkeit "
        "regelmässig verschuldensmindernd.",
        "beispiele": [
            "19-jähriger Täter hat eine Beziehung mit einer 14-Jährigen",
        ],
    },
}

OPFERALTER_ERLAEUTERUNG = (
    "Massgebend ist das Alter des jüngsten Opfers bei der (ersten) Begehung des "
    "Hauptdelikts. Je jünger das Opfer, desto schwerer wiegt in der Regel das "
    "Tatverschulden. Unter 16 Jahren greift zusätzlich der Schutz von Art. 187 StGB, unter "
    "12 Jahren gilt neurechtlich eine Mindeststrafe."
)

# Gruppen für die Ähnlichkeitsbewertung: Innerhalb einer Gruppe gilt eine
# andere Beziehung als ähnlich (vgl. praejudizfinder_sexual.js).
BEZIEHUNG_ERLAEUTERUNGEN = {
    "Ehegatte/Partner": ("nah", "Ehe, eingetragene Partnerschaft, Lebens- oder Liebesbeziehung, auch Ex-Partner."),
    "Elternteil/Kind": ("familie", "Eltern, Stief- und Pflegeeltern bzw. deren Lebenspartner gegenüber dem Kind."),
    "entfernt verwandt": ("familie", "Onkel, Grosseltern, Cousins usw."),
    "Bekannte": ("bekannt", "Freunde, Nachbarn, Arbeitskollegen, Bekannte der Familie."),
    "flüchtig Bekannt": ("bekannt", "Täter und Opfer haben sich erst kurz vorher kennengelernt, z.B. am selben Abend im Ausgang oder über eine Dating-App."),
    "Unbekannte": ("fremd", "Täter und Opfer kannten sich vor der Tat nicht (Überfall durch Fremde)."),
}

# Besonderheiten, nach denen auf der Seite gefragt wird, mit Gewicht und
# Erläuterung. Nur Katalogwerte, die im Bestand vorkommen, werden angeboten.
BESONDERHEITEN_FRAGEN = {
    "Versuch": {
        "schritt": "tat",
        "frage": "Blieb das Hauptdelikt im Versuchsstadium?",
        "text": "Beim Versuch (Art. 22 StGB) kann das Gericht die Strafe mildern. Massgebend ist, "
        "wie nahe der Täter dem Taterfolg kam.",
    },
    "verminderte Schuldfähigkeit": {
        "schritt": "taeter",
        "frage": "Wurde dem Täter eine verminderte Schuldfähigkeit attestiert?",
        "text": "War der Täter zur Tatzeit nur teilweise fähig, das Unrecht seiner Tat einzusehen "
        "oder danach zu handeln (Art. 19 Abs. 2 StGB, z.B. wegen psychischer Störung oder "
        "Intoxikation), wird die Strafe gemildert. Grundlage ist i.d.R. ein psychiatrisches "
        "Gutachten.",
    },
    "Geständnisrabatt": {
        "schritt": "taeter",
        "frage": "Ist der Täter geständig (Geständnisrabatt)?",
        "text": "Ein frühes, umfassendes Geständnis, das die Strafverfolgung erleichtert und "
        "Einsicht zeigt, wirkt strafmindernd - bei Sexualdelikten nicht zuletzt, weil es dem "
        "Opfer eine Aussage vor Gericht ersparen kann.",
    },
    "jugendlicheR TäterIn": {
        "schritt": "taeter",
        "frage": "War der Täter zur Tatzeit sehr jung (junger Erwachsener)?",
        "text": "Ein junges Alter des Täters kann sich bei der Täterkomponente strafmindernd "
        "auswirken.",
    },
    "Verletzung Beschleunigungsgebot": {
        "schritt": "taeter",
        "frage": "Dauerte das Verfahren übermässig lange (Verletzung des Beschleunigungsgebots)?",
        "text": "Eine Verletzung des Beschleunigungsgebots (Art. 5 StPO) führt zu einer "
        "Strafreduktion.",
    },
}

UEBRIGE_DELIKTE_ERLAEUTERUNG = (
    "Gemeint sind alle Schuldsprüche ausser den Sexualdelikten, z.B. Drohung, Nötigung, "
    "Körperverletzung, Betäubungsmittel- oder Strassenverkehrsdelikte. Die Datenbank "
    "verdichtet sie zu einem Deliktsscore: +2 Punkte pro Verbrechen (Strafandrohung über "
    "3 Jahre Freiheitsstrafe, z.B. Raub, schwere Körperverletzung, Art. 19 Abs. 2 BetmG), "
    "+1 Punkt pro Vergehen (bis 3 Jahre oder Geldstrafe, z.B. Drohung, Nötigung, einfache "
    "Körperverletzung) und +1 Zusatzpunkt, wenn ein solches Delikt mehrfach begangen wurde. "
    "Übertretungen (nur Busse, z.B. Tätlichkeiten) zählen nicht."
)


def _artikel_label(artikel, namen):
    """Bezeichnung eines Artikels aus seinen Katalogwerten, neurechtliche bevorzugt."""
    neu = [n for n in namen if not _altrechtlich(n)]
    basis = (neu or namen)[0]
    titel = basis.split(",")[1].strip() if "," in basis else basis
    return f"Art. {artikel} StGB – {titel[:1].upper()}{titel[1:]}"


# --- Gemeinsame Teile aller Deliktsarten ----------------------------------------


def _besonderheiten_fragen(vorhandene, ausser=()):
    """Fragen zu den Besonderheiten, soweit sie im Bestand der Deliktsart vorkommen."""
    return [
        {"value": name, **frage}
        for name, frage in BESONDERHEITEN_FRAGEN.items()
        if name in vorhandene and name not in ausser
    ]


def _grundfelder(urteil, detail_urlname):
    """Felder, die die Basis-Komponente (praejudizfinder_basis.js) bei jedem Urteil erwartet."""
    return {
        "pk": urteil.pk,
        "url": reverse(detail_urlname, args=[urteil.pk]),
        "pdf": urteil.url_link,
        "fall_nr": urteil.fall_nr,
        "gericht": urteil.gericht,
        "datum": urteil.urteilsdatum.strftime("%d.%m.%Y") if urteil.urteilsdatum else "",
        "deliktsscore": urteil.deliktsscore_uebrige_delikte,
        "vorbestraft": urteil.vorbestraft,
        "einschlaegig": urteil.vorbestraft_einschlaegig,
        "besonderheiten": [b.name for b in urteil.besonderheiten.all()],
        "hauptsanktion": urteil.hauptsanktion,
        "freiheitsstrafe": urteil.freiheitsstrafe_in_monaten,
        "tagessaetze": urteil.anzahl_tagessaetze,
        "vollzug": urteil.vollzug,
        "vollzug_label": urteil.get_vollzug_display(),
        "kurzsachverhalt": urteil.kurzsachverhalt,
    }


# --- Sexualdelikte ---------------------------------------------------------------


def sexual_schritte_erstellen():
    """Optionen und Erläuterungen der einzelnen Schritte, aus dem Bestand abgeleitet."""
    bestand = SexualdeliktUrteil.objects.all()
    anzahl_je_hauptdelikt = {}
    for name in bestand.values_list("hauptdelikt__name", flat=True):
        anzahl_je_hauptdelikt[name] = anzahl_je_hauptdelikt.get(name, 0) + 1

    hauptdelikte = []
    for delikt in Hauptdelikt.objects.order_by("name"):
        artikel = artikel_aus_name(delikt.name)
        alt = _altrechtlich(delikt.name)
        erlaeuterung = HAUPTDELIKT_ERLAEUTERUNGEN.get((artikel, alt), {})
        hauptdelikte.append(
            {
                "value": delikt.name,
                "artikel": artikel,
                "altrechtlich": alt,
                "titel": erlaeuterung.get("titel", delikt.name),
                "text": erlaeuterung.get("text", ""),
                "strafrahmen": erlaeuterung.get("strafrahmen", ""),
                "anzahl": anzahl_je_hauptdelikt.get(delikt.name, 0),
            }
        )
    # Erst nach Artikel, innerhalb des Artikels das neue vor dem alten Recht
    hauptdelikte.sort(key=lambda d: (d["artikel"], d["altrechtlich"]))

    vorhandene_tatmittel = set(bestand.values_list("hauptdelikt_tatmittel__name", flat=True))
    tatmittel = [
        {"value": name, **TATMITTEL_ERLAEUTERUNGEN.get(name, {"kurz": "", "text": "", "beispiele": []})}
        for name in Tatmittel.objects.order_by("name").values_list("name", flat=True)
        if name in vorhandene_tatmittel
    ]

    opferalter = [
        {"value": wert, "label": label}
        for wert, label in SexualdeliktUrteil.OPFERALTER_CHOICES
        if wert != "nicht bekannt"
    ]
    beziehungen = [
        {"value": wert, "label": label, "gruppe": BEZIEHUNG_ERLAEUTERUNGEN[wert][0], "text": BEZIEHUNG_ERLAEUTERUNGEN[wert][1]}
        for wert, label in SexualdeliktUrteil.BEZIEHUNG_CHOICES
        if wert in BEZIEHUNG_ERLAEUTERUNGEN
    ]

    namen_je_artikel = {}
    for name in ZusaetzlicheSexualdelikte.objects.values_list("name", flat=True):
        namen_je_artikel.setdefault(artikel_aus_name(name), []).append(name)
    weitere_sexualdelikte = [
        {"value": artikel, "label": _artikel_label(artikel, namen)}
        for artikel, namen in sorted(namen_je_artikel.items(), key=lambda e: int(re.sub(r"\D", "", e[0]) or 0))
        if artikel
    ]

    besonderheiten = _besonderheiten_fragen(
        set(Besonderheiten.objects.filter(besonderheiten__isnull=False).values_list("name", flat=True))
    )

    return {
        "stichtag": STICHTAG_NEUES_RECHT,
        "hauptdelikte": hauptdelikte,
        "tatmittel": tatmittel,
        "opferalter": opferalter,
        "opferalter_text": OPFERALTER_ERLAEUTERUNG,
        "beziehungen": beziehungen,
        "weitere_sexualdelikte": weitere_sexualdelikte,
        "uebrige_delikte_text": UEBRIGE_DELIKTE_ERLAEUTERUNG,
        "besonderheiten": besonderheiten,
    }


def sexual_urteile_erstellen():
    """Normalisiert die Sexualdelikt-Urteile für die clientseitige Bewertung."""
    urteile = (
        SexualdeliktUrteil.objects.select_related("hauptdelikt", "hauptdelikt_tatmittel")
        .prefetch_related("sexualdelikte_zusaetzliche", "besonderheiten")
        .order_by("-urteilsdatum", "-pk")
    )
    datensaetze = []
    for urteil in urteile:
        weitere = [d.name for d in urteil.sexualdelikte_zusaetzliche.all()]
        datensaetze.append(
            {
                **_grundfelder(urteil, "sexualurteil_detail"),
                "hauptdelikt": urteil.hauptdelikt.name,
                "hauptdelikt_artikel": artikel_aus_name(urteil.hauptdelikt.name),
                "tatmittel": urteil.hauptdelikt_tatmittel.name,
                "opferalter": urteil.hauptdelikt_opferalter,
                "opferalter_label": urteil.get_hauptdelikt_opferalter_display(),
                "beziehung": urteil.hauptdelikt_taeter_opfer_beziehung,
                "mehrfach": urteil.hauptdelikt_mehrfachbegehung,
                "anzahl": urteil.hauptdelikt_mehrfachbegehung_anzahl,
                "weitere_sexualdelikte": weitere,
                "weitere_artikel": sorted({artikel_aus_name(n) for n in weitere} - {""}),
            }
        )
    return datensaetze


# --- Gewaltdelikte ---------------------------------------------------------------
#
# Strafrahmen gemäss Fedlex (SR 311.0), Stand 1.10.2026. Bei Art. 122 StGB
# gilt die Mindeststrafe von einem Jahr erst seit der Harmonisierung der
# Strafrahmen (1. Juli 2023); vorher Freiheitsstrafe bis zu 10 Jahren oder
# Geldstrafe nicht unter 180 Tagessätzen.

GEWALT_HAUPTDELIKT_GRUPPEN = [
    ("toetung", "Vorsätzliche Tötungsdelikte"),
    ("schwer", "Schwere Körperverletzung und Lebensgefährdung"),
    ("einfach", "Einfache Körperverletzung und Tätlichkeiten"),
    ("beteiligung", "Beteiligung an Schlägereien"),
    ("raub", "Raub"),
    ("fahrlaessig", "Fahrlässigkeitsdelikte"),
]

GEWALT_HAUPTDELIKT_ERLAEUTERUNGEN = {
    "Mord": {
        "gruppe": "toetung", "artikel": "112",
        "text": "Vorsätzliche Tötung, bei der der Täter besonders skrupellos handelt, namentlich wenn "
        "der Beweggrund, der Zweck der Tat oder die Art der Ausführung besonders verwerflich ist "
        "(z.B. Tötung aus Habgier, zur Verdeckung einer anderen Tat, mit besonderer Grausamkeit).",
        "strafrahmen": "lebenslängliche Freiheitsstrafe oder Freiheitsstrafe nicht unter 10 Jahren",
    },
    "vorsätzliche Tötung": {
        "gruppe": "toetung", "artikel": "111",
        "text": "Grundtatbestand: Wer vorsätzlich einen Menschen tötet, ohne dass die Merkmale des "
        "Mordes oder des Totschlags vorliegen. Häufig als Versuch, etwa bei Messerstichen in den "
        "Oberkörper, die das Opfer überlebt; dann genügt Eventualvorsatz bezüglich des Todes.",
        "strafrahmen": "Freiheitsstrafe nicht unter 5 Jahren",
    },
    "Totschlag": {
        "gruppe": "toetung", "artikel": "113",
        "text": "Vorsätzliche Tötung in einer nach den Umständen entschuldbaren heftigen "
        "Gemütsbewegung oder unter grosser seelischer Belastung (privilegierter Tatbestand).",
        "strafrahmen": "Freiheitsstrafe von 1 bis 10 Jahren",
    },
    "schwere Körperverletzung": {
        "gruppe": "schwer", "artikel": "122",
        "text": "Vorsätzliche lebensgefährliche Verletzung, Verstümmelung oder Unbrauchbarmachen eines "
        "wichtigen Organs, bleibende Arbeitsunfähigkeit, arge und bleibende Entstellung des Gesichts "
        "oder eine andere schwere Schädigung der Gesundheit.",
        "strafrahmen": "Freiheitsstrafe von 1 bis 10 Jahren (vor 1.7.2023: bis 10 Jahre oder Geldstrafe "
        "nicht unter 180 Tagessätzen)",
    },
    "Gefährdung des Lebens": {
        "gruppe": "schwer", "artikel": "129",
        "text": "Der Täter bringt einen Menschen in skrupelloser Weise in unmittelbare Lebensgefahr, "
        "ohne ihn töten zu wollen (z.B. Würgen bis zur Bewusstlosigkeit, Schuss in Richtung eines "
        "Menschen).",
        "strafrahmen": "Freiheitsstrafe bis zu 5 Jahren oder Geldstrafe",
    },
    "einfache Körperverletzung": {
        "gruppe": "einfach", "artikel": "123",
        "text": "Vorsätzliche Schädigung von Körper oder Gesundheit, die über eine Tätlichkeit "
        "hinausgeht, aber nicht schwer ist (z.B. Prellungen, Platzwunden, Nasenbeinbruch). Von Amtes "
        "wegen verfolgt (Ziff. 2) bei Einsatz einer Waffe oder eines gefährlichen Gegenstands, gegenüber "
        "Wehrlosen und Obhutsbefohlenen sowie in Ehe und Partnerschaft.",
        "strafrahmen": "Freiheitsstrafe bis zu 3 Jahren oder Geldstrafe",
    },
    "Tätlichkeiten": {
        "gruppe": "einfach", "artikel": "126",
        "text": "Einwirkungen auf den Körper ohne Schädigung von Körper oder Gesundheit (z.B. Ohrfeige, "
        "Stoss). Übertretung.",
        "strafrahmen": "Busse",
    },
    "Raufhandel": {
        "gruppe": "beteiligung", "artikel": "133",
        "text": "Beteiligung an einer Schlägerei unter mindestens drei Personen, die den Tod oder die "
        "Körperverletzung eines Menschen zur Folge hat. Strafbar ist schon die Beteiligung; wer genau "
        "die Verletzung verursacht hat, muss nicht feststehen.",
        "strafrahmen": "Freiheitsstrafe bis zu 3 Jahren oder Geldstrafe",
    },
    "Angriff": {
        "gruppe": "beteiligung", "artikel": "134",
        "text": "Beteiligung an einem einseitigen Angriff mehrerer Personen auf einen oder mehrere "
        "Menschen, der den Tod oder eine Körperverletzung zur Folge hat.",
        "strafrahmen": "Freiheitsstrafe bis zu 5 Jahren oder Geldstrafe",
    },
    "Raub": {
        "gruppe": "raub", "artikel": "140",
        "text": "Diebstahl unter Anwendung von Gewalt gegen eine Person, unter Androhung gegenwärtiger "
        "Gefahr für Leib oder Leben oder nach Herbeiführen der Widerstandsunfähigkeit. Qualifiziert, "
        "wenn der Täter eine Schusswaffe oder gefährliche Waffe mit sich führt (Ziff. 2), als "
        "Bandenmitglied oder mit besonderer Gefährlichkeit handelt (Ziff. 3) oder das Opfer in "
        "Lebensgefahr bringt, schwer verletzt oder grausam behandelt (Ziff. 4).",
        "strafrahmen": "Ziff. 1: 6 Monate bis 10 Jahre; Ziff. 2: nicht unter 1 Jahr; Ziff. 3: nicht unter "
        "2 Jahren; Ziff. 4: nicht unter 5 Jahren Freiheitsstrafe",
    },
    "fahrlässige Tötung": {
        "gruppe": "fahrlaessig", "artikel": "117",
        "text": "Der Täter verursacht den Tod eines Menschen durch pflichtwidrige Unvorsichtigkeit, "
        "typischerweise im Strassenverkehr oder bei Arbeitsunfällen.",
        "strafrahmen": "Freiheitsstrafe bis zu 3 Jahren oder Geldstrafe",
    },
    "fahrlässige Körperverletzung": {
        "gruppe": "fahrlaessig", "artikel": "125",
        "text": "Der Täter schädigt einen Menschen durch pflichtwidrige Unvorsichtigkeit an Körper oder "
        "Gesundheit; bei schwerer Schädigung von Amtes wegen verfolgt.",
        "strafrahmen": "Freiheitsstrafe bis zu 3 Jahren oder Geldstrafe",
    },
}

VERSUCH_ERLAEUTERUNG = (
    "Beim Versuch (Art. 22 StGB) führt der Täter die Tat nicht zu Ende oder der Erfolg tritt nicht "
    "ein, z.B. überlebt das Opfer einen mit Tötungsvorsatz geführten Messerstich. Das Gericht kann "
    "die Strafe mildern; das Mass hängt davon ab, wie nahe der Erfolg war und wie schwer die "
    "tatsächlichen Folgen sind. Gerade bei Tötungsdelikten ist der Versuch der Regelfall in der "
    "Datenbank und prägt die Strafe stark."
)

VORSATZ_ERLAEUTERUNGEN = {
    "direktvorsatz": "Der Täter will den Erfolg (z.B. den Tod oder die Verletzung) oder weiss, dass "
    "er sicher eintreten wird.",
    "eventualvorsatz": "Der Täter hält den Erfolg für möglich und nimmt ihn in Kauf, auch wenn er "
    "ihn nicht anstrebt, z.B. wer wuchtig mit dem Messer in den Oberkörper sticht und dabei den Tod "
    "des Opfers in Kauf nimmt. Wirkt sich gegenüber dem direkten Vorsatz in der Regel "
    "verschuldensmindernd aus.",
    "fahrlaessig": "Der Täter hat den Erfolg nicht gewollt und nicht in Kauf genommen, ihn aber "
    "durch pflichtwidrige Unvorsichtigkeit verursacht.",
}

# Ordinale Reihenfolge, mildeste zuerst (vgl. praejudizfinder_gewalt.js)
VORSATZ_REIHE = ("fahrlaessig", "eventualvorsatz", "direktvorsatz")
VERLETZUNGSFOLGE_REIHE = ("keine", "Tätlichkeit", "leicht", "erheblich", "schwer", "lebensgefährlich", "Tod")

VERLETZUNGSFOLGE_ERLAEUTERUNG = (
    "Die schwerste tatsächlich eingetretene Verletzung beim Opfer des Hauptdelikts, nicht was der "
    "Täter gewollt oder in Kauf genommen hat. Die Stufe ist darum auch beim "
    "Versuch unabhängig vom Schuldspruch zu wählen: Eine versuchte Tötung kann keine Folge haben "
    "(etwa weil ein Schuss verfehlt hat), eine vollendete einfache Körperverletzung kann eine "
    "erhebliche Verletzung nach sich ziehen. Neben dem "
    "Hauptdelikt ist sie das wichtigste Mass für das Tatverschulden; benachbarte Stufen gelten bei "
    "der Suche als teilweise übereinstimmend."
)

# Beschreibung der Stufen, abgeleitet aus der Verwendung im Bestand (die
# Stufen sind Kategorien der Datenbank, keine gesetzlichen Begriffe; nur
# «schwer» und «lebensgefährlich» knüpfen an Art. 122 StGB an).
VERLETZUNGSFOLGE_ERLAEUTERUNGEN = {
    "keine": {
        "text": "Keine körperliche Verletzung, z.B. ein Raub mit blosser Drohung oder ein Angriff, der "
        "das Opfer verfehlt hat. Auch eine <strong>versuchte Tötung ohne Verletzung</strong> gehört "
        "hierher, nicht zur Stufe «geringfügig».",
        "beispiele": ["Schuss, der das Opfer verfehlt", "Hammerschlag, dem das Opfer ausweichen kann"],
    },
    "Tätlichkeit": {
        "text": "Körperliche Einwirkung ohne eigentliche Schädigung der Gesundheit (vgl. Art. 126 StGB): "
        "Rötungen, kurzer Schmerz, kleinste Schürfungen.",
        "beispiele": ["Stoss zu Boden mit Rötungen an Hals und Kopf"],
    },
    "leicht": {
        "text": "Verletzungen, die rasch und ohne Folgen abheilen und keine oder nur eine kurze "
        "ambulante Behandlung erfordern: Prellungen, Hämatome, Schürfungen, oberflächliche Schnitt- "
        "oder Stichwunden.",
        "beispiele": [
            "Faustschläge ins Gesicht mit Hämatom am Auge",
            "oberflächliche Stichwunde am Unterarm",
        ],
    },
    "erheblich": {
        "text": "Deutlich mehr als leicht: Die Verletzung muss ärztlich versorgt werden (Naht, Operation, "
        "Spitalaufenthalt) oder führt zu einer längeren Arbeitsunfähigkeit, heilt aber "
        "<strong>ohne bleibende Schäden</strong> aus. Typisch für die einfache Körperverletzung im "
        "oberen Bereich und für Messerstiche ohne Organverletzung.",
        "beispiele": [
            "Bruch von Nasenbein oder Augenhöhlenboden",
            "Stichwunde im Oberschenkel, genäht",
            "Schädel-Hirn-Trauma mit kurzer Bewusstlosigkeit, folgenlos abgeheilt",
        ],
    },
    "schwer": {
        "text": "Schwere Schädigung im Sinne von Art. 122 lit. b oder c StGB: <strong>bleibende "
        "Folgen</strong> oder eine ähnlich schwerwiegende Beeinträchtigung der Gesundheit, ohne dass "
        "eine konkrete Lebensgefahr bestand. Dazu zählen der Verlust oder die Unbrauchbarkeit eines "
        "wichtigen Organs oder Glieds, eine bleibende Entstellung des Gesichts oder dauernde "
        "Arbeitsunfähigkeit.",
        "beispiele": [
            "Verlust des Sehvermögens auf einem Auge",
            "schwere Hirnverletzung mit Folgeschäden",
        ],
    },
    "lebensgefährlich": {
        "text": "Die Verletzung versetzte das Opfer in <strong>unmittelbare Lebensgefahr</strong> (Art. 122 "
        "lit. a StGB): Ohne rasche medizinische Hilfe hätte es sterben können. Ob bleibende Schäden "
        "zurückbleiben, ist nicht entscheidend.",
        "beispiele": [
            "Messerstich in Brust oder Bauch mit Organverletzung",
            "Würgen bis zur Bewusstlosigkeit mit Stauungssyndrom",
            "Hirnblutung, Atemstillstand",
        ],
    },
    "Tod": {
        "text": "Das Opfer ist an den Folgen der Tat gestorben.",
        "beispiele": [],
    },
}

VERLETZUNGSFOLGE_ABGRENZUNG = (
    "<strong>Erheblich oder schwer?</strong> Entscheidend ist, ob die Verletzung ausheilt. Ein "
    "Knochenbruch, eine genähte Stichwunde oder eine Gehirnerschütterung sind auch dann «erheblich», "
    "wenn sie eine Operation oder einige Wochen Arbeitsunfähigkeit nach sich ziehen. «Schwer» ist "
    "eine Verletzung erst, wenn bleibende Schäden zurückbleiben (z.B. Sehverlust, Entstellung, "
    "dauernde Beeinträchtigung) oder die Gesundheit vergleichbar gravierend geschädigt ist. "
    "<strong>Schwer oder lebensgefährlich?</strong> «Lebensgefährlich» setzt eine konkrete "
    "Todesgefahr voraus, die abstrakte Gefährlichkeit des Angriffs genügt nicht."
)

GEWALT_TATMITTEL_ERLAEUTERUNGEN = {
    "körperliche Gewalt": ("koerper", "Faustschläge, Fusstritte, Stossen, ohne Gegenstand."),
    "Würgen": ("koerper", "Würgen oder Drosseln am Hals; wegen der Erstickungsgefahr besonders gefährlich."),
    "Messer/Stichwaffe": ("waffe", "Messer, Stich- oder Schnittwerkzeug, auch improvisiert (z.B. abgebrochene Flasche)."),
    "Schusswaffe": ("waffe", "Pistole, Gewehr und andere Feuerwaffen."),
    "stumpfer Gegenstand": ("waffe", "Schlagstock, Baseballschläger, Flasche, Stein u.ä."),
    "Fahrzeug/Motorfahrzeug": ("fahrzeug", "Das Fahrzeug als Tatmittel, z.B. Anfahren eines Menschen."),
    "andere": ("andere", "Andere oder mehrere Tatmittel."),
}

GEWALT_QUALIFIKATIONEN = [
    {
        "value": "waffe_gefaehrlicher_gegenstand",
        "frage": "Wurde eine Waffe oder ein gefährlicher Gegenstand verwendet?",
        "text": "Qualifiziert z.B. den Raub (Art. 140 Ziff. 2 StGB: Mitführen einer Schusswaffe oder "
        "anderen gefährlichen Waffe) und macht die einfache Körperverletzung zum Offizialdelikt (Art. 123 "
        "Ziff. 2 StGB). Gefährlich ist ein Gegenstand, wenn er so verwendet wird, dass er eine schwere "
        "Verletzung bewirken kann.",
    },
    {
        "value": "besondere_gefaehrlichkeit",
        "frage": "Hat das Gericht eine besondere Gefährlichkeit oder Grausamkeit bejaht?",
        "text": "Etwa die besondere Gefährlichkeit beim Raub (Art. 140 Ziff. 3 StGB, z.B. bei sorgfältig "
        "geplanten Überfällen mit Waffen) oder die besondere Skrupellosigkeit des Mordes. Nur bejahen, "
        "wenn das Gericht diesen Umstand ausdrücklich festgestellt hat.",
    },
    {
        "value": "lebensgefahr",
        "frage": "Hat der Täter das Opfer in Lebensgefahr gebracht?",
        "text": "Die Herbeiführung einer konkreten Lebensgefahr, z.B. beim Raub nach Art. 140 Ziff. 4 StGB "
        "oder bei einer lebensgefährlichen Körperverletzung. Erhöht das Tatverschulden erheblich.",
    },
]

GEWALT_BEZIEHUNG_ERLAEUTERUNGEN = {
    "Partner/Ex-Partner": ("nah", "Ehe, Partnerschaft oder frühere Beziehung (häusliche Gewalt)."),
    "Familie": ("nah", "Eltern, Kinder, Geschwister und weitere Angehörige."),
    "Bekannte": ("bekannt", "Freunde, Nachbarn, Arbeitskollegen."),
    "flüchtig bekannt": ("bekannt", "Kurz vor der Tat kennengelernt, z.B. am selben Abend im Ausgang."),
    "Unbekannte": ("fremd", "Täter und Opfer kannten sich nicht, z.B. Streit auf der Strasse oder Überfall."),
}

GEWALT_KOERPERTEIL_ERLAEUTERUNG = (
    "Angriffe gegen Kopf und Hals gelten als besonders gefährlich, weil schon einzelne Schläge oder "
    "Stiche lebensgefährliche Folgen haben können."
)

SUBSTANZ_ERLAEUTERUNG = (
    "Alkohol- oder Drogeneinfluss kann die Schuldfähigkeit vermindern (Art. 19 StGB) und damit "
    "strafmindernd wirken, sofern ein Gutachten oder das Gericht eine Verminderung annimmt. Viele "
    "Urteile machen dazu keine Angaben; das Kriterium wiegt darum bei der Suche wenig."
)

DELIKTSSUMME_ERLAEUTERUNG = (
    "Beim Raub der Wert der Beute bzw. der erstrebten Vermögenswerte in Franken. Er wiegt bei der "
    "Strafzumessung meist weniger als die Art der Gewaltanwendung."
)


def gewalt_schritte_erstellen():
    """Optionen und Erläuterungen der Gewaltdelikt-Schritte, aus dem Bestand abgeleitet."""
    bestand = GewaltdeliktUrteil.objects.all()

    def anzahl_je(feld):
        anzahl = {}
        for wert in bestand.values_list(feld, flat=True):
            anzahl[wert] = anzahl.get(wert, 0) + 1
        return anzahl

    anzahl_hd = anzahl_je("hauptdelikt")
    hauptdelikte = []
    for wert, label in GewaltdeliktUrteil.HAUPTDELIKT:
        if not anzahl_hd.get(wert):
            continue
        erlaeuterung = GEWALT_HAUPTDELIKT_ERLAEUTERUNGEN.get(wert, {})
        hauptdelikte.append(
            {
                "value": wert,
                "label": label,
                "titel": wert[:1].upper() + wert[1:],
                "artikel": erlaeuterung.get("artikel", ""),
                "gruppe": erlaeuterung.get("gruppe", ""),
                "text": erlaeuterung.get("text", ""),
                "strafrahmen": erlaeuterung.get("strafrahmen", ""),
                "anzahl": anzahl_hd[wert],
            }
        )
    gruppen = [
        {"key": key, "titel": titel}
        for key, titel in GEWALT_HAUPTDELIKT_GRUPPEN
        if any(d["gruppe"] == key for d in hauptdelikte)
    ]

    anzahl_tm = anzahl_je("tatmittel")
    tatmittel = [
        {
            "value": wert,
            "label": label,
            "gruppe": GEWALT_TATMITTEL_ERLAEUTERUNGEN[wert][0],
            "text": GEWALT_TATMITTEL_ERLAEUTERUNGEN[wert][1],
        }
        for wert, label in GewaltdeliktUrteil.TATMITTEL
        if wert in GEWALT_TATMITTEL_ERLAEUTERUNGEN and anzahl_tm.get(wert)
    ]

    vorsatz_labels = dict(GewaltdeliktUrteil.VORSATZFORM)
    vorsatzformen = [
        {"value": wert, "label": vorsatz_labels[wert], "text": VORSATZ_ERLAEUTERUNGEN[wert]}
        for wert in VORSATZ_REIHE
    ]

    folge_labels = dict(GewaltdeliktUrteil.VERLETZUNGSFOLGE)
    anzahl_folge = anzahl_je("verletzungsfolge")
    verletzungsfolgen = [
        {
            "value": wert,
            "label": folge_labels[wert],
            "stufe": stufe,
            "anzahl": anzahl_folge.get(wert, 0),
            **VERLETZUNGSFOLGE_ERLAEUTERUNGEN[wert],
        }
        for stufe, wert in enumerate(VERLETZUNGSFOLGE_REIHE)
    ]

    koerperteile = [
        {"value": wert, "label": label}
        for wert, label in GewaltdeliktUrteil.KOERPERTEIL
        if wert != "unbekannt"
    ]
    beziehungen = [
        {
            "value": wert,
            "label": label,
            "gruppe": GEWALT_BEZIEHUNG_ERLAEUTERUNGEN[wert][0],
            "text": GEWALT_BEZIEHUNG_ERLAEUTERUNGEN[wert][1],
        }
        for wert, label in GewaltdeliktUrteil.BEZIEHUNG_CHOICES
        if wert in GEWALT_BEZIEHUNG_ERLAEUTERUNGEN
    ]
    substanzen = [
        {"value": wert, "label": label}
        for wert, label in GewaltdeliktUrteil.SUBSTANZEINFLUSS
        if wert != "unbekannt"
    ]

    # Versuch ist bei den Gewaltdelikten ein eigenes Modellfeld und wird mit
    # dem Hauptdelikt gefragt, nicht als Besonderheit.
    besonderheiten = _besonderheiten_fragen(
        set(Besonderheiten.objects.filter(gewaltdelikte__isnull=False).values_list("name", flat=True)),
        ausser=("Versuch",),
    )

    return {
        "hauptdelikte": hauptdelikte,
        "hauptdelikt_gruppen": gruppen,
        "versuch_text": VERSUCH_ERLAEUTERUNG,
        "vorsatzformen": vorsatzformen,
        "tatmittel": tatmittel,
        "qualifikationen": GEWALT_QUALIFIKATIONEN,
        "verletzungsfolgen": verletzungsfolgen,
        "verletzungsfolge_text": VERLETZUNGSFOLGE_ERLAEUTERUNG,
        "verletzungsfolge_abgrenzung": VERLETZUNGSFOLGE_ABGRENZUNG,
        "koerperteile": koerperteile,
        "koerperteil_text": GEWALT_KOERPERTEIL_ERLAEUTERUNG,
        "beziehungen": beziehungen,
        "substanzen": substanzen,
        "substanz_text": SUBSTANZ_ERLAEUTERUNG,
        "deliktssumme_text": DELIKTSSUMME_ERLAEUTERUNG,
        "uebrige_delikte_text": UEBRIGE_DELIKTE_ERLAEUTERUNG,
        "besonderheiten": besonderheiten,
    }


def gewalt_urteile_erstellen():
    """Normalisiert die Gewaltdelikt-Urteile für die clientseitige Bewertung."""
    urteile = GewaltdeliktUrteil.objects.prefetch_related("besonderheiten").order_by("-urteilsdatum", "-pk")
    return [
        {
            **_grundfelder(urteil, "gewalturteil_detail"),
            "hauptdelikt": urteil.hauptdelikt,
            "hauptdelikt_label": urteil.get_hauptdelikt_display(),
            "versuch": urteil.versuch,
            "vorsatzform": urteil.vorsatzform,
            "vorsatzform_label": urteil.get_vorsatzform_display(),
            "tatmittel": urteil.tatmittel,
            "tatmittel_label": urteil.get_tatmittel_display(),
            "waffe_gefaehrlicher_gegenstand": urteil.waffe_gefaehrlicher_gegenstand,
            "besondere_gefaehrlichkeit": urteil.besondere_gefaehrlichkeit,
            "lebensgefahr": urteil.lebensgefahr,
            "mehrfach": urteil.mehrfach,
            "opferzahl": urteil.opferzahl,
            "beziehung": urteil.taeter_opfer_beziehung,
            "beziehung_label": urteil.get_taeter_opfer_beziehung_display(),
            "verletzungsfolge": urteil.verletzungsfolge,
            "verletzungsfolge_label": urteil.get_verletzungsfolge_display(),
            "koerperteil": urteil.angegriffenes_koerperteil,
            "koerperteil_label": urteil.get_angegriffenes_koerperteil_display(),
            "substanzeinfluss": urteil.substanzeinfluss,
            "substanzeinfluss_label": urteil.get_substanzeinfluss_display(),
            "deliktssumme": urteil.deliktssumme,
        }
        for urteil in urteile
    ]
