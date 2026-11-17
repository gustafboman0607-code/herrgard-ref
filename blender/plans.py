import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from program import ROOMS, BLOCKS, DOORS, LEVELS, NO_WINDOWS

CAT = {
 "tech": {"Skyddsrum", "Serverrum", "Teknik / UPS / el", "Hiss & trappa", "Förråd", "Korridor", "Städ- & robotcentral", "Verkstad / laddning"},
 "food": {"AI-kök (robotkök)", "Skafferi / varulager", "Eget kök", "Frukostrum", "Matsal"},
 "wet": {"Pool & spa", "Bastu & relax", "Master spa-bad", "Bad 2", "Bad 3", "Gäst-WC", "AI-tvättstuga"},
 "sleep": {"Master sovrum", "Walk-in closet", "Sovrum 2", "Sovrum 3", "Sovrum 4", "Barnrum 1", "Barnrum 2", "Gästsvit", "Privat rum"},
 "garage": {"Garage (6 bilar)"},
}
COL = {"tech": "#d9d9d9", "food": "#f3e2c3", "wet": "#cfe3ec", "sleep": "#e6d8ea", "garage": "#cccccc", "live": "#eee6d6"}
def colour(name):
    for k, v in CAT.items():
        if name in v: return COL[k]
    return COL["live"]

def draw(level, ax):
    rooms = ROOMS[level]
    for (bx0, by0, bx1, by1) in BLOCKS.values():
        ax.add_patch(Rectangle((bx0 - 0.45, by0 - 0.45), bx1 - bx0 + 0.9, by1 - by0 + 0.9, fc="#444", ec="none"))
    for name, x0, y0, x1, y1 in rooms:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=colour(name), ec="#333", lw=1.2))
        area = (x1 - x0) * (y1 - y0)
        fs = 7.5 if area < 25 else 9
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.35, name, ha="center", va="center", fontsize=fs, weight="bold", wrap=True)
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 - 0.55, f"{x1-x0:g}×{y1-y0:g} m · {area:g} m²", ha="center", va="center", fontsize=7, color="#333")
    for x, y, k in DOORS[level]:
        if k == 'h': ax.add_patch(Rectangle((x - 0.5, y - 0.12), 1.0, 0.24, fc="white", ec="none"))
        else: ax.add_patch(Rectangle((x - 0.12, y - 0.5), 0.24, 1.0, fc="white", ec="none"))
    ax.set_xlim(-12, 38); ax.set_ylim(-5, 17); ax.set_aspect("equal"); ax.axis("off")
    ax.annotate("", xy=(0, -4.5), xytext=(10, -4.5), arrowprops=dict(arrowstyle="|-|", lw=1))
    ax.text(5, -4.9, "10 m", ha="center", fontsize=8)
    ax.text(13, -4.6, "▼ ENTRÉ / GÅRDSPLAN", ha="center", fontsize=8, color="#555")
    ax.text(13, 16.2, "▲ TRÄDGÅRD", ha="center", fontsize=8, color="#555")
    tot = sum((x1 - x0) * (y1 - y0) for _, x0, y0, x1, y1 in rooms)
    ax.set_title(f"{level} – ca {tot:.0f} m²", fontsize=14, weight="bold", loc="left")

with PdfPages("out/planritningar.pdf") as pdf:
    for level, _, _ in LEVELS:
        fig, ax = plt.subplots(figsize=(16, 7.5)); draw(level, ax)
        fig.text(0.01, 0.01, "Herrgården v1 – skiss, mått i meter. Grått = teknik/kärna, beige = mat, blått = våtrum, lila = sovrum.", fontsize=8, color="#555")
        fig.tight_layout(); fig.savefig(f"out/plan_{level.replace(' ', '_').lower()}.png", dpi=130); pdf.savefig(fig); plt.close(fig)
tot = {l: sum((x1 - x0) * (y1 - y0) for _, x0, y0, x1, y1 in ROOMS[l]) for l, _, _ in LEVELS}
print(tot, sum(tot.values()))
