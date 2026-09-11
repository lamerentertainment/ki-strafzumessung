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

    kennzahlen() {
      const treffer = this.trefferPks.map((pk) => this.records[pk]);
      // Urteile mit in_ki_modell=false (z.B. eine lebenslängliche Freiheitsstrafe,
      // die als Platzhalterwert codiert ist) verzerren Mittelwert/Median/Spanne
      // der Freiheitsstrafe und werden daher aus dieser Stichprobe ausgeschlossen.
      // Sie bleiben Teil der Trefferliste (`anzahl`) und der Vollzugs-Verteilung.
      const freiheitsstrafen = treffer
        .filter((record) => record.hauptsanktion === "0" && record.in_ki_modell !== false)
        .map((record) => record.freiheitsstrafe_in_monaten)
        .filter((wert) => wert !== null && wert !== undefined)
        .sort((a, b) => a - b);
      const vollzug = { "0": 0, "1": 0, "2": 0 };
      treffer.forEach((record) => {
        if (vollzug[record.vollzug] !== undefined) vollzug[record.vollzug] += 1;
      });
      const mittelwert = freiheitsstrafen.length
        ? freiheitsstrafen.reduce((a, b) => a + b, 0) / freiheitsstrafen.length
        : null;
      return {
        anzahl: treffer.length,
        gesamt: Object.keys(this.records).length,
        fsAnzahl: freiheitsstrafen.length,
        fsMedian: this.median(freiheitsstrafen),
        fsMittel: mittelwert === null ? null : Math.round(mittelwert),
        // mittlere absolute Abweichung vom (ungerundeten) Mittelwert (in Monaten)
        fsMad:
          mittelwert === null
            ? null
            : Math.round(
              freiheitsstrafen.reduce((summe, wert) => summe + Math.abs(wert - mittelwert), 0) /
              freiheitsstrafen.length
            ),
        fsMin: freiheitsstrafen.length ? freiheitsstrafen[0] : null,
        fsMax: freiheitsstrafen.length ? freiheitsstrafen[freiheitsstrafen.length - 1] : null,
        bedingt: vollzug["0"],
        teilbedingt: vollzug["1"],
        unbedingt: vollzug["2"],
      };
    },

    median(werte) {
      if (!werte.length) return null;
      const mitte = Math.floor(werte.length / 2);
      return werte.length % 2 ? werte[mitte] : Math.round((werte[mitte - 1] + werte[mitte]) / 2);
    },

    /**
     * Wandelt eine Monatszahl in "X Jahre Y Monate" um, als Titel fuer eine
     * Tooltip-Anzeige (z.B. bei Median/Durchschnitt der Freiheitsstrafe).
     * Ab 12 Monaten sinnvoll; darunter (oder ohne Wert) leerer String, sodass
     * kein Tooltip erscheint.
     */
    jahreMonateTitel(monate) {
      if (monate === null || monate === undefined || monate <= 12) return "";
      const jahre = Math.floor(monate / 12);
      const rest = monate % 12;
      const teile = [`${jahre} ${jahre === 1 ? "Jahr" : "Jahre"}`];
      if (rest > 0) teile.push(`${rest} ${rest === 1 ? "Monat" : "Monate"}`);
      return teile.join(" ");
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
