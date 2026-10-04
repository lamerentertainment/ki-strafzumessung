# Vermögensdelikt-Präjudizien-Recherche: Kandidatenliste (entscheidsuche.ch)

Gesamtschweizerische Recherche nach kantonalen Vermögensdelikt-Präjudizien für
`database.models.Urteil`. Die DB enthält aktuell **288 Fälle** (ursprünglich 258 ausschliesslich
aus dem Kanton Zürich, ergänzt um kantonale Entscheide aus AG, GE, BE, BS, BL, FR, GR, ZG, SO und SZ) — gesucht sind Kandidaten aus
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

**Ausnahme 1 (User-Vorgabe):** Erzwingt ein Teilfreispruch innerhalb des Hauptdelikts eine
komplette Neufestsetzung der Strafe durch die Rechtsmittelinstanz (kein unveränderter
vorinstanzlicher Wert mehr vorhanden — sonst Ausschlussgrund oben), kann der Fall
ausnahmsweise anhand der Werte der Rechtsmittelinstanz selbst erfasst werden (`gericht`/
`urteilsdatum` = Rechtsmittelinstanz), **sofern** deren Neubeurteilung vom
Verschlechterungsverbot (Art. 391 Abs. 2 StPO) unberührt blieb — d.h. nur der Beschuldigte
(nicht auch die Staatsanwaltschaft) hatte Berufung erhoben, sodass die neue, mildere Strafe
eine eigenständige, nicht durch das Verbot nach unten „gedeckelte" Strafzumessung darstellt.
Hat hingegen auch die Staatsanwaltschaft (Anschluss-)Berufung erhoben oder wurde die Strafe
gerade wegen des Verschlechterungsverbots künstlich auf dem alten (zu hohen) Niveau belassen,
bleibt der Fall ungeeignet. Beispiel: `501 2018 103` (ID 356).

**Ausnahme 2 (User-Vorgabe):** Spiegelbildlich gilt: Hat die Vorinstanz das Hauptdelikt
selbst **vollständig freigesprochen** und wird dieser Freispruch erst im Rechtsmittelverfahren
auf Berufung der **Privatklägerschaft** (oder der Staatsanwaltschaft) hin in einen Schuldspruch
umgewandelt, existiert für das Hauptdelikt gar kein vorinstanzlicher Wert, auf den das
Vorinstanz-Prinzip überhaupt angewendet werden könnte. In diesem Fall ist die Verurteilung der
Rechtsmittelinstanz (die als einzige Instanz mit voller Kognition materiell über das Hauptdelikt
entschieden hat) als alleinige Quelle zu erfassen (`gericht`/`urteilsdatum` = Rechtsmittelinstanz)
— das Verschlechterungsverbot greift hier von vornherein nicht zu Gunsten des Beschuldigten, weil
die Verschärfung nicht auf einem eigenen Rechtsmittel des Beschuldigten beruht, sondern auf dem
Rechtsmittel der gegnerischen Partei. Andere, bereits vorinstanzlich rechtskräftig gewordene
Nebendelikte (weil unangefochten) fliessen normal in den `nebenverurteilungsscore` ein. Beispiel:
`STK 2024 11` (ID 360) — Vorinstanz sprach vom gewerbsmässigen Betrug (Hauptvorwurf) frei,
Privatkläger legte dagegen erfolgreich Berufung ein.

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

1. ✅ **[ERFASST - ID 346]** https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2013-105_2014-01-28.html — gewerbsmässiger Diebstahl (Einbrüche in Restaurants/Geschäft, Entwendung Spielautomat, Deliktssumme CHF 11'369.-), Sachbeschädigung, Hausfriedensbruch, AuG (Score 6); Vorinstanz Strafgericht Basel-Stadt 21.08.2013, 14 Monate FS unbedingt; Appellationsgericht weist Berufung vollumfänglich ab
2. ✅ **[ERFASST - ID 347]** https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2013-116_2015-06-19.html — gewerbsmässiger Betrug + ungetreue Geschäftsbesorgung (Abzweigung von Firmengeldern durch Geschäftsführer, Deliktssumme CHF 611'243.-, Score 2, Besonderheit: Versuch); Vorinstanz Strafgericht Basel-Stadt 05.09.2013, 36 Monate FS teilbedingt (12 M. unbed., 24 M. bed.); Appellationsgericht bestätigt Schuld- und Strafpunkt vollumfänglich (reduziert Probezeit von 5 auf 2 Jahre), BGer 6B_1045/2015 weist Beschwerde ab
3. ✅ **[ERFASST - ID 348]** https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2024-12_2024-12-18.html — gewerbsmässiger Betrug + Urkundenfälschung (Immobilienvermittlungs-Betrug, Deliktssumme CHF 435'000.-, Nebendelikte Veruntreuung und SVG unangefochten rechtskräftig, Score 9); Vorinstanz Strafgericht Basel-Stadt 21.09.2022, 39 Monate FS unbedingt + 30 TS Geldstrafe; Appellationsgericht weist Berufung vollumfänglich ab, BGer 6B_360/2025 weist Beschwerde ab
4. ❌ **[AUSGESCHLOSSEN - Raubdelikt (Art. 140 StGB) / Gewaltdelikt; Einsatzstrafe stützt auf versuchten Raub]** https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2013-117_2014-09-09.html — Vorinstanz und Appellationsgericht bildeten die Einsatzstrafe auf dem versuchten Raub (Art. 140 StGB); Raub ist ein Gewaltdelikt und kein Hauptdelikt im Katalog von `Urteil` (gehört in GewaltdeliktUrteil); zudem komplexe Beteiligungsverhältnisse mit Mitbeschuldigten
5. ✅ **[ERFASST - ID 349]** https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2024-108_2025-11-12.html — gewerbsmässiger Diebstahl (13 Ladendiebstähle hochwertiger Waren/Parfüms/Geräte zur Drogenfinanzierung, Deliktssumme CHF 7'424.-, Score 8); Vorinstanz Strafgericht Basel-Stadt 10.04.2024, 23 Monate FS unbedingt + 15 TS Geldstrafe; Appellationsgericht weist Berufung im Hauptpunkt vollumfänglich ab und bestätigt 23 Monate FS unbedingt (passt TS-Höhe an)
6. ❌ **[AUSGESCHLOSSEN - Hauptdelikt Check- und Kreditkartenmissbrauch (Art. 148 StGB) nicht im Modell-Katalog; Einsatzstrafe stützt auf Art. 148 StGB; 11 Teilfreisprüche]** https://entscheidsuche.ch/docs/BS_APG/BS_APG_001_SB-2023-49_2025-06-11.html — Einsatzstrafe wurde explizit für gewerbsmässigen Check- und Kreditkartenmissbrauch (Art. 148 StGB) festgesetzt; Art. 148 StGB ist kein zulässiges Hauptdelikt im Modell von `database.models.Urteil`; zudem 11 Freisprüche für Einzelpunkte

Ausgeschlossen (geprüft, ungeeignet): SB-2022-54 (Vorinstanz sprach frei, nur Privatklägerschaft legte Berufung ein → OG verurteilte selbst — kein vorinstanzlicher Schuldspruch); SB-2014-1 (OG änderte ab, mehrere Freisprüche, zu verschachtelt).

## Basel-Landschaft (Kantonsgericht)

1. ❌ **[AUSGESCHLOSSEN - Deliktssumme unbeziffert / nicht quantifizierbar]** https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-2012-256_2013-02-26.html — mehrfacher, teilweise versuchter bandenmässiger Diebstahl (Muttenz/Basel), Sachbeschädigung, Hausfriedensbruch (Freispruch von Gewerbsmässigkeit); Deliktsbeute bestand aus EUR 30.- Bargeld und nicht im Frankenwert bezifferten "diversen Gegenständen", die den Opfern vollständig zurückgegeben wurden; Deliktssumme laut Gericht "eher gering ausgefallen" und im Urteil unbeziffert
2. ✅ **[ERFASST - ID 350]** https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-15-237_2016-02-23.html — gewerbsmässiger Diebstahl (Serie von Einbrüchen in Wohnhäuser, Deliktssumme rund CHF 20'000.-), Sachbeschädigung, Hausfriedensbruch, Ausweisfälschung, AuG (Score 8); Vorinstanz Strafgericht Basel-Landschaft 21.09.2015, 42 Monate FS unbedingt; Kantonsgericht weist Berufung vollumfänglich ab
3. ❌ **[AUSGESCHLOSSEN - Reines Versuchsdelikt ohne erzielte Beute / Deliktssumme CHF 0.-]** https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-2021-137_2021-11-30.html — 4 Einbruchsversuche an einem Nachmittag ohne jede Beute ("wobei er indessen keinerlei Beute zu erzielen vermochte"); Deliktssumme CHF 0.- ist im Modell nicht abbildbar
4. ✅ **[ERFASST - ID 351]** https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-18-350_2019-07-03.html — gewerbs- und teilweise bandenmässiger Diebstahl (15 Einbruchdiebstähle in Wohnhäuser über 10 Monate, Deliktssumme CHF 69'719.40), mehrfache Sachbeschädigung, Hausfriedensbruch (Score 3, Besonderheit: Versuch); Vorinstanz Strafgericht Basel-Landschaft 27.09.2018, 45 Monate FS unbedingt, Landesverweisung 10J; Kantonsgericht bestätigt Schuldsprüche und Landesverweisung vollumfänglich, reduziert FS auf 36 Monate (Vorinstanz-Werte in DB erfasst)
5. ✅ **[ERFASST - ID 357]** https://entscheidsuche.ch/docs/BL_KG/BL_KG_004_460-14-4_2014-06-02.html — gewerbsmässiger Diebstahl (Wohnwagen-Einbrüche als "Kriminaltouristin" aus Frankreich, Deliktssumme über CHF 221'900.-) + geringfügige Sachbeschädigung + Ausweisfälschung + mehrfache Kontrollschilder-Delikte (Score 6); Vorinstanz Strafgericht Basel-Landschaft 08.01.2014, 24 Monate FS bedingt, Busse CHF 150.-; nur die Staatsanwaltschaft erhob Berufung (StA-Berufung teilweise gutgeheissen: OG spricht zusätzlich einen vorinstanzlich freigesprochenen Diebstahl/Sachbeschädigung/Hausfriedensbruch schuldig und erhöht die Strafe auf 30 Monate) — da dies gerade die im CLAUDE.md-Abschnitt 3 vorgesehene Konstellation ist (OG wird auf StA-Berufung hin strenger), werden die unveränderten vorinstanzlichen Werte erfasst

## Freiburg (Cour d'appel pénal, `FR_TC_006`)

1. ✅ **[ERFASST - ID 352]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2025-90_2026-02-25.pdf — bandenmässiger und gewerbsmässiger Diebstahl (18 Einbruchdiebstähle in FR/VD, Deliktssumme CHF 80'000.-) + Sachbeschädigung + mehrfacher, teils versuchter Hausfriedensbruch (Score 4, Besonderheit: Versuch); Vorinstanz Tribunal pénal de la Sarine 13.03.2025, 36 Monate FS (6 unbed./30 bed., Probezeit 5J), Landesverweisung 5J; Cour d'appel pénal weist Berufung (Strafhöhe + Härtefall-Landesverweisung) vollumfänglich ab
2. ✅ **[ERFASST - ID 354]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2021-162_2023-04-26.pdf — gewerbsmässiger Diebstahl, dreimal begangen (Baggerdiebstähle Kerzers/St-Saphorin/Lausanne als Hintermann/Organisator, Deliktssumme CHF 107'000.-) + Sachbeschädigung + Hausfriedensbruch + Irreführung der Rechtspflege + Verletzung der Buchführungspflicht (Score 6); Vorinstanz Tribunal pénal de l'arrondissement du Lac 24.06.2021, 17 Monate FS bedingt (Probezeit 5J); Cour d'appel pénal weist Berufung (voller Freispruchsantrag) vollumfänglich ab
3. ✅ **[ERFASST - ID 356, Ausnahme: Werte der Berufungsinstanz erfasst]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2018-103_2019-04-02.pdf — bandenmässiger Diebstahl (4 Fälle nach Teilfreispruch, Deliktssumme CHF 3'192.-) + versuchter bandenmässiger Diebstahl + Sachbeschädigung + (teils versuchter) Hausfriedensbruch + AuG-Widerhandlungen (Score 5); Vorinstanz Juge de police de l'arrondissement du Lac 21.12.2017 verurteilte ursprünglich für 5 Fälle zu 8 Monaten FS bedingt + Busse CHF 2'000; Kantonsgericht Freiburg spricht am 2.4.2019 von einem der 5 Fälle mangels Beweisen frei und muss die Strafe deshalb neu festsetzen — da nur der Beschuldigte (nicht die StA) Berufung erhoben hatte, war das Kantonsgericht dabei nur nach oben, nicht nach unten durch das Verschlechterungsverbot begrenzt; die neue, mildere Strafe (7 Monate FS bedingt + Busse CHF 1'500) wurde daher ausnahmsweise als eigenständige, vom Verschlechterungsverbot unberührte Strafzumessung anstelle der vorinstanzlichen Werte erfasst (`gericht`/`urteilsdatum` = Kantonsgericht Freiburg, 2.4.2019)
4. ✅ **[ERFASST - ID 362]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2016-126_2017-02-15.pdf — gewerbsmässiger, teils versuchter Diebstahl (28 Einbruchdiebstähle in FR/BE/GE/TI/ZH zwischen 2007–2011, aggregierte Deliktssumme rund CHF 100'000.-) + Sachbeschädigung + Hausfriedensbruch (teils versucht) + AuG-Widerhandlung + Gebrauchsdiebstahl an Motorfahrzeug (Score 6, Besonderheit: Versuch); Vorinstanz Tribunal pénal de l'arrondissement de la Gruyère 21.04.2016, 44 Monate FS unbedingt; Cour d'appel pénal heisst die Berufung nur in Nebenpunkten gut (3 weitere, separat angeklagte Diebstahlsvorwürfe mangels Beweisen freigesprochen, einzelne verjährte/mangels gültigem Strafantrag klassierte Nebendelikte), bestätigt aber die Grundqualifikation für alle 28 Fälle sowie die Freiheitsstrafe von 44 Monaten unverändert — trotz der grossen Fallzahl war eine klare aggregierte Deliktssumme im Urteil selbst ausgewiesen
5. ✅ **[ERFASST - ID 361]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2021-79_2023-01-13.pdf — bandenmässiger Diebstahl ("Rip Deal"-Betrugsdiebstahl, Umschlagaustausch-Trick gegen einen einzelnen Geschädigten, Deliktssumme CHF 350'000.-, Score 0); Vorinstanz Tribunal pénal de l'arrondissement de la Gruyère 06.10.2020, 36 Monate FS unbedingt (Freispruch von den alternativ angeklagten Varianten "vol par métier"/"escroquerie par métier" zum selben Sachverhalt); Cour d'appel pénal weist Anschlussberufung der StA (zusätzliche Gewerbsmässigkeits-Qualifikation) vollumfänglich ab und bestätigt Qualifikation/Strafhöhe unverändert, gewährt auf Berufung des Beschuldigten hin nur beim Vollzug teilbedingten Strafvollzug (Vorinstanz-Werte in DB erfasst)
6. ❌ **[AUSGESCHLOSSEN - zu stark verschachtelter Mehrfach-Komplex-Fall, dieselbe Sache in zwei Verfahrensstadien]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2016-59_2017-05-05.pdf und /FR_TC_006_501-2018-40_2021-11-30.pdf — Escroquerie par métier + escroquerie + violation obligation de tenir une comptabilité (4 verschiedene insolvente Gesellschaften) + faux dans les titres + dénonciation calomnieuse + violation d'obligation d'entretien (Familienrecht) + Widerhandlung AVS; das zweite Urteil (2021) ist derselbe Fall nach Rückweisung durch das Bundesgericht (rein prozedural wegen unzulässiger Beschränkung des Wahlverteidigers, keine materielle Beanstandung) — mind. 6 grundverschiedene Sachkomplexe (Baukonsortium, mehrere Darlehen, Villenreservation, Unterhaltspflichten, AVS) gegen dieselbe Person, Deliktssumme/Score nicht sauber auf ein Hauptdelikt isolierbar
7. ❌ **[AUSGESCHLOSSEN - Pensionskassen-Grossfall mit 6 Mitbeschuldigten]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2018-120_2019-06-11.pdf — Ungetreue Geschäftsbesorgung im Zusammenhang mit dem Ponzi-artigen Zusammenbruch einer Vorsorgeeinrichtung (Fonds de prévoyance ACSMS, Anlagevolumen > CHF 40 Mio.); 6 Mitbeschuldigte (Stiftungsräte, Revisionsstelle), davon 3 bereits erstinstanzlich vollständig freigesprochen, bei den übrigen grösstenteils Verjährung/Freispruch für die Zeit vor 2011 — Berufung nur durch die Staatsanwaltschaft gegen diese Freisprüche; zu komplex und zu stark auf Freisprüche hinauslaufend für eine saubere Einzelfall-Erfassung
8. ✅ **[ERFASST - ID 363, Ausnahme 2: Werte der Rechtsmittelinstanz erfasst]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2019-122_2020-10-08.pdf — Veruntreuung (Bauherr liess dem Beschuldigten Akontozahlungen zur Bezahlung von Subunternehmern zukommen, die dieser zweckwidrig verwendete, Deliktssumme CHF 64'068.50) + bereits vorinstanzlich rechtskräftige Nebendelikte (Vorenthaltung von Lohnabzügen, Veruntreuung unter amtlicher Verfügungsmacht stehender Werte, AHVG- und AuG-Widerhandlung, Score 5); Vorinstanz Wirtschaftsstrafgericht Freiburg 12.04.2016 hatte vom Veruntreuungs-Hauptvorwurf mangels nachgewiesener Bereicherung freigesprochen; nach zwei durch das Bundesgericht aufgehobenen Berufungsentscheiden (6B_1383/2016, 6B_221/2019) bejahte das Kantonsgericht Freiburg am 8.10.2020 schliesslich Schuld und verurteilte zusätzlich zu 6 Monaten FS bedingt für die Veruntreuung — da kein vorinstanzlicher Schuldspruch existierte, wurden die Werte der Rechtsmittelinstanz erfasst
❌ **[AUSGESCHLOSSEN - weiterer, ähnlich stark verschachtelter Konkursdelikt-Komplex]** https://entscheidsuche.ch/docs/FR_Gerichte/FR_TC_006_501-2015-43_2015-11-30.pdf — zweites, separates Verfahren gegen einen bereits 2013 wegen ähnlicher Konkursdelikte verurteilten Beschuldigten (24 Monate FS): banqueroute frauduleuse, diminution effective de l'actif, gestion fautive, gestion déloyale, violation obligation comptabilité, détournement de valeurs sous main de justice, Gewalt/Drohung gegen Behörden, AVS-/ALV-Widerhandlungen sowie ein separates Escroquerie-/Abus de confiance-Dossier — mind. 8 verschiedene Tatbestandsgruppen, zu komplex für eine saubere Isolierung

## Graubünden (Kantonsgericht)

1. ✅ **[ERFASST - ID 353]** https://entscheidsuche.ch/docs/GR_Gerichte/GR_KG_004_SK1-2021-55_2022-10-28.pdf — gewerbsmässiger Betrug (91 gefälschte Krankenkassen-Rückforderungsbelege, Deliktssumme CHF 70'795.-) + mehrfache Urkundenfälschung (Score 3); Vorinstanz Regionalgericht Imboden 27.04.2021, 17 Monate FS bedingt; Kantonsgericht Graubünden weist Berufung (voller Freispruchsantrag) vollumfänglich ab und bestätigt Schuldsprüche und Strafe identisch, streicht aber die vorinstanzliche Verbindungsbusse von CHF 5'000.-
2. ✅ **[ERFASST - ID 359]** https://entscheidsuche.ch/docs/GR_Gerichte/GR_KG_004_SK1-2020-49_2022-06-15.pdf — gewerbsmässiger gegen den eigenen Arbeitgeber gerichteter Betrug (vorgetäuschte 100%-Arbeitsunfähigkeit bei parallelem Vollzeitjob anderswo, Deliktssumme CHF 49'356.-) + mehrfache Urkundenfälschung (8 falsche Arztzeugnisse, Score 3), Landesverweisung 8J; Vorinstanz Regionalgericht Plessur 18.02.2020, Geldstrafe 360 TS à CHF 170.- bedingt; Kantonsgericht Graubünden weist Berufung (voller Freispruchsantrag) vollumfänglich ab, bestätigt Schuldsprüche und Landesverweisung, reduziert TS-Zahl leicht auf 330 (Vorinstanz-Werte in DB erfasst)
3. ❌ **[AUSGESCHLOSSEN - zu stark verschachtelter Mehrpersonen-Fall]** https://entscheidsuche.ch/docs/GR_Gerichte/GR_KG_004_SK1-2020-47_2021-07-14.pdf — dieser konkrete Beschluss (14.7.2021) ist nur ein Rückweisungsverfahren zu Zivilforderungen (durch Vergleich gegenstandslos geworden), das eigentliche Strafurteil ist SK1 18 6/7/8/9 vom 25.2.2019 (Kantonsgericht, https://entscheidsuche.ch/docs/GR_Gerichte/GR_KG_004_SK1-2018-6_2019-02-25.pdf) — 137 Seiten, drei Mitbeschuldigte (Haupttäter, Mittäter, separat wegen Geldwäscherei verfolgter Dritter) wegen gewerbsmässigen Betrugs z.N. eines Energiekonzerns via IT-Beratungsvertrags-Schwindel plus schwerer Geldwäscherei, mit vier separaten Bundesgerichtsbeschwerden (6B_1201/2019, 6B_1209/2019, 6B_1214/2019, 6B_1202/2019) — Deliktssumme/Score liessen sich innert vertretbarem Aufwand nicht sauber isolieren

Ausgeschlossen: SK1-2019-47 (untypischer, stark umstrittener Sachverhalt, Hauptdelikt-Qualifikation nicht eindeutig).

## Zug (Obergericht)

1. ✅ **[ERFASST - ID 355]** https://entscheidsuche.ch/docs/ZG_Obergericht/ZG_OG_999_S-2021-18_2022-04-06.pdf — gewerbsmässiger Anlagebetrug (Aktien-Schwindel via Kaltakquise, 44 Einzelhandlungen als Kollektivdelikt, Deliktssumme CHF 1'332'160.- bei 29 Geschädigten, Score 0); Vorinstanz Strafgericht Zug (Kollegialgericht) 21.05.2021, 27 Monate FS teilbedingt (18 bedingt/9 unbedingt); Obergericht weist Berufungen von Beschuldigtem und StA beide vollumfänglich ab und bestätigt Schuldspruch und Strafe identisch (Besonderheit: Verletzung Beschleunigungsgebot)
2. ❌ **[AUSGESCHLOSSEN - mehrfache Teilfreisprüche über zwei Rechtsmittelrunden, kein stabiler Vorinstanz-Wert]** https://entscheidsuche.ch/docs/ZG_Obergericht/ZG_OG_002_S-2023-10_2023-08-29.pdf — Vorinstanz Strafgericht Zug 7.9.2021 sprach bereits vom Hauptvorwurf des (gewerbsmässigen) Betrugs frei und verurteilte nur wegen mehrfacher qualifizierter ungetreuer Geschäftsbesorgung; 1. Berufungsurteil des Obergerichts (11.7.2022) spricht die Beschuldigte zusätzlich von einem Teil der Geschäftsbesorgungsvorwürfe frei und muss die Strafe deshalb selbst neu auf 23 Monate FS bedingt festsetzen; vorliegendes Urteil vom 29.8.2023 ist ein drittes, auf ein partielles Rückweisungsverfahren beschränktes Verfahren (nur noch Zivilforderungen) — es gibt keinen unveränderten erstinstanzlichen Schuldspruch/Strafwert, der übernommen werden könnte

## Schwyz (Kantonsgericht)

1. ❌ **[AUSGESCHLOSSEN - Sachverhalt der Vorinstanz nicht verfügbar]** https://entscheidsuche.ch/docs/SZ_Gerichte/SZ_KG_003_STK-2024-45_2025-11-17.pdf — Veruntreuung (Einzeltat) + gewerbsmässiger betrügerischer Missbrauch DVA (Art. 147, 2008–2017); Berufung im Strafpunkt am 23./27.10.2025 zurückgezogen (Vergleich betr. Zivilforderungen), Kantonsgericht schreibt Verfahren nur noch prozedural ab. Das erstinstanzliche Urteil des Strafgerichts Schwyz (SGO 2023 12) vom 16.11.2023 mit den Sachverhalts-/Beweiswürdigungserwägungen ist selbst nicht separat publiziert; der KG-Entscheid enthält nur das Dispositiv, keine Angaben zu Deliktssumme, Geschlecht (aus Dispositiv nicht klar), Nationalität oder zur Rollenverteilung zwischen Veruntreuung und DVA-Missbrauch — ohne das Volltext-Urteil nicht zuverlässig erfassbar
2. ✅ **[ERFASST - ID 360, Ausnahme 2: Werte der Rechtsmittelinstanz erfasst]** https://entscheidsuche.ch/docs/SZ_Gerichte/SZ_KG_003_STK-2024-11_2025-09-23.pdf — gewerbsmässiger Betrug (Darlehensbetrug gegen Privatperson in 9 Tranchen, Deliktssumme CHF 211'000.-) + Covid-19-Betrug + Urkundenfälschung + Missbrauch Ausweise/Kontrollschilder + Misswirtschaft + Unterlassung Buchführung + qualifizierte ungetreue Geschäftsbesorgung (Score 10); Vorinstanz Strafgericht Schwyz 11.09.2023 sprach vom gewerbsmässigen Betrug (Hauptvorwurf) mangels Arglist frei und verurteilte nur wegen der übrigen, kleineren Delikte zu 12 Monaten FS unbedingt; der Privatkläger legte gegen den Freispruch erfolgreich Berufung ein (StA verzichtete auf ein Rechtsmittel), Kantonsgericht Schwyz bejaht am 23.9.2025 die Arglist doch, spricht den Beschuldigten zusätzlich des gewerbsmässigen Betrugs schuldig und legt die Gesamtstrafe eigenständig auf 42 Monate unbedingt fest — da für das Hauptdelikt kein vorinstanzlicher Schuldspruch existierte (Freispruch) und die Verschärfung nicht auf einem Rechtsmittel des Beschuldigten beruhte (Verschlechterungsverbot greift nicht), wurden die Werte der Rechtsmittelinstanz erfasst (`gericht`/`urteilsdatum` = Kantonsgericht Schwyz, 23.9.2025)

Ausgeschlossen: STK-2022-11 (Vorinstanz sprach frei, OG bestätigt Freispruch — keine vorinstanzliche Verurteilung).

## Solothurn (Obergericht, Signatur `STBER.*`)

Vermögensdelikt-Berufungsurteile in SO sind über die reine `search`-API überwiegend vor dem Dispositiv
bei 100'000 Zeichen abgeschnitten; über `search_by_case_number` liefert das Feld `sourceUrl`
(`SO_Omni`-Pfad statt `SO_OG`) jedoch meist den vollständigen, unabgeschnittenen Volltext direkt per
`curl` (mit `-A "Mozilla/5.0"`, da der `SO_OG`-Pfad teils 404 liefert).

1. ✅ **[ERFASST - ID 358]** https://entscheidsuche.ch/docs/SO_Omni/SO_OG_006_STBER-2019-17_2019-06-13.html — gewerbsmässiger betrügerischer Missbrauch DVA (32 Bankomat-Einsätze mit entwendeten Karten zweier Geschädigter, Deliktssumme CHF 9'870.-, Score 1, Besonderheit: Versuch) + rechtswidriger Aufenthalt; Vorinstanz Richteramt Bucheggberg-Wasseramt 22.11.2018 (vom mitangeklagten gewerbsmässigen Diebstahl bereits vorinstanzlich freigesprochen), 11 Monate FS unbedingt, Landesverweisung 10J; Obergericht Solothurn weist Berufung (voller Freispruchsantrag, keine Anschlussberufung StA) vollumfänglich ab
2. ❌ **[AUSGESCHLOSSEN - Herabstufung des Hauptdelikts von vollendeter zu (bundesgerichtlich als rechtlich fragwürdig bezeichneter) versuchter Tat]** https://entscheidsuche.ch/docs/SO_OG/SO_OG_006_STBER-2022-76_2023-07-13.html — Vorinstanz Amtsgericht Thal-Gäu 15.07.2022 sprach den Beschuldigten der vollendeten qualifizierten ungetreuen Geschäftsbesorgung schuldig (Deliktssumme CHF 252'906.82), Geldstrafe 180 TS à CHF 160.- bedingt, Ersatzforderung CHF 252'000.-; auf die Berufung des Beschuldigten hin (keine Anschlussberufung der StA) stufte das Obergericht Solothurn die Tat am 13.7.2023 zum blossen untauglichen Versuch herab (Geldstrafe auf 90 TS reduziert, durch Untersuchungshaft vollständig abgegolten, sogar Genugtuung für Überhaft) — das Bundesgericht wies die dagegen erhobene Beschwerde am 3.3.2025 zwar ab, hielt aber ausdrücklich fest, dass die erstinstanzliche (vollendete) Qualifikation "richtigerweise" zutreffend gewesen wäre und nur wegen des Verschlechterungsverbots nicht wiederhergestellt werden konnte (6B_1211/2023 E. 1.4) — angesichts dieser gerichtlich anerkannten Unsicherheit über die korrekte rechtliche Qualifikation des Hauptdelikts zu unsicher für einen DB-Eintrag

Ausgeschlossen: STBER-2018-52 (OG sprach vom Hauptvorwurf ungetreue Geschäftsbesorgung frei); STBER-2023-79 (BGer 6B_653/2024 hat Entscheid aufgehoben).

## Waadt (Cour d'appel pénale, `VD_TC_003`)

1. ❌ **[AUSGESCHLOSSEN - Deliktssumme nicht beziffert]** https://entscheidsuche.ch/docs/VD_FindInfo/VD_TC_003_PE24-026120_2026-04-20.pdf — Vol (Art. 139 ch. 1, nicht qualifiziert) + tentative de vol, Vorinstanz Tribunal de police de Lausanne 15.07.2025 (213 Tage FS unbedingt, Zusatzstrafe zur Geldstrafe vom 4.7.2023), Berufung vollständig abgewiesen (Art. 139 ch. 1 CP, keine Banden-/Gewerbsmässigkeit); der Deliktswert der einzigen erfolgreichen Tat ("environ une tonne de câble électrique en bronze") wird im gesamten Urteil nirgends in CHF beziffert — Deliktssumme damit nicht erfassbar
2. ❌ **[AUSGESCHLOSSEN - zu stark verschachtelter Serientäter-Fall]** https://entscheidsuche.ch/docs/VD_FindInfo/VD_TC_003_PE12-010581_2018-08-20.pdf — Escroquerie par métier, Vorinstanz Tribunal correctionnel de l'Est vaudois 13.12.2017 (18 Monate FS, Zusatzstrafe zu Genfer Urteilen 2010/2013), Berufung "très partiellement admis" bestätigt zwar Schuldspruch und 18-Monate-Strafe unverändert (nur ein Nebenvorwurf "faux dans les certificats" fällt weg); der Sachverhalt umfasst aber mind. 14 grundverschiedene Einzelvorwürfe (Baugeschäfts-Betrug, Mietbetrug, Urkundenfälschung, Nötigung, mehrere AuG-Verstösse, Versicherungs-/Kontrollschilderbetrug) gegen zahlreiche verschiedene Geschädigte über mehrere Jahre, zusätzlich zwei weitere frühere Verurteilungen wegen identischer Vorgehensweise (GE 2010, GE 2013) und eine angeordnete ambulante Massnahme — die für das Hauptdelikt (escroquerie par métier) alleine massgebende Deliktssumme lässt sich von den übrigen, ebenfalls einschlägigen Vermögensdelikten nicht sauber isolieren

## Neuenburg (Cour pénale, `NE_TC_009`)

1. ❌ **[AUSGESCHLOSSEN - Deliktssumme nur teilweise beziffert, komplexer rückwirkender Konkurs mit mehreren Vorurteilen]** https://entscheidsuche.ch/docs/NE_Omni/NE_TC_009_CPEN-2021-77_2022-05-15.html — gewerbsmässiger Diebstahl (3 vollendete + 5 versuchte Einbrüche in FR/NE/VD binnen 3 Monaten), Vorinstanz Tribunal de police du Littoral et du Val-de-Travers 28.07.2021, 10 Monate FS unbedingt; Cour pénale reduziert einzig den Schuldspruch für Widerhandlung gegen das AIG (ne bis in idem, bereits durch zwei Genfer Strafbefehle abgegolten) und bestätigt im Übrigen (inkl. Diebstahl-Qualifikation) durch Motivsubstitution dieselbe Gesamtstrafe von 10 Monaten. Nicht erfasst: mehrere der gestohlenen Gegenstände (Rolex, Omega, Laptop, Schmuck, Gemälde) sind im Urteil ohne Frankenwert aufgeführt, sodass die für das Hauptdelikt massgebende Deliktssumme nicht vollständig quantifizierbar ist; zudem verlangt die Strafzumessung eine aufwendige Aufteilung in einen rückwirkend konkurrierenden und einen selbständigen Strafenteil (Art. 49 Abs. 2 StGB) über drei verschiedene Verfahren (GE/NE) hinweg

## Tessin (Corte di appello e di revisione penale, `TI_CARP_001`)

1. ❌ **[AUSGESCHLOSSEN - zu stark verschachtelter Mehrfach-Tatbestandsfall]** https://entscheidsuche.ch/docs/TI_Gerichte/TI_CARP_001_17-2021-22_2022-02-17.html — Incarto Nr. "17.2021.22+33+56" (drei verbundene Verfahren); Truffa (Immobilienkonsortium-Betrug CHF 330'000 + IV/Arbeitslosenkassen-Betrug) + falsa dichiarazione + infrazioni (LADI/AVS) + frode fiscale + amministrazione infedele aggravata ripetuta gegen dieselbe Person — mind. 5 grundverschiedene Tatbestandsgruppen über mehrere Jahre, Deliktssumme/Score liessen sich nicht sauber auf ein einzelnes Hauptdelikt isolieren
2. ❌ **[AUSGESCHLOSSEN - fünf verbundene Verfahren, zwei Mitbeschuldigte]** https://entscheidsuche.ch/docs/TI_Gerichte/TI_CARP_001_17-2021-219_2021-12-21.html — Incarto Nr. "17.2021.219+220+234+237+316" (fünf verbundene Verfahren); Truffa ripetuta (Covid-19-Kredite, Bilanzfälschung, CHF 1'060'000 Gesamtschaden) als Mittäterschaft zweier Beschuldigter (AP1, AP2) mit unterschiedlichem Umfang der Schuldsprüche sowie Anschlussberufung der Staatsanwaltschaft — zu stark verschachtelt für eine saubere Einzelfall-Erfassung

## Uri (Obergericht Strafabteilung, `UR_OG_003`)

1. ❌ **[AUSGESCHLOSSEN - nur Leitsatz-Auszug, kein Sachverhalt/Dispositiv verfügbar]** https://entscheidsuche.ch/docs/UR_Gerichte/UR_OG_003_2018-OG-S-15-12_2018-07-31.pdf — Gewerbs-/bandenmässiger Diebstahl, Sachbeschädigung, Hausfriedensbruch (Art. 139/144/186 StGB); der über entscheidsuche.ch indexierte Volltext (auch via `search_by_case_number` identisch) umfasst nur zwei Seiten mit einem publizierten Leitsatz-Auszug zu einer verfahrensrechtlichen Beweisverwertungsfrage — weder Sachverhalt noch Deliktssumme noch Strafdispositiv sind enthalten, eine vollständigere Fassung ist nicht auffindbar
2. ⚠️ https://entscheidsuche.ch/docs/UR_Gerichte/UR_OG_003_2025-OG-S-25-4_2025-05-14.pdf und …-25-5 — nur Abschreibungsverfügungen wegen Berufungsrückzugs; das zugrundeliegende erstinstanzliche Urteil (Landgerichtspräsidium I Uri, PSA 24 28/29 vom 14.01.2025, Diebstahl/Sachbeschädigung/Hausfriedensbruch/rechtswidrige Einreise) ist dadurch rechtskräftig, aber nicht separat online auffindbar — Hinweis auf existierenden, aber nicht direkt erfassbaren Fall

## COVID-19-Kredit-Recherche (Stand 04.10.2026, alle Kantone)

Gezielte Suche nach COVID-19-Kreditbetrugsfällen (entscheidsuche.ch, DE/FR/IT). Eingetragen
(DB-Stand danach: 325 Fälle):

1. ✅ **[ERFASST]** VD PE21.012626 (Cour d'appel pénale 10.12.2024; Tribunal de police Lausanne 05.03.2024) — Betrug CHF 50'000, 180 TS bedingt
2. ✅ **[ERFASST]** VD PE24.010912 (02.12.2025; Tribunal de police Broye/Nord vaudois 12.02.2025) — Betrug CHF 50'000, 90 TS bedingt
3. ✅ **[ERFASST, Ausnahme 2]** VD PE22.014241 (10.03.2026; Vorinstanz Freispruch) — Betrug CHF 30'000, 180 TS bedingt
4. ✅ **[ERFASST, Ausnahme 2]** SZ STK 2025 41 (15.04.2026; zweiter Rechtsgang nach BGer 7B_1346/2024) — Betrug CHF 20'000, 70 TS bedingt (Zusatzstrafe)
5. ✅ **[ERFASST, Ausnahme 2]** ZH SB220649 (13.12.2023) — Betrug CHF 50'000, 6 Monate FS bedingt + Busse
6. ✅ **[ERFASST, Ausnahme 2]** SZ STK 2022 42 (26.03.2024) — Betrug CHF 25'583 zu viel, 68 TS à 160 bedingt + Busse
7. ✅ **[ERFASST]** BL 460 23 58 (Strafgericht BL 23.11.2022, bestätigt 05.12.2023) — mehrfacher Betrug CHF 45'000 (3 Kredite, CHF 93'000), 14 Monate FS bedingt
8. ✅ **[ERFASST, Ausnahme 2]** BS SB.2021.108 (24.08.2022) — Betrug CHF 11'900, 50 TS bedingt
9. ✅ **[ERFASST]** BS SB.2021.117 (Strafdreiergericht BS 02.06.2021, OG 24.01.2023 +UF) — mehrfacher Betrug CHF 443'276 zu viel, 12 Monate FS bedingt
10. ✅ **[ERFASST]** SO STBER.2022.48 (Amtsgericht Olten-Gösgen 01.03.2022, OG 31.08.2023) — Betrug CHF 300'000, 15 Monate FS bedingt
11. ✅ **[ERFASST, Ausnahme 2]** AG SST.2022.310 (23.10.2023) — Betrug CHF 240'000 + UF + Geldwäscherei, 18 Monate bedingt + Busse

Ausgeschlossen:

- ❌ FR 501 2024 44 (kein Strafzumessungstext, Strafmass nicht angefochten); FR 501 2023 151 (Art. 164 StGB trägt Einsatzstrafe, Betrugsschaden unklar)
- ❌ Freispruch vom Betrug: BL 460 2023-29, BS SB.2022.116, AG SST.2024.289, ZH SB240162/164/555, GG250009/12/18, GG250208, GG240230
- ❌ Nur Busse/Übertretung: BS SB.2024.42, GE P/21567/2022
- ❌ Mehrdelikts-/Misswirtschaftsfälle: AG SST.2024.152, SST.2023.198, SST.2024.284, SST.2024.76, SO STBER.2022.68, SZ STK 2024-34, FR 501 2025 72, GE P/22374/2020, BE SK 2023 526 (mit Landesverweisung)
- ⚠️ nicht abschliessend geprüft: FR 501 2024 21 / 2025 129, BE SK 2023 157, ZG S1 2024 23 (533k Zeichen, mehrere Delikte), GR SK1 2022 51, ZH SB230433/435 (Geldwäscherei Hauptdelikt), NW SA 25 1 (ung. Geschäftsbesorgung, COVID nur Nebenaspekt, Vorinstanz 150 TS à 130, OG 115 TS + Busse)

Hinweis: Nationalität bei COVID-Kreditbetrug nicht aus fehlender Landesverweisung ableiten
(keine Katalogtat nach ZH OG SB220649).

## Weitere Vermögensdelikte (Stand 04.10.2026)

1. ✅ **[ERFASST]** GR SR1 24 4 (Regionalgericht Plessur 06.11.2023; KG GR 30.04.2025, BGer 6B_605/2025 abgewiesen) — (versuchter) Betrug IV/Unfallversicherung + mehrfache UF, 12 Monate bedingt, Landesverweisung 5 Jahre
2. ✅ **[ERFASST]** GR SR1 24 6 (Regionalgericht Maloja 30.11.2023; KG GR 04.09.2025, Veruntreuung freigesprochen, BGer 6B_924/2025 abgewiesen) — gewerbsmässiger betr. Missbrauch DVA (Kreditkarte), 28 Monate teilbedingt (OG: 24)

Geprüft, nicht erfasst: BS SB.2023.82 (gewerbsmässiger Betrug erst im Berufungsverfahren, Massnahme/Gutachten), ZH SB250248 (versuchter Diebstahl/HFB, 4 Monate unbedingt, sieben Vorstrafen, kein Deliktsbetrag), ZH SB240539 (versuchter Diebstahl/HFB, 90 TS, Landesverweisung).
3. ✅ **[ERFASST]** ZH SB230447 (Bezirksgericht Horgen 01.12.2022; OG 02.09.2024, Schuldsprüche bestätigt) — Betrug COVID-Schnelltests (EUR 150'000), 12 Monate teilbedingt + Geldstrafe

Abgearbeitet, nicht erfasst:
- ZH SB250018: mehrfacher Online-Betrug mit Kleinstbeträgen (5 Dossiers, 180 TS à 10), wenig aussagekräftig
- BL 460 24 266: gewerbsmässiger Betrug, Zusatzstrafe 3 J 9 M zu einem NW-Urteil (Zusatzstrafe-Konstellation, Strafzumessungsberufung mit bindenden Tatsachen)
- BS SB.2024.90: über 25 Privatkläger, gewerbsmässiger Online-Betrug (zu viele Geschädigte), Zusatzstrafe
- BS SB.2024.72, SO STBER.2025.16: Serien-Diebstahl mit Zusatzstrafe/Widerruf/Gesamtstrafe und weiteren Delikten
- AG SST.2024.144 (nur 2 Monate FS, Landesverweisung), AG SST.2024.204 (Pfändungsbetrug als Hauptdelikt), ZG S1 2025 11 (Raub), ZG S2 2025 4 (Serien-Einbruchdiebstahl mit Mittäter und mehreren Privatklägern)

## Veruntreuung / ungetreue Geschäftsbesorgung (Stand 04.10.2026)

1. ✅ **[ERFASST]** AG SST.2022.232 (Bezirksgericht Baden 26.04.2022; OG 13.03.2023, Berufung nur Strafzumessung) — mehrfache Veruntreuung zum Nachteil eines kranken Bekannten (102 Fälle, CHF 70'000 Einsatz), 3 Jahre teilbedingt
2. ✅ **[ERFASST, Ausnahme 2]** ZH SB210339 (OG 11.10.2022 nach BGer-Rückweisung 6B_701/2020) — mehrfache Veruntreuung Geschäftskreditkarte CHF 716'291, 18 Monate bedingt
3. ✅ **[ERFASST, Ausnahme 2]** ZH SB240412 (OG 27.03.2025, Berufung des Privatklägers) — Veruntreuung CHF 25'000 (Tausendernoten), 120 TS à 130 bedingt

Geprüft, nicht erfasst: AG SST.2022.278 (qual. ung. GB/Veruntreuung, Zuordnung der Schuldsprüche nach Teilanfechtung unklar), AG SST.2021.209 (gewerbs- und bandenmässiger Diebstahl, 3,5 Jahre), ZH SB230033 und SB210066 (Misswirtschaft/Gläubigerschädigung-lastig), BE SK 2021 254 / SK 2021 62 / SK 2023 120 / SK 2022 630 (sehr umfangreich, mehrere Delikte), GR SK1 2020 31 (viele Delikte), BS SB.2020.87 (gewerbsmässiger Betrug u.a.), GL OG.2023.00016, SZ STK 2024 13, AG SST.2022.3 (Freispruch).

## Sachbeschädigung / betrügerischer Missbrauch DVA (Stand 04.10.2026)

1. ✅ **[ERFASST]** ZH SB220630 (Bezirksgericht Horgen 08.11.2022; OG 05.10.2023, Berufung abgewiesen) — mehrfache Sachbeschädigung (Wohnung der Ex-Partnerin, Schaden ca. CHF 4'500), 180 TS à 30 unbedingt (durch Haft geleistet)

Geprüft, nicht erfasst: BS SB.2021.69 (gewerbsmässiger DVA/Diebstahl, Gesamtstrafe 36 Monate inkl. widerrufener Genfer Strafe, Landesverweisung), ZH SB220545 (nur ein DVA-Bezug über CHF 750 nach Teilfreispruch, 20 TS), BL 460 2020 294 (sehr umfangreich, mehrere Delikte), SO STBER.2024.59 (Veruntreuung + DVA), BE SK 2022 103 / SK 2024 170 (Diebstahl bzw. Raub dominant), BE SK 2024 79 (Sachbeschädigung, Teilfreisprüche, geringfügig), BS SB.2020.31 (Sachbeschädigung mit stationärer Massnahme).

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
