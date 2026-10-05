/**
 * Streudiagramm aehnlicher Praejudizien auf der Prognoseseite
 * (Vermoegensdelikte, siehe ``prognose_streudiagramm.html``).
 *
 * Baut auf ``urteilsFilter`` (filter.js) auf, statt die Diagrammlogik zu
 * duplizieren: Achsen, Punkte, Hover-Karten und Strafmass-Umrechnung
 * (kombinierte Ansicht, 30 Tagessaetze = 1 Monat) sind identisch zum
 * Streudiagramm der Urteilsliste. Es gibt hier aber kein Filterpanel - die
 * "Treffermenge" sind die vom View nach KNN-Distanz ausgewaehlten naechsten
 * Nachbarn der Eingabe (``_praejudizien_streudiagramm_daten`` in views.py).
 *
 * Zusaetzlich zur Urteilsliste:
 * - die Eingabe (Deliktssumme, senkrechte Linie) und die Strafmassprognose
 *   des KI-Modells (Raute) werden eingezeichnet, siehe ``eingabeSvg``;
 * - die oben als Karten angezeigten Praejudizien sind golden umrandet
 *   (``istHervorgehoben``).
 */
function praejudizienStreudiagramm(datenId) {
  const basis = urteilsFilter(null, null);
  return {
    ...basis,
    eingabe: { deliktssumme: null, strafmass: null },

    init() {
      const daten = JSON.parse(document.getElementById(datenId).textContent);
      // streudiagrammVM() liest Label und Einheit der Deliktssumme aus der
      // Filterspezifikation; ein Filterpanel gibt es hier nicht.
      this.spec = {
        felder: [{ name: "deliktssumme", label: "Deliktssumme", einheit: "CHF" }],
        gruppen: [],
      };
      this.records = daten.records;
      this.trefferPks = Object.keys(daten.records);
      this.eingabe = daten.eingabe;
      window.addEventListener("scroll", () => this.streudiagrammPunktVerbergen(), {
        passive: true,
      });
      window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") this.streudiagrammPunktVerbergen();
      });
    },

    /** Golden umrandet: die oben als Karten angezeigten Praejudizien. */
    istHervorgehoben(record) {
      return Boolean(record.angezeigt);
    },

    /** Eingegebene Deliktssumme, sofern auf der log. Achse darstellbar. */
    eingabeDeliktssumme() {
      const wert = this.eingabe.deliktssumme;
      return wert !== null && wert > 0 ? wert : null;
    },

    /**
     * Wie in der Urteilsliste, aber mit Achsenbereichen, die auch die Eingabe
     * und die Prognose umfassen - sonst laege die Markierung bei einer
     * Deliktssumme ausserhalb der Nachbarn neben dem Diagramm.
     */
    streudiagrammVM() {
      const daten = basis.streudiagrammVM.call(this);
      if (daten === null) return null;
      const summe = this.eingabeDeliktssumme();
      if (summe !== null) {
        const mengen = daten.punkte.map((p) => p.menge).concat([summe]);
        daten.mengeDomain = this.streudiagrammMengeDomain(
          Math.min(...mengen),
          Math.max(...mengen)
        );
      }
      if (this.eingabe.strafmass !== null) {
        daten.strafmassMax = Math.max(daten.strafmassMax, this.eingabe.strafmass);
      }
      return daten;
    },

    /**
     * Markierung der Eingabe: senkrechte Linie bei der eingegebenen
     * Deliktssumme und - falls eine Prognose vorliegt - eine Raute auf Hoehe
     * des prognostizierten Strafmasses. Als SVG-Markup aus demselben Grund wie
     * ``streudiagrammAchsenSvg`` (filter.js).
     */
    eingabeSvg(daten) {
      const summe = this.eingabeDeliktssumme();
      if (summe === null) return "";
      const x = this.streudiagrammX(daten, summe);
      let markup =
        `<line class="streudiagramm-eingabe" x1="${x}" x2="${x}" y1="12" y2="270"></line>`;
      if (this.eingabe.strafmass !== null) {
        const y = this.streudiagrammY(daten, this.eingabe.strafmass);
        const r = 7;
        const titel = this.escapeHtml(
          `Prognose: ${this.eingabe.strafmass.toFixed(1)} Monate bei ` +
            this.mengeAnzeige(summe, daten.einheit)
        );
        markup +=
          `<path class="streudiagramm-prognose" ` +
          `d="M ${x} ${y - r} L ${x + r} ${y} L ${x} ${y + r} L ${x - r} ${y} Z">` +
          `<title>${titel}</title></path>`;
      }
      return markup;
    },
  };
}
