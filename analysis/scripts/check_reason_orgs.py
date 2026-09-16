import csv, glob, os, re
from collections import Counter

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Network"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

VAGUE = {
    'check','checking','test','n/a','na','asdf','x','misc','other','unk','unknown',
    'lookup','look up','verify','verifying','.','-','none','review','follow up',
    'following up','fyi','see above','pd','ok','k','?','idk','tbd'
}
NUMERIC_RE = re.compile(r'^[\d\-\/#\.\s]+$')

targets = {'East Tawakoni TX PD', 'West Tawakoni TX PD', 'Fort Worth TX PD'}
reason_counts = {t: Counter() for t in targets}

for fp in files:
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if len(row) < 13: continue
            org = row[2].strip()
            if org not in targets: continue
            reason = row[6].strip().lower()
            reason_counts[org][reason] += 1

for t in targets:
    print(f"=== {t} ===")
    for val, c in reason_counts[t].most_common(15):
        print(f"  {val!r}: {c}")
    print()
