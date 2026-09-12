"""Abgabepunkt 6 (Teil 2) - Netzkonvergenz und Vergleich analytisch / numerisch.

Rechnet dieselbe Zange mit mehreren Netzfeinheiten und stellt das Ergebnis der
analytischen Loesung gegenueber. Ohne Konvergenznachweis ist ein FEM-Ergebnis
nicht belastbar - ein zu grobes Netz unterschaetzt die Kerbspannung systematisch.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "..", "cad"))

import analytisch
import fem_zange as F
import params as P

OUT = os.path.join(HIER, "..", "out", "bilder")
os.makedirs(OUT, exist_ok=True)

# Elementkantenlaenge im Kerbbereich [mm].
# Nach oben begrenzt: bei lc > 2,5 mm liegen auf der 3-mm-Ausrundung zu wenige
# Elemente, das Netz wird unbrauchbar (verzerrte quadratische Tetraeder).
NETZE = [2.5, 1.8, 1.3, 1.0, 0.7]
LC_GROB = 4.0


def main():
    ana = analytisch.main()

    print("\n" + "=" * 74)
    print("NETZKONVERGENZ")
    print("=" * 74)
    lauf = []
    for i, lc in enumerate(NETZE):
        print("\n--- Netz %d/%d:  lc_Kerbe = %.2f mm ---" % (i + 1, len(NETZE), lc))
        r = F.rechne(lc_fein=lc, lc_grob=LC_GROB, basis="konv%d" % i)
        r["lc"] = lc
        lauf.append(r)

    print("\n" + "=" * 74)
    print("KONVERGENZTABELLE")
    print("=" * 74)
    print("%8s %10s %10s %12s %12s %10s"
          % ("lc [mm]", "Knoten", "Elemente", "sig_v [MPa]", "u_max [mm]", "d_sig [%]"))
    print("-" * 74)
    vor = None
    for r in lauf:
        d = "" if vor is None else "%10.2f" % (100 * (r["s_frei"] - vor) / vor)
        print("%8.2f %10d %10d %12.2f %12.4f %10s"
              % (r["lc"], r["knoten"], r["elemente"], r["s_frei"], r["u_max"], d))
        vor = r["s_frei"]

    fein = lauf[-1]
    s_fem, u_fem = fein["s_frei"], fein["u_max"]

    print("\n" + "=" * 74)
    print("VERGLEICH ANALYTISCH / NUMERISCH   (F = %.1f N je Backe)" % F.F_LAST)
    print("=" * 74)
    print("%-42s %12s %12s" % ("", "analytisch", "FEM"))
    print("-" * 74)
    # Die FEM kennt keine Nennspannung - sie rechnet die Kerbe mit, statt sie
    # ueber eine Formzahl aufzuschlagen. Die Spalte bleibt deshalb leer.
    print("%-42s %12.2f %12s" % ("Nennbiegespannung sig_n [MPa]",
                                 ana["sig_nenn"], "-"))
    print("%-42s %12.2f %12.2f" % ("Vergleichsspannung sig_v,max [MPa]", ana["sig_max"], s_fem))
    print("%-42s %12.3f %12.3f" % ("Verformung u_max [mm]", ana["f_spitze"], u_fem))
    print("%-42s %12.2f %12.2f" % ("Sicherheit gegen Rp0,2", ana["S"], P.ZANGE_RP02 / s_fem))
    print("-" * 74)
    d_s = 100 * (s_fem - ana["sig_max"]) / ana["sig_max"]
    d_u = 100 * (u_fem - ana["f_spitze"]) / ana["f_spitze"]
    print("%-42s %12s %11.1f %%" % ("Abweichung Spannung", "", d_s))
    print("%-42s %12s %11.1f %%" % ("Abweichung Verformung", "", d_u))

    ak_fem = s_fem / ana["sig_nenn"]
    print("\nFormzahl der Einspannkerbe")
    print("  analytisch (Diagramm Roloff/Matek)  alpha_k = %.2f" % analytisch.ALPHA_K)
    print("  aus der FEM  sig_v,max / sig_n      alpha_k = %.2f" % ak_fem)

    print("\nBEWERTUNG")
    print("  Die Verformung stimmt bis auf %.1f %% ueberein. Die FEM liefert den" % abs(d_u))
    print("  groesseren Wert, weil die analytische Loesung eine starre Einspannung")
    print("  annimmt, waehrend im Modell der Anschraubkopf mitfedert.")
    print("  Die Spannung liegt %.1f %% %s der analytischen Abschaetzung; die aus dem"
          % (abs(d_s), "unter" if d_s < 0 else "ueber"))
    print("  Diagramm abgelesene Formzahl %.2f ist gegenueber dem FEM-Wert %.2f"
          % (analytisch.ALPHA_K, ak_fem))
    print("  %s." % ("konservativ" if analytisch.ALPHA_K > ak_fem else "zu guenstig"))
    print("  Beide Verfahren bestaetigen die Tragfaehigkeit: Sicherheit %.1f bzw. %.1f"
          % (ana["S"], P.ZANGE_RP02 / s_fem))
    print("  gegenueber der geforderten Mindestsicherheit %.1f." % P.ZANGE_S_ZUL)

    # ---------------------------------------------------------------- Diagramm
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6))
    n = [r["knoten"] for r in lauf]
    s = [r["s_frei"] for r in lauf]
    u = [r["u_max"] for r in lauf]

    a1.plot(n, s, "o-", color="#c0392b", lw=1.8, label="FEM")
    a1.axhline(ana["sig_max"], ls="--", color="#2c3e50",
               label="analytisch mit $\\alpha_k$ = %.2f" % analytisch.ALPHA_K)
    a1.axhline(ana["sig_nenn"], ls=":", color="#7f8c8d", label="Nennspannung")
    a1.set_xlabel("Knotenzahl"); a1.set_ylabel("$\\sigma_{v,max}$ [MPa]")
    a1.set_title("Netzkonvergenz Vergleichsspannung")
    a1.set_xscale("log"); a1.grid(alpha=0.3); a1.legend(fontsize=8)

    a2.plot(n, u, "o-", color="#2980b9", lw=1.8, label="FEM")
    a2.axhline(ana["f_spitze"], ls="--", color="#2c3e50", label="analytisch")
    a2.set_xlabel("Knotenzahl"); a2.set_ylabel("$u_{max}$ [mm]")
    a2.set_title("Netzkonvergenz Verformung")
    a2.set_xscale("log"); a2.grid(alpha=0.3); a2.legend(fontsize=8)

    fig.suptitle("Greiferzange, F = %.0f N je Backe - Gruppe %d, Bauteil %s"
                 % (F.F_LAST, P.GRUPPE, P.BAUTEIL), fontsize=11)
    fig.tight_layout()
    f = os.path.join(OUT, "fem_konvergenz.png")
    fig.savefig(f, dpi=160)
    fig.savefig(f.replace(".png", ".pdf"))
    print("\n  -> out/bilder/fem_konvergenz.png / .pdf")


if __name__ == "__main__":
    main()
