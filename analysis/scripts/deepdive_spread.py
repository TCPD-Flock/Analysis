import csv, glob, os, json, re
from collections import Counter, defaultdict
from datetime import datetime

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Org"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

VAGUE = {
    'check','checking','test','n/a','na','asdf','x','misc','other','unk','unknown',
    'lookup','look up','verify','verifying','.','-','none','review','follow up',
    'following up','fyi','see above','pd','ok','k','?','idk','tbd'
}
NUMERIC_RE = re.compile(r'^[\d\-\/#\.\s]+$')

def parse_time(s):
    s=s.strip()
    if not s: return None
    try:
        return datetime.strptime(s.replace(' UTC',''), '%m/%d/%Y, %I:%M:%S %p')
    except Exception:
        return None

detail = defaultdict(lambda: {'count':0, 'cases': set(), 'dts': [], 'reasons': Counter(), 'search_types': Counter()})

for fp in files:
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if len(row) < 13: continue
            name = row[1].strip()
            plate = row[5].strip().upper()
            if not plate: continue
            case_num = row[7].strip()
            search_time = row[9].strip()
            search_type = row[10].strip()
            reason = row[6].strip()
            key = (name, plate)
            d = detail[key]
            d['count'] += 1
            if case_num: d['cases'].add(case_num.lower())
            dt = parse_time(search_time)
            if dt: d['dts'].append(dt)
            d['reasons'][reason.lower()] += 1
            d['search_types'][search_type] += 1

candidates = []
for (name,plate), v in detail.items():
    if v['count'] < 4:
        continue
    if not v['dts']:
        continue
    span_days = (max(v['dts']) - min(v['dts'])).days
    if span_days < 14:
        continue  # only interested in long-spread patterns
    # vagueness: fraction of reasons that are blank/vague/numeric-only
    vague_n = 0
    for r_,c_ in v['reasons'].items():
        if r_ == '' or r_ in VAGUE or len(r_) <= 2 or NUMERIC_RE.match(r_):
            vague_n += c_
    vague_frac = vague_n / v['count']
    candidates.append({
        'officer': name, 'plate_last4': plate[-4:], 'count': v['count'],
        'span_days': span_days, 'num_distinct_cases': len(v['cases']),
        'vague_frac': round(vague_frac,2),
        'top_reasons': v['reasons'].most_common(5),
        'search_types': dict(v['search_types']),
        'first': min(v['dts']).isoformat(), 'last': max(v['dts']).isoformat(),
    })

# sort by span_days desc then by low case count / high vague_frac as interest signal
candidates.sort(key=lambda c: (-c['span_days'], -c['vague_frac']))
print("total long-spread (officer,plate) pairs (span>=14d, count>=4):", len(candidates))
for c in candidates[:25]:
    print(json.dumps(c, indent=2))

# Also specifically: no case number AND high vague fraction AND long span -> strongest "worth a human look" candidates
suspect = [c for c in candidates if c['num_distinct_cases']==0 and c['vague_frac']>=0.5]
suspect.sort(key=lambda c: -c['count'])
print("\n=== no-case + vague-reason + long-span candidates ===")
for c in suspect[:25]:
    print(json.dumps(c, indent=2))

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\spread_candidates.json",'w') as f:
    json.dump({'all_long_spread': candidates[:100], 'suspect': suspect[:50]}, f, indent=2)
