---
workflow: general-video
flow: automation
storyboard: no
message: "Der Plan steht — sag mir, was du anders willst"
destination: file
aspect: 1920x1080
language: de
audience: "Viktoriia, Projektpartnerin, Maschinenbau-Studentin"
length: 75s
angle: plan-pitch
---

## Intent

Pitch-Video für Viktoriia. Sie soll in gut einer Minute verstehen: welche zwei
Termine hart sind, wofür es Punkte gibt, wer was macht, und wie das
automatisierte Setup funktioniert (Claude über MCP an Onshape, dazu FEM,
MuJoCo, GitHub, FDM-Druck).

Ton: kollegial und konkret, kein Marketing. Es ist ein Vorschlag, kein
Beschluss — der Schluss fordert sie ausdrücklich auf, zu widersprechen.
Technisch, dunkel, präzise. Kein Voiceover, kein Musikbett: sie schaut das
wahrscheinlich stumm am Handy in der Bahn.

Wichtig laut Auftraggeber: **Timeline und Aufgabenteilung sind die Kernszenen.**
Das Setup ist der Überraschungseffekt, nicht der Hauptinhalt.

## Assets

- `assets/shots/onshape.png` — Onshape-Startseite, bewirbt selbst "FeatureScript MCP" und "Text → Code → CAD". Kernbeleg der Setup-Szene.
- `assets/shots/mcp.png` — modelcontextprotocol.io Doku mit Architekturdiagramm
- `assets/shots/mujoco.png` — mujoco.org Startseite
- `assets/shots/github.png` — das Projekt-Repo auf GitHub
- `assets/logos/*.svg|png` — offizielle Marken: Onshape, Claude, Anthropic, GitHub, ABB, Python
- `assets/work/greifer_iso.png`, `greifer_mit_bauteilB.png` — eigene CAD-Renderings aus der Vorarbeit
- `assets/work/fem_konvergenz.png` — eigener FEM-Konvergenzplot
- `assets/work/ablauf_*.png` — eigene MuJoCo-Ablaufbilder
- `assets/work/zeichnung.png` — eigene Baugruppenzeichnung
- `assets/work/konzeptskizze.png` — eigene Konzeptskizze
- `assets/work/aufstellung.png` — Aufstellungsstudie

## Customizations

- Echte Logos und echte Website-Screenshots statt nachgebauter Kacheln — ausdrücklich gewünscht.
- Eigene Arbeitsbilder aus der Vorarbeit mit einbauen, damit sichtbar ist, dass die Kette schon läuft.
- Die zwei roten Deadlines (26.11. / 15.01.) müssen optisch als das Härteste im Video stehen.
- Schluss mit Repo-Link und expliziter Aufforderung zum Widerspruch.

## Notes

- Deutsch, Du-Form, Viktoriia wird direkt angesprochen.
- Keine erfundenen Zahlen. Punkte, Termine und Kennwerte stammen aus
  `moodle/` und `PLAN.md`; nichts dazuerfinden.
- Viktoriia ist in LV-Gruppe BB-2, Elias in BB-1 — das Video behauptet nicht,
  die Terminfrage sei geklärt, sondern nennt sie als offenen Punkt.
