/**
 * Clientseitige Filterung der Urteilslisten (Alpine.js).
 *
 * Django rendert die Tabellenzeilen wie bisher; diese Komponente liest die
 * normalisierten Felddaten aus einem json_script-Block und blendet Zeilen
 * per `hidden` ein bzw. aus. Ohne JavaScript bleibt die vollstaendige Liste
 * sichtbar.
 *
 * Filterlogik: ODER innerhalb eines Feldes, UND ueber die Felder hinweg.
 */
function urteilsFilter(spezifikationId, datensaetzeId) {
  return {
    spec: null,
    records: {},
    q: "",
    zustand: {},
    aufgeklappt: false,
    offeneGruppen: {},
    sortFeld: "",
    sortRichtung: "asc",
    trefferPks: [],
    facetten: {},
    spannen: {},
    // Sanktionsart, deren Strafhoehen die Kennzahlenleiste auswertet
    kennzahlenSanktion: "k",
    // Strafmasshistogramm (aufklappbar unterhalb des Filterpanels)
    histogrammOffen: true,
    histogrammKarte: null,
    histogrammKartePos: { x: 0, y: 0 },
    // Streudiagramm Strafmass/Menge bzw. Strafmass/Deliktssumme (Betm- bzw.
    // Vermoegensdelikte-Liste; siehe streudiagramm() und streudiagrammVM())
    streudiagrammOffen: true,
    streudiagrammPunktKarte: null,
    streudiagrammPunktKartePos: { x: 0, y: 0 },
    // Manuelle Hervorhebung bestimmter Hauptdelikte im VM-Streudiagramm
    // (goldene Punkte), unabhaengig vom Filter - siehe streudiagrammVM() und
    // streudiagrammHervorhebungUmschalten().
    streudiagrammHervorhebung: [],
    // Regressionsgerade im VM- bzw. Betm-Streudiagramm ein-/ausblenden
    // (bei Betm nur verfuegbar, wenn genau eine Substanz gewaehlt ist, siehe
    // streudiagramm()), siehe streudiagrammRegressionSvg() und
    // streudiagrammRegressionGleichung().
    streudiagrammRegressionAnzeigen: false,
    // Frei eingegebene Deliktssumme bzw. Menge (Gramm/Stk.) fuer die
    // Strafmass-Vorhersage anhand der Regressionsgeraden, siehe
    // streudiagrammRegressionVorhersage().
    streudiagrammRegressionEingabe: "",

    init() {
      this.spec = JSON.parse(document.getElementById(spezifikationId).textContent);
      this.records = JSON.parse(document.getElementById(datensaetzeId).textContent);
      this.spec.felder.forEach((feld) => {
        this.zustand[feld.name] = this.leererZustand(feld);
      });
      this.spec.gruppen.forEach((gruppe, index) => {
        this.offeneGruppen[gruppe.titel] = index === 0;
      });
      this.ausUrlLesen();
      // Die Karten haengen fix im Viewport und wuerden sonst beim Scrollen
      // neben ihrem Block/Punkt stehen bleiben.
      window.addEventListener("scroll", () => {
        this.karteVerbergen();
        this.streudiagrammPunktVerbergen();
      }, { passive: true });
      window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          this.karteVerbergen();
          this.streudiagrammPunktVerbergen();
        }
      });
      this.$watch("q", () => this.anwenden());
      this.$watch("zustand", () => this.anwenden(), { deep: true });
      this.anwenden();
    },

    leererZustand(feld) {
      if (feld.typ === "choice" || feld.typ === "multi") return [];
      if (feld.typ === "bool") return null;
      if (feld.typ === "abhaengige_spanne") return { min: "", max: "", basis: null };
      return { min: "", max: "" };
    },

    feldNach(name) {
      return this.spec.felder.find((feld) => feld.name === name);
    },

    // --- Treffer ermitteln ---------------------------------------------------

    passt(record, feld) {
      const zustand = this.zustand[feld.name];
      const wert = record[feld.name];
      if (feld.typ === "choice") {
        return zustand.length === 0 || zustand.includes(String(wert));
      }
      if (feld.typ === "multi") {
        if (zustand.length === 0) return true;
        const werte = wert || [];
        return zustand.some((auswahl) => werte.includes(auswahl));
      }
      if (feld.typ === "bool") {
        return zustand === null || wert === zustand;
      }
      if (feld.typ === "abhaengige_spanne") {
        return this.passtSpanne(record, feld);
      }
      // Zahlen und Daten: leere Grenze heisst "offen"
      const { min, max } = zustand;
      if (min === "" && max === "") return true;
      if (wert === null || wert === undefined) return false;
      if (feld.typ === "date") {
        if (min !== "" && wert < min) return false;
        if (max !== "" && wert > max) return false;
        return true;
      }
      if (min !== "" && wert < Number(min)) return false;
      if (max !== "" && wert > Number(max)) return false;
      return true;
    },

    /**
     * Abhaengige Spanne: bezieht sich auf die im Quellfeld gewaehlten Werte.
     * Ohne Auswahl dort greift sie nicht. Ein Urteil passt, wenn irgendeine
     * gewaehlte Substanz in der Spanne liegt - passend zur ODER-Logik der
     * Chips. Reine und Bruttomengen werden nie vermischt.
     */
    passtSpanne(record, feld) {
      const gewaehlt = this.zustand[feld.quelle];
      if (!gewaehlt || gewaehlt.length === 0) return true;
      const { min, max, basis } = this.zustand[feld.name];
      if (min === "" && max === "" && basis === null) return true;
      const mengen = record[feld.name] || {};
      const basen = basis === null ? ["rein", "gemisch"] : [basis];
      return gewaehlt.some((schluessel) => {
        const eintrag = mengen[schluessel];
        if (!eintrag) return false;
        return basen.some((b) => {
          const wert = eintrag[b];
          if (wert === undefined || wert === null) return false;
          if (min !== "" && wert < Number(min)) return false;
          if (max !== "" && wert > Number(max)) return false;
          return true;
        });
      });
    },

    trifftZu(record, ausserFeld) {
      if (this.q.trim() !== "") {
        const begriffe = this.q.toLowerCase().split(/\s+/).filter(Boolean);
        if (!begriffe.every((begriff) => record._t.includes(begriff))) return false;
      }
      return this.spec.felder.every(
        (feld) => feld.name === ausserFeld || this.passt(record, feld)
      );
    },

    anwenden() {
      const treffer = [];
      Object.entries(this.records).forEach(([pk, record]) => {
        if (this.trifftZu(record, null)) treffer.push(pk);
      });
      this.trefferPks = treffer;
      this.facettenBerechnen();
      this.spannenBerechnen();
      this.zeilenAktualisieren();
      this.inUrlSchreiben();
    },

    zeilenAktualisieren() {
      const sichtbar = new Set(this.trefferPks);
      const tbody = document.querySelector("[data-urteilsliste]");
      if (!tbody) return;
      const zeilen = Array.from(tbody.querySelectorAll("tr[data-pk]"));
      zeilen.forEach((zeile) => {
        zeile.hidden = !sichtbar.has(zeile.dataset.pk);
      });
      if (this.sortFeld) this.zeilenSortieren(tbody, zeilen);
    },

    zeilenSortieren(tbody, zeilen) {
      const richtung = this.sortRichtung === "asc" ? 1 : -1;
      const sortiert = zeilen.slice().sort((a, b) => {
        const wertA = this.records[a.dataset.pk][this.sortFeld];
        const wertB = this.records[b.dataset.pk][this.sortFeld];
        if (wertA === null || wertA === undefined) return 1;
        if (wertB === null || wertB === undefined) return -1;
        if (wertA === wertB) return 0;
        return (wertA > wertB ? 1 : -1) * richtung;
      });
      sortiert.forEach((zeile) => tbody.appendChild(zeile));
    },

    sortieren(feldname) {
      if (this.sortFeld === feldname) {
        this.sortRichtung = this.sortRichtung === "asc" ? "desc" : "asc";
      } else {
        this.sortFeld = feldname;
        this.sortRichtung = "asc";
      }
      this.zeilenAktualisieren();
    },

    sortSymbol(feldname) {
      if (this.sortFeld !== feldname) return "";
      return this.sortRichtung === "asc" ? "▲" : "▼";
    },

    // --- Facettierte Trefferzahlen ------------------------------------------
    // Anzahl je Option unter Beruecksichtigung aller UEBRIGEN aktiven Filter,
    // damit man sich nie in eine leere Ergebnismenge klicken kann.

    facettenBerechnen() {
      const ergebnis = {};
      this.spec.felder.forEach((feld) => {
        if (!["choice", "multi", "bool"].includes(feld.typ)) return;
        const zaehler = {};
        Object.values(this.records).forEach((record) => {
          if (!this.trifftZu(record, feld.name)) return;
          const wert = record[feld.name];
          if (feld.typ === "multi") {
            (wert || []).forEach((eintrag) => {
              zaehler[eintrag] = (zaehler[eintrag] || 0) + 1;
            });
          } else {
            const schluessel = String(wert);
            zaehler[schluessel] = (zaehler[schluessel] || 0) + 1;
          }
        });
        ergebnis[feld.name] = zaehler;
      });
      this.facetten = ergebnis;
    },

    /**
     * Beschriftung, Einheit und Wertebereich einer abhaengigen Spanne, bezogen
     * auf die aktuell gewaehlten Quellwerte und die uebrigen aktiven Filter.
     * Die Grenzen des Gesamtbestands taugen hier nicht: Kokain reicht bis
     * 51'200 g, Marihuana bis 434'000 g.
     */
    spannenBerechnen() {
      const ergebnis = {};
      this.spec.felder.forEach((feld) => {
        if (feld.typ !== "abhaengige_spanne") return;
        const gewaehlt = this.zustand[feld.quelle] || [];
        const basis = this.zustand[feld.name].basis;
        const basen = basis === null ? ["rein", "gemisch"] : [basis];
        let min = null;
        let max = null;
        Object.values(this.records).forEach((record) => {
          if (!this.trifftZu(record, feld.name)) return;
          const mengen = record[feld.name] || {};
          gewaehlt.forEach((schluessel) => {
            const eintrag = mengen[schluessel];
            if (!eintrag) return;
            basen.forEach((b) => {
              const wert = eintrag[b];
              if (wert === undefined || wert === null) return;
              if (min === null || wert < min) min = wert;
              if (max === null || wert > max) max = wert;
            });
          });
        });
        const einheiten = new Set(
          gewaehlt.map((k) => feld.einheiten_je_schluessel[k] || feld.einheit)
        );
        let label = feld.label;
        if (gewaehlt.length === 1) label = `${feld.label} ${gewaehlt[0]}`;
        else if (gewaehlt.length === 2) label = `${feld.label} (${gewaehlt.join(" oder ")})`;
        else if (gewaehlt.length > 2) label = `${feld.label} (${gewaehlt.length} Substanzen)`;
        ergebnis[feld.name] = {
          label,
          // Bei gemischten Einheiten keine angeben, statt eine falsche
          einheit: einheiten.size === 1 ? [...einheiten][0] : "",
          min,
          max,
        };
      });
      this.spannen = ergebnis;
    },

    /** Trefferzahl einer Option unter den uebrigen aktiven Filtern. */
    anzahl(feldname, optionswert) {
      const zaehler = this.facetten[feldname];
      return zaehler ? zaehler[String(optionswert)] || 0 : 0;
    },

    // --- Bedienung -----------------------------------------------------------

    umschalten(feldname, wert) {
      const liste = this.zustand[feldname];
      const index = liste.indexOf(wert);
      if (index === -1) liste.push(wert);
      else liste.splice(index, 1);
      this.abhaengigeSynchronisieren();
    },

    /** Ohne Auswahl im Quellfeld hat die abhaengige Spanne keinen Bezug mehr. */
    abhaengigeSynchronisieren() {
      this.spec.felder.forEach((feld) => {
        if (feld.typ !== "abhaengige_spanne") return;
        if (this.zustand[feld.quelle].length === 0) {
          this.zustand[feld.name] = this.leererZustand(feld);
        }
      });
    },

    basisSetzen(feldname, wert) {
      const zustand = this.zustand[feldname];
      zustand.basis = zustand.basis === wert ? null : wert;
    },

    istGewaehlt(feldname, wert) {
      return this.zustand[feldname].includes(wert);
    },

    boolSetzen(feldname, wert) {
      this.zustand[feldname] = this.zustand[feldname] === wert ? null : wert;
    },

    aktiv(feld) {
      const zustand = this.zustand[feld.name];
      if (Array.isArray(zustand)) return zustand.length > 0;
      if (feld.typ === "bool") return zustand !== null;
      if (feld.typ === "abhaengige_spanne") {
        return (
          this.zustand[feld.quelle].length > 0 &&
          (zustand.min !== "" || zustand.max !== "" || zustand.basis !== null)
        );
      }
      return zustand.min !== "" || zustand.max !== "";
    },

    anzahlAktiv() {
      return this.spec.felder.filter((feld) => this.aktiv(feld)).length + (this.q.trim() ? 1 : 0);
    },

    aktiveGruppe(gruppe) {
      return gruppe.felder.filter((feld) => this.aktiv(feld)).length;
    },

    /** Aktive Filter als einzeln entfernbare Chips. */
    aktiveChips() {
      const chips = [];
      if (this.q.trim()) {
        chips.push({ label: `Suche: "${this.q.trim()}"`, feld: null });
      }
      this.spec.felder.forEach((feld) => {
        if (!this.aktiv(feld)) return;
        const zustand = this.zustand[feld.name];
        if (Array.isArray(zustand)) {
          const bezeichnungen = zustand.map((wert) => {
            const option = feld.optionen.find((o) => o.value === wert);
            return option ? option.label : wert;
          });
          chips.push({ label: `${feld.label}: ${bezeichnungen.join(" oder ")}`, feld: feld.name });
        } else if (feld.typ === "bool") {
          chips.push({ label: `${feld.label}: ${zustand ? "ja" : "nein"}`, feld: feld.name });
        } else if (feld.typ === "abhaengige_spanne") {
          const info = this.spannen[feld.name] || {};
          const teile = [];
          if (zustand.min !== "" || zustand.max !== "") {
            const von = zustand.min !== "" ? zustand.min : "…";
            const bis = zustand.max !== "" ? zustand.max : "…";
            teile.push(`${von} – ${bis} ${info.einheit || ""}`.trim());
          }
          if (zustand.basis !== null) teile.push(zustand.basis === "rein" ? "rein" : "Gemisch");
          chips.push({ label: `${info.label || feld.label}: ${teile.join(", ")}`, feld: feld.name });
        } else {
          const von = zustand.min !== "" ? zustand.min : "…";
          const bis = zustand.max !== "" ? zustand.max : "…";
          chips.push({ label: `${feld.label}: ${von} – ${bis} ${feld.einheit}`.trim(), feld: feld.name });
        }
      });
      return chips;
    },

    chipEntfernen(feldname) {
      if (feldname === null) {
        this.q = "";
        return;
      }
      this.zustand[feldname] = this.leererZustand(this.feldNach(feldname));
      this.abhaengigeSynchronisieren();
    },

    zuruecksetzen() {
      this.q = "";
      this.spec.felder.forEach((feld) => {
        this.zustand[feld.name] = this.leererZustand(feld);
      });
    },

    // --- Kennzahlen zur Treffermenge ----------------------------------------

    /** Umrechnungssatz der kombinierten Ansicht: 30 Tagessaetze = 1 Monat. */
    TAGESSAETZE_JE_MONAT: 30,

    /**
     * Sanktionsarten mit auswertbarer Strafhoehe, in der Reihenfolge des
     * Umschaltens. Die Busse ('2') fehlt, weil ihre Hoehe in keinem Modell
     * erfasst ist.
     *
     * Die kombinierte Ansicht steht voran und ist damit die Voreinstellung:
     * Sie rechnet Geldstrafen in Monate um und legt beide Sanktionsarten auf
     * eine Achse - sonst zerfaellt jede Treffermenge in zwei Teilbestaende,
     * die man nicht nebeneinander lesen kann.
     */
    sanktionsarten: [
      {
        code: "k",
        label: "Freiheits- und Geldstrafe",
        kombiniert: true,
        einheit: "Mt.",
        einheitDativ: "Monaten",
        monate: true,
        // Umgerechnete Werte liegen zwischen den Monatsstufen
        nachkomma: 1,
        hinweis: "Geldstrafen zu 30 Tagessätzen je Monat umgerechnet",
      },
      {
        code: "0",
        label: "Freiheitsstrafe",
        feld: "freiheitsstrafe_in_monaten",
        einheit: "Mt.",
        einheitDativ: "Monaten",
        monate: true,
        nachkomma: 0,
        hinweis: "",
      },
      {
        code: "1",
        label: "Geldstrafe",
        feld: "anzahl_tagessaetze",
        einheit: "Tagessätze",
        einheitDativ: "Tagessätzen",
        monate: false,
        nachkomma: 0,
        hinweis: "",
      },
    ],

    /** Platzhalterwert in freiheitsstrafe_in_monaten fuer eine lebenslaengliche Strafe. */
    LEBENSLAENGLICH_PLATZHALTER: 999,

    /**
     * Strafhoehe eines Urteils in der Einheit der gewaehlten Sanktionsart,
     * oder null, wenn das Urteil dort nicht hineingehoert.
     *
     * In der kombinierten Ansicht zaehlen Freiheits- und Geldstrafen
     * gemeinsam, letztere zum Satz von 30 Tagessaetzen je Monat. Bussen
     * bleiben ueberall aussen vor: ihre Hoehe ist in keinem Modell erfasst.
     * Lebenslaengliche Freiheitsstrafen (Platzhalter 999) verzerren
     * Mittelwert/Median/Histogrammklassen und bleiben darum aussen vor.
     */
    strafhoehe(record, art) {
      const zahl = (wert) => (wert === null || wert === undefined ? null : wert);
      const freiheitsstrafe = (wert) =>
        wert === this.LEBENSLAENGLICH_PLATZHALTER ? null : zahl(wert);
      if (!art.kombiniert) {
        if (art.code === "0") {
          return record.hauptsanktion === art.code
            ? freiheitsstrafe(record.freiheitsstrafe_in_monaten)
            : null;
        }
        return record.hauptsanktion === art.code ? zahl(record[art.feld]) : null;
      }
      if (record.hauptsanktion === "0") return freiheitsstrafe(record.freiheitsstrafe_in_monaten);
      if (record.hauptsanktion === "1") {
        const tagessaetze = zahl(record.anzahl_tagessaetze);
        return tagessaetze === null ? null : tagessaetze / this.TAGESSAETZE_JE_MONAT;
      }
      return null;
    },

    /** Strafhoehe als Anzeigetext, in der Genauigkeit der Sanktionsart. */
    formatiert(wert, art) {
      if (wert === null || wert === undefined) return "";
      return wert.toFixed(art.nachkomma);
    },

    /**
     * Strafhoehen der Treffer je Sanktionsart, aufsteigend sortiert; nur die
     * Arten, zu denen die Treffermenge ueberhaupt Werte hergibt.
     *
     * in_ki_modell=false schliesst ein Urteil nur vom KI-Modelltraining aus,
     * nicht von der Statistik hier - es zaehlt wie jedes andere zur
     * Stichprobe.
     */
    sanktionsstichproben() {
      const stichproben = this.sanktionsarten.map((art) => ({ art, werte: [] }));
      this.trefferPks.forEach((pk) => {
        const record = this.records[pk];
        stichproben.forEach((eintrag) => {
          const wert = this.strafhoehe(record, eintrag.art);
          if (wert !== null) eintrag.werte.push(wert);
        });
      });
      stichproben.forEach((s) => s.werte.sort((a, b) => a - b));
      return stichproben.filter((s) => s.werte.length > 0);
    },

    /**
     * Angezeigte Stichprobe: die gewaehlte Sanktionsart, solange die
     * Treffermenge dazu Werte hergibt, sonst die erste belegte. Ohne jede
     * auswertbare Sanktion null.
     */
    aktiveStichprobe() {
      const belegt = this.sanktionsstichproben();
      return belegt.find((s) => s.art.code === this.kennzahlenSanktion) || belegt[0] || null;
    },

    /** Wechselt auf die naechste Sanktionsart, zu der es Werte gibt. */
    sanktionUmschalten() {
      const belegt = this.sanktionsstichproben();
      if (belegt.length < 2) return;
      const aktuell = this.aktiveStichprobe();
      const index = belegt.findIndex((s) => s.art.code === aktuell.art.code);
      this.kennzahlenSanktion = belegt[(index + 1) % belegt.length].art.code;
    },

    kennzahlen() {
      const treffer = this.trefferPks.map((pk) => this.records[pk]);
      const vollzug = { "0": 0, "1": 0, "2": 0 };
      treffer.forEach((record) => {
        if (vollzug[record.vollzug] !== undefined) vollzug[record.vollzug] += 1;
      });
      return {
        anzahl: treffer.length,
        gesamt: Object.keys(this.records).length,
        sanktion: this.sanktionskennzahlen(),
        bedingt: vollzug["0"],
        teilbedingt: vollzug["1"],
        unbedingt: vollzug["2"],
      };
    },

    /** Median, Mittel, mittlere Abweichung und Spanne der angezeigten Sanktion. */
    sanktionskennzahlen() {
      const belegt = this.sanktionsstichproben();
      const stichprobe = this.aktiveStichprobe();
      if (stichprobe === null) return { anzahl: 0, umschaltbar: false, umschaltTitel: "" };
      const { art, werte } = stichprobe;
      const mittelwert = werte.reduce((a, b) => a + b, 0) / werte.length;
      const index = belegt.findIndex((s) => s.art.code === art.code);
      const naechste = belegt[(index + 1) % belegt.length].art;
      return {
        label: art.label,
        einheit: art.einheit,
        einheitDativ: art.einheitDativ,
        anzahl: werte.length,
        median: this.formatiert(this.median(werte), art),
        mittel: this.formatiert(mittelwert, art),
        // mittlere absolute Abweichung vom (ungerundeten) Mittelwert
        mad: this.formatiert(
          werte.reduce((summe, wert) => summe + Math.abs(wert - mittelwert), 0) / werte.length,
          art
        ),
        min: this.formatiert(werte[0], art),
        max: this.formatiert(werte[werte.length - 1], art),
        umschaltbar: belegt.length > 1,
        // Der Hinweis zur Umrechnung gehoert an dieselbe Stelle wie der
        // Umschalter - dort fragt man sich, was die Zahlen bedeuten.
        umschaltTitel: [
          art.hinweis,
          belegt.length > 1 ? `Kennzahlen zur ${naechste.label} anzeigen` : "",
        ]
          .filter(Boolean)
          .join(" · "),
      };
    },

    /** Median der (aufsteigend sortierten) Werte, ungerundet. */
    median(werte) {
      if (!werte.length) return null;
      const mitte = Math.floor(werte.length / 2);
      return werte.length % 2 ? werte[mitte] : (werte[mitte - 1] + werte[mitte]) / 2;
    },

    /**
     * Tooltip zu einer Strafhoehe der angezeigten Sanktionsart. Nur Monate
     * lassen sich als "X Jahre Y Monate" lesen, Tagessaetze nicht.
     */
    strafhoeheTitel(wert) {
      const stichprobe = this.aktiveStichprobe();
      return stichprobe && stichprobe.art.monate ? this.jahreMonateTitel(wert) : "";
    },

    /**
     * Wandelt eine Monatszahl in "X Jahre Y Monate" um, als Titel fuer eine
     * Tooltip-Anzeige (z.B. bei Median/Durchschnitt der Freiheitsstrafe).
     * Ab 12 Monaten sinnvoll; darunter (oder ohne Wert) leerer String, sodass
     * kein Tooltip erscheint.
     *
     * Nimmt auch die formatierten Anzeigewerte der Kennzahlenleiste entgegen,
     * die in der kombinierten Ansicht eine Nachkommastelle tragen.
     */
    jahreMonateTitel(monate) {
      const wert = Number(monate);
      if (monate === null || monate === undefined || monate === "" || Number.isNaN(wert)) {
        return "";
      }
      if (wert <= 12) return "";
      const jahre = Math.floor(wert / 12);
      const rest = Math.round((wert % 12) * 10) / 10;
      const teile = [`${jahre} ${jahre === 1 ? "Jahr" : "Jahre"}`];
      if (rest > 0) teile.push(`${rest} ${rest === 1 ? "Monat" : "Monate"}`);
      return teile.join(" ");
    },

    // --- Strafmasshistogramm -------------------------------------------------

    /**
     * Klassenbreiten je Sanktionsart, aufsteigend. Die Freiheitsstrafe wird in
     * Monaten erfasst, soll auf der Achse aber in Jahresschritten lesbar sein -
     * darum die Sprungfolge 1/3/6/12/24/60 Monate statt einer "schoenen"
     * Rundung nach Sturges o.ae.
     */
    klassenbreiten: {
      k: [1, 3, 6, 12, 24, 60],
      "0": [1, 3, 6, 12, 24, 60],
      "1": [10, 30, 60, 90, 180, 360],
    },

    /** Kleinste Breite, die die Spannweite auf hoechstens 16 Klassen aufteilt. */
    klassenbreite(art, min, max) {
      const kandidaten = this.klassenbreiten[art.code] || [1];
      const spanne = Math.max(max - min, 1);
      return (
        kandidaten.find((breite) => spanne / breite <= 16) ||
        kandidaten[kandidaten.length - 1]
      );
    },

    /**
     * Histogramm der angezeigten Sanktionsart: je Klasse die einzelnen Urteile,
     * damit jedes als eigener Block im Balken erscheint und einzeln
     * angesteuert werden kann.
     *
     * Ausgewertet wird dieselbe Stichprobe wie in der Kennzahlenleiste (siehe
     * sanktionsstichproben()); der Umschalter dort wirkt also auch hier.
     */
    histogramm() {
      const stichprobe = this.aktiveStichprobe();
      if (stichprobe === null) return null;
      const { art } = stichprobe;

      const eintraege = [];
      this.trefferPks.forEach((pk) => {
        const record = this.records[pk];
        const wert = this.strafhoehe(record, art);
        if (wert === null) return;
        eintraege.push({
          pk,
          wert,
          // Eigene Sanktionsart des Urteils: sie faerbt den Block und erlaubt
          // im Tooltip die Angabe der urspruenglichen Tagessaetze.
          hauptsanktion: record.hauptsanktion,
          tagessaetze: record.anzahl_tagessaetze,
          karte: record._karte || {},
          vollzug: record.vollzug,
        });
      });
      if (eintraege.length === 0) return null;

      const werte = eintraege.map((e) => e.wert);
      const min = Math.min(...werte);
      const max = Math.max(...werte);
      const breite = this.klassenbreite(art, min, max);
      const untergrenze = Math.floor(min / breite) * breite;
      const anzahlKlassen = Math.floor((max - untergrenze) / breite) + 1;

      const klassen = Array.from({ length: anzahlKlassen }, (_, i) => ({
        von: untergrenze + i * breite,
        bis: untergrenze + (i + 1) * breite,
        urteile: [],
      }));
      eintraege
        .sort((a, b) => a.wert - b.wert)
        .forEach((eintrag) => {
          const index = Math.min(
            Math.floor((eintrag.wert - untergrenze) / breite),
            anzahlKlassen - 1
          );
          klassen[index].urteile.push(eintrag);
        });

      const hoechste = Math.max(...klassen.map((k) => k.urteile.length));
      klassen.forEach((klasse) => {
        klasse.urteile.sort(
          (a, b) => this.blockRang(a) - this.blockRang(b) || a.wert - b.wert
        );
        klasse.label = this.klassenlabel(art, klasse.von, klasse.bis);
      });
      return {
        art,
        klassen,
        breite,
        hoechste,
        anzahl: eintraege.length,
        // Gesamthoehe rund 220 px, aber nie unter 5 px je Urteil
        blockHoehe: Math.max(5, Math.min(22, Math.round(220 / hoechste))),
        achstitel: art.monate ? "Strafmass (Jahre)" : "Strafmass (Tagessätze)",
        // Farblegende: nur die Sanktionsarten, die im Bild vorkommen
        sanktionen: this.sanktionsarten.filter(
          (eine) =>
            !eine.kombiniert && eintraege.some((e) => e.hauptsanktion === eine.code)
        ),
      };
    },

    /**
     * Runde Achsenstufen von 0 bis ``hoechste`` (1/2/5/10/20/...), auf ein
     * Ziel von ``ziel`` Stufen hin. Gemeinsame Grundlage fuer die Y-Achse des
     * Histogramms (Anzahl Urteile, darum ``mindestSchritt=1`` - Bruchteile
     * eines Urteils gibt es nicht) und die X-Achse des Streudiagramms
     * (Strafmass, auch gebrochene Schritte sinnvoll).
     */
    rundeStufen(hoechste, ziel, mindestSchritt = 0) {
      if (hoechste <= 0) return [];
      const roh = Math.max(hoechste / ziel, mindestSchritt || hoechste / (ziel * 1000));
      const groessenordnung = Math.pow(10, Math.floor(Math.log10(roh)));
      const schritt =
        [1, 2, 5, 10].map((f) => f * groessenordnung).find((s) => s >= roh) ||
        groessenordnung * 10;
      const stufen = [];
      for (let i = schritt; i <= hoechste; i += schritt) stufen.push(i);
      return stufen;
    },

    /**
     * Beschriftete Stufen der Y-Achse: hoechstens sechs, und nur auf runden
     * Schritten (1/2/5/10/20/...). Jede Zeile zu beschriften ergaebe bei
     * hohen Balken eine unlesbare Zahlenkolonne.
     */
    histogrammYTicks() {
      const daten = this.histogramm();
      if (daten === null) return [];
      return this.rundeStufen(daten.hoechste, 6, 1);
    },

    /**
     * Platz eines Urteils im Balken: erste Ordnung die Sanktionsart
     * (Freiheitsstrafe vor Geldstrafe), zweite der Vollzug von unbedingt nach
     * bedingt. Die Saeule waechst von unten nach oben (column-reverse), der
     * erste Rang steht also zuunterst - damit laeuft jeder Balken von
     * dunkelblau ueber hellblau und dunkelgruen bis hellgruen.
     */
    blockRang(eintrag) {
      const sanktionsrang = { "0": 0, "1": 1 }[eintrag.hauptsanktion];
      const vollzugsrang = { "2": 0, "1": 1, "0": 2 }[eintrag.vollzug];
      return (
        (sanktionsrang === undefined ? 9 : sanktionsrang) * 10 +
        (vollzugsrang === undefined ? 9 : vollzugsrang)
      );
    },

    /** Klassenbeschriftung; Monate ab Jahresbreite als Jahreszahlen. */
    klassenlabel(art, von, bis) {
      if (art.monate) {
        if (this.histogrammInJahren(von, bis)) {
          const jahr = (monate) => Math.round((monate / 12) * 10) / 10;
          return `${jahr(von)}–${jahr(bis)} J.`;
        }
        return `${von}–${bis} Mt.`;
      }
      return `${von}–${bis} TS`;
    },

    histogrammInJahren(von, bis) {
      return von % 12 === 0 && (bis - von) % 12 === 0;
    },

    /** Tooltip-Text einer ganzen Klasse (Achsenbeschriftung, Balkentitel). */
    klassentitel(klasse) {
      const anzahl = klasse.urteile.length;
      return `${klasse.label}: ${anzahl} ${anzahl === 1 ? "Urteil" : "Urteile"}`;
    },

    /**
     * Strafmass eines einzelnen Blocks im Klartext. Geldstrafen nennen ihre
     * Tagessaetze, in der kombinierten Ansicht zusaetzlich den umgerechneten
     * Monatswert - sonst liesse sich die Lage des Blocks nicht nachvollziehen.
     */
    blockStrafmass(eintrag) {
      const stichprobe = this.aktiveStichprobe();
      const art = stichprobe ? stichprobe.art : null;
      if (eintrag.hauptsanktion === "1") {
        const tagessaetze = `${eintrag.tagessaetze} Tagessätze`;
        if (art === null || !art.kombiniert) return tagessaetze;
        return `${tagessaetze} (= ${eintrag.wert.toFixed(1)} Monate)`;
      }
      const monate = eintrag.wert;
      const lang = this.jahreMonateTitel(monate);
      const kopf = `${monate} ${monate === 1 ? "Monat" : "Monate"}`;
      return lang ? `${kopf} (${lang})` : kopf;
    },

    vollzugstext(code) {
      return { "0": "bedingt", "1": "teilbedingt", "2": "unbedingt" }[code] || "";
    },

    /**
     * Hover-Karte zu einem Block. Der Inhalt wird nur beim Betreten
     * zusammengestellt - waehrend der Mausbewegung wird allein die Position
     * nachgefuehrt, sonst liefe die Stichprobenauswertung bei jedem Pixel neu.
     */
    karteZeigen(eintrag, event) {
      this.histogrammKarte = {
        ...eintrag.karte,
        strafmass: this.blockStrafmass(eintrag),
        vollzug: this.vollzugstext(eintrag.vollzug),
      };
      this.kartePositionieren(event);
    },

    /** Position am Mauszeiger, an den Viewport-Raendern umgeklappt. */
    positionAmZeiger(event) {
      const breite = 400;
      const hoehe = 220;
      const abstand = 14;
      let x = event.clientX + abstand;
      let y = event.clientY + abstand;
      if (x + breite > window.innerWidth - 16) x = event.clientX - breite - abstand;
      if (x < 16) x = 16;
      if (y + hoehe > window.innerHeight - 16) y = event.clientY - hoehe - abstand;
      if (y < 16) y = 16;
      return { x, y };
    },

    kartePositionieren(event) {
      if (this.histogrammKarte === null) return;
      this.histogrammKartePos = this.positionAmZeiger(event);
    },

    karteVerbergen() {
      this.histogrammKarte = null;
    },

    // --- Streudiagramm Strafmass/Menge (nur BetmUrteil) ---------------------

    STREUDIAGRAMM_BREITE: 640,
    STREUDIAGRAMM_HOEHE: 300,
    STREUDIAGRAMM_RAND: { links: 50, rechts: 12, oben: 12, unten: 30 },

    /**
     * Summe der gewaehlten Substanzen (siehe ``passtSpanne``) fuer ein
     * einzelnes Urteil, oder null, wenn keine der gewaehlten Substanzen mit
     * einer Menge in der passenden Bemessungsgrundlage vorliegt.
     */
    mengeGesamt(record, gewaehlt, basen) {
      const mengen = record.betm_menge || {};
      let summe = 0;
      let vorhanden = false;
      gewaehlt.forEach((schluessel) => {
        const eintrag = mengen[schluessel];
        if (!eintrag) return;
        basen.forEach((b) => {
          const wert = eintrag[b];
          if (wert === undefined || wert === null) return;
          summe += wert;
          vorhanden = true;
        });
      });
      return vorhanden ? summe : null;
    },

    /**
     * Streudiagramm Menge (x) / Strafmass (y) der Treffermenge, ausgewertet
     * fuer die im Filter gewaehlten Substanzen. Menge auf der x-Achse, weil
     * sie die erklaerende Groesse ist und das Strafmass das Ergebnis - analog
     * zum bestehenden Deliktssumme/Strafhoehe-Scatterplot der Vermoegensdelikte
     * (``db_utils.py``, ``kategorie_scatterplot_erstellen``). Ohne
     * Substanzwahl liefert es null: Mengen unterschiedlicher Substanzen
     * (Kokain vs. Marihuana) lassen sich nicht auf einer gemeinsamen Achse
     * vergleichen, siehe ``spannenBerechnen``. Ausgewertet wird dieselbe
     * Strafmass-Stichprobe wie im Histogramm (``aktiveStichprobe``), der
     * Umschalter dort wirkt also auch hier.
     */
    streudiagramm() {
      if (!this.spec.felder.some((feld) => feld.name === "betm")) return null;
      const gewaehlt = this.zustand.betm || [];
      if (gewaehlt.length === 0) return null;
      const stichprobe = this.aktiveStichprobe();
      if (stichprobe === null) return null;
      const { art } = stichprobe;
      const basis = (this.zustand.betm_menge || {}).basis ?? null;
      const basen = basis === null ? ["rein", "gemisch"] : [basis];

      const punkte = [];
      this.trefferPks.forEach((pk) => {
        const record = this.records[pk];
        const strafmass = this.strafhoehe(record, art);
        if (strafmass === null) return;
        const menge = this.mengeGesamt(record, gewaehlt, basen);
        if (menge === null || menge <= 0) return;
        punkte.push({
          pk,
          strafmass,
          menge,
          hauptsanktion: record.hauptsanktion,
          tagessaetze: record.anzahl_tagessaetze,
          vollzug: record.vollzug,
          // Alle Substanzen des Urteils, nicht nur die im Filter gewaehlten -
          // faerbt den Rand dunkelgrau, wenn mehr als eine Art beteiligt ist.
          mehrfachBetm: (record.betm || []).length > 1,
          karte: record._karte || {},
        });
      });
      if (punkte.length === 0) return null;

      const info = this.spannen.betm_menge || {};
      return {
        art,
        punkte,
        anzahl: punkte.length,
        mengeDomain: this.streudiagrammMengeDomain(
          Math.min(...punkte.map((p) => p.menge)),
          Math.max(...punkte.map((p) => p.menge))
        ),
        strafmassMax: Math.max(...punkte.map((p) => p.strafmass)) || 1,
        mengeLabel: info.label || "Menge",
        einheit: info.einheit || "",
        achstitelY: art.monate ? "Strafmass (Monate)" : "Strafmass (Tagessätze)",
        sanktionen: this.sanktionsarten.filter(
          (eine) => !eine.kombiniert && punkte.some((p) => p.hauptsanktion === eine.code)
        ),
        basisHinweis:
          basis === null
            ? "reine Wirkstoff- und Bruttomengen zusammengefasst"
            : basis === "rein"
            ? "reine Wirkstoffmenge"
            : "Bruttomenge (Gemisch)",
        // Regression nur bei genau einer gewaehlten Substanz: Mengen
        // unterschiedlicher Substanzen (Kokain vs. Marihuana) liegen um
        // Groessenordnungen auseinander und eine gemeinsame Regressionsgerade
        // ueber mehrere Substanzen waere ohne Aussagekraft, siehe auch die
        // gleiche Einschraenkung fuer die Achse selbst oben in diesem
        // Kommentar. Auf log10(Menge) wie bei streudiagrammVM(), siehe dort.
        regression:
          gewaehlt.length === 1
            ? this.linearRegression(punkte.map((p) => ({ x: Math.log10(p.menge), y: p.strafmass })))
            : null,
      };
    },

    /**
     * Streudiagramm Deliktssumme (x) / Strafmass (y) der Treffermenge
     * (Vermoegensdelikte). Analog zu ``streudiagramm()`` (Betm-Urteile), aber
     * ohne vorgelagerte Auswahl: Die Deliktssumme ist ein einzelnes
     * Zahlenfeld je Urteil, anders als bei den Betm-Mengen gibt es keine
     * unvergleichbaren "Substanzen", die erst gewaehlt werden muessten - die
     * Deliktssumme verschiedener Hauptdelikte liegt immer auf derselben
     * (CHF-)Achse. Nutzt darum dieselbe Geometrie/Render-Logik wie
     * ``streudiagramm()`` (``streudiagrammX/Y/Ticks/AchsenSvg/PunkteSvg`` etc.
     * lesen nur die generischen ``mengeDomain``/``mengeLabel``/``einheit``-
     * Felder des Rueckgabeobjekts, unabhaengig vom Modell). Ausgewertet wird
     * dieselbe Strafmass-Stichprobe wie im Histogramm (``aktiveStichprobe``).
     */
    streudiagrammVM() {
      if (!this.spec.felder.some((feld) => feld.name === "deliktssumme")) return null;
      const stichprobe = this.aktiveStichprobe();
      if (stichprobe === null) return null;
      const { art } = stichprobe;
      const deliktssummeFeld = this.feldNach("deliktssumme");

      const punkte = [];
      this.trefferPks.forEach((pk) => {
        const record = this.records[pk];
        const strafmass = this.strafhoehe(record, art);
        if (strafmass === null) return;
        const menge = record.deliktssumme;
        if (menge === null || menge === undefined || menge <= 0) return;
        punkte.push({
          pk,
          strafmass,
          menge,
          hauptsanktion: record.hauptsanktion,
          tagessaetze: record.anzahl_tagessaetze,
          vollzug: record.vollzug,
          karte: record._karte || {},
          hervorgehoben: this.streudiagrammHervorhebung.includes(record.hauptdelikt),
        });
      });
      if (punkte.length === 0) return null;

      return {
        art,
        punkte,
        anzahl: punkte.length,
        mengeDomain: this.streudiagrammMengeDomain(
          Math.min(...punkte.map((p) => p.menge)),
          Math.max(...punkte.map((p) => p.menge))
        ),
        strafmassMax: Math.max(...punkte.map((p) => p.strafmass)) || 1,
        mengeLabel: deliktssummeFeld ? deliktssummeFeld.label : "Deliktssumme",
        einheit: deliktssummeFeld ? deliktssummeFeld.einheit : "CHF",
        achstitelY: art.monate ? "Strafmass (Monate)" : "Strafmass (Tagessätze)",
        sanktionen: this.sanktionsarten.filter(
          (eine) => !eine.kombiniert && punkte.some((p) => p.hauptsanktion === eine.code)
        ),
        // Regression auf log10(Deliktssumme), nicht auf der Deliktssumme
        // selbst: die X-Achse ist logarithmisch, eine Gerade in diesem Raum
        // erscheint darum als Gerade im Diagramm (siehe streudiagrammX) - eine
        // Regression auf den Rohwerten waere zudem von den wenigen sehr hohen
        // Deliktssummen dominiert und im Bild als Kurve sichtbar.
        regression: this.linearRegression(
          punkte.map((p) => ({ x: Math.log10(p.menge), y: p.strafmass }))
        ),
      };
    },

    /**
     * Hervorhebung eines Hauptdelikts im VM-Streudiagramm ein-/ausschalten
     * (ODER-Verknuepfung wie bei den gewoehnlichen Chip-Filtern, siehe
     * ``umschalten``). Bewusst getrennt von ``zustand``/``trifftZu``: die
     * Hervorhebung soll die Treffermenge nur farblich markieren, nicht
     * zusaetzlich filtern - man will ja gerade sehen, wo sich z.B. Betrugs-
     * faelle innerhalb aller Vermoegensdelikte einordnen.
     */
    streudiagrammHervorhebungUmschalten(wert) {
      const index = this.streudiagrammHervorhebung.indexOf(wert);
      if (index === -1) this.streudiagrammHervorhebung.push(wert);
      else this.streudiagrammHervorhebung.splice(index, 1);
    },

    streudiagrammHervorhebungAktiv(wert) {
      return this.streudiagrammHervorhebung.includes(wert);
    },

    /**
     * Einfache lineare Regression y = a + b*x nach der Methode der kleinsten
     * Quadrate. Liefert null, wenn weniger als zwei Punkte vorliegen oder alle
     * x-Werte identisch sind (die Steigung waere nicht definiert) - z.B. wenn
     * nach der Filterung nur noch eine einzige Deliktssumme uebrig bleibt.
     */
    linearRegression(paare) {
      const n = paare.length;
      if (n < 2) return null;
      const xMittel = paare.reduce((summe, p) => summe + p.x, 0) / n;
      const yMittel = paare.reduce((summe, p) => summe + p.y, 0) / n;
      let sxy = 0;
      let sxx = 0;
      let syy = 0;
      paare.forEach((p) => {
        const dx = p.x - xMittel;
        const dy = p.y - yMittel;
        sxy += dx * dy;
        sxx += dx * dx;
        syy += dy * dy;
      });
      if (sxx === 0) return null;
      const steigung = sxy / sxx;
      const achsenabschnitt = yMittel - steigung * xMittel;
      // Guetemass R²: bei konstantem y (syy=0) gilt die Gerade als perfekte
      // Anpassung, statt eine Division durch 0 zu erzeugen.
      const r2 = syy === 0 ? 1 : (sxy * sxy) / (sxx * syy);
      return { steigung, achsenabschnitt, r2, n };
    },

    /**
     * Wertebereich der logarithmischen X-Achse (Menge): rund 10% Rand
     * ueber/unter den tatsaechlichen Werten, damit kein Punkt auf dem
     * Achsenrand liegt.
     */
    streudiagrammMengeDomain(min, max) {
      const untenLog = Math.log10(min) - 0.1;
      const obenLog = Math.log10(Math.max(max, min)) + 0.1;
      return { min: Math.pow(10, untenLog), max: Math.pow(10, Math.max(obenLog, untenLog + 0.2)) };
    },

    /** x-Pixelposition eines Punkts (Menge, logarithmisch, waechst nach rechts). */
    streudiagrammX(daten, menge) {
      const { links, rechts } = this.STREUDIAGRAMM_RAND;
      const breite = this.STREUDIAGRAMM_BREITE - links - rechts;
      const { min, max } = daten.mengeDomain;
      const anteil = (Math.log10(menge) - Math.log10(min)) / (Math.log10(max) - Math.log10(min));
      return links + anteil * breite;
    },

    /** y-Pixelposition eines Punkts (Strafmass, linear, Achse beginnt bei 0). */
    streudiagrammY(daten, strafmass) {
      const { oben, unten } = this.STREUDIAGRAMM_RAND;
      const hoehe = this.STREUDIAGRAMM_HOEHE - oben - unten;
      return oben + (1 - strafmass / daten.strafmassMax) * hoehe;
    },

    /**
     * "Schoene" Log-Achsenstufen (Menge, 1/2/5 je Zehnerpotenz) innerhalb der
     * Domain. Bei sehr grosser Spannweite (>5 Zehnerpotenzen, z.B. 1g bis
     * mehrere 100kg) nur die vollen Zehnerpotenzen, sonst wird die Achse
     * unlesbar.
     */
    streudiagrammXTicks(daten) {
      const { min, max } = daten.mengeDomain;
      const start = Math.floor(Math.log10(min));
      const ende = Math.ceil(Math.log10(max));
      const nurZehnerpotenzen = ende - start > 5;
      const stufen = [];
      for (let zehner = start; zehner <= ende; zehner += 1) {
        (nurZehnerpotenzen ? [1] : [1, 2, 5]).forEach((faktor) => {
          const wert = faktor * Math.pow(10, zehner);
          if (wert >= min && wert <= max) stufen.push(wert);
        });
      }
      return stufen;
    },

    /** Runde Y-Achsenstufen (Strafmass), analog zur Histogramm-Y-Achse. */
    streudiagrammYTicks(daten) {
      return this.rundeStufen(daten.strafmassMax, 6);
    },

    /**
     * Menge als Anzeigetext: ab 1000g in Kilogramm (analog zu
     * ``Betm.menge_anzeige`` im Backend), Substanzen mit Stueckzahlen
     * (LSD-Trips, Ecstasy-Pillen) unveraendert in ihrer Einheit. CHF-Betraege
     * (Deliktssumme der Vermoegensdelikte, siehe ``streudiagrammVM()``) sind
     * mit Tausendertrennzeichen und ab 1 Mio. gerundet in Millionen deutlich
     * lesbarer als eine nackte Zahl mit bis zu acht Stellen.
     */
    mengeAnzeige(gramm, einheit) {
      const rundung = (wert) => (wert >= 100 ? Math.round(wert) : Math.round(wert * 10) / 10);
      if (einheit === "CHF") {
        if (gramm >= 1000000) {
          const mio = gramm / 1000000;
          return `CHF ${rundung(mio)} Mio.`;
        }
        return `CHF ${Math.round(gramm).toLocaleString("de-CH")}`;
      }
      if (einheit && einheit !== "g") return `${rundung(gramm)} ${einheit}`;
      if (gramm >= 1000) {
        const kg = (gramm / 1000).toFixed(1).replace(/\.0$/, "");
        return `${kg}kg`;
      }
      return `${rundung(gramm)}g`;
    },

    /** Fuer die per ``x-html`` erzeugten SVG-Textknoten (siehe unten). */
    escapeHtml(text) {
      return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    },

    /**
     * Gitterlinien & Achsenbeschriftung des Streudiagramms als SVG-Markup.
     *
     * ``x-for`` funktioniert innerhalb von ``<svg>`` nicht: der HTML-Parser
     * behandelt ein ``<template>`` dort als fremdes SVG-Element ohne
     * ``.content``-Fragment, Alpine kann es also nicht klonen (bekannte
     * Einschraenkung, kein Alpine-Bug). Das Markup wird darum als String
     * gebaut und per ``x-html`` in ein ``<g>`` eingehaengt - anders als ein
     * ausserhalb des ``<svg>`` liegendes, teleportiertes Template entstehen
     * die Kindknoten dabei korrekt im SVG-Namensraum, weil der
     * ``innerHTML``-Parser den Namensraum des Zielelements uebernimmt.
     */
    streudiagrammAchsenSvg(daten) {
      // Y-Achse: Strafmass, linear.
      const yAchse = this.streudiagrammYTicks(daten)
        .map((stufe) => {
          const y = this.streudiagrammY(daten, stufe);
          // Ohne die Nachkommastelle der kombinierten Ansicht, wenn die
          // Stufe (anders als einzelne Urteilswerte) ohnehin rund ist.
          const text = this.escapeHtml(this.formatiert(stufe, daten.art).replace(/\.0+$/, ""));
          return (
            `<line class="streudiagramm-gitter" x1="50" x2="628" y1="${y}" y2="${y}"></line>` +
            `<text class="streudiagramm-tick" x="46" y="${y + 3}" text-anchor="end">${text}</text>`
          );
        })
        .join("");
      // X-Achse: Menge, logarithmisch.
      const xAchse = this.streudiagrammXTicks(daten)
        .map((stufe) => {
          const x = this.streudiagrammX(daten, stufe);
          const text = this.escapeHtml(this.mengeAnzeige(stufe, daten.einheit));
          return (
            `<line class="streudiagramm-gitter" x1="${x}" x2="${x}" y1="12" y2="270"></line>` +
            `<text class="streudiagramm-tick" x="${x}" y="284" text-anchor="middle">${text}</text>`
          );
        })
        .join("");
      return yAchse + xAchse;
    },

    /**
     * Schneidet ein Geradensegment (u0,y0)-(u1,y1) auf den Y-Bereich
     * [yMin, yMax] zu (Liang-Barsky, nur in Y - die X-Grenzen sind bereits
     * durch die Domain vorgegeben, siehe streudiagrammRegressionSvg). Noetig,
     * weil eine Regressionsgerade ausserhalb der Datenpunkte durchaus
     * negative oder unrealistisch hohe Strafmass-Werte vorhersagen kann, die
     * aber nicht ausserhalb des Diagramms gezeichnet werden sollen. Liefert
     * null, wenn das Segment vollstaendig ausserhalb liegt.
     */
    streudiagrammLinieKlippen(u0, y0, u1, y1, yMin, yMax) {
      let tStart = 0;
      let tEnde = 1;
      const dy = y1 - y0;
      if (dy !== 0) {
        const t1 = (yMin - y0) / dy;
        const t2 = (yMax - y0) / dy;
        tStart = Math.max(tStart, Math.min(t1, t2));
        tEnde = Math.min(tEnde, Math.max(t1, t2));
      } else if (y0 < yMin || y0 > yMax) {
        return null;
      }
      if (tStart > tEnde) return null;
      const lerp = (von, bis, t) => von + (bis - von) * t;
      return {
        u0: lerp(u0, u1, tStart),
        y0: lerp(y0, y1, tStart),
        u1: lerp(u0, u1, tEnde),
        y1: lerp(y0, y1, tEnde),
      };
    },

    /**
     * Regressionsgerade als SVG-<line>, auf den sichtbaren Plotbereich
     * geclippt. Leerer String ohne Regression, ohne eingeschaltete
     * Anzeige (``streudiagrammRegressionAnzeigen``) oder wenn die Gerade
     * vollstaendig ausserhalb des sichtbaren Bereichs verlaeuft.
     */
    streudiagrammRegressionSvg(daten) {
      if (!this.streudiagrammRegressionAnzeigen || !daten.regression) return "";
      const { achsenabschnitt: a, steigung: b } = daten.regression;
      const { min, max } = daten.mengeDomain;
      const u0 = Math.log10(min);
      const u1 = Math.log10(max);
      const geklippt = this.streudiagrammLinieKlippen(
        u0, a + b * u0, u1, a + b * u1, 0, daten.strafmassMax
      );
      if (geklippt === null) return "";
      const x1 = this.streudiagrammX(daten, Math.pow(10, geklippt.u0));
      const y1 = this.streudiagrammY(daten, geklippt.y0);
      const x2 = this.streudiagrammX(daten, Math.pow(10, geklippt.u1));
      const y2 = this.streudiagrammY(daten, geklippt.y1);
      return `<line class="streudiagramm-regression" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"></line>`;
    },

    /**
     * Regressionsgleichung als lesbarer Text inkl. Guetemass, z.B.
     * "Strafmass (Monate) ≈ 4.1 + 6.8 · log₁₀(Deliktssumme in CHF)
     * (R² = 0.31, n = 214)". Auf log10(Deliktssumme) bezogen, nicht auf die
     * Deliktssumme selbst - siehe streudiagrammVM().
     */
    streudiagrammRegressionGleichung(daten) {
      if (!daten.regression) return "";
      const { achsenabschnitt: a, steigung: b, r2, n } = daten.regression;
      const vorzeichen = b >= 0 ? "+" : "−";
      return (
        `${daten.achstitelY} ≈ ${a.toFixed(2)} ${vorzeichen} ${Math.abs(b).toFixed(2)} · ` +
        `log₁₀(${daten.mengeLabel} in ${daten.einheit}) (R² = ${r2.toFixed(2)}, n = ${n})`
      );
    },

    /**
     * Strafmass-Vorhersage fuer die frei eingegebene Deliktssumme
     * (``streudiagrammRegressionEingabe``, Eingabefeld unter dem Diagramm),
     * anhand der Regressionsgeraden. Null ohne Regression oder bei leerer/
     * nicht positiver Eingabe - log10 ist fuer 0 oder negative Werte nicht
     * definiert. Negative Vorhersagen (moegliche Extrapolation weit unterhalb
     * der Datenpunkte) werden fuer die Anzeige auf 0 gekappt, der Hinweis
     * ``ausserhalbBereich`` macht auf die Extrapolation aufmerksam, statt sie
     * stillschweigend als verlaessliche Prognose auszugeben.
     */
    streudiagrammRegressionVorhersage(daten) {
      if (!daten.regression) return null;
      const eingabe = Number(this.streudiagrammRegressionEingabe);
      if (!Number.isFinite(eingabe) || eingabe <= 0) return null;
      const { achsenabschnitt: a, steigung: b } = daten.regression;
      const wert = a + b * Math.log10(eingabe);
      return {
        text: `${this.formatiert(Math.max(wert, 0), daten.art)} ${daten.art.einheit}`,
        negativ: wert < 0,
        ausserhalbBereich: eingabe < daten.mengeDomain.min || eingabe > daten.mengeDomain.max,
      };
    },

    /**
     * Ein Punkt je Urteil als SVG-Markup (siehe ``streudiagrammAchsenSvg`` zum
     * Grund fuer ``x-html`` statt ``x-for``). Hover/Fokus laufen ueber
     * Event-Delegation am ``<svg>`` (``streudiagrammHover``), weil in
     * ``x-html`` eingefuegtes Markup keine Alpine-Direktiven wie ``x-on``
     * verarbeitet; der Link selbst bleibt normal navigierbar, da ``<a
     * href>`` als gewoehnliches SVG-Markup unveraendert funktioniert.
     *
     * Hervorgehobene Punkte (``streudiagrammHervorhebung``, nur VM) werden
     * zuletzt gezeichnet, damit ihr goldener Rand nicht von ueberlappenden
     * Nachbarpunkten verdeckt wird - SVG kennt kein z-index, spaetere Elemente
     * liegen automatisch oben.
     */
    streudiagrammPunkteSvg(daten) {
      const punkte = daten.punkte
        .slice()
        .sort((a, b) => (a.hervorgehoben ? 1 : 0) - (b.hervorgehoben ? 1 : 0));
      return punkte
        .map((punkt) => {
          const href = this.escapeHtml(punkt.karte.url || "#");
          const label = this.escapeHtml(
            `${punkt.karte.fall_nr || ""} – ${this.mengeAnzeige(punkt.menge, daten.einheit)}`
          );
          const cx = this.streudiagrammX(daten, punkt.menge);
          const cy = this.streudiagrammY(daten, punkt.strafmass);
          const mehrfachKlasse = punkt.mehrfachBetm ? " mehrfach-betm" : "";
          const hervorhebungKlasse = punkt.hervorgehoben ? " hervorgehoben" : "";
          const radius = punkt.hervorgehoben ? 7 : 5;
          return (
            `<a href="${href}" aria-label="${label}">` +
            `<circle class="streudiagramm-punkt sanktion-${punkt.hauptsanktion} vollzug-${punkt.vollzug}${mehrfachKlasse}${hervorhebungKlasse}" ` +
            `data-pk="${punkt.pk}" cx="${cx}" cy="${cy}" r="${radius}" tabindex="0"></circle>` +
            `</a>`
          );
        })
        .join("");
    },

    /**
     * Delegierter Hover-/Fokus-Handler fuer die per ``x-html`` erzeugten
     * Punkte (siehe ``streudiagrammPunkteSvg``): sucht anhand von
     * ``data-pk`` am Ereignisziel den zugehoerigen Punkt und zeigt dessen
     * Karte. ``focusin``/``focusout`` statt ``focus``/``blur``, weil nur
     * erstere im delegierten Handler am ``<svg>`` ueberhaupt ankommen
     * (``focus``/``blur`` bubbeln nicht).
     */
    streudiagrammHover(event, daten) {
      const ziel = event.target.closest("[data-pk]");
      if (!ziel) return;
      const punkt = daten.punkte.find((p) => String(p.pk) === ziel.dataset.pk);
      if (!punkt) return;
      this.streudiagrammPunktZeigen(punkt, daten, event);
    },

    /**
     * Hover-Karte zu einem Punkt des Streudiagramms. Wiederverwendet
     * ``blockStrafmass`` und ``vollzugstext`` aus dem Histogramm, ergaenzt um
     * die Menge - die Karten sind sonst inhaltlich identisch.
     */
    streudiagrammPunktZeigen(punkt, daten, event) {
      const strafmassEintrag = {
        hauptsanktion: punkt.hauptsanktion,
        tagessaetze: punkt.tagessaetze,
        wert: punkt.strafmass,
      };
      this.streudiagrammPunktKarte = {
        ...punkt.karte,
        strafmass: this.blockStrafmass(strafmassEintrag),
        vollzug: this.vollzugstext(punkt.vollzug),
        menge: `${daten.mengeLabel}: ${this.mengeAnzeige(punkt.menge, daten.einheit)}`,
      };
      this.streudiagrammPunktPositionieren(event);
    },

    streudiagrammPunktPositionieren(event) {
      if (this.streudiagrammPunktKarte === null) return;
      this.streudiagrammPunktKartePos = this.positionAmZeiger(event);
    },

    streudiagrammPunktVerbergen() {
      this.streudiagrammPunktKarte = null;
    },

    // --- URL-Synchronisierung (verlinkbare Filterergebnisse) -----------------

    inUrlSchreiben() {
      const params = new URLSearchParams();
      if (this.q.trim()) params.set("q", this.q.trim());
      this.spec.felder.forEach((feld) => {
        if (!this.aktiv(feld)) return;
        const zustand = this.zustand[feld.name];
        if (Array.isArray(zustand)) params.set(feld.name, zustand.join("|"));
        else if (feld.typ === "bool") params.set(feld.name, zustand ? "1" : "0");
        else if (feld.typ === "abhaengige_spanne") {
          if (zustand.min !== "") params.set(`${feld.name}_min`, zustand.min);
          if (zustand.max !== "") params.set(`${feld.name}_max`, zustand.max);
          if (zustand.basis !== null) params.set(`${feld.name}_basis`, zustand.basis);
        } else {
          if (zustand.min !== "") params.set(`${feld.name}_min`, zustand.min);
          if (zustand.max !== "") params.set(`${feld.name}_max`, zustand.max);
        }
      });
      const suchteil = params.toString();
      const ziel = suchteil ? `${location.pathname}?${suchteil}` : location.pathname;
      history.replaceState(null, "", ziel);
    },

    ausUrlLesen() {
      const params = new URLSearchParams(location.search);
      this.q = params.get("q") || "";
      this.spec.felder.forEach((feld) => {
        if (feld.typ === "choice" || feld.typ === "multi") {
          const wert = params.get(feld.name);
          if (wert) this.zustand[feld.name] = wert.split("|");
        } else if (feld.typ === "bool") {
          const wert = params.get(feld.name);
          if (wert === "1") this.zustand[feld.name] = true;
          if (wert === "0") this.zustand[feld.name] = false;
        } else {
          const min = params.get(`${feld.name}_min`);
          const max = params.get(`${feld.name}_max`);
          if (min !== null) this.zustand[feld.name].min = min;
          if (max !== null) this.zustand[feld.name].max = max;
          if (feld.typ === "abhaengige_spanne") {
            const basis = params.get(`${feld.name}_basis`);
            if (basis === "rein" || basis === "gemisch") {
              this.zustand[feld.name].basis = basis;
            }
          }
        }
      });
      if (this.anzahlAktiv() > 0) this.aufgeklappt = true;
    },

    linkKopieren() {
      navigator.clipboard.writeText(location.href);
    },

    // --- CSV-Export der Treffermenge ----------------------------------------

    /** Codierte Werte fuer den Export in die Klartext-Bezeichnung uebersetzen. */
    klartext(feld, wert) {
      if (wert === null || wert === undefined) return "";
      if (Array.isArray(wert)) return wert.join("; ");
      if (feld.typ === "abhaengige_spanne") {
        return Object.entries(wert)
          .map(([schluessel, basen]) =>
            Object.entries(basen)
              .map(([basis, menge]) => `${schluessel} ${menge} ${basis}`)
              .join(", ")
          )
          .join("; ");
      }
      if (feld.typ === "bool") return wert ? "ja" : "nein";
      if (feld.optionen) {
        const option = feld.optionen.find((o) => o.value === String(wert));
        if (option) return option.label;
      }
      return String(wert);
    },

    csvExportieren() {
      const spalten = [
        { name: "fall_nr", label: "Fall-Nr." },
        ...this.spec.felder,
      ];
      const zelle = (text) => `"${String(text).replace(/"/g, '""')}"`;
      const zeilen = this.trefferPks.map((pk) => {
        const record = this.records[pk];
        return spalten.map((feld) => zelle(this.klartext(feld, record[feld.name])));
      });
      const csv = [
        spalten.map((feld) => zelle(feld.label)).join(","),
        ...zeilen.map((zeile) => zeile.join(",")),
      ].join("\n");
      const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "urteile-gefiltert.csv";
      link.click();
      URL.revokeObjectURL(link.href);
    },
  };
}
