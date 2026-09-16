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
MONTHMAP = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}

def month_key_from_fname(fname):
    parts = fname.replace('.csv','').split('_')
    mon, yr = parts[-2], parts[-1]
    return f"{yr}-{MONTHMAP[mon]:02d}"

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

monthly = defaultdict(lambda: {
    'total':0,'vague':0,'numeric':0,'blank':0,'late_night':0,'weekend':0,
    'officers':set(),'plates':set()
})

# cross-tab accumulators
xtab = {
    'late_night': Counter(), 'daytime': Counter(),
    'weekend': Counter(), 'weekday': Counter(),
}

pair_detail = defaultdict(lambda: {
    'count':0, 'cases': set(), 'dts': [], 'reason_class': Counter(), 'search_types': Counter()
})

all_rows_for_pairs = []

for fp in files:
    fname = os.path.basename(fp)
    mk = month_key_from_fname(fname)
    m = monthly[mk]
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if len(row) < 13: continue
            name = row[1].strip()
            plate = row[5].strip().upper()
            reason = row[6].strip()
            case_num = row[7].strip()
            search_time = row[9].strip()
            search_type = row[10].strip()

            m['total'] += 1
            m['officers'].add(name)
            if plate: m['plates'].add(plate)

            rc = classify_reason(reason)
            if rc != 'other':
                m[rc] += 1

            dt = parse_time_local(search_time)
            is_late = dt is not None and 1 <= dt.hour < 5
            is_weekend = dt is not None and dt.weekday() >= 5
            if is_late: m['late_night'] += 1
            if is_weekend: m['weekend'] += 1

            if dt is not None:
                xtab['late_night' if is_late else 'daytime'][rc] += 1
                xtab['late_night' if is_late else 'daytime']['_total'] += 1
                xtab['weekend' if is_weekend else 'weekday'][rc] += 1
                xtab['weekend' if is_weekend else 'weekday']['_total'] += 1

            if plate:
                key = (name, plate)
                d = pair_detail[key]
                d['count'] += 1
                if case_num: d['cases'].add(case_num.lower())
                if dt is not None: d['dts'].append((dt, is_late, is_weekend))
                d['reason_class'][rc] += 1
                d['search_types'][search_type] += 1

monthly_out = {}
for mk, m in monthly.items():
    monthly_out[mk] = {
        'total': m['total'], 'vague': m['vague'], 'numeric': m['numeric'], 'blank': m['blank'],
        'late_night': m['late_night'], 'weekend': m['weekend'],
        'officers': len(m['officers']), 'plates': len(m['plates']),
    }

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\org_monthly.json",'w') as f:
    json.dump(monthly_out, f, indent=1)

print("=== off-hours reason-quality cross-tab ===")
for bucket in ['late_night','daytime','weekend','weekday']:
    c = xtab[bucket]
    tot = c['_total']
    bad = c.get('blank',0)+c.get('vague',0)+c.get('numeric',0)
    print(f"{bucket}: total={tot} blank={c.get('blank',0)} vague={c.get('vague',0)} numeric={c.get('numeric',0)} bad_pct={bad/tot*100:.1f}%")

# === stalking-risk composite ===
risk_rows = []
for (name,plate), d in pair_detail.items():
    if d['count'] < 3: continue
    dts = [x[0] for x in d['dts']]
    if not dts: continue
    span_days = (max(dts)-min(dts)).days
    late_frac = sum(1 for x in d['dts'] if x[1]) / len(d['dts'])
    weekend_frac = sum(1 for x in d['dts'] if x[2]) / len(d['dts'])
    manual = d['search_types'].get('search',0)+d['search_types'].get('search - Mobile',0)
    manual_frac = manual / d['count']
    case_frac = len(d['cases']) > 0
    bad_reason = d['reason_class'].get('blank',0)+d['reason_class'].get('vague',0)+d['reason_class'].get('numeric',0)
    vague_frac = bad_reason / d['count']
    # composite score: emphasizes manual searching, no case, vague reason, long span, off-hours concentration
    span_factor = min(span_days/30.0, 6.0)
    score = manual_frac * (0.4 if case_frac else 1.0) * (0.3 + 0.7*vague_frac) * (1 + span_factor) * (1 + late_frac + weekend_frac*0.5)
    risk_rows.append({
        'officer': name, 'plate_last4': plate[-4:], 'count': d['count'], 'span_days': span_days,
        'has_case': case_frac, 'vague_frac': round(vague_frac,2), 'late_night_frac': round(late_frac,2),
        'weekend_frac': round(weekend_frac,2), 'manual_frac': round(manual_frac,2),
        'score': round(score,2),
    })

risk_rows.sort(key=lambda r: -r['score'])
print("\n=== TOP 20 stalking-risk composite (Org log, count>=3) ===")
for r in risk_rows[:20]:
    print(r)

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\stalking_risk.json",'w') as f:
    json.dump(risk_rows[:60], f, indent=1)

print("\nTotal pairs scored:", len(risk_rows))
