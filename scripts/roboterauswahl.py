"""Abgabepunkt 1 - Roboterauswahl, Gruppe 2 / Bauteil B.

Anforderungen (hergeleitet in auslegung_B.py und build_scene.py):
  Reichweite   >= 1308 mm  (aeussere Foerderkette, 1300 mm Hoehe, 300 mm seitlich)
  Traglast     >= 3,1 kg   (0,60 kg Bauteil + 2,5 kg Greifer), mit Reserve 5 kg
  TCP-Bahngeschw. 1,37 m/s ; Bahnbeschl. 2,05 m/s2
"""
import numpy as np

R_REQ, M_REQ, V_REQ, A_REQ = 1308.0, 3.1, 1.37, 2.05

# Datenblattwerte (Quellen im Bericht), J1 = Grundachse
KAND = [
    # Name,                     Reichw.[mm], Traglast[kg], J1[deg/s], ros-industrial
    ("ABB IRB 1600-6/1.45",     1450, 6,  150, "abb_irb1600_support"),
    ("KUKA KR 10 R1420",        1420, 10, 210, "kuka_experimental"),
    ("FANUC M-10iD/12",         1441, 12, 210, "fanuc_m10_support"),
]

print("ANFORDERUNG:  R >= %.0f mm | m >= %.1f kg | v = %.2f m/s | a = %.2f m/s2\n"
      % (R_REQ, M_REQ, V_REQ, A_REQ))
print("%-22s %8s %8s %10s %10s  %s" %
      ("Modell", "R [mm]", "m [kg]", "v_TCP", "Reserve", "Bewertung"))
print("-" * 88)

for name, R, M, J1, pkg in KAND:
    # TCP-Bahngeschwindigkeit aus Grundachse: v = omega * r, r = horizontaler Arbeitsradius
    r_arb = R_REQ / 1000.0
    v_tcp = np.deg2rad(J1) * r_arb
    ok_R, ok_M, ok_v = R >= R_REQ, M >= M_REQ, v_tcp >= V_REQ
    res = R - R_REQ
    verdikt = "geeignet" if (ok_R and ok_M and ok_v) else "ungeeignet"
    flags = []
    if not ok_R: flags.append("Reichweite")
    if not ok_M: flags.append("Traglast")
    if not ok_v: flags.append("Geschwindigkeit")
    if flags: verdikt += " (" + ", ".join(flags) + ")"
    print("%-22s %8.0f %8.1f %8.2f m/s %7.0f mm  %s" % (name, R, M, v_tcp, res, verdikt))

print("\nGEGENPROBE - Klasse der Kollaborativen (TCP-Geschwindigkeit begrenzt):")
for name, R, M, vmax in [("Universal Robots UR10e", 1300, 12.5, 1.00)]:
    ok = (R >= R_REQ) and (vmax >= V_REQ)
    print("  %-24s R=%4.0f mm  m=%4.1f kg  v_max=%.2f m/s -> %s"
          % (name, R, M, vmax, "geeignet" if ok else
             "ungeeignet (Reichweite %.0f mm < %.0f, v %.2f < %.2f m/s)" % (R, R_REQ, vmax, V_REQ)))

print("\nAUSLEGUNGSPUNKT")
m_ges = 3.1
print("  Gewaehlt: ABB IRB 1600-6/1.45")
print("  - Reichweite 1450 mm, Reserve %.0f mm ueber dem kritischen Punkt" % (1450-R_REQ))
print("  - Traglast 6,0 kg, Auslastung %.0f %% (Bauteil + Greifer = %.1f kg)" % (m_ges/6*100, m_ges))
print("  - v_TCP aus J1 = %.2f m/s, das %.1f-fache der geforderten %.2f m/s"
      % (np.deg2rad(150)*1.308, np.deg2rad(150)*1.308/V_REQ, V_REQ))
print("  - 3D-Modell als URDF in ros-industrial (abb_irb1600_support) verfuegbar")
