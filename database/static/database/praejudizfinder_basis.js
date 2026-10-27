/*
 * Gemeinsame Basis der geführten Präjudiziensuchen ("Präjudizen finden"),
 * z.B. praejudizfinder_sexual.js und praejudizfinder_gewalt.js.
 *
 * Die Basis übernimmt alles, was nicht vom Delikt abhängt: Schrittnavigation,
 * Ähnlichkeitsrechnung, Ergebnisliste mit Kennzahlen, Tooltips, Vollzugsfarben
 * sowie die überall gleichen Kriterien übrige Delikte, Vorstrafen und
 * Besonderheiten. Die deliktspezifische Komponente liefert:
 *
 *   schritte              [{key, titel}, ...], letzter Schritt "ergebnis"
 *   leereAntworten()      Ausgangszustand von this.a (inkl. der Basisfelder,
 *                         siehe PF_BASIS_ANTWORTEN)
 *   kriterien(u)          Liste der Kriterien für ein Urteil, aufgebaut mit
 *                         kriterienListe() und gemeinsameKriterien()
 *   trefferZeile(u)       Kurzbeschreibung des Delikts in der Ergebnisliste
 *   passendesHauptdelikt  Anzahl Urteile mit passendem Hauptdelikt (Getter)
 *   passendLabel          Text dazu in der Seitenleiste
 *   antworten             Zeilen der Seitenleiste (Getter), i.d.R. mit
 *                         gemeinsameAntworten() ergänzt
 *   weiterHinweis         optional: Hinweis neben "weiter" (Getter)
 *   regeln                {kriterium: {label, gewicht, vergabe: [...]}} -
 *                         Gewicht und Punktevergabe je Kriterium, angezeigt
 *                         bei der Frage und als Tooltip der Schrittleiste.
 *                         Jeder Schritt nennt in schritte[].kriterien die
 *                         Kriterien, die er abfragt.
 *
 * Die Bewertung läuft im Browser: Jedes beantwortete Kriterium trägt mit
 * seinem Gewicht zur Ähnlichkeit bei; unbeantwortete Kriterien ("weiss
 * nicht") fallen aus der Rechnung heraus, statt als Nichtübereinstimmung zu
 * zählen.
 */

const PF_LEBENSLAENGLICH = 999;
// Umrechnung Geldstrafe -> Freiheitsstrafe für Median und Spanne
const PF_TAGESSAETZE_PRO_MONAT = 30;

// Antworten, die die Basis auswertet (gemeinsameKriterien/-Antworten)
const PF_BASIS_ANTWORTEN = () => ({
  uebrigeFrage: null, // "ja" | "nein" | null
  verbrechen: 0,
  vergehen: 0,
  mehrfachUebrige: 0,
  vorstrafen: null, // "keine" | "nicht_einschlaegig" | "einschlaegig" | null
  besonderheiten: {}, // name -> "ja" | "nein"
});

const PF_BASIS_GEWICHTE = {
  uebrige: 6,
  vorstrafen: 8,
  besonderheit: 5,
};

/*
 * Erzeugt eine Alpine-Komponente aus Basis und deliktspezifischem Teil.
 * Zusammengeführt wird über Property-Deskriptoren statt Spread, weil Spread
 * die Getter (treffer, kennzahlen, ...) einmalig auswerten und damit ihre
 * Reaktivität verlieren würde.
 */
function praejudizfinderKomponente(spezifisch) {
  return (schritteId, urteileId) => {
    const komponente = {};
    Object.defineProperties(komponente, Object.getOwnPropertyDescriptors(praejudizfinderBasis(schritteId, urteileId)));
    Object.defineProperties(komponente, Object.getOwnPropertyDescriptors(spezifisch()));
    komponente.a = komponente.leereAntworten();
    return komponente;
  };
}

function praejudizfinderBasis(schritteId, urteileId) {
  return {
    s: JSON.parse(document.getElementById(schritteId).textContent),
    urteile: JSON.parse(document.getElementById(urteileId).textContent),
    schritt: 0,
    anzahlTreffer: 10,
    // Besonderheiten, die die spezifische Komponente als eigenes Kriterium
    // bewertet und die darum nicht nochmals in gemeinsameKriterien zählen
    besonderheitenSeparat: [],
    regeln: {},
    // Aufgeklappte Ergebniskarten und nachgeladene Zusammenfassungen, je pk
    offeneKarten: {},
    zusammenfassungen: {},

    // --- Navigation -----------------------------------------------------------

    get aktuellerKey() {
      return this.schritte[this.schritt].key;
    },
    weiter() {
      if (this.schritt < this.schritte.length - 1) this.schritt++;
      this.$nextTick(() => window.scrollTo({ top: 0, behavior: "smooth" }));
    },
    zurueck() {
      if (this.schritt > 0) this.schritt--;
    },
    springen(index) {
      // Ohne Hauptdelikt ist keine sinnvolle Bewertung möglich
      if (index > 0 && !this.a.hauptdelikt) return;
      this.schritt = index;
    },
    // Hinweis neben "weiter" auf eine wichtige, noch offene Frage; die
    // spezifische Komponente kann ihn überschreiben
    get weiterHinweis() {
      return "";
    },
    zumErgebnis() {
      this.schritt = this.schritte.length - 1;
    },
    neuStarten() {
      this.a = this.leereAntworten();
      this.anzahlTreffer = 10;
      this.schritt = 0;
    },

    // --- Antworten ------------------------------------------------------------

    waehlen(feld, wert) {
      this.a[feld] = this.a[feld] === wert ? null : wert;
    },
    besonderheitWaehlen(name, wert) {
      const aktuell = this.a.besonderheiten[name];
      const neu = { ...this.a.besonderheiten };
      if (aktuell === wert) delete neu[name];
      else neu[name] = wert;
      this.a.besonderheiten = neu;
    },
    besonderheitenImSchritt(schritt) {
      return this.s.besonderheiten.filter((b) => b.schritt === schritt);
    },
    get deliktsscore() {
      if (this.a.uebrigeFrage === "nein") return 0;
      if (this.a.uebrigeFrage !== "ja") return null;
      const zahl = (w) => Math.max(0, parseInt(w, 10) || 0);
      return 2 * zahl(this.a.verbrechen) + zahl(this.a.vergehen) + zahl(this.a.mehrfachUebrige);
    },
    label(liste, wert) {
      const eintrag = this.s[liste].find((x) => x.value === wert);
      return eintrag ? eintrag.label || eintrag.titel || eintrag.value : wert;
    },

    // --- Transparenz der Gewichtung ------------------------------------------

    // Punktevergabe der gemeinsamen Kriterien (Werte aus PF_BASIS_GEWICHTE,
    // Regeln wie in gemeinsameKriterien)
    basisRegeln() {
      return {
        uebrige: {
          label: "Übrige Delikte",
          gewicht: PF_BASIS_GEWICHTE.uebrige,
          vergabe: [
            "gleicher Deliktsscore: volle Punkte",
            "je Punkt Differenz ein Viertel Abzug (ab 4 Punkten Differenz: 0)",
            "Score im Urteil nicht erfasst: 30 %",
          ],
        },
        vorstrafen: {
          label: "Vorstrafen",
          gewicht: PF_BASIS_GEWICHTE.vorstrafen,
          vergabe: [
            "gleiche Stufe: volle Punkte",
            "benachbarte Stufe (keine – nicht einschlägig – einschlägig): 50 %",
            "keine gegenüber einschlägig: 0",
          ],
        },
        besonderheit: {
          label: "Besonderheit",
          gewicht: PF_BASIS_GEWICHTE.besonderheit,
          vergabe: ["je Besonderheit: übereinstimmend volle Punkte, sonst 0"],
        },
      };
    },
    gewichtung(kriterium) {
      return { ...this.basisRegeln(), ...this.regeln }[kriterium] || null;
    },
    // Anzahl gefragter Besonderheiten, die über "besonderheit" bewertet werden
    get anzahlBesonderheiten() {
      return this.s.besonderheiten.filter((b) => !this.besonderheitenSeparat.includes(b.value)).length;
    },
    // Ob ein Kriterium beim aktuellen Fall überhaupt zählt (z.B. Beute nur
    // bei Raub); die spezifische Komponente kann das überschreiben
    kriteriumAktiv(kriterium) {
      return true;
    },
    punkteVon(kriterium) {
      const r = this.gewichtung(kriterium);
      if (!r || !this.kriteriumAktiv(kriterium)) return 0;
      return kriterium === "besonderheit" ? r.gewicht * this.anzahlBesonderheiten : r.gewicht;
    },
    // Maximal mögliche Punkte, wenn alle Fragen beantwortet sind
    get gesamtPunkte() {
      const alle = new Set(this.schritte.flatMap((x) => x.kriterien || []));
      return [...alle].reduce((summe, k) => summe + this.punkteVon(k), 0);
    },
    schrittTooltip(eintrag) {
      if (eintrag.key === "ergebnis") {
        return "Ähnlichkeit = erreichte ÷ mögliche Punkte der beantworteten Fragen.\nNicht beantwortete Fragen zählen nicht.";
      }
      const zeilen = (eintrag.kriterien || []).map((k) => {
        const r = this.gewichtung(k);
        if (!r) return null;
        if (k === "besonderheit") {
          return `${this.anzahlBesonderheiten} Besonderheiten: je ${r.gewicht} Punkte`;
        }
        return `${r.label}: ${r.gewicht} Punkte`;
      }).filter(Boolean);
      const summe = (eintrag.kriterien || []).reduce((s, k) => s + this.punkteVon(k), 0);
      return [`${eintrag.titel}: ${summe} von ${this.gesamtPunkte} Vergleichspunkten`, ...zeilen.map((z) => `• ${z}`),
        "Gewichtung nach Ermessen."].join("\n");
    },

    // --- Bewertung ------------------------------------------------------------

    // Jedes Kriterium trägt neben Gewicht und Übereinstimmung (0-1) die
    // verglichenen Werte und eine Begründung, damit die Badges der
    // Ergebnisseite per Tooltip nachvollziehbar sind (kriteriumTooltip).
    kriterienListe() {
      const k = [];
      // Nicht aufzählbar, sonst rendert x-for die Funktion als zusätzliches Badge
      Object.defineProperty(k, "add", {
        enumerable: false,
        value: (name, gewicht, wert, label, fall, urteil, grund) =>
          k.push({ name, gewicht, wert, label, fall, urteil, grund: grund || "" }),
      });
      return k;
    },
    // Übereinstimmung zweier Stufen einer geordneten Skala: je Stufe Abstand
    // wird 1/nenner abgezogen. Unbekannte Werte im Urteil zählen pauschal 30 %.
    ordinal(reihe, fall, urteil, nenner, einheit = "Stufe") {
      const i = reihe.indexOf(fall);
      const j = reihe.indexOf(urteil);
      if (j < 0) return { wert: 0.3, grund: "im Urteil nicht bekannt (pauschal 30 %)" };
      const d = Math.abs(i - j);
      const anteil = nenner === 2 ? "die Hälfte" : nenner === 3 ? "ein Drittel" : nenner === 4 ? "ein Viertel" : `1/${nenner}`;
      return {
        wert: Math.max(0, 1 - d / nenner),
        grund: d === 0 ? "übereinstimmend" : `${d} ${einheit}${d === 1 ? "" : "n"} entfernt (je ${einheit} ${anteil} Abzug)`,
      };
    },
    // Gleichheit mit optionaler Gruppenähnlichkeit (gleiche Gruppe = teilweise)
    gruppenvergleich(fall, urteil, gruppeVon, teilwert, teilgrund, unbekannt = []) {
      if (fall === urteil) return { wert: 1, grund: "identisch" };
      if (unbekannt.includes(urteil)) return { wert: 0.3, grund: "im Urteil nicht bekannt (pauschal 30 %)" };
      const g = gruppeVon(fall);
      if (g && g === gruppeVon(urteil)) return { wert: teilwert, grund: teilgrund };
      return { wert: 0, grund: "abweichend" };
    },
    jaNeinVergleich(antwort, hat) {
      const wert = (antwort === "ja") === hat ? 1 : 0;
      return { wert, grund: wert ? "übereinstimmend" : "abweichend" };
    },
    // Übrige Delikte, Vorstrafen und Besonderheiten - bei allen Deliktsarten gleich
    gemeinsameKriterien(u, k) {
      const a = this.a;
      const score = this.deliktsscore;
      if (score !== null) {
        let wert = 0.3;
        let grund = "Deliktsscore im Urteil nicht erfasst (pauschal 30 %)";
        if (u.deliktsscore !== null) {
          const d = Math.abs(score - u.deliktsscore);
          wert = Math.max(0, 1 - d / 4);
          grund = d === 0 ? "gleicher Score" : `Differenz ${d} Punkt${d === 1 ? "" : "e"} (je Punkt ein Viertel Abzug)`;
        }
        k.add("uebrige", PF_BASIS_GEWICHTE.uebrige, wert, "Übrige Delikte", `Score ${score}`,
          u.deliktsscore === null ? "nicht erfasst" : `Score ${u.deliktsscore}`, grund);
      }
      if (a.vorstrafen) {
        const rang = { keine: 0, nicht_einschlaegig: 1, einschlaegig: 2 };
        const text = ["keine", "nicht einschlägig", "einschlägig"];
        const uRang = u.einschlaegig ? 2 : u.vorbestraft ? 1 : 0;
        const d = Math.abs(rang[a.vorstrafen] - uRang);
        const wert = Math.max(0, 1 - d / 2);
        const grund = d === 0 ? "übereinstimmend" : d === 1 ? "eine Stufe entfernt (keine – nicht einschlägig – einschlägig)" : "gegensätzlich";
        k.add("vorstrafen", PF_BASIS_GEWICHTE.vorstrafen, wert, "Vorstrafen", text[rang[a.vorstrafen]], text[uRang], grund);
      }
      for (const [name, antwort] of Object.entries(a.besonderheiten)) {
        if (this.besonderheitenSeparat.includes(name)) continue;
        const hat = u.besonderheiten.includes(name);
        const { wert, grund } = this.jaNeinVergleich(antwort, hat);
        k.add(`b:${name}`, PF_BASIS_GEWICHTE.besonderheit, wert, name, antwort, hat ? "ja" : "nein", grund);
      }
    },
    gemeinsameAntworten(zeilen) {
      const a = this.a;
      if (this.deliktsscore !== null) zeilen.push(["Deliktsscore übrige", String(this.deliktsscore)]);
      const vs = { keine: "keine", nicht_einschlaegig: "nicht einschlägig", einschlaegig: "einschlägig" };
      if (a.vorstrafen) zeilen.push(["Vorstrafen", vs[a.vorstrafen]]);
      for (const [name, antwort] of Object.entries(a.besonderheiten)) {
        if (!this.besonderheitenSeparat.includes(name)) zeilen.push([name, antwort]);
      }
      return zeilen;
    },

    get bewertet() {
      return this.urteile
        .map((u) => {
          const k = this.kriterien(u);
          const summe = k.reduce((s, x) => s + x.gewicht, 0);
          const punkte = k.reduce((s, x) => s + x.gewicht * x.wert, 0);
          return { u, k, aehnlichkeit: summe ? punkte / summe : 0 };
        })
        .sort((x, y) => y.aehnlichkeit - x.aehnlichkeit);
    },
    get treffer() {
      return this.bewertet.slice(0, this.anzahlTreffer);
    },
    get sehrAehnlich() {
      return this.bewertet.filter((b) => b.aehnlichkeit >= 0.8).length;
    },

    // Kennzahlen der angezeigten Treffer. Median und Spanne umfassen Freiheits-
    // und Geldstrafen, umgerechnet mit 30 Tagessätzen = 1 Monat (Art. 34 i.V.m.
    // Art. 36 StGB: ein Tagessatz entspricht einem Tag Freiheitsstrafe; gleich
    // wie _strafmass_sortierschluessel in filterspec.py). Nicht eingerechnet
    // sind lebenslängliche Freiheitsstrafen und Bussen (Höhe nicht erfasst).
    get kennzahlen() {
      const strafmasse = this.treffer
        .map((b) => this.strafmass(b.u))
        .filter((x) => x !== null)
        .sort((x, y) => x.monate - y.monate);
      const n = strafmasse.length;
      const median = n
        ? n % 2 ? strafmasse[(n - 1) / 2].monate : (strafmasse[n / 2 - 1].monate + strafmasse[n / 2].monate) / 2
        : null;
      // Vollzug je Sanktionsart, damit die Badges wie im Strafmasshistogramm
      // und Streudiagramm der Datenbankansicht eingefärbt werden können
      // (Farbton = Sanktionsart, Helligkeit = Vollzug).
      const vollzug = [
        { code: "0", label: "Freiheitsstrafe", anzahl: { "0": 0, "1": 0, "2": 0 } },
        { code: "1", label: "Geldstrafe", anzahl: { "0": 0, "1": 0, "2": 0 } },
      ];
      this.treffer.forEach((b) => {
        const gruppe = vollzug.find((g) => g.code === b.u.hauptsanktion);
        if (gruppe && b.u.vollzug in gruppe.anzahl) gruppe.anzahl[b.u.vollzug]++;
      });
      return {
        anzahlStrafmasse: n,
        anzahlGs: strafmasse.filter((x) => x.geldstrafe).length,
        median,
        min: n ? strafmasse[0] : null,
        max: n ? strafmasse[n - 1] : null,
        vollzug: vollzug.filter((g) => Object.values(g.anzahl).some((n) => n > 0)),
      };
    },

    // --- Zusammenfassung in der Ergebniskarte -------------------------------

    // Klick auf die Karte klappt die Zusammenfassung auf. Ausgenommen sind
    // Klicks auf Links und Schaltflächen, in die geöffnete Zusammenfassung
    // sowie das Markieren von Text, damit sich z.B. der Kurzsachverhalt
    // kopieren lässt, ohne die Karte zu öffnen oder zu schliessen.
    karteKlick(u, event) {
      if (event.target.closest("a, button, .pf-zusammenfassung")) return;
      if (String(window.getSelection())) return;
      this.karteUmschalten(u);
    },
    karteUmschalten(u) {
      const offen = !this.offeneKarten[u.pk];
      this.offeneKarten = { ...this.offeneKarten, [u.pk]: offen };
      if (offen && !(u.pk in this.zusammenfassungen)) this.zusammenfassungLaden(u);
    },
    async zusammenfassungLaden(u) {
      this.zusammenfassungen = { ...this.zusammenfassungen, [u.pk]: { laedt: true } };
      let eintrag;
      try {
        const antwort = await fetch(u.zusammenfassung_url, { headers: { Accept: "application/json" } });
        if (!antwort.ok) throw new Error(antwort.status);
        const daten = await antwort.json();
        eintrag = { text: daten.zusammenfassung || "" };
      } catch (fehler) {
        eintrag = { fehler: true };
      }
      this.zusammenfassungen = { ...this.zusammenfassungen, [u.pk]: eintrag };
    },
    zusammenfassungErneutLaden(u) {
      const rest = { ...this.zusammenfassungen };
      delete rest[u.pk];
      this.zusammenfassungen = rest;
      this.zusammenfassungLaden(u);
    },

    // Strafmass eines Urteils in Monaten (Geldstrafe umgerechnet) samt
    // Anzeige in der ursprünglichen Einheit; null, wenn nicht vergleichbar
    strafmass(u) {
      if (u.hauptsanktion === "0" && u.freiheitsstrafe !== PF_LEBENSLAENGLICH && u.freiheitsstrafe !== null) {
        return { monate: u.freiheitsstrafe, geldstrafe: false, anzeige: `${u.freiheitsstrafe} Mt.` };
      }
      if (u.hauptsanktion === "1" && u.tagessaetze) {
        return { monate: u.tagessaetze / PF_TAGESSAETZE_PRO_MONAT, geldstrafe: true, anzeige: `${u.tagessaetze} TS` };
      }
      return null;
    },
    // Median in Monaten; unter einem Jahr mit einer Nachkommastelle, weil dort
    // auch kurze Geldstrafen (z.B. 45 TS = 1.5 Mt.) ins Gewicht fallen
    medianAnzeige(monate) {
      if (monate === null) return "–";
      const gerundet = monate < 12 ? Math.round(monate * 10) / 10 : Math.round(monate);
      const zahl = gerundet.toLocaleString("de-CH");
      return `${zahl} ${gerundet === 1 ? "Monat" : "Monate"}`;
    },

    // --- Anzeige --------------------------------------------------------------

    kriteriumTooltip(k, alle) {
      const summe = alle.reduce((s, x) => s + x.gewicht, 0);
      const beitrag = k.gewicht * k.wert;
      const status = k.wert >= 0.99 ? "✓ stimmt überein" : k.wert > 0 ? "◐ teilweise" : "✗ weicht ab";
      return [
        `${k.label}: ${status} (${Math.round(k.wert * 100)} %)`,
        `Ihr Fall: ${k.fall}`,
        `Urteil: ${k.urteil}`,
        k.grund && k.wert < 0.99 ? `Grund: ${k.grund}` : null,
        `Beitrag: ${this.punkte(beitrag)} von ${k.gewicht} Punkten (Gewicht ${k.gewicht} von gesamt ${summe})`,
      ].filter(Boolean).join("\n");
    },
    aehnlichkeitTooltip(b) {
      const summe = b.k.reduce((s, x) => s + x.gewicht, 0);
      const punkte = b.k.reduce((s, x) => s + x.gewicht * x.wert, 0);
      const zeilen = b.k.map((k) => `• ${k.label}: ${this.punkte(k.gewicht * k.wert)}/${k.gewicht}`);
      return [
        `Ähnlichkeit = erreichte ÷ mögliche Punkte`,
        `${this.punkte(punkte)} ÷ ${summe} = ${this.prozent(b.aehnlichkeit)}`,
        ...zeilen,
        `Nicht beantwortete Fragen zählen nicht.`,
        `Grün ab 80 %, gelb ab 60 %.`,
      ].join("\n");
    },
    punkte(x) {
      return (Math.round(x * 10) / 10).toLocaleString("de-CH");
    },
    prozent(wert) {
      return `${Math.round(wert * 100)} %`;
    },
    aehnlichkeitsKlasse(wert) {
      if (wert >= 0.8) return "text-bg-success";
      if (wert >= 0.6) return "text-bg-warning";
      return "text-bg-secondary";
    },
    kriteriumKlasse(wert) {
      if (wert >= 0.99) return "pf-krit-ja";
      if (wert > 0) return "pf-krit-teil";
      return "pf-krit-nein";
    },
    kriteriumSymbol(wert) {
      if (wert >= 0.99) return "bi-check-lg";
      if (wert > 0) return "bi-circle-half";
      return "bi-x-lg";
    },
    monate(m) {
      if (m === null || m === undefined) return "–";
      if (m === PF_LEBENSLAENGLICH) return "lebenslänglich";
      if (m < 12) return `${m} ${m === 1 ? "Monat" : "Monate"}`;
      const j = Math.floor(m / 12);
      const r = m % 12;
      const jahre = `${j} ${j === 1 ? "Jahr" : "Jahre"}`;
      return r ? `${m} Monate (${jahre} ${r} ${r === 1 ? "Monat" : "Monate"})` : `${m} Monate (${jahre})`;
    },
    sanktion(u) {
      if (u.hauptsanktion === "0") return `Freiheitsstrafe ${this.monate(u.freiheitsstrafe)}`;
      if (u.hauptsanktion === "1") return `Geldstrafe ${u.tagessaetze} Tagessätze`;
      return "Busse";
    },
    vollzugTooltip(v) {
      return {
        "0": "Bedingt: Die Strafe wird aufgeschoben und nicht vollzogen, sofern sich der Täter während der Probezeit von 2–5 Jahren bewährt (Art. 42 StGB; möglich bei Geldstrafe und Freiheitsstrafe bis 2 Jahre).",
        "1": "Teilbedingt: Ein Teil der Strafe wird vollzogen, der Rest aufgeschoben (Art. 43 StGB; Freiheitsstrafe von 1 bis 3 Jahren).",
        "2": "Unbedingt: Die Strafe wird vollständig vollzogen – zwingend bei Freiheitsstrafen über 3 Jahren, sonst bei ungünstiger Legalprognose.",
      }[v];
    },
    // Farben wie Strafmasshistogramm/Streudiagramm (stylesheet.css, .pf-vollzug)
    vollzugKlasse(u) {
      return `pf-vollzug sanktion-${u.hauptsanktion} vollzug-${u.vollzug}`;
    },
  };
}
