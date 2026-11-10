"""Step 1: today's road and rail networks of Great Britain from OpenFreeMap vector tiles (OpenStreetMap, ODbL).

Zoom 10 tiles over Great Britain: road centrelines of class motorway, trunk, primary and secondary, and railway lines of
subclass "rail" (narrow gauge, light rail, subway, tram, funicular and construction left out). Zoom 8 tiles: the railway
lines OpenMapTiles already shows at that zoom, used to mark today's main lines. Coordinates are converted to the British
National Grid and kept only inside the GB bounding box. Tiles are read into memory and cached as one compressed pickle in
SCR (deleted at the end of the build).
Output: SCR/osm_lines.pkl  {"roads": {class: [Nx2 arrays]}, "rail": [arrays], "rail_main": [arrays]}
"""
import sys, time, pickle, urllib.request, io
import numpy as np
import mapbox_vector_tile as mvt
from concurrent.futures import ThreadPoolExecutor
from common import *

UA = {"User-Agent": "historical-travel-study/1.0 (research)"}
OUT = os.path.join(SCR, "osm_lines.pkl")
ROADS = {"motorway", "trunk", "primary", "secondary"}
LON0, LON1, LAT0, LAT1 = -8.2, 1.9, 49.85, 60.9


def tile_xy(lon, lat, n):
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return int(x), int(y)


def main():
    if os.path.exists(OUT):
        print("cached", OUT); return
    tj = json.load(urllib.request.urlopen(urllib.request.Request("https://tiles.openfreemap.org/planet", headers=UA)))
    URL = tj["tiles"][0]
    fwd, _ = bng()

    def fetch(args):
        z, x, y = args
        n = 2 ** z
        for k in range(5):
            try:
                b = urllib.request.urlopen(urllib.request.Request(URL.format(z=z, x=x, y=y), headers=UA), timeout=60).read()
                d = mvt.decode(b, default_options={"y_coord_down": True})
                out = []
                lay = d.get("transportation")
                if not lay:
                    return args, out
                ext = lay["extent"]
                for f in lay["features"]:
                    p = f["properties"]; c = p.get("class")
                    if c in ROADS:
                        kind = c
                    elif c == "rail" and p.get("subclass") == "rail" and not p.get("service"):
                        kind = "rail"
                    else:
                        continue
                    g = f["geometry"]
                    if g["type"] not in ("LineString", "MultiLineString"):
                        continue
                    for ln in (g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]):
                        a = np.array(ln, float)
                        lon = (x + a[:, 0] / ext) / n * 360 - 180
                        lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * (y + a[:, 1] / ext) / n))))
                        E, N = fwd.transform(lon, lat)
                        out.append((kind, np.c_[E, N].astype(np.float32)))
                return args, out
            except Exception as ex:
                time.sleep(2 + 3 * k)
        print("failed", args, file=sys.stderr)
        return args, None

    jobs = []
    for z in (10, 8):
        n = 2 ** z
        xa, ya = tile_xy(LON0, LAT1, n); xb, yb = tile_xy(LON1, LAT0, n)
        jobs += [(z, x, y) for x in range(xa, xb + 1) for y in range(ya, yb + 1)]
    print("tiles", len(jobs), file=sys.stderr)
    res = {"roads": {c: [] for c in ROADS}, "rail": [], "rail_main": []}
    failed = 0
    t0 = time.time()
    with ThreadPoolExecutor(8) as ex:
        for i, ((z, x, y), out) in enumerate(ex.map(fetch, jobs)):
            if out is None:
                failed += 1; continue
            for kind, a in out:
                if not ((a[:, 0] > -50000) & (a[:, 0] < 700000) & (a[:, 1] > -10000) & (a[:, 1] < 1250000)).any():
                    continue
                if kind == "rail":
                    (res["rail"] if z == 10 else res["rail_main"]).append(a)
                elif z == 10:
                    res["roads"][kind].append(a)
            if i % 200 == 0:
                print(i, round(time.time() - t0), file=sys.stderr)
    res["failed"] = failed
    pickle.dump(res, gzip.open(OUT, "wb"))
    print({k: len(v) for k, v in res["roads"].items()}, len(res["rail"]), len(res["rail_main"]), "failed", failed)


if __name__ == "__main__":
    main()
