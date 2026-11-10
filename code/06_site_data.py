"""Step 6: map assets for the page.
  img/hours_<era>.png      the hour bands as a transparent image in Web Mercator (MapLibre image source)
  img/roads_<era>.png      1750 and 1830s: the turnpike roads (dark) and other main roads (light) rasterised at about 400 m,
                           a derived picture of the Rosevear et al. map (the shapefile itself is not redistributed)
  data/lookup.png          hours for every era on a lon/lat grid, one colour channel per era pair, for tap popups
  data/site.json           towns with modelled hours, documented journeys with model and error, 12-hour lines (base and
                           band) as GeoJSON, the 1851 rail lines and the inferred 1910 lines (simplified), bounds
"""
import pickle
import numpy as np, pandas as pd
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from common import *

R = jload(f"{DATA}/results.json")
RA = np.load(f"{SCR}/runs.npz")
J = pd.read_csv(f"{DATA}/journeys_model.csv")
T = pd.read_csv(f"{DATA}/towns_hours.csv")
fwd, inv = bng()
LON0, LON1, LAT0, LAT1 = -8.25, 1.95, 49.85, 60.9
BCOL = ["#6E1C17", "#A8382A", "#D2643A", "#E8955A", "#F2C07E", "#F8E2AE", "#C9D6DC", "#E6E2DA"]
BANDS = [0, 2, 4, 6, 8, 10, 12, 24, 1e9]
ny, nx = RA["1750_base"].shape


def merc_y(lat):
    return np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def merc_grid(W):
    y0, y1 = merc_y(LAT0), merc_y(LAT1)
    H = int(round(W * (y1 - y0) / np.radians(LON1 - LON0)))
    lon = np.linspace(LON0, LON1, W, endpoint=False) + (LON1 - LON0) / W / 2
    my = y1 - (np.arange(H) + 0.5) * (y1 - y0) / H
    lat = np.degrees(2 * np.arctan(np.exp(my)) - np.pi / 2)
    LO, LA = np.meshgrid(lon, lat)
    E, N = fwd.transform(LO, LA)
    i = ((Y1 - N) // CELL).astype(int); j = ((E - X0) // CELL).astype(int)
    ok = (i >= 0) & (i < ny) & (j >= 0) & (j < nx)
    return H, i, j, ok, E, N


def hex2rgb(h):
    return [int(h[k:k + 2], 16) for k in (1, 3, 5)]


W = 900
Hpx, I, Jx, OK, EE, NN = merc_grid(W)
land = np.isfinite(RA["1750_base"])
for e in ERAS:
    Hh = RA[f"{e}_base"]
    img = np.zeros((Hpx, W, 4), np.uint8)
    v = np.full((Hpx, W), np.nan)
    v[OK] = np.where(land[I[OK], Jx[OK]], np.nan_to_num(Hh[I[OK], Jx[OK]], nan=1e6), np.nan)
    for k in range(len(BCOL)):
        m = (v >= BANDS[k]) & (v < BANDS[k + 1])
        img[m, :3] = hex2rgb(BCOL[k]); img[m, 3] = 205 if k < 6 else 150
    Image.fromarray(img, "RGBA").save(f"{IMG}/hours_{e}.png", optimize=True)

# roads of 1750 and 1830 (derived raster)
N = pickle.load(gzip.open(os.path.join(SCR, "net.pkl"), "rb"))
for e, f, yr in (("1750", "tp1750", 1750), ("1830", "tp1830", 1830)):
    fig = plt.figure(figsize=(W / 100, Hpx / 100), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1)); ax.axis("off")
    ax.set_xlim(np.radians(LON0), np.radians(LON1)); ax.set_ylim(merc_y(LAT0), merc_y(LAT1))
    for a, at in N["turnpike"]:
        c = at[f]
        if c in (7, 8, 9):
            continue
        lon, lat = inv.transform(a[::3, 0] if len(a) > 6 else a[:, 0], a[::3, 1] if len(a) > 6 else a[:, 1])
        tp = c == yr
        ax.plot(np.radians(lon), merc_y(np.asarray(lat)), color="#2B2119" if tp else "#8C7F6A", lw=0.9 if tp else 0.45, alpha=0.95 if tp else 0.7, solid_capstyle="round")
    fig.savefig(f"{SCR}/roads.png", dpi=100, transparent=True); plt.close(fig)
    im = Image.open(f"{SCR}/roads.png").convert("RGBA")
    im.save(f"{IMG}/roads_{e}.png", optimize=True)
    os.remove(f"{SCR}/roads.png")

# lookup grid (lon/lat), hours * 2 capped at 250; 255 = sea or unreachable
LW, LH = 408, 663
lon = np.linspace(LON0, LON1, LW, endpoint=False) + (LON1 - LON0) / LW / 2
lat = np.linspace(LAT1, LAT0, LH, endpoint=False) - (LAT1 - LAT0) / LH / 2
LO, LA = np.meshgrid(lon, lat)
E, Nn = fwd.transform(LO, LA)
i = ((Y1 - Nn) // CELL).astype(int); j = ((E - X0) // CELL).astype(int)
ok = (i >= 0) & (i < ny) & (j >= 0) & (j < nx)
stack = []
for e in ERAS:
    Hh = RA[f"{e}_base"]
    v = np.full((LH, LW), 255, np.uint8)
    h = np.full((LH, LW), np.nan); h[ok] = Hh[i[ok], j[ok]]
    m = np.isfinite(h)
    v[m] = np.clip(np.round(h[m] * 2), 0, 250).astype(np.uint8)
    v[ok & land[np.clip(i, 0, ny - 1), np.clip(j, 0, nx - 1)] & ~m] = 252   # land beyond the model's horizon
    stack.append(v)
# five eras in a 2 x 3 tiled greyscale image (era k at tile k)
tile = np.full((LH * 2, LW * 3), 255, np.uint8)
for k, v in enumerate(stack):
    r, c = divmod(k, 3); tile[r * LH:(r + 1) * LH, c * LW:(c + 1) * LW] = v
Image.fromarray(tile, "L").save(f"{DATA}/lookup.png", optimize=True)

# 12-hour lines
xs = np.linspace(X0 + CELL / 2, X1 - CELL / 2, nx); ys = np.linspace(Y1 - CELL / 2, Y0 + CELL / 2, ny)


def contour_geo(H):
    Z = np.where(land, np.nan_to_num(H, nan=1e6), np.nan)
    cs = plt.contour(xs, ys, Z, levels=[BUDGET_H])
    lines = []
    for seg in cs.allsegs[0]:
        if len(seg) < 4:
            continue
        ls = LineString(seg).simplify(800)
        a = np.asarray(ls.coords)
        lo, la = inv.transform(a[:, 0], a[:, 1])
        lines.append([[round(float(x), 4), round(float(y), 4)] for x, y in zip(lo, la)])
    plt.close("all")
    return {"type": "MultiLineString", "coordinates": lines}


iso = {e: {t: contour_geo(RA[f"{e}_{t}"]) for t in ("base", "fast", "slow")} for e in ERAS}


def lines_json(lines, tol):
    out = []
    for a in lines:
        if len(a) < 2:
            continue
        ls = LineString(a).simplify(tol)
        b = np.asarray(ls.coords)
        lo, la = inv.transform(b[:, 0], b[:, 1])
        out.append([[round(float(x), 4), round(float(y), 4)] for x, y in zip(lo, la)])
    return out


rail51 = lines_json([a for a, _ in N["rail1851"]], 150)
inferred = lines_json([a for a, _ in N["rail_inf"]], 50)
towns = []
for _, r in T.iterrows():
    towns.append(dict(n=r.town, la=round(r.lat, 4), lo=round(r.lon, 4), km=round(r.crow_km), h=[None if not np.isfinite(r[e]) else round(float(r[e]), 2) for e in ERAS]))
docs = []
for _, r in J.iterrows():
    docs.append(dict(e=r.era, n=r.town, y=int(r.year), d=round(float(r.hours), 2), v=float(r.value), u=r.unit, m=r["mode"], s=r.source,
                     h=None if not np.isfinite(r.model) else round(float(r.model), 2),
                     l=None if pd.isna(r.get("model_loo")) else round(float(r.model_loo), 2), set=r.set))
S = dict(eras=ERAS, labels=[R["era_label"][e] for e in ERAS], bounds=[LON0, LAT0, LON1, LAT1], lookup=dict(w=LW, h=LH),
         towns=towns, docs=docs, iso=iso, rail1851=rail51, inferred=inferred,
         area=[dict(km2=round(R["A"][e]["km2"]), share=round(R["A"][e]["share"], 1)) for e in ERAS],
         band=[round(R["speeds"][e]["band_pc"], 1) for e in ERAS])
jsave(S, f"{DATA}/site.json")
print("site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB;", "overlays",
      sum(os.path.getsize(f"{IMG}/hours_{e}.png") for e in ERAS) // 1024, "KB; lookup", os.path.getsize(f"{DATA}/lookup.png") // 1024, "KB")
