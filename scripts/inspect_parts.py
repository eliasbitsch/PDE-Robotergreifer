"""Bauteil-Uebersicht: Bounding Box, Volumen, Masse (Annahme Stahl 7.85 g/cm3)."""
import glob, os
from build123d import import_step

RHO = 7.85  # g/cm3
SRC = "/mnt/c/git/FH/PDE/3D-Daten der Bauteile-20260904/*.STEP"

hdr = ("Datei", "X [mm]", "Y [mm]", "Z [mm]", "V [cm3]", "m [kg]")
print("%-14s %9s %9s %9s %10s %9s" % hdr)
print("-" * 66)
for f in sorted(glob.glob(SRC)):
    name = os.path.basename(f)
    try:
        p = import_step(f)
        b = p.bounding_box().size
        v = p.volume / 1000.0
        print("%-14s %9.1f %9.1f %9.1f %10.1f %9.3f"
              % (name, b.X, b.Y, b.Z, v, v * RHO / 1000.0))
    except Exception as e:
        print("%-14s FEHLER: %s: %s" % (name, type(e).__name__, e))
