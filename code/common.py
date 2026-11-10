"""Shared paths, constants and helpers for the day-from-london study ("A day from London").

Inputs (read in place, never modified):
  RAIL1851/1851EngWalesScotRail_Lines.shp  1851 England, Wales and Scotland Rail Lines (Satchell, Wrigley, Shaw-Taylor,
                         You and Marti-Henneberg 2023; UK Data Service ReShare SN 852991; CC BY 4.0). Every line open
                         for passengers and/or freight in 1851, British National Grid.
  OpenFreeMap vector tiles (OpenMapTiles schema, OpenStreetMap data, ODbL), zoom 10 and 8, read live by 01_networks.py:
                         today's motorway, trunk, primary and secondary roads and railway lines in Great Britain.
  BEECH/closed_stations.csv, open_stations.csv  Closed and open GB stations with closing years and points
                         (Hotham 2026, The Beeching cuts, from Wikipedia lists and Wikidata).
  GEO/lad23_bgc.geojson  ONS local authority districts (December 2023, generalised clipped), for the GB land mask.
  SETTLE (uk_settlements.tsv)  Wikidata UK settlements with population (CC0), for town markers.
  code/journeys.csv      Documented journey times from London (hand-entered from cited sources; see the source column).
  code/speeds.csv        The speed model (every speed with its source).
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(ROOT, "code")
RAIL1851 = os.environ.get("DL_RAIL1851", "/home/claude/newdata/raw_new13/day_from_london/1. 1851 England, Wales and Scotland rail lines")
BEECH = os.environ.get("DL_BEECH", "/home/claude/src6/beeching-cuts/data")
GEO = os.environ.get("DL_GEO", "/home/claude/newdata/raw/geo")
SETTLE = os.environ.get("DL_SETTLE", "/home/claude/newdata/raw_new8/uk_settlements.tsv")
FONTS = os.environ.get("DL_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("DL_SCRATCH", "/home/claude/scratch/day-from-london")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "day-from-london"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"

ERAS = ["1750", "1830", "1850", "1910", "today"]
ERA_LABEL = {"1750": "1750", "1830": "1830s", "1850": "1850", "1910": "1910", "today": "Today"}
ORIGIN = (51.5074, -0.1276)       # Charing Cross, the traditional centre of London for road distances
BUDGET_H = 12.0                   # hours of travel in "a day"
CELL = 2000                       # grid cell, metres (British National Grid)
X0, X1, Y0, Y1 = 0, 660000, 0, 1220000   # BNG extent of the grid (Great Britain incl. Shetland)
MI = 1.609344


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "x1": return f"{float(v):.1f} times"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "hm":
        h = float(v); hh = int(h); mm = int(round((h - hh) * 60))
        if mm == 60: hh, mm = hh + 1, 0
        return f"{hh} h {mm:02d} min" if hh else f"{mm} min"
    raise ValueError(f)


_T = None


def bng():
    """Transformers WGS84 <-> British National Grid."""
    global _T
    if _T is None:
        from pyproj import Transformer
        _T = (Transformer.from_crs(4326, 27700, always_xy=True), Transformer.from_crs(27700, 4326, always_xy=True))
    return _T
