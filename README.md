# CPCB Archive Data Downloader

This script (`Downloader.py`) downloads air quality data files from the CPCB archive (2017–2024) using download links provided in a master data CSV file. It supports checkpointing, so you can safely resume interrupted downloads.

---

## Usage

1. **Install required Python packages:**
   - `pandas`
   - `requests`

2. **Place the appropriate master data file** (e.g., `15_Min_MasterDataFinal.csv`, `1_Hour_MasterDataFinal.csv`, or `1_Day_MasterDataFinal.csv`) in the same directory as `Downloader.py`.

3. **Change the interval if needed:**
   By default, the script uses `15_Min_MasterDataFinal.csv`. To download data at a different interval, edit this line in the script:
   ```python
   df = pd.read_csv('15_Min_MasterDataFinal.csv')
   ```
   to:
   ```python
   df = pd.read_csv('1_Hour_MasterDataFinal.csv')
   # or
   df = pd.read_csv('1_Day_MasterDataFinal.csv')
   ```

4. **Run the script:**
   ```bash
   python Downloader.py
   ```

5. **Downloaded files** will be saved in the `CPCB_Full_Download/` directory, organized by state and city.

---

## Checkpointing & Diagnosis

- The script logs each successfully downloaded file in `download_log.txt`.
- If the download process is interrupted (e.g., due to network issues or manual stop), simply re-run the script. It will skip files already downloaded and resume from where it left off.
- To restart the download from scratch, delete `download_log.txt` and the `CPCB_Full_Download/` directory.

---

## Notes

- This script only fetches archive links (2017–2024).
- For the latest (live) data, use the CPCB portal’s Advance Search:
  [CPCB Live Data Portal](https://airquality.cpcb.gov.in/ccr/#/caaqm-dashboard-all/caaqm-landing)

---

## Troubleshooting

- If you encounter errors related to missing columns or files, ensure your master data CSV matches the expected format and is present in the directory.
- For network errors, check your internet connection and try again. 