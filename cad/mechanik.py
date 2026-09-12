"""Innere Mechanik des Greifers - Zahnstange-Ritzel, Servomotor.

Wirkprinzip (Variantenvergleich in mechanismus.py):

    Servomotor -> Planetengetriebe i=5 -> Ritzel -> zwei Zahnstangen

Das Ritzel zwingt beide Zahnstangen gegenlaeufig und gleich weit; die Backen
laufen also zwangslaeufig synchron, ohne Regelung und ohne zweiten Antrieb.

WARUM DIE ZAHNSTANGEN UEBEREINANDER LIEGEN

Liegen sie nebeneinander (XY-Ebene), steht die Ritzelachse senkrecht. Ein
NEMA 17 mit Planetengetriebe und Haltebremse ist rund 110 mm lang und wuerde
koaxial entweder nach oben in den Roboterflansch (nur 40 mm Platz) oder nach
unten ins Bauteil (nur 80 mm Platz) ragen. Beides kollidiert.

Uebereinander angeordnet (XZ-Ebene) steht die Ritzelachse waagerecht in Y.
Der Motor laesst sich dann seitlich direkt anflanschen - dort ist Freiraum,
weil die Zangen das Bauteil mittig fassen.

LAGEPLAN (Greifer-Koordinatensystem, Blick in -Y)

    z
    |   +-------------------------------------------------+  Gehaeuse
 42 |   |  ===== Zahnstange 1 (oben) ===========[Steg]     |
 57 |   |        Teillinie oben       vvvv                 |
 67 |   |  -- Ritzelachse (in Y) --  (Ritzel)  ---> Motor seitlich
 77 |   |        Teillinie unten      ^^^^                 |
 92 |   |     [Steg]========= Zahnstange 2 (unten) ======  |
 95 |   +-------------------------------------------------+
        |  Flansch Backe 2                 Flansch Backe 1 |
       -x                                                 +x

Die beiden Zahnstangen ueberlappen sich in x nur im Verzahnungsbereich um das
Ritzel; dort trennt sie die Hoehe. Ihre Anschraubflansche sitzen an
entgegengesetzten Enden, kommen sich also nicht in die Quere.

Die Verzahnung ist als Trapezprofil ausgefuehrt (Ersatzgeometrie). Die
Tragfaehigkeit wird analytisch in mechanismus.py nachgewiesen.
"""
import os
import sys
from math import cos, pi, radians, sin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build123d import Align, Axis, Box, Cylinder, Pos, Rot, fillet
import params as P

C = (Align.CENTER, Align.CENTER, Align.MIN)
CC = (Align.CENTER, Align.CENTER, Align.CENTER)
CU = (Align.CENTER, Align.CENTER, Align.MIN)

# ---------------------------------------------------------------- Ebenen in Z
Z_KOERPER = 40.0
# Gehaeusehoehe HERGELEITET aus der Verkleidung: der Funktionstraeger muss in
# die Squircle-Schale passen, also hoechstens 2*(SQ_C - Wand - Spiel) hoch
# sein. Nach unten begrenzt ihn die Mechanik: 2 Zahnstangen + Ritzel + Waende.
H_KOERPER = 62.0
Z_UNTEN = Z_KOERPER + H_KOERPER            # 95
T_FLANSCH = 10.0
Z_ZANGE_KOPF = Z_UNTEN + T_FLANSCH         # 105
T_ZANGE_KOPF = 10.0
Z_ZANGE = Z_ZANGE_KOPF + T_ZANGE_KOPF      # 115

# ---------------------------------------------------------------- Verzahnung
MODUL = P.MODUL
Z_RITZEL = P.Z_RITZEL
R_TEIL = P.R_TEILKREIS                     # 10,0 mm
B_ZAHN = P.B_ZAHN                          # 8 mm (Breite in Y)
H_KOPF = 1.00 * MODUL
H_FUSS = 1.25 * MODUL
H_ZAHN = H_KOPF + H_FUSS
D_WELLE = 8.0

# ---------------------------------------------------------------- Gehaeuse
GEH_X, GEH_Y = 124.0, 60.0
X_L, X_R = -GEH_X / 2, GEH_X / 2
WAND = 2.5

X_ZANGE = P.GREIF_ABSTAND / 2.0 + 8.0 + P.ZANGE_H / 2.0    # 47 mm

# Ritzelachse waagerecht in Y, mittig im Gehaeuse
Z_ACHSE = Z_KOERPER + H_KOERPER / 2.0                       # 67,5

# Zahnstangen: Querschnitt SCHL_H (in Z) x SCHL_B (in Y)
SCHL_H = 14.0
SCHL_B = 16.0
HUB = P.GREIFER_HUB

# Teillinien liegen um den Teilkreisradius ueber bzw. unter der Achse.
# Der Koerper sitzt um die Fusshoehe weiter weg, die Zaehne ragen von dort
# um die Kopfhoehe an den Teilkreis heran.
Z_TEIL_O = Z_ACHSE - R_TEIL                 # 57,5
Z_TEIL_U = Z_ACHSE + R_TEIL                 # 77,5
Z_RACK_O = Z_TEIL_O - H_FUSS - SCHL_H       # Oberkante Zahnstange oben
Z_RACK_U = Z_TEIL_U + H_FUSS                # Oberkante Zahnstange unten

# Laengen: Koerper muss bei geoeffneten Backen im Gehaeuse bleiben
RACK_VON, RACK_BIS = -30.0, 50.0
ZAHN_VON, ZAHN_BIS = -22.0, 22.0            # Verzahnungsbereich um das Ritzel

# ---------------------------------------------------------------- Antrieb
MOT_FLANSCH = P.MOT_FLANSCH
MOT_L_GETRIEBE = P.MOT_L_GETRIEBE
MOT_L_MOTOR = P.MOT_L_MOTOR
MOT_L_BREMSE = P.MOT_L_BREMSE
MOT_L = P.MOT_L_GESAMT
Y_MOT = GEH_Y / 2                                            # Anbauflaeche

# ---------------------------------------------------------------- Squircle
# Die Aussenform ist eine Superellipse (Squircle):
#     |y/a|^n + |z/c|^n = 1
# n = 2 ergibt eine Ellipse, n -> unendlich ein Rechteck. Bei n = 4 entsteht
# die volle, weiche Form, die an Geraeten ueblich ist: fast rechteckige
# Flaechen mit stetig gekruemmten Ecken - anders als eine Verrundung, die
# zwischen Gerade und Kreisbogen einen Kruemmungssprung hat.
SQ_N = 4.0                                  # Exponent der Superellipse
SQ_PUNKTE = 240                             # Stuetzstellen des Profils

# Halbachsen HERGELEITET, nicht gewaehlt:
#   a  Baulaenge des Antriebs + Wand; der Antrieb muss vollstaendig hinein,
#      sonst steht wieder etwas heraus
#   c  Bauhoehe der Mechanik (2 Zahnstangen + Ritzel) bzw. Umkreis des
#      Motorflansches - der groessere Wert bestimmt
WAND_SQ = 6.0                               # mm Wandstaerke Alu, gefraest
WAND_VERK = 3.0                             # mm Wandstaerke Verkleidung, SLS-Druck


def squircle(a, c, n=SQ_N, punkte=SQ_PUNKTE):
    """Punkte einer Superellipse mit den Halbachsen a und c."""
    from math import cos, sin, pi, copysign
    aus = []
    for i in range(punkte):
        t = 2 * pi * i / punkte
        ct, st = cos(t), sin(t)
        aus.append((copysign(abs(ct) ** (2.0 / n), ct) * a,
                    copysign(abs(st) ** (2.0 / n), st) * c))
    return aus


# ---------------------------------------------------------------- Gestaltung
# Der Antrieb wird nicht angeschraubt, sondern in einen angeformten Ausleger
# eingehaust, der mit grossem Radius in den Grundkoerper uebergeht. Auf der
# Gegenseite sitzt ein kuerzerer Ausleger fuer den Motortreiber - er macht die
# Form absichtsvoll und holt den Schwerpunkt naeher an die Flanschachse.
# Auslegerdurchmesser HERGELEITET: der NEMA-Flansch ist quadratisch, seine
# Ecken liegen auf dem Umkreis MOT_FLANSCH*sqrt(2). Der Ausleger muss diesen
# Umkreis aufnehmen, plus Wandstaerke fuer das Fraesen in Aluminium.
WAND_AUSL = 4.0                             # mm
AUSL_QUER = MOT_FLANSCH * 2 ** 0.5 + 2 * WAND_AUSL

# Squircle-Halbachsen aus Antrieb und Mechanik
# Der Antrieb kann erst NACH der Mechanik beginnen: die Zahnstangen belegen
# +-SCHL_B/2 um die Mittelebene. Diese Breite gehoert in die Halbachse.
SQ_A = SCHL_B / 2 + 3.0 + MOT_L + WAND_SQ                   # Y-Halbachse
SQ_C = max(SCHL_H + R_TEIL + WAND_SQ,
           MOT_FLANSCH * 2 ** 0.5 / 2 + WAND_SQ)            # Z-Halbachse
Y_MOT_INNEN = SCHL_B / 2 + 3.0                              # Motorsitz
Y_TRAEGER = SCHL_B / 2 + 8.0                                # zentraler Traeger
Y_AUSL_MOT = Y_MOT - 10.0 + MOT_L + 6.0     # Aussenkante Motorausleger
Y_AUSL_EL = 46.0                            # Laenge Elektronikausleger
R_AUSSEN = 10.0                             # Radius der senkrechten Aussenkanten
R_UEBER = 8.0                               # Radius am Uebergang zum Ausleger


# ================================================================ Bauteile
def gehaeuse():
    """Pos.4 - Funktionstraeger, EN AW-6082 T6, gefraest.

    WERKSTOFFGERECHTE TRENNUNG: nur was Kraft uebertraegt, ist aus Aluminium -
    Zahnstangenfuehrung, Ritzellagerung, Motorflansch, Verschraubung zum
    Schnellwechsler. Die Aussenform uebernimmt die Verkleidung (Pos.12) aus
    dem 3D-Druck; sie traegt keine Last und darf deshalb duennwandig sein.

    Ein massiver Squircle aus Aluminium waege 2,56 kg - der Greifer laege
    damit bei 83 %% der Robotertraglast. Getrennt sind es rund 0,8 kg.
    """
    p = Pos(0, 0, Z_KOERPER) * Box(GEH_X - 2 * WAND_SQ, 2 * Y_TRAEGER,
                                   H_KOERPER, align=C)
    p = fillet(p.edges().filter_by(Axis.Z), 6.0)

    # Motorflansch: Aufnahme fuer Getriebe und Zentrierung
    p += Pos(0, Y_MOT_INNEN, Z_ACHSE) * Rot(-90, 0, 0) * Cylinder(
        MOT_FLANSCH / 2 + 5, 14, align=CU)
    p -= Pos(0, Y_MOT_INNEN, Z_ACHSE) * Rot(-90, 0, 0) * Cylinder(
        MOT_FLANSCH / 2 - 3, 20, align=CU)

    # Fuehrungstaschen, je Zahnstange getrennt und in X begrenzt
    p -= Pos((RACK_VON + X_R) / 2, 0, Z_RACK_O) * Box(
        X_R - RACK_VON + 4, SCHL_B + 0.4, SCHL_H + H_FUSS + H_KOPF, align=C)
    p -= Pos((X_L - RACK_VON) / 2, 0, Z_TEIL_U - H_KOPF) * Box(
        X_R - RACK_VON + 4, SCHL_B + 0.4, SCHL_H + H_FUSS + H_KOPF, align=C)

    # Freiraum fuer die Stege zu den Backenflanschen
    for seite in (1, -1):
        x_m = seite * X_ZANGE
        p -= Pos(x_m, 0, Z_RACK_O + SCHL_H) * Box(
            26 + 2 * HUB + 2, SCHL_B + 0.4, Z_UNTEN - Z_RACK_O + 20, align=C)

    # Ritzelfreiraum und Lagerbohrung
    p -= Pos(0, 0, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        R_TEIL + H_KOPF + 1.0, B_ZAHN + 2, align=CC)
    p -= Pos(0, 0, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        D_WELLE / 2 + 0.1, 4 * Y_TRAEGER, align=CC)

    # Anschraubbild zum Schnellwechsler
    for i in range(4):
        a = radians(45 + 90 * i)
        p -= Pos(25.0 * cos(a), 25.0 * sin(a), Z_KOERPER - 5) * Cylinder(2.5, 20, align=C)
    return p


def verkleidung():
    """Pos.12 - Verkleidung, PA12 (SLS-Druck).

    Squircle-Profil (Superellipse, n = 4) als duennwandige Schale. Sie traegt
    keine Last, deshalb genuegen WAND_VERK Wandstaerke - im 3D-Druck ohne
    Mehraufwand herstellbar, waehrend dieselbe Form gefraest aus dem Vollen
    teuer und schwer waere.

    Oeffnungen: oben fuer den Schnellwechsler, unten fuer die Greiferzangen.
    """
    from build123d import Polyline, make_face, extrude, Plane

    def schale(a, c, laenge):
        k = Polyline(*[(y, z) for y, z in squircle(a, c)], close=True)
        return extrude(Plane.YZ * make_face(k), amount=laenge / 2, both=True)

    p = Pos(0, 0, Z_ACHSE) * schale(SQ_A, SQ_C, GEH_X)
    p -= Pos(0, 0, Z_ACHSE) * schale(SQ_A - WAND_VERK, SQ_C - WAND_VERK,
                                     GEH_X - 2 * WAND_VERK)

    # Freiraum fuer den Antrieb - er reicht bis nahe an die Schale
    p -= Pos(0, Y_MOT_INNEN, Z_ACHSE) * Rot(-90, 0, 0) * Cylinder(
        MOT_FLANSCH / 2 + 6, MOT_L + 4, align=CU)

    # Durchbruch oben fuer den Schnellwechsler
    p -= Pos(0, 0, Z_KOERPER - 10) * Cylinder(31, 30, align=C)
    # Durchbrueche unten fuer die Zangen
    for seite in (1, -1):
        p -= Pos(seite * X_ZANGE, 0, Z_UNTEN - 40) * Box(
            40 + 2 * HUB, SCHL_B + 26, 80, align=C)
    return p


def ritzel():
    """Pos.5 - Ritzel m=1, z=20, Achse waagerecht in Y."""
    p = Pos(0, 0, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        R_TEIL - H_FUSS, B_ZAHN, align=CC)
    teilung = pi * MODUL
    dicke = teilung / 2.0 - 0.12                 # Flankenspiel
    UEBERLAPP = 0.6                              # Zaehne greifen in die Nabe
    for i in range(Z_RITZEL):
        w = 360.0 * i / Z_RITZEL
        r = R_TEIL + (H_KOPF - H_FUSS) / 2.0 - UEBERLAPP / 2.0
        p += Pos(r * cos(radians(w)), 0, Z_ACHSE + r * sin(radians(w))) * \
            Rot(0, -w, 0) * Box(H_ZAHN + UEBERLAPP, B_ZAHN, dicke, align=CC)
    p -= Pos(0, 0, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        D_WELLE / 2, B_ZAHN + 2, align=CC)
    return p


def ritzelwelle():
    """Pos.6 - Ritzelwelle, im Gehaeuse gelagert, Abtrieb zum Getriebe."""
    # Endet buendig an der Anbauflaeche des Motors - der Getriebeabtrieb
    # kuppelt dort an, beide duerfen sich nicht durchdringen.
    return Pos(0, 0, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        D_WELLE / 2, 2 * (Y_MOT_INNEN + 1), align=CC)


def _zahnstange(oben, offen):
    """Zahnstange mit Steg und Anschraubflansch fuer eine Backe.

    oben=True  : obere Zahnstange, Zaehne nach unten, Backe bei +X
    oben=False : untere Zahnstange, Zaehne nach oben,  Backe bei -X
    """
    seite = 1 if oben else -1
    s = (HUB if offen else 0.0) * seite

    # Zahnunterkante (align=MIN). Der Zahn reicht vom Zahnfuss - der im
    # Koerper liegt - bis zum Kopfkreis am Ritzel. UEBERLAPP laesst ihn in den
    # Koerper eingreifen; beruehren sich beide nur tangential, verschmelzen
    # sie nicht und die Zahnstange bleibt in Einzelkoerper zerfallen.
    UEBERLAPP = 0.6
    if oben:
        z_koerper = Z_RACK_O
        # Zaehne ragen nach UNTEN zum Ritzel
        z_zahn = Z_TEIL_O - H_FUSS - UEBERLAPP
        x_von, x_bis = RACK_VON + s, RACK_BIS + s
    else:
        z_koerper = Z_RACK_U
        # Zaehne ragen nach OBEN zum Ritzel
        z_zahn = Z_TEIL_U - H_KOPF
        x_von, x_bis = -RACK_BIS + s, -RACK_VON + s

    p = Pos((x_von + x_bis) / 2, 0, z_koerper) * Box(
        x_bis - x_von, SCHL_B, SCHL_H, align=C)

    # Trapezzaehne zum Ritzel hin
    teilung = pi * MODUL
    dicke = teilung / 2.0 - 0.12
    n = int((ZAHN_BIS - ZAHN_VON) / teilung)
    for i in range(n + 1):
        xz = ZAHN_VON + i * teilung + s
        if not (x_von + 2 <= xz <= x_bis - 2):
            continue
        p += Pos(xz, 0, z_zahn) * Box(dicke, B_ZAHN, H_ZAHN + UEBERLAPP, align=C)

    # Steg nach unten zum Anschraubflansch
    x_mount = seite * X_ZANGE + s
    z_steg_von = z_koerper + SCHL_H if oben else Z_RACK_U + SCHL_H
    p += Pos(x_mount, 0, z_steg_von) * Box(
        26, SCHL_B, Z_UNTEN - z_steg_von, align=C)
    p += Pos(x_mount, 0, Z_UNTEN) * Box(30, SCHL_B + 10, T_FLANSCH, align=C)
    for dy in (-9, 9):
        p -= Pos(x_mount, dy, Z_UNTEN) * Cylinder(2.5, T_FLANSCH, align=C)
    return p


def zahnstange(seite, offen=False):
    """Pos.7 - Zahnstange mit Steg und Backenflansch (2x).

    seite = +1 : obere Zahnstange, Backe bei +X
    seite = -1 : untere Zahnstange, Backe bei -X
    """
    return _zahnstange(seite > 0, offen)


def motor():
    """Pos.8 - Servomotor mit Planetengetriebe und Haltebremse (Zukaufteil).

    NEMA 17 seitlich am Gehaeuse. Die Haltebremse ist zwingend: das
    Zahnstangengetriebe ist nicht selbsthemmend, bei Stromausfall wuerde das
    Bauteil sonst fallen.
    """
    y0 = Y_MOT_INNEN + 1.0
    p = Pos(0, y0 + MOT_L_GETRIEBE / 2, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        36.0 / 2, MOT_L_GETRIEBE, align=CC)                       # Getriebe
    p += Pos(0, y0 + MOT_L_GETRIEBE + MOT_L_MOTOR / 2, Z_ACHSE) * \
        Box(MOT_FLANSCH, MOT_L_MOTOR, MOT_FLANSCH, align=CC)      # Motor
    p += Pos(0, y0 + MOT_L_GETRIEBE + MOT_L_MOTOR + MOT_L_BREMSE / 2, Z_ACHSE) * \
        Rot(90, 0, 0) * Cylinder(38.0 / 2, MOT_L_BREMSE, align=CC)  # Bremse
    return p


if __name__ == "__main__":
    print("MECHANIK - %s" % P.GREIFER_TYP)
    print("  Motor     %s" % P.MOTOR_TYP)
    print("  Getriebe  i = %.0f  ->  Moment am Ritzel %.2f Nm"
          % (P.GETRIEBE_I, P.M_ABTRIEB))
    print("  Verzahnung m=%.1f, z=%d, b=%.0f -> Teilkreis Ø%.0f mm"
          % (MODUL, Z_RITZEL, B_ZAHN, 2 * R_TEIL))
    print("  Backenkraft %.1f N  (%.1f-fach ueber den erforderlichen %.1f N)"
          % (P.GREIFER_F_MAX, P.GREIFER_F_MAX / P.F_GREIF, P.F_GREIF))
    print("  Ritzelachse waagerecht bei z = %.1f, Motor seitlich ab y = %.0f"
          % (Z_ACHSE, Y_MOT))
    print()
    teile = [("Gehaeuse", gehaeuse(), 2.70), ("Ritzel", ritzel(), 7.85),
             ("Ritzelwelle", ritzelwelle(), 7.85),
             ("Zahnstange oben", zahnstange(1), 7.85),
             ("Zahnstange unten", zahnstange(-1), 7.85),
             ("Motoreinheit", motor(), 3.00)]
    mg = 0.0
    for n, k, rho in teile:
        v = k.volume / 1000.0
        m = v * rho / 1000.0
        mg += m
        print("  %-18s V = %8.2f cm3   m = %6.3f kg  (%d Koerper)"
              % (n, v, m, len(k.solids())))
    print("  %-18s %23s %6.3f kg" % ("Mechanik gesamt", "", mg))
