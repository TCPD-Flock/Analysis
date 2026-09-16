import csv, re, json, glob, os, time
from collections import Counter, defaultdict

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Network"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

VAGUE = {
    'check','checking','test','n/a','na','asdf','x','misc','other','unk','unknown',
    'lookup','look up','verify','verifying','.','-','none','review','follow up',
    'following up','fyi','see above','pd','ok','k','?','idk','tbd'
}
NUMERIC_RE = re.compile(r'^[\d\-\/#\.\s]+$')
PERIODS = ['all','2024','2025','2026']

org_counts = {p: Counter() for p in PERIODS}
org_vague = {p: Counter() for p in PERIODS}
org_total_rows = {p: 0 for p in PERIODS}

t0 = time.time()
for fi, fp in enumerate(files):
    fname = os.path.basename(fp)
    file_year = fname.replace('.csv','').split('_')[-1]
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if len(row) < 13: continue
            org = row[2].strip()
            reason = row[6].strip()
            rl = reason.lower()
            is_bad = (reason == '') or (rl in VAGUE or len(rl) <= 2)
            for p in ('all', file_year):
                if p not in org_counts: continue
                org_counts[p][org] += 1
                org_total_rows[p] += 1
                if is_bad:
                    org_vague[p][org] += 1
    print(f"[{fi+1}/{len(files)}] {fname} done, elapsed={time.time()-t0:.1f}s", flush=True)

out = {}
for p in PERIODS:
    out[p] = {
        'total_rows': org_total_rows[p],
        'org_counts': dict(org_counts[p]),
        'org_vague': dict(org_vague[p]),
    }

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\network_yearly.json", 'w') as f:
    json.dump(out, f)

print("DONE")
for p in PERIODS:
    print(p, "total_rows=", out[p]['total_rows'], "distinct_orgs=", len(out[p]['org_counts']))
