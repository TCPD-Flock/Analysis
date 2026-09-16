import csv, glob, os, json
from collections import Counter, defaultdict

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Org"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

# targets to deep-dive: (officer, plate) pairs from prior run's top list
targets = [
    ("Kreig  Wallace", "RJV4631"),
    ("Timothy  Rogers", "RJV4631"),
    ("Trevor Strong", "RJV4631"),
    ("Austin Thompson", None),  # unknown plate, will discover
    ("Kreig  Wallace", None),   # second Kreig plate (hash 31612)
    ("Kreig  Wallace", None),   # third Kreig plate (hash 58327)
    ("Domingo Rios", None),
]

# Instead: recompute full detail keyed by (officer,plate) for ALL pairs with count>=30, store search_type counter, case set, date min/max, file list
detail = defaultdict(lambda: {'count':0, 'search_type': Counter(), 'cases': set(), 'dates': [], 'files': set(), 'reasons': Counter()})

for fp in files:
    fname = os.path.basename(fp)
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
            d['search_type'][search_type] += 1
            if case_num: d['cases'].add(case_num)
            d['dates'].append(search_time)
            d['files'].add(fname)
            d['reasons'][reason.lower()] += 1

# filter to count>=25, sort desc
rows = [(k,v) for k,v in detail.items() if v['count']>=25]
rows.sort(key=lambda kv: -kv[1]['count'])

out = []
for (name,plate), v in rows[:20]:
    dates_sorted = sorted(v['dates'])
    out.append({
        'officer': name,
        'plate_last4': plate[-4:],
        'count': v['count'],
        'search_type': dict(v['search_type']),
        'num_distinct_cases': len(v['cases']),
        'case_sample': list(v['cases'])[:5],
        'first_date': dates_sorted[0] if dates_sorted else None,
        'last_date': dates_sorted[-1] if dates_sorted else None,
        'num_files_spanned': len(v['files']),
        'top_reasons': v['reasons'].most_common(5),
    })

for o in out:
    print(json.dumps(o, indent=2))

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\target_deepdive.json", 'w') as f:
    json.dump(out, f, indent=2)
