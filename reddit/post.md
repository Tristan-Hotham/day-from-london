**Title:** [OC] How much of Great Britain could you reach in one day from London? 5% in 1750, 19% in the 1830s, at least 47% by train in 1850, 97% today

**Body:**

I rebuilt the roads and railways of five eras on a 2 km grid and sent a traveller out of Charing Cross at dawn for 12 hours.

- 1750, stage coach on the turnpikes: 11,144 km² (5% of GB). Edinburgh: about 9 travelling days.
- 1830s, coaches at about 8.4 mph (fitted to 136 timetabled 1836 services): 19%.
- 1850, the first railways: at least 47%. 1910: at least 72%. Today, car or train: 97%.
- Checked against documented journeys the model did not see: 1837 mail coaches within a median 12%.
- Caveats: 1750 is a rough sketch (median error 28%, above the 25% limit I set in advance). The 1850 and 1910 figures are lower bounds: the model uses average trains and is 46% and 34% slower than documented expresses, checked on only 4 and 6 journeys.

Interactive map with an era slider (tap anywhere for the hours in every era): https://maps.tristanhotham.com/day-from-london/

**Source comment:**

Data: turnpike roads and London coach timetables 1819 and 1836 (Rosevear, Bogart, Shaw-Taylor, Satchell, openICPSR); 1851 rail lines (Cambridge Group, CC BY 4.0); OpenStreetMap via OpenFreeMap (ODbL); train speeds from Leunig (2006); journey times from Harper's road books and other cited sources. Method: shortest paths on a multimodal grid (Dijkstra), coach speeds fitted to timetables, leave-one-out validation. Tools: Python (numpy, scipy, geopandas, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/day-from-london
