import json, re, math

net = json.load(open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\network_analysis.json"))
dist = json.load(open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\state_distances.json"))
org_counts = net['all_org_counts']

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
FEDERAL_WORDBOUND = ['ICE', 'CBP', 'HSI', 'DEA', 'FBI', 'ATF']
FEDERAL_PHRASES = ['border patrol', 'homeland security investigations', 'us marshal', 'u.s. marshal',
                    'secret service', 'postal inspection', 'customs and border', 'immigration and customs',
                    'federal bureau of investigation', 'drug enforcement administration',
                    'bureau of alcohol, tobacco', 'internal revenue service', 'irs criminal investigation']

# Manual city-level corrections established during prior analysis (straight-line mi from The Colony, TX)
CITY_OVERRIDES = {
    'Memphis TN PD': 417, 'Shelby County TN SO': 417,
}

def classify(org):
    lo = org.lower()
    if FEDERAL_BRACKET in lo:
        return {'kind':'FEDERAL','state':None,'distance':None,'out_of_radius':False}
    for ph in FEDERAL_PHRASES:
        if ph in lo:
            return {'kind':'FEDERAL','state':None,'distance':None,'out_of_radius':False}
    for kw in FEDERAL_WORDBOUND:
        if re.search(r'\b'+kw+r'\b', org):
            return {'kind':'FEDERAL','state':None,'distance':None,'out_of_radius':False}
    st = None
    tokens = org.replace(',', ' ').split()
    for t in tokens:
        tt = t.strip('.')
        if tt in ABBR_SET:
            st = tt; break
    if st is None:
        for name, ab in STATE_NAMES.items():
            if name in org:
                st = ab; break
    if st is None:
        return {'kind':'UNKNOWN','state':None,'distance':None,'out_of_radius':False}
    d = CITY_OVERRIDES.get(org, dist.get(st))
    return {'kind':'STATE','state':st,'distance':d,'out_of_radius': d is not None and d>500}

full = {org: classify(org) for org in org_counts.keys()}
with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\org_classification_full.json", 'w') as f:
    json.dump(full, f, indent=1)

# sanity check totals
tot_out = sum(org_counts[o] for o,c in full.items() if c['out_of_radius'])
tot_fed = sum(org_counts[o] for o,c in full.items() if c['kind']=='FEDERAL')
tot_unk = sum(org_counts[o] for o,c in full.items() if c['kind']=='UNKNOWN')
print('out_of_radius total:', tot_out)
print('federal total:', tot_fed)
print('unknown total:', tot_unk)
print('distinct orgs:', len(full))
