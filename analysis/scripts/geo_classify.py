import json, re

d = json.load(open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\network_analysis.json"))
dist = json.load(open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\state_distances.json"))
org_counts = d['all_org_counts']

STATE_NAMES = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO',
    'Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID',
    'Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA',
    'Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS',
    'Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ',
    'New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK',
    'Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD',
    'Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA',
    'West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY',
}
ABBR_SET = set(dist.keys())

FEDERAL_BRACKET = '[federal]'
FEDERAL_WORDBOUND = ['ICE', 'CBP', 'HSI', 'DEA', 'FBI', 'ATF']  # short acronyms: require word boundaries
FEDERAL_PHRASES = ['border patrol', 'homeland security investigations', 'us marshal', 'u.s. marshal',
                    'secret service', 'postal inspection', 'customs and border', 'immigration and customs',
                    'federal bureau of investigation', 'drug enforcement administration',
                    'bureau of alcohol, tobacco', 'internal revenue service', 'irs criminal investigation']

def classify(org):
    lo = org.lower()
    if FEDERAL_BRACKET in lo:
        return ('FEDERAL', None)
    for ph in FEDERAL_PHRASES:
        if ph in lo:
            return ('FEDERAL', None)
    for kw in FEDERAL_WORDBOUND:
        if re.search(r'\b' + kw + r'\b', org):  # case-sensitive: acronyms are upper-case in source data
            return ('FEDERAL', None)
    # 2-letter state token
    tokens = org.replace(',', ' ').split()
    for t in tokens:
        tt = t.strip('.')
        if tt in ABBR_SET:
            return ('STATE', tt)
    for name, ab in STATE_NAMES.items():
        if name in org:
            return ('STATE', ab)
    return ('UNKNOWN', None)

federal = []
unknown = []
by_state = {}
for org, c in org_counts.items():
    kind, st = classify(org)
    if kind == 'FEDERAL':
        federal.append((org, c))
    elif kind == 'STATE':
        by_state.setdefault(st, []).append((org, c))
    else:
        unknown.append((org, c))

federal.sort(key=lambda x: -x[1])
unknown.sort(key=lambda x: -x[1])

print("=== FEDERAL agencies ===")
tot_fed = 0
for org, c in federal:
    print(f"  {org}: {c}")
    tot_fed += c
print("total federal searches:", tot_fed, "count of distinct federal orgs:", len(federal))

print("\n=== State summary (searches, distinct orgs, distance from Colony TX) ===")
state_summary = []
for st, orgs in by_state.items():
    total = sum(c for _,c in orgs)
    state_summary.append((st, total, len(orgs), dist.get(st)))
state_summary.sort(key=lambda x: -x[1])
for st, total, n, d_ in state_summary:
    flag = "OUTSIDE 500mi" if (d_ is not None and d_>500) else ""
    print(f"  {st}: searches={total} distinct_orgs={n} dist_mi={d_} {flag}")

print("\ntotal searches classified by state:", sum(x[1] for x in state_summary))
print("\n=== UNKNOWN / unclassified org names (top 40 by volume) ===")
for org, c in unknown[:40]:
    print(f"  {org}: {c}")
print("total unknown searches:", sum(c for _,c in unknown), "distinct unknown orgs:", len(unknown))

# Out-of-radius agency detail, top by volume
out_of_radius = []
for st, orgs in by_state.items():
    d_ = dist.get(st)
    if d_ is not None and d_ > 500:
        for org, c in orgs:
            out_of_radius.append((org, st, d_, c))
out_of_radius.sort(key=lambda x: -x[3])
print("\n=== Individual out-of-500mi agencies, top 30 by volume ===")
for org, st, d_, c in out_of_radius[:30]:
    print(f"  {org} ({st}, ~{d_}mi): {c}")
print("total out-of-radius searches:", sum(x[3] for x in out_of_radius), "distinct out-of-radius orgs:", len(out_of_radius))

out = {
    'federal': federal, 'total_federal_searches': tot_fed,
    'state_summary': state_summary,
    'unknown_top40': unknown[:40], 'total_unknown_searches': sum(c for _,c in unknown), 'unknown_org_count': len(unknown),
    'out_of_radius_top30': out_of_radius[:30],
    'total_out_of_radius_searches': sum(x[3] for x in out_of_radius),
    'out_of_radius_org_count': len(out_of_radius),
}
with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\geo_classification.json", 'w') as f:
    json.dump(out, f, indent=2)
