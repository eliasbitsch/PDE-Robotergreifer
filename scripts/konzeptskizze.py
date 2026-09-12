"""Abgabepunkt 2 - Konzeptskizze Greifer fuer Bauteil B (PA 6, Gruppe 2).
Parallelgreifer, seitlicher Griff auf die 70-mm-Flaechen, Weichbacken, Schnellwechsler."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

fig, ax = plt.subplots(figsize=(9, 10))
GREY, ORANGE, DARK, PART, PAD = "#b8bcc4", "#d4762a", "#3c4048", "#dfe3ea", "#2f2f2f"

def box(x, y, w, h, fc, ec=DARK, lw=1.4, z=2, **kw):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=z, **kw))

def dim(x1, y1, x2, y2, txt, off=0, vert=False):
    ax.annotate("", (x2, y2), (x1, y1),
                arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.1))
    mx, my = (x1+x2)/2, (y1+y2)/2
    ax.text(mx + (off if vert else 0), my + (0 if vert else off), txt,
            ha="center", va="center", color="#c0392b", fontsize=9,
            rotation=90 if vert else 0,
            bbox=dict(fc="white", ec="none", pad=0.8))

# --- Roboterflansch + Schnellwechselsystem ---
box(-30, 300, 60, 14, DARK, z=4)
ax.text(38, 307, "Roboterflansch ISO 9409-1", fontsize=9, va="center")
box(-34, 268, 68, 32, "#8a8f98", z=4)
ax.text(42, 284, "Schnellwechselsystem\n(Greiferwechsel lt. Angabe)", fontsize=9, va="center")

# --- Greifergrundkoerper / Antrieb ---
box(-52, 196, 104, 72, ORANGE, z=3)
ax.text(0, 232, "Parallelgreifer\n(pneumatisch, doppeltwirkend)",
        ha="center", va="center", fontsize=9.5, color="white", weight="bold")
ax.text(60, 214, "F_N = 14 N je Backe\nerforderlich", fontsize=9, va="center")

# --- Fuehrungen + Backen ---
for s in (-1, 1):
    box(s*22 - 11, 176, 22, 22, "#9aa0a8", z=3)                    # Schlitten
    box(s*46 - 11, 60, 22, 120, GREY, z=3)                          # Zangenarm
    box(s*35 - 11 if s < 0 else s*24, 78, 11, 84, PAD, z=4)         # Weichbacke NBR
ax.text(-104, 120, "Greiferzange\n(auswechselbar,\nan Bauteil angepasst)",
        fontsize=9, ha="center", va="center")
ax.text(104, 120, "Weichbacke NBR\nmu = 0,5\nschuetzt Ra 1,6",
        fontsize=9, ha="center", va="center")

# --- Bauteil B ---
box(-35, 80, 70, 80, PART, z=5)
ax.text(0, 120, "Bauteil B\nPA 6\n0,60 kg", ha="center", va="center", fontsize=9.5, weight="bold")

# --- Greifrichtung ---
for s in (-1, 1):
    ax.add_patch(FancyArrowPatch((s*60, 120), (s*40, 120), mutation_scale=16,
                                 color="#c0392b", lw=2, zorder=6))
ax.text(0, 52, "seitlicher Griff - kein Untergreifen (lt. Angabe)",
        ha="center", fontsize=9, style="italic", color="#c0392b")

# --- Bemassung ---
dim(-35, 70, 35, 70, "70 mm Greifabstand", off=-9)
dim(-57, 168, 57, 168, "Backenhub-Reserve", off=8)
ax.plot([-120, 120], [40, 40], color=DARK, lw=1.2, ls="--", zorder=1)
ax.text(0, 30, "Pufferband, Entnahmehoehe 1000 mm", ha="center", fontsize=9)

ax.set_xlim(-150, 175); ax.set_ylim(15, 330); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Konzeptskizze Greifer - Gruppe 2, Bauteil B (PA 6)\n"
             "Parallelgreifer mit Weichbacken und Schnellwechselsystem",
             fontsize=12, weight="bold", pad=14)
fig.tight_layout()
fig.savefig("/mnt/c/git/FH/PDE/konzeptskizze_B.png", dpi=170)
fig.savefig("/mnt/c/git/FH/PDE/konzeptskizze_B.pdf")
print("geschrieben: konzeptskizze_B.png / .pdf")
