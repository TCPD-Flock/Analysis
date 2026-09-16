import csv, re, json, glob, os
from collections import Counter, defaultdict
from datetime import datetime, timedelta

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Org"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

VAGUE = {
    'check','checking','test','n/a','na','asdf','x','misc','other','unk','unknown',
    'lookup','look up','verify','verifying','.','-','none','review','follow up',
    'following up','fyi','see above','pd','ok','k','?','idk','tbd'
}
NUMERIC_RE = re.compile(r'^[\d\-\/#\.\s]+$')

def us_central_offset_hours(dt_naive_utc):
    y = dt_naive_utc.year
    d = datetime(y,3,1)
    first_sunday = d + timedelta(days=(6-d.weekday())%7)
    second_sunday_mar = first_sunday + timedelta(days=7)
    dst_start = second_sunday_mar.replace(hour=8)
    d2 = datetime(y,11,1)
    first_sunday_nov = d2 + timedelta(days=(6-d2.weekday())%7)
    dst_end = first_sunday_nov.replace(hour=7)
    if dst_start <= dt_naive_utc < dst_end:
        return -5
    return -6

def parse_time_local(s):
    s = s.strip()
    if not s: return None
    try:
        dt = datetime.strptime(s.replace(' UTC',''), '%m/%d/%Y, %I:%M:%S %p')
        return dt + timedelta(hours=us_central_offset_hours(dt))
    except Exception:
        return None

def classify_reason(reason):
    rl = reason.strip().lower()
    if reason.strip() == '':
        return 'blank'
    if rl in VAGUE or len(rl) <= 2:
        return 'vague'
    if NUMERIC_RE.match(reason.strip()):
        return 'numeric'
    return 'other'

PERIODS = ['all','2024','2025','2026']

def blank_struct():
    return {
        'officer_total': Counter(), 'officer_vague': Counter(), 'officer_numeric': Counter(),
        'officer_late': Counter(), 'officer_weekend': Counter(),
        'xtab': Counter(),  # keys: late_total, late_bad, day_total, day_bad, weekend_total, weekend_bad, weekday_total, weekday_bad
        'grand_total': 0, 'late_total': 0, 'weekend_total': 0,
    }

data = {p: blank_struct() for p in PERIODS}

for fp in files:
    fname = os.path.basename(fp)
    file_year = fname.replace('.csv','').split('_')[-1]
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if len(row) < 13: continue
            name = row[1].strip()
            reason = row[6].strip()
            search_time = row[9].strip()

            rc = classify_reason(reason)
            is_bad = rc in ('blank','vague')  # true vagueness only, excludes numeric-habit

            dt = parse_time_local(search_time)
            is_late = dt is not None and 1 <= dt.hour < 5
            is_weekend = dt is not None and dt.weekday() >= 5

            for p in ('all', file_year):
                if p not in data: continue
                d = data[p]
                d['officer_total'][name] += 1
                d['grand_total'] += 1
                if rc == 'vague' or rc == 'blank':
                    d['officer_vague'][name] += 1
                if rc == 'numeric':
                    d['officer_numeric'][name] += 1
                if dt is not None:
                    if is_late:
                        d['officer_late'][name] += 1
                        d['late_total'] += 1
                        d['xtab']['late_total'] += 1
                        if is_bad: d['xtab']['late_bad'] += 1
                    else:
                        d['xtab']['day_total'] += 1
                        if is_bad: d['xtab']['day_bad'] += 1
                    if is_weekend:
                        d['officer_weekend'][name] += 1
                        d['weekend_total'] += 1
                        d['xtab']['weekend_total'] += 1
                        if is_bad: d['xtab']['weekend_bad'] += 1
                    else:
                        d['xtab']['weekday_total'] += 1
                        if is_bad: d['xtab']['weekday_bad'] += 1

out = {}
for p in PERIODS:
    d = data[p]
    out[p] = {
        'grand_total': d['grand_total'],
        'late_total': d['late_total'],
        'weekend_total': d['weekend_total'],
        'officer_total_top10': d['officer_total'].most_common(10),
        'officer_vague_rate_top6': [],
        'officer_numeric_rate_top6': [],
        'officer_late_rate_top6': [],
        'officer_weekend_rate_top6': [],
        'xtab': dict(d['xtab']),
    }
    # vague rate top6 (min threshold for sample size, scaled to period)
    min_n = 10 if p!='all' else 30
    rows = []
    for name,total in d['officer_total'].items():
        if total < min_n: continue
        vague_rate = d['officer_vague'][name]/total*100
        rows.append((name, vague_rate, total))
    rows.sort(key=lambda x: -x[1])
    out[p]['officer_vague_rate_top6'] = [(n, round(r,1), t) for n,r,t in rows[:6]]

    rows = []
    for name,total in d['officer_total'].items():
        if total < min_n: continue
        numeric_rate = d['officer_numeric'][name]/total*100
        rows.append((name, numeric_rate, total))
    rows.sort(key=lambda x: -x[1])
    out[p]['officer_numeric_rate_top6'] = [(n, round(r,1), t) for n,r,t in rows[:6]]

    min_n2 = 10 if p!='all' else 30
    rows = []
    for name,total in d['officer_total'].items():
        if total < min_n2: continue
        late_rate = d['officer_late'][name]/total*100
        rows.append((name, late_rate, total))
    rows.sort(key=lambda x: -x[1])
    out[p]['officer_late_rate_top6'] = [(n, round(r,1), t) for n,r,t in rows[:6]]

    rows = []
    for name,total in d['officer_total'].items():
        if total < min_n2: continue
        weekend_rate = d['officer_weekend'][name]/total*100
        rows.append((name, weekend_rate, total))
    rows.sort(key=lambda x: -x[1])
    out[p]['officer_weekend_rate_top6'] = [(n, round(r,1), t) for n,r,t in rows[:6]]

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\org_yearly.json", 'w') as f:
    json.dump(out, f, indent=1)

for p in PERIODS:
    d = out[p]
    print(f"=== {p} === grand_total={d['grand_total']} late_total={d['late_total']} weekend_total={d['weekend_total']}")
    xt = d['xtab']
    if xt.get('late_total') and xt.get('day_total'):
        print(f"  late_bad%={xt['late_bad']/xt['late_total']*100:.1f} day_bad%={xt['day_bad']/xt['day_total']*100:.1f}")
    if xt.get('weekend_total') and xt.get('weekday_total'):
        print(f"  weekend_bad%={xt['weekend_bad']/xt['weekend_total']*100:.1f} weekday_bad%={xt['weekday_bad']/xt['weekday_total']*100:.1f}")
    print("  top10 officers:", d['officer_total_top10'])
    print("  vague rate top6:", d['officer_vague_rate_top6'])
    print("  numeric rate top6:", d['officer_numeric_rate_top6'])
    print("  late rate top6:", d['officer_late_rate_top6'])
    print("  weekend rate top6:", d['officer_weekend_rate_top6'])
    print()
