"""The travel-time model: one directed graph per era, shortest paths from Charing Cross (scipy Dijkstra).

Nodes: the land cells of the 2 km grid, plus the vertices of each network layer (lines resampled every STEP metres).
Edges: cell to its 8 neighbours (walking, or driving on minor roads today); along each line at the layer's speed;
cell <-> network vertex access links (walking to the vertex; a wait on boarding where the era has one).
All times in hours.
"""
import pickle
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from common import *

STEP = 300.0
NET = None

DEFAULT = dict(
    walk=4.8,            # km/h, all eras before today
    r=0.6,               # non-turnpike main road speed as a share of the turnpike speed
    wait=0.5,            # hours: boarding a train (rail eras) or a feeder coach (1850, 1910)
    ferry_wait=0.5,      # hours added on each ferry crossing in the turnpike map
    branch=0.5,          # branch-line speed as a share of the main-line speed
    station_km=1.5,      # rail vertices within this distance of an era station can be boarded
    budget=12.0,
    cell=CELL,
    inferred=True,       # 1910: include inferred lines
    today_minor=30.0,    # km/h between cells today
    today_speeds={"motorway": 100.0, "trunk": 80.0, "primary": 60.0, "secondary": 45.0},
)


def net():
    global NET
    if NET is None:
        NET = pickle.load(gzip.open(os.path.join(SCR, "net.pkl"), "rb"))
    return NET


def resample(a, step=STEP):
    a = a[np.isfinite(a).all(axis=1)]
    if len(a) < 2:
        return a
    seg = np.hypot(*np.diff(a, axis=0).T)
    keep = np.r_[True, seg > 0]
    a = a[keep]
    if len(a) < 2:
        return a
    out = [a[:1]]
    for p, q in zip(a[:-1], a[1:]):
        L = math.hypot(*(q - p))
        k = max(1, int(math.ceil(L / step)))
        t = np.arange(1, k + 1)[:, None] / k
        out.append(p + (q - p) * t)
    return np.vstack(out)


class Grid:
    def __init__(self, cell=CELL):
        N = net()
        land = N["land"]
        if cell != CELL:   # coarser grid for the sensitivity check: a coarse cell is land if any fine cell is
            f = cell // CELL
            h, w = land.shape[0] // f * f, land.shape[1] // f * f
            land = land[:h, :w].reshape(h // f, f, w // f, f).max(axis=(1, 3))
        self.cell = cell
        self.land = land
        self.ny, self.nx = land.shape
        ii, jj = np.nonzero(land)
        self.ii, self.jj = ii, jj
        self.n = len(ii)
        self.idx = -np.ones(land.shape, int)
        self.idx[ii, jj] = np.arange(self.n)
        self.E = X0 + (jj + 0.5) * cell
        self.N = Y1 - (ii + 0.5) * cell
        self.tree = cKDTree(np.c_[self.E, self.N])

    def edges(self, speed_kmh):
        src, dst, w = [], [], []
        for di, dj in ((0, 1), (1, 0), (1, 1), (1, -1)):
            a =self.idx[0:self.ny - di, max(0, -dj):self.nx - max(0, dj)]
            b = self.idx[di:self.ny, max(0, dj):self.nx - max(0, -dj)]
            m = (a >= 0) & (b >= 0)
            L = self.cell / 1000 * math.hypot(di, dj)
            src += [a[m], b[m]]; dst += [b[m], a[m]]; w += [np.full(m.sum() * 2, L / speed_kmh)]
        return np.concatenate(src), np.concatenate(dst), np.concatenate(w)

    def cell_of(self, E, N, maxd=3000):
        d, k = self.tree.query(np.c_[E, N])
        k = np.where(d <= maxd, k, -1)
        return k, d


class Layer:
    """Polylines resampled into vertices. Edges remember their line and length, so speeds can change without rebuilding."""

    def __init__(self, lines, snap=40.0):
        V, S, D, KM, LN, FI = [], [], [], [], [], []
        off = 0
        for k, a in enumerate(lines):
            r = resample(a)
            if len(r) < 2:
                continue
            n = len(r)
            seg = np.hypot(*np.diff(r, axis=0).T) / 1000.0
            V.append(r)
            i = np.arange(off, off + n - 1)
            first = np.zeros(n - 1, bool); first[0] = True
            S += [i, i + 1]; D += [i + 1, i]; KM += [seg, seg]; LN += [np.full(2 * (n - 1), k)]; FI += [first, first]
            off += n
        self.V = np.vstack(V)
        s, d, km, ln, fi = (np.concatenate(x) for x in (S, D, KM, LN, FI))
        tr = cKDTree(self.V)
        pr = tr.query_pairs(snap, output_type="ndarray")
        if len(pr):
            s = np.r_[s, pr[:, 0], pr[:, 1]]; d = np.r_[d, pr[:, 1], pr[:, 0]]
            km = np.r_[km, np.zeros(2 * len(pr))]; ln = np.r_[ln, -np.ones(2 * len(pr), int)]; fi = np.r_[fi, np.zeros(2 * len(pr), bool)]
        self.s, self.d, self.km, self.ln, self.fi = s, d, km, ln, fi
        self.n = len(self.V)
        self.nlines = len(lines)

    def weights(self, speed, extra=None):
        sp = np.r_[speed, 1.0][self.ln]          # snaps (ln = -1) take the appended 1.0 and have 0 km
        w = self.km / np.maximum(sp, 1e-6)
        if extra is not None:
            w = w + np.r_[extra, 0.0][self.ln] * self.fi
        bad = np.r_[speed, 1.0][self.ln] <= 0
        return w, bad


_LAYER_CACHE = {}


def layer_for(key, lines_fn):
    if key not in _LAYER_CACHE:
        _LAYER_CACHE[key] = lines_fn()
    return _LAYER_CACHE[key]


def era_layers(era, P, speeds):
    """speeds: 'tp' (turnpike coach km/h; also the feeder coaches of 1850 and 1910) and 'rail' (main-line km/h)."""
    N = net()
    out = []
    road_era = {"1750": "tp1750", "1820": "tp1820", "1830": "tp1830", "1850": "tp1838", "1910": "tp1838"}
    if era in road_era:
        f = road_era[era]; yr = int(f[2:])
        def mk():
            lines = [a for a, _ in N["turnpike"]] + [a for a, _ in N["scot_roads"]]
            lay = Layer(lines)
            lay.code = np.array([at[f] for _, at in N["turnpike"]] + [-1] * len(N["scot_roads"]))
            lay.ferry = np.array([at["ferry"] for _, at in N["turnpike"]] + [False] * len(N["scot_roads"]))
            return lay
        lay = layer_for(("road", f), mk)
        v = speeds["tp"]
        sp = np.where(lay.code == yr, v, v * P["r"])
        sp = np.where(np.isin(lay.code, [7, 8, 9]), 0.0, sp)
        sp = np.where(lay.code == -1, v * P["r"] if era == "1750" else v, sp)
        ex = np.where(lay.ferry, P["ferry_wait"], 0.0)
        out.append((lay, sp, ex, dict(kind="road", wait=P["wait"] if era in ("1850", "1910") else 0.0)))
    if era == "today":
        def mk():
            lay = Layer([a for a, _ in N["osm_road"]])
            lay.cls = np.array([at["cls"] for _, at in N["osm_road"]])
            return lay
        lay = layer_for(("road", "today"), mk)
        sp = np.array([P["today_speeds"][c] for c in lay.cls])
        out.append((lay, sp, None, dict(kind="road", wait=0.0)))
    if era in ("1850", "1910", "today"):
        inf = P["inferred"] and era == "1910"
        def mk():
            if era == "1850":
                lines = [a for a, _ in N["rail1851"]]
            elif era == "1910":
                lines = [a for a, _ in N["rail1851"]] + [a for a, _ in N["rail_osm"]] + ([a for a, _ in N["rail_inf"]] if inf else [])
            else:
                lines = [a for a, _ in N["rail_osm"]]
            lay = Layer(lines)
            mt = cKDTree(N["rail_main_pts"])
            lay.main = np.array([((mt.query(resample(a, 500))[0] <= 250).mean() >= 0.5) if len(a) > 1 else False for a in lines])
            return lay
        lay = layer_for(("rail", era, inf), mk)
        vm = speeds["rail"]
        sp = np.where(lay.main, vm, vm * P["branch"])
        out.append((lay, sp, None, dict(kind="rail", wait=P["wait"], stations=N["st"][era])))
    return out


def build(era, P, speeds, grid):
    walk = P["today_minor"] if era == "today" else P["walk"]
    s0, d0, w0 = grid.edges(walk)
    S, D, W = [s0], [d0], [w0]
    off = grid.n
    info = []
    for lay, sp, ex, acc in era_layers(era, P, speeds):
        w, bad = lay.weights(sp, ex)
        S.append(lay.s[~bad] + off); D.append(lay.d[~bad] + off); W.append(w[~bad])
        V = lay.V
        key = ("acc", id(lay), acc["kind"], P["station_km"], grid.cell, era if acc["kind"] == "rail" else "")
        if key not in _LAYER_CACHE:
            ok = np.ones(len(V), bool)
            if acc["kind"] == "rail":
                ok = cKDTree(acc["stations"]).query(V)[0] <= P["station_km"] * 1000
            if acc["kind"] == "road":   # vertices only on usable lines
                pass
            k, dist = grid.cell_of(V[:, 0], V[:, 1], maxd=grid.cell * 1.5)
            ok &= k >= 0
            vi = np.nonzero(ok)[0]
            _LAYER_CACHE[key] = (vi, k[vi], dist[vi])
        vi, kc, dist = _LAYER_CACHE[key]
        t_walk = dist / 1000.0 / walk
        S += [kc, vi + off]; D += [vi + off, kc]; W += [t_walk + acc["wait"], t_walk]
        info.append(dict(off=off, n=lay.n, V=V, kind=acc["kind"], vi=vi))
        off += lay.n
    s, d, w = np.concatenate(S), np.concatenate(D), np.concatenate(W)
    G = coo_matrix((w + 1e-9, (s, d)), shape=(off, off)).tocsr()
    return G, info, off


_LAST = [None]


def solve(era, speeds, P=None, grid=None, limit=250.0):
    if _LAST[0] != era:          # keep only one era's layers in memory
        _LAYER_CACHE.clear(); _LAST[0] = era
    P = dict(DEFAULT, **(P or {}))
    grid = grid or Grid(P["cell"])
    G, info, n = build(era, P, speeds, grid)
    fwd, _ = bng()
    oE, oN = fwd.transform(ORIGIN[1], ORIGIN[0])
    o = int(grid.tree.query([oE, oN])[1])
    t = dijkstra(G, directed=True, indices=o, limit=limit)
    walk = P["today_minor"] if era == "today" else P["walk"]
    return Result(grid, info, t, walk, era)


class Result:
    def __init__(self, grid, info, t, walk, era):
        self.grid, self.info, self.t, self.walk, self.era = grid, info, t, walk, era
        self.cells = t[:grid.n]
        V = [grid.tree.data] + [x["V"] for x in info]
        self.allV = np.vstack(V)
        self.tree = cKDTree(self.allV)

    def at(self, E, N, r=2500.0):
        """Hours to points: min over nodes within r metres of (node time + walk from node to the point)."""
        out = np.full(len(E), np.inf)
        for i, (e, n) in enumerate(zip(E, N)):
            ids = self.tree.query_ball_point([e, n], r)
            if not ids:
                continue
            ids = np.array(ids)
            dd = np.hypot(self.allV[ids, 0] - e, self.allV[ids, 1] - n) / 1000.0
            out[i] = np.min(self.t[ids] + dd / self.walk)
        return out

    def raster(self):
        R = np.full(self.grid.land.shape, np.nan, np.float32)
        R[self.grid.ii, self.grid.jj] = self.cells
        return R
