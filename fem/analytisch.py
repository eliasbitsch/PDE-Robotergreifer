"""Abgabepunkt 5 - Analytische Festigkeitsberechnung der Greiferzange.

Modell: Kragarm mit Rechteckquerschnitt, eingespannt am Anschraubkopf,
belastet durch die Greifkraft, die ueber die Weichbacke flaechig eingeleitet wird.

Lokales Koordinatensystem (wie in out/step/Greiferzange_FEM.step):
  z = 0 ... 10    Anschraubkopf (Einspannung)
  z = 10 ... 130  Kragarm, Querschnitt ZANGE_B (y) x ZANGE_H (x)
  z = 70 ... 130  Backentasche, dort greift die Greifkraft in x-Richtung an

Massgeblicher Lastfall ist die volle Zylinderkraft des Greifers (Backen fahren
auf ein Hindernis), nicht die zum Halten noetige Greifkraft.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cad"))
import params as P

# ---------------------------------------------------------------- Geometrie
Z_EINSPANNUNG = 10.0                          # mm, Wurzel des Kragarms
Z_LAST_VON = 10.0 + P.ZANGE_L - P.BACKE_LAENGE   # 70 mm
Z_LAST_BIS = 10.0 + P.ZANGE_L                    # 130 mm
Z_RESULTIERENDE = (Z_LAST_VON + Z_LAST_BIS) / 2.0   # 100 mm
Z_SPITZE = Z_LAST_BIS

A_HEBEL = Z_RESULTIERENDE - Z_EINSPANNUNG     # mm, wirksamer Hebelarm
L_FREI = Z_SPITZE - Z_EINSPANNUNG             # mm, freie Kraglaenge

B, H = P.ZANGE_B, P.ZANGE_H                   # mm
A_QUER = B * H                                # mm^2
W_B = B * H ** 2 / 6.0                        # mm^3  Widerstandsmoment
I_Y = B * H ** 3 / 12.0                       # mm^4  Flaechentraegheitsmoment

# ---------------------------------------------------------------- Kerbwirkung
# Abgesetzter Flachstab unter Biegung (Roloff/Matek, Diagramm):
#   D = ZANGE_H + 12 (Kopfbreite), d = ZANGE_H, r = ZANGE_FILLET
D_KOPF = P.ZANGE_H + 12.0
VERH_D_d = D_KOPF / P.ZANGE_H
VERH_r_d = P.ZANGE_FILLET / P.ZANGE_H
ALPHA_K = 1.62          # abgelesen fuer D/d = 2,2 und r/d = 0,3


def rechne(F, bez):
    M = F * A_HEBEL                           # Nmm
    sig_nenn = M / W_B                        # MPa
    sig_max = ALPHA_K * sig_nenn              # MPa, mit Kerbwirkung
    tau = 1.5 * F / A_QUER                    # MPa, parabolische Schubverteilung
    # Durchbiegung: Einzelkraft im Schwerpunkt der Lastflaeche
    f_last = F * A_HEBEL ** 3 / (3.0 * P.ZANGE_E * I_Y)
    f_spitze = F * A_HEBEL ** 2 / (6.0 * P.ZANGE_E * I_Y) * (3.0 * L_FREI - A_HEBEL)
    S_vorh = P.ZANGE_RP02 / sig_max

    print("\n%s   F = %.1f N je Backe" % (bez, F))
    print("  Biegemoment Einspannung  M     = %8.0f Nmm" % M)
    print("  Nennbiegespannung        sig_n = %8.2f MPa" % sig_nenn)
    print("  mit Kerbwirkung a_k=%.2f  sig   = %8.2f MPa" % (ALPHA_K, sig_max))
    print("  Schubspannung            tau   = %8.2f MPa  (%.1f %% von sig)"
          % (tau, 100 * tau / sig_max))
    print("  Durchbiegung Kraftangriff f     = %8.3f mm" % f_last)
    print("  Durchbiegung Spitze       f_max = %8.3f mm" % f_spitze)
    print("  Sicherheit gegen Fliessen S     = %8.2f  (zul. %.1f) -> %s"
          % (S_vorh, P.ZANGE_S_ZUL, "OK" if S_vorh >= P.ZANGE_S_ZUL else "NICHT AUSREICHEND"))
    return dict(F=F, M=M, sig_nenn=sig_nenn, sig_max=sig_max, tau=tau,
                f_last=f_last, f_spitze=f_spitze, S=S_vorh)


def main():
    print("ANALYTISCHE FESTIGKEITSBERECHNUNG GREIFERZANGE")
    print("Gruppe %d, Bauteil %s" % (P.GRUPPE, P.BAUTEIL))
    print()
    print("WERKSTOFF  %s" % P.ZANGE_WERKSTOFF)
    print("  E = %.0f MPa   nu = %.2f   Rp0,2 = %.0f MPa" % (P.ZANGE_E, P.ZANGE_NU, P.ZANGE_RP02))
    print()
    print("QUERSCHNITT (Kragarm)")
    print("  b x h    = %.0f x %.0f mm      A  = %.0f mm2" % (B, H, A_QUER))
    print("  W_b      = %.1f mm3           I_y = %.1f mm4" % (W_B, I_Y))
    print("  Hebelarm a = %.0f mm   freie Laenge l = %.0f mm" % (A_HEBEL, L_FREI))
    print("  Kerbe: D/d = %.2f, r/d = %.2f -> alpha_k = %.2f" % (VERH_D_d, VERH_r_d, ALPHA_K))

    r1 = rechne(P.F_GREIF, "LASTFALL 1 - erforderliche Greifkraft (Bauteil halten)")
    r2 = rechne(P.F_ZANGE_AUSLEGUNG, "LASTFALL 2 - volle Zylinderkraft (MASSGEBLICH)")

    print("\nERGEBNIS")
    print("  Auslegung erfolgt nach Lastfall 2.")
    print("  sig_max = %.1f MPa < sig_zul = %.0f MPa, Sicherheit %.2f."
          % (r2["sig_max"], P.ZANGE_SIGMA_ZUL, r2["S"]))
    print("  Die Durchbiegung von %.3f mm an der Backe ist gegenueber dem"
          % r2["f_spitze"])
    print("  Backenhub von %.1f mm vernachlaessigbar (%.1f %%)."
          % (P.GREIFER_HUB, 100 * r2["f_spitze"] / P.GREIFER_HUB))
    print("\n  Vergleichswerte fuer die FEM (Lastfall 2):")
    print("    sig_v,max  %.2f MPa   (Kerbgrund, Einspannung)" % r2["sig_max"])
    print("    u_max      %.3f mm    (Spitze, x-Richtung)" % r2["f_spitze"])
    return r2


if __name__ == "__main__":
    main()
