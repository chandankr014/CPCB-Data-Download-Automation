import requests
import pandas as pd
import os

# ========== USER SETTINGS ==========
TARGET_YEAR = 2016
MASTER_DATA_FILE = "15_Min_MasterDataFinal.csv"
OUTPUT_DIR = str(TARGET_YEAR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== LOAD DATA ==========
df = pd.read_csv(MASTER_DATA_FILE)
# We need the 2017 links as a template to generate other years
if '2017' not in df.columns:
    raise ValueError("The master data file must contain a '2017' column with download links.")

# ========== GENERATE LINKS FOR TARGET YEAR ==========
def make_year_link(link_2017, target_year):
    """
    Given a 2017 link, generate the link for the target year by replacing year in path and filename.
    """
    if pd.isna(link_2017):
        return None
    link = str(link_2017)
    link = link.replace('/2017/', f'/{target_year}/').replace('_2017_', f'_{target_year}_')
    return link

df[f'{TARGET_YEAR}'] = df['2017'].apply(lambda link: make_year_link(link, TARGET_YEAR))

# ========== DOWNLOAD FUNCTION ==========
def download_file(url, save_path):
    try:
        response = requests.get(url, timeout=30)
        # Check for server error or bad status
        if response.status_code != 200 or b"Internal Server Error" in response.content[:100]:
            print(f"Failed to download {os.path.basename(save_path)}: Server error or bad status code")
            return False
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {os.path.basename(save_path)}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

# ========== MAIN DOWNLOAD LOOP ==========
for idx, row in df.iterrows():
    link = row.get(f'{TARGET_YEAR}')
    if pd.isna(link) or not isinstance(link, str):
        continue
    # Extract filename from the link
    file_path = link.split("file_name=")[-1]
    filename = os.path.basename(file_path)
    # Try to extract the year from the path (assuming .../YEAR/...)
    parts = file_path.split('/')
    year_in_path = None
    for part in parts:
        if part.isdigit() and len(part) == 4:
            year_in_path = part
            break
    if year_in_path:
        filename_with_year = f"{year_in_path}_{filename}"
    else:
        filename_with_year = filename
    save_path = os.path.join(OUTPUT_DIR, filename_with_year)
    download_file(link, save_path)

print(f"\nAll available files for {TARGET_YEAR} have been processed.")

# ========== TIPS ==========
# - To download another year, just change TARGET_YEAR at the top and re-run the script.
# - Make sure your master data file has the '2017' column with valid links as a template.
# - Downloaded files will be saved in a folder named after the year (e.g., '2016'). 