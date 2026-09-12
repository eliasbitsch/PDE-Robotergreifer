"""Bauteil B: planare Flaechen finden und gegenueberliegende Paare als
Greifflaechen-Kandidaten bewerten (seitliches Greifen, kein Untergreifen)."""
import numpy as np
from build123d import import_step, Plane, Face

F = "/mnt/c/git/FH/PDE/3D-Daten der Bauteile-20260904/Bauteil_B.STEP"
p = import_step(F)
bb = p.bounding_box()
print("BBox  X=%.1f  Y=%.1f  Z=%.1f mm   V=%.1f cm3" % (bb.size.X, bb.size.Y, bb.size.Z, p.volume/1000))
print("Schwerpunkt:", tuple(round(c, 1) for c in p.center()))
print()

planar = []
for f in p.faces():
    try:
        n = f.normal_at(f.center())
        planar.append((f.area, np.array([n.X, n.Y, n.Z]), f.center()))
    except Exception:
        pass

# nur nennenswerte Flaechen, nach Groesse
planar = [x for x in planar if x[0] > 100]
planar.sort(key=lambda x: -x[0])
print("%-6s %10s   %-22s %s" % ("#", "A [mm2]", "Normale", "Mittelpunkt"))
for i, (a, n, c) in enumerate(planar[:12]):
    print("%-6d %10.0f   (%5.2f %5.2f %5.2f)   (%6.1f %6.1f %6.1f)"
          % (i, a, n[0], n[1], n[2], c.X, c.Y, c.Z))

print("\nGegenueberliegende, parallele Flaechenpaare (Backen-Kandidaten):")
seen = []
for i, (a1, n1, c1) in enumerate(planar):
    for j, (a2, n2, c2) in enumerate(planar[i+1:], i+1):
        if np.dot(n1, n2) < -0.98:                      # antiparallel
            d = np.array([c2.X-c1.X, c2.Y-c1.Y, c2.Z-c1.Z])
            span = abs(np.dot(d, n1))
            if span > 5 and min(a1, a2) > 500:
                seen.append((min(a1, a2), span, n1, i, j))
seen.sort(key=lambda x: -x[0])
for a, span, n, i, j in seen[:6]:
    ax = "XYZ"[int(np.argmax(abs(n)))]
    print("  Flaechen %2d/%2d  Greifrichtung %s  Backenabstand %6.1f mm  nutzbar %7.0f mm2"
          % (i, j, ax, span, a))
