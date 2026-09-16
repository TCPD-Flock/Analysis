# The Colony, TX PD — Flock Safety ALPR Audit Log Analysis (full research file)

**Source:** Records produced by The Colony, TX Police Department under Texas Public Information Act request (Flock export #857).
**Analyzed:** September 2026. **Coverage period in the data:** January 1, 2024 – August 13, 2026 (32 months; the last month is partial, cut off at the 13th).
**This version:** written for handoff to another analysis session working on The Colony PD's Flock/ALPR documents — it uses **real officer names throughout** (not the anonymized `Officer-NN` codes used in the public-facing `index.html`; see §13) and includes full data tables, not just headline examples, so it can be extended without re-deriving everything from the raw CSVs.

---

## 0. How to use this document

- Sections 1–7 are the original per-category analysis (justification, volume, repeated-target, off-hours, geography).
- Section 8 is a full year-over-year breakdown (2024 vs. 2025 vs. 2026, Jan–Aug apples-to-apples) for every metric above — built after the original analysis, and it's where most of the *new* signal is (a platform change, an access-concentration cliff, two federal-access spikes).
- Section 9 flags a **data-generation change in the underlying system in January 2026** that affects how several metrics should be read post-2026 — read this before trusting any 2026 "vague reason" or "distinct agency" number at face value.
- Section 10 is a running Q&A log — the exact questions this dataset can and can't answer, with direct answers, useful as a template for what to ask next.
- Section 12 (methodology) documents every threshold, regex, and formula used, so a fresh session can either trust or challenge each one.
- Section 13 tells you exactly where the reusable scripts, cached intermediate JSON, and other deliverables live, so **you should not need to re-scan the 17.1M-row network log from scratch** — it's already been done four ways (all-time, and per-year) and cached.
- Raw plate numbers are intentionally omitted from this document, same as the public version — flagged entries are cited by **source file + row ID**. Officer names are real (internal document), but if you're producing anything public-facing, run it through the anonymization scheme in §13 first.

---

## 1. What's in the export

The department produced two distinct logs, which Flock calls the **Org Audit Log** and the **Network Audit Log**:

| Log | Folder | Rows | What it captures | Names/plates visible? |
|---|---|---|---|---|
| **Org log** | `TheColonyTXPD-Org/` | 24,333 | Searches **run by Colony's own officers** (104 distinct users), including searches they ran against other agencies' camera networks | Yes — officer name and searched plate are both present |
| **Network log** | `TheColonyTXPD-Network/` | 17,135,439 | Searches **run by outside agencies** (5,363 distinct agencies) against Colony's own cameras | No — requesting officer's name and searched plate are both redacted (`***`); only the requesting agency and stated reason are visible |

This split matters: individual-officer patterns (repeated targets, off-hours behavior, personal habits in justification text) can only be examined in the **Org log**. The **Network log** is huge (3.4 GB, 32 monthly files) and can only be analyzed in aggregate — by agency, by state, by reason text.

Both logs share the same 13 columns: `ID, Name, Org Name, Total Networks Searched, Time Frame, License Plate, Reason, Case #, Filters, Search Time, Search Type, Text Prompt, Moderation`. Timestamps are UTC in the raw files; Org-log analysis below converts to Central Time (America/Chicago, DST-aware) where local time-of-day matters. **Each monthly CSV file is cleanly bounded to its calendar month** (verified: e.g. `TheColonyTXPD_network_Jan_2024.csv` runs 2024-01-01 06:02 UTC to 2024-01-31 05:59 UTC) — safe to bucket by filename for monthly/yearly aggregation without re-parsing every row's date.

`Search Type` values seen: `search`, `search - Mobile` (manual queries), `lookup`, `lookup - Mobile` (more often tied to a standing "hotlist" alert firing automatically whenever a flagged plate is read by any camera in the network), plus small volumes of `convoy` (multi-vehicle detection), `apiV1`, `freeform`, `visual`, `multiGeo`, `mostSeenOcrValues`, `searchSummary - Mobile`. The search/lookup distinction is the basis for separating "automated hotlist hit" from "manual search" throughout this document.

---

## 2. Basic stats (all-time)

- **Org log:** 24,333 searches, Jan 1 2024 – Aug 13 2026, by 104 unique officers, all under one org name ("The Colony TX PD" — no sub-units or aliases). Search type split: `search`/`search - Mobile` 12,384; `lookup`/`lookup - Mobile` 11,949.
- **Network log:** 17,135,439 searches, same range, from 5,363 unique agencies. Search type split: `lookup`-type 13.34M; `search`-type 3.75M; `convoy` 35,403; small remainder in other types.
- Combined ≈17.16M logged search events over ~31.4 months, i.e. roughly 18,400/day network-wide, of which Colony's own officers account for ~26/day.

---

## 3. Missing or vague justification (all-time)

**Method:** the `Reason` field classified as **blank**, **numeric/case-number-only** (regex `^[\d\-\/#\.\s]+$` — digits, dashes, slashes, #, periods, whitespace only), a fixed list of **generic/vague terms** (see §12) or single/double-character strings, or **substantive** (everything else). Heuristic, not a manual read of every row.

### Org log

| Category | Count | % |
|---|---|---|
| Substantive text | 19,655 | 80.8% |
| Case-number only | 3,728 | 15.3% |
| Vague/short term | 948 | 3.9% |
| Blank | 2 | 0.0% |

3,681 of the 3,728 case-number-only rows also have the dedicated `Case #` column blank — i.e., the case number is typed into the wrong field with no cross-reference at all.

**By officer, case-number-only rate** (top): **Stephanie Johnson 96.9%** (602/621), **James Barfield 84.4%** (81/96), **Caleb Ray 65.1%** (n=106), **Taylor Wolfe 61.2%** (n=49), **John Downing 59.7%** (1,725/2,891 — largest by raw count), **Timothy Rogers 58.7%** (n=881). Same underlying habit (case # typed into Reason, Case # field left blank); by rate rather than raw count, Johnson and Barfield are more consistent about it than Downing despite far lower volume.

**By officer, vague/blank rate** (top): **Joel Galvin 66.2%** (749/1,131 — overwhelmingly a literal `"."` repeated across dozens of distinct plates, spanning >1 year), Dewayne Kyle 13.4% (n=67), Matthew Winnett 6.5% (n=217), Trevor Robinson 4.7% (n=86), N Bakker 4.0% (n=50), Lesley Huntsinger 3.5% (n=258). Galvin is the single strongest "no real justification" finding in the dataset. Example rows: `TheColonyTXPD_org_Apr_2025.csv` rows `7115ee0d-0442-493e-b924-5797ee2c6980`, `62be83aa-a4bc-4234-b09a-4fc0932f7873`, `61a446b8-eef7-4a97-9451-55a954970644`.

### Network log

| Category | Count | % |
|---|---|---|
| Substantive text | 15,218,406 | 88.8% |
| Case-number only | 990,219 | 5.8% |
| Vague/short term | 922,580 | 5.4% |
| Blank | 4,234 | 0.02% |

**Worst offenders by rate** (agencies with ≥500 lifetime searches; corrected/algorithmic ranking — see note below):

| Agency | Vague rate | n |
|---|---|---|
| East Tawakoni TX PD | 97.7% | 19,803 |
| Blaine CO OK SO | 89.1% | 5,090 |
| Austell GA PD | 86.8% | 2,371 |
| West Tawakoni TX PD | 85.5% | 9,046 |
| Cape Girardeau County MO SO | 84.5% | 4,917 |
| Georgia Attorney General's Office - GA | 84.3% | 883 |
| Powder Springs GA PD | 80.6% | 966 |
| Brooklyn OH PD | 79.7% | 705 |

> **Correction note:** an earlier draft of this list (Fulton/DeKalb/Lawrenceville/Mishawaka County GA/IN PDs at 62–70%) was built by sorting agencies by *absolute count* of vague hits, then hand-picking a few high-rate examples from that list — it was never a true top-8-by-rate. This table is the properly rate-sorted version (min. 500 lifetime searches to filter noise); those four agencies are all still genuinely >50% vague, just not top-8. East Tawakoni's citation and framing (single-keystroke reasons — `s`, `h`, `j`, `k`…) is unaffected either way: `TheColonyTXPD_network_Apr_2024.csv`, row `1f6b4135-0b75-41ab-963a-751f162035ce`, entire stated reason `"d"`.

**Fort Worth TX PD** is a partial exception worth naming separately: 15.7% flagged (72,061/458,116), but inspection shows most of it is terse-but-legible department shorthand (`inv`, `sus`, `sus veh`, `stolen`, radio codes `51`/`60`) rather than truly empty text — lower-confidence flag than the Tawakoni pattern. **Houston TX PD** (2.5% of 1.70M) and **Dallas TX PD** (3.2% of 1.23M) — the two highest-volume agencies — are close to the network-wide average despite dominating raw volume.

---

## 4. Volume outliers — top 10 by search count (all-time)

### Org log (of 104 officers)
John Downing 2,891 · Maria Mccracken 2,095 · Kreig Wallace 1,924 · Joel Galvin 1,131 · Aaron Gillespie 1,104 · Domingo Rios 901 · Timothy Rogers 881 · Tosha Whitley 769 · Stephanie Johnson 621 · Hector D Garcia 617.
Top 10 = 12,934/24,333 (53%) despite being <10% of the 104 officers who appear at all.

### Network log (of 5,363 agencies)
Houston TX PD 1,701,176 (9.9%) · Dallas TX PD 1,231,255 (7.2%) · Texas Dept. of Public Safety 505,399 (2.9%) · Fort Worth TX PD 458,116 (2.7%) · Harris County TX SO 363,631 (2.1%) · California Highway Patrol 263,884 (1.5%) · Louisville Metro KY PD 150,087 (0.9%) · Missouri State Highway Patrol 137,887 (0.8%) · Hillsborough County FL SO 136,954 (0.8%) · Grand Prairie TX PD 128,442 (0.7%).
Top 10 = 4.98M/17.14M (29%). Long tail: median agency in the 5,363-agency list runs only a few dozen searches total over 31 months.

---

## 5. Repeated-target pattern — is anyone doing this without a real case?

Only possible in the Org log (only place plates and officer names are both unredacted). Grouped every (officer, plate) pair (1,785 pairs with 3+ searches) and scored on: manual (`search`) vs. likely-automated (`lookup`); whether a case number is *ever* attached; reason vagueness; off-hours concentration; duration span. See §12 for the exact composite-score formula.

### The single largest case (hotlist, not manual)

One plate searched **964 times by Kreig Wallace** in a 19-day window (Oct 3–22, 2025; `TheColonyTXPD_org_Oct_2025.csv`, e.g. row `f5d99307-a6dd-49f5-8627-52a70b843039`), **253 times by Timothy Rogers** (Oct 6–8, 2025; row `db57f2ae-e8b1-4c42-893e-2ee18b5f275c`), **91 times by Trevor Strong** (Sep 25–Nov 11, 2025; row `909de617-7761-4d7a-9b04-8a7600bb268e`) — 1,308 combined hits. Almost all `lookup`/`lookup - Mobile` type tied to one consistent case reference (`sc25-31`/`sc25-29`, typo variants), reason "investigation"/"narcotics" — consistent with a Flock hotlist alert firing automatically on every camera read of a flagged plate during an active case, not manual re-querying. **Worth confirming directly with the department** — the raw log can't distinguish "964 manual searches" from "vehicle drove past cameras 964 times while flagged," and those mean very different things.

### Full list: sustained, no-case, low-volume repeats (28 pairs, span ≥14 days)

This is the shape that looks most like personal/stalking-adjacent misuse elsewhere — the opposite of the hotlist case above: **low volume, spread over weeks to months, no case number ever recorded for that specific plate by that officer.** Ranked by composite score (all components shown):

| Officer | Hits | Span (days) | Vague-reason frac | Late-night frac | Weekend frac | Manual-search frac | Score | Row citation |
|---|---|---|---|---|---|---|---|---|
| John Downing | 6 | 94 | 1.00 | 0.00 | 0.67 | 0.83 | 4.59 | `org_Apr_2024.csv` / `a670c370-e4e6-411b-84e1-9c5bdc9bc1f0` |
| Joel Galvin | 12 | 129 | 1.00 | 0.17 | 0.00 | 0.67 | 4.12 | `org_Jul_2025.csv` / `819ffb28-cb5e-43d9-a87c-1e5ade20da46` |
| Joel Galvin | 15 | 150 | 1.00 | 0.53 | 0.73 | 0.33 | 3.80 | `org_Aug_2025.csv` / `a519dd9e-f9c2-4cf3-a40b-574d65434d32` |
| Joel Galvin | 5 | 172 | 1.00 | 0.00 | 0.40 | 0.40 | 3.23 | `org_Mar_2025.csv` / `1b6d940e-6a32-46cb-8341-35ca55214168` |
| Joel Galvin | 10 | 66 | 1.00 | 0.30 | 0.70 | 0.60 | 3.17 | `org_Aug_2025.csv` / `be5cfb37-d8ed-4632-aac4-4d3667e939da` |
| Tosha Whitley | 3 | 296 | 0.00 | 0.00 | 0.67 | 1.00 | 2.80 | `org_Jan_2025.csv` / `301e4cd7-cf18-42fd-8b8d-e53897189919` |
| Stephanie Johnson | 6 | 46 | 1.00 | 0.00 | 0.00 | 1.00 | 2.53 | `org_Jul_2024.csv` / `4f9e070a-851c-4d8d-8f2d-76d8516bdbd9` |
| Hector D Garcia | 5 | 139 | 0.20 | 0.00 | 0.00 | 1.00 | 2.48 | `org_Feb_2024.csv` / `097d64b1-65d2-441b-a7de-3bd8ac7460d2` |
| James Barfield | 7 | 41 | 1.00 | 0.00 | 0.00 | 1.00 | 2.37 | `org_Apr_2024.csv` / `f30827dc-f651-42e2-aaf9-4a38070a7523` |
| Domingo Rios | 7 | 450 | 0.14 | 0.00 | 0.00 | 0.71 | 2.00 | `org_Apr_2026.csv` / `f72c7228-a9d3-4293-9cf5-00813bfee5ab` |
| Simon Wilcock | 4 | 167 | 0.00 | 0.00 | 0.00 | 1.00 | 1.97 | `org_Dec_2024.csv` / `5dc01288-4a55-4149-b888-73d39e615a8e` |
| Timothy Rogers | 3 | 58 | 1.00 | 0.00 | 0.00 | 0.67 | 1.96 | `org_Apr_2024.csv` / `fe5579d2-ef41-4e1c-a3ba-0d8b0fda95f5` |
| John Downing | 8 | 26 | 1.00 | 0.00 | 0.00 | 1.00 | 1.87 | `org_Apr_2025.csv` / `1875e6fc-9c88-46cf-ab6d-162fb32b17f3` |
| Stephanie Johnson | 10 | 40 | 1.00 | 0.00 | 0.00 | 0.80 | 1.87 | `org_Aug_2024.csv` / `9767d7d0-418f-4a49-aaab-c6bb2f4d0cc1` |
| Simon Wilcock | 7 | 125 | 0.00 | 0.00 | 0.29 | 1.00 | 1.77 | `org_Aug_2024.csv` / `985d3223-7e52-4300-b96d-121fcf3bde5e` |
| John Downing | 3 | 44 | 1.00 | 0.00 | 0.00 | 0.67 | 1.64 | `org_Apr_2025.csv` / `833d48ab-6c17-4139-a057-971d851c59f2` |
| Stephanie Johnson | 3 | 17 | 1.00 | 0.00 | 0.00 | 1.00 | 1.57 | `org_Oct_2024.csv` / `ef44cc79-6c5d-407b-90e2-481487438a12` |
| Joel Galvin | 4 | 134 | 0.75 | 0.25 | 0.25 | 0.25 | 1.55 | `org_Apr_2025.csv` / `e5aab7c8-a9c8-4437-a2b8-c6b7c1c2b171` |
| Joel Galvin | 4 | 50 | 0.50 | 0.50 | 0.50 | 0.50 | 1.52 | `org_Apr_2025.csv` / `79325ae5-d6e3-4469-b025-7f528d38c5a0` |
| Stephanie Johnson | 16 | 30 | 0.81 | 0.00 | 0.00 | 0.88 | 1.52 | `org_Feb_2024.csv` / `9944f0f0-d3b2-415e-9f45-7c1f812be5f5` |
| John Downing | 14 | 46 | 1.00 | 0.00 | 0.00 | 0.57 | 1.45 | `org_Dec_2024.csv` / `629fa6b9-0f70-46d2-a5f4-783723de4891` |
| Joel Galvin | 5 | 70 | 0.60 | 0.40 | 0.20 | 0.40 | 1.44 | `org_Jul_2025.csv` / `6b9b8631-8d2b-4b9a-8941-0f51bec24965` |
| Simon Wilcock | 6 | 345 | 0.00 | 0.00 | 0.00 | 0.67 | 1.40 | `org_Apr_2026.csv` / `dc90f013-a138-40ab-8483-b4eae083121a` |
| Joel Galvin | 12 | 64 | 0.58 | 0.08 | 0.25 | 0.50 | 1.34 | `org_Dec_2024.csv` / `dfb4e037-9f5e-4c04-9728-22d55dcaa59b` |
| John Downing | 9 | 30 | 1.00 | 0.00 | 0.00 | 0.67 | 1.33 | `org_Aug_2024.csv` / `48130771-bc32-476d-96fe-5a3bda30b574` |
| Aaron Gillespie | 10 | 471 | 0.80 | 0.00 | 0.60 | 0.40 | 1.25 | `org_Dec_2025.csv` / `2282ad37-e088-4876-893f-892ff1a3aba1` |
| Simon Wilcock | 4 | 84 | 0.00 | 0.00 | 0.00 | 1.00 | 1.14 | `org_Jul_2024.csv` / `8eb09dba-8805-44b0-b0fe-d96de3416ee0` |
| John Downing | 4 | 14 | 1.00 | 0.00 | 0.00 | 0.75 | 1.10 | `org_Nov_2024.csv` / `57e4d75a-76c7-4138-9d6e-e4d7bb124cd0` |

**Concentration:** Joel Galvin (6 of 28), John Downing (7 of 28), Stephanie Johnson (4 of 28), Simon Wilcock (4 of 28), Domingo Rios/Timothy Rogers/Hector D Garcia/James Barfield/Tosha Whitley/Aaron Gillespie (1 each). No individual pair is alarming on volume alone (max 27→16 hits — the table above shows Stephanie Johnson's 16-hit/30-day pair is actually the highest raw count in this sustained list); it's the **combination** of the same handful of officers repeating this exact shape — same plate, weeks apart, no case, vague or absent reason — across many distinct plates, that's worth a closer human look.

**What this data can't tell you:** whether any of these 28 reflect a personal relationship, curiosity, or an officer who simply never bothered to log a case number for an otherwise legitimate reason. It tells you the pattern exists and exactly which rows to pull; it can't tell you intent.

There is also a secondary, lower-concern bucket: 32 (officer, plate) pairs with no case number that are **single-session bursts** (span <14 days, often same-day) — e.g. Joel Galvin 23 hits/12 days, Stephanie Johnson 11 hits/7 days. These read more like a real-time chase/lookup on a person of interest during one shift than sustained interest, but they're also missing a case number, which is odd if it was a real operational need. Full list in `analysis/data/stalking_risk.json` (filter `span_days < 14`).

---

## 6. Off-hours / unusual timing (Org log)

Timestamps converted UTC→Central (DST-aware). All-time baseline: **7.9%** of searches fall 1–5am local, **20.5%** fall on a weekend.

**Late-night rate by officer** (top, min. 30 searches): Megan Ramirez 47.6% (n=42), Cheyenne Anderson 42.9% (n=56), Ryan Downs 40.6% (n=32), Lesley Huntsinger 40.3% (n=258), Austin Thompson 38.1% (n=507), Marcus Maxie 35.6% (n=90).
**Weekend rate by officer** (top): Kevin Bell 86.9% (n=84), Brian Baker 62.5% (n=32), Lesley Huntsinger 60.5% (n=258), Eric Zimmerman 60.2% (n=98), Zachary Woolston 58.8% (n=182), Anna Varvil 58.5% (n=53).

**Important caveat:** cannot distinguish shift assignment from misuse without a duty roster (not in this export). An officer clustering at 2am on Saturdays is far more likely on a night-shift rotation than doing anything improper.

### The sharper finding: reason quality by time-of-day (decomposed)

Isolating **true** blank/vague reasons from the separate case-number-habit (which is a distinct phenomenon tied to specific officers, not to timing):

| Bucket | Blank/vague rate |
|---|---|
| 1–5am (late night) | **11.2%** |
| Daytime | 3.3% |
| Weekend | **7.0%** |
| Weekday | 3.1% |

A **3.4×** gap for late-night vs. daytime, **2.2×** for weekend vs. weekday. (If you don't exclude the case-number habit, this flips — daytime looks "worse" — purely because that habit is a big-volume daytime administrative pattern unrelated to timing. The decomposed version is the one that actually answers "are odd-hour searches less well-documented.") This pattern **holds and even strengthens year over year** through 2025 before the Jan-2026 platform change erases the whole "vague reason" category — see §8's per-year table.

---

## 7. Out-of-network / out-of-state access (Network log)

The department has publicly described sharing as limited to Texas or ~500 miles. Checked via requesting agency's home-state distance from The Colony, TX (state-centroid haversine distance, spot-corrected for large border-state agencies — see §12), and separately via federal-agency tag search.

### By distance

96.6%+ of rows mapped to a state (rest are transit authorities, tribal police, dispatch consortia — excluded, not guessed). **~6.87M of 17.14M network searches (~40%) came from agencies whose home city sits >~500 miles away.** Georgia (1.03M) and Florida (1.00M) alone each out-search every in-radius state except Texas. Of 5,363 total partner agencies, **~75% are outside the 500-mile band**, even though the highest-*volume* agencies are in-state — i.e., the "Texas/500mi" framing understates network breadth when measured by number of partner agencies rather than search volume.

Largest out-of-radius agencies: California Highway Patrol (~1,309mi, 263,884), Louisville Metro KY PD (~758mi, 150,087), Hillsborough County FL SO (~977mi, 136,954), Palm Beach County FL SO (~977mi, 107,814), Cobb County GA PD (~767mi, 94,904), Fairfax County VA PD (~1,101mi, 78,920), Arizona DPS (~839mi, 63,155), Coweta County GA SO (~767mi, 56,132).

### Federal agencies (15 distinct, explicitly tagged `[Federal]`, 91,400 searches / 0.5% of network total)

| Agency | Searches | Status |
|---|---|---|
| US Postal Inspection Service | 56,238 | active |
| Federal Bureau of Investigation (FBI) | 21,440 | active |
| ATF Nashville TN | 7,143 | inactive |
| US Border Patrol | 3,703 | inactive |
| ATF Louisville KY | 1,739 | inactive |
| Natchez Trace Parkway MS – National Park Service | 272 | active |
| US GSA Office of Inspector General | 237 | active |
| Langley VA Air Force Base | 218 | active |
| Homeland Security Investigations | 161 | inactive |
| Naval Criminal Investigative Service | 145 | inactive |
| National Park Service TN | 61 | inactive |
| Wright-Patterson OH Air Force Base | 22 | active |
| Lake Mead NV NRA | 13 | active |
| Roudebush Medical Center IN Veterans Affairs PD | 6 | active |
| US Park Police – Chattahoochee River NRA | 2 | active |

**No entry anywhere in the export is tagged ICE or CBP.** The two closest categories — US Border Patrol and Homeland Security Investigations — total 3,864 searches combined and are both explicitly marked **inactive** in the export, meaning access was later revoked. Only USPIS and FBI have meaningful *active* federal access. Example rows: FBI — `TheColonyTXPD_network_Jul_2026.csv`, row `bb15dcbf-9616-44b0-b2ec-f919c6b06a16`; Border Patrol (inactive) — `TheColonyTXPD_network_Aug_2025.csv`, row `c5f3a384-373c-4008-9c49-16e7e9a90524`.

### Bidirectional note

Colony's own officers also reach outward: the Org log's `Filters` field shows voluntary state-scoping on 8,965+7,861+… searches, most often "texas" (7,861) but also arkansas (138), georgia (96), florida (58), oklahoma (55), illinois (55) — Colony officers searching other states' networks too, not just being searched by them. This report focuses on inbound access since that's where the public "Texas/500mi" claim was made, but the same policy question applies both directions.

---

## 8. Year-over-year: 2024 vs. 2025 vs. 2026 (full breakdown)

All "2026" figures are **Jan 1 – Aug 13 2026 only** (partial year, ~7.4 of 12 months); 2024/2025 are full calendar years unless a table says "Jan–Aug" for a fair comparison.

### 8.1 Headline volume & growth (Jan–Aug each year, apples-to-apples)

| Metric | 2024 | 2025 | 2026 | Growth 24→25 | Growth 25→26 |
|---|---|---|---|---|---|
| Network-log searches | 2,179,202 | 4,970,398 | 5,394,693 | +128% | +9% |
| Org-log searches | 3,771 | 6,883 | 6,527 | +83% | −5% |
| Out-of-radius share of network traffic | 50.5% | 40.9% | 31.8% | — | — |
| Federal share of network traffic | 0.17% | 0.54% | 0.84% | ~3× | ~1.6× |
| Avg. distinct partner agencies/month | 2,456 | 3,385 | 891 (Jan–Jul) | +38% | **−74%** |
| Org-log late-night share (1–5am) | 4.5% | 10.2% | 9.7% | ~2.3× | flat |
| Org-log weekend share | 18.9% | 22.5% | 20.7% | — | — |

Full-year (not Jan–Aug) totals, for reference: Network log 2024 = 3,959,775; 2025 = 7,780,971; 2026 (partial, Jan–Aug13) = 5,394,693. Org log 2024 = 6,178; 2025 = 11,628; 2026 (partial) = 6,527.

**Reading this:** explosive growth 2024→2025 in both logs, then a near-plateau (network) or slight decline (org) into 2026. Out-of-radius *share* fell even as its *absolute volume* grew every year (1.10M → 2.04M → 1.72M, Jan–Aug), because in-state volume grew faster. Federal share of traffic rose steadily. The 74% collapse in distinct partner agencies is the single sharpest inflection point in the whole dataset — see §9.

### 8.2 Top 10 officers by year (real names, count + % of that year's Org-log total)

| Rank | 2024 | 2025 | 2026 (partial) |
|---|---|---|---|
| 1 | John Downing — 1,252 (20.3%) | Kreig Wallace — 1,391 (12.0%) | Maria Mccracken — 657 (10.1%) |
| 2 | Stephanie Johnson — 621 (10.1%) | John Downing — 1,177 (10.1%) | Domingo Rios — 650 (10.0%) |
| 3 | Maria Mccracken — 416 (6.7%) | Maria Mccracken — 1,022 (8.8%) | John Downing — 462 (7.1%) |
| 4 | Aaron Gillespie — 333 (5.4%) | Joel Galvin — 750 (6.4%) | Kreig Wallace — 449 (6.9%) |
| 5 | Joel Galvin — 239 (3.9%) | Timothy Rogers — 683 (5.9%) | Austin Thompson — 305 (4.7%) |
| 6 | Steven Wheeler — 170 (2.8%) | Aaron Gillespie — 649 (5.6%) | Cassie Fears — 213 (3.3%) |
| 7 | Skylar Sillivent — 161 (2.6%) | Tosha Whitley — 589 (5.1%) | Trevor Strong — 201 (3.1%) |
| 8 | Timothy Rogers — 154 (2.5%) | Trevor Strong — 291 (2.5%) | Hector D Garcia — 192 (2.9%) |
| 9 | Simon Wilcock — 147 (2.4%) | Hector D Garcia — 288 (2.5%) | Auldon Barker — 187 (2.9%) |
| 10 | Hector D Garcia — 137 (2.2%) | Simon Wilcock — 258 (2.2%) | Andrea Jordan — 163 (2.5%) |

Note Kreig Wallace's #1 2025 ranking is driven substantially by the 964-hit hotlist case in October 2025 (§5) — not necessarily 1,391 independent manual searches.

### 8.3 Top 10 requesting agencies by year (count + % of that year's Network-log total)

| Rank | 2024 | 2025 | 2026 (partial) |
|---|---|---|---|
| 1 | Houston TX PD — 448,248 (11.3%) | Houston TX PD — 716,436 (9.2%) | Houston TX PD — 536,492 (9.9%) |
| 2 | Dallas TX PD — 298,686 (7.5%) | Dallas TX PD — 526,545 (6.8%) | Dallas TX PD — 406,024 (7.5%) |
| 3 | Fort Worth TX PD — 128,229 (3.2%) | Fort Worth TX PD — 190,478 (2.4%) | Texas DPS — 276,674 (5.1%) |
| 4 | Harris County TX SO — 80,755 (2.0%) | Texas DPS — 176,149 (2.3%) | California Highway Patrol — 260,935 (4.8%) |
| 5 | Texas DPS — 52,576 (1.3%) | Harris County TX SO — 168,005 (2.2%) | Fort Worth TX PD — 139,409 (2.6%) |
| 6 | Riverside County CA SO — 40,753 (1.0%) | Missouri Highway Patrol — 78,017 (1.0%) | Harris County TX SO — 114,871 (2.1%) |
| 7 | Harris County Const TX Pct 4 — 38,929 (1.0%) | Harris County Const TX Pct 4 — 57,639 (0.7%) | Louisville Metro KY PD — 88,652 (1.6%) |
| 8 | Grand Prairie TX PD — 31,176 (0.8%) | Pasadena TX PD — 56,328 (0.7%) | Hillsborough County FL SO — 83,602 (1.5%) |
| 9 | Plano TX PD — 28,814 (0.7%) | Grand Prairie TX PD — 55,350 (0.7%) | Palm Beach County FL SO — 52,713 (1.0%) |
| 10 | Cobb County GA SO — 24,600 (0.6%) | Montgomery County TX SO — 54,844 (0.7%) | Montgomery County TX SO — 48,728 (0.9%) |

**Note the 2026 shift:** California Highway Patrol jumps to #4 (4.8% share) from nowhere near the top-10 in 2024/2025 — worth a specific look at CHP's access history/rationale.

### 8.4 Justification quality by year

| Metric | 2024 | 2025 | 2026 |
|---|---|---|---|
| Org log: substantive/case#/vague/blank | 3,752 / 2,202 / 224 / 0 | 9,376 / 1,526 / 724 / 2 | 6,527 / 0 / 0 / 0 |
| Org log vague+case# combined rate | 39.2% (Jan–Aug) | 26.2% (Jan–Aug) | ~0% *(not meaningful — see §9)* |
| Network log: substantive/case#/vague/blank | 3.19M / 402,920 / 370,521 / 1 | 6.64M / 587,105 / 551,885 / 4,007 | 5.39M / 194 / 174 / 226 |

**Comparing only the two full-freeform years** (2024 vs. 2025, both real): Org-log justification quality *improved* (39.2%→26.2% vague/case#-only). 2026 cannot be compared directly — see §9.

**Officer vague-rate top6, by year** (real names):
- **2024:** Joel Galvin 67.8% (n=239), Trevor Robinson 21.1% (n=19), Matthew Winnett 14.7% (n=75), Christopher Keys 6.6% (n=122), Maria Mccracken 2.4% (n=416), Aaron Gillespie 1.8% (n=333).
- **2025:** Joel Galvin 78.3% (n=750) — *rate increased year over year*, Dewayne Kyle 18.8% (n=48), N Bakker 8.0% (n=25), Lesley Huntsinger 7.0% (n=129), John Downing 5.6% (n=1,177), Dispatcher E 3.7% (n=27).
- **2026:** all ~0% (schema change; top6 by n only, not meaningful as a ranking).

**Officer case#-only-rate top6, by year:**
- **2024:** Taylor Wolfe 100% (n=23), Miles Outon 100% (n=15), Stephanie Johnson 96.9% (n=621), James Barfield 94.2% (n=86), John Downing 86.9% (n=1,252), Timothy Rogers 84.4% (n=154).
- **2025:** Ceasar Montano 91.0% (n=166), Cheyenne Anderson 72.7% (n=11), Taylor Wolfe 70.0% (n=10), Salim Plumb 69.0% (n=187), Cassie Fears 57.8% (n=64), Timothy Rogers 56.7% (n=683).
- **2026:** all 0% (schema change).

**Network agency worst-offenders by year** (min. ~150 searches/year to filter noise):
- **2024:** Priceville AL PD 99.0% (n=5,318), East Tawakoni TX PD 98.5% (n=19,632), West Tawakoni TX PD 97.9% (n=6,026), Acworth GA PD 97.0% (n=201), Doral FL PD 96.7% (n=214), Buford City Schools GA 96.3% (n=243), North Little Rock AR PD 95.1% (n=756), Cape Girardeau County MO SO 92.7% (n=2,384).
- **2025:** Thrall City PD TX 100% (n=173), Steele AL PD 98.0% (n=452), Elm Ridge TX PD 91.6% (n=10,266), Blaine CO OK SO 91.4% (n=4,325), Austell GA PD 88.9% (n=960), Thackerville OK PD 87.4% (n=253), Powder Springs GA PD 86.6% (n=590), Georgia Attorney General's Office 85.7% (n=783).
- **2026:** Tomball TX PD 1.1% (n=1,244), Edinburg TX PD 0.6% (n=3,591), Crandall TX PD 0.5% (n=215), Lindale TX PD 0.3% (n=351), Thomas County KS SO 0.2% (n=580), Lea County NM SO 0.2% (n=645), La Vernia TX PD 0.2% (n=548), Clarksville IN PD 0.1% (n=7,855) — **note the collapse to near-zero even for the "worst" agencies**, consistent with the platform-wide reason-field change (§9), not a real behavior change at any of these specific departments.

### 8.5 Off-hours by year

| Metric | 2024 | 2025 | 2026 |
|---|---|---|---|
| Late-night baseline | 4.6% | 8.7% | 9.7% |
| Weekend baseline | 20.5% | 20.4% | 20.7% |
| Late-night blank/vague rate | 8.5% | **19.0%** | 0.0%* |
| Daytime blank/vague rate | 3.4% | 5.0% | 0.0%* |
| Weekend blank/vague rate | 7.0% | **10.9%** | 0.0%* |
| Weekday blank/vague rate | 2.7% | 5.1% | 0.0%* |

*2026 rows marked with `*` are artifacts of the January 2026 schema change (§9), not evidence that off-hours documentation became perfect — treat as "not measurable," not "zero problem."

**The late-night/daytime gap widens in 2025** (2.5× in 2024 → 3.8× in 2025) before the measurement itself breaks in 2026. This is worth flagging on its own: whatever is driving the late-night vagueness gap, it was getting *worse*, not better, right up until the reason field stopped being freeform text.

**Late-night rate top6 by year (real names):**
- **2024:** Trevor Robinson 89.5% (n=19), Steven Wheeler 40.0% (n=170), TJ Vowell-Zundel 37.0% (n=46), Tosha Whitley 31.0% (n=84), Marcus Maxie 29.0% (n=69), Christopher Bell 28.6% (n=28).
- **2025:** Marcus Maxie 75.0% (n=16), Megan Ramirez 59.1% (n=22), Eric Zimmerman 48.4% (n=31), Christopher Jones 46.7% (n=92), Austin Thompson 42.9% (n=91), Bryan Chavez 41.8% (n=146).
- **2026:** Ashley Fulton 72.7% (n=11), Joaquin Reyes 55.0% (n=20), Cheyenne Anderson 54.5% (n=44), Lesley Huntsinger 50.0% (n=110), Austin Thompson 49.8% (n=305), Payton Connatser 44.9% (n=49).

**Weekend rate top6 by year:**
- **2024:** Edward Wilcox 100% (n=25), Kevin Argueta 83.0% (n=47), Rena Laymon 80.8% (n=26), Christopher Jones 74.3% (n=35), Brooke Berger 71.6% (n=102), Ali Abbas 71.4% (n=63).
- **2025:** Brian Baker 94.1% (n=17), Eric Zimmerman 90.3% (n=31), Kevin Bell 87.7% (n=81), Dispatcher E 70.4% (n=27), Lesley Huntsinger 69.8% (n=129), Craig Stillwagon 63.9% (n=36).
- **2026:** Robyn Summers 100% (n=16), Anna Varvil 73.0% (n=37), Ashley Fulton 72.7% (n=11), Auldon Barker 63.6% (n=187), Lesley Huntsinger 59.1% (n=110), Cheyenne Anderson 54.5% (n=44).

### 8.6 Geography by year

| | 2024 | 2025 | 2026 (partial) |
|---|---|---|---|
| Texas | 1,761,194 (44.5%) | 3,485,605 (44.8%) | 2,909,441 (53.9%) |
| Other in-radius | 287,086 (7.3%) | 896,268 (11.5%) | 656,180 (12.2%) |
| Out-of-radius (>500mi) | 1,875,516 (47.4%) | 3,275,310 (42.1%) | 1,717,758 (31.8%) |
| Federal | 5,802 (0.15%) | 40,434 (0.52%) | 45,164 (0.84%) |
| Unclassified name | 30,177 (0.76%) | 83,354 (1.07%) | 66,150 (1.23%) |
| **Total** | 3,959,775 | 7,780,971 | 5,394,693 |

**Top out-of-radius agencies by year:**
- **2024:** Riverside County CA SO 40,753 (~1,309mi), Cobb County GA SO 24,600 (~767mi), Fairfax County VA PD 24,477 (~1,101mi), Mishawaka PD IN 23,303 (~753mi), Volusia County FL SO 17,892 (~977mi), Cobb County GA PD 16,738 (~767mi), Village of Lynwood IL PD 16,071 (~666mi), DeKalb County GA PD 16,029 (~767mi).
- **2025:** Louisville Metro KY PD 51,620 (~758mi), Palm Beach County FL SO 48,012 (~977mi), Hillsborough County FL SO 47,576 (~977mi), Cobb County GA PD 36,824 (~767mi), Fairfax County VA PD 32,506 (~1,101mi), Coweta County GA SO 28,635 (~767mi), Jacksonville FL SO 28,227 (~977mi), Columbus OH PD 27,175 (~930mi).
- **2026:** California Highway Patrol 260,935 (~1,309mi — huge jump from prior years), Louisville Metro KY PD 88,652, Hillsborough County FL SO 83,602, Palm Beach County FL SO 52,713, Cobb County GA PD 41,342, Lexington KY PD 38,606, Pinellas County FL SO 36,123, Arizona DPS 31,749.

**Federal by year:**
- **2024** (total 5,802, 8 distinct): ATF Nashville TN [inactive] 4,151, ATF Louisville KY [inactive] 1,227, US GSA OIG 180, Langley VA AFB 160, National Park Service TN [Inactive] 61, Wright-Patterson OH AFB 15, Lake Mead NV NRA 5, Roudebush IN VA PD 3.
- **2025** (total 40,434, 12 distinct): US Postal Inspection Service 32,786, US Border Patrol [Inactive] 3,703, ATF Nashville TN [inactive] 2,992, ATF Louisville KY [inactive] 512, Homeland Security Investigations [Inactive] 161, Naval Criminal Investigative Service [Inactive] 145, Langley VA AFB 58, US GSA OIG 57.
- **2026** (total 45,164, only **3** distinct — down from 8–12 in prior years): US Postal Inspection Service 23,452, FBI 21,440, Natchez Trace Parkway MS NPS 272. **The FBI's entire 21,440-search all-time total occurred in 2026** — it had zero presence in 2024 or 2025 federal breakdowns above. Combined with the July 2026 single-month spike (§9), FBI access at Colony is a distinctly 2026 phenomenon worth asking about directly.

---

## 9. A platform-level change in January 2026 (read before trusting any 2026 "quality" metric)

Starting with the January 2026 file, in **both** logs simultaneously:

1. **The `Reason` field stops accepting/containing freeform text almost entirely.** Values switch to fixed category strings like `"Auto Theft / VCD Investigation - Auto Theft / VCD Investigation"`, `"Wanted Person (Arrest Warrant/Fugitive) - Criminal Justice Purpose"`. Bare case numbers, single letters, "test", periods — all vanish from the data starting that month (Network log vague+numeric: Dec 2025 = 25,424+25,491; Jan 2026 = 125+129; Feb 2026 = 32+47; by May 2026, effectively zero). This is consistent with Flock switching the search UI to a **mandatory category dropdown**, not a sudden department-wide improvement in officer behavior. It's arguably a good change (it would have prevented East Tawakoni PD's single-letter pattern and Joel Galvin's "." habit had it existed earlier) — but it makes 2024/2025 vs. 2026 justification-quality numbers **not comparable**.
2. **The number of distinct outside agencies searching Colony's cameras per month drops ~74%**, from an average ~3,385/month in 2025 to ~891/month in 2026 (Jan–Jul), while total search *volume* kept climbing the whole time. Access became concentrated in far fewer, larger partner agencies rather than actually shrinking. (Verified this isn't a parsing artifact: agencies with ≤2 lifetime searches in a sample month dropped from 370 in March 2025 to 22 in March 2026 — a real change in agency participation, not a naming-convention break in the new files.)

Both changes land on the exact same month boundary, across both independently-exported logs — strong evidence of one platform-level event, not a Colony policy decision, but **this is an inference from the data pattern, not a confirmed fact**. Recommend asking the department (or Flock directly) to confirm what changed in January 2026 and why. If a future document arrives that describes a Flock platform update, product change, or new agency-onboarding process around that date, it would confirm or refute this reading.

**Practical implication for continued analysis:** any 2026 figure involving Reason-field content (vague%, case#-only%, "worst offender" agency rankings) should be treated as measuring something different than the same metric in 2024/2025 — not "got better," but "can no longer occur in this form." Volume, geography, timing, and repeated-target metrics are unaffected by this change and remain comparable across all three years.

**Separately:** July 2026 saw a spike to 21,744 federal-tagged searches in one month (vs. low-thousands in adjacent months), of which 18,417 was FBI alone — the FBI's entire visible presence in this dataset is concentrated in 2026, with none in 2024/2025 (§8.6). Two distinct, unexplained step-changes in federal access, both worth a direct question to the department.

---

## 10. Questions this dataset can answer — asked and answered

| Question | Answer | Where |
|---|---|---|
| Is anyone searching the same plate repeatedly without a real case — the pattern linked to stalking elsewhere? | **Yes, at low volume.** 28 (officer, plate) pairs, manual searches, 14 days–15 months apart, no case number ever recorded. Concentrated in Joel Galvin, John Downing, Stephanie Johnson, Simon Wilcock. Not high-volume — the highest-volume repeat pattern (964 hits) looks automated/case-linked instead. | §5 |
| Are people accessing the system at odd hours, and does that look different from daytime use? | **Yes, measurably.** Late-night share of activity roughly doubled 2024→2025 and held. Once the case-number habit is excluded, late-night searches are 3.4× (all-time), up to 3.8× (2025) more likely to carry no real reason than daytime. | §6, §8.5 |
| How does 2024 vs. 2025 vs. 2026 compare? | Explosive growth 2024→2025 (+83–128%), then plateau/slight decline into 2026. Out-of-radius share fell as a % even as its absolute volume grew. Federal share rose ~5×. Distinct partner agencies collapsed 74% starting Jan 2026. | §8 |
| Has justification quality gotten better or worse over time? | Improved 2024→2025 in the two comparable freeform years (39.2%→26.2% Org-log vague/case#-only). 2026 is not measurable the same way — see §9. | §8.4, §9 |
| Is network exposure to outside agencies growing or shrinking? | All three are simultaneously true: absolute out-of-radius volume grew every year; its *share* of a faster-growing total shrank; the *number* of distinct agencies with any access collapsed 74% in 2026. No single-number summary is honest — present all three. | §7, §8.1, §8.6 |
| Is ICE or CBP involved? | No entry anywhere is tagged ICE or CBP. Border Patrol and Homeland Security Investigations both appear but are marked inactive (access later revoked). FBI and USPIS are the only agencies with meaningful active federal access — and FBI's entire presence is concentrated in 2026, including an unexplained 18,417-search spike in July 2026 alone. | §7, §8.6, §9 |
| Can the data distinguish manual curiosity-driven searches from automated hotlist hits? | Partially, via `Search Type` (`search` = manual, `lookup` = often hotlist-automated). This is what separates the 964-hit hotlist case from the 28-pair sustained list (mostly manual). Can't read intent behind a manual search. | §5, §12 |
| Do Colony's own officers reach into far-away out-of-state networks too? | Yes — the `Filters` field shows voluntary searches scoped to Arkansas, Georgia, Florida, Oklahoma, Illinois by Colony officers, not just Texas. The access relationship is bidirectional. | §7 |
| Is one officer/agency responsible for a disproportionate share of activity, and is that changing? | Yes and it shifts: John Downing dominates 2024 (20.3% of all Org-log searches that year); Kreig Wallace (driven by the hotlist case) dominates 2025; Maria Mccracken/Domingo Rios lead 2026 so far. Houston TX PD is consistently #1 agency every year (9.2–11.3% share). | §4, §8.2, §8.3 |
| What changed around January 2026, and does it explain other anomalies? | A platform-level reason-field format change, plus a ~74% drop in distinct partner agencies, land on the exact same month across both independently-produced logs — very likely one underlying event. Not yet confirmed with the department. | §9 |

---

## 11. Summary of what deserves follow-up (priority order)

1. **Joel Galvin's justification pattern** — 66% of his searches (all-time), 78% in 2025 alone, carry no real reason, mostly a literal "." repeated across dozens of plates. The single strongest, most explainable-or-not finding in the dataset.
2. **The 28-pair sustained no-case repeat-target list** (§5) — the pattern most resembling personal/stalking-adjacent interest, concentrated in 5 officers. Low volume by design (3–16 hits each), which is itself the tell.
3. **The January 2026 platform change** (§9) — confirm with the department/Flock. Explains both the vague-reason collapse and the 74% drop in distinct partner agencies; without confirmation, both look like anomalies rather than a UI change.
4. **The 964-search hotlist hit** (§5) — confirm it's automated, and pull the underlying case file (sc25-29/sc25-31) given the scale either way.
5. **FBI access concentrated entirely in 2026**, including an unexplained 18,417-search July 2026 spike (§8.6, §9) — ask directly what happened.
6. **The late-night reason-quality gap widened 2024→2025** (2.5×→3.8×) right up until the measurement broke in 2026 (§8.5) — worth knowing whether it's still widening under the new category system, which would require the department's help to assess since the current data can't measure it the same way anymore.
7. **East/West Tawakoni PD's single-character "reasons"** (§3) — ask whether Colony's data-sharing agreement has any reason-field quality requirement for partner agencies.
8. **The ~40% out-of-500-mile network share** (§7) — the plainest, most quantifiable gap vs. the department's public "Texas/500 miles" claim, independent of any individual-search judgment call.
9. **The case-number-in-Reason-field habit** — most visible in John Downing (60%) but more consistent in Stephanie Johnson (97%) and James Barfield (84%). A training/workflow fix, not misuse, but it means Reason text can't audit these officers without pulling linked case numbers separately.

---

## 12. Methodology (exact, reproducible)

- **Vague/generic reason terms** (case-insensitive exact match, or any reason ≤2 characters): `check, checking, test, n/a, na, asdf, x, misc, other, unk, unknown, lookup, look up, verify, verifying, ., -, none, review, follow up, following up, fyi, see above, pd, ok, k, ?, idk, tbd`.
- **"Numeric/case-number-only"**: regex `^[\d\-\/#\.\s]+$` (digits, dashes, slashes, #, periods, whitespace only) on the trimmed Reason string.
- **Off-hours window**: 1:00–5:00am Central Time. UTC→Central conversion is DST-aware but computed manually (first-Sunday-of-November / second-Sunday-of-March rule) rather than via `zoneinfo`, because this environment's Python lacks the `tzdata` package.
- **Out-of-radius threshold**: >500 miles, straight-line (haversine) distance from The Colony, TX (33.0812, −96.8994) to each US state's population centroid. Manually corrected for agencies whose city is far from their state's centroid — currently only Memphis/Shelby County TN (417mi actual vs. 610mi if using Tennessee's centroid). **This is a screening tool, not survey-grade** — check any other border-state agency individually before treating its classification as certain.
- **Federal classification**: primary signal is the literal `[Federal]` bracket tag in the source Org Name (present in the raw data itself). Fallback: word-boundary match on `ICE|CBP|HSI|DEA|FBI|ATF` (boundary is essential — an earlier version matched `ICE` as a substring of "Police" and miscategorized every state police agency as federal) plus phrase match on things like "border patrol", "postal inspection", "federal bureau of investigation".
- **Stalking-risk composite score** (per officer/plate pair, min. 3 searches): `manual_frac × (0.4 if ever has a case# else 1.0) × (0.3 + 0.7×vague_frac) × (1 + min(span_days/30, 6)) × (1 + late_frac + weekend_frac×0.5)`. All five component values are always shown alongside the score (§5's table) so the ranking can be second-guessed rather than trusted blindly. "Sustained" = span ≥14 days; a separate lower-priority bucket covers same-day/short-span bursts.
- **Monthly/yearly bucketing**: by source filename (`TheColonyTXPD_{network|org}_{Mon}_{YYYY}.csv`), verified each file is cleanly bounded to its calendar month — no need to re-parse every row's timestamp for month/year grouping (only needed for hour/weekday-of-week analysis within a file).
- **Min. sample thresholds**: officer-level rate rankings require ≥30 searches (all-time) or ≥10 (single-year) to appear in a "top offenders" list, to suppress small-sample noise. Agency-level vague-rate rankings require ≥500 lifetime searches (all-time) or ≥150 (single-year).

---

## 13. Artifacts, reproducibility, and where things live

- **This document** (`audit_log_analysis.md`) — full analysis, real names, for internal use. Stays local / does not get pushed anywhere public.
- **`index.html`** (same directory) — public-facing, interactive version with charts, a 2024/2025/2026 filter (on Justification/Volume/Off-Hours/Out-of-Network tabs only), and all individual officers replaced with anonymized `Officer-NN` codes. Built from the same underlying data as this document. Hosted on GitHub Pages by the user.
- **`officer_id_mapping_PRIVATE.md`** (one directory **above** `flock_857_the_colony_tx_pd/`, i.e. `C:\Projects\Flock\officer_id_mapping_PRIVATE.md`) — the real-name ↔ `Officer-NN` code table for the public HTML. 56 officers mapped (27 from the original all-time top lists, ordered by volume; 29 more added when per-year breakdowns surfaced additional names, ordered alphabetically). **Do not commit this file to the GitHub repo that hosts `index.html`.**
- **`analysis/scripts/`** and **`analysis/data/`** (inside `flock_857_the_colony_tx_pd/`) — every Python script used to produce every number in this document, plus cached JSON outputs of each. See `analysis/README.md` for a full script-by-script index, run order, and the exact constants/thresholds used (duplicated in §12 above for convenience, but the README is the canonical copy — update both if you change a threshold). **Re-running the full 17.1M-row network scan takes ~30-40 seconds** on this data; everything else is near-instant. No third-party packages required (standard library only: `csv`, `re`, `json`, `collections`, `datetime`).
- **Raw source data**: `TheColonyTXPD-Network/` (3.4GB, 32 monthly CSVs, redacted names/plates) and `TheColonyTXPD-Org/` (5.4MB, 32 monthly CSVs, unredacted) — both siblings of this file.

### Suggested next steps for a continuing session

- If you receive department policy documents, data-sharing agreements, or Flock contract terms: check them against the "Texas/500 miles" framing (§7) and against whether individual-agency reason-field quality is contractually required (relevant to the Tawakoni PDs, §3).
- If you receive duty rosters or shift schedules: cross-reference against the off-hours officer lists in §6/§8.5 — this is the single biggest open caveat in the whole analysis (can't currently distinguish shift assignment from unusual behavior).
- If you receive anything about a Flock platform update, UI change, or new agency-onboarding process in Jan 2026: it would directly confirm or refute §9's inference.
- If you receive CAD/RMS case records: the case numbers embedded in Reason-field text throughout (e.g. `sc25-31`, `2024-17788`) could be cross-referenced to check whether the 28 sustained-repeat pairs in §5 ever got a real case opened after the fact, even if not logged in Flock at the time.
- If new monthly export files arrive (Sep 2026 onward): `analysis/scripts/network_monthly.py` and `org_monthly.py` can be re-run as-is against the extended file set (just don't forget Aug 2026 is partial — check whether a new Aug 2026 file replaces it with the full month before re-aggregating).
