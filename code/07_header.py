"""Step 7: header.png, the 1200 x 630 social card: title on cream paper beside the 1750 and today maps."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
R = jload(f"{DATA}/results.json"); RA = np.load(f"{SCR}/runs.npz")
PAPER, INK, MUT, SEA, RED = "#F6EED8", "#2B2119", "#6E604E", "#E4ECEF", "#B4442E"
BANDS = [0, 2, 4, 6, 8, 10, 12, 24, 1e9]
BCOL = ["#6E1C17", "#A8382A", "#D2643A", "#E8955A", "#F2C07E", "#F8E2AE", "#D5DEE2", "#ECEAE4"]
CMAP = ListedColormap(BCOL); NORM = BoundaryNorm(BANDS, len(BCOL))
fig = plt.figure(figsize=(12, 6.3), dpi=100); fig.patch.set_facecolor(PAPER)
fig.text(0.045, 0.86, "DATA STUDY", family="IBM Plex Mono", fontsize=13, color="white", va="top", bbox=dict(fc=RED, ec=RED, pad=5))
fig.text(0.045, 0.74, "A day\nfrom London", family=DISP, fontsize=50, fontweight="bold", color=INK, va="top", linespacing=0.95)
fig.text(0.045, 0.40, f"How far could you get in 12 hours?\n1750: {R['A']['1750']['share']:.0f}% of Great Britain.\nToday: {R['A']['today']['share']:.0f}%.",
         fontsize=19, color=INK, va="top", linespacing=1.3, family="Source Serif 4")
fig.text(0.045, 0.07, "Dr Tristan Hotham  ·  maps.tristanhotham.com", family="IBM Plex Mono", fontsize=11, color=MUT)
for k, e in enumerate(("1750", "today")):
    ax = fig.add_axes((0.47 + k * 0.265, 0.03, 0.26, 0.94)); ax.set_facecolor(SEA)
    H = RA[f"{e}_base"]; land = np.isfinite(H)
    Hn = np.where(land, np.nan_to_num(H, nan=1e6), np.nan)
    ax.imshow(np.ma.masked_invalid(Hn), extent=(X0, X1, Y0, Y1), cmap=CMAP, norm=NORM, interpolation="nearest", origin="upper")
    xs = np.linspace(X0 + CELL / 2, X1 - CELL / 2, H.shape[1]); ys = np.linspace(Y1 - CELL / 2, Y0 + CELL / 2, H.shape[0])
    ax.contour(xs, ys, np.where(land, np.nan_to_num(H, nan=1e6), np.nan), levels=[BUDGET_H], colors=INK, linewidths=1.2)
    ax.plot(530000, 180400, "o", ms=5, mfc="white", mec=INK, mew=1.3)
    ax.set_xlim(60000, 660000); ax.set_ylim(0, 1000000); ax.set_aspect("equal"); ax.axis("off")
    ax.text(0.97, 0.015, R["era_label"][e], transform=ax.transAxes, ha="right", family=DISP, fontsize=24, fontweight="bold", color=RED if e == "today" else "#8A6A3B", va="bottom")
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
from PIL import Image
im = Image.open(os.path.join(ROOT, "header.png")); assert im.size == (1200, 630), im.size
print("header.png", im.size)
