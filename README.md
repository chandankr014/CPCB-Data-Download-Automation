# CPCB Archive Data Downloader

Two scripts to download air quality data from the CPCB archive:

- **`script.py`** — builds the master CSV of download links.
- **`Downloader.py`** — downloads every file listed in that master CSV.

Both support the 2025 portal rebuild (links are auto-rewritten to the new endpoint) and checkpointing, so interrupted runs resume safely.

---

## Usage

1. **Install packages:**
   ```bash
   pip install pandas requests
   ```

2. **Build the link master** (needs `sites_master.csv` in the same folder):
   ```bash
   python script.py
   ```
   This writes `15_Min_MasterDataFinal.csv`. Edit the config block at the top of `script.py` to change:
   - `FREQUENCY` — `'15Min'`, `'1Hr'`, or `'1Day'`
   - `YEARS` — years to include (default 2017–2025)
   - `VALIDATE` — `True` checks each link and keeps only files that exist (slower); `False` skips checking

3. **Download the files:**
   ```bash
   python Downloader.py
   ```
   Set which master and years to pull at the top of `Downloader.py`
   (`df = pd.read_csv(...)` and `year_columns`).

4. **Downloaded files** are saved under `CPCB/<YEAR>_<FREQUENCY>/`
   (e.g. `CPCB/2019_15Min/`).

---

## Checkpointing

- Each downloaded file is logged in `download_log.txt`.
- Re-run `Downloader.py` to resume — already-downloaded files are skipped.
- To start over, delete `download_log.txt` and the `CPCB/` directory.

---

## Notes

- These scripts fetch **archive** data (past years). For live data, use the
  CPCB portal's Advance Search:
  [CPCB Live Data Portal](https://airquality.cpcb.gov.in/ccr/#/caaqm-dashboard-all/caaqm-landing)
- Some stations have no data for certain years (e.g. IMD stations before they
  came online); those links 404 and are skipped — this is expected, not an error.

---

## Troubleshooting

- **Missing columns/files:** ensure `sites_master.csv` / the master CSV are
  present and match the expected format.
- **Network errors:** check your connection and re-run (it resumes).
