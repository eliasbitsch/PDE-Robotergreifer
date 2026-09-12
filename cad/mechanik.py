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
# Die Hoehenkette wird von INNEN nach AUSSEN aufgebaut: Verzahnung -> Zahn-
# stange -> Funktionstraeger -> Verkleidung. Kein Glied ist gesetzt, jedes
# folgt aus dem davor. Fruehere Fassungen hatten H_KOERPER = 62 mm fest
# eingetragen; das war 13 mm mehr, als die Mechanik braucht.
Z_KOERPER = 40.0                           # Unterkante Schnellwechsler

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

# Zahnstangen: Querschnitt SCHL_H (in Z) x SCHL_B (in Y)
SCHL_B = 16.0                               # = B_ZAHN + 2 x 4 mm Fuehrungsrand
# Hoehe des Zahnstangenkoerpers HERGELEITET aus zwei Bedingungen:
#
#  (a) Festigkeit. Die Backenkraft greift rund L_HEBEL unterhalb der
#      Zahnstange an. Das Kippmoment laeuft durch den Zahnstangenquerschnitt
#      am Steganschluss:  sigma = M / (SCHL_B * SCHL_H^2 / 6) <= Rp0,2 / S
#  (b) Gestaltung. Unter dem Zahnfuss muss mindestens noch einmal die volle
#      Zahnhoehe an Werkstoff stehen, sonst ist der Zahn nicht angebunden:
#      SCHL_H >= 2 * H_ZAHN
#
# Massgebend ist (b) - die Zahnstange ist also nicht kraft-, sondern
# gestaltbestimmt. Der aufgerundete Wert steht in SCHL_H.
RACK_RP02 = 260.0                           # MPa, EN AW-6082 T6
RACK_S = 2.0                                # - Sicherheit gegen Fliessen
L_HEBEL = 150.0                             # mm Zahnstangenmitte -> Backenmitte
_h_fest = (6 * P.F_ZANGE_AUSLEGUNG * L_HEBEL / SCHL_B / (RACK_RP02 / RACK_S)) ** 0.5
_h_gest = 2 * H_ZAHN
from math import ceil as _ceil
SCHL_H = float(_ceil(max(_h_fest, _h_gest)))   # auf volle mm aufgerundet
HUB = P.GREIFER_HUB

# Bauhoehe der Mechanik ab der Ritzelachse: bis zum Teilkreis, von dort um die
# Zahnfusshoehe in den Zahnstangenkoerper, dann dessen Hoehe.
H_MECH = R_TEIL + H_FUSS + SCHL_H
WAND_TRAEGER = 3.0                          # mm Decke/Boden des Funktionstraegers
H_MECH_GES = 2 * (H_MECH + WAND_TRAEGER)
# Zweite Bedingung: der Motor sitzt mit seinem Flansch am Traeger. Der
# NEMA-17-Flansch ist 42 mm hoch - mehr als die Mechanik braucht. Die Bauhoehe
# wird also NICHT von der Verzahnung bestimmt, sondern vom Motor. Kleiner ginge
# nur mit NEMA 14 (35 mm), der aber nur die 1,4-fache statt der geforderten
# 2,0-fachen Momentreserve haelt (siehe params.py).
H_MOTOR_GES = P.MOT_FLANSCH + 2 * WAND_TRAEGER
H_KOERPER = max(H_MECH_GES, H_MOTOR_GES)
Z_UNTEN = Z_KOERPER + H_KOERPER
T_FLANSCH = 10.0                            # M6 in Alu: 1,5 d Einschraubtiefe
Z_ZANGE_KOPF = Z_UNTEN + T_FLANSCH
T_ZANGE_KOPF = 10.0
Z_ZANGE = Z_ZANGE_KOPF + T_ZANGE_KOPF

# Ritzelachse waagerecht in Y, mittig im Gehaeuse
Z_ACHSE = Z_KOERPER + H_KOERPER / 2.0


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
MOT_L = P.MOT_L_GESAMT
Y_MOT = GEH_Y / 2                                            # Anbauflaeche

# ---------------------------------------------------------------- Squircle
# Die Aussenform ist eine Superellipse (Squircle):
#     |y/a|^n + |z/c|^n = 1
# n = 2 ergibt eine Ellipse, n -> unendlich ein Rechteck. Bei n = 4 entsteht
# die volle, weiche Form, die an Geraeten ueblich ist: fast rechteckige
# Flaechen mit stetig gekruemmten Ecken - anders als eine Verrundung, die
# zwischen Gerade und Kreisbogen einen Kruemmungssprung hat.
# Exponent: n = 4 ist die klassische Squircle-Form. Weil sich die Superellipse
# zu den Enden verjuengt, kostet ein kleines n Bauraum - der Antrieb muss ja
# hineinpassen. Gerechnet (siehe _halbachsen) ergibt sich die Bautiefe:
#     n = 4 -> 136 mm    n = 5 -> 127    n = 6 -> 122    n = 8 -> 117
# Gewaehlt ist n = 6: 14 mm schlanker als n = 4 und optisch noch deutlich vom
# Rechteck entfernt. Der Wert ist der einzige Stellhebel dieser Abwaegung.
SQ_N = 6.0                                  # Exponent der Superellipse
SQ_PUNKTE = 96                              # Stuetzstellen des Spline-Profils
                                            # (Flaechenfehler < 0,05 % gegen 240)

# Halbachsen HERGELEITET, nicht gewaehlt:
#   a  Baulaenge des Antriebs + Wand; der Antrieb muss vollstaendig hinein,
#      sonst steht wieder etwas heraus
#   c  Bauhoehe der Mechanik (2 Zahnstangen + Ritzel) bzw. Umkreis des
#      Motorflansches - der groessere Wert bestimmt
WAND_SQ = 6.0                               # mm Wandstaerke Alu, gefraest
WAND_VERK = 3.0                             # mm Wandstaerke Verkleidung, SLS-Druck


def squircle(a_p, c, a_m=None, n=SQ_N, punkte=SQ_PUNKTE):
    """Punkte einer Superellipse, in +y und -y unterschiedlich weit.

    a_m = a_p ergibt die symmetrische Form. Sind die Halbachsen verschieden,
    treffen sich beide Haelften bei y = 0 auf z = +-c. Dort verlaeuft die
    Superellipse waagerecht (dz/dy = 0), die Tangente ist also stetig - die
    Form bleibt an der Nahtstelle knickfrei.
    """
    from math import cos, sin, pi, copysign
    a_m = a_p if a_m is None else a_m
    aus = []
    for i in range(punkte):
        t = 2 * pi * i / punkte
        ct, st = cos(t), sin(t)
        a = a_p if ct >= 0 else a_m
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
Y_MOT_INNEN = SCHL_B / 2 + 3.0                              # Motorsitz  (+Y)
Y_BRE_INNEN = -(SCHL_B / 2 + 3.0)                           # Bremssitz  (-Y)
Y_TRAEGER = SCHL_B / 2 + 8.0                                # zentraler Traeger

# HALBACHSEN AUS DER EINSCHLUSSBEDINGUNG, nicht aus einer Summe.
#
# Eine Superellipse verjuengt sich zu ihren Enden hin. Am Ende des Motors ist
# die Schale also nicht mehr so hoch wie in der Mitte - eine simple Addition
# "Sitz + Antriebslaenge + Wand" liefert deshalb ein zu kleines Profil, in dem
# der Motor mit seinen Ecken in der Wand steckt. Genau das ist passiert.
#
# Richtig ist: jedes Einbauteil liefert einen Eckpunkt (y, z), den die INNERE
# Superellipse noch umschliessen muss:
#
#     (y/a)^n + (z/c)^n <= 1
#
# Nach a aufgeloest und ueber alle Einbauteile maximiert. Weil c von denselben
# Punkten abhaengt, wird beides iterativ bestimmt.
#
# Der Exponent n steuert dabei den Handel zwischen Form und Bauraum: je
# groesser n, desto rechteckiger das Profil und desto weniger verjuengt es
# sich - und desto schlanker darf es bei gleichem Inhalt sein.
Y_MOT_ENDE = SCHL_B / 2 + 3.0 + 1.0 + MOT_L                 # Aussenkante Motor
Y_BRE_ENDE = SCHL_B / 2 + 3.0 + 1.0 + P.BREMSE_L            # Aussenkante Bremse
SPIEL_VERK = 1.0                                            # mm Luft zum Einbau

#                     y            z                        Seite
EINBAU_P = [(Y_TRAEGER,     H_KOERPER / 2),                 # Funktionstraeger
            (Y_MOT_ENDE,    MOT_FLANSCH / 2)]               # Motor
EINBAU_M = [(Y_TRAEGER,     H_KOERPER / 2),                 # Funktionstraeger
            (Y_BRE_ENDE,    P.BREMSE_D / 2)]                # Haltebremse


def _halbachsen(n=SQ_N):
    """Innere Halbachsen (a+, a-, c), die alle Einbauteile umschliessen."""
    pkt = [(y + SPIEL_VERK, z + SPIEL_VERK) for y, z in EINBAU_P + EINBAU_M]
    c = max(z for _, z in pkt) + 0.1
    a_p = a_m = max(y for y, _ in pkt) + 0.1
    for _ in range(200):
        def loese_a(liste):
            a = 0.0
            for y, z in liste:
                rest = 1.0 - (z / c) ** n
                a = max(a, y / rest ** (1.0 / n) if rest > 1e-9 else 1e9)
            return a
        a_p = loese_a([(y + SPIEL_VERK, z + SPIEL_VERK) for y, z in EINBAU_P])
        a_m = loese_a([(y + SPIEL_VERK, z + SPIEL_VERK) for y, z in EINBAU_M])
        c_neu = c
        for (y, z), a in [(pkt[0], a_p), (pkt[1], a_p), (pkt[2], a_m), (pkt[3], a_m)]:
            rest = 1.0 - (y / a) ** n
            if rest > 1e-9:
                c_neu = max(c_neu, z / rest ** (1.0 / n))
        if abs(c_neu - c) < 1e-6:
            break
        c = c_neu
    return a_p, a_m, c


_A_P, _A_M, _C = _halbachsen()
SQ_C = _C + WAND_VERK
SQ_A_P = _A_P + WAND_VERK                                   # Antriebsseite
SQ_A_M = _A_M + WAND_VERK                                   # Bremsseite
SQ_A = max(SQ_A_P, SQ_A_M)                                  # fuer Nachweise
# Z-Halbachse: die Schale muss den Funktionstraeger mit Spiel umschliessen.
# Der NEMA-Flansch ist quadratisch und steht ACHSPARALLEL im Gehaeuse - nicht
# auf der Ecke. Massgebend ist deshalb MOT_FLANSCH/2, nicht die Diagonale.
# Die frueher angesetzte Diagonale hat die Verkleidung um 17 mm zu hoch
# gemacht; das war der groesste Einzelfehler in der Hoehenkette.
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
        H_KOERPER / 2, 14, align=CU)
    p -= Pos(0, Y_MOT_INNEN, Z_ACHSE) * Rot(-90, 0, 0) * Cylinder(
        MOT_FLANSCH / 2 - 3, 20, align=CU)

    # Bremsflansch auf der Gegenseite, gleiche Bauart
    p += Pos(0, Y_BRE_INNEN, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        H_KOERPER / 2, 14, align=CU)
    p -= Pos(0, Y_BRE_INNEN, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        P.BREMSE_D / 2 + 0.2, 20, align=CU)   # Aufnahmebohrung, H7-Sitz

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
    from build123d import Spline, make_face, extrude, Plane

    def schale(a_p, a_m, c, laenge):
        # Periodischer Spline durch die Stuetzstellen, KEIN Polygonzug.
        # Ein 240-Eck erzeugt 240 Regelflaechen; in der Zeichnung projiziert
        # jede davon eine eigene Kante, die Ansichten liefen schwarz zu.
        # Der Spline ergibt eine einzige Flaeche - und die STEP-Datei
        # beschreibt damit die Kurve, statt sie zu facettieren.
        k = Spline(*[(y, z) for y, z in squircle(a_p, c, a_m, punkte=SQ_PUNKTE)],
                   periodic=True)
        return extrude(Plane.YZ * make_face(k), amount=laenge / 2, both=True)

    p = Pos(0, 0, Z_ACHSE) * schale(SQ_A_P, SQ_A_M, SQ_C, GEH_X)
    p -= Pos(0, 0, Z_ACHSE) * schale(SQ_A_P - WAND_VERK, SQ_A_M - WAND_VERK,
                                     SQ_C - WAND_VERK, GEH_X - 2 * WAND_VERK)

    # Keine Freistellung fuer Motor oder Bremse: die Halbachsen sind so
    # bestimmt, dass beide von selbst hineinpassen (siehe _halbachsen). Eine
    # zusaetzliche Tasche wuerde die Schale nur durchbrechen - genau das ist
    # in der Fassung davor passiert, der Motor war durch das Loch zu sehen.

    # Durchbruch oben fuer den Schnellwechsler: nur durch die Deckflaeche,
    # Ø58 Zukaufteil plus 2 mm Fuge.
    z_deckel = Z_ACHSE - SQ_C
    p -= Pos(0, 0, z_deckel - 5) * Cylinder(
        58 / 2 + 2, (Z_KOERPER + 1) - (z_deckel - 5), align=C)

    # Durchbrueche unten fuer die Zangen. Sie muessen genau den Steg der
    # Zahnstange freistellen - vom Beginn des Stegs bis unter die Schale -
    # und den Backenhub nach beiden Seiten zulassen.
    z_oben = Z_RACK_O + SCHL_H                  # dort beginnt der obere Steg
    z_unten = Z_ACHSE + SQ_C + 1
    # In x nur so breit wie der Steg auf seinem Weg: von der geschlossenen
    # Stellung (x = X_ZANGE) bis zur offenen (x = X_ZANGE + HUB), je 13 mm
    # halbe Stegbreite plus 2 mm Fuge. Frueher war der Schlitz mittig auf
    # X_ZANGE und reichte damit bis an den Motor - man sah ihn durch die Fuge.
    x_von = X_ZANGE - 13.0 - 2.0
    x_bis = X_ZANGE + HUB + 13.0 + 2.0
    for seite in (1, -1):
        p -= Pos(seite * (x_von + x_bis) / 2, 0, (z_oben + z_unten) / 2) * Box(
            x_bis - x_von, SCHL_B + 10 + 4, z_unten - z_oben, align=CC)
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
    y_p, y_m = Y_MOT_INNEN + 1.0, Y_BRE_INNEN - 1.0
    return Pos(0, (y_p + y_m) / 2, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        D_WELLE / 2, y_p - y_m, align=CC)


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
    return p


def bremse():
    """Pos.12 - Federkraft-Haltebremse auf dem freien Ritzelwellenende.

    Stromlos eingefallen; das Zahnstangengetriebe ist nicht selbsthemmend.

    Sie sitzt jetzt VOR dem Getriebe und muss deshalb das volle Ritzelmoment
    halten statt nur ein Fuenftel davon - sie wird dadurch groesser. Dafuer
    nutzt sie den Raum, der auf der Gegenseite der Ritzelachse ohnehin frei
    war: die Bautiefe sinkt von 176 auf 114 mm.

    Zweiter Vorteil: sie greift direkt am Ritzel an, nicht hinter fuenf
    Getriebestufen. Das Getriebespiel liegt damit nicht mehr zwischen Bremse
    und Last.
    """
    y0 = Y_BRE_INNEN - 1.0
    return Pos(0, y0 - P.BREMSE_L / 2, Z_ACHSE) * Rot(90, 0, 0) * Cylinder(
        P.BREMSE_D / 2, P.BREMSE_L, align=CC)


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
             ("Motoreinheit", motor(), 3.00),
             ("Haltebremse", bremse(), 3.00)]
    mg = 0.0
    for n, k, rho in teile:
        v = k.volume / 1000.0
        m = v * rho / 1000.0
        mg += m
        print("  %-18s V = %8.2f cm3   m = %6.3f kg  (%d Koerper)"
              % (n, v, m, len(k.solids())))
    print("  %-18s %23s %6.3f kg" % ("Mechanik gesamt", "", mg))
