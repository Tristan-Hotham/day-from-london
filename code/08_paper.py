"""Step 8: the paper. Fills code/paper_template.tex with code/paper_body.tex, the results paragraphs and tables written here
from data/results.json, the bibliography code/paper_bib.tex, and compiles with xelatex. Output:
release/paper/Hotham_Day_from_London.pdf and .tex beside the f_*.pdf figures. The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24105505
printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/08_paper.py
Also writes SCR/text_extra.json (derived phrases shared with the blog and page)."""
import subprocess
import numpy as np, pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
J = pd.read_csv(f"{DATA}/journeys_model.csv")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Day_from_London"
A, F, V, S, L, T = R["A"], R["fits"], R["valid"], R["speeds"], R["era_label"], R["towns"]
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
N = lambda v, d=0: (f"{v:,.{d}f}").replace("-", "$-$")
pc = lambda v: f"{v:.0f}\\%"
M = jload(f"{SCR}/model_runs.json")
import pickle
NET = pickle.load(gzip.open(os.path.join(SCR, "net.pkl"), "rb"))
R_INF_KM = sum(float(np.hypot(*(a[1] - a[0]))) for a, _ in NET["rail_inf"]) / 1000


def far_phrase(e):
    f = R["farthest_town"][e]
    return f"{f['town'].replace(' upon Tyne', '')}, {f['km']:.0f} km away, in {f['hours']:.1f} hours" if f else "no large town beyond the London area"


EXTRA = {
    "DAYKM": F["1750"]["speed_kmh"] * BUDGET_H,
    "EDDAYS1750": R["edinburgh_model"]["1750"] / 12,
    "FAR_1750": far_phrase("1750"), "FAR_1830": far_phrase("1830"), "FAR_1850": far_phrase("1850"), "FAR_1910": far_phrase("1910"),
}
r1850 = R["ratio"]["1850_1830"]
EXTRA["RATIO_1850_TXT"] = "doubled" if r1850 < 2.5 else ("tripled" if r1850 < 3.5 else f"multiplied by {r1850:.0f}")
jsave(EXTRA, f"{SCR}/text_extra.json")

# ---------------------------------------------------------------- results paragraphs
v = {e: F[e] for e in ("1750", "1830", "1819")}
RES_SPEEDS = (
    f"Table~\\ref{{tab:speeds}} lists every speed in the model and Figure~\\ref{{fig:coach}} shows the coach timetables. Fitted to the fastest scheduled service to each of {R['coach']['n_termini_1836']} termini in 1836, "
    f"the turnpike coach speed is {F['1830']['speed_kmh']:.1f} km/h ({R['mph']['1830']:.1f} mph), with non-turnpike main roads at {0.6 * F['1830']['speed_kmh']:.1f} km/h. "
    f"Fitted in the same way to {R['coach']['n_termini_1819']} termini in 1819, on the turnpikes of 1820, it is {F['1819']['speed_kmh']:.1f} km/h ({R['mph']['1819']:.1f} mph). "
    f"For 1750 the twelve cited journeys give {F['1750']['speed_kmh']:.2f} km/h ({R['mph']['1750']:.1f} mph) of moving time on a turnpike, that is, about "
    f"{F['1750']['speed_kmh'] * 12:.0f} km in a twelve-hour coaching day; counting ten or fourteen travelling hours a day instead gives "
    f"{F['1750']['speed_kmh_day10']:.2f} and {F['1750']['speed_kmh_day14']:.2f} km/h. "
    f"These fitted speeds follow the trajectory in the literature closely. \\citet{{gerhold2014}}, as summarised by \\citet{{alvarez2017}}, gives 8.7 mph for London journeys of 80 miles and more in the 1830s, "
    f"against {R['mph']['1830']:.1f} mph here; \\citet{{bogart2005}} gives average journey speeds of 6.85 mph for the 1810s, against {R['mph']['1819']:.1f} mph here for 1819. "
    f"For the 1750s Bogart's average of 2.61 mph is total distance over total journey time, so it includes time not spent moving; the model's {R['mph']['1750']:.1f} mph over twelve travelling hours "
    f"is equivalent to {R['mph']['1750'] / 2:.1f} mph over 24 hours, which is the same order. The median scheduled speed of all timed 1836 services, {R['coach']['median_mph_1836']:.1f} mph along the mapped route, "
    f"is below the fitted turnpike speed because shorter routes ran slower and because the model's speed applies only to turnpike sections.\n\n"
    f"Rail circuity from London to the largest towns of England and Wales (23 reached in 1850, 30 in 1910) is {S['1850']['circuity']:.2f} on the 1851 network and {S['1910']['circuity']:.2f} on the 1910 network, "
    f"so Leunig's important-route speeds become {S['1850']['main_kmh']:.1f} km/h ({R['mph']['rail1850']:.1f} mph) and {S['1910']['main_kmh']:.1f} km/h ({R['mph']['rail1910']:.1f} mph) along the track. "
    f"Today's main-line speed, fitted to the twelve fastest times from London, is {F['today_rail']['speed_kmh']:.0f} km/h ({R['mph']['railtoday']:.0f} mph). This is not a running speed: in the fit the traveller walks to the station and waits half an hour, and the fitted speed absorbs that overhead, so modelled times from Charing Cross match the stated station-to-station times, and the model slightly understates today's door-to-door rail times.")

def vline(k, lab):
    x = k
    return f"{lab} & {x['n']} & {x['mdape']:.1f} & {x['within20']:.0f} & {x['bias_log']:+.3f}\\\\\n".replace("+-", "-").replace("-0.", "$-$0.")

TV = ("\\begin{table}[tbp]\\centering\\small\\caption{Validation against documented journey times. MdAPE: median absolute percentage error; bias: mean of $\\log$(model/documented). "
      "Fitted eras are validated leaving one destination out (LOO).}\\label{tab:valid}\\begin{tabular}{lrrrr}\\toprule Test & $N$ & MdAPE (\\%) & Within 20\\% (\\%) & Bias\\\\\\midrule\n"
      + vline(F["1750"]["loo"], "1750: cited journeys 1739 to 1764, LOO")
      + vline(F["1830"]["loo"], "1830s: fastest 1836 coach per terminus, LOO")
      + vline(V["1830_mail1837"], "1830s: 1837 mail-coach list, out of sample")
      + vline(F["1819"]["loo"], "1819 check: fastest coach per terminus, LOO")
      + vline(V["1850_all"], "1850: trains 1838 to 1862, out of sample")
      + vline(V["1910_all"], "1910: express trains 1896 to 1904, out of sample")
      + vline(F["today_rail"]["loo"], "Today: fastest trains, LOO")
      + "\\bottomrule\\end{tabular}\\end{table}")

def worst(e, k=3):
    d = J[J.era == e].copy()
    col = "model_loo" if e in ("1750", "today") else "model"
    d["e"] = (d[col] - d.hours) / d.hours * 100
    d = d.reindex(d.e.abs().sort_values(ascending=False).index).head(k)
    return "; ".join(f"{r.town} {int(r.year)} ({r.e:+.0f}\\%)".replace("+-", "-") for r in d.itertuples())

RES_VALID = (
    f"Table~\\ref{{tab:valid}} and Figure~\\ref{{fig:valid}} compare modelled and documented times. The 1830s model fits the 1836 timetables with a leave-one-out median absolute error of "
    f"{F['1830']['loo']['mdape']:.1f}\\% ({F['1830']['loo']['within20']:.0f}\\% of termini within 20\\%) and almost no bias, and it reproduces the separate 1837 list of mail coaches, which it never saw, "
    f"with a median error of {V['1830_mail1837']['mdape']:.1f}\\% ({V['1830_mail1837']['within20']:.0f}\\% within 20\\%). "
    f"The Edinburgh mail of 1837 is modelled at {R['ex']['edinburgh_1837']['model']:.1f} hours against {R['ex']['edinburgh_1837']['doc']:.1f} documented, and the Holyhead mail at "
    f"{R['ex']['holyhead_1837']['model']:.1f} against {R['ex']['holyhead_1837']['doc']:.1f}. The largest 1837 errors are {worst('1830')}.\n\n"
    f"The 1750 model is much weaker: its leave-one-out median absolute error is {F['1750']['loo']['mdape']:.1f}\\% over {F['1750']['loo']['n']} journeys, above the 25\\% that the plan set as evidence against the model. "
    f"The cited journeys disagree with each other as much as with the model: Edinburgh in ten days (1754) and in a fortnight (1763); Birmingham in three days (1749) and in 40 hours (1740). "
    f"The largest errors are {worst('1750')}. By the test set in advance the 1750 model fails, and the 1750 map should be read only as a rough sketch of the order of magnitude, with the uncertainty band in Figure~\\ref{{fig:maps}}.\n\n"
    f"For the railways, where speeds come from Leunig's averages rather than from the documented times, the model is slower than the famous expresses, as expected: "
    f"the median absolute error is {V['1850_all']['mdape']:.0f}\\% for the {V['1850_all']['n']} journeys around 1850 and {V['1910_all']['mdape']:.0f}\\% for the {V['1910_all']['n']} around 1910, with mean log errors of "
    f"{V['1850_all']['bias_log']:+.2f} and {V['1910_all']['bias_log']:+.2f}. Liverpool in 1851 is modelled at {R['ex']['liverpool_1851']['model']:.1f} hours against six by express \\citep{{sidney1851}}; "
    f"Edinburgh around 1901 at {R['ex']['edinburgh_1901']['model']:.1f} hours against 8.25. Fitting the rail speed to these documented fastest trains instead would give "
    f"{F['1850_fastest']['speed_kmh']:.0f} km/h in 1850 and {F['1910_fastest']['speed_kmh']:.0f} km/h in 1910 on main lines; Section~\\ref{{sec:robust}} reports the maps that result. With only four and six documented journeys these checks are thin, but they all point the same way: the 1850 and 1910 areas in this paper are lower bounds for a traveller who could take the fastest train, not precise estimates. "
    f"Today's fitted rail model misses the twelve fastest times by a median {F['today_rail']['loo']['mdape']:.0f}\\% when each is left out.").replace("+-", "-")

def s(e): return f"{A[e]['share']:.0f}\\%"
RES_MAPS = (
    f"Figure~\\ref{{fig:maps}} shows the five surfaces, Table~\\ref{{tab:area}} the area within six, twelve and 24 hours, and Figure~\\ref{{fig:area}} the share of land within twelve hours. "
    f"In 1750, a day of coaching from London covered {N(A['1750']['km2'])} km$^2$ ({s('1750')} of Great Britain's {N(R['land_km2'])} km$^2$ of land in the model), "
    f"the farthest cell lying {A['1750']['reach_km']:.0f} km from Charing Cross in a straight line; with speeds raised or lowered by the era's validation error the share is "
    f"{A['1750']['share_lo']:.0f} to {A['1750']['share_hi']:.0f}\\%. By the 1830s the area within a day had grown to {N(A['1830']['km2'])} km$^2$ ({s('1830')}), "
    f"{R['ratio']['1830_1750']:.1f} times the 1750 area, reaching {A['1830']['reach_km']:.0f} km. "
    f"The railway of 1850 then raised it to {N(A['1850']['km2'])} km$^2$ ({s('1850')}), {r1850:.1f} times the 1830s area in about fifteen years, the fastest gain per year between any two of the five dates (the 1750 to 1830s gain, {R['ratio']['1830_1750']:.1f}-fold, took more than eighty years). "
    f"The 1910 network reached {N(A['1910']['km2'])} km$^2$ ({s('1910')}) and today {N(A['today']['km2'])} km$^2$ ({s('today')}), {R['ratio']['today_1750']:.0f} times the area of 1750. "
    f"Of the {R['towns_n']} towns on the map, {R['towns_within']['1750']} were within a day of London in 1750, {R['towns_within']['1830']} in the 1830s, {R['towns_within']['1850']} in 1850, "
    f"{R['towns_within']['1910']} in 1910 and {R['towns_within']['today']} today.\n\n"
    f"The shapes differ as much as the areas. The 1750 and 1830s surfaces are close to circular, because the turnpikes radiated from London in every direction and the coach ran at much the same speed on all of them. "
    f"In 1850 the inner hours follow the main lines out of London like the spokes of a star, and the edge of the day is ragged: it runs out along the trunk lines to Lancashire, Yorkshire and Holyhead "
    f"({R['towns']['Holyhead']['1850']:.1f} hours) while parts of Wales and the south-west remain beyond it. In 1910 the denser network fills most of the gaps and the day reaches Edinburgh and Glasgow; "
    f"today every mainland town on the map is within it (Wick in {R['towns']['Wick']['today']:.1f} hours), and the land beyond a day lies on islands without a modelled crossing.")

TA = ("\\begin{table}[tbp]\\centering\\small\\caption{Land of Great Britain within 6, 12 and 24 hours of Charing Cross, by era (2 km cells). The range shows the 12-hour area with all speeds lowered and raised by the era's median validation error.}\\label{tab:area}"
      "\\begin{tabular}{lrrrrr}\\toprule Era & 6 hours & 12 hours & Share (\\%) & Range (\\%) & 24 hours\\\\\\midrule\n"
      + "".join(f"{L[e]} & {N(A[e]['km2_6h'])} & {N(A[e]['km2'])} & {A[e]['share']:.1f} & {A[e]['share_lo']:.0f} to {A[e]['share_hi']:.0f} & {N(A[e]['km2_24h'])}\\\\\n" for e in ERAS)
      + "\\bottomrule\\end{tabular}\\end{table}")

tw = ["Brighton", "Oxford", "Bristol", "Birmingham", "York", "Manchester", "Exeter", "Holyhead", "Newcastle upon Tyne", "Edinburgh", "Glasgow", "Aberdeen", "Inverness", "Wick"]
tw = [t for t in tw if t in T]
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{Modelled hours from Charing Cross to selected towns.}\\label{tab:towns}"
      "\\begin{tabular}{lrrrrr}\\toprule Town & 1750 & 1830s & 1850 & 1910 & Today\\\\\\midrule\n"
      + "".join(f"{t.replace(' upon Tyne', '')} & " + " & ".join("" if T[t][e] is None else f"{T[t][e]:.1f}" for e in ERAS) + "\\\\\n" for t in tw)
      + "\\bottomrule\\end{tabular}\\end{table}")
cv = R["convergence_edinburgh_min_per_year"]
RES_TOWNS = (
    f"Table~\\ref{{tab:towns}} gives modelled hours to selected towns and Figure~\\ref{{fig:towns}} plots them. Edinburgh, the classic test of the road north, is "
    f"{T['Edinburgh']['1750']:.0f} hours of travel from London in the 1750 model ({T['Edinburgh']['1750'] / 12:.0f} twelve-hour days), {T['Edinburgh']['1830']:.0f} in the 1830s, "
    f"{T['Edinburgh']['1850']:.1f} in 1850, {T['Edinburgh']['1910']:.1f} in 1910 and {T['Edinburgh']['today']:.1f} today (Figure~\\ref{{fig:edinburgh}}). "
    f"In Janelle's terms the model's London to Edinburgh time fell by {cv['1750_1830']:.0f} minutes a year between 1750 and 1836, {cv['1830_1850']:.0f} minutes a year between 1836 and 1850, "
    f"{cv['1850_1910']:.0f} between 1850 and 1910 and {cv['1910_today']:.1f} since. The fall between 1750 and the 1830s is the largest in absolute terms, because the starting point was so far away; "
    f"the fall between 1836 and 1850 is the fastest per year. Manchester went from {T['Manchester']['1750']:.0f} hours to {T['Manchester']['1830']:.0f}, {T['Manchester']['1850']:.1f}, "
    f"{T['Manchester']['1910']:.1f} and {T['Manchester']['today']:.1f}; Bristol from {T['Bristol']['1750']:.0f} to {T['Bristol']['1830']:.1f}, {T['Bristol']['1850']:.1f}, "
    f"{T['Bristol']['1910']:.1f} and {T['Bristol']['today']:.1f}.")

names = [("r04", "Other main roads at 0.4 of turnpike speed"), ("r08", "Other main roads at 0.8"), ("r10", "Other main roads at turnpike speed"),
         ("wait0", "No waits"), ("wait60", "Waits of 60 minutes"), ("walk4", "Walking 4 km/h"), ("walk6", "Walking 6 km/h"),
         ("branch035", "Branch lines at 0.35 of main"), ("branch07", "Branch lines at 0.7 of main"), ("grid4", "4 km grid"),
         ("noinferred", "1910 without inferred lines"), ("fastest_train", "Rail speed fitted to fastest trains"),
         ("budget8", "8-hour day"), ("budget16", "16-hour day")]
rows = f"Main model & " + " & ".join(f"{A[e]['share']:.0f}" for e in ERAS) + "\\\\\\midrule\n"
for k, lab in names:
    rows += lab + " & " + " & ".join("" if R["sens"].get(k, {}).get(e) is None else f"{R['sens'][k][e] / R['land_km2'] * 100:.0f}" for e in ERAS) + "\\\\\n"
rows += "1750 with 10-hour coaching days & " + f"{R['sens']['day_hours']['10'] / R['land_km2'] * 100:.0f} & & & & \\\\\n"
rows += "1750 with 14-hour coaching days & " + f"{R['sens']['day_hours']['14'] / R['land_km2'] * 100:.0f} & & & & \\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sensitivity: share of Great Britain's land within the day (\\%), by era. Blank: not applicable to that era.}\\label{tab:sens}"
      "\\begin{tabular}{lrrrrr}\\toprule Check & 1750 & 1830s & 1850 & 1910 & Today\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
sr = R["sens_range"]
RES_ROBUST = (
    f"Table~\\ref{{tab:sens}} and Figure~\\ref{{fig:sens}} report the planned checks. Leaving aside the length of the day, the 12-hour share ranges from "
    + ", ".join(f"{sr[e]['min'] / R['land_km2'] * 100:.0f} to {sr[e]['max'] / R['land_km2'] * 100:.0f}\\% in {'the 1830s' if e=='1830' else ('today' if e=='today' else L[e])}" for e in ERAS)
    + ". The ordering of the eras never changes. In the coach eras no single assumption moves the share by more than two percentage points; in the railway eras the waits and above all the train speed matter: "
    f"fitting train speeds to the documented fastest trains rather than Leunig's averages raises the 1850 share to {R['sens']['fastest_train']['1850'] / R['land_km2'] * 100:.0f}\\% and the 1910 share to "
    f"{R['sens']['fastest_train']['1910'] / R['land_km2'] * 100:.0f}\\%. Leaving out the inferred lines of 1910 changes the 1910 share to {R['sens']['noinferred']['1910'] / R['land_km2'] * 100:.0f}\\%, "
    f"so the reconstruction matters mainly for remote branch-line country. A coarser 4 km grid gives nearly the same areas. The length of the day matters most of all: an eight-hour day "
    f"reaches {R['sens_budget']['1750']['8'] / R['land_km2'] * 100:.0f}\\% of the land in 1750 and {R['sens_budget']['1850']['8'] / R['land_km2'] * 100:.0f}\\% in 1850; a sixteen-hour day "
    f"{R['sens_budget']['1750']['16'] / R['land_km2'] * 100:.0f}\\% and {R['sens_budget']['1850']['16'] / R['land_km2'] * 100:.0f}\\%.")

DISCUSSION = open(os.path.join(CODE, "paper_discussion.tex"), encoding="utf-8").read()
CONCLUSION = open(os.path.join(CODE, "paper_conclusion.tex"), encoding="utf-8").read()

# ---------------------------------------------------------------- appendix tables
SP = ("\\begin{table}[tbp]\\centering\\small\\caption{The speed model. Fitted: chosen to minimise squared log error against documented times; fixed: assumed or from the cited source.}\\label{tab:speeds}"
      "\\begin{tabular}{p{2.1cm}p{6.6cm}rp{3.8cm}}\\toprule Era & Element & km/h & Source\\\\\\midrule\n"
      f"1750 & Coach on a turnpike of 1750 & {F['1750']['speed_kmh']:.2f} & fitted, 12 journeys\\\\\n"
      f" & Other main road; Scotland's main roads & {0.6 * F['1750']['speed_kmh']:.2f} & 0.6 of turnpike (assumed)\\\\\n"
      f"1830s & Coach on a turnpike of 1830; Scotland's main roads & {F['1830']['speed_kmh']:.1f} & fitted, 1836 timetables\\\\\n"
      f" & Other main road & {0.6 * F['1830']['speed_kmh']:.1f} & 0.6 of turnpike (assumed)\\\\\n"
      f"1819 check & Coach on a turnpike of 1820 & {F['1819']['speed_kmh']:.1f} & fitted, 1819 timetables\\\\\n"
      f"1850 & Main-line train & {S['1850']['main_kmh']:.1f} & \\citet{{leunig2006}} $\\times$ circuity {S['1850']['circuity']:.2f}\\\\\n"
      f" & Branch-line train & {S['1850']['main_kmh'] * S['1850']['branch_ratio']:.1f} & minor/important ratio\\\\\n"
      f" & Feeder coach on 1838 roads & {F['1830']['speed_kmh']:.1f} & 1830s fit\\\\\n"
      f"1910 & Main-line train & {S['1910']['main_kmh']:.1f} & \\citet{{leunig2006}} $\\times$ circuity {S['1910']['circuity']:.2f}\\\\\n"
      f" & Branch-line train & {S['1910']['main_kmh'] * S['1910']['branch_ratio']:.1f} & minor/important ratio\\\\\n"
      f" & Feeder coach on 1838 roads & {F['1830']['speed_kmh']:.1f} & 1830s fit\\\\\n"
      f"Today & Main-line train; branch & {F['today_rail']['speed_kmh']:.0f}; {F['today_rail']['speed_kmh'] / 2:.0f} & fitted, 12 times; half\\\\\n"
      " & Motorway, trunk, primary, secondary & 100, 80, 60, 45 & fixed, below \\citet{dft2025} free-flow\\\\\n"
      " & Between cells (minor roads) & 30 & fixed\\\\\n"
      "All before today & Walking between cells & 4.8 & fixed (3 mph)\\\\\n"
      "Rail eras & Wait on boarding a train or feeder coach & 30 min & fixed\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for e in ERAS:
    d = J[J.era == e]
    for r in d.itertuples():
        mod = r.model_loo if (e in ("1750", "today") and not pd.isna(r.model_loo)) else r.model
        doc = f"{r.value:g} days" if r.unit == "days" else f"{r.hours:.2f} h"
        rows += f"{L[e]} & {tex(r.town)} & {int(r.year)} & {doc} & {mod:.1f} & {(mod - r.hours) / r.hours * 100:+.0f} & {tex(r.source)}\\\\\n".replace("+-", "-").replace(" -", " $-$")
TD = ("{\\scriptsize\\setlength{\\tabcolsep}{3pt}\\begin{longtable}{llrrrrp{5.2cm}}\\caption{Documented journeys from London and the model. Model: leave-one-out time for 1750 and today, otherwise the model; days counted as 12 travelling hours.}\\label{tab:docs}\\\\\\toprule "
      "Era & Destination & Year & Documented & Model (h) & Error (\\%) & Source\\\\\\midrule\\endfirsthead \\toprule Era & Destination & Year & Documented & Model (h) & Error (\\%) & Source\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
APPX = ("\\subsection{Speeds}\n" + SP + "\n\\subsection{Documented journeys}\n" + TD + "\n\\subsection{Data construction}\n"
        f"The turnpike map has {len(NET['turnpike']):,} line parts after splitting multi-part features; sections coded 7, 8 or 9 for a decade (not yet made, estate roads) are left out of that decade's network. "
        f"Scotland's proxy roads are {len(NET['scot_roads']):,} OpenStreetMap trunk, primary and motorway lines whose midpoints fall in or within 2 km of Scotland's land cells. "
        f"The 1910 inferred lines join {NET['n_far_closed']:,} closed stations; their total length is {R_INF_KM:,.0f} km. "
        "All networks are resampled every 300 m; vertices of different lines closer than 40 m are joined. The land grid uses the ONS December 2023 local authority boundaries (generalised, clipped to the coastline). "
        "Coach termini are the end of each service's mapped route farthest from Charing Cross; services whose terminus is within 15 km of Charing Cross are left out. "
        "Point times are the minimum, over all graph nodes within 2.5 km, of the node's time plus the walk from it.\n")

ABSTRACT = (
    "How much of Great Britain lay within a day's travel of London, and how did that change between the coaching era and today? "
    f"I build a multimodal network model on a 2 km grid for five dates (1750, the 1830s, 1850, 1910 and today) from historical GIS of the turnpike roads of England and Wales and the railways of 1851, a reconstruction of the 1910 rail network, and OpenStreetMap. "
    f"Coach speeds are fitted to scheduled times of London coach services in 1836 ({R['coach']['n_termini_1836']} destinations) and to twelve cited journeys of 1739 to 1764; train speeds come from published averages; every era is tested on journeys it was not fitted to. "
    f"The 1830s model reproduces the 1837 mail-coach timetable with a median absolute error of {V['1830_mail1837']['mdape']:.0f}\\%. The 1750 model fails the error threshold set in advance ({F['1750']['loo']['mdape']:.0f}\\% against 25\\%), so its map is a rough sketch. The 1850 and 1910 models use average train speeds and are slower than documented expresses by a median {V['1850_all']['mdape']:.0f}\\% and {V['1910_all']['mdape']:.0f}\\%, on four and six journeys, so their areas are lower bounds. "
    f"Leaving Charing Cross at dawn, twelve hours of travel reached {A['1750']['share']:.0f}\\% of Great Britain's land in 1750, {A['1830']['share']:.0f}\\% in the 1830s, at least {A['1850']['share']:.0f}\\% in 1850, "
    f"at least {A['1910']['share']:.0f}\\% in 1910 and {A['today']['share']:.0f}\\% today. The largest gain per year came between the 1830s and 1850, when the first railways multiplied the area within a day by at least {r1850:.1f} in about fifteen years. "
    "The surfaces and code are released for reuse.")

body = open(os.path.join(CODE, "paper_body.tex"), encoding="utf-8").read()
for k, val in (("RES_SPEEDS", RES_SPEEDS), ("RES_VALID", RES_VALID), ("RES_MAPS", RES_MAPS), ("RES_TOWNS", RES_TOWNS), ("RES_ROBUST", RES_ROBUST),
               ("DISCUSSION", DISCUSSION), ("CONCLUSION", CONCLUSION)):
    body = body.replace("{{" + k + "}}", val)
FIGS = {
    "maps": ("Hours of travel from Charing Cross (white dot) in each era, 2 km cells. Solid line: 12 hours; dashed lines: 12 hours with all speeds raised or lowered by the era's median validation error.", "\\textwidth"),
    "valid": ("Modelled against documented journey times (log scales). Fitted eras are shown leaving each destination out; the 1837 mails, the trains of 1850 and 1910 are out of sample. Dotted lines: within 20\\%.", "0.7\\textwidth"),
    "coach": ("Scheduled speeds of the fastest London coach to each terminus, 1819 and 1836, against route length, with the fitted turnpike speed.", "0.95\\textwidth"),
    "area": ("Share of Great Britain's land within 12 hours of Charing Cross by era; whiskers: speeds lowered and raised by the era's median validation error.", "0.7\\textwidth"),
    "edinburgh": ("London to Edinburgh: documented times (days counted as 12 travelling hours) and the model.", "0.75\\textwidth"),
    "towns": ("Modelled hours from Charing Cross to selected towns by era.", "0.75\\textwidth"),
    "sens": ("Sensitivity of the share of land within 12 hours to the model's assumptions.", "0.8\\textwidth"),
}
fig = lambda k: f"\\begin{{figure}}[tbp]\\centering\\includegraphics[width={FIGS[k][1]}]{{f_{k}.pdf}}\\caption{{{FIGS[k][0]}}}\\label{{fig:{k}}}\\end{{figure}}"
body = body.replace("\\subsection{Calibrated speeds}", fig("coach") + "\n\\subsection{Calibrated speeds}")
body = body.replace("\\subsection{How well the model reproduces documented journeys}", "\\subsection{How well the model reproduces documented journeys}\n" + TV + "\n" + fig("valid"))
body = body.replace("\\subsection{A day from London}", "\\subsection{A day from London}\n" + fig("maps") + "\n" + TA + "\n" + fig("area"))
body = body.replace("\\subsection{Towns and the road north}", "\\subsection{Towns and the road north}\n" + TT + "\n" + fig("towns") + "\n" + fig("edinburgh"))
body = body.replace("\\section{Robustness}\\label{sec:robust}", "\\section{Robustness}\\label{sec:robust}\n" + TS + "\n" + fig("sens"))
extra = {"BOG1750": "2.6", "BOG1820": "8.0", "TP_N": f"{len(NET['turnpike']):,}", "CO_ROUTES": f"{R['coach']['n_services_1819'] + R['coach']['n_services_1836']:,} timed",
         "R51_N": f"{len(NET['rail1851']):,}", "NFAR": f"{NET['n_far_closed']:,}", "INF_KM": None, "LAND_CELLS": f"{int(R['land_km2'] / 4):,}",
         "RAIL1850_KMH": f"{S['1850']['main_kmh']:.1f}", "RAIL1910_KMH": f"{S['1910']['main_kmh']:.1f}", "RATIO_1850_TXT": EXTRA["RATIO_1850_TXT"]}
extra["INF_KM"] = f"{R_INF_KM:,.0f}"
for k, val in extra.items():
    body = body.replace("{{" + k + "}}", val)


def tfmt(v_, f):
    if f == "int": return f"{int(round(float(v_))):,}"
    for k in ("f0", "f1", "f2", "f3"):
        if f == k: return f"{float(v_):.{k[1]}f}".replace("-", "$-$")
    return tex(str(v_))


t = open(os.path.join(CODE, "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{ABSTRACT}}", ABSTRACT).replace("{{BODY}}", body).replace("{{APPENDIX}}", APPX)
t = t.replace("{{BIBLIOGRAPHY}}", open(os.path.join(CODE, "paper_bib.tex"), encoding="utf-8").read())
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
t = re.sub(r"\{\{(?!DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24105505", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("DSIT", "DCMS", "pre-registered", "preregistered"):
    assert bad not in t, bad
cites = set(re.findall(r"\\cite[a-z]*\{([^}]+)\}", t)); keys = set()
for c in cites: keys |= {x.strip() for x in c.split(",")}
bib = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", t))
assert keys <= bib, keys - bib
print("uncited references:", sorted(bib - keys))
for lab in re.findall(r"\\label\{((?:fig|tab):[^}]+)\}", t):
    assert f"ref{{{lab}}}" in t, f"unreferenced {lab}"
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
bodytxt = txt.split("\nReferences\n")[0]
ab = txt.split("Abstract")[1].split("Keywords")[0]
print("paper", r.returncode, len(txt.split()), "words total;", len(bodytxt.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "references", len(bib))
jsave({"words": len(bodytxt.split()), "abstract": len(ab.split()), "figs": len(FIGS), "tabs": len(re.findall(r"\\label\{tab:", t)),
       "pages": [l for l in pages.splitlines() if l.startswith("Pages")][0].split()[-1], "refs": len(bib)}, f"{SCR}/paper_stats.json")
