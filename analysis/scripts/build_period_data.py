import json, re, os

DATA_DIR = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data"

def norm(name):
    return re.sub(r'\s+', ' ', name).strip()

MAP = json.load(open(os.path.join(DATA_DIR, 'full_officer_mapping.json')))
def code(name):
    n = norm(name)
    if n not in MAP:
        raise KeyError(n)
    return f"Officer-{MAP[n]:02d}"

org_y = json.load(open(os.path.join(DATA_DIR, 'org_yearly.json')))
net_y = json.load(open(os.path.join(DATA_DIR, 'network_yearly.json')))
geo_rs = json.load(open(os.path.join(DATA_DIR, 'yearly_reason_geo.json')))
cls = json.load(open(os.path.join(DATA_DIR, 'org_classification_full.json')))

FED_STATUS = {
    'US Postal Inspection Service': 'active',
    'Federal Bureau of Investigation (FBI)': 'active',
    'ATF Nashville TN': 'inactive',
    'US Border Patrol': 'inactive',
    'ATF Louisville KY': 'inactive',
    'Homeland Security Investigations': 'inactive',
    'National Park Service TN': 'inactive',
}
def fed_status(org):
    for k,v in FED_STATUS.items():
        if k in org: return v
    if 'inactive' in org.lower() or '[inactive]' in org.lower() or 'deactivated' in org.lower():
        return 'inactive'
    return 'active'

PERIODS = ['all','2024','2025','2026']
period_key_map = {'all':'all','2024':'2024','2025':'2025','2026':'2026'}

out = {}
for p in PERIODS:
    o = org_y[p]
    n = net_y[p]
    rg_net = geo_rs['network'][p]
    rg_org = geo_rs['org'][p]

    # --- org reason breakdown ---
    orgReason = {
        'substantive': rg_org['total'] - rg_org['vague'] - rg_org['numeric'] - rg_org['blank'],
        'caseNumber': rg_org['numeric'], 'vague': rg_org['vague'], 'blank': rg_org['blank'],
        'total': rg_org['total'],
    }
    netReason = {
        'substantive': rg_net['total'] - rg_net['vague'] - rg_net['numeric'] - rg_net['blank'],
        'caseNumber': rg_net['numeric'], 'vague': rg_net['vague'], 'blank': rg_net['blank'],
        'total': rg_net['total'],
    }
    reasonSuppressed = (p == '2026')  # dropdown UI change makes this not meaningful

    # --- officer rate lists (coded) ---
    def coded_rate_list(lst):
        return [{'officer': code(name), 'rate': rate, 'n': n_} for name, rate, n_ in lst]

    officerVague = coded_rate_list(o['officer_vague_rate_top6'])
    officerNumeric = coded_rate_list(o['officer_numeric_rate_top6'])
    lateTop = coded_rate_list(o['officer_late_rate_top6'])
    weekendTop = coded_rate_list(o['officer_weekend_rate_top6'])

    lateBaseline = round(o['late_total']/o['grand_total']*100, 1) if o['grand_total'] else 0
    weekendBaseline = round(o['weekend_total']/o['grand_total']*100, 1) if o['grand_total'] else 0

    xt = o['xtab']
    def pct(a,b): return round(a/b*100,1) if b else 0
    xtab = {
        'lateBad': pct(xt.get('late_bad',0), xt.get('late_total',0)),
        'dayBad': pct(xt.get('day_bad',0), xt.get('day_total',0)),
        'weekendBad': pct(xt.get('weekend_bad',0), xt.get('weekend_total',0)),
        'weekdayBad': pct(xt.get('weekday_bad',0), xt.get('weekday_total',0)),
    }

    # --- top officers (volume) with % of period total ---
    topOfficers = [{'officer': code(name), 'count': c, 'pct': round(c/o['grand_total']*100,1)}
                   for name,c in o['officer_total_top10']]

    # --- top agencies (volume) with % of period total ---
    org_counts = n['org_counts']
    org_vague_counts = n['org_vague']
    period_total = n['total_rows']
    top_agencies_sorted = sorted(org_counts.items(), key=lambda x:-x[1])[:10]
    topAgencies = [{'org': org, 'count': c, 'pct': round(c/period_total*100,1)} for org,c in top_agencies_sorted]

    # --- network vague-rate worst offenders ---
    min_total = 500 if p=='all' else 150
    rows = []
    for org, tot in org_counts.items():
        if tot < min_total: continue
        vc = org_vague_counts.get(org,0)
        rows.append((org, round(vc/tot*100,1), tot))
    rows.sort(key=lambda x:-x[1])
    netVagueWorst = [{'org': r[0], 'rate': r[1], 'n': r[2]} for r in rows[:8]]
    netVagueSuppressed = (p == '2026')

    # --- geo composition ---
    geo = {
        'tx': rg_net['tx'], 'otherInRadius': rg_net['total']-rg_net['tx']-rg_net['out_of_radius']-rg_net['federal']-rg_net['unknown_org'],
        'outOfRadius': rg_net['out_of_radius'], 'federal': rg_net['federal'], 'unknown': rg_net['unknown_org'],
        'total': rg_net['total'],
    }

    # --- out of radius top agencies ---
    rows = []
    for org, c in org_counts.items():
        info = cls.get(org)
        if info and info.get('out_of_radius'):
            rows.append((org, c, info.get('distance')))
    rows.sort(key=lambda x:-x[1])
    outOfRadiusTop = [{'org': r[0], 'count': r[1], 'dist': r[2]} for r in rows[:8]]

    # --- federal table ---
    rows = []
    for org, c in org_counts.items():
        info = cls.get(org)
        if info and info.get('kind')=='FEDERAL':
            rows.append((org, c))
    rows.sort(key=lambda x:-x[1])
    federalTop = [{'org': r[0], 'count': r[1], 'status': fed_status(r[0])} for r in rows[:8]]
    federalTotal = sum(c for _,c in rows)
    federalDistinct = len(rows)

    out[p] = {
        'orgReason': orgReason, 'netReason': netReason, 'reasonSuppressed': reasonSuppressed,
        'officerVague': officerVague, 'officerNumeric': officerNumeric,
        'lateTop': lateTop, 'weekendTop': weekendTop, 'lateBaseline': lateBaseline, 'weekendBaseline': weekendBaseline,
        'xtab': xtab,
        'topOfficers': topOfficers, 'officerGrandTotal': o['grand_total'],
        'topAgencies': topAgencies, 'agencyGrandTotal': period_total,
        'netVagueWorst': netVagueWorst, 'netVagueSuppressed': netVagueSuppressed,
        'geo': geo,
        'outOfRadiusTop': outOfRadiusTop,
        'federalTop': federalTop, 'federalTotal': federalTotal, 'federalDistinct': federalDistinct,
    }

with open(os.path.join(DATA_DIR, 'period_data.json'), 'w') as f:
    json.dump(out, f, indent=1)

print("Built period_data.json")
for p in PERIODS:
    print(p, "org total:", out[p]['officerGrandTotal'], "net total:", out[p]['agencyGrandTotal'],
          "netVagueSuppressed:", out[p]['netVagueSuppressed'])
