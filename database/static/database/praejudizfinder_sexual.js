/*
 * Geführte Präjudiziensuche für Sexualdelikte ("Präjudizen finden").
 *
 * Die Schritte und Erläuterungen kommen aus database/praejudizfinder.py
 * (json_script "pf-schritte"), die Urteile aus "pf-urteile". Bewertet wird
 * hier im Browser: Jedes beantwortete Kriterium trägt mit seinem Gewicht zur
 * Ähnlichkeit bei; unbeantwortete Kriterien ("weiss nicht") fallen aus der
 * Rechnung heraus, statt als Nichtübereinstimmung zu zählen.
 */

// Gewichte der Kriterien. Hauptdelikt und Tatmittel bestimmen den Strafrahmen
// bzw. die Art der Tatbegehung und wiegen darum am schwersten.
const PF_GEWICHTE = {
  hauptdelikt: 30,
  tatmittel: 15,
  opferalter: 12,
  beziehung: 7,
  mehrfach: 9,
  weitere: 7,
  uebrige: 6,
  vorstrafen: 8,
  besonderheit: 5,
  versuch: 9,
};

// Ordinale Reihenfolge des Opferalters, jüngste zuerst
const PF_ALTERSSTUFEN = ["unter_6", "unter_10", "unter_14", "unter_16", "unter_18", "erwachsen"];

// Beide Tatmittel sind Nötigungsmittel und liegen sich näher als die übrigen
const PF_TATMITTEL_NAEHE = { "Gewalt|psychischer Druck": 0.5, "psychischer Druck|Gewalt": 0.5 };

const PF_LEBENSLAENGLICH = 999;

document.addEventListener("alpine:init", () => {
  Alpine.data("praejudizfinder", (schritteId, urteileId) => ({
    s: JSON.parse(document.getElementById(schritteId).textContent),
    urteile: JSON.parse(document.getElementById(urteileId).textContent),
    schritt: 0,
    schritte: [
      { key: "hauptdelikt", titel: "Hauptdelikt" },
      { key: "tatmittel", titel: "Tatmittel" },
      { key: "opfer", titel: "Opfer" },
      { key: "tat", titel: "Tatbegehung" },
      { key: "weitere", titel: "Weitere Sexualdelikte" },
      { key: "uebrige", titel: "Übrige Delikte" },
      { key: "taeter", titel: "Täter & Verfahren" },
      { key: "ergebnis", titel: "Ähnliche Urteile" },
    ],
    a: {
      hauptdelikt: null,
      tatmittel: null,
      opferalter: null,
      beziehung: null,
      mehrfach: null, // "ja" | "nein" | null
      anzahl: null,
      weitereFrage: null, // "ja" | "nein" | null
      weitere: [],
      uebrigeFrage: null, // "ja" | "nein" | null
      verbrechen: 0,
      vergehen: 0,
      mehrfachUebrige: 0,
      vorstrafen: null, // "keine" | "nicht_einschlaegig" | "einschlaegig" | null
      besonderheiten: {}, // name -> "ja" | "nein"
    },
    offeneErlaeuterung: null,
    anzahlTreffer: 10,

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
    neuStarten() {
      this.a = {
        ...this.a,
        hauptdelikt: null, tatmittel: null, opferalter: null, beziehung: null,
        mehrfach: null, anzahl: null, weitereFrage: null, weitere: [],
        uebrigeFrage: null, verbrechen: 0, vergehen: 0, mehrfachUebrige: 0,
        vorstrafen: null, besonderheiten: {},
      };
      this.anzahlTreffer = 10;
      this.schritt = 0;
    },
    waehlen(feld, wert) {
      this.a[feld] = this.a[feld] === wert ? null : wert;
    },
    weitereUmschalten(artikel) {
      const i = this.a.weitere.indexOf(artikel);
      if (i >= 0) this.a.weitere.splice(i, 1);
      else this.a.weitere.push(artikel);
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
    gewaehltesHauptdelikt() {
      return this.s.hauptdelikte.find((d) => d.value === this.a.hauptdelikt);
    },
    hauptdelikteNach(altrechtlich) {
      return this.s.hauptdelikte.filter((d) => d.altrechtlich === altrechtlich);
    },
    get deliktsscore() {
      if (this.a.uebrigeFrage === "nein") return 0;
      if (this.a.uebrigeFrage !== "ja") return null;
      const zahl = (w) => Math.max(0, parseInt(w, 10) || 0);
      return 2 * zahl(this.a.verbrechen) + zahl(this.a.vergehen) + zahl(this.a.mehrfachUebrige);
    },

    // --- Bewertung ------------------------------------------------------------

    // Jedes Kriterium trägt neben Gewicht und Übereinstimmung (0-1) die
    // verglichenen Werte und eine Begründung, damit die Badges der
    // Ergebnisseite per Tooltip nachvollziehbar sind (kriteriumTooltip).
    kriterien(u) {
      const a = this.a;
      const k = [];
      const add = (name, gewicht, wert, label, fall, urteil, grund) =>
        k.push({ name, gewicht, wert, label, fall, urteil, grund: grund || "" });
      const jaNein = (b) => (b ? "ja" : "nein");

      if (a.hauptdelikt) {
        const gewaehlt = this.gewaehltesHauptdelikt();
        let wert = 0;
        let grund = "anderes Delikt";
        if (u.hauptdelikt === a.hauptdelikt) { wert = 1; grund = "identisch"; }
        else if (gewaehlt && u.hauptdelikt_artikel === gewaehlt.artikel) {
          wert = 0.85;
          grund = "gleicher Artikel, aber altes statt neues Recht (oder umgekehrt)";
        } else if (gewaehlt && ["189", "190"].includes(gewaehlt.artikel) && ["189", "190"].includes(u.hauptdelikt_artikel)) {
          wert = 0.4;
          grund = "sexuelle Nötigung und Vergewaltigung sind verwandte Nötigungstatbestände";
        }
        add("hauptdelikt", PF_GEWICHTE.hauptdelikt, wert, "Hauptdelikt", a.hauptdelikt, u.hauptdelikt, grund);
      }
      if (a.tatmittel) {
        const naehe = PF_TATMITTEL_NAEHE[`${a.tatmittel}|${u.tatmittel}`];
        const wert = u.tatmittel === a.tatmittel ? 1 : naehe || 0;
        const grund = u.tatmittel === a.tatmittel ? "identisch"
          : naehe ? "Gewalt und psychischer Druck sind beides Nötigungsmittel" : "anderes Tatmittel";
        add("tatmittel", PF_GEWICHTE.tatmittel, wert, "Tatmittel", a.tatmittel, u.tatmittel, grund);
      }
      if (a.opferalter) {
        let wert = 0.3;
        let grund = "Opferalter im Urteil nicht bekannt (pauschal 30 %)";
        const i = PF_ALTERSSTUFEN.indexOf(a.opferalter);
        const j = PF_ALTERSSTUFEN.indexOf(u.opferalter);
        if (j >= 0) {
          const d = Math.abs(i - j);
          wert = Math.max(0, 1 - d / 3);
          grund = d === 0 ? "gleiche Altersstufe"
            : `${d} Altersstufe${d === 1 ? "" : "n"} entfernt (je Stufe ein Drittel Abzug)`;
        }
        add("opferalter", PF_GEWICHTE.opferalter, wert, "Opferalter",
          this.label("opferalter", a.opferalter), u.opferalter_label, grund);
      }
      if (a.beziehung) {
        let wert = 0;
        let grund = "andere Art von Beziehung";
        if (u.beziehung === a.beziehung) { wert = 1; grund = "identisch"; }
        else if (u.beziehung === "Beziehung unbekannt") { wert = 0.3; grund = "Beziehung im Urteil unbekannt (pauschal 30 %)"; }
        else {
          const gruppe = (b) => (this.s.beziehungen.find((x) => x.value === b) || {}).gruppe;
          if (gruppe(u.beziehung) && gruppe(u.beziehung) === gruppe(a.beziehung)) {
            wert = 0.6;
            grund = "ähnliche Beziehung (gleiche Gruppe, z.B. Familie oder Bekannte)";
          }
        }
        add("beziehung", PF_GEWICHTE.beziehung, wert, "Täter-Opfer-Beziehung", a.beziehung, u.beziehung, grund);
      }
      if (a.mehrfach) {
        let wert = (a.mehrfach === "ja") === u.mehrfach ? 1 : 0;
        let grund = wert ? "übereinstimmend" : "einmalige statt mehrfache Begehung (oder umgekehrt)";
        const anzahl = parseInt(a.anzahl, 10);
        const fall = a.mehrfach === "ja" ? `mehrfach${anzahl > 1 ? ` (${anzahl} Taten)` : ""}` : "einmalig";
        const urteil = u.mehrfach ? `mehrfach${u.anzahl > 1 ? ` (${u.anzahl} Taten)` : ""}` : "einmalig";
        if (wert && a.mehrfach === "ja" && anzahl > 1 && u.anzahl > 1) {
          // Anzahl Taten logarithmisch vergleichen: 5 vs. 10 liegt näher als 1 vs. 6
          const abstand = Math.abs(Math.log(anzahl) - Math.log(u.anzahl));
          wert = Math.max(0.5, 1 - abstand / 3);
          if (wert < 0.99) grund = "beide mehrfach, aber unterschiedliche Anzahl Taten (Abzug nach Verhältnis, mind. 50 %)";
        }
        add("mehrfach", PF_GEWICHTE.mehrfach, wert, "Einfache/mehrfache Begehung", fall, urteil, grund);
      }
      const versuch = a.besonderheiten["Versuch"];
      if (versuch) {
        const hat = u.besonderheiten.includes("Versuch");
        const wert = (versuch === "ja") === hat ? 1 : 0;
        add("versuch", PF_GEWICHTE.versuch, wert, "Versuch", versuch, jaNein(hat),
          wert ? "übereinstimmend" : "vollendet statt versucht (oder umgekehrt)");
      }
      if (a.weitereFrage) {
        const vorhanden = new Set(u.weitere_artikel);
        const urteil = vorhanden.size ? [...vorhanden].map((x) => `Art. ${x}`).join(", ") : "keine";
        let wert;
        let grund;
        let fall;
        if (a.weitereFrage === "nein") {
          fall = "keine";
          wert = vorhanden.size === 0 ? 1 : 0;
          grund = wert ? "übereinstimmend keine" : "das Urteil enthält weitere Sexualdelikte";
        } else if (a.weitere.length === 0) {
          fall = "ja (nicht näher bestimmt)";
          wert = vorhanden.size > 0 ? 1 : 0;
          grund = wert ? "das Urteil enthält ebenfalls weitere Sexualdelikte" : "das Urteil enthält keine weiteren Sexualdelikte";
        } else {
          const gesucht = new Set(a.weitere);
          fall = [...gesucht].map((x) => `Art. ${x}`).join(", ");
          const schnitt = [...gesucht].filter((x) => vorhanden.has(x)).length;
          const vereinigung = new Set([...gesucht, ...vorhanden]).size;
          wert = schnitt / vereinigung;
          grund = `${schnitt} von ${vereinigung} genannten Artikeln gemeinsam`;
        }
        add("weitere", PF_GEWICHTE.weitere, wert, "Weitere Sexualdelikte", fall, urteil, grund);
      }
      const score = this.deliktsscore;
      if (score !== null) {
        let wert = 0.3;
        let grund = "Deliktsscore im Urteil nicht erfasst (pauschal 30 %)";
        if (u.deliktsscore !== null) {
          const d = Math.abs(score - u.deliktsscore);
          wert = Math.max(0, 1 - d / 4);
          grund = d === 0 ? "gleicher Score" : `Differenz ${d} Punkt${d === 1 ? "" : "e"} (je Punkt ein Viertel Abzug)`;
        }
        add("uebrige", PF_GEWICHTE.uebrige, wert, "Übrige Delikte", `Score ${score}`,
          u.deliktsscore === null ? "nicht erfasst" : `Score ${u.deliktsscore}`, grund);
      }
      if (a.vorstrafen) {
        const rang = { keine: 0, nicht_einschlaegig: 1, einschlaegig: 2 };
        const text = ["keine", "nicht einschlägig", "einschlägig"];
        const uRang = u.einschlaegig ? 2 : u.vorbestraft ? 1 : 0;
        const d = Math.abs(rang[a.vorstrafen] - uRang);
        const wert = Math.max(0, 1 - d / 2);
        const grund = d === 0 ? "übereinstimmend" : d === 1 ? "eine Stufe entfernt (keine – nicht einschlägig – einschlägig)" : "gegensätzlich";
        add("vorstrafen", PF_GEWICHTE.vorstrafen, wert, "Vorstrafen", text[rang[a.vorstrafen]], text[uRang], grund);
      }
      for (const [name, antwort] of Object.entries(a.besonderheiten)) {
        if (name === "Versuch") continue;
        const hat = u.besonderheiten.includes(name);
        const wert = (antwort === "ja") === hat ? 1 : 0;
        add(`b:${name}`, PF_GEWICHTE.besonderheit, wert, name, antwort, jaNein(hat),
          wert ? "übereinstimmend" : "abweichend");
      }
      return k;
    },

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
    // Urteile, die beim Hauptdelikt (ggf. über altes/neues Recht) übereinstimmen
    get passendesHauptdelikt() {
      const gewaehlt = this.gewaehltesHauptdelikt();
      if (!gewaehlt) return this.urteile.length;
      return this.urteile.filter((u) => u.hauptdelikt_artikel === gewaehlt.artikel).length;
    },
    get sehrAehnlich() {
      return this.bewertet.filter((b) => b.aehnlichkeit >= 0.8).length;
    },

    // Kennzahlen der angezeigten Treffer (nur Freiheitsstrafen, ohne lebenslänglich)
    get kennzahlen() {
      const fs = this.treffer
        .filter((b) => b.u.hauptsanktion === "0" && b.u.freiheitsstrafe !== PF_LEBENSLAENGLICH)
        .map((b) => b.u.freiheitsstrafe)
        .sort((x, y) => x - y);
      const median = fs.length
        ? fs.length % 2 ? fs[(fs.length - 1) / 2] : (fs[fs.length / 2 - 1] + fs[fs.length / 2]) / 2
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
        anzahlFs: fs.length,
        median,
        min: fs.length ? fs[0] : null,
        max: fs.length ? fs[fs.length - 1] : null,
        vollzug: vollzug.filter((g) => Object.values(g.anzahl).some((n) => n > 0)),
      };
    },

    // --- Anzeige --------------------------------------------------------------

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
    label(liste, wert) {
      const eintrag = this.s[liste].find((x) => x.value === wert);
      return eintrag ? eintrag.label || eintrag.titel || eintrag.value : wert;
    },
    // Zusammenfassung der bisherigen Antworten für die Seitenleiste
    get antworten() {
      const a = this.a;
      const zeilen = [];
      const hd = this.gewaehltesHauptdelikt();
      if (hd) zeilen.push(["Hauptdelikt", `Art. ${hd.artikel} – ${hd.titel}`]);
      if (a.tatmittel) zeilen.push(["Tatmittel", a.tatmittel]);
      if (a.opferalter) zeilen.push(["Opferalter", this.label("opferalter", a.opferalter)]);
      if (a.beziehung) zeilen.push(["Beziehung", this.label("beziehungen", a.beziehung)]);
      if (a.mehrfach) zeilen.push(["Begehung", a.mehrfach === "ja" ? `mehrfach${parseInt(a.anzahl, 10) > 1 ? ` (${parseInt(a.anzahl, 10)}×)` : ""}` : "einmalig"]);
      if (a.weitereFrage === "nein") zeilen.push(["Weitere Sexualdelikte", "keine"]);
      if (a.weitereFrage === "ja") zeilen.push(["Weitere Sexualdelikte", a.weitere.length ? a.weitere.map((x) => `Art. ${x}`).join(", ") : "ja"]);
      if (this.deliktsscore !== null) zeilen.push(["Deliktsscore übrige", String(this.deliktsscore)]);
      const vs = { keine: "keine", nicht_einschlaegig: "nicht einschlägig", einschlaegig: "einschlägig" };
      if (a.vorstrafen) zeilen.push(["Vorstrafen", vs[a.vorstrafen]]);
      for (const [name, antwort] of Object.entries(a.besonderheiten)) zeilen.push([name, antwort]);
      return zeilen;
    },
  }));
});
