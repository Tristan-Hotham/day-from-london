"""Step 11: README.md, LICENSE, reddit/post.md and release/paper/cover_note.md from data/results.json.
10.5281/zenodo.24105505, https://doi.org/10.5281/zenodo.24105505 and https://blog.tristanhotham.com/2026/10/31/day-from-london/ are left for the publisher to fill."""
from common import *

R = jload(f"{DATA}/results.json")
A, F, V, S = R["A"], R["fits"], R["valid"], R["speeds"]
L = R["era_label"]
E = R["edinburgh_model"]
area_rows = "\n".join(f"| {L[e]} | {A[e]['km2']:,.0f} | {A[e]['share']:.0f}% | {A[e]['share_lo']:.0f}% to {A[e]['share_hi']:.0f}% | {E[e]:.1f} |" for e in ERAS)
readme = f"""# A day from London

How far could you get from London in one day? A transparent network model of Great Britain's roads and railways in 1750, the 1830s, 1850, 1910 and today, on a 2 km grid, with coach and train speeds calibrated on cited timetables and journey times, or taken from published estimates, and tested on journeys the model did not see. A traveller leaves Charing Cross at dawn and travels for twelve hours. A data study by Dr Tristan Hotham (Independent researcher). The analysis was pre-specified in a written plan before any travel time was computed (NOTES.md). The 1750 map is a rough sketch and the 1850 and 1910 areas are lower bounds (see the caveats below).

Interactive page: https://maps.tristanhotham.com/{SLUG}/
Paper: {{https://doi.org/10.5281/zenodo.24105505}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/day-from-london/}}
Code and data: {REPO}

## Headline results

| Era | Land within 12 hours (km²) | Share of Great Britain | Range (speeds plus or minus model error) | Modelled hours to Edinburgh |
|---|---|---|---|---|
{area_rows}

- The area within a day of London grew {R['ratio']['today_1750']:.0f}-fold between 1750 and today, and {R['ratio']['1850_1830']:.1f}-fold between the 1830s and 1850 alone.
- Coach speeds fitted to timetables: {R['mph']['1830']:.1f} mph on turnpikes in the 1830s (fastest service to each of {R['coach']['n_termini_1836']} termini in 1836; leave-one-out median absolute error {F['1830']['loo']['mdape']:.0f}%), {R['mph']['1819']:.1f} mph in 1819 ({R['coach']['n_termini_1819']} termini), {R['mph']['1750']:.1f} mph in 1750 (12 cited journeys to 9 towns, counting a day as 12 travelling hours; error {F['1750']['loo']['mdape']:.0f}%).
- Out of sample: the 1836-fitted model reproduces the 1837 mail-coach timetable to a median {V['1830_mail1837']['mdape']:.0f}% ({V['1830_mail1837']['n']} mails). Trains run at Leunig's (2006) average speeds, so the model is slower than the documented fastest expresses (median gap {V['1850_all']['mdape']:.0f}% in 1850, {V['1910_all']['mdape']:.0f}% in 1910).
- Weakest parts: 1750 (few cited journeys; its leave-one-out error of {F['1750']['loo']['mdape']:.0f}% fails the 25% threshold set in advance, so the 1750 map is a rough sketch), the railway eras (average trains, checked on only {V['1850_all']['n']} and {V['1910_all']['n']} documented journeys, so the 1850 and 1910 areas are lower bounds), the 1910 network (lines that have closed are inferred as straight links between closed stations), and the lack of timetables everywhere.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; hour bands for each era as image overlays, 12-hour line and its uncertainty, era buttons and play, towns, documented journeys, tap anywhere for hours in every era, search, layers, full screen. |
| `img/hours_*.png`, `img/roads_*.png` | Page overlays: hour bands by era; a low resolution drawing of the 1750 and 1830 roads (derived). |
| `header.png` | Social card, 1200 x 630. |
| `data/isochrone_areas.csv` | Land within 6, 12 and 24 hours by era, with the uncertainty range. |
| `data/towns_hours.csv` | Modelled hours from Charing Cross to {R['towns_n']} towns in each era. |
| `data/journeys_model.csv` | Every documented journey time used, with its source, the modelled time (and the leave-one-out time where fitted) and the error. |
| `data/coach_services.csv` | The fastest timed London coach service to each terminus in 1819 and 1836 (derived from Rosevear et al.), with modelled times. |
| `data/lookup.png`, `data/site.json` | Page data: hours on a lon/lat grid for every era (value = 2 x hours; 252 = beyond 250 hours; 255 = sea), towns, 12-hour lines, 1851 rail lines, inferred 1910 lines. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts in order, the model (`model.py`), `journeys.csv` (documented times with sources), templates. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the post text and a looping GIF. |

## Method in brief

1. `01_networks.py`: today's roads (motorway to secondary) and railways from OpenFreeMap vector tiles (zoom 10; zoom 8 rail marks main lines).
2. `02_networks_build.py`: the 2 km land grid (ONS local authorities, Great Britain), the turnpike map with each section's turnpike status in 1750, 1820, 1830 and 1838, the 1851 rail lines, stations by era, and the inferred lines of 1910 (stations closed after 1910 more than 2 km from the 1851 or today's lines, joined by a minimum spanning tree with links up to 15 km).
3. `model.py`, `03_model_runs.py`: one directed graph per era (walking between cells at 4.8 km/h, coaches, trains, 30-minute waits for trains and feeder coaches), Dijkstra from Charing Cross; coach speeds fitted to the 1836 and 1819 timetables and the 1750 journeys, today's train speed to 12 fastest times, all validated leaving one destination out; 1850 and 1910 train speeds from Leunig (2006) converted to track speeds by each network's circuity ({S['1850']['circuity']:.2f} and {S['1910']['circuity']:.2f}); uncertainty bands and {len([k for k in R['sens'] if not k.startswith('budget') and k != 'day_hours'])} sensitivity runs.
4. `04_results.py` to `11_readme.py`: results, figures, page data and page, header, paper, release files and this README.

## Sources and licences

- Rosevear, A., Bogart, D., Shaw-Taylor, L. and Satchell, M. (2023) Turnpike road map for England and Wales 1700 to 1838, openICPSR project 195126 (version V2.1), doi:10.3886/E195126. Rosevear, A., Bogart, D. and Shaw-Taylor, L. (2023) Stagecoach services in England and Wales 1819 and 1836, openICPSR, doi:10.3886/E195128V2. No licence is stated on the project pages, so these files are not redistributed here; only derived results are.
- Satchell, M., Wrigley, E. A., Shaw-Taylor, L. M. W., You, X. and Henneberg, J. (2023) 1851 England, Wales and Scotland Rail Lines, UK Data Service ReShare, doi:10.5255/UKDA-SN-852991, CC BY 4.0.
- OpenStreetMap contributors, via OpenFreeMap vector tiles (ODbL). ONS local authority boundaries (Open Government Licence v3.0). Stations from Did Beeching Kill Your Town? (Hotham 2026; Wikipedia lists CC BY-SA 4.0, Wikidata CC0). Town points from Natural Earth (public domain).
- Leunig, T. (2006) Time is money, Journal of Economic History 66(3), 635 to 673, for train speeds. Documented journey times from Harper (1899, 1902, 1903, 1922), Smiles (1867), Sidney (1851), Bogart (2005), Wikipedia (CC BY-SA 4.0) and Visit London, as listed in `data/journeys_model.csv`.
- This repository: code MIT; text, figures and derived data CC BY 4.0, except data derived from OpenStreetMap (ODbL).

## How to rerun

Python 3 with numpy, pandas, geopandas, scipy, shapely, pyproj, rasterio, matplotlib, Pillow and mapbox-vector-tile; xelatex for the paper. Put the raw files where `code/common.py` and `code/02_networks_build.py` expect them (or set the DL_* environment variables), then run `code/01_networks.py` to `code/11_readme.py` in order and `reddit/collage.py`. `03_model_runs.py` takes about an hour on two cores. The paper's DOI line is filled from the environment: `DOI=10.5281/zenodo.N python3 code/08_paper.py`.

## Citation

Hotham, T. (2026) A day from London: one-day travel reach across Great Britain in 1750, the 1830s, 1850, 1910 and today, from a calibrated historical network model. Zenodo. {{https://doi.org/10.5281/zenodo.24105505}}

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS", "pre-registered"):
    assert bad not in re.sub(r"^\|[-|]+\|$", "", readme, flags=re.M), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/byelection-attention/LICENSE", encoding="utf-8").read().split("Text, figures")[0]
lic += ("Text, figures and the paper: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/\n"
        "Derived data (data/): CC BY 4.0, except data derived from OpenStreetMap (the 1910 and today travel times use OSM roads and railways; "
        "OSM-derived content is under the Open Database License, https://opendatacommons.org/licenses/odbl/). The 1851 rail lines are CC BY 4.0 "
        "(Satchell et al. 2023). The turnpike road map and London coach services (Rosevear et al., openICPSR) are not redistributed; "
        "derived travel times and fitted speeds only.\n")
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""**Title:** [OC] How much of Great Britain could you reach in one day from London? {A['1750']['share']:.0f}% in 1750, {A['1830']['share']:.0f}% in the 1830s, at least {A['1850']['share']:.0f}% by train in 1850, {A['today']['share']:.0f}% today

**Body:**

I rebuilt the roads and railways of five eras on a 2 km grid and sent a traveller out of Charing Cross at dawn for 12 hours.

- 1750, stage coach on the turnpikes: {A['1750']['km2']:,.0f} km² ({A['1750']['share']:.0f}% of GB). Edinburgh: about {E['1750'] / 12:.0f} travelling days.
- 1830s, coaches at about {R['mph']['1830']:.1f} mph (fitted to {R['coach']['n_termini_1836']} timetabled 1836 services): {A['1830']['share']:.0f}%.
- 1850, the first railways: at least {A['1850']['share']:.0f}%. 1910: at least {A['1910']['share']:.0f}%. Today, car or train: {A['today']['share']:.0f}%.
- Checked against documented journeys the model did not see: 1837 mail coaches within a median {V['1830_mail1837']['mdape']:.0f}%.
- Caveats: 1750 is a rough sketch (median error {F['1750']['loo']['mdape']:.0f}%, above the 25% limit I set in advance). The 1850 and 1910 figures are lower bounds: the model uses average trains and is {V['1850_all']['mdape']:.0f}% and {V['1910_all']['mdape']:.0f}% slower than documented expresses, checked on only {V['1850_all']['n']} and {V['1910_all']['n']} journeys.

Interactive map with an era slider (tap anywhere for the hours in every era): https://maps.tristanhotham.com/{SLUG}/

**Source comment:**

Data: turnpike roads and London coach timetables 1819 and 1836 (Rosevear, Bogart, Shaw-Taylor, Satchell, openICPSR); 1851 rail lines (Cambridge Group, CC BY 4.0); OpenStreetMap via OpenFreeMap (ODbL); train speeds from Leunig (2006); journey times from Harper's road books and other cited sources. Method: shortest paths on a multimodal grid (Dijkstra), coach speeds fitted to timetables, leave-one-out validation. Tools: Python (numpy, scipy, geopandas, matplotlib), MapLibre. Paper and code: {REPO}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
cover = f"""# Cover note: A Day from London

## Suggested journals (no author fee on the standard subscription route)

All three are hybrid journals: publishing on the standard subscription route costs the author nothing, and open access is optional and paid (an APC applies only if that option is chosen). Do not tick the open access option.

1. **Journal of Historical Geography** (Elsevier). Historical GIS and the geography of transport are within scope. Word limit (checked on the Guide for Authors, November 2026): standard articles should generally not exceed 10,000 words including references and the abstract; tables, maps and figures do not count; the abstract must be under 200 words. This version fits the length; the abstract (about 250 words) must be cut below 200 for submission. No submission fee is mentioned.
2. **The Journal of Transport History** (Sage). Publishes peer-reviewed work on all aspects of transport pasts. Word limit not confirmed: the Sage author-instructions page could not be loaded during the check (November 2026); an earlier check of the journal's calls for papers gave 8,000 words including notes, which would mean moving the appendix and some robustness detail to supplementary material. Confirm the limit and the fee position on the author page before submitting.
3. **Journal of Transport Geography** (Elsevier). Suits the accessibility and time-space convergence framing. Word limit not confirmed (the Guide for Authors could not be reached during the check); confirm before submitting.

Length of this version: about {{WORDS}} words before references, {{FIGS}} figures and {{TABS}} tables.

## Summary of the contribution

How much of Great Britain lay within a day of London, and how did that change from the coaching era to today? This paper builds one transparent network model on a 2 km grid for five dates, using the Cambridge Group's historical GIS of turnpike roads and of the 1851 railways, a reconstruction of the 1910 network and OpenStreetMap. Coach speeds are fitted to {R['coach']['n_termini_1836']} timetabled London services of 1836 and to cited journeys of the 1740s to 1760s; train speeds come from Leunig's published averages; every era is validated on journeys it did not see. Twelve hours from Charing Cross reached {A['1750']['share']:.0f}% of the land in 1750 (a rough sketch: the 1750 model misses its documented journeys by more than the limit set in advance), {A['1830']['share']:.0f}% in the 1830s, at least {A['1850']['share']:.0f}% in 1850, at least {A['1910']['share']:.0f}% in 1910 (lower bounds, since the trains are average trains) and {A['today']['share']:.0f}% today. The paper turns point-to-point histories of time-space convergence into tested national surfaces and releases them for reuse.
"""
PS = jload(f"{SCR}/paper_stats.json")
cover = cover.replace("{WORDS}", f"{round(PS['words'], -2):,}").replace("{FIGS}", str(PS["figs"])).replace("{TABS}", str(PS["tabs"]))
open(os.path.join(REL, "paper", "cover_note.md"), "w", encoding="utf-8").write(cover)
print("README, LICENSE, post.md, cover_note written")
