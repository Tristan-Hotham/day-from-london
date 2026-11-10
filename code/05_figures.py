"""Step 5: figures for the paper (release/paper/f_*.pdf), the blog (release/blog/b_*.png) and the page (img/*.jpg)."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
RA = np.load(f"{SCR}/runs.npz")
J = pd.read_csv(f"{DATA}/journeys_model.csv")
C = pd.read_csv(f"{DATA}/coach_services.csv")
PAP = os.path.join(REL, "paper"); BLOG = os.path.join(REL, "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 10, "axes.edgecolor": "#6E604E", "axes.labelcolor": "#2B2119",
                     "xtick.color": "#6E604E", "ytick.color": "#6E604E", "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42})
PAPER = "#FBF7EC"; INK = "#2B2119"; MUT = "#6E604E"; SEA = "#E4ECEF"
ERA_COL = {"1750": "#8A6A3B", "1830": "#D08A1E", "1850": "#2F7FB8", "1910": "#3B8B5A", "today": "#B4442E"}
BANDS = [0, 2, 4, 6, 8, 10, 12, 24, 1e9]
BCOL = ["#6E1C17", "#A8382A", "#D2643A", "#E8955A", "#F2C07E", "#F8E2AE", "#D5DEE2", "#ECEAE4"]
CMAP = ListedColormap(BCOL); NORM = BoundaryNorm(BANDS, len(BCOL))
EXT = (X0, X1, Y0, Y1)
LBL = R["era_label"]


def save(fig, name, blog=None, img=None):
    fig.savefig(f"{PAP}/f_{name}.pdf", facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(f"{BLOG}/b_{blog}.png", dpi=200, facecolor=fig.get_facecolor())
        im = Image.open(f"{BLOG}/b_{blog}.png").convert("RGB")
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{blog}.png", optimize=True)
    if img:
        fig.savefig(f"{SCR}/tmp.png", dpi=150, facecolor=fig.get_facecolor())
        Image.open(f"{SCR}/tmp.png").convert("RGB").save(f"{IMG}/{img}.jpg", quality=86, optimize=True)
        os.remove(f"{SCR}/tmp.png")
    plt.close(fig)


def gbmap(ax, era, title=None, band=True, label=True):
    H = RA[f"{era}_base"]
    land = np.isfinite(H)
    ax.set_facecolor(SEA)
    Hn = np.where(np.isfinite(H), H, np.nan)
    Hn = np.where(land & ~np.isfinite(Hn), 1e6, Hn)          # unreachable land
    ax.imshow(np.ma.masked_invalid(Hn), extent=EXT, cmap=CMAP, norm=NORM, interpolation="nearest", origin="upper")
    xs = np.linspace(X0 + CELL / 2, X1 - CELL / 2, H.shape[1]); ys = np.linspace(Y1 - CELL / 2, Y0 + CELL / 2, H.shape[0])
    ax.contour(xs, ys, np.where(land, np.nan_to_num(H, nan=1e6), np.nan), levels=[BUDGET_H], colors=INK, linewidths=1.1)
    if band:
        for tag in ("fast", "slow"):
            B = RA[f"{era}_{tag}"]
            ax.contour(xs, ys, np.where(land, np.nan_to_num(B, nan=1e6), np.nan), levels=[BUDGET_H], colors=INK, linewidths=0.6, linestyles="dashed")
    ax.plot(530000, 180400, "o", ms=4, mfc="white", mec=INK, mew=1.2, zorder=5)
    ax.set_xlim(60000, 660000); ax.set_ylim(0, 1090000)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
    for s in ax.spines.values(): s.set_visible(False)
    if title:
        ax.text(0.03, 0.985, title, transform=ax.transAxes, fontsize=13, fontweight="bold", color=ERA_COL[era], va="top")
    if label:
        a = R["A"][era]
        ax.text(0.97, 0.985, f"{a['km2']:,.0f} km²\n{a['share']:.0f}% of GB", transform=ax.transAxes, fontsize=8.5, color=INK, va="top", ha="right", linespacing=1.2)


def legend_bands(fig, rect):
    ax = fig.add_axes(rect)
    labs = ["0 to 2", "2 to 4", "4 to 6", "6 to 8", "8 to 10", "10 to 12", "12 to 24", "over 24"]
    for i, (c, l) in enumerate(zip(BCOL, labs)):
        ax.add_patch(plt.Rectangle((i, 0), 0.95, 1, color=c))
        ax.text(i + 0.47, -0.25, l, ha="center", va="top", fontsize=7.5, color=INK)
    ax.text(0, 1.35, "Hours from Charing Cross (2 km cells). Solid line: 12 hours; dashed: 12 hours with speeds plus or minus the validation error",
            fontsize=7.8, color=MUT, va="bottom")
    ax.set_xlim(0, 8); ax.set_ylim(-1.2, 1.6); ax.axis("off")


# ---------- 1. the five maps
fig = plt.figure(figsize=(11, 4.6), facecolor=PAPER)
for i, e in enumerate(ERAS):
    ax = fig.add_axes((0.005 + i * 0.199, 0.17, 0.195, 0.82)); ax.set_facecolor(SEA)
    gbmap(ax, e, LBL[e])
legend_bands(fig, (0.08, 0.035, 0.84, 0.07))
save(fig, "maps", "maps", "maps")

# ---------- 2. validation scatter
fig, ax = plt.subplots(figsize=(6.4, 5.6), facecolor=PAPER); ax.set_facecolor(PAPER)
mk = {"1750": "s", "1830": "o", "1850": "^", "1910": "D", "today": "v"}
for e in ERAS:
    d = J[J.era == e].copy()
    if e == "1830":
        d2 = C[C.year == 1836]
        ax.scatter(d2.hours, d2.model_loo, s=10, color=ERA_COL[e], alpha=0.35, lw=0, label="1836 coach timetable (Bates), left out one at a time")
    y = d.model_loo if e in ("1750", "today") else d.model
    lab = {"1750": "1739 to 1764 journeys, left out one at a time", "1830": "1837 mail-coach list (out of sample)", "1850": "1838 to 1862 trains (out of sample)",
           "1910": "1896 to 1904 express trains (out of sample)", "today": "fastest trains today, left out one at a time"}[e]
    ax.scatter(d.hours, y, s=26, marker=mk[e], color=ERA_COL[e], edgecolor="white", lw=0.6, label=lab, zorder=3)
lim = (0.8, 300)
ax.plot(lim, lim, color=INK, lw=0.9); ax.plot(lim, [l * 1.2 for l in lim], color=MUT, lw=0.6, ls=":"); ax.plot(lim, [l / 1.2 for l in lim], color=MUT, lw=0.6, ls=":")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*lim); ax.set_ylim(*lim)
ticks = [1, 2, 5, 10, 20, 50, 100, 200]
ax.set_xticks(ticks); ax.set_xticklabels(ticks); ax.set_yticks(ticks); ax.set_yticklabels(ticks)
ax.set_xlabel("Documented journey time from London (hours of travel)"); ax.set_ylabel("Modelled time (hours)")
ax.legend(fontsize=7.2, frameon=False, loc="upper left")
ax.text(200, 150, "plus or minus 20%", fontsize=7, color=MUT, rotation=45, ha="center")
fig.tight_layout(); save(fig, "valid", "valid", "valid")

# ---------- 3. coach speeds 1819 and 1836
fig, axs = plt.subplots(1, 2, figsize=(9, 3.8), facecolor=PAPER, sharey=True)
for ax, yr in zip(axs, (1819, 1836)):
    ax.set_facecolor(PAPER)
    d = C[C.year == yr]
    ax.scatter(d.route_miles, d.mph, s=14, color=ERA_COL["1830"] if yr == 1836 else "#A88A4A", alpha=0.75, lw=0)
    key = "1830" if yr == 1836 else "1819"
    ax.axhline(R["mph"][key], color=INK, lw=0.9, ls="--")
    ax.text(260, R["mph"][key] + 0.25, f"fitted turnpike speed {R['mph'][key]:.1f} mph", ha="right", fontsize=8, color=INK)
    ax.set_title(f"{yr}: fastest service to each of {len(d)} places", fontsize=10, loc="left")
    ax.set_xlabel("Route length (miles)")
    ax.set_xlim(0, 300)
axs[0].set_ylabel("Scheduled speed (mph, stops included)")
fig.tight_layout(); save(fig, "coach", "coach", "coach")

# ---------- 4. areas
fig, ax = plt.subplots(figsize=(6.4, 3.6), facecolor=PAPER); ax.set_facecolor(PAPER)
x = np.arange(5)
v = [R["A"][e]["share"] for e in ERAS]; lo = [R["A"][e]["share_lo"] for e in ERAS]; hi = [R["A"][e]["share_hi"] for e in ERAS]
ax.bar(x, v, color=[ERA_COL[e] for e in ERAS], width=0.62)
ax.errorbar(x, v, yerr=[np.array(v) - np.array(lo), np.array(hi) - np.array(v)], fmt="none", ecolor=INK, capsize=4, lw=0.9)
for i, e in enumerate(ERAS):
    ax.text(i, hi[i] + 2, f"{v[i]:.0f}%", ha="center", fontsize=9, color=INK)
ax.set_xticks(x); ax.set_xticklabels([LBL[e] for e in ERAS]); ax.set_ylim(0, 112)
ax.set_ylabel("Share of Great Britain's land\nwithin 12 hours of London (%)")
fig.tight_layout(); save(fig, "area", "area", "area")

# ---------- 5. London to Edinburgh through time
fig, ax = plt.subplots(figsize=(6.6, 3.9), facecolor=PAPER); ax.set_facecolor(PAPER)
ed = pd.DataFrame(R["edinburgh_doc"])
ax.scatter(ed.year, ed.hours, color=INK, s=24, zorder=3, label="documented (days counted as 12 travelling hours)")
YR = {"1750": 1750, "1830": 1836, "1850": 1850, "1910": 1910, "today": 2026}
ax.plot([YR[e] for e in ERAS], [R["edinburgh_model"][e] for e in ERAS], color="#B4442E", lw=1.5, marker="o", ms=6, mfc="white", label="model")
ax.axhline(BUDGET_H, color=MUT, lw=0.7, ls=":"); ax.text(1752, BUDGET_H * 1.07, "one 12-hour day", fontsize=8, color=MUT)
ax.set_yscale("log"); ax.set_yticks([3, 6, 12, 24, 48, 96, 192]); ax.set_yticklabels([3, 6, 12, 24, 48, 96, 192])
ax.set_ylabel("Hours, London to Edinburgh"); ax.set_xlim(1740, 2035)
ax.legend(fontsize=8, frameon=False)
fig.tight_layout(); save(fig, "edinburgh", "edinburgh", "edinburgh")

# ---------- 6. hours to selected towns by era
towns = ["Brighton", "Oxford", "Bristol", "Birmingham", "York", "Manchester", "Exeter", "Holyhead", "Newcastle upon Tyne", "Edinburgh", "Aberdeen", "Inverness", "Wick"]
towns = [t for t in towns if t in R["towns"]]
fig, ax = plt.subplots(figsize=(6.6, 4.6), facecolor=PAPER); ax.set_facecolor(PAPER)
for i, t in enumerate(towns[::-1]):
    hs = [R["towns"][t][e] for e in ERAS]
    ax.plot([h for h in hs if h], [i] * sum(1 for h in hs if h), color="#D5CBB5", lw=1, zorder=1)
    for e, h in zip(ERAS, hs):
        if h:
            ax.scatter(h, i, color=ERA_COL[e], s=34, zorder=3, edgecolor="white", lw=0.5, label=LBL[e] if i == 0 else None)
ax.axvline(BUDGET_H, color=INK, lw=0.8, ls="--"); ax.text(BUDGET_H * 1.05, len(towns) - 0.4, "12 hours", fontsize=8)
ax.set_xscale("log"); ax.set_xticks([1, 2, 4, 8, 16, 32, 64, 128, 256]); ax.set_xticklabels([1, 2, 4, 8, 16, 32, 64, 128, 256])
ax.set_yticks(range(len(towns))); ax.set_yticklabels([t.replace(" upon Tyne", "") for t in towns[::-1]])
ax.set_xlabel("Modelled hours from Charing Cross")
ax.legend(fontsize=8, frameon=False, loc="lower right", ncol=5, bbox_to_anchor=(1, -0.3))
fig.tight_layout(); save(fig, "towns", "towns", "towns")

# ---------- 7. sensitivity
names = [("base", "Main model"), ("r04", "Other main roads at 0.4 of turnpike speed"), ("r08", "... at 0.8"), ("r10", "... at 1.0"),
         ("wait0", "No waits"), ("wait60", "Waits of 60 minutes"), ("walk4", "Walking 4 km/h"), ("walk6", "Walking 6 km/h"),
         ("branch035", "Branch lines 0.35 of main"), ("branch07", "Branch lines 0.7 of main"), ("grid4", "4 km grid"),
         ("noinferred", "1910 without inferred lines"), ("fastest_train", "Rail speed fitted to fastest trains")]
fig, ax = plt.subplots(figsize=(7.2, 4.6), facecolor=PAPER); ax.set_facecolor(PAPER)
for j, e in enumerate(ERAS):
    for i, (k, lab) in enumerate(names):
        val = R["A"][e]["km2"] if k == "base" else R["sens"].get(k, {}).get(e)
        if val is None: continue
        ax.scatter(val / R["land_km2"] * 100, len(names) - 1 - i, color=ERA_COL[e], s=28 if k == "base" else 16,
                   marker="D" if k == "base" else "o", zorder=3, label=LBL[e] if i == 0 else None)
ax.set_yticks(range(len(names))); ax.set_yticklabels([n[1] for n in names[::-1]], fontsize=8)
ax.set_xlabel("Share of GB land within 12 hours (%)"); ax.set_xlim(0, 101)
ax.legend(fontsize=8, frameon=False, ncol=5, loc="lower center", bbox_to_anchor=(0.4, -0.32))
fig.tight_layout(); save(fig, "sens", "sens", None)
print("figures done")
