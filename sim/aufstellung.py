"""Aufstellungsstudie Roboter - welche Basisposition und Sockelhoehe sind noetig?

Die Erstauslegung (Roboter mittig, direkt auf dem Boden) ist NICHT erreichbar:
an der Ablage steht der IRB 1600 praktisch voll gestreckt und kann die
senkrechte Werkzeuglage nicht mehr einhalten.

Ursache ist die Bauhoehe des Greifers: der TCP liegt 205 mm unter dem Flansch,
der Flansch muss also deutlich hoeher stehen als die Ablageebene.

Das Skript rastert Basisversatz und Sockelhoehe ab und meldet, welche
Kombinationen alle Bahnstuetzpunkte erreichen.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import mujoco

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.join(HIER, "..", "cad"))

import ablauf as A
import params as P

OUT = os.path.join(HIER, "..", "out", "bilder")
os.makedirs(OUT, exist_ok=True)

# Basisversatz in x (negativ = naeher zum Werkstuecktraeger) und Sockelhoehe
VERSATZ = np.arange(-0.40, 0.05, 0.05)
SOCKEL = np.arange(0.0, 0.65, 0.10)

TOL = 0.002        # m, zulaessiger Restfehler der IK


def pruefe(base_x, h_sockel):
    m = mujoco.MjModel.from_xml_string(A.mjcf(base_x, h_sockel))
    d = mujoco.MjData(m)
    knoten, _ = A.bahn(m, d, n_zwischen=2, still=True)
    return max(k[2] for k in knoten)


def main():
    print("AUFSTELLUNGSSTUDIE  %s" % P.ROBOTER)
    print("Zulaessiger Restfehler der IK: %.0f mm\n" % (TOL * 1000))

    R = np.zeros((len(SOCKEL), len(VERSATZ)))
    for i, h in enumerate(SOCKEL):
        for j, x in enumerate(VERSATZ):
            R[i, j] = pruefe(float(x), float(h))

    print("groesster Restfehler [mm]   (Spalten = Basisversatz x)")
    print("%8s" % "Sockel" + "".join("%8.2f" % x for x in VERSATZ))
    print("-" * (8 + 8 * len(VERSATZ)))
    for i, h in enumerate(SOCKEL):
        zeile = "%8.2f" % h
        for j in range(len(VERSATZ)):
            v = R[i, j] * 1000
            zeile += "%8s" % ("  ok" if R[i, j] < TOL else "%.0f" % v)
        print(zeile)

    ok = R < TOL
    if not ok.any():
        print("\nKEINE Kombination erreicht alle Stuetzpunkte.")
        print("Der IRB 1600-6/1.45 ist fuer diese Anlage zu klein -")
        print("naechste Groesse waehlen (z.B. IRB 2600-12/1.65) oder den")
        print("Greifer kuerzer bauen (derzeit %.0f mm ab Flansch)." % (A.L_GREIFER * 1000))
    else:
        # sparsamste Loesung: kleinster Sockel, dann kleinster Betrag des Versatzes
        kand = [(SOCKEL[i], VERSATZ[j], R[i, j])
                for i in range(len(SOCKEL)) for j in range(len(VERSATZ)) if ok[i, j]]
        kand.sort(key=lambda t: (t[0], abs(t[1])))
        h, x, res = kand[0]
        print("\nEMPFEHLUNG")
        print("  Sockelhoehe    %.0f mm" % (h * 1000))
        print("  Basisversatz   %.0f mm %s" % (abs(x) * 1000,
              "Richtung Werkstuecktraeger" if x < 0 else "Richtung Pufferband"))
        print("  groesster Restfehler %.2f mm" % (res * 1000))
        print("\n  In ablauf.py eintragen:  BASE_X = %.2f   H_SOCKEL = %.2f" % (x, h))

    # ---------------------------------------------------------------- Diagramm
    fig, ax = plt.subplots(figsize=(9, 4.6))
    z = np.clip(R * 1000, 0, 400)
    pc = ax.pcolormesh(VERSATZ * 1000, SOCKEL * 1000, z, cmap="RdYlGn_r",
                       shading="nearest", vmin=0, vmax=400)
    fig.colorbar(pc, ax=ax, label="groesster Restfehler der IK [mm]")
    yy, xx = np.where(ok)
    if len(xx):
        ax.plot(VERSATZ[xx] * 1000, SOCKEL[yy] * 1000, "o", ms=7, mfc="none",
                mec="#111111", mew=1.4, label="erreichbar")
        ax.legend(loc="upper right", fontsize=9)
    ax.set_xlabel("Basisversatz in x [mm]   (negativ = Richtung Werkstuecktraeger)")
    ax.set_ylabel("Sockelhoehe [mm]")
    ax.set_title("Aufstellung %s - Erreichbarkeit aller Bahnstuetzpunkte\n"
                 "Gruppe %d, Bauteil %s" % (P.ROBOTER, P.GRUPPE, P.BAUTEIL),
                 fontsize=11)
    fig.tight_layout()
    f = os.path.join(OUT, "aufstellung.png")
    fig.savefig(f, dpi=160)
    fig.savefig(f.replace(".png", ".pdf"))
    print("\n  -> out/bilder/aufstellung.png / .pdf")


if __name__ == "__main__":
    main()
