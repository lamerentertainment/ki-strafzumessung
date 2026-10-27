"""
Geführte Präjudiziensuche ("Präjudizen finden") für Sexualdelikte.

Die Seite führt Schritt für Schritt durch die strafzumessungsrelevanten
Merkmale (Hauptdelikt, Tatmittel, Opfer, Tatbegehung, weitere Delikte, Täter)
und schlägt am Ende die ähnlichsten Urteile aus der Datenbank vor.

Hier stehen nur die Schrittdefinitionen mit ihren Erläuterungen sowie die
Normalisierung der Urteile in eine schlanke JSON-Struktur. Die eigentliche
Ähnlichkeitsbewertung geschieht clientseitig (siehe
``database/static/database/praejudizfinder_sexual.js``), damit jede Antwort
sofort auf die Trefferzahl durchschlägt, ohne Roundtrip - wie bei den
Filteransichten (``filterspec.py``).
"""

import re

from django.urls import reverse

from .models import (
    Besonderheiten,
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


def schritte_erstellen():
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

    vorhandene_besonderheiten = set(
        Besonderheiten.objects.filter(besonderheiten__isnull=False).values_list("name", flat=True)
    )
    besonderheiten = [
        {"value": name, **frage}
        for name, frage in BESONDERHEITEN_FRAGEN.items()
        if name in vorhandene_besonderheiten
    ]

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


def urteile_erstellen():
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
                "pk": urteil.pk,
                "url": reverse("sexualurteil_detail", args=[urteil.pk]),
                "pdf": urteil.url_link,
                "fall_nr": urteil.fall_nr,
                "gericht": urteil.gericht,
                "datum": urteil.urteilsdatum.strftime("%d.%m.%Y") if urteil.urteilsdatum else "",
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
        )
    return datensaetze
