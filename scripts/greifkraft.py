"""Greifkraftberechnung Bauteil B - Reibschluss, Parallelgreifer, seitlicher Griff.

Kritischer Lastfall: Greifrichtung horizontal (X), Beschleunigung vertikal.
Das Bauteil haengt allein in der Reibung zwischen zwei Backen.

    2 * mu * F_N  >=  S * m * (g + a)        ->   F_N = S*m*(g+a) / (2*mu)
"""
import numpy as np

m   = 4.149     # kg, Bauteil B, Stahl 7.85 g/cm3 (Werkstoff lt. Tab.1 pruefen!)
g   = 9.81      # m/s2
S   = 2.0       # Sicherheitsbeiwert (VDI 2860 / Herstellerempfehlung)
n   = 2         # Reibflaechen (Parallelgreifer, 2 Backen)

def F_N(mu, a):
    return S * m * (g + a) / (n * mu)

mus = [(0.15, "Stahl/Stahl, trocken"),
       (0.30, "Backen geriffelt / gehaertet"),
       (0.50, "Elastomer-Belag (NBR)"),
       (0.70, "Elastomer, hoher Grip")]
accs = [0, 2*g, 3*g, 5*g]

print("Bauteil B:  m = %.3f kg   G = %.1f N" % (m, m*g))
print("Sicherheitsbeiwert S = %.1f, %d Reibflaechen\n" % (S, n))
print("Erforderliche Normalkraft je Backe F_N [N]")
print("%-32s" % "Reibpaarung" + "".join("  a=%-5.0fg" % (a/g) for a in accs))
print("-" * (32 + 9*len(accs)))
for mu, name in mus:
    print("%-32s" % ("%s (mu=%.2f)" % (name, mu))
          + "".join("%9.0f" % F_N(mu, a) for a in accs))

mu_sel, a_sel = 0.50, 3*g
F = F_N(mu_sel, a_sel)
print("\nAuslegungspunkt: mu = %.2f (Elastomer-Belag), a = %.0f g" % (mu_sel, a_sel/g))
print("  -> F_N = %.0f N je Backe" % F)
print("  -> Flaechenpressung auf %d mm2 Backenflaeche: p = %.2f N/mm2"
      % (6200, F/6200))
print("\nHinweis: Schwerpunkt liegt %.1f mm ausserhalb der Backenmitte (Z),"
      % 4.5)
print("das Kippmoment M = F_G * e = %.1f Nmm ist bei der Backenlaenge zu beruecksichtigen."
      % (m*g*4.5))
