# day-from-london: working notes

Brief: /home/claude/work/new13/BRIEFS.md section H (+ shared rules new12, new11, new10, new9, new8, house brief
/home/claude/newdata/BRIEF.md, GIF brief /home/claude/gifs/BRIEF.md). Format refs: fame-half-life, byelection-attention.
Scratch: /home/claude/scratch/day-from-london (delete at the end, by exact path).

## Inputs (raw, read only, never modified or redistributed)
- 1851 England, Wales and Scotland Rail Lines (Satchell, Wrigley, Shaw-Taylor, You, Marti-Henneberg 2023; ReShare SN 852991,
  doi:10.5255/UKDA-SN-852991; CC BY 4.0). 1,431 polylines, 6,336 miles.
- Turnpike roads of England and Wales 1700 to 1838 ("turnpikes and main 2026" shapefile, openICPSR 195126 V2.1;
  Rosevear, Bogart, Shaw-Taylor, Satchell; doi:10.3886/E195126). 23,556 polylines, England and Wales only. Fields TP_1750 ..
  TP_1850: the year = a turnpike at that date; 0 = a main road but not a turnpike; 9 = not yet made (new line, left out).
- London coaches 1819 and 1836 (openICPSR 195128 V2.0; Rosevear, Bogart, Shaw-Taylor; doi:10.3886/E195128V2). 1,333 service
  routes drawn on the turnpike map; London-start services with a journey time: 358 in 1819 (147 termini, Cary's New
  Itinerary), 283 in 1836 (136 termini, Bates 1969 Directory of Stage Coach Services 1836).
- OpenFreeMap vector tiles (OSM, ODbL): today's motorway, trunk, primary, secondary roads and rail (z10), and the rail lines
  shown at z8 (used to mark main lines). Fetched by code/01_networks.py, cached in scratch.
- src6/beeching-cuts closed_stations.csv and open_stations.csv (station points; closing years; Wikidata opening years).
- Documented journey times typed from cited sources into code/journeys.csv (Harper 1903 vol 2 for the 1837 mail list;
  Smiles; Harper road books; Bogart 2005; others as found, each row with its source).
Licences: openICPSR deposits carry no stated licence on the project pages (to check the terms page); release derived results
only (travel-time grids, isochrones, fitted speeds), never the raw shapefiles.

## Analysis plan (written 2026-11-10 08:51 UTC, before any travel time was computed or compared with a documented time)

Question: leaving Charing Cross at dawn, how much of Great Britain could a traveller reach within one day's travel in 1750,
the 1830s, 1850, 1910 and today, and how well does a simple, transparent network model reproduce documented journey times?

Day: 12 hours of travel (dawn departure; about the length of daylight at the equinox; a long coaching day). Sensitivity 8 and
16 hours. The full travel-time surface is kept (to 250 hours) so towns beyond the day also get hours.

Space: 2 km grid on the British National Grid, Great Britain land only (ONS LAD 2023 clipped boundaries, Northern Ireland
dropped). Islands without a mapped ferry or bridge are unreachable by land and are reported as such.

Graph (one per era), shortest paths by Dijkstra from the grid cell holding Charing Cross:
- Walking layer: every land cell joined to its 8 neighbours at 4.8 km/h (3 mph), all eras before today. Today: 30 km/h
  (driving on minor roads) between cells.
- Road layer, coach eras (1750, 1830s): the turnpike map. A section is a turnpike in the era if TP_1750 = 1750 (TP_1830 = 1830
  for the 1830s); other existing main roads (code 0) run at r = 0.6 of the turnpike speed; code 9 (not yet built) left out.
  Ferries in the map are kept as roads plus a 30 minute wait. Scotland has no turnpike map: OSM trunk and primary roads
  are used as a proxy for its main roads (non-turnpike speed in 1750, turnpike speed in the 1830s). Said plainly.
- Road layer, 1850 and 1910: the 1838 turnpike map (TP_1838 = 1838 at the turnpike speed, other main roads at r) at the
  1830s coach speeds, as feeder coaches and carriers; boarding a coach anywhere costs a 30 minute wait. Scotland as above.
- Road layer, today: OSM motorway, trunk, primary, secondary at fixed typical speeds 100, 80, 60, 45 km/h (to be sourced
  from DfT published average speeds, cited); no calibration.
- Rail layer: 1850 = the 1851 lines. 1910 = today's OSM rail + the 1851 lines + inferred lines for stations that closed after
  1910 and lie more than 2 km from those lines (minimum spanning tree among such stations plus the shortest link to the
  network, links at most 15 km; drawn dashed and flagged as inferred). Today = OSM rail. A rail section is "main" if within
  250 m of a line shown at z8 (today's main lines), else "branch" at 0.5 of the main speed. Boarding: at any rail vertex
  within 1.5 km of a station known to be open in the era (1850: Wikidata opening year <= 1850, plus closed stations within
  500 m of an 1851 line; 1910: open stations opened by 1910, plus closed stations closed after 1910; today: open
  stations); a 30 minute wait on boarding, alighting free.

Speeds and calibration (one free parameter per era, everything else fixed above):
- 1830s: turnpike coach speed v_T fitted to the fastest scheduled 1836 time per terminus in the London coaches file
  (Bates 1836; geometry end point = terminus), minimising the sum of squared log errors (model/documented).
- 1750: v_T fitted to the cited c.1740 to 1765 London journeys in code/journeys.csv; journeys given in days are converted at
  12 travelling hours per day (one coaching day = the 12 hour budget; sensitivity 10 and 14 hours).
- 1850, 1910, today: rail main-line speed fitted to cited fastest documented journey times from London in that era.
- Check of the speed trajectory: the same fit on the 1819 Cary times (TP_1820 network); fitted speeds 1750, 1819, 1836
  compared with Bogart's (2005) decade averages and Gerhold's (2014) 8.7 mph (journeys of 80 miles and more, 1830s).

Validation (main error measure): leave one destination out (refit without it, predict it) for each era; report N, median
absolute percentage error, mean log error (bias) and the share within 20%. Out-of-sample checks: the 1837 mail-coach list
(Harper 1903) against the 1836-calibrated model; documented London to Edinburgh (and York, Bristol, Manchester where cited)
in each era.

Headline outputs: land area of GB within 12 hours each era (km2 and share); farthest reach; hours to 60 large towns per era;
London to Edinburgh modelled vs documented by era; Janelle's convergence rate (minutes saved per year) London to Edinburgh
from documented times.

Sensitivity (pre-set): budget 8 and 16 h; r = 0.4, 0.8, 1.0; waits 0 and 60 min; walking 4 and 6 km/h; branch ratio 0.35
and 0.7; grid 4 km; hours per coaching day 10 and 14 (1750); 1910 without inferred lines.

Uncertainty on the map: each era's 12 hour line drawn again with speeds scaled by plus and minus the LOO median absolute
error, as a soft band.

What would count against the model: LOO median absolute error above 25% in an era, or systematic bias (mean log error
beyond plus or minus 0.1) with distance; reported as found.

## Log
- 2026-11-10 09:28 UTC, before any calibration or validation was run (only smoke tests of the code at arbitrary speeds):
  deviation from the plan for rail speeds in 1850 and 1910. Fewer than ten cited fastest London journey times per rail era
  could be found online (Leunig's UKDS timetable sets SN 5234 and SN 6384 need a login), too few to fit a speed. So the main
  model uses Leunig's (2006 working paper, Table 6) published average in-train speeds, crow-flies mph: important routes 22.7 (1850), 36.9
  (1910); minor routes 17.8 and 20.4. Converted to speeds along the track by the median rail circuity (network km over
  straight-line km) from London to the 30 largest towns of England and Wales on each era's network; branch lines at
  minor/important (0.78 in 1850, 0.55 in 1910) instead of the fixed 0.5. Waiting: the 30 minute boarding wait.
  The documented fastest times are then an out-of-sample check (the model represents an average train, so it should be
  slower than the fastest; reported). Sensitivity: rail speed fitted to the documented fastest times ("fastest train").
  Today's rail main speed: fitted to 12 fastest times from London quoted by Visit London (LOO as planned). Today's roads:
  fixed speeds as planned (DfT 2024 free-flow car speeds 68 mph motorway, 51 mph rural single carriageway, as upper bounds).
  1750 calibration set: 12 cited journeys to 9 towns (Smiles 1867; Harper 1901 to 1903 road books; Bogart 2005; Gerhold as
  cited by the Great North Road site): the 30 to 60 hoped for could not be found; reported as a limitation.

## Results (first full run of the plan; all numbers in data/results.json)
- Fitted coach speeds: 1830s 13.5 km/h (8.4 mph; 136 termini of 1836, LOO MdAPE 9.1%, 92% within 20%); 1819 11.0 km/h
  (6.8 mph; 147 termini, LOO 12.6%); 1750 5.75 km/h (3.6 mph over 12 h days; 12 journeys, LOO 27.9%: ABOVE the 25% threshold
  set in the plan, reported as evidence against the 1750 model; read the 1750 map as a sketch).
- Out of sample: 1837 mail list 27 destinations, MdAPE 11.6%, bias +0.08. Rail (Leunig speeds x circuity 1.15 / 1.05 =
  42.1 / 62.6 km/h main): slower than documented fastest trains by a median 46% (1850, n=4) and 34% (1910, n=6), as expected
  for average trains; fastest-train fit 65 / 90 km/h kept as sensitivity. Today rail fitted 210 km/h (absorbs walk + wait),
  LOO 5.0%.
- Land within 12 h: 1750 11,144 km2 (4.8%), 1830s 43,440 (18.9%), 1850 107,216 (46.6%), 1910 165,432 (71.9%), today
  222,292 (96.6%; only islands beyond). Ratios: 1830s/1750 3.9, 1850/1830s 2.5, today/1750 19.9.
- Edinburgh modelled: 109, 44, 17.6, 10.7, 3.6 h. Ordering of eras unchanged in every sensitivity run.
- Data still worth getting: Leunig's UKDS timetable sets (SN 5234, SN 6384) to fit and test rail speeds; the full CAMPOP
  1807 to 1994 rail lines for 1910; more dated 1740s to 1760s coach advertisements.
- Scratch /home/claude/scratch/day-from-london deleted at the end (03_model_runs.py regenerates runs.npz in about 30 to 60 min).
