"""Abgabepunkt 4 - 3D-Konstruktion Greifer, Gruppe 10 / Bauteil B.

Parametrischer Aufbau mit build123d. Jede Iteration = ein Skriptlauf.

Aufbau von oben nach unten (z = 0 an der Roboter-Flanschflaeche, +Z zum Bauteil):
  z   0 .. 10    Adapterplatte am Roboterflansch (ISO 9409-1-50-4-M6)
  z  10 .. 40    Schnellwechselsystem (Roboter- + Greiferseite)
  z  40 .. 95    Greifergehaeuse mit der Mechanik (siehe mechanik.py)
  z  95 ..105    Anschraubflansch der Zahnstangen
  z 105 ..115    Anschraubkopf der Greiferzangen
  z 115 ..235    Greiferzangen (auswechselbar, an Bauteil B angepasst)

Die innere Mechanik (Zylinder, Kolben, Zahnstangen, Ritzel) steckt in
mechanik.py, damit diese Datei die Baugruppenlogik behaelt.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build123d import (
    Align, Axis, Box, Cylinder, Location, Mode, Plane, Pos, Rot,
    chamfer, export_step, fillet,
)
import mechanik as M
import params as P

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "step")
os.makedirs(OUT, exist_ok=True)

C = (Align.CENTER, Align.CENTER, Align.MIN)

# ---------------------------------------------------------------- Massketten
Z_FLANSCH = 0.0
T_ADAPTER = 10.0
T_WECHSLER_R = 14.0
T_WECHSLER_G = 16.0

Z_WECHSLER = Z_FLANSCH + T_ADAPTER
Z_WECHSLER_G = Z_WECHSLER + T_WECHSLER_R

# Ebenen der Mechanik uebernehmen, damit es nur eine Massenkette gibt
Z_KOERPER = M.Z_KOERPER
Z_ZANGE_KOPF = M.Z_ZANGE_KOPF
T_ZANGE_KOPF = M.T_ZANGE_KOPF
Z_ZANGE = M.Z_ZANGE

D_FLANSCH = 63.0
D_LOCHKREIS = 50.0
D_ZENTRIERUNG = 31.5
D_SCHRAUBE = 6.6

ZL, ZB, ZH = P.ZANGE_L, P.ZANGE_B, P.ZANGE_H
X_ZANGE = M.X_ZANGE


def _flanschbild(part, z0, z1):
    """4 Durchgangsloecher auf Lochkreis 50 + Zentrierbohrung."""
    from math import cos, radians, sin
    for i in range(4):
        a = radians(45 + 90 * i)
        r = D_LOCHKREIS / 2.0
        part -= Pos(r * cos(a), r * sin(a), z0) * Cylinder(
            D_SCHRAUBE / 2, z1 - z0, align=C)
    part -= Pos(0, 0, z0) * Cylinder(D_ZENTRIERUNG / 2, (z1 - z0) * 0.4, align=C)
    return part


def adapterplatte():
    """Pos.1 - Adapterplatte Roboterflansch -> Schnellwechsler."""
    p = Pos(0, 0, Z_FLANSCH) * Cylinder(D_FLANSCH / 2, T_ADAPTER, align=C)
    p = _flanschbild(p, Z_FLANSCH, Z_FLANSCH + T_ADAPTER)
    p = chamfer(p.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[-1], 1.0)
    return p


def wechsler_roboterseite():
    """Pos.2 - Schnellwechselsystem, Roboterseite (fest am Roboter)."""
    p = Pos(0, 0, Z_WECHSLER) * Cylinder(58 / 2, T_WECHSLER_R, align=C)
    p -= Pos(0, 0, Z_WECHSLER + T_WECHSLER_R - 5) * (
        Cylinder(58 / 2, 3, align=C) - Cylinder(48 / 2, 3, align=C))
    p -= Pos(0, 0, Z_WECHSLER + T_WECHSLER_R - 4) * Cylinder(30.2 / 2, 4, align=C)
    p = _flanschbild(p, Z_WECHSLER, Z_WECHSLER + T_WECHSLER_R)
    return p


def wechsler_greiferseite():
    """Pos.3 - Schnellwechselsystem, Greiferseite (bleibt am Greifer).

    Fuehrt die Motorleitung durch. Beim Servoantrieb sind hier elektrische
    Kontakte noetig statt einer Luftkupplung - der Preis der Antriebswahl,
    dokumentiert in params.py.
    """
    p = Pos(0, 0, Z_WECHSLER_G) * Cylinder(58 / 2, T_WECHSLER_G, align=C)
    p += Pos(0, 0, Z_WECHSLER_G - 4) * Cylinder(30 / 2, 4, align=C)
    for dy in (-18, 18):
        p -= Pos(0, dy, Z_WECHSLER_G) * Cylinder(4 / 2, T_WECHSLER_G, align=C)
    return p


def zange(seite):
    """Pos.10 - GREIFERZANGE (2x), das nachzuweisende Bauteil.

    Kragarm aus EN AW-7075 T6, am Zahnstangenflansch verschraubt.
    Ausgelegt auf die volle Backenkraft des Zylinders, nicht auf die zum
    Halten noetige Greifkraft.
    """
    x = seite * X_ZANGE
    p = Pos(x, 0, Z_ZANGE_KOPF) * Box(ZH + 12, ZB, T_ZANGE_KOPF, align=C)
    for dy in (-9, 9):
        p -= Pos(x, dy, Z_ZANGE_KOPF) * Cylinder(6.6 / 2, T_ZANGE_KOPF, align=C)
    p += Pos(x, 0, Z_ZANGE) * Box(ZH, ZB, ZL, align=C)

    x_innen = seite * (P.GREIF_ABSTAND / 2.0 + 8.0)
    p -= Pos(x_innen, 0, Z_ZANGE + ZL - P.BACKE_LAENGE) * Box(
        2 * P.BACKE_TIEFE, P.BACKE_BREITE, P.BACKE_LAENGE, align=C)

    kanten = p.edges().filter_by(Axis.Y).group_by(Axis.Z)[1]
    kerben = [e for e in kanten if abs(abs(e.center().X - x) - ZH / 2) < 0.1]
    p = fillet(kerben, P.ZANGE_FILLET)
    return p


def weichbacke(seite):
    """Pos.11 - Weichbacke NBR (2x), schuetzt die Oberflaeche Ra 1,6."""
    x = seite * (P.GREIF_ABSTAND / 2.0 + 4.0)
    return Pos(x, 0, Z_ZANGE + ZL - P.BACKE_LAENGE) * Box(
        8 + P.BACKE_TIEFE, P.BACKE_BREITE, P.BACKE_LAENGE, align=C)


# ---------------------------------------------------------------- Stueckliste
# (Pos, Benennung, Anzahl, Werkstoff, Dichte g/cm3, Erzeuger)
# Der Erzeuger bekommt die Seite (+1/-1); bei Einzelteilen wird sie ignoriert.
STUECKLISTE = [
    ("1",  "Adapterplatte",                 1, "EN AW-6082 T6",      2.70, lambda s=1: adapterplatte()),
    ("2",  "Schnellwechsler Roboterseite",  1, "Zukaufteil, 1.4301", 7.90, lambda s=1: wechsler_roboterseite()),
    ("3",  "Schnellwechsler Greiferseite",  1, "Zukaufteil, 1.4301", 7.90, lambda s=1: wechsler_greiferseite()),
    ("4",  "Funktionstraeger",              1, "EN AW-6082 T6",      2.70, lambda s=1: M.gehaeuse()),
    ("5",  "Ritzel m=1 z=20",               1, "16MnCr5 einsatzgeh.", 7.85, lambda s=1: M.ritzel()),
    ("6",  "Ritzelwelle",                   1, "1.7225",             7.85, lambda s=1: M.ritzelwelle()),
    ("7",  "Zahnstange mit Backenflansch",  2, "16MnCr5 einsatzgeh.", 7.85, M.zahnstange),
    ("8",  "Servomotor mit Planetengetriebe", 1, "Zukaufteil",        3.00, lambda s=1: M.motor()),
    ("9",  "Greiferzange",                  2, P.ZANGE_WERKSTOFF,    2.80, zange),
    ("10", "Weichbacke",                    2, "NBR 70 Shore A",     1.35, weichbacke),
    ("11", "Verkleidung",                   1, "PA12 schwarz, SLS",  1.01, lambda s=1: M.verkleidung()),
    ("12", "Haltebremse am Ritzel",         1, "Zukaufteil",         3.00, lambda s=1: M.bremse()),
]

# Positionen, die doppelt vorkommen (links/rechts)
PAARE = {"7", "9", "10"}


def alle_koerper():
    """Jeder Koerper der Baugruppe einzeln: (Schluessel, Pos, Benennung, Koerper).

    Einzige Stelle, an der die Baugruppe zusammengesetzt wird - Zeichnung,
    Rendering und Simulation greifen darauf zu, damit nichts auseinanderlaeuft.
    """
    aus = []
    for pos, name, anz, werkstoff, rho, fn in STUECKLISTE:
        if pos in PAARE:
            for s, tag in ((1, "L"), (-1, "R")):
                aus.append(("pos%s%s" % (pos, tag), pos,
                            "%s %s" % (name, tag), fn(s)))
        else:
            aus.append(("pos%s" % pos, pos, name, fn()))
    return aus


def baugruppe_teile():
    return [(k, b) for k, pos, n, b in alle_koerper()]


def baugruppe_compound():
    """Benannte Einzelkoerper als Compound.

    Bewusst NICHT verschmolzen: ein mit '+' vereinigter Koerper landet in
    Onshape als ein einziges namenloses COMPOUND und die Stueckliste dort
    waere wertlos.
    """
    from build123d import Compound
    kinder = []
    for key, pos, name, koerper in alle_koerper():
        sol = koerper.solids()
        k = sol[0] if len(sol) == 1 else Compound(children=sol)
        k.label = "Pos%s_%s" % (pos, name.replace(" ", "_"))
        kinder.append(k)
    c = Compound(children=kinder)
    c.label = "Greifer_Gruppe%d_Bauteil%s" % (P.GRUPPE, P.BAUTEIL)
    return c


# Paarungen, bei denen ein Verschnitt aus der Ersatzgeometrie stammt und
# keine Konstruktionsfehler sind. Die Verzahnung ist als Trapezprofil
# modelliert; Trapezzaehne auf einem Kreis koennen mit einer geraden
# Zahnstange nicht ueberschneidungsfrei kaemmen, dafuer braeuchte es
# Evolventenprofile. Der Nachweis der Verzahnung erfolgt analytisch in
# mechanismus.py, nicht ueber die Modellgeometrie.
BEKANNT = {("5", "7")}


def durchdringungspruefung(spiel=1e-3):
    """Paarweiser Verschnitt aller Bauteile.

    Rueckgabe: (echte Treffer, bekannte Ersatzgeometrie-Treffer)
    """
    koerper = alle_koerper()
    echt, bekannt = [], []
    for i, (ka, pa, na, a) in enumerate(koerper):
        for kb, pb, nb, b in koerper[i + 1:]:
            v = (a & b).volume
            if v <= spiel:
                continue
            paar = tuple(sorted((pa, pb)))
            (bekannt if paar in BEKANNT else echt).append((na, nb, v / 1000.0))
    return echt, bekannt


def stueckliste_daten():
    zeilen, m_ges = [], 0.0
    for pos, name, anz, werkstoff, rho, fn in STUECKLISTE:
        v = fn(1).volume / 1000.0
        m = v * rho / 1000.0
        m_ges += m * anz
        zeilen.append((pos, name, anz, werkstoff, v, m))
    return zeilen, m_ges


def main():
    print("GREIFER - %s" % P.GREIFER_TYP)
    print("Gruppe %d, Bauteil %s\n" % (P.GRUPPE, P.BAUTEIL))
    print("ANTRIEB")
    print("  %s, Getriebe i = %.0f" % (P.MOTOR_TYP, P.GETRIEBE_I))
    print("  Moment am Ritzel %.2f Nm -> F_Backe = %.1f N (%.1f-fach)"
          % (P.M_ABTRIEB, P.GREIFER_F_MAX, P.GREIFER_F_MAX / P.F_GREIF))
    print("  Hub %.0f mm je Backe aus %.0f Grad Ritzeldrehung\n"
          % (P.GREIFER_HUB,
             P.GREIFER_HUB / (2 * 3.14159 * P.R_TEILKREIS) * 360))

    zeilen, m_ges = stueckliste_daten()
    print("STUECKLISTE")
    print("  %-4s %-32s %4s %-22s %9s %9s"
          % ("Pos", "Benennung", "Anz", "Werkstoff", "V [cm3]", "m [kg]"))
    print("  " + "-" * 86)
    for pos, name, anz, werkstoff, v, m in zeilen:
        print("  %-4s %-32s %4d %-22s %9.2f %9.3f"
              % (pos, name, anz, werkstoff, v, m))
    print("  " + "-" * 86)
    print("  %-4s %-32s %4s %-22s %9s %9.3f" % ("", "Gesamtmasse", "", "", "", m_ges))
    print("  Auslastung Traglast %s: %.0f %% (Greifer + Bauteil)"
          % (P.ROBOTER, 100 * (m_ges + P.B_MASSE) / P.M_TRAGLAST))

    comp = baugruppe_compound()
    export_step(comp, os.path.join(OUT, "Greifer_Baugruppe.step"))
    print("\n  -> out/step/Greifer_Baugruppe.step  (%d benannte Koerper)"
          % len(comp.children))

    for key, pos, name, koerper in alle_koerper():
        kurz = name
        for bad in "/\\:*?\"<>|":
            kurz = kurz.replace(bad, "")
        export_step(koerper, os.path.join(
            OUT, "Pos%s_%s.step" % (pos, "_".join(kurz.split()))))
    print("  -> %d Einzelteile als STEP" % len(comp.children))

    z = Pos(-X_ZANGE, 0, -Z_ZANGE_KOPF) * zange(1)
    export_step(z, os.path.join(OUT, "Greiferzange_FEM.step"))
    print("  -> out/step/Greiferzange_FEM.step  (Einspannung bei z=0)")

    print("\nSTEP-RUECKLESEPRUEFUNG")
    print("  Der interne Modellzustand sagt nichts darueber aus, was im STEP")
    print("  ankommt. Degenerierte Geometrie zerfaellt erst beim Export.")
    from build123d import import_step
    zurueck = import_step(os.path.join(OUT, "Greifer_Baugruppe.step"))
    n_soll = len(comp.children)
    n_ist = len(zurueck.solids())
    v_soll = sum(k.volume for _, k in baugruppe_teile()) / 1000.0
    v_ist = sum(s.volume for s in zurueck.solids()) / 1000.0
    print("  Koerper   Modell %d   STEP %d   %s"
          % (n_soll, n_ist, "ok" if n_soll == n_ist else "ABWEICHUNG"))
    print("  Volumen   Modell %.2f cm3   STEP %.2f cm3   %s"
          % (v_soll, v_ist,
             "ok" if abs(v_soll - v_ist) < 0.5 else "ABWEICHUNG %.2f cm3"
             % abs(v_soll - v_ist)))

    print("\nDURCHDRINGUNGSPRUEFUNG")
    echt, bekannt = durchdringungspruefung()
    if echt:
        for na, nb, v in echt:
            print("  KOLLISION  %-30s <-> %-30s  %.3f cm3" % (na, nb, v))
    else:
        print("  keine Durchdringungen")
    for na, nb, v in bekannt:
        print("  (Verzahnung, Ersatzgeometrie: %s / %s, %.3f cm3)" % (na, nb, v))

    ges = baugruppe_compound()
    bb = ges.bounding_box()
    print("\nBAUGRUPPE")
    print("  Huellmass            %.0f x %.0f x %.0f mm"
          % (bb.size.X, bb.size.Y, bb.size.Z))
    print("  Bauhoehe ab Flansch  %.0f mm" % (Z_ZANGE + ZL))
    print("  Greifabstand         %.1f mm" % P.GREIF_ABSTAND)
    print("  Backenhub je Seite   %.1f mm" % P.GREIFER_HUB)


if __name__ == "__main__":
    main()
