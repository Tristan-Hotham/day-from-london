"""Step 4: data/results.json, holding every number quoted anywhere, from SCR/model_runs.json, data/journeys_model.csv,
data/towns_hours.csv and data/coach_services.csv. Also data/isochrone_areas.csv."""
import numpy as np, pandas as pd
from common import *

M = jload(f"{SCR}/model_runs.json")
J = pd.read_csv(f"{DATA}/journeys_model.csv")
T = pd.read_csv(f"{DATA}/towns_hours.csv")
C = pd.read_csv(f"{DATA}/coach_services.csv")
R = {"slug": SLUG, "budget_h": BUDGET_H, "cell_km": CELL / 1000, "land_km2": M["land_km2"], "eras": ERAS,
     "era_label": ERA_LABEL}
from model import Grid
g4 = Grid(4000); land4 = g4.n * 16.0
for e, v_ in M["sens"]["grid4"].items():      # express the 4 km result on the 2 km land total, so shares compare
    M["sens"]["grid4"][e] = v_ * M["land_km2"] / land4
R["land4_km2"] = land4
R["fits"] = M["fits"]; R["valid"] = M["valid"]; R["speeds"] = M["speeds"]; R["sens"] = M["sens"]; R["coach"] = M["coach"]
R["area"] = M["area"]; R["reach"] = M["reach"]
mph = lambda k: k / MI

# headline areas
A = {}
for e in ERAS:
    a = M["area"][e]
    A[e] = dict(km2=a["base"]["km2_12h"], share=a["base"]["share_12h"], lo=a["slow"]["km2_12h"], hi=a["fast"]["km2_12h"],
                share_lo=a["slow"]["km2_12h"] / M["land_km2"] * 100, share_hi=a["fast"]["km2_12h"] / M["land_km2"] * 100,
                km2_6h=a["base"]["km2_6h"], km2_24h=a["base"]["km2_24h"], reach_km=M["reach"][e]["max_crow_km"])
R["A"] = A
R["ratio"] = {"1830_1750": A["1830"]["km2"] / A["1750"]["km2"], "1850_1830": A["1850"]["km2"] / A["1830"]["km2"],
              "1910_1850": A["1910"]["km2"] / A["1850"]["km2"], "today_1750": A["today"]["km2"] / A["1750"]["km2"],
              "1910_1750": A["1910"]["km2"] / A["1750"]["km2"]}
pd.DataFrame([dict(era=ERA_LABEL[e], km2_12h=round(A[e]["km2"]), share_pc=round(A[e]["share"], 1), km2_12h_band_low=round(A[e]["lo"]),
                   km2_12h_band_high=round(A[e]["hi"]), km2_6h=round(A[e]["km2_6h"]), km2_24h=round(A[e]["km2_24h"]),
                   farthest_crow_km=round(A[e]["reach_km"])) for e in ERAS]).to_csv(f"{DATA}/isochrone_areas.csv", index=False)

# speeds in mph for prose
R["mph"] = {"1750": mph(M["fits"]["1750"]["speed_kmh"]), "1830": mph(M["fits"]["1830"]["speed_kmh"]),
            "1819": mph(M["fits"]["1819"]["speed_kmh"]), "rail1850": mph(M["speeds"]["1850"]["main_kmh"]),
            "rail1910": mph(M["speeds"]["1910"]["main_kmh"]), "railtoday": mph(M["fits"]["today_rail"]["speed_kmh"]),
            "fast1850": mph(M["fits"]["1850_fastest"]["speed_kmh"]), "fast1910": mph(M["fits"]["1910_fastest"]["speed_kmh"])}

# towns: hours by era
T = T.set_index("town")
key = ["Manchester", "Birmingham", "Bristol", "York", "Exeter", "Edinburgh", "Glasgow", "Holyhead", "Aberdeen", "Inverness",
       "Penzance", "Norwich", "Dover", "Brighton", "Cardiff", "Newcastle upon Tyne", "Liverpool", "Leeds", "Carlisle", "Plymouth", "Oxford", "Cambridge", "Wick"]
R["towns"] = {t: {e: (None if not np.isfinite(T.loc[t, e]) else float(T.loc[t, e])) for e in ERAS} for t in key if t in T.index}
within = {e: int((T[e] <= BUDGET_H).sum()) for e in ERAS}
R["towns_n"] = len(T); R["towns_within"] = within
R["towns_within_pc"] = {e: within[e] / len(T) * 100 for e in ERAS}
# farthest big town within the day, by era (by crow distance)
far = {}
for e in ERAS:
    s = T[(T[e] <= BUDGET_H)].sort_values("crow_km", ascending=False)
    far[e] = dict(town=s.index[0], km=float(s.crow_km.iloc[0]), hours=float(s[e].iloc[0])) if len(s) else None
R["farthest_town"] = far

# documented London to Edinburgh, and the model
ed = J[J.town == "Edinburgh"].sort_values("year")
R["edinburgh_doc"] = [dict(year=int(r.year), hours=float(r.hours), value=float(r.value), unit=r.unit, mode=r["mode"], source=r.source) for _, r in ed.iterrows()]
R["edinburgh_model"] = {e: R["towns"]["Edinburgh"][e] for e in ERAS}
# Janelle-style convergence from the model: minutes saved per year London to Edinburgh between eras (era years 1750, 1836, 1850, 1910, 2026)
YR = {"1750": 1750, "1830": 1836, "1850": 1850, "1910": 1910, "today": 2026}
conv = {}
for a, b in (("1750", "1830"), ("1830", "1850"), ("1850", "1910"), ("1910", "today")):
    ta, tb = R["edinburgh_model"][a], R["edinburgh_model"][b]
    conv[f"{a}_{b}"] = (ta - tb) * 60 / (YR[b] - YR[a])
R["convergence_edinburgh_min_per_year"] = conv

# validation tables
def ev(df, col="model"):
    d = df[np.isfinite(df[col]) & np.isfinite(df.hours)]
    pe = (d[col] - d.hours) / d.hours * 100
    return dict(n=len(d), mdape=float(np.median(np.abs(pe))), bias=float(np.median(pe)))

R["valid_rows"] = {}
for e in ("1750", "1830", "1850", "1910", "today"):
    d = J[J.era == e]
    R["valid_rows"][e] = [dict(town=r.town, year=int(r.year), doc=float(r.hours), model=float(r.model),
                               loo=(None if pd.isna(r.get("model_loo")) else float(r.model_loo)), err=float(r.error_pc), source=r.source)
                          for _, r in d.iterrows()]
# examples for prose
def row(e, town, year=None):
    d = J[(J.era == e) & (J.town == town)]
    if year: d = d[d.year == year]
    r = d.iloc[0]
    return dict(doc=float(r.hours), model=float(r.model), err=float(r.error_pc), year=int(r.year))
R["ex"] = {"edinburgh_1754": row("1750", "Edinburgh", 1754), "manchester_1754": row("1750", "Manchester", 1754),
           "edinburgh_1837": row("1830", "Edinburgh"), "holyhead_1837": row("1830", "Holyhead"), "brighton_1837": row("1830", "Brighton"),
           "liverpool_1851": row("1850", "Liverpool"), "edinburgh_1901": row("1910", "Edinburgh"), "penzance_1904": row("1910", "Penzance"),
           "bristol_1903": row("1910", "Bristol"), "edinburgh_today": row("today", "Edinburgh")}
# coach speed distribution
C36 = C[C.year == 1836]; C19 = C[C.year == 1819]
R["coach"].update(dict(n_fit_1836=len(C36), n_fit_1819=len(C19)))
# sensitivity ranges for 12-hour area
rng = {}
for e in ERAS:
    vals = [v[e] for k, v in M["sens"].items() if isinstance(v, dict) and e in v and not k.startswith("budget")]
    rng[e] = dict(min=float(min(vals)), max=float(max(vals)), n=len(vals))
R["sens_range"] = rng
R["sens_budget"] = {e: {"8": M["sens"]["budget8"][e], "16": M["sens"]["budget16"][e]} for e in ERAS}

for e in ERAS:
    assert 0 < A[e]["km2"] <= M["land_km2"]
assert A["1750"]["km2"] < A["1830"]["km2"] < A["1850"]["km2"] < A["1910"]["km2"] <= A["today"]["km2"] + 1e-6, "areas not increasing"
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({e: (round(A[e]["km2"]), round(A[e]["share"], 1), round(A[e]["reach_km"])) for e in ERAS}))
print("towns within", within, "of", len(T))
print("edinburgh model", {e: round(v, 1) for e, v in R["edinburgh_model"].items()})
print("mph", {k: round(v, 1) for k, v in R["mph"].items()})
