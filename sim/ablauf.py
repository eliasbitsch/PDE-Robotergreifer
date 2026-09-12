"""Abgabepunkt 8 - Visuelle Darstellung des Arbeitsablaufes inkl. Kollisionskontrolle.

Vollstaendig skriptgesteuert mit MuJoCo (Apache 2.0), ohne GUI:
  ABB IRB 1600 (Kinematik aus ros-industrial, BSD)
  + Greifer aus cad/greifer.py
  + Anlage nach Abb.1 (Pufferband, Werkstuecktraeger, Schutzeinhausung)

Ablauf: Entnahme am Pufferband (h=1000) -> Transport -> Ablage am
Werkstuecktraeger (h=1300, zwei Ketten a 600 mm, 1800 mm entfernt).

Die Kollisionskontrolle wertet ueber die gesamte Bahn die Kontaktpaare von
MuJoCo aus. Roboter und Greifer liegen in einer Kollisionsgruppe, die Anlage
in einer zweiten - so werden nur echte Anlagenkollisionen gemeldet und nicht
die gewollten Beruehrungen innerhalb des Roboters.

Koordinaten: Roboterfuss im Ursprung, x zum Pufferband, z nach oben.
"""
import os
import sys

import numpy as np
from PIL import Image
import mujoco

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "cad"))
import params as P

MESH_ROB = os.path.join(HIER, "meshes", "irb1600")
MESH_GR = os.path.join(HIER, "..", "out", "mesh")
OUT = os.path.join(HIER, "..", "out", "bilder")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ Anlage
X_PICK = P.DIST_HORIZONTAL / 2.0          # +0,90 m
X_PLACE = -P.DIST_HORIZONTAL / 2.0        # -0,90 m
H_PICK = P.H_ENTNAHME                     # 1,00 m
H_PLACE = P.H_ABLAGE                      # 1,30 m
DY_KETTE = P.KETTEN_ABSTAND / 2.0         # +-0,30 m
H_ZAUN = P.EINHAUSUNG_HOEHE               # 2,10 m

# Greifer: TCP liegt ZANGE-Laenge unter dem Flansch
L_GREIFER = 0.235                         # m, Bauhoehe ab Flansch (aus greifer.py)
Z_GRIFF = 0.030                           # m, Griffmitte ueber der Bauteilunterkante
H_TEIL = P.B_BBOX[2] / 1000.0             # 0,080 m

# Ablageorientierung am Werkstuecktraeger. Laut Angabe wird die Orientierung
# bei der Angabenausgabe definiert - hier als Parameter gefuehrt.
DREHUNG_ABLAGE = np.deg2rad(90.0)

# Aufstellung des Roboters - Ergebnis der Studie in aufstellung.py.
# Mit dem Roboter mittig auf dem Boden ist der Ablauf NICHT ausfuehrbar:
# Achse 5 (+-115 Grad) reicht nicht aus, um das Werkzeug bei weit und hoch
# gestrecktem Arm senkrecht nach unten zu stellen. Ein Sockel entschaerft das,
# weil der Arm dann flacher zur Ablageebene steht.
BASE_X = -0.10       # m, Richtung Werkstuecktraeger
H_SOCKEL = 0.50      # m

# ------------------------------------------------------------------ Roboter
# Gelenkurspruenge und -achsen aus abb_irb1600_support/urdf/irb1600_10_145_macro.xacro
GELENKE = [
    ("joint_1", (0.0, 0.0, 0.0),     (0, 0, 1), (-180, 180)),
    ("joint_2", (0.15, 0.0, 0.4865), (0, 1, 0), (-90, 120)),
    ("joint_3", (0.0, 0.0, 0.700),   (0, 1, 0), (-245, 65)),
    ("joint_4", (0.300, 0.0, 0.0),   (1, 0, 0), (-200, 200)),
    ("joint_5", (0.300, 0.0, 0.0),   (0, 1, 0), (-115, 115)),
    ("joint_6", (0.065, 0.0, 0.0),   (1, 0, 0), (-400, 400)),
]

# Teileliste NICHT fest verdrahten - sie muss der Konstruktion folgen.
# Eine veraltete Liste laedt stillschweigend alte STL-Dateien; der Lauf geht
# durch und meldet "kollisionsfrei" fuer einen Greifer, den es nicht mehr gibt.
sys.path.insert(0, os.path.join(HIER, "..", "cad"))
import greifer as _G
GREIFER_TEILE = [k for k, pos, name, koerper in _G.alle_koerper()]


def mjcf(base_x=0.0, h_sockel=0.0):
    rob_v = os.path.join(MESH_ROB, "visual")
    rob_c = os.path.join(MESH_ROB, "collision")

    assets = [
        '<texture type="skybox" builtin="gradient" rgb1="0.55 0.62 0.72" '
        'rgb2="0.93 0.94 0.96" width="512" height="512"/>',
        '<texture name="t_boden" type="2d" builtin="checker" rgb1="0.70 0.71 0.73" '
        'rgb2="0.78 0.79 0.81" width="512" height="512"/>',
        '<material name="boden" texture="t_boden" texrepeat="18 18" reflectance="0.12"/>',
        '<material name="abb" rgba="0.93 0.45 0.09 1" specular="0.4" shininess="0.35"/>',
        '<material name="dunkel" rgba="0.20 0.21 0.24 1"/>',
        '<material name="anlage" rgba="0.56 0.59 0.64 1" specular="0.3"/>',
        '<material name="zaun" rgba="0.35 0.70 0.45 0.16"/>',
        '<material name="teil" rgba="0.88 0.89 0.92 1"/>',
        '<material name="gr_koerper" rgba="0.87 0.42 0.09 1"/>',
        '<material name="gr_stahl" rgba="0.62 0.65 0.70 1"/>',
        '<material name="gr_backe" rgba="0.15 0.15 0.17 1"/>',
    ]
    for _, link in [(0, "base_link")] + [(0, "link_%d" % i) for i in range(1, 7)]:
        assets.append('<mesh name="v_%s" file="%s/%s.stl"/>' % (link, rob_v, link))
        assets.append('<mesh name="c_%s" file="%s/%s.stl"/>' % (link, rob_c, link))
    for t in GREIFER_TEILE:
        assets.append('<mesh name="g_%s" file="%s/%s.stl" scale="0.001 0.001 0.001"/>'
                      % (t, MESH_GR, t))
    assets.append('<mesh name="teilB" file="%s/bauteilB.stl" scale="0.001 0.001 0.001"/>'
                  % MESH_GR)

    def rob_geoms(link):
        # contype=1/conaffinity=2: Roboter kollidiert nur mit der Anlage (Gruppe 2)
        return ('<geom type="mesh" mesh="v_%s" material="abb" contype="0" '
                'conaffinity="0" group="0"/>'
                '<geom type="mesh" mesh="c_%s" contype="1" conaffinity="2" '
                'group="3" rgba="1 0 0 0.3"/>' % (link, link))

    # verschachtelte Kette aufbauen
    kette = ""
    zu = ""
    for i, (name, xyz, axis, lim) in enumerate(GELENKE):
        link = "link_%d" % (i + 1)
        kette += ('<body name="%s" pos="%g %g %g">'
                  '<joint name="%s" type="hinge" axis="%d %d %d" range="%g %g"/>'
                  '%s'
                  % (link, xyz[0], xyz[1], xyz[2], name,
                     axis[0], axis[1], axis[2], lim[0], lim[1], rob_geoms(link)))
        zu += "</body>"

    # Greifer am Flansch: tool0 = Flansch um 90 Grad um Y gedreht (siehe xacro),
    # damit zeigt die Werkzeugachse entlang +x von link_6.
    g = '<body name="greifer" pos="0 0 0" euler="0 90 0">'
    farbe = {"pos4": "gr_koerper", "pos7L": "gr_backe", "pos7R": "gr_backe"}
    for t in GREIFER_TEILE:
        g += ('<geom type="mesh" mesh="g_%s" material="%s" contype="1" '
              'conaffinity="2" group="0"/>' % (t, farbe.get(t, "gr_stahl")))
    # Greifpunkt als Referenz (Bauteilmitte zwischen den Backen)
    g += '<site name="tcp" pos="0 0 %g" size="0.006" rgba="1 0 0 1"/>' % (
        L_GREIFER - 0.030)
    g += '<body name="werkstueck" pos="0 0 %g"><geom name="teil" type="mesh" ' \
         'mesh="teilB" material="teil" contype="4" conaffinity="2" group="0"/>' \
         '</body>' % (L_GREIFER - 0.030)
    g += "</body>"

    anlage = f"""
    <geom name="boden" type="plane" size="6 6 0.1" material="boden"
          contype="2" conaffinity="1"/>
    <body name="pufferband" pos="{X_PICK + 0.25} 0 {H_PICK/2}">
      <geom name="g_puffer" type="box" size="0.35 0.25 {H_PICK/2}"
            material="anlage" contype="2" conaffinity="1"/>
    </body>
    <body name="traeger_l" pos="{X_PLACE - 0.15} {DY_KETTE} {H_PLACE/2}">
      <geom name="g_traeger_l" type="box" size="0.30 0.12 {H_PLACE/2}"
            material="anlage" contype="2" conaffinity="1"/>
    </body>
    <body name="traeger_r" pos="{X_PLACE - 0.15} {-DY_KETTE} {H_PLACE/2}">
      <geom name="g_traeger_r" type="box" size="0.30 0.12 {H_PLACE/2}"
            material="anlage" contype="2" conaffinity="1"/>
    </body>
    <body name="zaun_h" pos="{X_PLACE - 0.75} 0 {H_ZAUN/2}">
      <geom name="g_zaun_h" type="box" size="0.02 1.4 {H_ZAUN/2}"
            material="zaun" contype="2" conaffinity="1"/>
    </body>
    <body name="zaun_y1" pos="0 1.4 {H_ZAUN/2}">
      <geom name="g_zaun_y1" type="box" size="1.7 0.02 {H_ZAUN/2}"
            material="zaun" contype="2" conaffinity="1"/>
    </body>
    <body name="zaun_y2" pos="0 -1.4 {H_ZAUN/2}">
      <geom name="g_zaun_y2" type="box" size="1.7 0.02 {H_ZAUN/2}"
            material="zaun" contype="2" conaffinity="1"/>
    </body>
    """

    return f"""
<mujoco model="anlage_gruppe{P.GRUPPE}">
  <compiler angle="degree" meshdir="."/>
  <option gravity="0 0 -9.81"/>
  <visual>
    <global offwidth="1920" offheight="1200"/>
    <quality shadowsize="8192" offsamples="8"/>
    <headlight ambient="0.40 0.40 0.43" diffuse="0.45 0.45 0.45" specular="0.15 0.15 0.15"/>
    <map znear="0.01" zfar="50"/>
  </visual>
  <asset>{"".join(assets)}</asset>
  <worldbody>
    <light pos="2 -2 3.5" dir="-0.5 0.5 -0.8" diffuse="0.55 0.55 0.55"/>
    <light pos="-2 2 3" dir="0.5 -0.5 -0.8" diffuse="0.30 0.30 0.32"/>
    {anlage}
    <body name="sockel" pos="{base_x} 0 {h_sockel/2}">
      <geom name="g_sockel" type="cylinder" size="0.22 {max(h_sockel,0.001)/2}"
            material="dunkel" contype="1" conaffinity="2"/>
    </body>
    <body name="base_link" pos="{base_x} 0 {h_sockel}">
      <geom type="mesh" mesh="v_base_link" material="dunkel" contype="0" conaffinity="0"/>
      <geom type="mesh" mesh="c_base_link" contype="1" conaffinity="2" group="3"
            rgba="1 0 0 0.3"/>
      {kette}{g}{zu}
    </body>
  </worldbody>
</mujoco>
"""


# ------------------------------------------------------------------ Kinematik
def tcp_pose(m, d):
    sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "tcp")
    return d.site_xpos[sid].copy(), d.site_xmat[sid].reshape(3, 3).copy()


W_ORI = 0.5          # Gewichtung der Orientierungs- gegen die Lageabweichung


def _ik_fehler(m, d, p_ziel, R_ziel):
    p, R = tcp_pose(m, d)
    e_p = p_ziel - p
    aa = np.zeros(3)
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, np.ascontiguousarray(R_ziel @ R.T).flatten())
    mujoco.mju_quat2Vel(aa, q, 1.0)
    return e_p, aa


def _ik_lauf(m, d, p_ziel, R_ziel, q0, iter=400):
    """Ein Levenberg-Marquardt-Lauf mit adaptiver Daempfung."""
    sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "tcp")
    lo, hi = m.jnt_range[:6, 0], m.jnt_range[:6, 1]
    jacp, jacr = np.zeros((3, m.nv)), np.zeros((3, m.nv))

    d.qpos[:6] = np.clip(q0, lo, hi)
    mujoco.mj_forward(m, d)
    e_p, aa = _ik_fehler(m, d, p_ziel, R_ziel)
    kost = np.linalg.norm(e_p) ** 2 + (W_ORI * np.linalg.norm(aa)) ** 2
    lam = 0.05

    for _ in range(iter):
        if kost < 1e-10:
            break
        mujoco.mj_jacSite(m, d, jacp, jacr, sid)
        J = np.vstack([jacp[:, :6], W_ORI * jacr[:, :6]])
        err = np.concatenate([e_p, W_ORI * aa])
        dq = J.T @ np.linalg.solve(J @ J.T + lam ** 2 * np.eye(6), err)

        q_alt = d.qpos[:6].copy()
        d.qpos[:6] = np.clip(q_alt + dq, lo, hi)
        mujoco.mj_forward(m, d)
        e_p2, aa2 = _ik_fehler(m, d, p_ziel, R_ziel)
        kost2 = np.linalg.norm(e_p2) ** 2 + (W_ORI * np.linalg.norm(aa2)) ** 2

        if kost2 < kost:                 # Schritt war gut -> weniger daempfen
            kost, e_p, aa = kost2, e_p2, aa2
            lam = max(lam * 0.7, 1e-4)
        else:                            # Schritt war schlecht -> zurueck, mehr daempfen
            d.qpos[:6] = q_alt
            mujoco.mj_forward(m, d)
            lam = min(lam * 2.5, 10.0)
            if lam >= 10.0:
                break

    return d.qpos[:6].copy(), np.linalg.norm(e_p), np.linalg.norm(aa)


def _entwirre(q, q0, lo, hi):
    """Waehlt fuer jedes Gelenk das um k*360 Grad versetzte Aequivalent,
    das der Vorgaengerstellung am naechsten liegt (A4 und A6 koennen mehr
    als eine Umdrehung, dort ist +180 Grad und -180 Grad dieselbe Pose)."""
    aus = q.copy()
    for i in range(len(q)):
        kand = [q[i] + k * 2 * np.pi for k in (-2, -1, 0, 1, 2)]
        kand = [c for c in kand if lo[i] - 1e-9 <= c <= hi[i] + 1e-9]
        if kand:
            aus[i] = min(kand, key=lambda c: abs(c - q0[i]))
    return aus


def ik(m, d, p_ziel, R_ziel, q0, tol=1e-3, neustarts=12, rng=None):
    """IK mit Mehrfachstart UND Konfigurationstreue.

    Zwei Fallstricke, die hier beide auftreten:

    1. Ein einzelner gradientenbasierter Lauf bleibt bei 6-achsigen Knickarmen
       in lokalen Minima haengen. Deshalb mehrere Startwerte.

    2. Waehlt man unter den Loesungen einfach die mit dem kleinsten Restfehler,
       springt der Arm zwischen den Stuetzpunkten in eine andere Konfiguration
       (Ellbogen um, Handgelenk geklappt) - bis zu 360 Grad in einer Achse.
       Solche Spruenge sind weder fahrbar noch taktzeitgerecht, und eine
       Kollisionspruefung entlang einer solchen Bahn ist wertlos.
       Deshalb: unter allen ausreichend genauen Loesungen die waehlen, die der
       Vorgaengerstellung am naechsten liegt.
    """
    rng = rng or np.random.default_rng(0)
    lo, hi = m.jnt_range[:6, 0], m.jnt_range[:6, 1]
    lo_s, hi_s = np.maximum(lo, -np.pi), np.minimum(hi, np.pi)
    q0 = np.clip(q0, lo, hi)

    # Grundachsen staerker gewichten: ein Sprung in A1 bewegt den ganzen Arm
    gew = np.array([3.0, 2.0, 2.0, 1.0, 1.0, 0.5])

    treffer = []
    for k in range(neustarts):
        start = q0 if k == 0 else rng.uniform(lo_s, hi_s)
        q, e_p, e_o = _ik_lauf(m, d, p_ziel, R_ziel, start)
        if e_p < tol and e_o < 0.02:
            q = _entwirre(q, q0, lo, hi)
            treffer.append((np.linalg.norm(gew * (q - q0)), q, e_p))
        if len(treffer) >= 4 and k >= 5:
            break

    if treffer:
        treffer.sort(key=lambda t: t[0])
        best_q, best_p = treffer[0][1], treffer[0][2]
    else:
        # nichts im Toleranzband - beste Naeherung zurueckgeben
        best_q, best_p, _ = _ik_lauf(m, d, p_ziel, R_ziel, q0)

    d.qpos[:6] = best_q
    mujoco.mj_forward(m, d)
    return best_q, best_p


def R_greifer(drehung):
    """Werkzeugachse nach unten, Greifrichtung um 'drehung' um z gedreht."""
    cz, sz = np.cos(drehung), np.sin(drehung)
    x = np.array([cz, sz, 0.0])          # Greifrichtung (Backen)
    z = np.array([0.0, 0.0, -1.0])       # Werkzeugachse zeigt nach unten
    y = np.cross(z, x)
    return np.column_stack([x, y, z])


# ------------------------------------------------------------------ Bahn
def stuetzpunkte():
    """Bahnstuetzpunkte des Arbeitsablaufes (Position, Orientierung, Bezeichnung)."""
    z_griff_pick = H_PICK + Z_GRIFF + H_TEIL / 2
    z_griff_place = H_PLACE + Z_GRIFF + H_TEIL / 2
    R_p = R_greifer(0.0)
    R_a = R_greifer(DREHUNG_ABLAGE)
    frei = 0.18
    return [
        ("Grundstellung",      np.array([0.85, 0.0, 1.45]), R_p),
        ("Anfahrt Entnahme",   np.array([X_PICK, 0.0, z_griff_pick + frei]), R_p),
        ("Entnahme",           np.array([X_PICK, 0.0, z_griff_pick]), R_p),
        ("Abheben",            np.array([X_PICK, 0.0, z_griff_pick + frei]), R_p),
        # Der Transportpunkt darf NICHT ueber der Achse 1 liegen (x=y=0):
        # dort ist die Grundachse unbestimmt (Basissingularitaet) und die
        # Loesung kippt in eine andere Konfiguration. Stattdessen auf der
        # Schwenkbahn, die A1 ohnehin von der Entnahme zur Ablage nimmt.
        ("Transport",          np.array([0.0, 0.80, 1.45]), R_greifer(np.pi / 2)),
        ("Anfahrt Ablage",     np.array([X_PLACE, DY_KETTE, z_griff_place + frei]), R_a),
        ("Ablage",             np.array([X_PLACE, DY_KETTE, z_griff_place]), R_a),
        ("Rueckzug",           np.array([X_PLACE, DY_KETTE, z_griff_place + frei]), R_a),
    ]


def bahn(m, d, n_zwischen=14, still=False):
    """Gelenkwinkel entlang der Bahn; linear zwischen den Stuetzpunkten."""
    pts = stuetzpunkte()
    q = np.zeros(6)
    knoten = []
    if not still:
        print("STUETZPUNKTE (IK)")
    for name, p, R in pts:
        q, res = ik(m, d, p, R, q)
        if not still:
            ok = "ok" if res < 1e-3 else "RESTFEHLER %.1f mm" % (res * 1000)
            print("  %-20s (%6.3f %6.3f %6.3f)  %s" % (name, p[0], p[1], p[2], ok))
        knoten.append((name, q.copy(), res))

    traj = []
    for i in range(len(knoten) - 1):
        qa, qb = knoten[i][1], knoten[i + 1][1]
        for k in range(n_zwischen):
            s = k / float(n_zwischen)
            # Rampe statt linear, damit die Bewegung nicht ruckt
            s = 3 * s ** 2 - 2 * s ** 3
            traj.append((knoten[i][0], knoten[i + 1][0], qa + s * (qb - qa)))
    traj.append((knoten[-1][0], knoten[-1][0], knoten[-1][1]))
    return knoten, traj


# ------------------------------------------------------------------ Kollision
def kollisionen(m, d):
    """Kontaktpaare zwischen Roboter/Greifer (Gruppe 1) und Anlage (Gruppe 2)."""
    treffer = []
    for i in range(d.ncon):
        c = d.contact[i]
        g1, g2 = c.geom1, c.geom2
        t1 = m.geom_contype[g1], m.geom_conaffinity[g1]
        t2 = m.geom_contype[g2], m.geom_conaffinity[g2]
        # nur Roboter/Werkstueck (contype 1 oder 4) gegen Anlage (contype 2)
        paar = {t1[0], t2[0]}
        if 2 in paar and (1 in paar or 4 in paar):
            n1 = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g1) or "geom%d" % g1
            n2 = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g2) or "geom%d" % g2
            treffer.append((n1, n2, -c.dist))
    return treffer


# ------------------------------------------------------------------ Rendern
def rendere(m, d, name, cam):
    r = mujoco.Renderer(m, 1200, 1920)
    c = mujoco.MjvCamera()
    c.type = mujoco.mjtCamera.mjCAMERA_FREE
    c.lookat[:] = [0.0, 0.0, 1.0]
    c.distance, c.azimuth, c.elevation = cam
    r.update_scene(d, camera=c)
    f = os.path.join(OUT, name)
    Image.fromarray(r.render()).save(f)
    r.close()
    return f


def main():
    print("ARBEITSABLAUF UND KOLLISIONSKONTROLLE")
    print("Gruppe %d, Bauteil %s, %s\n" % (P.GRUPPE, P.BAUTEIL, P.ROBOTER))

    m = mujoco.MjModel.from_xml_string(mjcf(BASE_X, H_SOCKEL))
    d = mujoco.MjData(m)
    print("  Modell: %d Koerper, %d Geome, %d Gelenke\n" % (m.nbody, m.ngeom, m.njnt))

    knoten, traj = bahn(m, d)

    print("\nKOLLISIONSKONTROLLE ueber %d Bahnpunkte" % len(traj))
    gefunden = {}
    for k, (von, nach, q) in enumerate(traj):
        d.qpos[:6] = q
        mujoco.mj_forward(m, d)
        for n1, n2, tiefe in kollisionen(m, d):
            schl = tuple(sorted((n1, n2)))
            if schl not in gefunden or tiefe > gefunden[schl][1]:
                gefunden[schl] = ("%s -> %s" % (von, nach), tiefe)

    if gefunden:
        print("  %-44s %-28s %s" % ("Geometriepaar", "Bahnabschnitt", "Eindringtiefe"))
        print("  " + "-" * 92)
        for (n1, n2), (abschnitt, tiefe) in sorted(
                gefunden.items(), key=lambda x: -x[1][1]):
            print("  %-44s %-28s %8.1f mm"
                  % ("%s / %s" % (n1, n2), abschnitt, tiefe * 1000))
        print("\n  %d Kollisionspaare - Bahn ist NICHT freigegeben." % len(gefunden))
    else:
        print("  keine Kollisionen - Bahn ist kollisionsfrei.")

    print("\nBilder")
    for i, (name, q, res) in enumerate(knoten):
        d.qpos[:6] = q
        mujoco.mj_forward(m, d)
        f = rendere(m, d, "ablauf_%d_%s.png"
                    % (i, name.lower().replace(" ", "_").replace("ü", "ue")),
                    (4.2, 128, -14))
        print("  ->", os.path.relpath(f, os.path.join(HIER, "..")))

    return gefunden


if __name__ == "__main__":
    main()
