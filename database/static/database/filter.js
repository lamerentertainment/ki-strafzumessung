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
      const freiheitsstrafen = treffer
        .filter((record) => record.hauptsanktion === "0")
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
        // mittlere absolute Abweichung vom (ungerundeten) Mittelwert
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

    // --- URL-Synchronisierung (verlinkbare Filterergebnisse) -----------------

    inUrlSchreiben() {
      const params = new URLSearchParams();
      if (this.q.trim()) params.set("q", this.q.trim());
      this.spec.felder.forEach((feld) => {
        if (!this.aktiv(feld)) return;
        const zustand = this.zustand[feld.name];
        if (Array.isArray(zustand)) params.set(feld.name, zustand.join("|"));
        else if (feld.typ === "bool") params.set(feld.name, zustand ? "1" : "0");
        else {
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
