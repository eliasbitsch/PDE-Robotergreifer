"""Abgabepunkt 3 (Teil 2) - Variantenvergleich der Greifmechanik.

Verglichen werden drei Wirkprinzipien fuer den geforderten Parallelgriff:
  A  Zahnstange-Ritzel, pneumatisch
  B  Keilhakengetriebe, pneumatisch
  C  Trapezgewindespindel, elektrisch

Bewertet wird quantitativ (Bauraum, Masse, Kraftverlauf, Selbsthemmung,
Stellzeit) und anschliessend gewichtet nach VDI 2225.

Auslegungsfall (aus params.py):
  erforderliche Greifkraft  F_GREIF je Backe
  erforderlicher Backenhub  GREIFER_HUB je Backe
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params as P

# ---------------------------------------------------------------- Randbedingungen
P_LUFT = 0.6                 # N/mm^2  = 6 bar Betriebsdruck
MU_FUEHRUNG = 0.10           # -  Gleitreibung gehaertet/gehaertet, geschmiert
ETA_ZAHN = 0.92              # -  Wirkungsgrad Zahnstange-Ritzel
S_BACKE = P.GREIFER_HUB      # mm  Hub je Backe
F_SOLL = P.F_GREIF           # N   erforderliche Greifkraft je Backe
T_SCHLIESS = P.T_GREIFEN     # s

RHO_STAHL = 7.85e-3          # g/mm^3
RHO_ALU = 2.70e-3

# Normreihe Pneumatikzylinder
ZYLINDER = [12, 16, 20, 25, 32, 40]

# Mindest-Baubreite. Die Backen sitzen beim Greifabstand von GREIF_ABSTAND auf
# x = +-(GREIF_ABSTAND/2 + Belag + Zangendicke/2); der Mechanismus muss diese
# Spanne ueberbruecken. Das gilt fuer JEDES Wirkprinzip und darf deshalb keiner
# Variante als Vorteil angerechnet werden.
X_BACKE = P.GREIF_ABSTAND / 2.0 + 8.0 + P.ZANGE_H / 2.0
BREITE_MIN = 2 * X_BACKE + 30.0


def bauraum(laenge, breite, hoehe):
    """Bauraum mit der aufgabenbedingten Mindestbreite."""
    return (max(laenge, BREITE_MIN), breite, hoehe)


def zylinderkraft(D):
    """Theoretische Druckkraft eines doppeltwirkenden Zylinders [N]."""
    return P_LUFT * np.pi / 4.0 * D ** 2


def waehle_zylinder(F_noetig):
    for D in ZYLINDER:
        if zylinderkraft(D) >= F_noetig:
            return D, zylinderkraft(D)
    return ZYLINDER[-1], zylinderkraft(ZYLINDER[-1])


# ================================================================ Variante A
def variante_A():
    """Zahnstange-Ritzel.

    Der Zylinder treibt Zahnstange 1 (Backe 1). Das Ritzel leitet die Kraft
    auf Zahnstange 2 (Backe 2) um, dadurch laufen beide Backen zwangslaeufig
    synchron. Im Gleichgewicht muss der Kolben beide Backenkraefte aufbringen:
        F_Kolben = 2 * F_Backe / eta
    """
    F_noetig = 2 * F_SOLL / ETA_ZAHN
    D, F_K = waehle_zylinder(F_noetig)
    F_backe = ETA_ZAHN * F_K / 2.0

    # Verzahnung: Modul 1, z = 16 -> Teilkreis 16 mm
    modul, z = 1.0, 16
    r_teil = modul * z / 2.0
    b_zahn = 8.0                       # mm Zahnbreite
    F_t = F_backe                      # Umfangskraft am Ritzel
    # Zahnfussspannung, vereinfacht nach Roloff/Matek (Y_Fa*Y_Sa ~ 4,3 bei z=16)
    sigma_F = F_t / (b_zahn * modul) * 4.3

    hub_kolben = S_BACKE               # 1:1, Zahnstange laeuft mit der Backe
    laenge = hub_kolben + 2 * D + 30   # Zylinder + Deckel + Anschluesse
    breite = 2 * (r_teil + 12) + 20
    hoehe = 2 * r_teil + 26

    # Masse: Gehaeuse Alu (als Hohlkasten, 60 % gefuellt), Innenteile Stahl
    # Masse aus dem TATSAECHLICHEN Bauraum, nicht aus der antriebsseitigen
    # Laenge - sonst bekommt die Variante einen Massenvorteil angerechnet, den
    # die Aufgabenstellung gar nicht zulaesst.
    l, b, h = bauraum(laenge, breite, hoehe)
    m_geh = l * b * h * 0.35 * RHO_ALU / 1000.0
    m_innen = (2 * b_zahn * 10 * (l - 20) + np.pi / 4 * D ** 2 * hub_kolben) \
        * RHO_STAHL / 1000.0

    return dict(
        name="A  Zahnstange-Ritzel (pneumatisch)",
        D=D, F_K=F_K, F_backe=F_backe, reserve=F_backe / F_SOLL,
        selbsthemmend=False,
        hub_antrieb=hub_kolben,
        bauraum=bauraum(laenge, breite, hoehe),
        masse=m_geh + m_innen,
        stellzeit=T_SCHLIESS,
        rechnung="Modul %.1f, z=%d, b=%.0f mm -> sigma_F = %.0f N/mm2"
                 % (modul, z, b_zahn, sigma_F),
        synchron="zwangslaeufig ueber das Ritzel",
        sigma_F=sigma_F,
    )


# ================================================================ Variante B
def variante_B(alpha_grad):
    """Keilhakengetriebe.

    Der Kolben bewegt sich axial, ein Keil mit dem Winkel alpha setzt das in
    die Querbewegung der Backen um.
        Querhub   s_q  = s_ax * tan(alpha)
        Kraft     F_Backe = F_Kolben / (2 * tan(alpha + rho)),  rho = arctan(mu)
    Selbsthemmung liegt vor, solange tan(alpha) < mu.
    """
    a = np.deg2rad(alpha_grad)
    rho = np.arctan(MU_FUEHRUNG)
    uebersetzung = 1.0 / (2.0 * np.tan(a + rho))

    F_noetig = F_SOLL / uebersetzung
    D, F_K = waehle_zylinder(F_noetig)
    F_backe = F_K * uebersetzung

    hub_ax = S_BACKE / np.tan(a)
    selbsthemmend = np.tan(a) < MU_FUEHRUNG

    laenge = hub_ax + 2 * D + 30
    breite = 2 * (S_BACKE + 24) + 20
    hoehe = D + 40

    m_geh = laenge * breite * hoehe * 0.35 * RHO_ALU / 1000.0
    m_innen = (np.pi / 4 * D ** 2 * hub_ax + 2 * 18 * 14 * (S_BACKE + 40)) \
        * RHO_STAHL / 1000.0

    return dict(
        name="B  Keilhaken %d Grad (pneumatisch)" % alpha_grad,
        D=D, F_K=F_K, F_backe=F_backe, reserve=F_backe / F_SOLL,
        selbsthemmend=selbsthemmend,
        hub_antrieb=hub_ax,
        bauraum=bauraum(laenge, breite, hoehe),
        masse=m_geh + m_innen,
        stellzeit=T_SCHLIESS,
        rechnung="i = 1/(2*tan(%d+%.1f)) = %.2f ; tan(alpha) = %.3f %s mu = %.2f"
                 % (alpha_grad, np.rad2deg(rho), uebersetzung, np.tan(a),
                    "<" if selbsthemmend else ">", MU_FUEHRUNG),
        synchron="zwangslaeufig ueber den Keil",
        alpha=alpha_grad,
    )


# ================================================================ Variante C
def variante_C():
    """Trapezgewindespindel, elektrisch.

    Linksgewinde / Rechtsgewinde auf einer Spindel -> beide Backen laufen
    gegenlaeufig und synchron. Selbsthemmung, wenn tan(phi) < mu.
    """
    d2, steigung = 8.5, 2.0            # Tr10x2
    phi = np.arctan(steigung / (np.pi * d2))
    rho = np.arctan(MU_FUEHRUNG)
    selbsthemmend = np.tan(phi) < MU_FUEHRUNG

    F_backe = 300.0                    # frei waehlbar, hier Motormoment-begrenzt
    M_an = F_backe * d2 / 2.0 * np.tan(phi + rho) / 1000.0   # Nm

    n_noetig = (S_BACKE / steigung) / T_SCHLIESS * 60.0       # 1/min

    laenge = S_BACKE + 40 + 55         # Spindel + Motor
    breite = 70.0
    hoehe = 60.0
    m_motor = 0.55                     # kg, Schrittmotor NEMA 17 + Getriebe
    l, b, h = bauraum(laenge, breite, hoehe)
    m_geh = l * b * h * 0.35 * RHO_ALU / 1000.0
    m_innen = (np.pi / 4 * 10 ** 2 * (l - 20)
               + 2 * 25 * 25 * 20 * 0.6) * RHO_STAHL / 1000.0

    return dict(
        name="C  Trapezgewindespindel (elektrisch)",
        D=None, F_K=None, F_backe=F_backe, reserve=F_backe / F_SOLL,
        selbsthemmend=selbsthemmend,
        hub_antrieb=S_BACKE,
        bauraum=bauraum(laenge, breite, hoehe),
        masse=m_geh + m_innen + m_motor,
        stellzeit=T_SCHLIESS,
        rechnung="Tr10x2: phi = %.1f Grad, M_an = %.2f Nm, n = %.0f 1/min"
                 % (np.rad2deg(phi), M_an, n_noetig),
        synchron="zwangslaeufig ueber Links-/Rechtsgewinde",
        drehzahl=n_noetig,
    )


# ================================================================ Bewertung
# (Kriterium, Gewicht) - Summe der Gewichte = 1
# Gewichte aus der Aufgabenstellung begruendet:
#  - Masse geht direkt in die Robotertraglast (6 kg) ein -> hoch
#  - Halten bei Energieausfall ist ein Sicherheitsthema -> hoch
#  - Schnellwechselsystem ist in der Angabe ausdruecklich gefordert -> hoch
#  - Regelbarkeit der Greifkraft bringt bei genau EINEM Bauteiltyp kaum
#    Nutzen und wird deshalb niedrig gewichtet
# ENERGIEKOSTEN sind bewusst KEIN Kriterium: nachgerechnet ergibt der
# Ø16-Zylinder 97 Nm3 Luft im Jahr, also 1,46-2,92 EUR gegenueber 1,07 EUR
# Strom beim Servo. Bei dieser Zylindergroesse traegt das Argument nicht.
KRITERIEN = [
    ("Bauraum",                   0.12),
    ("Masse",                     0.20),
    ("Halten bei Energieausfall", 0.20),
    ("Schnellwechseltauglichkeit", 0.18),
    ("Fertigungsaufwand",         0.15),
    ("Geraeuschentwicklung",      0.10),
    ("Regelbarkeit Greifkraft",   0.05),
]


def punkte(v):
    """Technische Wertigkeit 0..4 nach VDI 2225."""
    art = v["name"][0]
    vol = np.prod(v["bauraum"]) / 1000.0                   # cm^3
    p_bau = float(np.interp(vol, [150, 300, 500, 900], [4, 3, 2, 0]))
    p_mas = float(np.interp(v["masse"], [0.2, 0.5, 1.0, 1.8], [4, 3, 2, 0]))

    # Halten bei Energieausfall:
    #   selbsthemmendes Getriebe haelt ohne Hilfsmittel            -> 4
    #   Pneumatik mit Rueckschlagventil am Greifer haelt bis zur
    #   Leckage, ist aber Stand der Technik und zulaessig          -> 3
    p_sic = 4 if v["selbsthemmend"] else 3

    # Schnellwechsel: Luftkupplung ist einfach und robust. Elektrische
    # Kontakte im Wechsler sind aufwendiger, aber als Serienmodul (Schunk SWS,
    # ATI) Stand der Technik - die fruehere Bewertung mit 1 war zu hart.
    p_wex = {"A": 4, "B": 4, "C": 2}[art]

    # Fertigung: Verzahnung ist Normgeometrie und als Zukaufteil verfuegbar.
    # Eine Spindel mit Links- UND Rechtsgewinde ist ein Sonderteil.
    p_fer = {"A": 3, "B": 1, "C": 2}[art]

    # Geraeusch: Pneumatik-Abluft liegt bei rund 80 dB(A) und laesst sich mit
    # Schalldaempfer entschaerfen; ein Servoantrieb ist praktisch lautlos.
    p_lrm = {"A": 2, "B": 2, "C": 4}[art]

    p_reg = {"A": 1, "B": 1, "C": 4}[art]
    return dict(zip([k for k, _ in KRITERIEN],
                    [p_bau, p_mas, p_sic, p_wex, p_fer, p_lrm, p_reg]))


def main():
    print("VARIANTENVERGLEICH GREIFMECHANIK")
    print("Gruppe %d, Bauteil %s\n" % (P.GRUPPE, P.BAUTEIL))
    print("AUSLEGUNGSFALL")
    print("  erforderliche Greifkraft  %.1f N je Backe" % F_SOLL)
    print("  erforderlicher Backenhub  %.1f mm je Backe" % S_BACKE)
    print("  Betriebsdruck             %.1f bar" % (P_LUFT * 10))
    print("  Reibwert Fuehrung         mu = %.2f" % MU_FUEHRUNG)

    varianten = [variante_A(), variante_B(20), variante_B(6), variante_C()]

    print("\n" + "=" * 96)
    for v in varianten:
        l, b, h = v["bauraum"]
        print("\n%s" % v["name"])
        if v["D"]:
            print("  Zylinder            Ø%d mm -> F_Kolben = %.0f N" % (v["D"], v["F_K"]))
        print("  Greifkraft je Backe %.0f N   (%.1f-fache Anforderung)"
              % (v["F_backe"], v["reserve"]))
        print("  Antriebshub         %.0f mm  fuer %.0f mm Backenhub"
              % (v["hub_antrieb"], S_BACKE))
        print("  Bauraum             %.0f x %.0f x %.0f mm = %.0f cm3"
              % (l, b, h, l * b * h / 1000))
        print("  Masse (geschaetzt)  %.2f kg" % v["masse"])
        print("  Selbsthemmend       %s" % ("JA" if v["selbsthemmend"] else "NEIN"))
        print("  Synchronisierung    %s" % v["synchron"])
        print("  Rechnung            %s" % v["rechnung"])

    # ---------------------------------------------------------------- Matrix
    print("\n" + "=" * 96)
    print("BEWERTUNG NACH VDI 2225   (0 = unbefriedigend ... 4 = sehr gut)")
    print("=" * 96)
    kopf = "%-30s" % "Kriterium" + "%7s" % "Gew."
    for v in varianten:
        kopf += "%10s" % v["name"][0:6].strip()
    print(kopf)
    print("-" * 96)

    pl = [punkte(v) for v in varianten]
    summen = np.zeros(len(varianten))
    for krit, gew in KRITERIEN:
        zeile = "%-30s%7.2f" % (krit, gew)
        for i, p in enumerate(pl):
            zeile += "%10.1f" % p[krit]
            summen[i] += gew * p[krit]
        print(zeile)
    print("-" * 96)
    zeile = "%-30s%7s" % ("gewichtete Wertigkeit", "")
    for s in summen:
        zeile += "%10.2f" % s
    print(zeile)
    zeile = "%-30s%7s" % ("technische Wertigkeit x", "")
    for s in summen:
        zeile += "%10.2f" % (s / 4.0)
    print(zeile)

    i = int(np.argmax(summen))
    print("\nERGEBNIS")
    print("  Beste Variante: %s  (x = %.2f)" % (varianten[i]["name"], summen[i] / 4))
    return varianten, summen


if __name__ == "__main__":
    main()
