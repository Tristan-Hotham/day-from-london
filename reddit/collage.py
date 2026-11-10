"""Reddit collage (r/dataisbeautiful style), light background, 2700 x 2025 px: five maps of how much of Great Britain a
traveller leaving London at dawn could reach in 12 hours (1750, 1830s, 1850, 1910, today), with the land share and the
London to Edinburgh time. Run after code/03 and code/04:  python3 reddit/collage.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
plt.rcParams.update({"font.family": "Source Serif 4", "axes.unicode_minus": False})
PAPER, INK, MUT, SEA = "#FAF6EC", "#2B2119", "#6E604E", "#E4ECEF"
HALO = [pe.withStroke(linewidth=4, foreground=SEA)]
ERA_COL = {"1750": "#8A6A3B", "1830": "#D08A1E", "1850": "#2F7FB8", "1910": "#3B8B5A", "today": "#B4442E"}
BANDS = [0, 2, 4, 6, 8, 10, 12, 24, 1e9]
BCOL = ["#6E1C17", "#A8382A", "#D2643A", "#E8955A", "#F2C07E", "#F8E2AE", "#D5DEE2", "#ECEAE4"]
CMAP = ListedColormap(BCOL); NORM = BoundaryNorm(BANDS, len(BCOL))
R = jload(f"{DATA}/results.json")
RA = np.load(f"{SCR}/runs.npz")
L = R["era_label"]

fig = plt.figure(figsize=(13.5, 10.125), dpi=200)
fig.patch.set_facecolor(PAPER)
fig.text(0.035, 0.958, "A day from London", family=DISP, fontsize=34, fontweight="bold", color=INK, va="top")
fig.text(0.035, 0.893, "How much of Great Britain could you reach in 12 hours, leaving Charing Cross at dawn? Modelled on the road\n"
         "and rail networks of each era, with speeds calibrated on coach timetables and documented journeys", fontsize=13.5, color=MUT, va="top")
w = 0.188
for i, e in enumerate(ERAS):
    ax = fig.add_axes((0.02 + i * (w + 0.005), 0.27, w, 0.45)); ax.set_facecolor(SEA)
    x0f = 0.02 + i * (w + 0.005) + 0.012
    H = RA[f"{e}_base"]; land = np.isfinite(H)
    Hn = np.where(land, np.nan_to_num(H, nan=1e6), np.nan)
    ax.imshow(np.ma.masked_invalid(Hn), extent=(X0, X1, Y0, Y1), cmap=CMAP, norm=NORM, interpolation="nearest", origin="upper")
    xs = np.linspace(X0 + CELL / 2, X1 - CELL / 2, H.shape[1]); ys = np.linspace(Y1 - CELL / 2, Y0 + CELL / 2, H.shape[0])
    ax.contour(xs, ys, np.where(land, np.nan_to_num(H, nan=1e6), np.nan), levels=[BUDGET_H], colors=INK, linewidths=1.3)
    ax.plot(530000, 180400, "o", ms=5, mfc="white", mec=INK, mew=1.4, zorder=5)
    ax.set_xlim(60000, 660000); ax.set_ylim(0, 1000000); ax.set_aspect("equal"); ax.axis("off")
    fig.text(x0f, 0.83, L[e], family=DISP, fontsize=21, fontweight="bold", color=ERA_COL[e], va="top")
    a = R["A"][e]
    ed = R["edinburgh_model"][e]
    fig.text(x0f, 0.79, ("at least " if e in ("1850", "1910") else "") + f"{a['share']:.0f}% of Great Britain\nwithin 12 hours" + (" (rough sketch)" if e == "1750" else ""), fontsize=10.5, color=INK, va="top")
    fig.text(x0f, 0.747, f"Edinburgh: {ed:.0f} h" if ed >= 10 else f"Edinburgh: {ed:.1f} h", fontsize=10.5, color=MUT, va="top")
    mode = {"1750": "stage coach on the\nturnpikes of 1750", "1830": "fast coaches on the\nturnpikes of 1830", "1850": "trains on the\nlines of 1851",
            "1910": "trains on the\nnetwork of 1910", "today": "car or train"}[e]
    fig.text(x0f, 0.258, mode.replace("\n", " "), fontsize=9.5, color=MUT, va="top")
# legend
lx = fig.add_axes((0.08, 0.135, 0.84, 0.045)); lx.axis("off"); lx.set_xlim(0, 8); lx.set_ylim(-1.3, 1.2)
labs = ["0 to 2 h", "2 to 4", "4 to 6", "6 to 8", "8 to 10", "10 to 12", "12 to 24", "over 24"]
for k, (c, l) in enumerate(zip(BCOL, labs)):
    lx.add_patch(plt.Rectangle((k, 0), 0.96, 1, color=c, ec="#B8AE98", lw=0.5))
    lx.text(k + 0.48, -0.25, l, ha="center", va="top", fontsize=11, color=INK)
fig.text(0.08, 0.183, "Hours of travel from Charing Cross (white dot). Black line: the edge of a 12-hour day.", fontsize=11.5, color=INK)
fig.text(0.035, 0.065, f"Model error against documented journeys (median, out of sample): 1750 {R['fits']['1750']['loo']['mdape']:.0f}%, 1830s {R['fits']['1830']['loo']['mdape']:.0f}%, "
         f"1850 {R['valid']['1850_all']['mdape']:.0f}%, 1910 {R['valid']['1910_all']['mdape']:.0f}%, today (trains) {R['fits']['today_rail']['loo']['mdape']:.0f}%. No timetables: fixed 30-minute waits."
         "\n1750 fails the 25% limit set in advance: read it as a rough sketch. 1850 and 1910 use average trains, slower than the 4 and 6 documented expresses: their areas are lower bounds.", fontsize=10, color=MUT, va="bottom")
fig.text(0.035, 0.025, "Data: turnpike roads and London coaches 1819 and 1836 (Rosevear, Bogart, Shaw-Taylor, Satchell, openICPSR); 1851 rail lines (Satchell et al., CC BY 4.0);\n"
         "OpenStreetMap via OpenFreeMap (ODbL); train speeds from Leunig (2006); documented journeys from Harper (1899 to 1922) and others. Dr Tristan Hotham  ·  maps.tristanhotham.com/day-from-london",
         fontsize=9, color=MUT, va="bottom")
out = os.path.join(HERE, "day_from_london_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER)
print(out)
