"""
CPCB Archive Data Link Builder
------------------------------
Builds the master CSV of download links consumed by Downloader.py.

BACKGROUND (2025 portal rebuild):
CPCB rebuilt the air-quality portal. The old metadata API
(dataRepository/file_Path) that this script used to call is gone and now
sits behind an authenticated, AES-encrypted proxy. Fortunately:
  1. The public download endpoint needs no auth or token, and
  2. Archive filenames follow a fixed, deterministic pattern.
So instead of calling the dead API, we generate the links directly from
'sites_master.csv' and (optionally) confirm each one exists with a cheap
HEAD request against the new endpoint.

The links are written in the ORIGINAL URL format
(dataRepository/download_file?file_name=Raw_data/...). Downloader.py
rewrites them to the new endpoint at download time via its to_new_url(),
so both this freshly-built master and any older master behave identically.

USAGE:
  - Set FREQUENCY and YEARS below, then run: python script.py
  - To skip existence-checking (faster, but keeps links for missing years),
    set VALIDATE = False. Downloader.py tolerates 404s either way.
"""

import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

# ========== CONFIG ==========
SITES_FILE = 'sites_master.csv'
FREQUENCY = '15Min'                               # '15Min' | '1Hr' | '1Day'
YEARS = [str(y) for y in range(2026, 2016, -1)]   # 2026 .. 2017
VALIDATE = True                                   # HEAD-check each link; drop missing ones
MAX_WORKERS = 16                                  # parallelism for validation
SEED_FROM_EXISTING = True                         # reuse verified filenames from an existing master

# frequency -> (path directory, filename suffix, output master file)
FREQ_MAP = {
    '15Min': ('15Min', '15Min', '15_Min_MasterDataFinal.csv'),
    '1Hr':   ('1Hr',   '1Hr',   '1_Hour_MasterDataFinal.csv'),
    '1Day':  ('1Day',  '1Day',  '1_Day_MasterDataFinal.csv'),
}
PATH_DIR, SUFFIX, OUT_FILE = FREQ_MAP[FREQUENCY]

# Old-format prefix (what we store). Must stay in sync with Downloader.to_new_url.
OLD_PREFIX = 'https://airquality.cpcb.gov.in/dataRepository/download_file?file_name=Raw_data/'
NEW_PREFIX = 'https://airquality.cpcb.gov.in/caaqms-common/dataRepository/download-excel-file?file_name=/Raw_data/'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://airquality.cpcb.gov.in/ccr/'}


def load_known_filenames():
    """Map site_code -> exact filename taken from an existing master (any year).

    The current master holds server-verified filenames, so reusing them avoids
    re-deriving names for known stations and sidesteps malformed names in
    sites_master.csv. Read before we overwrite OUT_FILE.
    """
    known = {}
    if not (SEED_FROM_EXISTING and os.path.exists(OUT_FILE)):
        return known
    old = pd.read_csv(OUT_FILE)
    year_cols = [c for c in old.columns if str(c).isdigit()]
    for _, r in old.iterrows():
        for c in year_cols:
            v = r.get(c)
            if isinstance(v, str) and 'file_name=' in v:
                known[r['site_code']] = v.split('/')[-1]
                break
    return known


def derive_filename(site_code, name):
    """Reproduce CPCB's archive filename from the station name.

    e.g. 'CRRI Mathura Road, Delhi - IMD' -> 'CRRI_Mathura_Road_Delhi_IMD'
    Rule: drop commas, turn the ' - ' agency separator into a space, then
    turn every remaining space into an underscore (spaces are not collapsed).
    Correct for well-formed names; malformed source names may need seeding.
    """
    n = str(name).replace(',', '').replace(' - ', ' ').replace(' ', '_')
    return f'{site_code}_{n}_{SUFFIX}.csv'


def make_link(site_code, name, year, known):
    """Old-format download link (the canonical identifier stored in the master)."""
    fn = known.get(site_code) or derive_filename(site_code, name)
    return f'{OLD_PREFIX}{PATH_DIR}/{year}/{fn}'


def to_new_url(link):
    """Same rewrite Downloader.py applies; used here only for HEAD validation."""
    return link.replace(
        '/dataRepository/download_file?file_name=Raw_data/',
        '/caaqms-common/dataRepository/download-excel-file?file_name=/Raw_data/'
    )


def link_exists(link):
    try:
        r = requests.head(to_new_url(link), headers=HEADERS, timeout=30)
        return r.status_code == 200
    except requests.RequestException:
        return False


# ========== BUILD ==========
known = load_known_filenames()
if known:
    print(f'Seeded {len(known)} verified filenames from existing {OUT_FILE}.')

sites = pd.read_csv(SITES_FILE).rename(columns={'stateID': 'state'})
rows = sites[['site_code', 'name', 'city', 'state']].to_dict('records')

records = []
tasks = []  # (record_index, year, link)
for i, row in enumerate(rows):
    rec = {'site_code': row['site_code'], 'name': row['name'],
           'city': row['city'], 'state': row['state']}
    for y in YEARS:
        link = make_link(row['site_code'], row['name'], y, known)
        rec[y] = link
        tasks.append((i, y, link))
    records.append(rec)

print(f'Sites: {len(records)} | Years: {YEARS[-1]}-{YEARS[0]} | Candidate links: {len(tasks)}')

if VALIDATE:
    print(f'Validating with {MAX_WORKERS} parallel HEAD requests (this can take a few minutes)...')

    def check(task):
        i, y, link = task
        return i, y, link_exists(link)

    kept = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for i, y, ok in ex.map(check, tasks):
            if ok:
                kept += 1
            else:
                records[i][y] = None
    print(f'Valid links: {kept} / {len(tasks)}')

df = pd.DataFrame(records, columns=['site_code', 'name', 'city', 'state'] + YEARS)
df.to_csv(OUT_FILE, index=False)
print(f'Wrote {OUT_FILE} ({len(df)} stations).')
