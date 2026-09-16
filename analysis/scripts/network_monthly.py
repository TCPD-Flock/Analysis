import csv, re, json, glob, os, time
from collections import Counter, defaultdict

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Network"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

cls = json.load(open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\org_classification_full.json"))

VAGUE = {
    'check','checking','test','n/a','na','asdf','x','misc','other','unk','unknown',
    'lookup','look up','verify','verifying','.','-','none','review','follow up',
    'following up','fyi','see above','pd','ok','k','?','idk','tbd'
}
NUMERIC_RE = re.compile(r'^[\d\-\/#\.\s]+$')

MONTHMAP = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}

def month_key_from_fname(fname):
    # TheColonyTXPD_network_Jan_2024.csv
    parts = fname.replace('.csv','').split('_')
    mon, yr = parts[-2], parts[-1]
    return f"{yr}-{MONTHMAP[mon]:02d}"

monthly = defaultdict(lambda: {
    'total':0, 'vague':0, 'numeric':0, 'blank':0,
    'out_of_radius':0, 'federal':0, 'unknown_org':0, 'tx':0,
    'distinct_orgs': set(),
})

t0 = time.time()
for fi, fp in enumerate(files):
    fname = os.path.basename(fp)
    mk = month_key_from_fname(fname)
    m = monthly[mk]
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if len(row) < 13: continue
            org = row[2].strip()
            reason = row[6].strip()
            m['total'] += 1
            m['distinct_orgs'].add(org)
            c = cls.get(org)
            if c:
                if c['kind'] == 'FEDERAL':
                    m['federal'] += 1
                elif c['kind'] == 'STATE':
                    if c['state'] == 'TX':
                        m['tx'] += 1
                    if c['out_of_radius']:
                        m['out_of_radius'] += 1
                else:
                    m['unknown_org'] += 1
            rl = reason.lower()
            if reason == '':
                m['blank'] += 1
            elif rl in VAGUE or len(rl) <= 2:
                m['vague'] += 1
            elif NUMERIC_RE.match(reason):
                m['numeric'] += 1
    print(f"[{fi+1}/{len(files)}] {fname} ({mk}) done, elapsed={time.time()-t0:.1f}s", flush=True)

out = {}
for mk, m in monthly.items():
    out[mk] = {
        'total': m['total'], 'vague': m['vague'], 'numeric': m['numeric'], 'blank': m['blank'],
        'out_of_radius': m['out_of_radius'], 'federal': m['federal'], 'unknown_org': m['unknown_org'],
        'tx': m['tx'], 'distinct_orgs': len(m['distinct_orgs']),
    }

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\network_monthly.json", 'w') as f:
    json.dump(out, f, indent=1)

print("DONE")
for mk in sorted(out.keys()):
    print(mk, out[mk])
