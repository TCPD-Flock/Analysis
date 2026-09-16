import csv, re, json, glob, os, time
from collections import Counter, defaultdict
from datetime import datetime

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Network"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

VAGUE = {
    'check','checking','test','n/a','na','asdf','x','misc','other','unk','unknown',
    'lookup','look up','verify','verifying','.','-','none','review','follow up',
    'following up','fyi','see above','pd','ok','k','?','idk','tbd'
}
NUMERIC_RE = re.compile(r'^[\d\-\/#\.\s]+$')

def parse_time(s):
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.strptime(s.replace(' UTC',''), '%m/%d/%Y, %I:%M:%S %p')
    except Exception:
        return None

rows_total = 0
min_dt = None
max_dt = None
org_counts = Counter()
reason_blank = 0
reason_numeric_only = 0
reason_vague = 0
reason_other = 0
search_type_counts = Counter()
hour_hist = Counter()
weekday_hist = Counter()
org_reason_vague = Counter()  # per-org vague count
org_reason_total = Counter()

t0 = time.time()
for fi, fp in enumerate(files):
    fname = os.path.basename(fp)
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if len(row) < 13:
                continue
            org = row[2].strip()
            reason = row[6].strip()
            search_time = row[9].strip()
            search_type = row[10].strip()

            rows_total += 1
            org_counts[org] += 1
            search_type_counts[search_type] += 1
            org_reason_total[org] += 1

            dt = parse_time(search_time)
            if dt:
                if min_dt is None or dt < min_dt: min_dt = dt
                if max_dt is None or dt > max_dt: max_dt = dt
                hour_hist[dt.hour] += 1
                weekday_hist[dt.weekday()] += 1

            rl = reason.lower()
            if reason == '':
                reason_blank += 1
                org_reason_vague[org] += 1
            elif rl in VAGUE or len(rl) <= 2:
                reason_vague += 1
                org_reason_vague[org] += 1
            elif NUMERIC_RE.match(reason):
                reason_numeric_only += 1
            else:
                reason_other += 1
    print(f"[{fi+1}/{len(files)}] {fname} done, rows_total={rows_total}, elapsed={time.time()-t0:.1f}s")

print("\n=== NETWORK SUMMARY ===")
print("rows_total:", rows_total)
print("date range:", min_dt, "to", max_dt)
print("unique orgs:", len(org_counts))
print("reason_blank:", reason_blank, "reason_numeric_only:", reason_numeric_only,
      "reason_vague(non-blank,short):", reason_vague, "reason_other:", reason_other)
print("search_type_counts:", search_type_counts.most_common())
print("\ntop 20 orgs by volume:")
for o,c in org_counts.most_common(20):
    print(f"  {o}: {c}")

out = {
    'rows_total': rows_total,
    'min_dt': str(min_dt), 'max_dt': str(max_dt),
    'unique_orgs': len(org_counts),
    'org_counts_top40': org_counts.most_common(40),
    'all_org_counts': dict(org_counts),
    'reason_blank': reason_blank,
    'reason_numeric_only': reason_numeric_only,
    'reason_vague': reason_vague,
    'reason_other': reason_other,
    'search_type_counts': search_type_counts.most_common(),
    'hour_hist': dict(hour_hist),
    'weekday_hist': dict(weekday_hist),
    'org_reason_vague_top30': org_reason_vague.most_common(30),
    'org_reason_total_for_vague_top30': {o: org_reason_total[o] for o,_ in org_reason_vague.most_common(30)},
}
with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\network_analysis.json", 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, default=str)
print("\nSaved network_analysis.json")
