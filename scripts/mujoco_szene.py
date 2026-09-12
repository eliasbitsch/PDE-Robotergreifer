"""Anlagenszene nach Abb.1 in MuJoCo - Gruppe 2, Bauteil B.
Pufferband h=1000, Werkstuecktraeger h=1300 (2 Ketten a 600 mm), Abstand 1800 mm."""
import os, numpy as np, mujoco
from PIL import Image

OUT = "/mnt/c/git/FH/PDE/sim"
L0, L1, L2, L3 = 0.40, 0.65, 0.55, 0.15
X_PICK, X_PLACE, H_PICK, H_PLACE, DY = 0.90, -0.90, 1.00, 1.30, 0.30

def arm():
    return f"""
  <body name="base" pos="0 0 0">
    <geom type="cylinder" size="0.17 {L0/2}" pos="0 0 {L0/2}" material="stahl"/>
    <body name="shoulder" pos="0 0 {L0}">
      <joint name="A1" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
      <geom type="cylinder" size="0.135 0.09" pos="0 0 0.09" material="orange"/>
      <body name="upperarm" pos="0 0 0.18">
        <joint name="A2" type="hinge" axis="0 1 0" range="-2.0 2.0"/>
        <geom type="capsule" size="0.085" fromto="0 0 0 0 0 {L1}" material="orange"/>
        <body name="forearm" pos="0 0 {L1}">
          <joint name="A3" type="hinge" axis="0 1 0" range="-2.6 2.6"/>
          <geom type="cylinder" size="0.105 0.055" material="stahl"/>
          <geom type="capsule" size="0.070" fromto="0 0 0 0 0 {L2}" material="orange"/>
          <body name="wrist" pos="0 0 {L2}">
            <joint name="A4" type="hinge" axis="0 1 0" range="-2.2 2.2"/>
            <geom type="cylinder" size="0.075 0.05" material="stahl"/>
            <geom type="capsule" size="0.052" fromto="0 0 0 0 0 {L3}" material="orange"/>
            <body name="flange" pos="0 0 {L3}">
              <joint name="A5" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
              <geom type="cylinder" size="0.055 0.022" material="dunkel"/>
              <!-- Platzhalter Greifer: Grundkoerper + zwei Backen -->
              <geom type="box" size="0.055 0.038 0.045" pos="0 0 0.065" material="orange"/>
              <geom type="box" size="0.011 0.038 0.062" pos=" 0.046 0 0.170" material="stahl"/>
              <geom type="box" size="0.011 0.038 0.062" pos="-0.046 0 0.170" material="stahl"/>
            </body>
          </body>
        </body>
      </body>
    </body>
  </body>"""

XML = f"""
<mujoco model="anlage">
  <compiler angle="radian" meshdir="{OUT}/meshes"/>
  <visual>
    <global offwidth="1600" offheight="1100"/>
    <quality shadowsize="8192" offsamples="8"/>
    <headlight ambient="0.35 0.35 0.38" diffuse="0.35 0.35 0.35" specular="0.1 0.1 0.1"/>
    <map znear="0.01" zfar="60"/>
  </visual>
  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.62 0.70 0.80" rgb2="0.94 0.95 0.97"
             width="512" height="512"/>
    <texture name="boden" type="2d" builtin="checker" rgb1="0.72 0.73 0.75" rgb2="0.80 0.81 0.83"
             width="512" height="512"/>
    <material name="boden" texture="boden" texrepeat="14 14" reflectance="0.15" specular="0.3"/>
    <material name="orange" rgba="0.87 0.42 0.09 1" specular="0.5" shininess="0.4"/>
    <material name="stahl"  rgba="0.42 0.45 0.50 1" specular="0.7" shininess="0.6"/>
    <material name="dunkel" rgba="0.16 0.17 0.20 1" specular="0.4"/>
    <material name="anlage" rgba="0.55 0.58 0.63 1" specular="0.35" shininess="0.3"/>
    <material name="pa6"    rgba="0.90 0.90 0.93 1" specular="0.25" shininess="0.2"/>
    <mesh name="bauteilB" file="bauteil_B.stl" scale="0.001 0.001 0.001"/>
  </asset>
  <worldbody>
    <light pos="2.5 -2.5 4.5" dir="-0.45 0.45 -1" directional="true"
           diffuse="0.75 0.74 0.72" specular="0.25 0.25 0.25" castshadow="true"/>
    <light pos="-3 2 3.5" dir="0.5 -0.4 -1" directional="true"
           diffuse="0.25 0.26 0.30" castshadow="false"/>
    <geom name="boden" type="plane" size="8 8 0.1" material="boden"/>

    <!-- Pufferband, Entnahmehoehe 1000 -->
    <body pos="{X_PICK} 0 0">
      <geom type="box" size="0.36 0.26 {H_PICK/2}" pos="0 0 {H_PICK/2}" material="anlage"/>
      <geom type="box" size="0.36 0.28 0.012" pos="0 0 {H_PICK+0.012}" material="dunkel"/>
    </body>
    <!-- zwei Foerderketten, Ablagehoehe 1300, Abstand 600 -->
    <body pos="{X_PLACE} {DY} 0">
      <geom type="box" size="0.30 0.11 {H_PLACE/2}" pos="0 0 {H_PLACE/2}" material="anlage"/>
    </body>
    <body pos="{X_PLACE} {-DY} 0">
      <geom type="box" size="0.30 0.11 {H_PLACE/2}" pos="0 0 {H_PLACE/2}" material="anlage"/>
    </body>

    <!-- Bauteil B auf dem Pufferband -->
    <body name="bauteil" pos="{X_PICK} 0 {H_PICK+0.065}">
      <geom type="mesh" mesh="bauteilB" material="pa6"/>
    </body>
{arm()}
  </worldbody>
</mujoco>
"""
open(os.path.join(OUT, "anlage.xml"), "w").write(XML)
m = mujoco.MjModel.from_xml_string(XML)
d = mujoco.MjData(m)
for name, q in [("A1", 0.0), ("A2", -0.62), ("A3", 1.15), ("A4", 1.02), ("A5", 0.0)]:
    d.qpos[m.joint(name).qposadr[0]] = q
mujoco.mj_forward(m, d)

cam = mujoco.MjvCamera()
cam.lookat[:] = [0.0, 0.0, 0.85]
opt = mujoco.MjvOption()
r = mujoco.Renderer(m, 1100, 1600)
for tag, (az, el, dist) in {"iso": (128, -18, 5.2), "front": (90, -12, 5.0)}.items():
    cam.azimuth, cam.elevation, cam.distance = az, el, dist
    r.update_scene(d, camera=cam, scene_option=opt)
    Image.fromarray(r.render()).save(os.path.join(OUT, f"mj_{tag}.png"))
    print("geschrieben:", f"mj_{tag}.png")
