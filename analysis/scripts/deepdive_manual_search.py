import csv, glob, os, json
from collections import Counter, defaultdict

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Org"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

detail = defaultdict(lambda: {'count':0, 'cases': set(), 'dates': [], 'files': set(), 'reasons': Counter()})

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
            if search_type not in ('search', 'search - Mobile'):
                continue
            key = (name, plate)
            d = detail[key]
            d['count'] += 1
            if case_num: d['cases'].add(case_num)
            d['dates'].append(search_time)
            d['files'].add(fname)
            d['reasons'][reason.lower()] += 1

rows = [(k,v) for k,v in detail.items() if v['count']>=5]
rows.sort(key=lambda kv: -kv[1]['count'])
print("num (officer,plate) pairs with >=5 manual 'search' type hits:", len(rows))

out = []
for (name,plate), v in rows[:25]:
    dates_sorted = sorted(v['dates'])
    out.append({
        'officer': name,
        'plate_last4': plate[-4:],
        'count': v['count'],
        'num_distinct_cases': len(v['cases']),
        'case_sample': list(v['cases'])[:5],
        'first_date': dates_sorted[0] if dates_sorted else None,
        'last_date': dates_sorted[-1] if dates_sorted else None,
        'num_files_spanned': len(v['files']),
        'top_reasons': v['reasons'].most_common(5),
    })

for o in out:
    print(json.dumps(o, indent=2))

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\manual_search_deepdive.json", 'w') as f:
    json.dump(out, f, indent=2)
