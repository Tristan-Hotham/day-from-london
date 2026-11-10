"""Step 3: calibrate, validate and run the model for every era, plus the planned sensitivity checks.

Outputs
  SCR/runs.npz                hours rasters for each era (base, low and high uncertainty band) and each sensitivity run
  data/journeys_model.csv     every documented journey with the modelled hours and the error (base and leave-one-out)
  data/coach_services.csv     the timed London coach services of 1819 and 1836 used to fit coach speeds (derived)
  data/towns_hours.csv        modelled hours from Charing Cross to the map towns, by era
  SCR/model_runs.json         numbers for step 4 (results.json)
"""
import sys, time
import numpy as np, pandas as pd, geopandas as gpd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from model import *

T0 = time.time()
fwd, inv = bng()
OE, ON = fwd.transform(ORIGIN[1], ORIGIN[0])
COACH = "/home/claude/newdata/raw_new13/day_from_london/coaches_icpsr_195128/London coaches.shp"
LEUNIG = {"1850": (22.7, 17.8), "1910": (36.9, 20.4)}   # Leunig 2006 WP Table 6, in-train crow-flies mph: important, minor
MPH = 1.609344


def log(*a):
    print(f"[{time.time() - T0:6.0f}s]", *a, file=sys.stderr, flush=True)


# ------------------------------------------------------------------ documented journeys and towns
J = pd.read_csv(f"{CODE}/journeys.csv")
J["E"], J["N"] = fwd.transform(J.lon.values, J.lat.values)
J["hours"] = np.where(J.unit == "days", J.value * 12.0, J.value)

ne = gpd.read_file(f"{GEO}/ne_10m_populated_places_simple.geojson")
ne = ne[(ne.adm0name == "United Kingdom") & (ne.name != "London")]
ne = ne[~((ne.longitude < -5.4) & (ne.latitude < 55.4) & (ne.latitude > 54))]       # Northern Ireland
TW = pd.DataFrame({"town": ne.name.replace({"Newcastle": "Newcastle upon Tyne", "Stoke": "Stoke-on-Trent"}).values,
                   "lat": ne.latitude.values, "lon": ne.longitude.values, "pop": ne.pop_max.values})
extra = J.drop_duplicates("town")[["town", "lat", "lon"]]
extra = extra[~extra.town.isin(TW.town)]
TW = pd.concat([TW, extra.assign(pop=np.nan)], ignore_index=True)
TW["E"], TW["N"] = fwd.transform(TW.lon.values, TW.lat.values)
TW["crow_km"] = np.hypot(TW.E - OE, TW.N - ON) / 1000

# ------------------------------------------------------------------ coach services (1819, 1836)
cg = gpd.read_file(COACH)
cg = cg[(cg.Start == "London")]
rows = []
for r in cg.itertuples():
    g = r.geometry
    if g is None or g.is_empty:
        continue
    lines = [g] if g.geom_type == "LineString" else list(g.geoms)
    pts = np.vstack([np.asarray(l.coords)[:, :2] for l in lines])
    d = np.hypot(pts[:, 0] - OE, pts[:, 1] - ON)
    e = pts[np.argmax(d)]
    for yr, t in ((1819, r.time1819), (1836, r.Batestime)):
        if int(r.Year) == yr and t and t > 0:
            rows.append(dict(year=yr, terminus=r.Terminus, hours=float(t), route_miles=float(r.length), E=e[0], N=e[1],
                             crow_km=d.max() / 1000, coach=(r.coa1819 if yr == 1819 else r.Batescoach) or ""))
CS = pd.DataFrame(rows)
CS = CS[CS.crow_km >= 15]          # leave out short stages inside the London area
CS["mph"] = CS.route_miles / CS.hours
# fastest service per terminus and year
CF = CS.sort_values("hours").drop_duplicates(["year", "terminus"]).reset_index(drop=True)
log("coach services", len(CS), "termini", CF.groupby("year").size().to_dict())

grid = Grid()


def times_matrix(era, cands, key, E, N, extra_speeds=None, P=None):
    M = np.zeros((len(cands), len(E)))
    for i, v in enumerate(cands):
        sp = dict(extra_speeds or {}); sp[key] = v
        R = solve(era, sp, P=P, grid=grid)
        M[i] = R.at(E, N)
    return M


def fit(M, cands, obs, groups=None):
    """Best candidate (min sum of squared log errors) and leave-one-group-out predictions."""
    ok = np.isfinite(M).all(axis=0) & np.isfinite(obs)
    L = (np.log(M[:, ok]) - np.log(obs[ok])) ** 2
    best = int(np.argmin(L.sum(axis=1)))
    pred_loo = np.full(len(obs), np.nan)
    g = np.asarray(groups if groups is not None else np.arange(len(obs)))
    for u in np.unique(g[ok]):
        m = (g[ok] == u)
        b = int(np.argmin(L[:, ~m].sum(axis=1)))
        idx = np.nonzero(ok)[0][m]
        pred_loo[idx] = M[b, idx]
    return best, pred_loo


def errs(pred, obs):
    ok = np.isfinite(pred) & np.isfinite(obs)
    pe = (pred[ok] - obs[ok]) / obs[ok] * 100
    lg = np.log(pred[ok] / obs[ok])
    return dict(n=int(ok.sum()), mdape=float(np.median(np.abs(pe))), mape=float(np.mean(np.abs(pe))),
                bias_log=float(np.mean(lg)), within20=float(np.mean(np.abs(pe) <= 20) * 100), median_pe=float(np.median(pe)))


OUT = {"fits": {}, "valid": {}, "speeds": {}, "sens": {}, "area": {}, "reach": {}}
RAST = {}
JM = []

# ------------------------------------------------------------------ 1830s: fit on Bates 1836
c36 = CF[CF.year == 1836].reset_index(drop=True)
cands = np.arange(9.0, 20.01, 0.5)
M36 = times_matrix("1830", cands, "tp", c36.E.values, c36.N.values)
b, loo = fit(M36, cands, c36.hours.values, c36.terminus.values)
v1830 = float(cands[b])
c36["model"] = M36[b]; c36["model_loo"] = loo
OUT["fits"]["1830"] = dict(speed_kmh=v1830, speed_mph=v1830 / MPH, n=len(c36), base=errs(M36[b], c36.hours.values), loo=errs(loo, c36.hours.values),
                           grid=[float(cands[0]), float(cands[-1])], at_edge=b in (0, len(cands) - 1))
log("1830 fit", v1830, OUT["fits"]["1830"]["loo"])

# 1819 check (Cary), turnpikes of 1820
c19 = CF[CF.year == 1819].reset_index(drop=True)
M19 = times_matrix("1820", cands, "tp", c19.E.values, c19.N.values)
b19, loo19 = fit(M19, cands, c19.hours.values, c19.terminus.values)
c19["model"] = M19[b19]; c19["model_loo"] = loo19
OUT["fits"]["1819"] = dict(speed_kmh=float(cands[b19]), speed_mph=float(cands[b19]) / MPH, n=len(c19), base=errs(M19[b19], c19.hours.values),
                           loo=errs(loo19, c19.hours.values), at_edge=b19 in (0, len(cands) - 1))
log("1819 fit", cands[b19], OUT["fits"]["1819"]["loo"])
pd.concat([c19, c36])[["year", "terminus", "coach", "hours", "route_miles", "crow_km", "mph", "model", "model_loo"]].round(3).to_csv(
    f"{DATA}/coach_services.csv", index=False)
CS[["year", "terminus", "coach", "hours", "route_miles", "crow_km", "mph"]].round(3).to_csv(f"{SCR}/coach_all.csv", index=False)
OUT["coach"] = dict(n_services_1819=int((CS.year == 1819).sum()), n_services_1836=int((CS.year == 1836).sum()),
                    n_termini_1819=len(c19), n_termini_1836=len(c36),
                    median_mph_1819=float(CS[CS.year == 1819].mph.median()), median_mph_1836=float(CS[CS.year == 1836].mph.median()),
                    median_mph_80plus_1836=float(CS[(CS.year == 1836) & (CS.route_miles >= 80)].mph.median()),
                    fastest_median_mph_1836=float(c36.mph.median()), fastest_median_mph_1819=float(c19.mph.median()))

# 1830s out of sample: the 1837 mail list and other dated checks
R1830 = solve("1830", {"tp": v1830}, grid=grid)
jv = J[J.era == "1830"].copy()
jv["model"] = R1830.at(jv.E.values, jv.N.values)
OUT["valid"]["1830_mail1837"] = errs(jv.model.values, jv.hours.values)
JM.append(jv)

# ------------------------------------------------------------------ 1750: fit on cited journeys
j50 = J[J.era == "1750"].copy().reset_index(drop=True)
c50 = np.arange(3.0, 14.01, 0.25)
M50 = times_matrix("1750", c50, "tp", j50.E.values, j50.N.values)
b50, loo50 = fit(M50, c50, j50.hours.values, j50.town.values)
v1750 = float(c50[b50])
j50["model"] = M50[b50]; j50["model_loo"] = loo50
OUT["fits"]["1750"] = dict(speed_kmh=v1750, speed_mph=v1750 / MPH, n=len(j50), n_towns=int(j50.town.nunique()),
                           base=errs(M50[b50], j50.hours.values), loo=errs(loo50, j50.hours.values), at_edge=b50 in (0, len(c50) - 1))
# day-length sensitivity (10 and 14 hours per coaching day)
for H in (10, 14):
    obs = np.where(j50.unit == "days", j50.value * H, j50.value)
    bh, _ = fit(M50, c50, obs, j50.town.values)
    OUT["fits"]["1750"][f"speed_kmh_day{H}"] = float(c50[bh])
JM.append(j50)
log("1750 fit", v1750, OUT["fits"]["1750"]["loo"])

# ------------------------------------------------------------------ rail circuity and Leunig speeds (1850, 1910)
big = TW[(TW.lat < 55.0) & TW["pop"].notna()].copy()
big = big[~big.town.isin(["Glasgow", "Edinburgh", "Aberdeen", "Dundee", "Greenock", "Ayr", "Inverness", "Perth", "Dumfries", "Fort William", "Kirkwall", "Wick", "Lerwick"])]
big = big.sort_values("pop", ascending=False).head(30)


def rail_circuity(era):
    P = dict(DEFAULT)
    lay = [x for x in era_layers(era, P, {"tp": 10.0, "rail": 1.0})if x[3]["kind"] == "rail"][0][0]
    G = coo_matrix((lay.km + 1e-9, (lay.s, lay.d)), shape=(lay.n, lay.n)).tocsr()
    tr = cKDTree(lay.V)
    o = tr.query_ball_point([OE, ON], 6000)       # London termini: any rail vertex within 6 km of Charing Cross
    d = dijkstra(G, indices=o, min_only=True)
    dd, k = tr.query(np.c_[big.E, big.N])
    net_km = d[k]
    ratio = net_km / big.crow_km.values
    ok = np.isfinite(ratio) & (dd < 5000)
    return float(np.median(ratio[ok])), int(ok.sum())


for era in ("1850", "1910"):
    circ, n = rail_circuity(era)
    imp, mino = LEUNIG[era]
    vmain = imp * MPH * circ
    OUT["speeds"][era] = dict(circuity=circ, n_towns=n, leunig_important_mph=imp, leunig_minor_mph=mino,
                              main_kmh=vmain, branch_ratio=mino / imp)
    log(era, "circuity", circ, "main km/h", vmain)

# ------------------------------------------------------------------ today: rail fitted on Visit London times
jt = J[J.era == "today"].copy().reset_index(drop=True)
ct = np.arange(80.0, 220.01, 5.0)
Mt = times_matrix("today", ct, "rail", jt.E.values, jt.N.values)
# a rail-only check: the modelled time today is the faster of car and train; the fit uses the rail model alone
P_railonly = dict(today_speeds={"motorway": 1.0, "trunk": 1.0, "primary": 1.0, "secondary": 1.0}, today_minor=4.8)
Mt_rail = times_matrix("today", ct, "rail", jt.E.values, jt.N.values, P=P_railonly)
bt, loot = fit(Mt_rail, ct, jt.hours.values, jt.town.values)
vt = float(ct[bt])
jt["model"] = Mt_rail[bt]; jt["model_loo"] = loot; jt["model_car_or_rail"] = Mt[bt]
OUT["fits"]["today_rail"] = dict(speed_kmh=vt, n=len(jt), base=errs(Mt_rail[bt], jt.hours.values), loo=errs(loot, jt.hours.values),
                                 at_edge=bt in (0, len(ct) - 1))
JM.append(jt)
log("today rail fit", vt, OUT["fits"]["today_rail"]["loo"])

SPEEDS = {"1750": {"tp": v1750}, "1830": {"tp": v1830},
          "1850": {"tp": v1830, "rail": OUT["speeds"]["1850"]["main_kmh"]},
          "1910": {"tp": v1830, "rail": OUT["speeds"]["1910"]["main_kmh"]},
          "today": {"rail": vt}}
PERA = {"1850": {"branch": OUT["speeds"]["1850"]["branch_ratio"]}, "1910": {"branch": OUT["speeds"]["1910"]["branch_ratio"]}}

# ------------------------------------------------------------------ rail eras: out-of-sample checks
for era in ("1850", "1910"):
    R = solve(era, SPEEDS[era], P=PERA.get(era), grid=grid)
    jj = J[J.era == era].copy()
    jj["model"] = R.at(jj.E.values, jj.N.values)
    OUT["valid"][era] = errs(jj.model.values[jj.set.values == "valid"], jj.hours.values[jj.set.values == "valid"])
    OUT["valid"][era + "_all"] = errs(jj.model.values, jj.hours.values)
    # fastest-train variant: rail speed fitted to the documented times
    cr = np.arange(30.0, 140.01, 5.0)
    Mr = times_matrix(era, cr, "rail", jj.E.values, jj.N.values, extra_speeds={"tp": v1830}, P=PERA.get(era))
    br, loor = fit(Mr, cr, jj.hours.values, jj.town.values)
    jj["model_fast"] = Mr[br]; jj["model_fast_loo"] = loor
    OUT["fits"][era + "_fastest"] = dict(speed_kmh=float(cr[br]), n=len(jj), base=errs(Mr[br], jj.hours.values), loo=errs(loor, jj.hours.values))
    JM.append(jj)
    log(era, "valid", OUT["valid"][era], "fastest fit", cr[br])

jm = pd.concat(JM, ignore_index=True)
jm["error_pc"] = (jm.model - jm.hours) / jm.hours * 100
cols = ["era", "set", "town", "year", "value", "unit", "hours", "mode", "source", "model", "model_loo", "error_pc", "model_fast", "model_car_or_rail", "note"]
jm[[c for c in cols if c in jm.columns]].round(3).to_csv(f"{DATA}/journeys_model.csv", index=False)

# ------------------------------------------------------------------ base runs, bands, towns
land_km2 = int(grid.n) * (CELL / 1000) ** 2
OUT["land_km2"] = land_km2
TH = TW[["town", "lat", "lon", "pop", "crow_km"]].copy()
cellE, cellN = grid.E, grid.N
crow_cell = np.hypot(cellE - OE, cellN - ON) / 1000
for era in ERAS:
    mdape = {"1750": OUT["fits"]["1750"]["loo"]["mdape"], "1830": OUT["fits"]["1830"]["loo"]["mdape"],
             "1850": OUT["valid"]["1850_all"]["mdape"], "1910": OUT["valid"]["1910_all"]["mdape"],
             "today": OUT["fits"]["today_rail"]["loo"]["mdape"]}[era]
    OUT["speeds"].setdefault(era, {}).update({k: float(v) for k, v in SPEEDS[era].items()})
    OUT["speeds"][era]["band_pc"] = mdape
    for tag, f in (("base", 1.0), ("fast", 1 + mdape / 100), ("slow", 1 / (1 + mdape / 100))):
        sp = {k: v * f for k, v in SPEEDS[era].items()}
        P = dict(PERA.get(era, {}))
        if era == "today" and tag != "base":
            P["today_speeds"] = {k: v * f for k, v in DEFAULT["today_speeds"].items()}; P["today_minor"] = DEFAULT["today_minor"] * f
        R = solve(era, sp, P=P, grid=grid)
        RAST[f"{era}_{tag}"] = R.raster()
        c = R.cells
        OUT["area"].setdefault(era, {})[tag] = dict(km2_12h=float((c <= 12).sum() * 4), share_12h=float((c <= 12).mean() * 100),
                                                     km2_6h=float((c <= 6).sum() * 4), km2_24h=float((c <= 24).sum() * 4))
        if tag == "base":
            TH[era] = R.at(TW.E.values, TW.N.values)
            reach = c <= 12
            OUT["reach"][era] = dict(max_crow_km=float(crow_cell[reach].max()), median_hours_towns=float(np.nanmedian(np.where(np.isfinite(TH[era]), TH[era], np.nan))))
    log(era, OUT["area"][era]["base"])
TH.round(3).to_csv(f"{DATA}/towns_hours.csv", index=False)

# ------------------------------------------------------------------ sensitivity
SENS = [("budget8", None, {}), ("budget16", None, {}), ("r04", {"r": 0.4}, {}), ("r08", {"r": 0.8}, {}), ("r10", {"r": 1.0}, {}),
        ("wait0", {"wait": 0.0, "ferry_wait": 0.0}, {}), ("wait60", {"wait": 1.0, "ferry_wait": 1.0}, {}),
        ("walk4", {"walk": 4.0}, {}), ("walk6", {"walk": 6.0}, {}), ("branch035", {"branch": 0.35}, {}), ("branch07", {"branch": 0.7}, {}),
        ("grid4", {"cell": 4000}, {}), ("noinferred", {"inferred": False}, {}), ("fastest_train", None, {})]
g4 = Grid(4000)
for name, _, _ in SENS:
    OUT["sens"][name] = {}
for era in ERAS:
    for name, Pd, _ in SENS:
        if name == "noinferred" and era != "1910":
            continue
        if name.startswith("branch") and era not in ("1850", "1910", "today"):
            continue
        if name in ("r04", "r08", "r10", "walk4", "walk6") and era == "today":
            continue
        if name.startswith("budget"):
            c = RAST[f"{era}_base"]; c = c[np.isfinite(c)]
            hb = 8 if name == "budget8" else 16
            OUT["sens"][name][era] = float((c <= hb).sum() * 4)
            continue
        P = dict(PERA.get(era, {}))
        if Pd:
            P.update(Pd)
        sp = dict(SPEEDS[era])
        if name == "fastest_train":
            if era not in ("1850", "1910"):
                continue
            sp["rail"] = OUT["fits"][era + "_fastest"]["speed_kmh"]
        R = solve(era, sp, P=P, grid=g4 if name == "grid4" else grid)
        OUT["sens"][name][era] = float((R.cells <= 12).sum() * (R.grid.cell / 1000) ** 2)
    log("sens", era, {k: v.get(era) for k, v in OUT["sens"].items()})
# 1750 with 10 and 14 hour coaching days
for H in (10, 14):
    R = solve("1750", {"tp": OUT["fits"]["1750"][f"speed_kmh_day{H}"]}, grid=grid)
    OUT["sens"].setdefault("day_hours", {})[str(H)] = float((R.cells <= 12).sum() * 4)

np.savez_compressed(f"{SCR}/runs.npz", **RAST)
jsave(OUT, f"{SCR}/model_runs.json", indent=1)
log("done")
