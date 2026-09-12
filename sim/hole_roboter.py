"""Laedt das ABB-IRB-1600-Modell von ros-industrial (BSD-Lizenz).

Quelle: https://github.com/ros-industrial/abb  (abb_irb1600_support)

Die Kinematik der 1,45-m-Varianten (6/1.45, 8/1.45, 10/1.45) ist identisch;
sie unterscheiden sich in Motorisierung und Traglast, nicht in der Geometrie.
ros-industrial liefert die 1,45-m-Armgeometrie unter irb1600_x_145 - genau
diese wird hier verwendet und im Bericht als solche ausgewiesen.
"""
import os
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "meshes", "irb1600")

BASIS = ("https://raw.githubusercontent.com/ros-industrial/abb/"
         "kinetic-devel/abb_irb1600_support/meshes")

# (Mesh-Satz, Linkname) - link_2 kommt aus dem 1,45-m-Satz
LINKS = [
    ("irb1600", "base_link"),
    ("irb1600", "link_1"),
    ("irb1600_x_145", "link_2"),
    ("irb1600", "link_3"),
    ("irb1600", "link_4"),
    ("irb1600", "link_5"),
    ("irb1600", "link_6"),
]


def main():
    os.makedirs(ZIEL, exist_ok=True)
    print("ABB IRB 1600 - Meshes von ros-industrial (BSD)")
    for art in ("visual", "collision"):
        d = os.path.join(ZIEL, art)
        os.makedirs(d, exist_ok=True)
        for satz, link in LINKS:
            url = "%s/%s/%s/%s.stl" % (BASIS, satz, art, link)
            f = os.path.join(d, link + ".stl")
            if os.path.exists(f) and os.path.getsize(f) > 0:
                print("  %-10s %-12s vorhanden" % (art, link))
                continue
            try:
                urllib.request.urlretrieve(url, f)
                print("  %-10s %-12s %7.0f kB" % (art, link, os.path.getsize(f) / 1024))
            except Exception as e:
                print("  %-10s %-12s FEHLER %s" % (art, link, e))


if __name__ == "__main__":
    main()
