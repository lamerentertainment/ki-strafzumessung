# Vermögensdelikt-Präjudizien-Recherche: Kandidatenliste (entscheidsuche.ch)

Gesamtschweizerische Recherche nach kantonalen Vermögensdelikt-Präjudizien für
`database.models.Urteil`. Die DB enthält aktuell **270 Fälle** (ursprünglich 258 ausschliesslich
aus dem Kanton Zürich, ergänzt um kantonale Entscheide aus AG, GE und BE) — gesucht sind Kandidaten aus
**allen übrigen Kantonen** für die Hauptdelikte Betrug (Art. 146 StGB), Veruntreuung (Art. 138 StGB), ungetreue Geschäftsbesorgung
(Art. 158 StGB), betrügerischer Missbrauch einer Datenverarbeitungsanlage (Art. 147 StGB),
Diebstahl (Art. 139 StGB) und Sachbeschädigung (Art. 144 StGB) — dasjenige Delikt, auf das
die vorinstanzliche Einsatzstrafe abgestützt wurde.

**Auswahlkriterium (User-Vorgabe):** Ein Fall eignet sich in der Regel, wenn (a) der
vorinstanzliche Schuldspruch von der Rechtsmittelinstanz **bestätigt** wird, oder (b) bei
(teilweiser) Abweisung/Änderung durch die Rechtsmittelinstanz der **vorinstanzliche
Schuldspruch selbst** einen **überschaubaren Sachverhalt** betraf, aus dem sich die
strafzumessungsrelevanten Punkte (Deliktssumme, mehrfach/gewerbsmässig/bandenmässig,
Vorstrafen, Vollzug) klar ablesen lassen. Massgebend für die DB ist ohnehin immer der
**vorinstanzliche** Schuldspruch und die vorinstanzliche Sanktion (CLAUDE.md Abschnitt 3).
Nicht geeignet: Freispruch/Herabstufung des Hauptdelikts im Rechtsmittelverfahren,
vollständige Rückweisungen, stark verschachtelte Serientäter-Fälle mit derart vielen
Einzelvorwürfen, dass sich Deliktssumme/Score nicht sauber isolieren lassen, sowie reine
Übertretungsfälle (geringfügiger Vermögenswert nach Art. 172ter StGB, Busse).

**Vor jedem DB-Insert:** vollständigen Urteilstext lesen (Duplikat-Check `fall_nr`,
Vorinstanz-Werte übernehmen, Choices prüfen, `full_clean()` vor `save()` — siehe CLAUDE.md
Abschnitt 4 und Skill `praejudiz-recherche`). Bei ⚠️-markierten Fällen war entweder der
Berufungsausgang bezüglich des Hauptdelikts aus dem Suchtreffer/Auszug nicht sicher
erkennbar, der über die Such-API zurückgegebene Volltext vor dem Dispositiv abgeschnitten,
oder der Sachverhalt durch mehrere Mitbeschuldigte/Einzelvorwürfe verschachtelt — vor
Erfassung unbedingt im vollständigen PDF/HTML verifizieren.

## Aargau (Obergericht, Signatur `SST.*`)

1. ✅ **[ERFASST - ID 334]** https://entscheidsuche.ch/docs/AG_Gerichte/AG_OG_008_SST-2022-272_2023-03-21.pdf — gewerbsmässiger betrügerischer Missbrauch DVA (12 Trickdiebstähle Kredit-/Debitkarten, ~CHF 51'400 + EUR 2'000 / Deliktssumme CHF 55'000), Vorinstanz Bezirksgericht Baden 10.06.2022, 54 Monate FS unbedingt (4½ Jahre), Landesverweisung 15J
2. ✅ **[ERFASST - ID 335]** https://entscheidsuche.ch/docs/AG_Gerichte/AG_OG_008_SST-2023-42_2023-11-15.pdf — gewerbsmässiger Betrug + mehrfache Urkundenfälschung (Score 3), Vorinstanz Bezirksgericht Aarau 21.11.2022, 12 Monate FS bedingt, Verbindungsbusse CHF 2'000, Landesverweisung 5J (SIS angeordnet)
3. ✅ **[ERFASST - ID 336]** https://entscheidsuche.ch/docs/AG_Gerichte/AG_OG_008_SST-2023-43_2023-11-15.pdf — Mittäterin desselben Betrugskomplexes, gewerbsmässiger Betrug + mehrfache Urkundenfälschung (Score 3), Vorinstanz Bezirksgericht Aarau 21.11.2022, 11 Monate FS bedingt, Verbindungsbusse CHF 2'000, Landesverweisung 5J (SIS angeordnet)
4. ✅ **[ERFASST - ID 337]** https://entscheidsuche.ch/docs/AG_Gerichte/AG_OG_008_SST-2022-279_2023-10-31.pdf — gewerbsmässiger Betrug (Romance Scam, Deliktssumme CHF 130'000) + mehrfacher Verweisungsbruch (Score 2), Vorinstanz Bezirksgericht Aarau 18.08.2022, 42 Monate FS unbedingt (3½ Jahre), Rückfall-Landesverweisung 20J

## Genf (Cour de Justice, `GE_CJ_009`)

1. ✅ **[ERFASST - ID 338]** https://entscheidsuche.ch/docs/GE_Gerichte/GE_CJ_009_P-13930-2020_2024-04-04.pdf — COVID-19-Kredite: Betrug (CHF 15'000) + mehrfache Veruntreuung + Urkundenfälschung + AHVG-Widerhandlung (Score 6), Vorinstanz Tribunal de police 11.07.2023, 6 Monate FS unbedingt
2. ✅ **[ERFASST - ID 339]** https://entscheidsuche.ch/docs/GE_Gerichte/GE_CJ_009_P-12558-2021_2022-11-14.pdf — gewerbsmässiger betrügerischer Missbrauch DVA (Art. 147 Abs. 2 StGB, ~CHF 70'000) + gewerbs-/bandenmässiger Diebstahl (21x Zahlungskarten an Bankomaten) + Veruntreuung (Score 5), Vorinstanz Tribunal correctionnel 10.03.2022, 48 Monate FS unbedingt (4 Jahre), Landesverweisung 8J, Berufung vollumfänglich abgewiesen
3. ✅ **[ERFASST - ID 340]** https://entscheidsuche.ch/docs/GE_Gerichte/GE_CJ_009_P-1438-2020_2021-12-08.pdf — Veruntreuung (Art. 138 Ziff. 1 Abs. 2 StGB, Kundengelder Reisebüro, CHF 6'784), Vorinstanz Tribunal de police 20.05.2021, Geldstrafe 60 TS à CHF 30.- bedingt (Probezeit 3J), Berufung (Geltendmachung Notstand Art. 17 StGB wegen häuslicher Gewalt) vollumfänglich abgewiesen
4. ✅ **[ERFASST - ID 341]** https://entscheidsuche.ch/docs/GE_Gerichte/GE_CJ_009_P-25348-2018_2023-07-06.pdf — mehrfacher Betrug (Audiosystem CHF 5'385 + Waren CHF 618, Deliktssumme CHF 6'003) + arglistige Vermögensschädigung (Art. 151 StGB, Renovierungsauftrag über CHF 325'495 Schaden, Score 1), Vorinstanz Tribunal de police 11.08.2022, 12 Monate FS unbedingt, ambulante Massnahme Art. 63 StGB, verminderte Schuldfähigkeit (mittelschwer, Mythomanie); Cour de Justice bestätigt 12 M. FS, schiebt Vollzug nach Art. 63 Abs. 2 StGB zugunsten der ambulanten Massnahme auf
5. ❌ **[AUSGESCHLOSSEN - Raubdelikt (Art. 140 StGB) / Gewaltdelikt; Vorinstanz hatte Krypto-Teil eingestellt, zweitinstanzlich abgeändert]** https://entscheidsuche.ch/docs/GE_Gerichte/GE_CJ_009_P-16901-2021_2023-10-25.pdf — Raub (Opfer an Auto mitgeschleift) + Gefährdung des Lebens (Art. 129 StGB) + gewerbsmässiger Betrug, gehört in GewaltdeliktUrteil; zudem zweitinstanzliche Neubeurteilung nach vorinstanzlicher Verfahrenseinstellung für Krypto-Komplex
6. ❌ **[AUSGESCHLOSSEN - Strafe zu über 70% aus Widerrufen früherer Strafen gebildet; Deliktssumme unbeziffert]** https://entscheidsuche.ch/docs/GE_Gerichte/GE_CJ_009_P-6148-2020_2021-01-18.pdf — Vol + Tentative de vol + Sachbeschädigung (Metallarmband und Badge aus Auto; Autoscheibe eingeschlagen), vorinstanzliche Gesamtstrafe von 24 Monaten FS bestand zu über 17 Monaten aus zwei Widerrufen früherer Strafen (101 Tage Reststrafe + 18 Monate bedingter Strafrest); Deliktssumme unbeziffert

## Bern (Obergericht, Strafkammer)

1. ✅ **[ERFASST - ID 342]** https://entscheidsuche.ch/docs/BE_ZivilStraf/BE_OG_005_SK-2022-454_2022-12-22.pdf — gewerbsmässiger Diebstahl (9 Einbruchdiebstähle Hotels/Chalets, Deliktssumme CHF 155'103.- [effektive Beute CHF 23'103.-]), mehrfache Sachbeschädigung, mehrfacher Hausfriedensbruch, AuG (Score 6); Vorinstanz Regionalgericht Oberland 17.03.2022, 35 Monate FS unbedingt, Landesverweisung 7J; OG bestätigt Urteil vollumfänglich
2. ✅ **[ERFASST - ID 343]** https://entscheidsuche.ch/docs/BE_ZivilStraf/BE_OG_005_SK-2023-169_2024-05-28.pdf — gewerbsmässiger Betrug (Raumdüfte/Diffuser-Verkauf an 77-jährige Rentnerin mit fiktiven Weiterverkäufen, Deliktssumme CHF 128'000.-); Vorinstanz Regionalgericht Bern-Mittelland 15.11.2022, 23.5 Monate FS bedingt (DB: 24 M.), Landesverweisung 5J; OG bestätigt Schuldspruch und Freiheitsstrafe vollumfänglich, hebt Landesverweisung gestützt auf Art. 66a Abs. 2 StGB (Härtefall) auf
3. ✅ **[ERFASST - ID 344]** https://entscheidsuche.ch/docs/BE_ZivilStraf/BE_OG_005_SK-2023-23_2023-11-16.pdf — mehrfache qualifizierte Veruntreuung (CHF 2'555'000.- + EUR 50'000.- / CHF 2'609'000.-) durch leitenden Bankangestellten zu Lasten betagter Kundin + mehrfache WG-Widerhandlung (Score 2); Vorinstanz Kantonales Wirtschaftsstrafgericht Bern 10.11.2022, 66 Monate FS unbedingt + 30 TS Geldstrafe bedingt (1 M. Geständnisrabatt berücksichtigt); OG bestätigt Schuldsprüche, erhöht FS auf StA-Anschlussberufung hin auf 74 Monate und streicht Geständnisrabatt wegen Widerrufs im Berufungsverfahren — Vorinstanz-Werte (66 M. FS) in DB erfasst
4. ❌ **[AUSGESCHLOSSEN - Teilfreispruch im Hauptdelikt durch OG; reine Zusatzstrafe nach Art. 49 Abs. 2 StGB zu früherem Zürcher Urteil; 28 verschachtelte Anklagekomplexe]** https://entscheidsuche.ch/docs/BE_ZivilStraf/BE_OG_005_SK-2018-133_2019-03-28.pdf — OG sprach vom Vorwurf des gewerbsmässigen Betrugs z.N. von F. (CHF 44'000.-) frei; Strafe bei Vorinstanz (42 M.) und OG (50 M.) war eine Zusatzstrafe zu Obergericht Zürich vom 15.08.2016
5. ✅ **[ERFASST - ID 345]** https://entscheidsuche.ch/docs/BE_ZivilStraf/BE_OG_005_SK-2020-49_2021-07-13.pdf — gewerbsmässiger Arbeitslosenversicherungsbetrug (Deliktssumme CHF 67'868.60 über 21 Monate) + Nichtabgabe von Kontrollschildern (Score 1); Vorinstanz Regionalgericht Emmental-Oberaargau 15.10.2019, 10 Monate FS bedingt + 25 TS Geldstrafe unbedingt, Landesverweisung 5J; OG bestätigt Schuldspruch und Landesverweisung, wandelt Sanktion über lex mitior (aArt. 34 aStGB) in Geldstrafe von 315 TS (25 TS unbed. / 290 TS bed.) um — Vorinstanz-Werte (10 M. FS bedingt) in DB erfasst

## Basel-Stadt (Appellationsgericht)

1. https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2013-105_2014-01-28.html — gewerbsmässiger Diebstahl, mehrfache Sachbeschädigung, mehrfacher Hausfriedensbruch, mehrfache rechtswidrige Einreise — erstinstanzliches Urteil vollständig bestätigt
2. https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2013-116_2015-06-19.html — gewerbsmässiger Betrug + mehrfache/versuchte ungetreue Geschäftsbesorgung (Bereicherungsabsicht), Schuldpunkt bestätigt, 3 Jahre FS (2 bedingt), BGer 6B_1045/2015 bestätigt
3. https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2024-12_2024-12-18.html — gewerbsmässiger Betrug + mehrfache Urkundenfälschung (mehrfache Veruntreuung bereits unangefochten rechtskräftig), Berufung abgewiesen, 3 Jahre 3 Monate FS, BGer 6B_360/2025 rechtskräftig
4. ⚠️ https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2013-117_2014-09-09.html — versuchter Raub, bandenmässiger Diebstahl, gewerbsmässiger Betrug, versuchter Missbrauch DVA u.a. — sehr komplex (Raub kein Modell-Hauptdelikt), Ausgang vs. Vorinstanz vor Erfassung genau prüfen
5. ⚠️ https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2024-108_2025-11-12.html — gewerbsmässiger Diebstahl (Rückfall), Volltext vor Dispositiv bei 100'000 Zeichen abgeschnitten
6. ⚠️ https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2023-49_2025-06-11.html — mehrfacher/versuchter Betrug + Missbrauch DVA + Kreditkartenmissbrauch, viele einzelne Anklageziffern (teils Freispruch, teils rechtskräftig) — Deliktssumme nur mit sorgfältiger Lektüre isolierbar

Ausgeschlossen (geprüft, ungeeignet): SB-2022-54 (Vorinstanz sprach frei, nur Privatklägerschaft legte Berufung ein → OG verurteilte selbst — kein vorinstanzlicher Schuldspruch); SB-2014-1 (OG änderte ab, mehrere Freisprüche, zu verschachtelt).

## Basel-Landschaft (Kantonsgericht)

1. https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-2012-256_2013-02-26.html — mehrfacher, teilweise versuchter banden-/gewerbsmässiger Diebstahl, Sachbeschädigung, mehrfacher Hausfriedensbruch, vollumfänglich bestätigt (auch Anschlussberufung StA abgewiesen), 2 Jahre FS unbedingt
2. https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-15-237_2016-02-23.html — gewerbsmässiger Diebstahl, mehrfache Sachbeschädigung, mehrfacher Hausfriedensbruch, Fälschen von Ausweisen, bestätigt, 3 Jahre 6 Monate FS
3. https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-2021-137_2021-11-30.html — gewerbsmässiger (versuchter) Diebstahl, mehrfacher Hausfriedensbruch, vollumfänglich bestätigt, 15 Monate FS, Landesverweisung 7J
4. ⚠️ https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-18-350_2019-07-03.html — gewerbs-/bandenmässiger Diebstahl, Hausfriedensbruch, Sachbeschädigung, "teilweise Gutheissung" — prüfen ob nur Strafmass oder auch Qualifikation geändert wurde
5. ⚠️ https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-14-4_2014-06-02.html — StA-Berufung teilweise gutgeheissen (mehr Schuldsprüche als Vorinstanz); vorinstanzlicher (engerer) Schuldspruch ggf. isolierbar, aber komplex

## Freiburg (Cour d'appel pénal, `FR_TC_006`)

1. https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2025-90_2026-02-25.pdf — Vol par métier et en bande + dommages à la propriété (17x) + Hausfriedensbruch, Berufung vollständig abgewiesen, Vorinstanz Tribunal pénal de la Sarine 13.03.2025, 36 Monate FS (6 unbed./30 bed.)
2. https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2021-162_2023-04-26.pdf — Vol par métier + Sachbeschädigung + Hausfriedensbruch, Berufung vollständig abgewiesen, Vorinstanz Tribunal pénal du Lac 24.06.2021
3. https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2018-103_2019-04-02.pdf — Vol en bande (mehrere Einzelfälle), Berufung teilweise gutgeheissen (Freispruch nur bei einem separaten Einzelfall, Grundqualifikation für übrige Fälle bestätigt)
4. ⚠️ https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2016-126_2017-02-15.pdf — Vol par métier + Sachbeschädigung, sehr viele Einzelfälle (1.1–5.14) über mehrere Jahre — eventuell zu verschachtelt
5. ⚠️ https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2021-79_2023-01-13.pdf — Vol en bande et par métier, Berufung teilweise gutgeheissen, unklar ob "par métier"-Qualifikation dabei wegfiel
6. ⚠️ https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2016-59_2017-05-05.pdf und /FR_TC_006_501-2018-40_2021-11-30.pdf — Escroquerie par métier, Volltext bei 100'000 Zeichen abgeschnitten, Dispositiv nicht sichtbar, evtl. dieselbe Sache in zwei Verfahrensstadien
7. ⚠️ https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2018-120_2019-06-11.pdf — Gestion déloyale (Art. 158), Volltext abgeschnitten
8. ⚠️ https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2019-122_2020-10-08.pdf und /FR_TC_006_501-2015-43_2015-11-30.pdf — Abus de confiance/gestion déloyale in Konkurs-/Mehrparteienkontext mit Bundesgerichts-Rückweisungen, komplex

## Graubünden (Kantonsgericht)

1. https://entscheidsuche.ch/docs/GR_Gerichte/GR_KG_004_SK1-2021-55_2022-10-28.pdf — mehrfache Urkundenfälschung + gewerbsmässiger Betrug (Art. 146 Abs. 2) gegen Arbeitgeber/Sozialversicherung, Gesamtschaden ~CHF 70'795; Vorinstanz Regionalgericht Imboden, FS 17 Monate bedingt; OG bestätigt Qualifikation und Strafe identisch
2. https://entscheidsuche.ch/docs/GR_Gerichte/GR_KG_004_SK1-2020-49_2022-06-15.pdf — gewerbsmässiger Betrug (Art. 146 Abs. 2) gegen Arbeitgeber + Landesverweisung; Vorinstanz Regionalgericht Plessur, Geldstrafe 360 TS; Berufung betraf nur Strafhöhe (OG reduziert leicht auf 330 TS), Schuldspruch unverändert bestätigt
3. ⚠️ https://entscheidsuche.ch/docs/GR_Gerichte/GR_KG_004_SK1-2020-47_2021-07-14.pdf — mehrere Mitbeschuldigte, bereits einmal beim Bundesgericht (Rückweisung), gewerbsmässiger Betrug — nur mit sorgfältiger Auswahl einer Person und Prüfung des aktuellen Verfahrensstands verwendbar

Ausgeschlossen: SK1-2019-47 (untypischer, stark umstrittener Sachverhalt, Hauptdelikt-Qualifikation nicht eindeutig).

## Zug (Obergericht)

1. https://entscheidsuche.ch/docs/ZG_Obergericht/ZG_OG_999_S-2021-18_2022-04-06.pdf — gewerbsmässiger Anlagebetrug (Aktien-Schwindel, CHF 1.3 Mio, 29 Geschädigte); Vorinstanz Strafgericht Zug, FS 27 Monate teilbedingt; Berufungen von Beschuldigtem und StA beide erfolglos, OG bestätigt exakt 27 Monate
2. https://entscheidsuche.ch/docs/ZG_Obergericht/ZG_OG_002_S-2023-10_2023-08-29.pdf — mehrfache qualifizierte ungetreue Geschäftsbesorgung (Vermögensverwaltung); Vorinstanz Strafgericht Zug, FS 23 Monate bedingt; Kern-Schuldspruch seit 2021 unverändert bestätigt (⚠️ 2. Rechtsgang nach Teil-Rückweisung — prüfen, ob nur Zivil-/Nebenpunkte betroffen waren)

## Schwyz (Kantonsgericht)

1. https://entscheidsuche.ch/docs/SZ_Gerichte/SZ_KG_003_STK-2024-45_2025-11-17.pdf — Veruntreuung (Einzeltat) + gewerbsmässiger betrügerischer Missbrauch DVA (Art. 147, 2008–2017, seltener Hauptdelikt-Typ), vom gewerbsmässigen Betrug freigesprochen; Vorinstanz Strafgericht Schwyz, FS 12 Monate bedingt; Berufung betraf nur noch Zivilforderungen (per Vergleich erledigt) — Schuldspruch/Strafe unverändert rechtskräftig
2. ⚠️ https://entscheidsuche.ch/docs/SZ_Gerichte/SZ_KG_003_STK-2024-11_2025-09-23.pdf — Betrug (Vorinstanz verneinte gewerbsmässig), Deliktsbetrag Darlehen CHF 242'500 abzgl. CHF 211'000 zurückbezahlt; Vorinstanz FS 4 Monate bedingt, im Berufungsverfahren Hinweis auf FS 42 Monate (vermutlich Gesamtstrafenbildung mit anderem Verfahren) — Ausgang zu unklar, vor Erfassung Volltext genau studieren

Ausgeschlossen: STK-2022-11 (Vorinstanz sprach frei, OG bestätigt Freispruch — keine vorinstanzliche Verurteilung).

## Solothurn (Obergericht, Signatur `STBER.*`)

Trotz guter Erfahrung bei Betm-Fällen hier keine sauber verifizierbaren Treffer: Vermögensdelikt-Berufungsurteile in SO sind überwiegend sehr lang (Volltext beim Dispositiv bei 100'000 Zeichen abgeschnitten) oder mehrfachtäterschaftlich verschachtelt.

- ⚠️ https://entscheidsuche.ch/docs/SO_OG/SO_OG_006_STBER-2019-17_2019-06-13.html — gewerbsmässiger Diebstahl, nur Beschuldigter hat Berufung erhoben (keine Anschlussberufung StA, reformatio-in-peius-Schutz), Volltext vor Dispositiv abgeschnitten — Ausgang im PDF verifizieren
- ⚠️ https://entscheidsuche.ch/docs/SO_OG/SO_OG_006_STBER-2022-76_2023-07-13.html — ungetreue Geschäftsbesorgung (Bereicherungsabsicht), Deliktssumme CHF 252'906.82 genannt, Volltext ebenfalls vor Dispositiv abgeschnitten

Ausgeschlossen: STBER-2018-52 (OG sprach vom Hauptvorwurf ungetreue Geschäftsbesorgung frei); STBER-2023-79 (BGer 6B_653/2024 hat Entscheid aufgehoben).

## Waadt (Cour d'appel pénale, `VD_TC_003`)

1. https://entscheidsuche.ch/docs/VD_FindInfo/VD_TC_003_PE24-026120_2026-04-20.pdf — Vol + Versuch, Berufung vollständig abgewiesen, Vorinstanz Tribunal de police de Lausanne 15.07.2025
2. ⚠️ https://entscheidsuche.ch/docs/VD_FindInfo/VD_TC_003_PE12-010581_2018-08-20.pdf — Escroquerie par métier, komplexer Mehrfachtäter mit mehreren widerrufenen Vorstrafen aus GE/NE, Berufung nur "très partiellement admis" (Kern bestätigt) — nur mit sorgfältiger Lektüre

## Neuenburg (Cour pénale, `NE_TC_009`)

1. https://entscheidsuche.ch/docs/NE_Omni/NE_TC_009_CPEN-2021-77_2022-05-15.html — Einbruchdiebstahl, Berufung abgewiesen, Vorinstanz Tribunal de police du Littoral et du Val-de-Travers 28.07.2021, 10 Monate FS unbedingt (teilweise Zusatzstrafe)

## Tessin (Corte di appello e di revisione penale, `TI_CARP_001`)

1. ⚠️ https://entscheidsuche.ch/docs/TI_Gerichte/TI_CARP_001_17-2021-22_2022-02-17.html — Truffa + amministrazione infedele aggravata u.a., vom Bundesgericht in 6B_409/2022 bestätigt; viele Nebenvorwürfe (Falschbeurkundung, LADI-Widerhandlung, Steuerbetrug) — vor Erfassung prüfen, ob Hauptdelikt/Score sauber isolierbar
2. ⚠️ https://entscheidsuche.ch/docs/TI_Gerichte/TI_CARP_001_17-2021-219_2021-12-21.html — Truffe Covid-Kredit (Bilanzfälschung, CHF 1'060'000 Gesamtschaden), erstinstanzlich für eine Partei vollumfänglich, für die zweite fast vollumfänglich bestätigt; zwei Mitbeschuldigte, mehrere Einzeltaten — Sachverhalt vor Erfassung entflechten

## Uri (Obergericht Strafabteilung, `UR_OG_003`)

1. ⚠️ https://entscheidsuche.ch/docs/UR_Gerichte/UR_OG_003_2018-OG-S-15-12_2018-07-31.pdf — Gewerbs-/bandenmässiger Diebstahl, Sachbeschädigung, Hausfriedensbruch (Art. 139/144/186 StGB); nur Leitentscheid-Auszug verfügbar ("teilweise Gutheissung der Berufung") — ob dies die Hauptdelikt-Qualifikation betrifft, muss im Volltext geprüft werden
2. ⚠️ https://entscheidsuche.ch/docs/UR_Gerichte/UR_OG_003_2025-OG-S-25-4_2025-05-14.pdf und …-25-5 — nur Abschreibungsverfügungen wegen Berufungsrückzugs; das zugrundeliegende erstinstanzliche Urteil (Landgerichtspräsidium I Uri, PSA 24 28/29 vom 14.01.2025, Diebstahl/Sachbeschädigung/Hausfriedensbruch/rechtswidrige Einreise) ist dadurch rechtskräftig, aber nicht separat online auffindbar — Hinweis auf existierenden, aber nicht direkt erfassbaren Fall

## 0 brauchbare Treffer

- **Jura**: sehr geringes Fallvolumen im Index (nur 465 Dokumente total); einziger Treffer (`JU_TC_003_CP-2021-48`) betrifft Wirtschaftsdelikte ausserhalb des Zielkatalogs (banqueroute frauduleuse/gestion fautive) und ist zu verschachtelt/abgeschnitten.
- **Schaffhausen, Luzern**: entscheidsuche.ch enthält praktisch keine rezenten, im Volltext durchsuchbaren Vermögensdelikt-Berufungsurteile; `list_hierarchy` bestätigt, dass diese Kantone unter den ergiebigsten Hierarchie-IDs für "Betrug" gar nicht auftauchen (im Gegensatz zu GR/BE). SH liefert nur branchenfremde Verwaltungsgerichts-Leitentscheide (Steuer-, Submissions-, Sozialversicherungsrecht).
- **St. Gallen, Thurgau, Glarus, Obwalden, Appenzell Innerrhoden, Appenzell Ausserrhoden**: entscheidsuche.ch indexiert für diese Kantone primär kuratierte prozessrechtliche Leitentscheide (Ausstand, Akteneinsicht, Nichtanhandnahme) statt des vollständigen Bestands ordentlicher Berufungsurteile mit ausformuliertem Dispositiv — keine materiellen Vermögensdelikt-Treffer mit Strafzumessung gefunden.
- **Wallis**: einzige Gerichts-Hierarchie bündelt alle Kammern ungetrennt; gefundene Cour-pénale-II-Fälle waren entweder gewaltdeliktdominiert (Raub) oder Verfahren mit sehr vielen Privatklägern — keiner erfüllte das Kriterium "überschaubarer Sachverhalt" mit vertretbarem Rechercheaufwand.
- **Nidwalden**: einziger Diebstahl-Treffer betraf primär eine Körperverletzung (Diebstahl nur Nebendelikt); einziger "Wirtschaftsdelikte"-Treffer ist ein noch beim Bundesgericht hängiges Verfahren nach Rückweisung (nicht rechtskräftig, mehrere Mitbeschuldigte).

## Hinweis zur Recherche

`opencaselaw`-Tools waren während Teilen dieser Recherche durchgehend fehlerhaft
("Invalid request parameters" auch bei minimalen Queries) — die Recherche lief in diesen
Fällen ausschliesslich über `mcp__plugin_bettercallclaude_entscheidsuche__*`.
