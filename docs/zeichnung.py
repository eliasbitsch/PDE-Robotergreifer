"""Abgabepunkt 7 - Baugruppenzeichnung inkl. Stueckliste.

Erzeugt aus der parametrischen Baugruppe automatisch ein Zeichnungsblatt:
drei Ansichten (Vorderansicht, Seitenansicht, Draufsicht) mit verdeckten
Kanten, eine Isometrie, Positionsnummern, Schriftfeld und Stueckliste.

Die Ansichten entstehen ueber die HLR-Projektion von build123d (Drawing),
die Stuecklistendaten (Volumen, Masse) direkt aus den Volumenmodellen -
die Liste kann also nicht von der Konstruktion abweichen.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "cad"))

import build123d as bd
import greifer as G
import params as P

# Im Modell liegt der Roboterflansch bei z = 0 und +Z zeigt zum Bauteil - die
# Zange zeigt also in +Z. In der Zeichnung soll der Greifer haengen, wie er am
# Roboter haengt: Flansch oben, Zange nach unten. Dafuer wird die Baugruppe vor
# dem Projizieren um 180 Grad um X gedreht. Die Drehung gilt fuer ALLE
# Ansichten und fuer die Hinweislinien, sonst laufen Geometrie und
# Positionsnummern auseinander.
DARSTELLUNG = bd.Rot(180, 0, 0)

OUT = os.path.join(HIER, "..", "out")
os.makedirs(OUT, exist_ok=True)

# Dichten [g/cm3] fuer die Massenspalte der Stueckliste
DICHTE = {
    "EN AW-6082 T6": 2.70,
    "EN AW-7075 T6": 2.80,
    "Zukaufteil, 1.4301": 7.90,
    "Zukaufteil": 7.85,
    "1.7225": 7.85,
    "NBR 70 Shore A": 1.35,
}

# Blattformat A3 quer [mm]
BL_B, BL_H = 420.0, 297.0
RAND = 10.0


# ------------------------------------------------------------------ Geometrie
def kanten(shape, look_from, with_hidden=True, look_up=(0, 0, 1)):
    """HLR-Projektion -> Listen von Polylinien (sichtbar, verdeckt)."""
    d = bd.Drawing(shape, look_from=look_from, look_up=look_up,
                   with_hidden=with_hidden)

    def poly(compound):
        aus = []
        if compound is None:
            return aus
        for e in compound.edges():
            n = 2 if e.geom_type == bd.GeomType.LINE else 24
            pts = [e @ (i / (n - 1.0)) for i in range(n)]
            aus.append(np.array([[p.X, p.Y] for p in pts]))
        return aus

    return poly(d.visible_lines), poly(d.hidden_lines if with_hidden else None)


# Blickrichtung und "oben" je Ansicht. Bei der Draufsicht muss look_up
# umdefiniert werden, sonst ist es parallel zur Blickrichtung (Nullvektor).
ANSICHTEN = [
    ("Vorderansicht", (0, -1, 0), (0, 0, 1)),
    ("Seitenansicht", (1, 0, 0),  (0, 0, 1)),
    ("Draufsicht",    (0, 0, 1),  (0, 1, 0)),
    ("Isometrie",     (1, -1, 0.7), (0, 0, 1)),
]


def ansichtsbasis(look_from, look_up):
    """Rechtshaendige Basis der Ansichtsebene (ex = rechts, ey = oben)."""
    ez = np.asarray(look_from, dtype=float)
    ez /= np.linalg.norm(ez)
    up = np.asarray(look_up, dtype=float)
    ex = np.cross(up, ez)
    ex /= np.linalg.norm(ex)
    ey = np.cross(ez, ex)
    return ex, ey


def bbox_mitte(shape):
    b = shape.bounding_box()
    return np.array([(b.min.X + b.max.X) / 2.0,
                     (b.min.Y + b.max.Y) / 2.0,
                     (b.min.Z + b.max.Z) / 2.0])


def zeichne(ax, sicht, x0, y0, massstab, mit_verdeckt=True):
    """Zeichnet eine Ansicht der Baugruppe; gibt die 2D-Lage je Position zurueck."""
    name, richtung, oben = sicht
    ges = baugruppe()
    sicht_v, sicht_h = kanten(ges, richtung, mit_verdeckt, oben)

    alle = sicht_v + sicht_h
    pts = np.vstack(alle)
    mitte = (pts.min(axis=0) + pts.max(axis=0)) / 2.0

    def tf(a):
        return (a - mitte) * massstab + np.array([x0, y0])

    for a in sicht_h:
        b = tf(a)
        ax.plot(b[:, 0], b[:, 1], color="#888888", lw=0.35, ls=(0, (4, 2)), zorder=2)
    for a in sicht_v:
        b = tf(a)
        ax.plot(b[:, 0], b[:, 1], color="#111111", lw=0.7, zorder=3)

    hoehe = (pts.max(axis=0) - pts.min(axis=0))[1] * massstab
    ax.text(x0, y0 - hoehe / 2 - 7, name, ha="center", va="top", fontsize=7.5,
            color="#111111")

    # Lage der einzelnen Positionen fuer die Positionsnummern.
    # bd.Drawing zentriert jede Projektion auf ihr eigenes Bauteil - die
    # Schwerpunkte einzeln zu projizieren ergaebe also immer (0,0). Deshalb
    # werden die 3D-Schwerpunkte hier selbst auf die Ansichtsebene abgebildet.
    ex, ey = ansichtsbasis(richtung, oben)
    c_ges = bbox_mitte(ges)
    lagen = {}
    for key, pos, bez, k in G.alle_koerper():
        if pos in lagen:          # bei Paaren genuegt eine Hinweislinie
            continue
        d3 = bbox_mitte(DARSTELLUNG * k) - c_ges
        lagen[pos] = np.array([np.dot(d3, ex), np.dot(d3, ey)]) * massstab \
            + np.array([x0, y0])
    return lagen


_CACHE = {}


def baugruppe():
    if "ges" not in _CACHE:
        ges = None
        for key, pos, name, k in G.alle_koerper():
            k = DARSTELLUNG * k
            ges = k if ges is None else ges + k
        _CACHE["ges"] = ges
    return _CACHE["ges"]


# ------------------------------------------------------------------ Stueckliste
def stueckliste():
    """Kommt direkt aus greifer.py - eine Quelle fuer Modell und Liste."""
    return G.stueckliste_daten()


# ------------------------------------------------------------------ Blatt
def rahmen(ax):
    ax.add_patch(plt.Rectangle((RAND, RAND), BL_B - 2 * RAND, BL_H - 2 * RAND,
                               fill=False, ec="#111111", lw=1.0, zorder=6))


def schriftfeld(ax, m_ges):
    b, h = 180.0, 32.0
    x0, y0 = BL_B - RAND - b, RAND
    ax.add_patch(plt.Rectangle((x0, y0), b, h, fc="white", ec="#111111", lw=1.0, zorder=7))
    for dy in (8, 16, 24):
        ax.plot([x0, x0 + b], [y0 + dy, y0 + dy], color="#111111", lw=0.5, zorder=8)
    ax.plot([x0 + 105, x0 + 105], [y0, y0 + h], color="#111111", lw=0.5, zorder=8)

    def t(dx, dy, s, **kw):
        kw.setdefault("fontsize", 6.5)
        ax.text(x0 + dx, y0 + dy, s, va="center", zorder=9, **kw)

    t(3, 28, "GREIFER FUER BAUTEIL %s" % P.BAUTEIL, fontsize=9, weight="bold")
    t(3, 20, "Produktdesign und Produktentwicklung - MRE WS26")
    t(3, 12, "Gruppe %d:  %s" % (P.GRUPPE, ", ".join(P.AUTOREN)))
    t(3, 4, "Roboter: %s" % P.ROBOTER)
    t(108, 28, "Baugruppenzeichnung")
    t(108, 20, "Massstab  1:2")
    t(108, 12, "Gesamtmasse  %.2f kg" % m_ges)
    t(108, 4, "Masse in mm, Winkel in Grad")


def liste(ax, zeilen, m_ges):
    sp = [9, 64, 9, 42, 17, 17]          # Spaltenbreiten
    b = sum(sp)
    zh = 4.6
    x0 = BL_B - RAND - b
    y0 = RAND + 32.0 + 4.0
    n = len(zeilen)

    ax.add_patch(plt.Rectangle((x0, y0), b, zh * (n + 1), fc="white", ec="#111111",
                               lw=1.0, zorder=7))
    for i in range(1, n + 1):
        ax.plot([x0, x0 + b], [y0 + i * zh, y0 + i * zh], color="#111111",
                lw=0.4, zorder=8)
    xc = x0
    for w in sp[:-1]:
        xc += w
        ax.plot([xc, xc], [y0, y0 + zh * (n + 1)], color="#111111", lw=0.4, zorder=8)

    def zeile(y, werte, **kw):
        xc = x0
        for w, s in zip(sp, werte):
            ax.text(xc + 1.5, y + zh / 2, s, fontsize=5.6, va="center", zorder=9, **kw)
            xc += w

    zeile(y0 + n * zh, ["Pos", "Benennung", "Anz", "Werkstoff / Norm", "V [cm3]", "m [kg]"],
          weight="bold")
    for i, (pos, bez, anz, werkstoff, v, m) in enumerate(reversed(zeilen)):
        zeile(y0 + (n - 1 - i) * zh,
              [pos, bez, str(anz), werkstoff, "%.1f" % v, "%.3f" % m])


def positionsnummern(ax, lagen, mitte, radius=62.0):
    """Positionsballons auf einem Ring um die Ansicht.

    Ein rein radialer Versatz vom Bauteilschwerpunkt reicht nicht: die
    Schwerpunkte liegen fast alle auf der Mittelachse, die Ballons wuerden
    uebereinanderfallen. Deshalb werden sie winkelversetzt auf einem Ring
    verteilt - in der Reihenfolge, in der die Bauteile stehen.
    """
    if not lagen:
        return
    mitte = np.asarray(mitte, dtype=float)

    # Nach dem Winkel des Ankers sortieren, nicht nach der Positionsnummer -
    # sonst kreuzen sich die Hinweislinien.
    def wink(kv):
        d = kv[1] - mitte
        a = np.arctan2(d[1], d[0])
        return -a if a <= np.deg2rad(150) else np.deg2rad(150) - a

    posl = sorted(lagen.items(), key=wink)
    n = len(posl)

    # Ballons oben links beginnend im Uhrzeigersinn verteilen,
    # der untere Bereich bleibt fuer die Ansichtsbeschriftung frei.
    winkel = np.linspace(np.deg2rad(150), np.deg2rad(-120), n)

    for (pos, p), w in zip(posl, winkel):
        b = mitte + radius * np.array([np.cos(w), np.sin(w)])
        ax.plot([p[0], b[0]], [p[1], b[1]], color="#111111", lw=0.4, zorder=4)
        ax.plot([p[0]], [p[1]], marker="o", ms=1.6, color="#111111", zorder=4)
        ax.add_patch(Circle(b, 3.6, fc="white", ec="#111111", lw=0.6, zorder=5))
        ax.text(b[0], b[1], pos, ha="center", va="center", fontsize=6,
                zorder=6, weight="bold")


def main():
    print("BAUGRUPPENZEICHNUNG + STUECKLISTE")
    zeilen, m_ges = stueckliste()
    print("\n%-4s %-38s %4s %-22s %9s %9s"
          % ("Pos", "Benennung", "Anz", "Werkstoff", "V [cm3]", "m [kg]"))
    print("-" * 92)
    for pos, bez, anz, werkstoff, v, m in zeilen:
        print("%-4s %-38s %4d %-22s %9.1f %9.3f" % (pos, bez, anz, werkstoff, v, m))
    print("-" * 92)
    print("%-4s %-38s %4s %-22s %9s %9.3f" % ("", "Gesamtmasse Greifer", "", "", "", m_ges))

    if m_ges > P.M_GREIFER:
        print("\n  HINWEIS: %.2f kg liegen ueber der Annahme %.1f kg aus der Auslegung."
              % (m_ges, P.M_GREIFER))
    print("  Traglast %s: %.1f kg, Auslastung %.0f %% (Greifer + Bauteil)"
          % (P.ROBOTER, P.M_TRAGLAST, 100 * (m_ges + P.B_MASSE) / P.M_TRAGLAST))

    print("\nZeichnungsblatt erzeugen ...")
    fig = plt.figure(figsize=(BL_B / 25.4, BL_H / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, BL_B); ax.set_ylim(0, BL_H)
    ax.set_aspect("equal"); ax.axis("off")

    rahmen(ax)
    M = 0.5                                      # Massstab 1:2
    lagen = zeichne(ax, ANSICHTEN[0], 95, 185, M)
    zeichne(ax, ANSICHTEN[1], 200, 185, M)
    zeichne(ax, ANSICHTEN[2], 95, 65, M)
    zeichne(ax, ANSICHTEN[3], 290, 200, M * 0.8, mit_verdeckt=False)
    positionsnummern(ax, lagen, (95, 185))
    liste(ax, zeilen, m_ges)
    schriftfeld(ax, m_ges)

    f = os.path.join(OUT, "Baugruppenzeichnung_Greifer.pdf")
    fig.savefig(f)
    fig.savefig(f.replace(".pdf", ".png"), dpi=200)
    print("  ->", os.path.relpath(f, os.path.join(HIER, "..")))


if __name__ == "__main__":
    main()
