# Projektplan — Robotergreifer, Bauteil B

**LV:** Produktdesign und Produktentwicklung, MRE WS 2026/27
**Gruppe:** 10 · **Bauteil:** B (PA 6, Ra 1,6)
**Team:** Bitsch Elias · Ovdiienko Viktoriia
**Stand:** 14.09.2026 — Vorschlag, noch nicht abgestimmt

---

## 1. Worum es geht

Ein Roboter nimmt Bauteil B vom Pufferband (Höhe 1000 mm), fährt 1800 mm
horizontal und legt es auf einem Werkstückträger ab (Höhe 1300 mm).
Taktzeit 5 s je Bauteil. Wir konstruieren den Greifer dafür — das Bauteil
selbst ist gegeben und wird nicht verändert.

Abzugeben sind acht Punkte laut Angabe (Roboterauswahl, Greifkonzept,
Greifkraftberechnung, 3D-Konstruktion, analytische Festigkeit, FEM,
Baugruppenzeichnung, Ablaufsimulation mit Kollisionskontrolle), abgelegt in
der Ordnerstruktur aus Abb. 2 der Angabe.

---

## 2. Technische Festlegungen

Diese fünf Entscheidungen stehen aus der Vorarbeit fest. Wenn Viktoriia eine
davon anders sieht, ist jetzt der richtige Zeitpunkt — nach dem Design Freeze
in KW 40 kostet jede Änderung die halbe Kette.

| Thema | Festlegung | Warum |
|---|---|---|
| **Greifkonzept** | 2-Finger-Parallelgreifer, Backen | Bauteil B hat zwei ebene, parallele Seitenflächen im Abstand 70 mm. Formschluss ist nicht nötig, Reibschluss reicht. Einfachste Lösung, die die Aufgabe erfüllt. |
| **Antrieb** | **Servomotor** mit Planetengetriebe und Haltebremse | Regelbare Greifkraft (PA 6 ist weich, Ra 1,6 darf nicht leiden), leise, keine Druckluftinfrastruktur. Preis: nicht selbsthemmend → Haltebremse ist zwingend, nicht optional. |
| **Mechanik** | Zahnstange–Ritzel, 1:1 synchron | 12,5 mm Backenhub brauchen nur ~72° Ritzeldrehung. Eine Trapezspindel bräuchte 6 Umdrehungen und bei 0,3 s Schließzeit über 1000 1/min. |
| **CAD** | **Onshape** (parametrisch, browserbasiert) | Beide sehen dasselbe Modell live, keine Versionskonflikte, keine lokale Installation. Ersetzt die bisherige Skript-Konstruktion als führendes Modell. |
| **Simulation** | **MuJoCo** | Siehe Abschnitt 3. |

### Kennwerte aus der Vorauslegung (zu bestätigen, nicht gesetzt)

- Bauteil B: 95 × 100 × 80 mm, 528,5 cm³, PA 6 (ρ = 1140 kg/m³) → **0,602 kg**
- Greifflächen: ±X, Backenabstand **70 mm**, 6200 mm² je Seite
- Bahnbeschleunigung aus Taktzeitbudget: **2,05 m/s²**
- Erforderliche Greifkraft: **14,3 N je Backe** (µ = 0,5 NBR/PA 6, S = 2,0)
- Roboter: **ABB IRB 1600-6/1.45**
- Wichtigster Befund: Mit dem Roboter mittig auf dem Boden ist der Ablauf
  **nicht ausführbar** — nicht wegen der Reichweite, sondern wegen Achse 5
  (±115°). Lösung: **Sockel 500 mm + Basisversatz 100 mm**. Das gehört als
  Erkenntnis in den Bericht, nicht versteckt.

---

## 3. Simulation: MuJoCo statt Gazebo

**Entscheidung: MuJoCo.**

Gazebo wäre die richtige Wahl, wenn wir gegen einen echten ABB-Controller mit
ROS 2 und MoveIt fahren würden — Sensorsimulation, Plugins, ganze Anlagenwelt.
Das brauchen wir nicht. Die Angabe verlangt "visuelle Darstellung inkl.
Kollisionskontrolle des Arbeitsablaufes", also Kinematik, Kollision und ein
Video.

Dafür ist MuJoCo besser:

- **Läuft ohne ROS**, direkt aus Python — kein Stack, der eine Woche Setup frisst
- **Kontaktkräfte** sind auswertbar. Wir können zeigen, dass das Bauteil unter
  der berechneten Greifkraft *tatsächlich* nicht rutscht, statt es nur zu
  behaupten. Das ist ein echtes Argument im Bericht.
- **Headless-Rendering** in guter Qualität → Bilder für die Doku und das Video
  entstehen im selben Lauf
- **Läuft bereits.** `sim/aufstellung.py` und `sim/ablauf.py` funktionieren,
  inklusive Levenberg-Marquardt-IK mit Konfigurationstreue. Das Rad ist schon
  rund.

Gazebo hätte gegenüber MuJoCo hier nur Nachteile: schwerer, ROS-abhängig, auf
Windows nur über WSL, und kein Mehrwert für das, was abgegeben wird.

---

## 4. Aufgabenteilung

Zwei Hälften, die jede für sich eine geschlossene Geschichte erzählen.
Niemand bekommt Restarbeiten.

### Elias — System & Integration

| # | Paket | Ergebnis | Ordner |
|---|---|---|---|
| E1 | **Roboterauswahl & Aufstellung** | Auswahlrechnung (Reichweite, Taktzeit, Traglast), Aufstellungsstudie Sockel/Basisversatz, Nachweis der Erreichbarkeit aller Stützpunkte | `Elias/01_Roboter` |
| E2 | **Greifer-Grundkörper** | Gehäuse, Antriebseinheit (Servo + Getriebe + Bremse), Ritzel/Zahnstange, Führung, Schnellwechsler, Roboterflansch ISO 9409-1-50-4-M6 | `Elias/02_CAD_Grundkoerper` |
| E3 | **Baugruppenzeichnung & Stückliste** | A3-Zeichnung, Positionsnummern, Stückliste mit Kauf-/Fertigungsteilen | `Elias/03_Zeichnung` |
| E4 | **Ablaufsimulation & Kollisionskontrolle** | MuJoCo-Modell, Bahn Entnahme → Ablage, Kollisionsprotokoll, Ablaufvideo | `Elias/04_Simulation` |
| E5 | **Infrastruktur** | Repo, Onshape-Dokument, MCP-Anbindung, Parametertabelle, Doku-Vorlage | `gemeinsam/` |

### Viktoriia — Auslegung & Nachweis

| # | Paket | Ergebnis | Ordner |
|---|---|---|---|
| V1 | **Greifkonzept & Konzeptskizze** | Variantenvergleich nach VDI 2225 (Parallel/Winkel/Vakuum/Magnet), Begründung der Wahl, bemaßte Konzeptskizze | `Viktoriia/01_Konzept` |
| V2 | **Greifkraft & Antriebsauslegung** | Kraftbilanz (Gewicht + Beschleunigung + Sicherheit), Reibwert mit Quelle, Flächenpressung auf PA 6, Ritzelmoment, Motorauswahl mit Reserve, Bremsenauslegung | `Viktoriia/02_Auslegung` |
| V3 | **Greiferzange & Weichbacken (CAD)** | Parametrische Zange in Onshape, Backentasche, Kontur passend zu Bauteil B | `Viktoriia/03_CAD_Zange` |
| V4 | **Festigkeitsnachweis analytisch + FEM** | Biegespannung und Durchbiegung analytisch, FEM mit Netzkonvergenz, Vergleich beider Wege mit Abweichungsdiskussion | `Viktoriia/04_Nachweis` |
| V5 | **FDM-Validierung** | Zange drucken, Greifversuch, Durchbiegung messen, gegen FEM halten | `Viktoriia/05_FDM` |

**Warum dieser Schnitt:** Viktoriia konstruiert genau das Bauteil, das sie
danach berechnet, prüft und druckt — Zange und Backen. Elias baut alles
drumherum und bringt es zum Laufen. Die Schnittstelle zwischen beiden ist eine
einzige Fläche: die **Anschraubebene Schlitten ↔ Zange**. Die wird in KW 41
festgelegt und danach nicht mehr angefasst.

### Gemeinsam

- **Dokumentation** — jede/r schreibt die eigenen Kapitel, gegenseitiges Review
- **Cross-Review** vor jedem Meilenstein: Elias prüft Viktoriias Rechnungen
  nach, Viktoriia prüft Elias' Modell auf Fertigbarkeit
- **Abgabe-ZIP** in der Struktur aus Abb. 2

---

## 5. Die FDM-Idee

Das verlangt niemand — aber es ist billig und hebt die Arbeit deutlich.

Wir drucken die Greiferzange aus PLA/PETG im Maßstab 1:1, klemmen sie ein,
hängen eine definierte Last ans freie Ende und **messen die Durchbiegung**.
Dann rechnen wir dieselbe Geometrie mit dem E-Modul des Druckwerkstoffs neu
und vergleichen drei Zahlen: analytisch, FEM, gemessen.

Was das bringt:

- Der Vergleich analytisch/numerisch wird vom Pflichtpunkt zum belastbaren
  Ergebnis — mit einem realen dritten Datenpunkt
- Man sieht sofort, ob die Einspannung im FEM-Modell zu steif angenommen war.
  Das ist der klassische Fehler und wir können ihn belegen statt vermuten.
- Die gedruckte Zange lässt sich im Video zeigen. Eine echte Backe in der Hand
  schlägt jedes Rendering.

**Wichtig für die Ehrlichkeit im Bericht:** Gedruckt wird PLA, gebaut wird
EN AW-7075. Der Test validiert das *Modell* (Randbedingungen, Lasteinleitung,
Netz), nicht das Bauteil. Genau so schreiben wir es hin.

---

## 6. Timeline

> ⚠️ **Der Abgabetermin ist angenommen, nicht bestätigt.** Ich komme von hier
> aus nicht an Moodle. Sobald der echte Termin feststeht, verschieben sich alle
> Meilensteine mit — die Abstände zwischen ihnen bleiben.
> **Annahme: Abgabe Freitag, 15.01.2027.**

| Meilenstein | Zeitraum | Ergebnis | Wer |
|---|---|---|---|
| **M0 — Kickoff** | KW 38 (14.–20.09.) | Plan abgestimmt, Rollen fix, Onshape + Repo stehen, offene Fragen an LV-Leitung raus | beide |
| **M1 — Konzept steht** | KW 39–40 (21.09.–04.10.) | Roboter gewählt (E1), Greifkonzept + Skizze (V1), Greifkraft gerechnet (V2) → **Design Freeze** | beide |
| **M2 — CAD schließt** | KW 41–44 (05.10.–01.11.) | Zange (V3) und Grundkörper (E2) getrennt konstruiert, Baugruppe schließt kollisionsfrei, Schnittstelle eingefroren | beide |
| **M3 — Nachweise** | KW 45–47 (02.11.–22.11.) | Analytisch + FEM + Netzkonvergenz + Vergleich (V4) | Viktoriia |
| **M4 — FDM-Test** | KW 48–49 (23.11.–06.12.) | Zange gedruckt, Messung, Abgleich mit FEM (V5) | Viktoriia, Druck: Elias |
| **M5 — Output** | KW 50–51 (07.12.–20.12.) | Zeichnung + Stückliste (E3), Simulation + Ablaufvideo (E4) | Elias |
| *Weihnachtspause* | KW 52–01 | — | — |
| **M6 — Abgabe** | KW 02–03 (04.–15.01.) | Doku zusammengeführt, Cross-Review, ZIP hochgeladen | beide |

**Puffer:** rund drei Wochen. Bewusst so — das ist nicht die einzige LV im
Semester, und die FEM-Kette hat erfahrungsgemäß einen schlechten Tag verdient.

**Fixer Termin:** jede Woche ein kurzer Sync, 20 Minuten, Stand + Blocker.

---

## 7. Offene Punkte

Diese müssen früh geklärt werden, weil sie nach hinten teuer werden:

1. **Gruppennummer.** `task.md` sagt Gruppe 10, Tab. 1 der Angabe kennt nur
   Gruppen 1–8 (Bauteil B = Gruppe 2). Bei der LV-Leitung nachfragen, bevor
   irgendein Dokument mit einer Nummer im Kopf gedruckt wird.
2. **Ablageorientierung am Werkstückträger.** Laut Angabe wird das bei der
   Angabenausgabe definiert. Aktuell mit 90° Drehung gerechnet. Wenn die
   Orientierung anders ist, ändert sich die Bahn und möglicherweise die
   Greifrichtung.
3. **FDM-Drucker.** Verfügbarkeit und Werkstoff klären (Labor oder privat).
4. **Onshape-Lizenz.** Free-Plan macht Dokumente öffentlich. Für eine
   Studienarbeit ist das meist egal, sollte aber bewusst entschieden sein —
   Education-Plan ist kostenlos und privat.

---

## 8. Arbeitsweise im Repo

```
PDE/
├─ Elias/          ← Elias arbeitet nur hier
├─ Viktoriia/      ← Viktoriia arbeitet nur hier
├─ gemeinsam/      ← Parameter, Vorlagen, Abgabe-ZIP
│  ├─ abgabe/      ← finale Struktur nach Abb. 2
│  └─ referenzen/
├─ cad/ fem/ sim/  ← bestehende Skriptkette (Vorarbeit, bleibt als Referenz)
└─ PLAN.md
```

**Regel:** jede/r committet nur im eigenen Ordner. Dann gibt es keine
Merge-Konflikte. Zusammengeführt wird ausschließlich in `gemeinsam/abgabe/`,
und zwar am Ende, bewusst und gemeinsam.

Commit-Nachrichten auf Deutsch, eine Zeile, was sich geändert hat und warum.

---

## 9. Was Viktoriia dazu sagen soll

Der Plan ist ein **Vorschlag**, kein Beschluss. Konkret bitte Rückmeldung zu:

- Passt die Aufteilung? Wenn du lieber CAD statt FEM machst (oder umgekehrt),
  tauschen wir — die Pakete sind so geschnitten, dass V3↔E2 und V4↔E4 tauschbar
  sind.
- Onshape okay, oder arbeitest du lieber in etwas anderem? (SolidWorks,
  Fusion, Inventor — dann müssen wir nur die Schnittstelle über STEP klären.)
- Ist dir die Timeline zu eng oder zu locker?
- Hast du beim FEM einen Tool-Wunsch? Es gibt hier eine laufende
  CalculiX-Kette, aber wenn du lieber in einer GUI rechnest, ist das
  vollkommen in Ordnung — dann wird die Skriptkette die unabhängige
  Gegenrechnung, und der Bericht wird dadurch besser, nicht schlechter.
