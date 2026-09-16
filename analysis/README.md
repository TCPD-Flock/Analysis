# Analysis scripts & cached data

Supporting material behind `../audit_log_analysis.md`. Everything here is reproducible from the raw CSVs in `../TheColonyTXPD-Network/` and `../TheColonyTXPD-Org/` — the `data/` folder just caches expensive results (the network log is 17.1M rows / 3.4GB; a full scan takes ~25-40s, so no need to redo it to check a number).

## scripts/

Run from anywhere (they use absolute paths to the CSV source dirs and to `../data/`). Python 3, standard library only (`csv`, `re`, `json`, `collections`, `datetime`) — no pandas, nothing to install.

| Script | What it does | Output |
|---|---|---|
| `analyze_org.py` | Full pass over the Org log: officer volume, reason-quality classification, repeated (officer,plate) target counts, off-hours histograms | `org_analysis.json` |
| `analyze_network.py` | Full pass over the Network log: agency volume, reason-quality, search-type breakdown, hour/weekday histograms | `network_analysis.json` |
| `state_distance.py` | Haversine distance from The Colony, TX to every US state's centroid | `state_distances.json` |
| `geo_classify.py` | Classifies every network-log agency as TX / other in-radius / out-of-radius (>500mi) / federal / unknown, using `state_distances.json` | `geo_classification.json` |
| `org_classify_full.py` | Same classification, but for **every** agency (not just top-N) — used for per-year breakdowns | `org_classification_full.json` |
| `deepdive_targets.py` | Full detail on the top repeated (officer,plate) pairs (search-type mix, case numbers, date range) | `target_deepdive.json` |
| `deepdive_manual_search.py` | Same, restricted to manual `search`/`search - Mobile` type only (excludes likely-automated `lookup` hits) | `manual_search_deepdive.json` |
| `deepdive_spread.py` | Long-duration (14+ day span) repeated-target candidates, with vagueness/case-number scoring | `spread_candidates.json` |
| `off_hours.py` | Department-wide and per-officer late-night (1-5am local)/weekend search share, DST-aware UTC→Central conversion | `off_hours.json` |
| `org_deep.py` | The full stalking-risk composite score (all 1,785 officer/plate pairs, 3+ searches) + the off-hours reason-quality cross-tab (blank/vague rate by time-of-day) + monthly Org breakdown | `stalking_risk.json`, `org_monthly.json` |
| `network_monthly.py` | Monthly Network log time series: volume, reason-quality, geo composition, federal count, distinct-agency count | `network_monthly.json` |
| `org_yearly.py` | Same as `org_deep.py` but bucketed by year (2024/2025/2026) instead of month, plus per-year officer top-lists | `org_yearly.json` |
| `network_yearly.py` | Per-year (and all-time) org_counts + org_vague_counts for every agency — the base data for per-year "top agencies" and "worst justification" lists | `network_yearly.json` |
| `build_period_data.py` | Consolidates `org_yearly.json` + `network_yearly.json` + `yearly_reason_geo.json` + `org_classification_full.json` into the single `period_data.json` blob the HTML report's year-filter reads. Applies officer anonymization codes from `full_officer_mapping.json`. | `period_data.json` |
| `find_examples.py` | Grabs one example row (file + ID) per named finding, for citation | prints to stdout |
| `check_reason_orgs.py` | Pulls raw `Reason` text distribution for specific named agencies (used to confirm the Tawakoni single-character pattern and Fort Worth's radio-code shorthand) | prints to stdout |

**Run order if reproducing from scratch:** `state_distance.py` → `analyze_org.py` + `analyze_network.py` → `geo_classify.py` + `org_classify_full.py` → `off_hours.py` → `org_deep.py` → `network_monthly.py` → `org_yearly.py` + `network_yearly.py` (this one takes the ~30s full scan) → `build_period_data.py`. The deepdive/find_examples/check_reason_orgs scripts are standalone lookups, run any time.

## data/

Cached JSON outputs of the scripts above, keyed by the field names used inside each script (not identical schemas between files — check the producing script). `full_officer_mapping.json` is the real-name → `Officer-NN` code table used only for the public HTML; the analysis in `audit_log_analysis.md` uses real names throughout.

## Key constants baked into these scripts (change here if you disagree with them)

- **Vague/generic reason list**: `check, checking, test, n/a, na, asdf, x, misc, other, unk, unknown, lookup, look up, verify, verifying, ., -, none, review, follow up, following up, fyi, see above, pd, ok, k, ?, idk, tbd` (case-insensitive), plus any reason ≤2 characters.
- **"Numeric/case-number-only" reason**: matches regex `^[\d\-\/#\.\s]+$` — digits, dashes, slashes, #, periods, whitespace only.
- **Off-hours window**: 1:00–5:00 AM Central Time (America/Chicago, DST computed manually — see `off_hours.py`'s `us_central_offset_hours()`, since this machine's Python lacks the `tzdata` package for `zoneinfo`).
- **"Out of radius"**: state-centroid haversine distance > 500 miles from The Colony, TX (33.0812, -96.8994), with manual overrides in `org_classify_full.py`'s `CITY_OVERRIDES` dict for agencies whose actual city is far from their state's centroid (currently just Memphis/Shelby County TN, at 417mi vs. Tennessee's 610mi centroid distance — add more here if you spot other mismatches, e.g. a west-Texas-adjacent New Mexico or Oklahoma agency).
- **Federal classification**: bracket tag `[Federal]` in the org name (primary signal, from the source data itself), plus a fallback word-boundary match on `ICE|CBP|HSI|DEA|FBI|ATF` and phrase match on things like "border patrol", "postal inspection" — **the word-boundary requirement matters**: an earlier version of this matched `ICE` as a substring and miscategorized every "...State Police..." agency as federal. If you touch `FEDERAL_WORDBOUND`, keep the `\b` boundaries.
- **Stalking-risk composite score** (`org_deep.py`): `manual_frac × (0.4 if ever has a case# else 1.0) × (0.3 + 0.7×vague_frac) × (1 + min(span_days/30, 6)) × (1 + late_frac + weekend_frac×0.5)`. Deliberately transparent/inspectable rather than a black box — the report always shows the component parts (span, vague%, late%, weekend%, manual%) alongside the score.
