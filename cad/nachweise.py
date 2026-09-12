"""Maskette und Nachweise - woher jede Hauptabmessung kommt.

Jede Abmessung des Greifers muss herleitbar sein: aus dem Bauteil, aus einer
Rechnung, aus einer Norm oder aus der Fertigung. Dieses Skript fuehrt die
Herleitung und markiert, was noch reine Annahme ist.

Aufruf:  python nachweise.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params as P

BELEGT, ANNAHME = "belegt", "ANNAHME"
zeilen = []


def masse(groesse, wert, einheit, herleitung, art=BELEGT):
    zeilen.append((groesse, wert, einheit, herleitung, art))


# ================================================================ Bauteil
masse("Greifabstand", P.GREIF_ABSTAND, "mm",
      "Flaechenpaar 1/2 aus Bauteil_B.STEP, Normale +-X (analyze_B.py)")
masse("Greifflaeche", P.GREIF_FLAECHE, "mm2",
      "kleinere der beiden gegenueberliegenden Flaechen")
masse("Bauteilmasse", P.B_MASSE, "kg",
      "V = %.1f cm3 aus dem STEP, PA 6 mit rho = %.0f kg/m3 (Tab.1)"
      % (P.B_VOL * 1e6, P.B_RHO))

# ================================================================ Greifkraft
masse("Bahnbeschleunigung", P.A_BAHN, "m/s2",
      "Trapezprofil ueber %.2f s Verfahrzeit, t_a = t/3 (Abb.1: %.1f s Takt)"
      % (P.T_EINWEG, P.TAKTZEIT))
masse("Greifkraft erforderlich", P.F_GREIF, "N",
      "F = S*m*(g+a)/(n*mu) mit S = %.1f, mu = %.2f, n = %d"
      % (P.S_SICHERHEIT, P.MU_BELAG, P.N_BACKEN))
masse("Backenhub", P.GREIFER_HUB, "mm",
      "(Bauteilbreite %.0f - Greifabstand %.0f)/2 = %.1f mm plus %.1f mm Freigang"
      % (P.B_BBOX[0], P.GREIF_ABSTAND,
         (P.B_BBOX[0] - P.GREIF_ABSTAND) / 2, P.FREIGANG))

# ================================================================ Antrieb
masse("Teilkreisradius Ritzel", P.R_TEILKREIS, "mm",
      "m = %.1f, z = %d; z > 17 vermeidet Unterschnitt ohne Profilverschiebung"
      % (P.MODUL, P.Z_RITZEL))
ritzel_drehung = P.GREIFER_HUB / (2 * math.pi * P.R_TEILKREIS) * 360
masse("Ritzeldrehung fuer Hub", ritzel_drehung, "Grad",
      "s = %.0f mm auf dem Teilkreis Ø%.0f mm" % (P.GREIFER_HUB, 2 * P.R_TEILKREIS))
n_noetig = (ritzel_drehung / 360) * P.GETRIEBE_I / P.T_GREIFEN * 60
masse("Motordrehzahl noetig", n_noetig, "1/min",
      "%.0f Grad Ritzeldrehung mal i = %.0f in %.2f s Schliesszeit"
      % (ritzel_drehung, P.GETRIEBE_I, P.T_GREIFEN))
M_noetig = 2 * P.F_GREIF * P.R_TEILKREIS / 1000 / P.ETA_GETRIEBE / P.GETRIEBE_I / P.GETRIEBE_ETA
masse("Motormoment noetig", M_noetig, "Nm",
      "2 Backen x %.1f N am Radius %.0f mm, durch i = %.0f und eta"
      % (P.F_GREIF, P.R_TEILKREIS, P.GETRIEBE_I))
masse("Motormoment gewaehlt", P.MOTOR_M_NENN, "Nm",
      "NEMA 17; Reserve %.1f-fach gegenueber %.3f Nm"
      % (P.MOTOR_M_NENN / M_noetig, M_noetig))

# ================================================================ Verzahnung
F_t = P.GREIFER_F_MAX
sigma_F = F_t / (P.B_ZAHN * P.MODUL) * 4.3
masse("Zahnbreite", P.B_ZAHN, "mm",
      "sigma_F = F_t/(b*m)*Y = %.0f N/mm2 bei F_t = %.1f N; "
      "16MnCr5 einsatzgehaertet zul. ca. 500 N/mm2" % (sigma_F, F_t))

# ================================================================ Zange
masse("Zangenlaenge", P.ZANGE_L, "mm",
      "Luft %.0f + Randmass (%.0f Bauteilhoehe - %.0f Backe)/2 + Backe %.0f; "
      "Greifflaeche laeuft ueber die volle Bauteilhoehe (analyze_B.py)"
      % (P.LUFT_BAUTEIL, P.B_BBOX[2], P.BACKE_LAENGE, P.BACKE_LAENGE))
A_LAST = P.ZANGE_A_LAST
masse("Kraftarm an der Zange", A_LAST, "mm",
      "Mitte der Weichbacke ab Einspannung: %.0f - %.0f/2"
      % (P.ZANGE_L, P.BACKE_LAENGE))
M_b = P.F_ZANGE_AUSLEGUNG * A_LAST
W_b = P.ZANGE_B * P.ZANGE_H ** 2 / 6
masse("Zangenquerschnitt b x h", P.ZANGE_B, "mm (Breite)",
      "sigma = M/W = %.0f/%.0f = %.1f N/mm2, mit a_k = 1.62 -> %.1f N/mm2; "
      "Sicherheit %.1f gegen Rp0,2 = %.0f"
      % (M_b, W_b, M_b / W_b, M_b / W_b * 1.62,
         P.ZANGE_RP02 / (M_b / W_b * 1.62), P.ZANGE_RP02))
masse("Ausrundung Einspannung", P.ZANGE_FILLET, "mm",
      "r/d = %.2f, D/d = %.2f -> a_k = 1.62 (Roloff/Matek); FEM bestaetigt 1.4"
      % (P.ZANGE_FILLET / P.ZANGE_H, (P.ZANGE_H + 12) / P.ZANGE_H))

# ================================================================ Gehaeuse
import mechanik as M
masse("Gehaeuselaenge", M.GEH_X, "mm",
      "Backen bei x = +-%.0f mm plus Hub %.0f und Wand -> 2*(%.0f+%.0f+%.0f)"
      % (M.X_ZANGE, P.GREIFER_HUB, M.X_ZANGE, P.GREIFER_HUB, 5))
masse("Zahnstangenhoehe", M.SCHL_H, "mm",
      "Festigkeit fordert %.1f mm (M = %.0f N x %.0f mm, S = %.1f gegen "
      "Rp0,2 = %.0f), Gestaltung 2 x Zahnhoehe = %.1f mm -> aufgerundet"
      % (M._h_fest, P.F_ZANGE_AUSLEGUNG, M.L_HEBEL, M.RACK_S, M.RACK_RP02,
         M._h_gest))
masse("Gehaeusehoehe", M.H_KOERPER, "mm",
      "groesser von Mechanik 2 x (%.0f + %.2f + %.0f + %.0f) = %.1f und "
      "Motorflansch %.0f + 2 x %.0f = %.0f -> der MOTOR bestimmt die Bauhoehe"
      % (P.R_TEILKREIS, M.H_FUSS, M.SCHL_H, M.WAND_TRAEGER, M.H_MECH_GES,
         P.MOT_FLANSCH, M.WAND_TRAEGER, M.H_MOTOR_GES))

masse("Halbachse Verkleidung z", M.SQ_C, "mm",
      "Einschlussbedingung (y/a)^%.0f + (z/c)^%.0f <= 1 fuer Traeger "
      "(%.0f|%.1f), Motor (%.0f|%.0f) und Bremse (%.0f|%.0f), plus %.0f Wand"
      % (M.SQ_N, M.SQ_N, M.Y_TRAEGER, M.H_KOERPER / 2,
         M.Y_MOT_ENDE, P.MOT_FLANSCH / 2, M.Y_BRE_ENDE, P.BREMSE_D / 2,
         M.WAND_VERK))
masse("Halbachse Verkleidung +y", M.SQ_A_P, "mm",
      "Antriebsseite: Motor mit Getriebe endet bei y = %.0f" % M.Y_MOT_ENDE)
masse("Halbachse Verkleidung -y", M.SQ_A_M, "mm",
      "Bremsseite: Haltebremse endet bei y = -%.0f" % M.Y_BRE_ENDE)
masse("Bautiefe Greifer", M.SQ_A_P + M.SQ_A_M, "mm",
      "Bremse auf dem freien Wellenende statt hinter dem Motor, Profil "
      "dadurch asymmetrisch; Exponent n = %.0f (n = 4 ergaebe 136 mm)"
      % M.SQ_N)
masse("Haltemoment Bremse", P.BREMSE_M_NOETIG, "Nm",
      "sitzt VOR dem Getriebe, haelt deshalb das volle Ritzelmoment "
      "2 x %.1f N x %.0f mm / eta; gewaehlt %.1f Nm"
      % (P.F_GREIF, P.R_TEILKREIS, P.BREMSE_M_NENN))
masse("Bauhoehe Greifer gesamt", M.Z_ZANGE + P.ZANGE_L, "mm",
      "Flansch -> Wechsler %.0f + Traeger %.1f + Flansch %.0f + Kopf %.0f "
      "+ Zange %.0f" % (M.Z_KOERPER, M.H_KOERPER, M.T_FLANSCH,
                        M.T_ZANGE_KOPF, P.ZANGE_L))

# Zangenquerschnitt ueber die Steifigkeit, nicht ueber die Festigkeit
import math
I_y = P.ZANGE_B * P.ZANGE_H ** 3 / 12
f_zange = (P.F_ZANGE_AUSLEGUNG * A_LAST ** 2 / (6 * P.ZANGE_E * I_y)
           * (3 * P.ZANGE_L - A_LAST))
f_belag = P.ZANGE_F_BELAG
masse("Zangendicke h", P.ZANGE_H, "mm",
      "kleinster Wert, der f_zange <= f_belag haelt: h_noetig = %.2f mm, "
      "aufgerundet. NICHT aus der Festigkeit - die liefert Sicherheit > 40"
      % P._h_noetig)
masse("Zangendurchbiegung", f_zange, "mm",
      "massgebend ist die Steifigkeit, nicht die Festigkeit (S = %.0f): "
      "die Zange darf sich nicht staerker verformen als der Weichbelag "
      "(%.3f mm), sonst ist die Greifkraft nicht definiert"
      % (P.ZANGE_RP02 / (P.F_ZANGE_AUSLEGUNG * A_LAST /
         (P.ZANGE_B * P.ZANGE_H ** 2 / 6) * 1.62), f_belag))

# ================================================================ Ausgabe
def main():
    print("MASSKETTE UND NACHWEISE - Greifer Gruppe %d, Bauteil %s\n"
          % (P.GRUPPE, P.BAUTEIL))
    print("%-26s %10s %-12s %s" % ("Groesse", "Wert", "Einheit", "Herleitung"))
    print("-" * 118)
    offen = 0
    for g, w, e, h, art in zeilen:
        mark = "  " if art == BELEGT else "! "
        if art != BELEGT:
            offen += 1
        print("%s%-24s %10.2f %-12s %s" % (mark, g, w, e, h))
    print("-" * 118)
    print("%d Groessen, davon %d noch Annahme (mit ! markiert)" % (len(zeilen), offen))
    if offen:
        print("\nOFFEN - diese Groessen brauchen noch eine Begruendung:")
        for g, w, e, h, art in zeilen:
            if art != BELEGT:
                print("  %-24s %s" % (g, h))


if __name__ == "__main__":
    main()
