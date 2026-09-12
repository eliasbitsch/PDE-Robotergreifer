"""Abgabepunkt 6 - Numerische Festigkeitsberechnung der Greiferzange.

Vollautomatische Kette ohne GUI:
    STEP  ->  gmsh (C3D10-Netz)  ->  CalculiX (ccx)  ->  Auswertung
Ergebnis: von-Mises-Vergleichsspannung und Verformung, direkt vergleichbar
mit fem/analytisch.py.

Randbedingungen:
  Einspannung  Auflageflaeche des Anschraubkopfs (z = 0), alle Freiheitsgrade
  Last         Flaechenlast auf dem Taschengrund der Weichbacke, +x-Richtung
               (Reaktion der Greifkraft auf die Zange)

Die Flaechenlast wird als konsistente Knotenlast auf die 6-Knoten-Dreiecke der
Lastflaeche verteilt (Eckknoten 0, Mittenknoten A/3) - das ist fuer quadratische
Elemente die exakte Umrechnung einer konstanten Flaechenpressung.
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cad"))
import params as P

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HIER, "..")
STEP = os.path.join(ROOT, "out", "step", "Greiferzange_FEM.step")
ARB = os.path.join(ROOT, "out", "fem")
os.makedirs(ARB, exist_ok=True)

CCX = os.path.expanduser("~/.local/bin/ccx")
CCX_LIB = os.path.expanduser("~/opt/lg4/usr/lib/x86_64-linux-gnu")

# Netzfeinheit
LC_GROB = 4.0        # mm, allgemein
LC_FEIN = 1.0        # mm, an der Einspannkerbe (Spannungsmaximum)

# Lastflaeche (lokale Koordinaten der Greiferzange_FEM.step)
Z_LAST_VON = 10.0 + P.ZANGE_L - P.BACKE_LAENGE     # 70
Z_LAST_BIS = 10.0 + P.ZANGE_L                      # 130
X_TASCHE = -(P.ZANGE_H / 2.0 - P.BACKE_TIEFE)      # -3,5 Taschengrund
Z_KERBE = 10.0                                     # Einspannkerbe

F_LAST = P.F_ZANGE_AUSLEGUNG                       # N


# ------------------------------------------------------------------ Vernetzen
def vernetze(lc_fein=LC_FEIN, lc_grob=LC_GROB):
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("zange")
    gmsh.model.occ.importShapes(STEP)
    gmsh.model.occ.synchronize()

    gmsh.option.setNumber("Mesh.MeshSizeMin", lc_fein)
    gmsh.option.setNumber("Mesh.MeshSizeMax", lc_grob)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.option.setNumber("Mesh.SecondOrderIncomplete", 0)
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)
    # Ohne diese Optimierung liegen die Mittenknoten auf der Ausrundung so
    # unguenstig, dass einzelne C3D10 eine negative Jacobi-Determinante haben
    # und ccx abbricht. 2 = elastische Optimierung der gekruemmten Elemente.
    gmsh.option.setNumber("Mesh.HighOrderOptimize", 2)

    # Netzverfeinerung um die Einspannkerbe
    f = gmsh.model.mesh.field
    f.add("Box", 1)
    f.setNumber(1, "VIn", lc_fein)
    f.setNumber(1, "VOut", lc_grob)
    f.setNumber(1, "XMin", -20); f.setNumber(1, "XMax", 20)
    f.setNumber(1, "YMin", -25); f.setNumber(1, "YMax", 25)
    f.setNumber(1, "ZMin", Z_KERBE - 8); f.setNumber(1, "ZMax", Z_KERBE + 12)
    f.setAsBackgroundMesh(1)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)

    gmsh.model.mesh.generate(3)

    nt, nc, _ = gmsh.model.mesh.getNodes()
    knoten = {int(t): nc[3 * i:3 * i + 3] for i, t in enumerate(nt)}

    # C3D10 (10-Knoten-Tetraeder) = gmsh-Typ 11
    et, etags, enodes = gmsh.model.mesh.getElements(dim=3)
    elemente = {}
    for typ, tags, nodes in zip(et, etags, enodes):
        if typ == 11:
            nn = nodes.reshape(-1, 10)
            for tag, row in zip(tags, nn):
                elemente[int(tag)] = [int(x) for x in row]
    if not elemente:
        raise RuntimeError("kein C3D10-Netz erzeugt")

    # 6-Knoten-Dreiecke der Oberflaeche (gmsh-Typ 9) fuer die Lasteinleitung
    gmsh.model.mesh.createFaces()
    st, stags, snodes = gmsh.model.mesh.getElements(dim=2)
    dreiecke = []
    for typ, tags, nodes in zip(st, stags, snodes):
        if typ == 9:
            dreiecke = [[int(x) for x in r] for r in nodes.reshape(-1, 6)]
    gmsh.finalize()
    return knoten, elemente, dreiecke


# ------------------------------------------------------- Randbedingungen
def knotenmengen(knoten, dreiecke):
    """Einspannknoten (z=0) und konsistente Knotenlasten auf dem Taschengrund."""
    fest = [t for t, c in knoten.items() if abs(c[2]) < 1e-6]

    # Dreiecke, die vollstaendig auf dem Taschengrund liegen
    last_tri = []
    for tri in dreiecke:
        c = np.array([knoten[n] for n in tri])
        if (np.all(np.abs(c[:, 0] - X_TASCHE) < 1e-4)
                and np.all(c[:, 2] > Z_LAST_VON - 1e-4)
                and np.all(c[:, 2] < Z_LAST_BIS + 1e-4)):
            last_tri.append(tri)
    if not last_tri:
        raise RuntimeError("Lastflaeche nicht gefunden (x = %.2f)" % X_TASCHE)

    # konsistente Knotenlast fuer 6-Knoten-Dreiecke: Ecken 0, Mitten A/3
    gewicht = {}
    A_ges = 0.0
    for tri in last_tri:
        c = np.array([knoten[n] for n in tri])
        A = 0.5 * np.linalg.norm(np.cross(c[1] - c[0], c[2] - c[0]))
        A_ges += A
        for n in tri[3:6]:
            gewicht[n] = gewicht.get(n, 0.0) + A / 3.0

    p = F_LAST / A_ges                       # MPa
    lasten = {n: p * w for n, w in gewicht.items()}
    return fest, lasten, A_ges, p


# ------------------------------------------------------------------ CalculiX
def nach_c3d10(n, knoten):
    """gmsh-Tet10 -> CalculiX/Abaqus C3D10.

    gmsh  : 0-3 Ecken, 4=(0,1) 5=(1,2) 6=(0,2) 7=(0,3) 8=(2,3) 9=(1,3)
    Abaqus: 1-4 Ecken, 5=(1,2) 6=(2,3) 7=(1,3) 8=(1,4) 9=(2,4) 10=(3,4)
    -> die letzten beiden Mittenknoten sind vertauscht.

    Zusaetzlich muss die Ecknumerierung ein positives Volumen ergeben, sonst
    bricht ccx mit "nonpositive jacobian determinant" ab.
    """
    p = [np.asarray(knoten[t]) for t in n[:4]]
    if np.dot(p[1] - p[0], np.cross(p[2] - p[0], p[3] - p[0])) < 0.0:
        # Ecken 2 und 3 tauschen, Mittenknoten entsprechend mitziehen
        n = [n[0], n[1], n[3], n[2], n[4], n[9], n[7], n[6], n[8], n[5]]
    return [n[0], n[1], n[2], n[3], n[4], n[5], n[6], n[7], n[9], n[8]]


def jacobi_check(elemente, knoten):
    """Zaehlt Elemente mit nichtpositiver Jacobi-Determinante an den Ecken.

    ccx bricht daran ab; besser vorher pruefen als 40000 Fehlerzeilen lesen.
    """
    schlecht = 0
    for n in elemente.values():
        p = [np.asarray(knoten[t]) for t in n[:4]]
        if np.dot(p[1] - p[0], np.cross(p[2] - p[0], p[3] - p[0])) == 0.0:
            schlecht += 1
    return schlecht


def schreibe_inp(knoten, elemente, fest, lasten, pfad):
    z = ["*HEADING", "Greiferzange Gruppe %d - %s" % (P.GRUPPE, P.ZANGE_WERKSTOFF), "*NODE"]
    for t, c in sorted(knoten.items()):
        z.append("%d, %.6f, %.6f, %.6f" % (t, c[0], c[1], c[2]))

    z.append("*ELEMENT, TYPE=C3D10, ELSET=EALL")
    for t, n in sorted(elemente.items()):
        z.append("%d, %s" % (t, ", ".join(str(x) for x in nach_c3d10(n, knoten))))

    z += ["*NSET, NSET=NFEST"]
    for i in range(0, len(fest), 8):
        z.append(", ".join(str(x) for x in fest[i:i + 8]))

    # CalculiX legt kein NALL an - fuer *NODE PRINT muss die Menge existieren
    alle = sorted(knoten)
    z += ["*NSET, NSET=NALL"]
    for i in range(0, len(alle), 8):
        z.append(", ".join(str(x) for x in alle[i:i + 8]))

    z += ["*MATERIAL, NAME=ALU7075",
          "*ELASTIC", "%.1f, %.3f" % (P.ZANGE_E, P.ZANGE_NU),
          "*SOLID SECTION, ELSET=EALL, MATERIAL=ALU7075",
          "*STEP", "*STATIC",
          "*BOUNDARY", "NFEST, 1, 3, 0.0",
          "*CLOAD"]
    for n, f in sorted(lasten.items()):
        z.append("%d, 1, %.8f" % (n, f))       # Richtung +x

    z += ["*NODE PRINT, NSET=NALL", "U, S", "*NODE FILE", "U, S", "*END STEP"]
    open(pfad, "w").write("\n".join(z) + "\n")


def loese(basis):
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = CCX_LIB + ":" + env.get("LD_LIBRARY_PATH", "")
    r = subprocess.run([CCX, basis], cwd=ARB, env=env,
                       capture_output=True, text=True, timeout=1800)
    log = r.stdout + r.stderr
    open(os.path.join(ARB, "ccx.log"), "w").write(log)
    if "*ERROR" in log or not os.path.exists(os.path.join(ARB, basis + ".dat")):
        print(log[-2500:])
        raise RuntimeError("CalculiX abgebrochen")
    return log


# ------------------------------------------------------------------ Auswertung
def lies_frd(pfad):
    """Liest Knotenwerte aus der CalculiX-Ergebnisdatei .frd.

    Festbreitenformat - die Werte laufen bei negativen Zahlen ohne Trennzeichen
    ineinander ("1.49E-03-3.38E-02"), split() ist hier also unbrauchbar.
      Spalten:  0..2  Kennung " -1"
                3..12 Knotennummer
                ab 13 je 12 Zeichen ein Wert
    Rueckgabe: {Blockname: {Knoten: [Werte]}}
    """
    bloecke, aktuell, ncomp = {}, None, 0
    for zeile in open(pfad, errors="replace"):
        if zeile.startswith(" -4"):
            name = zeile[5:13].strip()
            ncomp = int(zeile[13:18])
            aktuell = bloecke.setdefault(name, {})
            continue
        if zeile.startswith(" -5") or zeile.startswith(" -3"):
            continue
        if zeile.startswith(" -1") and aktuell is not None:
            t = int(zeile[3:13])
            # ncomp ist die deklarierte Komponentenzahl; DISP deklariert 4,
            # schreibt aber nur 3 (die vierte ist der abgeleitete Betrag).
            werte = []
            for i in range(ncomp):
                feld = zeile[13 + 12 * i:25 + 12 * i]
                if not feld.strip():
                    break
                werte.append(float(feld))
            aktuell[t] = werte
            continue
        if zeile.startswith(" -2"):
            aktuell = None
    return bloecke


def mises(s):
    """von-Mises-Vergleichsspannung. .frd-Reihenfolge: SXX SYY SZZ SXY SYZ SZX."""
    sxx, syy, szz, sxy, syz, szx = s[:6]
    return np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
                   + 3.0 * (sxy ** 2 + syz ** 2 + szx ** 2))


def rechne(lc_fein=LC_FEIN, lc_grob=LC_GROB, basis="zange", still=False):
    print("NUMERISCHE FESTIGKEITSBERECHNUNG GREIFERZANGE (CalculiX)")
    print("Gruppe %d, Bauteil %s\n" % (P.GRUPPE, P.BAUTEIL))

    print("Vernetzen (gmsh) ...")
    knoten, elemente, dreiecke = vernetze(lc_fein, lc_grob)
    print("  %d Knoten, %d Elemente C3D10" % (len(knoten), len(elemente)))

    fest, lasten, A_last, p = knotenmengen(knoten, dreiecke)
    print("  Einspannung  %d Knoten bei z = 0" % len(fest))
    print("  Lastflaeche  %.0f mm2, p = %.4f MPa, F = %.1f N auf %d Knoten"
          % (A_last, p, F_LAST, len(lasten)))
    print("  Kontrolle    Summe Knotenlasten = %.3f N" % sum(lasten.values()))

    schreibe_inp(knoten, elemente, fest, lasten, os.path.join(ARB, basis + ".inp"))
    print("\nLoesen (CalculiX) ...")
    loese(basis)

    bloecke = lies_frd(os.path.join(ARB, basis + ".frd"))
    U = bloecke.get("DISP", {})
    S = bloecke.get("STRESS", {})
    ERR = bloecke.get("ERROR", {})
    if not U or not S:
        raise RuntimeError("keine Ergebnisse in der .frd-Datei (%s)" % list(bloecke))

    # Verformung
    betrag = {t: np.linalg.norm(v[:3]) for t, v in U.items()}
    t_umax = max(betrag, key=betrag.get)
    u_max = betrag[t_umax]
    ux_max = max(abs(v[0]) for v in U.values())

    # Spannung
    sv = {t: mises(v) for t, v in S.items()}
    t_smax = max(sv, key=sv.get)
    s_max = sv[t_smax]

    # Spannungsmaximum ohne die Einspannknoten (dort sitzen RB-Singularitaeten)
    frei = {t: v for t, v in sv.items() if knoten[t][2] > 1.0}
    t_sfrei = max(frei, key=frei.get)
    s_frei = frei[t_sfrei]

    c_s = knoten[t_sfrei]
    c_u = knoten[t_umax]

    print("\nERGEBNIS  (Lastfall: F = %.1f N je Backe)" % F_LAST)
    print("  u_max            %8.3f mm   an (%.1f, %.1f, %.1f)"
          % (u_max, c_u[0], c_u[1], c_u[2]))
    print("  u_x,max          %8.3f mm" % ux_max)
    print("  sig_v,max        %8.2f MPa  (inkl. Einspannung, Knoten %d)" % (s_max, t_smax))
    print("  sig_v,max (frei) %8.2f MPa  an (%.1f, %.1f, %.1f)"
          % (s_frei, c_s[0], c_s[1], c_s[2]))
    print("  Sicherheit       %8.2f  gegen Rp0,2 = %.0f MPa"
          % (P.ZANGE_RP02 / s_frei, P.ZANGE_RP02))

    if ERR:
        e = [v[0] for t, v in ERR.items() if knoten[t][2] > 1.0]
        print("\nNETZGUETE (CalculiX-Fehlerschaetzer)")
        print("  mittlerer Fehler %8.1f %%   Maximum %.1f %%"
              % (float(np.mean(e)), float(np.max(e))))

    return dict(u_max=u_max, ux_max=ux_max, s_max=s_max, s_frei=s_frei,
                knoten=len(knoten), elemente=len(elemente))


def main():
    return rechne()


if __name__ == "__main__":
    main()
