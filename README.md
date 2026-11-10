# A day from London

How far could you get from London in one day? A transparent network model of Great Britain's roads and railways in 1750, the 1830s, 1850, 1910 and today, on a 2 km grid, with coach and train speeds calibrated on cited timetables and journey times, or taken from published estimates, and tested on journeys the model did not see. A traveller leaves Charing Cross at dawn and travels for twelve hours. A data study by Dr Tristan Hotham (Independent researcher). The analysis was pre-specified in a written plan before any travel time was computed (NOTES.md). The 1750 map is a rough sketch and the 1850 and 1910 areas are lower bounds (see the caveats below).

Interactive page: https://maps.tristanhotham.com/day-from-london/
Paper: https://doi.org/10.5281/zenodo.24105505
Blog post: https://blog.tristanhotham.com/2026/10/31/day-from-london/
Code and data: https://github.com/Tristan-Hotham/day-from-london

## Headline results

| Era | Land within 12 hours (km²) | Share of Great Britain | Range (speeds plus or minus model error) | Modelled hours to Edinburgh |
|---|---|---|---|---|
| 1750 | 11,144 | 5% | 4% to 7% | 108.9 |
| 1830s | 43,440 | 19% | 17% to 21% | 44.4 |
| 1850 | 107,216 | 47% | 33% to 61% | 17.6 |
| 1910 | 165,432 | 72% | 62% to 80% | 10.7 |
| Today | 222,292 | 97% | 97% to 97% | 3.6 |

- The area within a day of London grew 20-fold between 1750 and today, and 2.5-fold between the 1830s and 1850 alone.
- Coach speeds fitted to timetables: 8.4 mph on turnpikes in the 1830s (fastest service to each of 136 termini in 1836; leave-one-out median absolute error 9%), 6.8 mph in 1819 (147 termini), 3.6 mph in 1750 (12 cited journeys to 9 towns, counting a day as 12 travelling hours; error 28%).
- Out of sample: the 1836-fitted model reproduces the 1837 mail-coach timetable to a median 12% (27 mails). Trains run at Leunig's (2006) average speeds, so the model is slower than the documented fastest expresses (median gap 46% in 1850, 34% in 1910).
- Weakest parts: 1750 (few cited journeys; its leave-one-out error of 28% fails the 25% threshold set in advance, so the 1750 map is a rough sketch), the railway eras (average trains, checked on only 4 and 6 documented journeys, so the 1850 and 1910 areas are lower bounds), the 1910 network (lines that have closed are inferred as straight links between closed stations), and the lack of timetables everywhere.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; hour bands for each era as image overlays, 12-hour line and its uncertainty, era buttons and play, towns, documented journeys, tap anywhere for hours in every era, search, layers, full screen. |
| `img/hours_*.png`, `img/roads_*.png` | Page overlays: hour bands by era; a low resolution drawing of the 1750 and 1830 roads (derived). |
| `header.png` | Social card, 1200 x 630. |
| `data/isochrone_areas.csv` | Land within 6, 12 and 24 hours by era, with the uncertainty range. |
| `data/towns_hours.csv` | Modelled hours from Charing Cross to 65 towns in each era. |
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
3. `model.py`, `03_model_runs.py`: one directed graph per era (walking between cells at 4.8 km/h, coaches, trains, 30-minute waits for trains and feeder coaches), Dijkstra from Charing Cross; coach speeds fitted to the 1836 and 1819 timetables and the 1750 journeys, today's train speed to 12 fastest times, all validated leaving one destination out; 1850 and 1910 train speeds from Leunig (2006) converted to track speeds by each network's circuity (1.15 and 1.05); uncertainty bands and 12 sensitivity runs.
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

Hotham, T. (2026) A day from London: one-day travel reach across Great Britain in 1750, the 1830s, 1850, 1910 and today, from a calibrated historical network model. Zenodo. https://doi.org/10.5281/zenodo.24105505

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
