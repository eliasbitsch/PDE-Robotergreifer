"""Bauteil B aus STEP nach STL fuer die pybullet-Szene."""
from build123d import import_step, export_stl
src = "/mnt/c/git/FH/PDE/3D-Daten der Bauteile-20260904/Bauteil_B.STEP"
dst = "/mnt/c/git/FH/PDE/sim/meshes/bauteil_B.stl"
p = import_step(src)
export_stl(p, dst, tolerance=0.05, angular_tolerance=0.2)
print("geschrieben:", dst)
print("BBox:", p.bounding_box().size)
