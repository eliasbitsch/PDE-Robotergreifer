"""Rendert die Greifer-Baugruppe als PNG (Kontrollbild / Abbildungen fuer den Bericht).

Exportiert die Bauteile einzeln nach STL und rendert sie mit MuJoCo, damit die
Positionen farblich unterscheidbar sind.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from build123d import export_stl
from PIL import Image
import mujoco

import greifer as G
import params as P

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MESH = os.path.join(ROOT, "out", "mesh")
OUT = os.path.join(ROOT, "out", "bilder")
os.makedirs(MESH, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# Pos -> Farbe
FARBE = {
    "1":  "0.55 0.58 0.63 1",    # Adapterplatte, Alu
    "2":  "0.30 0.32 0.36 1",    # Wechsler Roboterseite
    "3":  "0.38 0.40 0.45 1",    # Wechsler Greiferseite
    "4":  "0.87 0.42 0.09 1",    # Gehaeuse, orange
    "5":  "0.80 0.35 0.35 1",    # Ritzel, rot
    "6":  "0.50 0.52 0.56 1",    # Ritzelwelle
    "7":  "0.45 0.60 0.80 1",    # Zahnstange, blau
    "8":  "0.25 0.65 0.45 1",    # Servomotor, gruen
    "9":  "0.72 0.75 0.80 1",    # Greiferzange
    "10": "0.15 0.15 0.17 1",    # Weichbacke NBR
    "11": "0.11 0.11 0.12 1",    # Verkleidung, schwarzes PA12 (SLS)
    "12": "0.30 0.34 0.40 1",    # Haltebremse
}


def export_meshes():
    """Jedes Bauteil einzeln als STL - Quelle ist greifer.alle_koerper().

    Der Ordner wird vorher geleert. Bleiben STL-Dateien einer frueheren
    Konstruktion liegen, laedt die Simulation sie stillschweigend weiter.
    """
    for alt in os.listdir(MESH):
        if alt.endswith(".stl") and alt != "bauteilB.stl":
            os.remove(os.path.join(MESH, alt))
    teile = []
    for key, pos, name, koerper in G.alle_koerper():
        export_stl(koerper, os.path.join(MESH, key + ".stl"))
        teile.append((pos, key))
    return teile


def xml(teile, mit_bauteil):
    assets, geoms = [], []
    # STL kommt in mm, MuJoCo rechnet in m
    MM = 'scale="0.001 0.001 0.001"'
    for pos, key in teile:
        assets.append('<mesh name="%s" file="%s.stl" %s/>' % (key, key, MM))
        geoms.append('<geom type="mesh" mesh="%s" rgba="%s" '
                     'contype="0" conaffinity="0"/>' % (key, FARBE[pos]))
    if mit_bauteil:
        assets.append('<mesh name="teilB" file="bauteilB.stl" %s/>' % MM)
        z = (G.Z_ZANGE + G.ZL - G.P.BACKE_LAENGE / 2) / 1000.0
        geoms.append('<geom type="mesh" mesh="teilB" rgba="0.88 0.89 0.92 1" '
                     'pos="0 0 %f" contype="0" conaffinity="0"/>' % z)
    return f"""
<mujoco model="greifer">
  <compiler angle="radian" meshdir="{MESH}"/>
  <visual>
    <global offwidth="1800" offheight="1400"/>
    <quality shadowsize="8192" offsamples="8"/>
    <headlight ambient="0.42 0.42 0.45" diffuse="0.45 0.45 0.45" specular="0.25 0.25 0.25"/>
    <map znear="0.001" zfar="30"/>
  </visual>
  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.55 0.62 0.72" rgb2="0.93 0.94 0.96"
             width="512" height="512"/>
    {"".join(assets)}
  </asset>
  <worldbody>
    <light pos="0.4 -0.5 0.6" dir="-0.5 0.6 -0.7" diffuse="0.6 0.6 0.6"/>
    <light pos="-0.4 0.4 0.5" dir="0.5 -0.5 -0.7" diffuse="0.3 0.3 0.32"/>
    <body name="greifer" pos="0 0 0" euler="3.14159 0 0">
      {"".join(geoms)}
    </body>
  </worldbody>
</mujoco>
"""


def render(teile, mit_bauteil, name, cam):
    m = mujoco.MjModel.from_xml_string(xml(teile, mit_bauteil))
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    r = mujoco.Renderer(m, 1400, 1800)
    c = mujoco.MjvCamera()
    c.type = mujoco.mjtCamera.mjCAMERA_FREE
    c.lookat[:] = [0, 0, -0.115]
    c.distance, c.azimuth, c.elevation = cam
    r.update_scene(d, camera=c)
    f = os.path.join(OUT, name)
    Image.fromarray(r.render()).save(f)
    print("  ->", os.path.relpath(f, ROOT))


def main():
    print("STL-Export ...")
    teile = export_meshes()
    print("  %d Meshes" % len(teile))

    # Bauteil B mitexportieren
    from build123d import import_step
    b = import_step(os.path.join(ROOT, "3D-Daten der Bauteile-20260904", "Bauteil_B.STEP"))
    from build123d import Pos
    export_stl(Pos(*[-c for c in P.B_COG]) * b, os.path.join(MESH, "bauteilB.stl"))

    print("Rendern ...")
    render(teile, False, "greifer_iso.png", (0.50, 140, -22))
    render(teile, False, "greifer_front.png", (0.44, 90, 0))
    render(teile, False, "greifer_seite.png", (0.46, 0, -8))
    render(teile, True, "greifer_mit_bauteilB.png", (0.58, 135, -18))
    # Mechanik ohne Gehaeuse - sonst sieht man von der Konstruktion nichts
    innen = [(p, k) for p, k in teile if p not in ("1", "2", "3", "4", "11")]
    render(innen, False, "greifer_mechanik.png", (0.34, 150, -32))
    render(innen, False, "greifer_mechanik_oben.png", (0.30, 90, -78))


if __name__ == "__main__":
    main()
