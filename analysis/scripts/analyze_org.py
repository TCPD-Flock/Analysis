import csv, re, json, glob, os
from collections import Counter, defaultdict
from datetime import datetime

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Org"

files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

VAGUE = {
    'check','checking','test','n/a','na','asdf','x','misc','other','unk','unknown',
    'lookup','look up','verify','verifying','.','-','none','review','follow up',
    'following up','fyi','see above','pd','ok','k','?','idk','tbd','misc.','na.',
    'unsure','random','curious','bored','personal'
}
NUMERIC_RE = re.compile(r'^[\d\-\/#\.\s]+$')

def parse_time(s):
    s = s.strip()
    if not s:
        return None
    # format: 01/30/2024, 07:24:19 PM UTC
    try:
        return datetime.strptime(s.replace(' UTC',''), '%m/%d/%Y, %I:%M:%S %p')
    except Exception:
        return None

rows_total = 0
min_dt = None
max_dt = None
org_names = Counter()
officer_counts = Counter()
reason_blank = 0
reason_numeric_only = 0
reason_vague = 0
reason_other = 0
numeric_and_blank_case = 0
search_type_counts = Counter()
filters_counts = Counter()

# repeated target: (officer, plate) -> count ; also track case list of examples (row ids) sparse
target_counts = Counter()
target_examples = {}  # (officer,plate) -> first row identifying info (file, line no proxy via ID)

# off hours per officer
officer_hour_hist = defaultdict(lambda: Counter())  # officer -> hour(UTC) counter
officer_weekday_hist = defaultdict(lambda: Counter())
officer_total = Counter()

# per officer reason-vagueness
officer_vague_count = Counter()
officer_numeric_count = Counter()

sample_flagged_rows = []  # store limited examples with file+id for vague/blank reasons

row_id_counter = 0

for fp in files:
    fname = os.path.basename(fp)
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if len(row) < 13:
                continue
            row_id_counter += 1
            rid = row[0].strip()
            name = row[1].strip()
            org = row[2].strip()
            plate = row[5].strip()
            reason = row[6].strip()
            case_num = row[7].strip()
            filt = row[8].strip()
            search_time = row[9].strip()
            search_type = row[10].strip()

            rows_total += 1
            org_names[org] += 1
            officer_counts[name] += 1
            search_type_counts[search_type] += 1
            filters_counts[filt] += 1

            dt = parse_time(search_time)
            if dt:
                if min_dt is None or dt < min_dt: min_dt = dt
                if max_dt is None or dt > max_dt: max_dt = dt
                officer_hour_hist[name][dt.hour] += 1
                officer_weekday_hist[name][dt.weekday()] += 1
            officer_total[name] += 1

            rl = reason.lower()
            is_vague = False
            is_numeric = False
            if reason == '':
                reason_blank += 1
                is_vague = True
            elif rl in VAGUE or len(rl) <= 2:
                reason_vague += 1
                is_vague = True
            elif NUMERIC_RE.match(reason):
                reason_numeric_only += 1
                is_numeric = True
                if case_num == '':
                    numeric_and_blank_case += 1
            else:
                reason_other += 1

            if is_vague:
                officer_vague_count[name] += 1
                if len(sample_flagged_rows) < 400:
                    sample_flagged_rows.append({
                        'type': 'blank_or_vague', 'file': fname, 'id': rid, 'name': name,
                        'reason': reason, 'case': case_num, 'search_time': search_time
                    })
            if is_numeric:
                officer_numeric_count[name] += 1
                if len(sample_flagged_rows) < 800:
                    sample_flagged_rows.append({
                        'type': 'numeric_only', 'file': fname, 'id': rid, 'name': name,
                        'reason': reason, 'case': case_num, 'search_time': search_time
                    })

            if plate:
                key = (name, plate.upper())
                target_counts[key] += 1
                if key not in target_examples:
                    target_examples[key] = {'file': fname, 'id': rid, 'search_time': search_time, 'reason': reason}

print("ORG rows_total:", rows_total)
print("date range:", min_dt, "to", max_dt)
print("unique org names:", len(org_names), org_names.most_common(10))
print("unique officers:", len(officer_counts))
print("reason_blank:", reason_blank, "reason_numeric_only:", reason_numeric_only,
      "reason_vague(non-blank):", reason_vague, "reason_other:", reason_other)
print("numeric_and_blank_case:", numeric_and_blank_case)
print("search_type_counts:", search_type_counts.most_common())
print("top officers by volume:")
for n,c in officer_counts.most_common(10):
    print(" ", n, c)

print("\ntop repeated targets (officer, plate):")
top_targets = target_counts.most_common(30)
for (name,plate), c in top_targets:
    if c >= 5:
        ex = target_examples[(name,plate)]
        print(f"  officer={name!r} plate_hash={hash(plate)%100000} count={c} first_example(file={ex['file']}, id={ex['id']})")

# Save full data to json for report building (without raw plate values in top-level; we'll hash)
out = {
    'rows_total': rows_total,
    'min_dt': str(min_dt), 'max_dt': str(max_dt),
    'org_names': org_names.most_common(20),
    'unique_officers': len(officer_counts),
    'officer_counts_top10': officer_counts.most_common(10),
    'reason_blank': reason_blank,
    'reason_numeric_only': reason_numeric_only,
    'reason_vague': reason_vague,
    'reason_other': reason_other,
    'numeric_and_blank_case': numeric_and_blank_case,
    'search_type_counts': search_type_counts.most_common(),
    'filters_counts': filters_counts.most_common(20),
    'officer_vague_count_top15': officer_vague_count.most_common(15),
    'officer_numeric_count_top15': officer_numeric_count.most_common(15),
    'top_targets': [
        {'officer': name, 'plate_last4': plate[-4:] if len(plate)>=4 else plate, 'count': c,
         'example_file': target_examples[(name,plate)]['file'], 'example_id': target_examples[(name,plate)]['id']}
        for (name,plate), c in top_targets
    ],
    'officer_hour_hist': {k: dict(v) for k,v in officer_hour_hist.items()},
    'officer_weekday_hist': {k: dict(v) for k,v in officer_weekday_hist.items()},
    'officer_total': dict(officer_total),
    'sample_flagged_rows': sample_flagged_rows[:200],
}

with open(r"C:\Projects\Flock\flock_857_the_colony_tx_pd\analysis\data\org_analysis.json", 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, default=str)

print("\nSaved org_analysis.json")
