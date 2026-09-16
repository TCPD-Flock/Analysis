import csv, glob, os, re

BASE = r"C:\Projects\Flock\flock_857_the_colony_tx_pd\TheColonyTXPD-Network"
files = sorted(glob.glob(os.path.join(BASE, "*.csv")))

wanted = {
    'tawakoni_single_char': None,
    'fort_worth_code': None,
    'chp_outside': None,
    'fbi_federal': None,
    'postal_federal': None,
    'border_patrol_federal': None,
}

for fp in files:
    fname = os.path.basename(fp)
    with open(fp, newline='', encoding='utf-8', errors='replace') as f:
        r = csv.reader(f)
        header = next(r)
        for row in r:
            if len(row) < 13: continue
            org = row[2].strip()
            reason = row[6].strip()
            rid = row[0].strip()
            search_time = row[9].strip()

            if wanted['tawakoni_single_char'] is None and org in ('East Tawakoni TX PD','West Tawakoni TX PD') and len(reason)==1:
                wanted['tawakoni_single_char'] = {'file':fname,'id':rid,'org':org,'reason':reason,'time':search_time}
            if wanted['fort_worth_code'] is None and org=='Fort Worth TX PD' and reason in ('51','60'):
                wanted['fort_worth_code'] = {'file':fname,'id':rid,'org':org,'reason':reason,'time':search_time}
            if wanted['chp_outside'] is None and org=='California Highway Patrol':
                wanted['chp_outside'] = {'file':fname,'id':rid,'org':org,'reason':reason,'time':search_time}
            if wanted['fbi_federal'] is None and 'Federal Bureau of Investigation' in org:
                wanted['fbi_federal'] = {'file':fname,'id':rid,'org':org,'reason':reason,'time':search_time}
            if wanted['postal_federal'] is None and 'Postal Inspection' in org:
                wanted['postal_federal'] = {'file':fname,'id':rid,'org':org,'reason':reason,'time':search_time}
            if wanted['border_patrol_federal'] is None and 'Border Patrol' in org:
                wanted['border_patrol_federal'] = {'file':fname,'id':rid,'org':org,'reason':reason,'time':search_time}
    if all(v is not None for v in wanted.values()):
        break

for k,v in wanted.items():
    print(k, v)
