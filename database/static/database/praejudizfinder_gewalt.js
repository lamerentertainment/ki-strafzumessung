/*
 * Geführte Präjudiziensuche für Gewaltdelikte ("Präjudizen finden").
 *
 * Deliktspezifischer Teil; Navigation, Bewertung, Ergebnisliste und die
 * gemeinsamen Kriterien (übrige Delikte, Vorstrafen, Besonderheiten) stehen
 * in praejudizfinder_basis.js. Schritte und Erläuterungen kommen aus
 * database/praejudizfinder.py (json_script "pf-schritte"), die Urteile aus
 * "pf-urteile".
 */

// Gewichte der Kriterien, vorerst nach Ermessen; empirischer Vergleich auf der
// Dev-Seite ridge_auswertung/gewalt. Bei einer Änderung dort auch
// GEWALT_KONFIG["suchkriterien"] in ridge_auswertung.py nachführen. Hauptdelikt,
// Versuch und Verletzungsfolge bestimmen Strafrahmen und Erfolgsunrecht und
// wiegen darum am schwersten. Übrige Delikte, Vorstrafen und Besonderheiten:
// PF_BASIS_GEWICHTE.
const PF_GEWALT_GEWICHTE = {
  hauptdelikt: 30,
  versuch: 15,
  verletzungsfolge: 15,
  vorsatzform: 8,
  tatmittel: 8,
  lebensgefahr: 6,
  besondere_gefaehrlichkeit: 6,
  waffe_gefaehrlicher_gegenstand: 4,
  mehrfach: 6,
  opferzahl: 4,
  beziehung: 5,
  deliktssumme: 5,
  koerperteil: 3,
  substanzeinfluss: 3,
};

// Teilübereinstimmung zwischen Gruppen von Hauptdelikten (gleiche Gruppe: 50 %)
const PF_GEWALT_GRUPPEN_NAEHE = {
  "toetung|schwer": 0.3,
  "schwer|einfach": 0.3,
  "einfach|beteiligung": 0.3,
  "schwer|beteiligung": 0.2,
};

const PF_VORSATZ_REIHE = ["fahrlaessig", "eventualvorsatz", "direktvorsatz"];
const PF_VERLETZUNGSFOLGE_REIHE = ["keine", "Tätlichkeit", "leicht", "erheblich", "schwer", "lebensgefährlich", "Tod"];

const PF_QUALIFIKATIONS_LABEL = {
  waffe_gefaehrlicher_gegenstand: "Waffe/gefährlicher Gegenstand",
  besondere_gefaehrlichkeit: "besondere Gefährlichkeit",
  lebensgefahr: "Lebensgefahr",
};

document.addEventListener("alpine:init", () => {
  Alpine.data("praejudizfinder", praejudizfinderKomponente(() => ({
    schritte: [
      { key: "hauptdelikt", titel: "Hauptdelikt", kriterien: ["versuch", "hauptdelikt"] },
      { key: "tat", titel: "Tatbegehung", kriterien: ["vorsatzform", "mehrfach", "opferzahl", "deliktssumme"] },
      {
        key: "tatmittel", titel: "Tatmittel & Qualifikationen",
        kriterien: ["tatmittel", "waffe_gefaehrlicher_gegenstand", "besondere_gefaehrlichkeit", "lebensgefahr"],
      },
      { key: "opfer", titel: "Opfer & Folgen", kriterien: ["verletzungsfolge", "koerperteil", "beziehung"] },
      { key: "uebrige", titel: "Übrige Delikte", kriterien: ["uebrige"] },
      { key: "taeter", titel: "Täter & Verfahren", kriterien: ["substanzeinfluss", "vorstrafen", "besonderheit"] },
      { key: "ergebnis", titel: "Ähnliche Urteile" },
    ],
    // Gewicht und Punktevergabe je Kriterium, wie in kriterien() umgesetzt
    regeln: (() => {
      const G = PF_GEWALT_GEWICHTE;
      const n = PF_GEWALT_GRUPPEN_NAEHE;
      const jaNein = (label, gewicht) => ({
        label, gewicht, vergabe: ["übereinstimmend ja bzw. nein: volle Punkte, sonst 0"],
      });
      return {
        hauptdelikt: {
          label: "Hauptdelikt",
          gewicht: G.hauptdelikt,
          vergabe: [
            "gleiches Hauptdelikt: volle Punkte",
            "verwandtes Delikt derselben Gruppe (z.B. Mord ↔ vorsätzliche Tötung): 50 %",
            `Tötungsdelikte ↔ schwere Körperverletzung/Lebensgefährdung: ${n["toetung|schwer"] * 100} %`,
            `schwere ↔ einfache Körperverletzung: ${n["schwer|einfach"] * 100} %; einfache Körperverletzung ↔ Schlägereien: ${n["einfach|beteiligung"] * 100} %; schwere Körperverletzung ↔ Schlägereien: ${n["schwer|beteiligung"] * 100} %`,
            "anderes Delikt: 0",
          ],
        },
        versuch: {
          label: "Versuch",
          gewicht: G.versuch,
          vergabe: ["übereinstimmend vollendet bzw. versucht: volle Punkte, sonst 0"],
        },
        vorsatzform: {
          label: "Vorsatzform",
          gewicht: G.vorsatzform,
          vergabe: [
            "gleiche Vorsatzform: volle Punkte",
            "Eventualvorsatz ↔ direkter Vorsatz: 50 %",
            "im Urteil nicht bekannt: 30 %",
            "entfällt bei fahrlässigen Hauptdelikten (die Fahrlässigkeit steckt schon im Hauptdelikt)",
          ],
        },
        mehrfach: jaNein("Einfache/mehrfache Begehung", G.mehrfach),
        opferzahl: {
          label: "Anzahl Opfer",
          gewicht: G.opferzahl,
          vergabe: ["gleiche Anzahl: volle Punkte", "je Opfer Unterschied ein Drittel Abzug"],
        },
        deliktssumme: {
          label: "Beute (nur Raub)",
          gewicht: G.deliktssumme,
          vergabe: [
            "Vergleich nach Grössenordnung: je Zehnerpotenz Unterschied die Hälfte Abzug (CHF 1'000 ↔ 10'000: 50 %)",
            "Beute im Urteil nicht beziffert: 30 %",
          ],
        },
        tatmittel: {
          label: "Tatmittel",
          gewicht: G.tatmittel,
          vergabe: [
            "gleiches Tatmittel: volle Punkte",
            "ähnliches Tatmittel (Messer/Schusswaffe/Schlagwerkzeug bzw. Faust/Würgen): 50 %",
            "im Urteil nicht bekannt: 30 %",
          ],
        },
        waffe_gefaehrlicher_gegenstand: jaNein(PF_QUALIFIKATIONS_LABEL.waffe_gefaehrlicher_gegenstand, G.waffe_gefaehrlicher_gegenstand),
        besondere_gefaehrlichkeit: jaNein(PF_QUALIFIKATIONS_LABEL.besondere_gefaehrlichkeit, G.besondere_gefaehrlichkeit),
        lebensgefahr: jaNein(PF_QUALIFIKATIONS_LABEL.lebensgefahr, G.lebensgefahr),
        verletzungsfolge: {
          label: "Verletzungsfolge",
          gewicht: G.verletzungsfolge,
          vergabe: [
            "gleiche Stufe: volle Punkte",
            "je Stufe Abstand ein Drittel Abzug (z.B. erheblich ↔ schwer: 67 %, ab 3 Stufen: 0)",
            "im Urteil nicht bekannt: 30 %",
          ],
        },
        koerperteil: {
          label: "Angegriffenes Körperteil",
          gewicht: G.koerperteil,
          vergabe: [
            "gleiche Körperregion: volle Punkte",
            "eine Seite «mehrere Regionen»: 50 %",
            "im Urteil nicht bekannt: 30 %",
          ],
        },
        beziehung: {
          label: "Täter-Opfer-Beziehung",
          gewicht: G.beziehung,
          vergabe: [
            "gleiche Beziehung: volle Punkte",
            "ähnliche Beziehung (Partner/Familie bzw. Bekannte/flüchtig Bekannte): 60 %",
            "im Urteil unbekannt: 30 %",
          ],
        },
        substanzeinfluss: {
          label: "Substanzeinfluss",
          gewicht: G.substanzeinfluss,
          vergabe: [
            "gleiche Angabe: volle Punkte",
            "beide unter Einfluss, aber andere Substanz: 50 %",
            "im Urteil nicht bekannt: 30 %",
          ],
        },
      };
    })(),
    passendLabel: "Urteile mit diesem Hauptdelikt",

    leereAntworten() {
      return {
        ...PF_BASIS_ANTWORTEN(),
        hauptdelikt: null,
        versuch: null, // "ja" | "nein" | null
        vorsatzform: null,
        mehrfach: null,
        opferzahl: null,
        deliktssumme: null,
        tatmittel: null,
        qualifikationen: {}, // feld -> "ja" | "nein"
        verletzungsfolge: null,
        koerperteil: null,
        beziehung: null,
        substanzeinfluss: null,
      };
    },
    qualifikationWaehlen(feld, wert) {
      const neu = { ...this.a.qualifikationen };
      if (neu[feld] === wert) delete neu[feld];
      else neu[feld] = wert;
      this.a.qualifikationen = neu;
    },
    gewaehltesHauptdelikt() {
      return this.s.hauptdelikte.find((d) => d.value === this.a.hauptdelikt);
    },
    hauptdelikteInGruppe(gruppe) {
      return this.s.hauptdelikte.filter((d) => d.gruppe === gruppe);
    },
    // Der Versuch steht zwar zuoberst, wird aber leicht übersprungen, wer
    // direkt ein Hauptdelikt anklickt
    get weiterHinweis() {
      if (this.aktuellerKey === "hauptdelikt" && this.a.hauptdelikt && !this.a.versuch) {
        return "Vollendet oder versucht? Noch offen";
      }
      return "";
    },
    init() {
      // Eine Vorsatzform, die nicht zum (neu) gewählten Hauptdelikt passt,
      // wird verworfen, statt unbemerkt in die Bewertung einzufliessen
      this.$watch("a.hauptdelikt", () => {
        if (this.a.vorsatzform && !this.vorsatzformenErlaubt.some((v) => v.value === this.a.vorsatzform)) {
          this.a.vorsatzform = null;
        }
      });
    },
    get istFahrlaessig() {
      const hd = this.gewaehltesHauptdelikt();
      return Boolean(hd && hd.gruppe === "fahrlaessig");
    },
    // Fahrlässige Hauptdelikte (Art. 117/125 StGB) sind per Definition
    // fahrlässig, vorsätzliche schliessen Fahrlässigkeit aus: Angeboten werden
    // nur die zum Hauptdelikt passenden Vorsatzformen.
    get vorsatzformenErlaubt() {
      if (this.istFahrlaessig) return [];
      return this.s.vorsatzformen.filter((v) => v.value !== "fahrlaessig");
    },
    kriteriumAktiv(kriterium) {
      if (kriterium === "deliktssumme") return this.istRaub;
      if (kriterium === "vorsatzform") return !this.istFahrlaessig;
      return true;
    },
    get istRaub() {
      return this.a.hauptdelikt === "Raub";
    },
    get passendesHauptdelikt() {
      if (!this.a.hauptdelikt) return this.urteile.length;
      return this.urteile.filter((u) => u.hauptdelikt === this.a.hauptdelikt).length;
    },

    kriterien(u) {
      const a = this.a;
      const G = PF_GEWALT_GEWICHTE;
      const k = this.kriterienListe();
      const gruppeVon = (hd) => (this.s.hauptdelikte.find((d) => d.value === hd) || {}).gruppe;

      if (a.hauptdelikt) {
        let wert = 0;
        let grund = "anderes Delikt";
        const g1 = gruppeVon(a.hauptdelikt);
        const g2 = gruppeVon(u.hauptdelikt);
        if (u.hauptdelikt === a.hauptdelikt) { wert = 1; grund = "identisch"; }
        else if (g1 && g1 === g2) { wert = 0.5; grund = "verwandtes Delikt derselben Gruppe"; }
        else {
          const naehe = PF_GEWALT_GRUPPEN_NAEHE[`${g1}|${g2}`] || PF_GEWALT_GRUPPEN_NAEHE[`${g2}|${g1}`];
          if (naehe) {
            wert = naehe;
            grund = "benachbarte Deliktsgruppe (z.B. versuchte Tötung und schwere Körperverletzung)";
          }
        }
        k.add("hauptdelikt", G.hauptdelikt, wert, "Hauptdelikt", a.hauptdelikt, u.hauptdelikt, grund);
      }
      if (a.versuch) {
        const { wert } = this.jaNeinVergleich(a.versuch, u.versuch);
        k.add("versuch", G.versuch, wert, "Versuch", a.versuch, u.versuch ? "ja" : "nein",
          wert ? "übereinstimmend" : "vollendet statt versucht (oder umgekehrt)");
      }
      if (a.vorsatzform && this.kriteriumAktiv("vorsatzform")) {
        const { wert, grund } = this.ordinal(PF_VORSATZ_REIHE, a.vorsatzform, u.vorsatzform, 2);
        k.add("vorsatzform", G.vorsatzform, wert, "Vorsatzform",
          this.label("vorsatzformen", a.vorsatzform), u.vorsatzform_label, grund);
      }
      if (a.mehrfach) {
        const { wert, grund } = this.jaNeinVergleich(a.mehrfach, u.mehrfach);
        k.add("mehrfach", G.mehrfach, wert, "Einfache/mehrfache Begehung",
          a.mehrfach === "ja" ? "mehrfach" : "einmalig", u.mehrfach ? "mehrfach" : "einmalig", grund);
      }
      const opferzahl = parseInt(a.opferzahl, 10);
      if (opferzahl > 0) {
        const d = Math.abs(opferzahl - u.opferzahl);
        const wert = Math.max(0, 1 - d / 3);
        k.add("opferzahl", G.opferzahl, wert, "Anzahl Opfer", String(opferzahl), String(u.opferzahl),
          d === 0 ? "übereinstimmend" : `${d} Opfer Unterschied (je Opfer ein Drittel Abzug)`);
      }
      const summe = parseInt(a.deliktssumme, 10);
      if (this.istRaub && summe > 0) {
        let wert = 0.3;
        let grund = "Beute im Urteil nicht beziffert (pauschal 30 %)";
        if (u.deliktssumme > 0) {
          // Logarithmisch: 1'000 vs. 2'000 Franken liegt so nah wie 10'000 vs. 20'000
          const faktor = Math.abs(Math.log10(summe) - Math.log10(u.deliktssumme));
          wert = Math.max(0, 1 - faktor / 2);
          grund = faktor < 0.01 ? "übereinstimmend" : "andere Grössenordnung (je Zehnerpotenz die Hälfte Abzug)";
        }
        k.add("deliktssumme", G.deliktssumme, wert, "Beute", this.franken(summe),
          u.deliktssumme ? this.franken(u.deliktssumme) : "nicht beziffert", grund);
      }
      if (a.tatmittel) {
        const gruppe = (t) => (this.s.tatmittel.find((x) => x.value === t) || {}).gruppe;
        const { wert, grund } = this.gruppenvergleich(a.tatmittel, u.tatmittel, gruppe, 0.5,
          "ähnliches Tatmittel (z.B. Messer und Schlagwerkzeug, Faustschläge und Würgen)", ["unbekannt"]);
        k.add("tatmittel", G.tatmittel, wert, "Tatmittel", this.label("tatmittel", a.tatmittel), u.tatmittel_label, grund);
      }
      for (const [feld, antwort] of Object.entries(a.qualifikationen)) {
        const { wert, grund } = this.jaNeinVergleich(antwort, u[feld]);
        k.add(feld, G[feld], wert, PF_QUALIFIKATIONS_LABEL[feld], antwort, u[feld] ? "ja" : "nein", grund);
      }
      if (a.verletzungsfolge) {
        const { wert, grund } = this.ordinal(PF_VERLETZUNGSFOLGE_REIHE, a.verletzungsfolge, u.verletzungsfolge, 3);
        k.add("verletzungsfolge", G.verletzungsfolge, wert, "Verletzungsfolge",
          this.label("verletzungsfolgen", a.verletzungsfolge), u.verletzungsfolge_label, grund);
      }
      if (a.koerperteil) {
        let wert = 0;
        let grund = "andere Körperregion";
        if (u.koerperteil === a.koerperteil) { wert = 1; grund = "identisch"; }
        else if (u.koerperteil === "unbekannt") { wert = 0.3; grund = "im Urteil nicht bekannt (pauschal 30 %)"; }
        else if ([a.koerperteil, u.koerperteil].includes("mehrere")) {
          wert = 0.5;
          grund = "eine Seite betrifft mehrere Körperregionen";
        }
        k.add("koerperteil", G.koerperteil, wert, "Angegriffenes Körperteil",
          this.label("koerperteile", a.koerperteil), u.koerperteil_label, grund);
      }
      if (a.beziehung) {
        const gruppe = (b) => (this.s.beziehungen.find((x) => x.value === b) || {}).gruppe;
        const { wert, grund } = this.gruppenvergleich(a.beziehung, u.beziehung, gruppe, 0.6,
          "ähnliche Beziehung (gleiche Gruppe, z.B. Partner und Familie)", ["unbekannt"]);
        k.add("beziehung", G.beziehung, wert, "Täter-Opfer-Beziehung",
          this.label("beziehungen", a.beziehung), u.beziehung_label, grund);
      }
      if (a.substanzeinfluss) {
        const gruppe = (x) => (x === "nein" ? "nein" : "substanz");
        const { wert, grund } = this.gruppenvergleich(a.substanzeinfluss, u.substanzeinfluss, gruppe, 0.5,
          "beide unter Substanzeinfluss, aber unterschiedliche Substanzen", ["unbekannt"]);
        k.add("substanzeinfluss", G.substanzeinfluss, wert, "Substanzeinfluss",
          this.label("substanzen", a.substanzeinfluss), u.substanzeinfluss_label, grund);
      }
      this.gemeinsameKriterien(u, k);
      return k;
    },

    franken(x) {
      return `CHF ${Math.round(x).toLocaleString("de-CH")}`;
    },
    trefferZeile(u) {
      const teile = [u.hauptdelikt_label + (u.versuch ? ", versucht" : "") + (u.mehrfach ? ", mehrfach" : "")];
      if (u.tatmittel !== "unbekannt") teile.push(u.tatmittel_label);
      if (u.verletzungsfolge !== "unbekannt") teile.push(`Folge: ${u.verletzungsfolge_label}`);
      return teile.join(" · ");
    },

    // Zusammenfassung der bisherigen Antworten für die Seitenleiste
    get antworten() {
      const a = this.a;
      const zeilen = [];
      const hd = this.gewaehltesHauptdelikt();
      if (hd) zeilen.push(["Hauptdelikt", hd.label]);
      if (a.versuch) zeilen.push(["Versuch", a.versuch]);
      if (a.vorsatzform) zeilen.push(["Vorsatzform", this.label("vorsatzformen", a.vorsatzform)]);
      if (a.mehrfach) zeilen.push(["Begehung", a.mehrfach === "ja" ? "mehrfach" : "einmalig"]);
      if (parseInt(a.opferzahl, 10) > 0) zeilen.push(["Anzahl Opfer", String(parseInt(a.opferzahl, 10))]);
      if (this.istRaub && parseInt(a.deliktssumme, 10) > 0) zeilen.push(["Beute", this.franken(parseInt(a.deliktssumme, 10))]);
      if (a.tatmittel) zeilen.push(["Tatmittel", this.label("tatmittel", a.tatmittel)]);
      for (const [feld, antwort] of Object.entries(a.qualifikationen)) zeilen.push([PF_QUALIFIKATIONS_LABEL[feld], antwort]);
      if (a.verletzungsfolge) zeilen.push(["Verletzungsfolge", this.label("verletzungsfolgen", a.verletzungsfolge)]);
      if (a.koerperteil) zeilen.push(["Körperteil", this.label("koerperteile", a.koerperteil)]);
      if (a.beziehung) zeilen.push(["Beziehung", this.label("beziehungen", a.beziehung)]);
      if (a.substanzeinfluss) zeilen.push(["Substanzeinfluss", this.label("substanzen", a.substanzeinfluss)]);
      return this.gemeinsameAntworten(zeilen);
    },
  })));
});
