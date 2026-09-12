"""Anlagenszene nach Abb.1 fuer pybullet: generischer 6-Achser, Pufferband (h=1000),
Werkstuecktraeger (h=1300, 2 Ketten a 600 mm), Abstand 1800 mm, Schutzeinhausung 2100.
Erzeugt URDF + Szene und rendert eine Uebersicht."""
import os, math
import numpy as np
import pybullet as pb
import pybullet_data

OUT = "/mnt/c/git/FH/PDE/sim"
os.makedirs(OUT, exist_ok=True)

# ---- generischer 6R-Knickarm, Reichweite ~1350 mm ----
L0, L1, L2, L3 = 0.40, 0.65, 0.55, 0.15     # Sockel, Oberarm, Unterarm, Handgelenk

def link(name, length, radius, rgba):
    return f"""
  <link name="{name}">
    <visual><origin xyz="0 0 {length/2}"/>
      <geometry><cylinder radius="{radius}" length="{length}"/></geometry>
      <material name="m_{name}"><color rgba="{rgba}"/></material></visual>
    <collision><origin xyz="0 0 {length/2}"/>
      <geometry><cylinder radius="{radius}" length="{length}"/></geometry></collision>
    <inertial><mass value="5"/><inertia ixx="0.1" iyy="0.1" izz="0.1" ixy="0" ixz="0" iyz="0"/></inertial>
  </link>"""

def joint(name, parent, child, xyz, axis, lo, hi):
    return f"""
  <joint name="{name}" type="revolute">
    <parent link="{parent}"/><child link="{child}"/>
    <origin xyz="{xyz}"/><axis xyz="{axis}"/>
    <limit lower="{lo}" upper="{hi}" effort="500" velocity="4.0"/>
  </joint>"""

O = "1.0 0.45 0.05 1"
urdf = "<?xml version='1.0'?>\n<robot name='generic6r'>"
urdf += link("base", L0, 0.16, "0.25 0.25 0.28 1")
urdf += link("shoulder", 0.18, 0.13, O)
urdf += link("upperarm", L1, 0.10, O)
urdf += link("forearm",  L2, 0.085, O)
urdf += link("wrist1",   0.12, 0.07, O)
urdf += link("wrist2",   L3, 0.06, O)
urdf += link("flange",   0.04, 0.055, "0.2 0.2 0.2 1")
P = math.pi
urdf += joint("A1", "base",     "shoulder", f"0 0 {L0}",  "0 0 1", -P,     P)
urdf += joint("A2", "shoulder", "upperarm", "0 0 0.18",   "0 1 0", -2.0,  2.0)
urdf += joint("A3", "upperarm", "forearm",  f"0 0 {L1}",  "0 1 0", -2.6,  2.6)
urdf += joint("A4", "forearm",  "wrist1",   f"0 0 {L2}",  "0 0 1", -P,     P)
urdf += joint("A5", "wrist1",   "wrist2",   "0 0 0.12",   "0 1 0", -2.2,  2.2)
urdf += joint("A6", "wrist2",   "flange",   f"0 0 {L3}",  "0 0 1", -P,     P)
urdf += "\n</robot>\n"
urdf_path = os.path.join(OUT, "generic6r.urdf")
open(urdf_path, "w").write(urdf)
print("URDF:", urdf_path, " Reichweite ab Schulter =", L1+L2+L3, "m")

# ---- Szene ----
pb.connect(pb.DIRECT)
pb.setAdditionalSearchPath(pybullet_data.getDataPath())
pb.setGravity(0, 0, -9.81)
pb.loadURDF("plane.urdf")

def box(hx, hy, hz, pos, rgba):
    v = pb.createVisualShape(pb.GEOM_BOX, halfExtents=[hx,hy,hz], rgbaColor=rgba)
    c = pb.createCollisionShape(pb.GEOM_BOX, halfExtents=[hx,hy,hz])
    return pb.createMultiBody(0, c, v, pos)

X_PICK, X_PLACE = 0.90, -0.90        # 1800 mm Abstand
H_PICK, H_PLACE = 1.00, 1.30         # Abb.1
CHAIN_DY = 0.30                      # 600 mm Kettenabstand

box(0.35, 0.25, H_PICK/2, [X_PICK, 0, H_PICK/2], [0.6,0.6,0.65,1])          # Pufferband
for dy in (-CHAIN_DY, CHAIN_DY):                                             # 2 Foerderketten
    box(0.30, 0.12, H_PLACE/2, [X_PLACE, dy, H_PLACE/2], [0.45,0.5,0.6,1])
robot = pb.loadURDF(urdf_path, [0,0,0], useFixedBase=True)

# Bauteil B auf dem Pufferband
mesh = "/mnt/c/git/FH/PDE/sim/meshes/bauteil_B.stl"
vb = pb.createVisualShape(pb.GEOM_MESH, fileName=mesh, meshScale=[1e-3]*3, rgbaColor=[0.85,0.85,0.88,1])
cb = pb.createCollisionShape(pb.GEOM_MESH, fileName=mesh, meshScale=[1e-3]*3)
teil = pb.createMultiBody(0.602, cb, vb, [X_PICK, 0, H_PICK+0.04])

for j, q in enumerate([0.0, -0.55, 1.1, 0.0, 1.0, 0.0]):
    pb.resetJointState(robot, j, q)

vm = pb.computeViewMatrixFromYawPitchRoll([0,0,0.9], 4.2, 35, -18, 0, 2)
pm = pb.computeProjectionMatrixFOV(52, 4/3, 0.1, 20)
w,h,rgb,_,_ = pb.getCameraImage(1000, 750, vm, pm, renderer=pb.ER_TINY_RENDERER)
from PIL import Image
Image.fromarray(np.reshape(rgb,(h,w,4))[:,:,:3].astype(np.uint8)).save(os.path.join(OUT,"szene.png"))
print("Bild:", os.path.join(OUT,"szene.png"))
print("Reichweite noetig: %.0f mm  (Pick: %.0f mm, Place seitlich: %.0f mm)"
      % (1242, math.hypot(X_PICK, H_PICK-L0)*1000, math.hypot(X_PLACE, CHAIN_DY, )*1000 if False else math.sqrt(X_PLACE**2+CHAIN_DY**2+(H_PLACE-L0)**2)*1000))
pb.disconnect()
