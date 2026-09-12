"""Gruppe 2 - Bauteil B (PA 6): Taktzeit-Bilanz, Beschleunigung, Greifkraft, Roboterwahl.

Anlagendaten aus Abb.1:  Entnahme h=1000, Ablage h=1300, Abstand 1800 mm,
Kettenabstand 600 mm, Taktzeit 5 s je Bauteil.
"""
import numpy as np

# ---------- Bauteil ----------
V    = 528.5e-6           # m3   (aus STEP)
RHO  = 1140.0             # kg/m3  PA 6
m_B  = V * RHO
g    = 9.81
print("BAUTEIL B  (PA 6, Ra 1,6)")
print("  V = %.1f cm3   rho = %.0f kg/m3   m = %.3f kg   G = %.2f N" % (V*1e6, RHO, m_B, m_B*g))

# ---------- Taktzeit ----------
s_h, s_v = 1.800, 0.300   # m
T        = 5.0            # s
t_greif, t_loese = 0.30, 0.20     # s  Zangen oeffnen/schliessen
t_fein   = 2 * 0.25               # s  Feinpositionierung Entnahme + Ablage
t_move   = T - (t_greif + t_loese + t_fein)   # verbleibt fuer Hin- + Rueckweg
t_one    = t_move / 2

print("\nTAKTZEIT-BILANZ (T = %.1f s)" % T)
for lbl, v in [("Greifen (schliessen)", t_greif), ("Loesen (oeffnen)", t_loese),
               ("Feinpositionierung", t_fein), ("Verfahren hin+zurueck", t_move)]:
    print("  %-26s %5.2f s" % (lbl, v))
print("  -> je Verfahrweg: %.2f s" % t_one)

# Trapezprofil, Beschleunigungsphase = 1/3 der Zeit (Faustwert Industrieroboter)
s_ges = np.hypot(s_h, s_v)
a_req = s_ges / (t_one**2 * (1/3) * (2/3) + 0.5*(1/3)**2 * t_one**2 * 2/1)  # s = a*ta*(t-ta)
ta    = t_one / 3.0
a_req = s_ges / (ta * (t_one - ta))
v_max = a_req * ta
print("\nBEWEGUNGSPROFIL (Trapez, t_a = t/3)")
print("  Weg (raeumlich)      %.3f m" % s_ges)
print("  Beschleunigung       %.2f m/s2  = %.2f g" % (a_req, a_req/g))
print("  Spitzengeschwindigkeit %.2f m/s" % v_max)

# ---------- Greifkraft ----------
S, n = 2.0, 2
def FN(mu, a): return S * m_B * (g + a) / (n * mu)

print("\nGREIFKRAFT  (Reibschluss, S = %.1f, %d Backen)" % (S, n))
paare = [(0.20, "PA6 / Stahl trocken"), (0.35, "PA6 / Stahl geriffelt"),
         (0.50, "PA6 / NBR-Belag"), (0.65, "PA6 / PUR-Weichbelag")]
print("  %-26s %10s" % ("Reibpaarung", "F_N [N]"))
for mu, nm in paare:
    print("  %-26s %10.0f" % ("%s (mu=%.2f)" % (nm, mu), FN(mu, a_req)))

mu_s = 0.50
F    = FN(mu_s, a_req)
A_backe = 2000.0   # mm2 konservativ genutzte Backenflaeche
print("\n  Auslegung: mu = %.2f (NBR-Belag) -> F_N = %.0f N je Backe" % (mu_s, F))
print("  Flaechenpressung p = %.3f N/mm2 auf %.0f mm2" % (F/A_backe, A_backe))
print("  (PA 6 zul. Flaechenpressung ca. 30 N/mm2 - unkritisch, Ra 1,6 bleibt erhalten)")

# ---------- Roboter ----------
m_greifer = 2.5
print("\nROBOTERAUSWAHL")
print("  Reichweite: 1800/2 = 900 mm + 300 mm seitlich + Greiferlaenge")
print("               -> R >= %.0f mm" % (np.hypot(900+150, 300) + 150))
print("  Traglast:   Bauteil %.2f kg + Greifer %.1f kg = %.2f kg  -> Nennlast >= %.0f kg"
      % (m_B, m_greifer, m_B + m_greifer, np.ceil((m_B+m_greifer)*1.5)))
print("  Dynamik:    %.2f g Bahnbeschleunigung noetig - fuer 6-Achser dieser Klasse ueblich"
      % (a_req/g))
