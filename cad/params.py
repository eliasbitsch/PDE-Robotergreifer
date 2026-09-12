"""Zentrale Parameter - Gruppe 10, Bauteil B (PA 6).

EINZIGE Quelle der Wahrheit. Alle Skripte (Auslegung, CAD, FEM, Simulation)
importieren von hier, damit eine Iteration nur an einer Stelle passiert.

Quellen:
  Angabe WS26.pdf, Abb.1  -> Anlagengeometrie, Taktzeit
  Angabe WS26.pdf, Tab.1  -> Werkstoff PA 6, Ra 1,6
  scripts/analyze_B.py    -> Bauteilgeometrie aus Bauteil_B.STEP
"""
from math import hypot, pi

# ---------------------------------------------------------------- Organisation
GRUPPE = 10
BAUTEIL = "B"
AUTOREN = ["Bitsch Elias", "Ovdiienko Viktoriia"]

# ---------------------------------------------------------------- Bauteil B
# aus analyze_B.py (Bauteil_B.STEP)
B_BBOX = (95.0, 100.0, 80.0)        # mm
B_VOL = 528.5e-6                    # m^3  (528,5 cm^3)
B_COG = (-3.0, -1.9, -4.5)          # mm, Schwerpunkt rel. STEP-Ursprung

# Tab.1: PA 6, Ra 1,6  -> NICHT Stahl. Aeltere Rechnung mit 4,149 kg war falsch.
B_RHO = 1140.0                      # kg/m^3   PA 6 (Datenblatt 1,12...1,15)
B_MASSE = B_VOL * B_RHO             # kg  -> 0,602
B_RA = 1.6                          # um, geforderte Oberflaeche -> Weichbacken

# Greifflaechen: Paar 1/2 aus analyze_B.py, Normale +-X
GREIF_RICHTUNG = "X"
GREIF_ABSTAND = 70.0                # mm, Backenabstand am Bauteil
GREIF_FLAECHE = 6200.0              # mm^2, kleinere der beiden Flaechen
# Schwerpunktversatz quer zur Greifrichtung -> Kippmoment auf die Zange
GREIF_EXZENTRIZITAET = 4.5          # mm (COG_z)

# ---------------------------------------------------------------- Anlage (Abb.1)
H_ENTNAHME = 1.000                  # m  Pufferband
H_ABLAGE = 1.300                    # m  Werkstuecktraeger
DIST_HORIZONTAL = 1.800             # m  Entnahme <-> Ablage
KETTEN_ABSTAND = 0.600              # m  zwei parallele Foerderketten
EINHAUSUNG_HOEHE = 2.100            # m
TAKTZEIT = 5.0                      # s je Bauteil

# ---------------------------------------------------------------- Physik
G = 9.81                            # m/s^2

# ---------------------------------------------------------------- Zeitbudget
# Aufteilung der Taktzeit; Handhabungszeiten nach Herstellerangaben Parallelgreifer
T_GREIFEN = 0.30                    # s  Zange schliessen
T_LOESEN = 0.20                     # s  Zange oeffnen
T_FEIN = 0.50                       # s  Feinpositionierung Entnahme + Ablage
T_VERFAHREN = TAKTZEIT - (T_GREIFEN + T_LOESEN + T_FEIN)   # s  hin + zurueck
T_EINWEG = T_VERFAHREN / 2.0

# Trapezprofil mit Beschleunigungsphase t_a = t/3 (Faustwert Industrieroboter)
WEG_RAEUMLICH = hypot(DIST_HORIZONTAL, H_ABLAGE - H_ENTNAHME)   # m
_TA = T_EINWEG / 3.0
A_BAHN = WEG_RAEUMLICH / (_TA * (T_EINWEG - _TA))   # m/s^2
V_BAHN = A_BAHN * _TA                               # m/s

# ---------------------------------------------------------------- Greifkraft
S_SICHERHEIT = 2.0                  # -  Sicherheitsbeiwert (VDI 2860)
N_BACKEN = 2                        # -  Reibflaechen beim Parallelgreifer
MU_BELAG = 0.50                     # -  PA 6 gegen NBR-Weichbelag

# F_N = S * m * (g + a) / (n * mu)
F_GREIF = S_SICHERHEIT * B_MASSE * (G + A_BAHN) / (N_BACKEN * MU_BELAG)   # N je Backe

# ---------------------------------------------------------------- Greifer
M_GREIFER = 2.5                     # kg  Annahme Grundkoerper + Zangen + Wechsler
FLANSCH_NORM = "ISO 9409-1-50-4-M6"

# EIGENKONSTRUKTION statt Zukaufgreifer.
# Wirkprinzip aus dem Variantenvergleich in mechanismus.py:
# Zahnstange-Ritzel, elektrisch ueber Servomotor mit Planetengetriebe.
#
# Warum Zahnstange und nicht Spindel:
#   Fuer 12 mm Backenhub braucht die Zahnstange nur 69 Grad Ritzeldrehung,
#   eine Trapezspindel Tr10x2 dagegen 6 volle Umdrehungen. Bei 0,30 s
#   Schliesszeit sind das 1200 1/min - ein einfacher Schrittmotor mit
#   1000 1/min verfehlt damit die Taktvorgabe. Die Zahnstange schafft es
#   mit Faktor 20 Reserve.
#
# Warum Servo und nicht Pneumatik:
#   Die Bewertung in mechanismus.py liegt mit 0,66 zu 0,64 praktisch gleich
#   auf, die Entscheidung faellt also nach Zusatzkriterien: geringere
#   Geraeuschentwicklung, regelbare Greifkraft, keine Druckluftinfrastruktur.
#   Energiekosten sind KEIN Argument - nachgerechnet trennen Druckluft und
#   Strom bei dieser Zylindergroesse weniger als 2 EUR im Jahr.
#
# Preis der Entscheidung:
#   Zahnstange-Ritzel ist NICHT selbsthemmend. Bei Stromausfall wuerde das
#   Bauteil fallen -> Haltebremse am Motor ist zwingend, nicht optional.
#   Ausserdem braucht der Schnellwechsler elektrische Kontakte statt einer
#   Luftkupplung.
GREIFER_TYP = "Eigenkonstruktion, Zahnstange-Ritzel, Servomotor"
# Backenhub GEOMETRISCH hergeleitet, nicht geschaetzt:
# Bauteil B ist B_BBOX[0] = 95 mm breit, gegriffen wird auf GREIF_ABSTAND = 70 mm.
# Die Backen muessen also ueber die Vorspruenge hinaus oeffnen:
#     (95 - 70) / 2 = 12,5 mm  plus Freigang
# Mit den urspruenglichen 12 mm waere der Greifer beim Einfahren angestossen.
FREIGANG = 1.5                      # mm seitliche Luft je Seite
GREIFER_HUB = (B_BBOX[0] - GREIF_ABSTAND) / 2.0 + FREIGANG

# Verzahnung. z = 20 liegt ueber der Grenzzaehnezahl 17, damit ist keine
# Profilverschiebung noetig.
MODUL = 1.0                         # mm
Z_RITZEL = 20                       # -
B_ZAHN = 8.0                        # mm Zahnbreite
R_TEILKREIS = MODUL * Z_RITZEL / 2.0                 # mm
ETA_GETRIEBE = 0.92                 # - Wirkungsgrad Zahnstange-Ritzel

# Antrieb
# Motorauswahl belegt in nachweise.py: Bedarf 0,069 Nm. Der NEMA 17 Pancake
# ist die flachste reale Baugroesse, die die geforderte Reserve von 2,0 haelt
# (NEMA 14 schafft nur 1,4x). Gleicher Flansch wie der Standard-NEMA-17, aber
# nur 20 statt 34-48 mm Baulaenge - das entscheidet ueber die Gehaeuseform.
MOTOR_TYP = "Schrittmotor NEMA 17 Pancake mit Planetengetriebe und Haltebremse"
MOTOR_M_NENN = 0.16                 # Nm Haltemoment (Pancake-Bauform)
GETRIEBE_I = 5.0                    # - Planetengetriebe
GETRIEBE_ETA = 0.90                 # -

# Baulaengen der Antriebseinheit. Die Gesamtlaenge bestimmt die Gestaltung des
# Gehaeuses: je laenger der Antrieb, desto weiter kragt er aus.
# Gewaehlt ist eine Ausfuehrung mit angebautem Planetengetriebe und
# elektromagnetischer Federkraftbremse - kompakter als drei Einzelbaugruppen.
MOT_L_GETRIEBE = 30.0               # mm
MOT_L_MOTOR = 20.0                  # mm  NEMA 17 Pancake
MOT_L_GESAMT = MOT_L_GETRIEBE + MOT_L_MOTOR                  # 50 mm, Seite +Y
MOT_FLANSCH = 42.0                  # mm  NEMA 17

# BREMSE AUF DEM FREIEN WELLENENDE, nicht hinter dem Motor.
# Sass die Bremse hinter dem Motor, lag der gesamte Antrieb auf einer Seite
# der Ritzelachse: 30 + 20 + 21 = 71 mm. Die Gegenseite blieb leer und wurde
# von der symmetrischen Aussenform trotzdem mitgebaut - 176 mm Bautiefe fuer
# 71 mm Antrieb. Auf dem freien Wellenende nutzt die Bremse den leeren Raum.
#
# Preis: sie bremst jetzt VOR dem Getriebe und muss deshalb das volle
# Ritzelmoment halten statt nur ein Fuenftel davon.

# Die Zange muss die volle Kraft aushalten, die der Antrieb aufbringen kann.
# Sie ergibt sich aus dem Motormoment, nicht aus der Haltekraft.
M_ABTRIEB = MOTOR_M_NENN * GETRIEBE_I * GETRIEBE_ETA          # Nm am Ritzel

# Haltemoment der Bremse: sie muss die Greifkraft beider Backen halten.
BREMSE_M_NOETIG = 2 * F_GREIF * R_TEILKREIS / 1000.0 / ETA_GETRIEBE   # Nm
BREMSE_M_NENN = 0.4                 # Nm, naechste Baugroesse Federkraftbremse
BREMSE_L = 30.0                     # mm Baulaenge fuer dieses Moment
BREMSE_D = 40.0                     # mm Aussendurchmesser
GREIFER_F_MAX = M_ABTRIEB * 1000.0 / R_TEILKREIS / 2.0 * ETA_GETRIEBE   # N je Backe

# MASSGEBLICHER LASTFALL FUER DIE ZANGE
F_ZANGE_AUSLEGUNG = GREIFER_F_MAX

# ---------------------------------------------------------------- Roboter
ROBOTER = "ABB IRB 1600-6/1.45"
R_ROBOTER = 1450.0                  # mm Reichweite
M_TRAGLAST = 6.0                    # kg Nennlast

# ---------------------------------------------------------------- Greiferzange
# Geometrie des FEM-/Festigkeitsnachweis-Bauteils. Kragarm, am Schlitten
# eingespannt, Greifkraft F_GREIF am freien Ende quer zur Armachse.
ZANGE_WERKSTOFF = "EN AW-7075 T6"
ZANGE_E = 71000.0                   # MPa  E-Modul
ZANGE_NU = 0.33                     # -    Querkontraktion
ZANGE_RHO = 2800.0                  # kg/m^3
ZANGE_RP02 = 460.0                  # MPa  Streckgrenze
ZANGE_S_ZUL = 2.0                   # -    Sicherheit gegen Fliessen
ZANGE_SIGMA_ZUL = ZANGE_RP02 / ZANGE_S_ZUL   # MPa

ZANGE_B = 25.0                      # mm  Breite (quer zur Lastrichtung)
ZANGE_FILLET = 3.0                  # mm  Ausrundung an der Einspannung

# Lasteinleitung: Weichbacke sitzt in einer Tasche am freien Ende
BACKE_LAENGE = 60.0                 # mm  Laenge der Backentasche (z-Richtung)
BACKE_BREITE = ZANGE_B - 10.0       # mm  Breite der Backentasche (y-Richtung)
BACKE_TIEFE = 1.5                   # mm  Taschentiefe

# ZANGENLAENGE GEOMETRISCH HERGELEITET, nicht gesetzt.
# Die Greifflaeche von Bauteil B laeuft ueber die volle Bauteilhoehe
# (B_BBOX[2] = 80 mm, aus analyze_B.py: Flaechen bei x = +-35 mm reichen von
# z = -40 bis +40). Die Weichbacke wird mittig darauf gesetzt, also bleibt
# oben und unten je (80 - 60)/2 = 10 mm Rand. Darueber braucht der
# Zangenkopf Luft zur Bauteiloberseite:
#
#     L = Luft + Randmass oben + Backenlaenge
#
# Mit 120 mm war die Zange 40 mm laenger als noetig. Das kostete nicht nur
# Bauhoehe: die Durchbiegung waechst mit dem Quadrat des Kraftarms, die
# Biegespannung linear damit.
LUFT_BAUTEIL = 10.0                 # mm Abstand Zangenkopf -> Bauteiloberseite
ZANGE_L = LUFT_BAUTEIL + (B_BBOX[2] - BACKE_LAENGE) / 2.0 + BACKE_LAENGE
# Kraftangriff = Mitte der Weichbacke, gemessen ab der Einspannung
ZANGE_A_LAST = ZANGE_L - BACKE_LAENGE / 2.0

# ZANGENDICKE AUS DER STEIFIGKEIT, NICHT AUS DER FESTIGKEIT.
#
# Der Festigkeitsnachweis ist hier kein Auslegungskriterium: er liefert
# Sicherheiten jenseits von 40, die Zange wuerde auch mit 3 mm halten.
# Massgebend ist etwas anderes - die Zange darf sich unter der Greifkraft
# nicht staerker verformen als der Weichbelag, auf dem sie aufliegt.
# Andernfalls bestimmt die Zangenfederung die Greifkraft mit, und die
# geregelte Kraft des Servoantriebs waere wertlos.
#
#   Weichbelag (NBR 70 Shore A, E ~ 5 MPa), Druck auf die Backenflaeche:
#       f_belag = F / A_backe * t_belag / E
#   Zange als Kragarm mit Einzelkraft im Abstand a:
#       f_zange = F a^2 (3L - a) / (6 E I),    I = b h^3 / 12
#
# Gleichgesetzt und nach h aufgeloest, auf volle mm aufgerundet.
NBR_E = 5.0                         # MPa  E-Modul NBR 70 Shore A
NBR_T = 8.0                         # mm   Dicke des Weichbelags
_f_belag = F_ZANGE_AUSLEGUNG / (BACKE_LAENGE * BACKE_BREITE) * NBR_T / NBR_E
_h_noetig = (F_ZANGE_AUSLEGUNG * ZANGE_A_LAST ** 2 * (3 * ZANGE_L - ZANGE_A_LAST)
             / (6 * ZANGE_E * _f_belag) * 12 / ZANGE_B) ** (1.0 / 3.0)
from math import ceil as _ceil
ZANGE_H = float(_ceil(_h_noetig))   # mm  Dicke (in Lastrichtung = Biegerichtung)
ZANGE_F_BELAG = _f_belag            # mm  zulaessige Durchbiegung

if __name__ == "__main__":
    print("GRUPPE %d - BAUTEIL %s (PA 6)" % (GRUPPE, BAUTEIL))
    print("  Masse              %.3f kg   (G = %.2f N)" % (B_MASSE, B_MASSE * G))
    print("  Greifabstand       %.1f mm auf %.0f mm2" % (GREIF_ABSTAND, GREIF_FLAECHE))
    print()
    print("BEWEGUNG")
    print("  Verfahrzeit je Weg %.2f s  (von %.1f s Taktzeit)" % (T_EINWEG, TAKTZEIT))
    print("  Weg                %.3f m" % WEG_RAEUMLICH)
    print("  Beschleunigung     %.2f m/s2  = %.2f g" % (A_BAHN, A_BAHN / G))
    print("  Spitzengeschw.     %.2f m/s" % V_BAHN)
    print()
    print("GREIFKRAFT")
    print("  mu = %.2f, S = %.1f, %d Backen" % (MU_BELAG, S_SICHERHEIT, N_BACKEN))
    print("  F_N                %.1f N je Backe" % F_GREIF)
    print("  Flaechenpressung   %.3f N/mm2 auf %.0f mm2" % (F_GREIF / GREIF_FLAECHE, GREIF_FLAECHE))
    print()
    print("GREIFERZANGE (%s)" % ZANGE_WERKSTOFF)
    print("  Kragarm %.0f x %.0f x %.0f mm, sigma_zul = %.0f MPa"
          % (ZANGE_L, ZANGE_B, ZANGE_H, ZANGE_SIGMA_ZUL))
