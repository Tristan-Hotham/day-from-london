"""Step 9: index.html from code/page_template.html, code/page_essay.html and code/page.css, filled from data/results.json,
with the full-screen snippet. 10.5281/zenodo.24105505, https://doi.org/10.5281/zenodo.24105505 and https://blog.tristanhotham.com/2026/10/31/day-from-london/ are left for the publisher to fill."""
from common import *

R = jload(f"{DATA}/results.json")
EXTRA = jload(f"{SCR}/text_extra.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(CODE, "page_template.html"), encoding="utf-8").read()
t = t.replace("{{ESSAY}}", open(os.path.join(CODE, "page_essay.html"), encoding="utf-8").read())
t = t.replace("{{CSS}}", open(os.path.join(CODE, "page.css"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(CODE, "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a")


def fill(m):
    k, f = m.group(1), m.group(3)
    if k in KEEP: return m.group(0)
    if k in EXTRA: return fmt(EXTRA[k], f) if f else str(EXTRA[k])
    return fmt(get(R, k), f)


t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", fill, t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
S = jload(f"{DATA}/site.json")
names = {x["n"] for x in S["towns"]}
for g in re.findall(r'data-go="([^"]+)"', t):
    assert g.split("|")[0] in names, g
assert t.rstrip().endswith("</html>") and 'site-nav.js" defer></script>\n</body>' in t
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
