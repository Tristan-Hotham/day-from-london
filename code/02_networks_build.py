"""Step 2: the land grid and the era networks, as plain arrays, cached in SCR/net.pkl.

Land grid: 2 km cells (British National Grid) whose centre lies in a Great Britain local authority (ONS LAD 2023, England,
Wales and Scotland; Northern Ireland dropped). Each cell knows whether it is in Scotland.

Line sets (each a list of (Nx2 float array in metres, attributes)):
  turnpike  the Rosevear et al. turnpike and main road map (England and Wales): TP_1750, TP_1830, TP_1838 codes, ferry flag.
            Code 9 (not yet built) is kept in the attributes and dropped per era in step 3.
  scot      OSM trunk and primary roads inside Scotland (proxy for Scotland's main roads before the motor age).
  osm_road  OSM motorway, trunk, primary, secondary (today).
  rail1851  the 1851 lines (CAMPOP).
  rail_osm  today's OSM rail (z10) ; rail_main marks lines OSM shows at z8.
  rail_inf  inferred 1910 lines: stations closed after 1910 lying more than 2 km from rail1851 and rail_osm, joined by a
            minimum spanning tree (links at most 15 km) plus the shortest link from each tree to the network.
Stations by era: 1850, 1910, today (see NOTES plan).
"""
import pickle, sys
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import minimum_spanning_tree, connected_components
from scipy.sparse import coo_matrix
from rasterio import features
from rasterio.transform import from_origin
from common import *

OUT = os.path.join(SCR, "net.pkl")
TP_DIR = "/home/claude/newdata/raw_new13/day_from_london/turnpikes_icpsr_195126/turnpikes-and-main-2025"
TP_SHP = os.path.join(TP_DIR, "turnpikes and main 2026.shp")


def lines_of(geom):
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [np.asarray(geom.coords)[:, :2]]
    if geom.geom_type == "MultiLineString":
        return [np.asarray(g.coords)[:, :2] for g in geom.geoms]
    return []


def main():
    fwd, inv = bng()
    # ---------- land grid
    lad = gpd.read_file(f"{GEO}/lad23_bgc.geojson").to_crs(27700)
    code = [c for c in lad.columns if c.upper().startswith("LAD") and c.upper().endswith("CD")][0]
    lad = lad[~lad[code].str.startswith("N")]
    nx, ny = (X1 - X0) // CELL, (Y1 - Y0) // CELL
    tr = from_origin(X0, Y1, CELL, CELL)
    land = features.rasterize(((g, 1) for g in lad.geometry), out_shape=(ny, nx), transform=tr, all_touched=False, dtype="uint8")
    scot = features.rasterize(((g, 1) for g in lad[lad[code].str.startswith("S")].geometry), out_shape=(ny, nx), transform=tr, dtype="uint8")
    wales = features.rasterize(((g, 1) for g in lad[lad[code].str.startswith("W")].geometry), out_shape=(ny, nx), transform=tr, dtype="uint8")
    print("land cells", int(land.sum()), "km2", int(land.sum()) * 4, file=sys.stderr)

    # ---------- turnpike map
    tp = gpd.read_file(TP_SHP)
    T = []
    for r in tp.itertuples():
        trust = str(r.TRUST) if r.TRUST is not None else ""
        ferry = str(r.wasTP or "").upper().startswith("F") or trust.startswith("-")
        a = dict(tp1750=int(r.TP_1750), tp1820=int(r.TP_1820), tp1830=int(r.TP_1830), tp1838=int(r.TP_1838), ferry=bool(ferry),
                 old=str(r.Old_or_new or ""), cary=int(r.Cary_map))
        for ln in lines_of(r.geometry):
            if len(ln) >= 2:
                T.append((ln.astype(np.float64), a))
    print("turnpike lines", len(T), file=sys.stderr)

    print("osm", file=sys.stderr, flush=True)
    # ---------- OSM
    O = pickle.load(gzip.open(os.path.join(SCR, "osm_lines.pkl"), "rb"))
    osm_road = []
    scot_lines = []
    for c, arrs in O["roads"].items():
        for a in arrs:
            a = a.astype(np.float64)
            osm_road.append((a, {"cls": c}))
            if c in ("trunk", "primary", "motorway"):
                mid = a[len(a) // 2]
                ci, cj = int((Y1 - mid[1]) // CELL), int((mid[0] - X0) // CELL)
                if 0 <= ci < ny and 0 <= cj < nx and scot[max(0, ci - 1):ci + 2, max(0, cj - 1):cj + 2].any():
                    scot_lines.append((a, {"cls": c}))
    rail_osm = [(a.astype(np.float64), {}) for a in O["rail"]]
    rail_main_pts = np.vstack([densify(a.astype(np.float64), 200) for a in O["rail_main"]])

    print("r51", file=sys.stderr, flush=True)
    # ---------- 1851 rail
    shp = [f for f in os.listdir(RAIL1851) if f.endswith(".shp")][0]
    r51 = gpd.read_file(os.path.join(RAIL1851, shp)).to_crs(27700)
    rail1851 = [(ln, {}) for g in r51.geometry for ln in lines_of(g) if len(ln) >= 2]

    print("st", file=sys.stderr, flush=True)
    # ---------- stations
    op = pd.read_csv(f"{BEECH}/open_stations.csv")
    op["y0"] = pd.to_numeric(op.wd_open_years.astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    cl = pd.read_csv(f"{BEECH}/closed_stations.csv").dropna(subset=["lat", "lon"])
    cl = cl[(cl.lat > 49.8) & (cl.lat < 61) & (cl.lon > -8.5) & (cl.lon < 2)]
    oe, on = fwd.transform(op.lon.values, op.lat.values)
    ce, cn = fwd.transform(cl.lon.values, cl.lat.values)
    op["E"], op["N"] = oe, on
    cl["E"], cl["N"] = ce, cn
    # pre-1975 "open" list includes stations opened after the era: the opening year decides.
    r51pts = np.vstack([densify(a, 200) for a, _ in rail1851])
    osmpts = np.vstack([densify(a, 200) for a, _ in rail_osm])
    t51, tosm = cKDTree(r51pts), cKDTree(osmpts)
    d51 = t51.query(np.c_[cl.E, cl.N])[0]
    dosm = tosm.query(np.c_[cl.E, cl.N])[0]
    st1850 = np.vstack([op.loc[op.y0 <= 1850, ["E", "N"]].values, cl.loc[d51 <= 500, ["E", "N"]].values])
    st1910 = np.vstack([op.loc[op.y0 <= 1910, ["E", "N"]].values, cl.loc[cl.year_closed > 1910, ["E", "N"]].values])
    sttoday = op[["E", "N"]].values

    print("inf", file=sys.stderr, flush=True)
    # ---------- inferred 1910 lines
    far = cl[(cl.year_closed > 1910) & (np.minimum(d51, dosm) > 2000)].copy()
    P = far[["E", "N"]].values
    inf = []
    if len(P):
        tr_ = cKDTree(P)
        pairs = tr_.query_pairs(15000, output_type="ndarray")
        dd = np.hypot(*(P[pairs[:, 0]] - P[pairs[:, 1]]).T)
        M = coo_matrix((dd + 1e-6, (pairs[:, 0], pairs[:, 1])), shape=(len(P), len(P)))
        mst = minimum_spanning_tree(M).tocoo()
        for i, j in zip(mst.row, mst.col):
            inf.append((np.array([P[i], P[j]]), {"kind": "mst"}))
        ncomp, lab = connected_components(mst, directed=False)
        allnet = np.vstack([r51pts, osmpts])
        tall = cKDTree(allnet)
        for k in range(ncomp):
            idx = np.where(lab == k)[0]
            d, j = tall.query(P[idx])
            b = np.argmin(d)
            if d[b] <= 15000:
                inf.append((np.array([P[idx[b]], allnet[j[b]]]), {"kind": "link"}))
    print("inferred 1910 stations", len(P), "links", len(inf), "km", round(sum(np.hypot(*(a[1] - a[0])) for a, _ in inf) / 1000), file=sys.stderr)

    net = dict(land=land, scot=scot, wales=wales, turnpike=T, scot_roads=scot_lines, osm_road=osm_road, rail1851=rail1851,
               rail_osm=rail_osm, rail_inf=inf, rail_main_pts=rail_main_pts, st={"1850": st1850, "1910": st1910, "today": sttoday},
               n_far_closed=len(P))
    pickle.dump(net, gzip.open(OUT, "wb"))
    print("saved", OUT)


def densify(a, step):
    """Resample a polyline so consecutive vertices are at most `step` metres apart (keeps original vertices)."""
    a = a[np.isfinite(a).all(axis=1)]
    if len(a) == 0:
        return np.zeros((0, 2))
    out = [a[:1]]
    for p, q in zip(a[:-1], a[1:]):
        L = math.hypot(*(q - p))
        k = max(1, int(math.ceil(L / step)))
        t = np.arange(1, k + 1)[:, None] / k
        out.append(p + (q - p) * t)
    return np.vstack(out)


if __name__ == "__main__":
    main()
