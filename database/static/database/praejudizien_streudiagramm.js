/**
 * Streudiagramm aehnlicher Praejudizien auf den Prognoseseiten
 * (Vermoegens- und Betm-Delikte, siehe ``prognose_streudiagramm.html``).
 *
 * Baut auf ``urteilsFilter`` (filter.js) auf, statt die Diagrammlogik zu
 * duplizieren: Achsen, Punkte, Hover-Karten und Strafmass-Umrechnung
 * (kombinierte Ansicht, 30 Tagessaetze = 1 Monat) sind identisch zu den
 * Streudiagrammen der Urteilslisten - bei den Vermoegensdelikten
 * ``streudiagrammVM()`` (Deliktssumme), bei den Betm-Delikten
 * ``streudiagramm()`` (Menge einer Substanz, rein und Gemisch
 * zusammengefasst wie in der Liste ohne Wahl der Bemessungsgrundlage). Es gibt
 * hier aber kein Filterpanel - die "Treffermenge" sind die vom View nach
 * KNN-Distanz ausgewaehlten naechsten Nachbarn der Eingabe
 * (``_praejudizien_streudiagramm_daten`` in views.py), die x-Achse legt der
 * View fest (``achse``).
 *
 * Zusaetzlich zu den Urteilslisten:
 * - die Eingabe (senkrechte Linie) und die Strafmassprognose des KI-Modells
 *   (senkrechter Farbverlauf wie im Verlaufsdiagramm oberhalb) werden
 *   eingezeichnet, siehe ``eingabeSvg``/``prognoseSvg``;
 * - die unterhalb als Karten angezeigten Praejudizien sind golden umrandet
 *   (``istHervorgehoben``).
 */
function praejudizienStreudiagramm(datenId) {
  const basis = urteilsFilter(null, null);
  return {
    ...basis,
    achse: { typ: "deliktssumme", label: "", einheit: "" },
    eingabe: { menge: null, strafmass: null },
    verlauf: null,

    init() {
      const daten = JSON.parse(document.getElementById(datenId).textContent);
      this.achse = daten.achse;
      this.records = daten.records;
      this.trefferPks = Object.keys(daten.records);
      this.eingabe = daten.eingabe;
      this.verlauf = daten.verlauf;
      // Die Streudiagramm-Funktionen aus filter.js lesen Label/Einheit und
      // (bei Betm) die gewaehlte Substanz aus Filterspezifikation, -zustand
      // und Spannen; ein Filterpanel gibt es hier nicht, darum fest gesetzt.
      if (this.achse.typ === "betm") {
        this.spec = { felder: [{ name: "betm" }], gruppen: [] };
        this.zustand = { betm: [this.achse.substanz], betm_menge: { basis: null } };
        this.spannen = {
          betm_menge: { label: this.achse.label, einheit: this.achse.einheit },
        };
      } else {
        this.spec = {
          felder: [
            { name: "deliktssumme", label: this.achse.label, einheit: this.achse.einheit },
          ],
          gruppen: [],
        };
      }
      window.addEventListener("scroll", () => this.streudiagrammPunktVerbergen(), {
        passive: true,
      });
      window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") this.streudiagrammPunktVerbergen();
      });
    },

    /** Golden umrandet: die unterhalb als Karten angezeigten Praejudizien. */
    istHervorgehoben(record) {
      return Boolean(record.angezeigt);
    },

    /** Eingegebene Menge/Deliktssumme, sofern auf der log. Achse darstellbar. */
    eingabeMenge() {
      const wert = this.eingabe.menge;
      return wert !== null && wert > 0 ? wert : null;
    },

    /**
     * Wie in der Urteilsliste, aber mit Achsenbereichen, die auch die Eingabe
     * und die Prognose umfassen - sonst laege die Markierung bei einer Eingabe
     * ausserhalb der Nachbarn neben dem Diagramm.
     */
    praejudizienDiagramm() {
      const daten =
        this.achse.typ === "betm"
          ? basis.streudiagramm.call(this)
          : basis.streudiagrammVM.call(this);
      if (daten === null) return null;
      const menge = this.eingabeMenge();
      if (menge !== null) {
        const mengen = daten.punkte.map((p) => p.menge).concat([menge]);
        daten.mengeDomain = this.streudiagrammMengeDomain(
          Math.min(...mengen),
          Math.max(...mengen)
        );
      }
      const bereich = this.prognoseBereich();
      if (bereich !== null) {
        daten.strafmassMax = Math.max(daten.strafmassMax, bereich.rechts);
      }
      return daten;
    },

    /**
     * Wertebereich des Prognoseverlaufs in Monaten, wie ``verlauf_erstellen``
     * (prognoseverlauf.py): voll gefaerbter Kern (``kernbreite``) mittig ueber
     * der Prognose, nach beiden Seiten ``ausblendung`` Monate Ausblendung, unten
     * bei 0 gekappt. Null ohne Prognose (Bagatelldelikt).
     */
    prognoseBereich() {
      const prognose = this.eingabe.strafmass;
      if (prognose === null || prognose <= 0 || !this.verlauf) return null;
      const { kernbreite, ausblendung } = this.verlauf;
      const untere = Math.max(prognose - kernbreite / 2, 0);
      const obere = prognose + kernbreite / 2;
      return {
        links: Math.max(untere - ausblendung, 0),
        untere,
        obere,
        rechts: obere + ausblendung,
      };
    },

    /** Senkrechte Linie bei der eingegebenen Deliktssumme bzw. Menge. */
    eingabeSvg(daten) {
      const summe = this.eingabeMenge();
      if (summe === null) return "";
      const x = this.streudiagrammX(daten, summe);
      return `<line class="streudiagramm-eingabe" x1="${x}" x2="${x}" y1="12" y2="270"></line>`;
    },

    /**
     * Strafmassprognose als senkrechter Farbverlauf entlang der Eingabelinie -
     * dieselbe Blau-Rampe, Kernbreite und Ausblendung wie das Verlaufsdiagramm
     * oberhalb (``prognoseverlauf.html``), nur um 90 Grad gedreht. Statt zur
     * Seitenfarbe (weiss) blendet der Verlauf hier ueber die Deckkraft aus,
     * damit Gitterlinien und Punkte darunter sichtbar bleiben (auch im
     * Dark Mode). Seitlich blendet eine Maske den Verlauf ebenfalls aus, damit
     * er als weicher Bereich und nicht als harter Balken erscheint - die
     * Breite ist ohne Bedeutung, nur die Hoehe (Strafmass) traegt Information.
     * Wird unter den Punkten gezeichnet, damit diese anklickbar
     * bleiben. Als SVG-Markup aus demselben Grund wie
     * ``streudiagrammAchsenSvg`` (filter.js).
     */
    prognoseSvg(daten) {
      const summe = this.eingabeMenge();
      const bereich = this.prognoseBereich();
      if (summe === null || bereich === null) return "";
      const { links, untere, obere, rechts } = bereich;
      const rampe = this.verlauf.rampe;
      const stufen = rampe.length - 1;
      // Offsets relativ zum Band: 0 = oberer Rand (rechts), 1 = unterer (links)
      const offset = (wert) => ((rechts - wert) / (rechts - links)) * 100;
      const stop = (wert, i) =>
        `<stop offset="${offset(wert).toFixed(2)}%" stop-color="${rampe[i]}" ` +
        `stop-opacity="${(0.75 * (1 - i / stufen)).toFixed(3)}"></stop>`;
      const stops = [];
      // Oben ausgeblendet -> voll, Kern durchgehend voll, voll -> unten ausgeblendet.
      for (let i = stufen; i >= 0; i -= 1) {
        stops.push(stop(obere + ((rechts - obere) * i) / stufen, i));
      }
      stops.push(stop(untere, 0));
      for (let i = 1; i <= stufen; i += 1) {
        stops.push(stop(untere - ((untere - links) * i) / stufen, i));
      }

      const x = this.streudiagrammX(daten, summe);
      const yOben = this.streudiagrammY(daten, rechts);
      const yUnten = this.streudiagrammY(daten, links);
      const breite = 30;
      const xLinks = x - breite / 2;
      const flaeche = `x="${xLinks}" y="${yOben}" width="${breite}" height="${yUnten - yOben}"`;
      return (
        `<defs>` +
        `<linearGradient id="prognose-verlauf" x1="0" y1="0" x2="0" y2="1">${stops.join("")}</linearGradient>` +
        `<linearGradient id="prognose-verlauf-seitlich" x1="0" y1="0" x2="1" y2="0">` +
        `<stop offset="0%" stop-color="#000"></stop>` +
        `<stop offset="35%" stop-color="#fff"></stop>` +
        `<stop offset="65%" stop-color="#fff"></stop>` +
        `<stop offset="100%" stop-color="#000"></stop>` +
        `</linearGradient>` +
        `<mask id="prognose-verlauf-maske" maskUnits="userSpaceOnUse" ${flaeche}>` +
        `<rect ${flaeche} fill="url(#prognose-verlauf-seitlich)"></rect>` +
        `</mask>` +
        `</defs>` +
        `<rect class="streudiagramm-prognose" ${flaeche} ` +
        `fill="url(#prognose-verlauf)" mask="url(#prognose-verlauf-maske)">` +
        `<title>Prognosebereich</title></rect>`
      );
    },
  };
}
