/*
 * Geführte Präjudiziensuche für Sexualdelikte ("Präjudizen finden").
 *
 * Deliktspezifischer Teil; Navigation, Bewertung, Ergebnisliste und die
 * gemeinsamen Kriterien stehen in praejudizfinder_basis.js. Schritte und
 * Erläuterungen kommen aus database/praejudizfinder.py (json_script
 * "pf-schritte"), die Urteile aus "pf-urteile".
 */

// Gewichte der Kriterien (nach Ermessen; empirischer Vergleich auf der
// Dev-Seite sexual_evaluation). Übrige Delikte, Vorstrafen und Besonderheiten:
// PF_BASIS_GEWICHTE.
const PF_GEWICHTE = {
  hauptdelikt: 30,
  tatmittel: 15,
  opferalter: 12,
  beziehung: 7,
  mehrfach: 9,
  weitere: 7,
  versuch: 9,
};

// Ordinale Reihenfolge des Opferalters, jüngste zuerst
const PF_ALTERSSTUFEN = ["unter_6", "unter_10", "unter_14", "unter_16", "unter_18", "erwachsen"];

// Beide Tatmittel sind Nötigungsmittel und liegen sich näher als die übrigen
const PF_TATMITTEL_NAEHE = { "Gewalt|psychischer Druck": 0.5, "psychischer Druck|Gewalt": 0.5 };

document.addEventListener("alpine:init", () => {
  Alpine.data("praejudizfinder", praejudizfinderKomponente(() => ({
    schritte: [
      { key: "hauptdelikt", titel: "Hauptdelikt", kriterien: ["hauptdelikt"] },
      { key: "tatmittel", titel: "Tatmittel", kriterien: ["tatmittel"] },
      { key: "opfer", titel: "Opfer", kriterien: ["opferalter", "beziehung"] },
      { key: "tat", titel: "Tatbegehung", kriterien: ["mehrfach", "versuch"] },
      { key: "weitere", titel: "Weitere Sexualdelikte", kriterien: ["weitere"] },
      { key: "uebrige", titel: "Übrige Delikte", kriterien: ["uebrige"] },
      { key: "taeter", titel: "Täter & Verfahren", kriterien: ["vorstrafen", "besonderheit"] },
      { key: "ergebnis", titel: "Ähnliche Urteile" },
    ],
    // Gewicht und Punktevergabe je Kriterium, wie in kriterien() umgesetzt
    regeln: {
      hauptdelikt: {
        label: "Hauptdelikt",
        gewicht: PF_GEWICHTE.hauptdelikt,
        vergabe: [
          "gleiches Hauptdelikt: volle Punkte",
          "gleicher Artikel, aber altes statt neues Recht (oder umgekehrt): 85 %",
          "sexuelle Nötigung ↔ Vergewaltigung (Art. 189/190): 40 %",
          "anderes Delikt: 0",
        ],
      },
      tatmittel: {
        label: "Tatmittel",
        gewicht: PF_GEWICHTE.tatmittel,
        vergabe: [
          "gleiches Tatmittel: volle Punkte",
          `Gewalt ↔ psychischer Druck (beides Nötigungsmittel): ${PF_TATMITTEL_NAEHE["Gewalt|psychischer Druck"] * 100} %`,
          "anderes Tatmittel: 0",
        ],
      },
      opferalter: {
        label: "Opferalter",
        gewicht: PF_GEWICHTE.opferalter,
        vergabe: [
          "gleiche Altersstufe: volle Punkte",
          "je Altersstufe Abstand ein Drittel Abzug (ab 3 Stufen: 0)",
          "Alter im Urteil nicht bekannt: 30 %",
        ],
      },
      beziehung: {
        label: "Täter-Opfer-Beziehung",
        gewicht: PF_GEWICHTE.beziehung,
        vergabe: [
          "gleiche Beziehung: volle Punkte",
          "ähnliche Beziehung (Familie bzw. Bekannte/flüchtig Bekannte): 60 %",
          "Beziehung im Urteil unbekannt: 30 %",
          "andere Beziehung: 0",
        ],
      },
      mehrfach: {
        label: "Einfache/mehrfache Begehung",
        gewicht: PF_GEWICHTE.mehrfach,
        vergabe: [
          "übereinstimmend einmalig bzw. mehrfach: volle Punkte",
          "beide mehrfach mit Anzahl Taten: Abzug nach Verhältnis der Anzahl, mindestens 50 %",
          "einmalig ↔ mehrfach: 0",
        ],
      },
      versuch: {
        label: "Versuch",
        gewicht: PF_GEWICHTE.versuch,
        vergabe: ["übereinstimmend vollendet bzw. versucht: volle Punkte, sonst 0"],
      },
      weitere: {
        label: "Weitere Sexualdelikte",
        gewicht: PF_GEWICHTE.weitere,
        vergabe: [
          "«nein»: volle Punkte, wenn das Urteil ebenfalls keine weiteren Sexualdelikte enthält, sonst 0",
          "Artikel gewählt: Anteil gemeinsamer Artikel an allen genannten (z.B. 1 von 3 = 33 %)",
          "«ja» ohne Auswahl: volle Punkte, wenn das Urteil weitere Sexualdelikte enthält",
        ],
      },
    },
    // Versuch wird im Schritt "Tatbegehung" gefragt und als eigenes Kriterium
    // (mit höherem Gewicht) bewertet
    besonderheitenSeparat: ["Versuch"],
    passendLabel: "Urteile zum selben Artikel",

    leereAntworten() {
      return {
        ...PF_BASIS_ANTWORTEN(),
        hauptdelikt: null,
        tatmittel: null,
        opferalter: null,
        beziehung: null,
        mehrfach: null, // "ja" | "nein" | null
        anzahl: null,
        weitereFrage: null, // "ja" | "nein" | null
        weitere: [],
      };
    },
    weitereUmschalten(artikel) {
      const i = this.a.weitere.indexOf(artikel);
      if (i >= 0) this.a.weitere.splice(i, 1);
      else this.a.weitere.push(artikel);
    },
    gewaehltesHauptdelikt() {
      return this.s.hauptdelikte.find((d) => d.value === this.a.hauptdelikt);
    },
    hauptdelikteNach(altrechtlich) {
      return this.s.hauptdelikte.filter((d) => d.altrechtlich === altrechtlich);
    },
    // Urteile, die beim Hauptdelikt (ggf. über altes/neues Recht) übereinstimmen
    get passendesHauptdelikt() {
      const gewaehlt = this.gewaehltesHauptdelikt();
      if (!gewaehlt) return this.urteile.length;
      return this.urteile.filter((u) => u.hauptdelikt_artikel === gewaehlt.artikel).length;
    },

    kriterien(u) {
      const a = this.a;
      const k = this.kriterienListe();

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
        k.add("hauptdelikt", PF_GEWICHTE.hauptdelikt, wert, "Hauptdelikt", a.hauptdelikt, u.hauptdelikt, grund);
      }
      if (a.tatmittel) {
        const naehe = PF_TATMITTEL_NAEHE[`${a.tatmittel}|${u.tatmittel}`];
        const wert = u.tatmittel === a.tatmittel ? 1 : naehe || 0;
        const grund = u.tatmittel === a.tatmittel ? "identisch"
          : naehe ? "Gewalt und psychischer Druck sind beides Nötigungsmittel" : "anderes Tatmittel";
        k.add("tatmittel", PF_GEWICHTE.tatmittel, wert, "Tatmittel", a.tatmittel, u.tatmittel, grund);
      }
      if (a.opferalter) {
        const { wert, grund } = this.ordinal(PF_ALTERSSTUFEN, a.opferalter, u.opferalter, 3, "Altersstufe");
        k.add("opferalter", PF_GEWICHTE.opferalter, wert, "Opferalter",
          this.label("opferalter", a.opferalter), u.opferalter_label, grund);
      }
      if (a.beziehung) {
        const gruppe = (b) => (this.s.beziehungen.find((x) => x.value === b) || {}).gruppe;
        const { wert, grund } = this.gruppenvergleich(a.beziehung, u.beziehung, gruppe, 0.6,
          "ähnliche Beziehung (gleiche Gruppe, z.B. Familie oder Bekannte)", ["Beziehung unbekannt"]);
        k.add("beziehung", PF_GEWICHTE.beziehung, wert, "Täter-Opfer-Beziehung", a.beziehung, u.beziehung, grund);
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
        k.add("mehrfach", PF_GEWICHTE.mehrfach, wert, "Einfache/mehrfache Begehung", fall, urteil, grund);
      }
      const versuch = a.besonderheiten["Versuch"];
      if (versuch) {
        const hat = u.besonderheiten.includes("Versuch");
        const wert = (versuch === "ja") === hat ? 1 : 0;
        k.add("versuch", PF_GEWICHTE.versuch, wert, "Versuch", versuch, hat ? "ja" : "nein",
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
        k.add("weitere", PF_GEWICHTE.weitere, wert, "Weitere Sexualdelikte", fall, urteil, grund);
      }
      this.gemeinsameKriterien(u, k);
      return k;
    },

    trefferZeile(u) {
      return [
        u.hauptdelikt + (u.mehrfach ? ", mehrfach" : ""),
        u.tatmittel,
        `Opfer ${u.opferalter_label.toLowerCase()}`,
      ].join(" · ");
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
      if (a.besonderheiten["Versuch"]) zeilen.push(["Versuch", a.besonderheiten["Versuch"]]);
      if (a.weitereFrage === "nein") zeilen.push(["Weitere Sexualdelikte", "keine"]);
      if (a.weitereFrage === "ja") zeilen.push(["Weitere Sexualdelikte", a.weitere.length ? a.weitere.map((x) => `Art. ${x}`).join(", ") : "ja"]);
      return this.gemeinsameAntworten(zeilen);
    },
  })));
});
