import csv, glob, os, json
from collections import Counter, defaultdict
from datetime import datetime, timedelta

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Org"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

def us_central_offset_hours(dt_naive_utc):
    # US DST: second Sunday in March 2am local -> first Sunday in November 2am local.
    # Approximate using UTC dates: CDT (UTC-5) roughly mid-Mar to early-Nov, else CST (UTC-6).
    y = dt_naive_utc.year
    # second Sunday of March
    d = datetime(y,3,1)
    first_sunday = d + timedelta(days=(6-d.weekday())%7)
    second_sunday_mar = first_sunday + timedelta(days=7)
    dst_start = second_sunday_mar.replace(hour=8)  # 2am CST = 8am UTC
    # first Sunday of November
    d2 = datetime(y,11,1)
    first_sunday_nov = d2 + timedelta(days=(6-d2.weekday())%7)
    dst_end = first_sunday_nov.replace(hour=7)  # 2am CDT = 7am UTC
    if dst_start <= dt_naive_utc < dst_end:
        return -5  # CDT
    return -6  # CST

def parse_time(s):
    s = s.strip()
    if not s: return None
    try:
        dt = datetime.strptime(s.replace(' UTC',''), '%m/%d/%Y, %I:%M:%S %p')
        offset = us_central_offset_hours(dt)
        return dt + timedelta(hours=offset)
    except Exception:
        return None

officer_stats = defaultdict(lambda: {'total':0, 'late_night':0, 'weekend':0, 'hour_hist': Counter()})
overall = {'total':0, 'late_night':0, 'weekend':0}

for fp in files:
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if len(row) < 13: continue
            name = row[1].strip()
            search_time = row[9].strip()
            dt = parse_time(search_time)
            if not dt: continue
            st = officer_stats[name]
            st['total'] += 1
            st['hour_hist'][dt.hour] += 1
            overall['total'] += 1
            is_late = dt.hour >= 1 and dt.hour < 5  # 1am-5am local
            is_weekend = dt.weekday() >= 5
            if is_late:
                st['late_night'] += 1
                overall['late_night'] += 1
            if is_weekend:
                st['weekend'] += 1
                overall['weekend'] += 1

overall_late_pct = overall['late_night']/overall['total']*100
overall_weekend_pct = overall['weekend']/overall['total']*100
print(f"OVERALL: total={overall['total']} late_night(1-5am local)%={overall_late_pct:.1f} weekend%={overall_weekend_pct:.1f}")

rows = []
for name, st in officer_stats.items():
    if st['total'] < 30:
        continue
    late_pct = st['late_night']/st['total']*100
    weekend_pct = st['weekend']/st['total']*100
    rows.append((name, st['total'], late_pct, weekend_pct))

print("\nTop officers by late-night % (min 30 searches):")
for name,total,late_pct,weekend_pct in sorted(rows, key=lambda x:-x[2])[:15]:
    print(f"  {name}: total={total} late_night%={late_pct:.1f} weekend%={weekend_pct:.1f}")

print("\nTop officers by weekend % (min 30 searches):")
for name,total,late_pct,weekend_pct in sorted(rows, key=lambda x:-x[3])[:15]:
    print(f"  {name}: total={total} late_night%={late_pct:.1f} weekend%={weekend_pct:.1f}")

out = {
    'overall': overall, 'overall_late_pct': overall_late_pct, 'overall_weekend_pct': overall_weekend_pct,
    'officer_rows': [{'name':n,'total':t,'late_pct':lp,'weekend_pct':wp} for n,t,lp,wp in rows],
}
with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\off_hours.json",'w') as f:
    json.dump(out, f, indent=2)
