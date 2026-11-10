"""Step 10: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24105505, https://doi.org/10.5281/zenodo.24105505 and https://blog.tristanhotham.com/2026/10/31/day-from-london/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Day_from_London"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
EXTRA = jload(f"{SCR}/text_extra.json")      # derived phrases written by 08_paper.py (from results.json)
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()


def fill(m):
    k, f = m.group(1), m.group(3)
    if k in KEEP: return m.group(0)
    if k in EXTRA: return fmt(EXTRA[k], f) if f else str(EXTRA[k])
    return fmt(get(R, k), f)


post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", fill, post)
post = re.sub(r"\{\{IMG\|[^}]*\}\}", lambda m: re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", fill, m.group(0)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP, set(re.findall(r"\{\{([^|}]+)\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
A = R["A"]
meta = {"title": "A day from London",
        "slug": "day-from-london",
        "excerpt": f"Leave Charing Cross at dawn and travel for twelve hours. In 1750 that reached {A['1750']['share']:.0f}% of Great Britain; in the 1830s {A['1830']['share']:.0f}%; by rail in 1850 at least {A['1850']['share']:.0f}%; in 1910 at least {A['1910']['share']:.0f}%; today {A['today']['share']:.0f}%. I rebuilt five eras of roads and railways to map the edge of the day.",
        "seo_description": f"How much of Great Britain could you reach in a day from London? {A['1750']['share']:.0f}% in 1750, {A['today']['share']:.0f}% today. Roads and railways of five eras.",
        "tags": ["maps", "data visualisation", "transport history", "stagecoaches", "turnpikes", "railways", "London", "history"],
        "header_alt": "Title card on cream paper reading 'A day from London' beside two maps of Great Britain coloured by hours of travel from London, a small patch around London in 1750 and almost the whole island today."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc",)) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"").replace("km^2", "km²").replace("\\,", " ").replace("\\citep{", "(").replace("\\citet{", "(")
ab = re.sub(r"\\[a-z]+\{([^}]*)\}", r"\1", ab)
zmeta = {"title": "A Day from London: One-Day Travel Reach across Great Britain in 1750, the 1830s, 1850, 1910 and Today, from a Calibrated Historical Network Model",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/day-from-london/}}.</p><p>Sources: turnpike roads and London coach services of 1819 and 1836 (Rosevear, Bogart, Shaw-Taylor and Satchell, openICPSR 195126 and 195128; derived results only); 1851 England, Wales and Scotland rail lines (Satchell et al., UK Data Service ReShare SN 852991, CC BY 4.0); OpenStreetMap contributors via OpenFreeMap (ODbL); train speeds from Leunig (2006). Text, figures and derived data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["time-space convergence", "accessibility", "turnpike roads", "stagecoaches", "railways", "historical GIS", "Great Britain", "London"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.3886/E195126", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "10.3886/E195128V2", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "10.5255/UKDA-SN-852991", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
