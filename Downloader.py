import re
import os
import requests
from urllib.parse import urlparse, parse_qs
import pandas as pd

# Log file to track downloaded files
LOG_FILE = 'download_log.txt'

def read_download_log():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def append_to_download_log(identifier):
    with open(LOG_FILE, 'a') as f:
        f.write(identifier + '\n')


df = pd.read_csv('15_Min_MasterDataFinal.csv')
year_columns = ['2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017']

all_links = df[year_columns].stack().tolist()
print("Total Files to Download: ", len(all_links))

def generate_filename(url):
    parsed_url = urlparse(url)
    file_name = parse_qs(parsed_url.query)['file_name'][0]
    # Replace slashes with underscores and remove leading path
    formatted_name = file_name.replace('/', '_').replace('Raw_data_','')
    return formatted_name


def extract_site_id(link):
    # Use regex to extract the site_id (e.g., site_103, site_104, etc.)
    match = re.search(r'site_\d+', link)
    site_id = match.group(0) if match else None
    if site_id:
        # Extract city and state based on the site_id
        row = df[df['site_code'] == site_id][['city', 'state']]
        if not row.empty:
            city, state = row.iloc[0]['city'], row.iloc[0]['state']
            return city, state
    return None, None

# Read the log of already downloaded files (by filename)
downloaded_files = read_download_log()

for link in all_links:
    filename = generate_filename(link)
    if filename in downloaded_files:
        print(f'Skipping already downloaded: {filename}')
        continue
    c,s = extract_site_id(link)
    save_dir = f'CPCB_Full_Download/{s}/{c}'
    file_path = os.path.join(save_dir, filename)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    try:
        response = requests.get(link, stream=True)
        response.raise_for_status()  # Check for HTTP errors

        # Write the content to a file
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f'\033[92mDownloaded: {file_path}\033[0m')
        append_to_download_log(filename)

    except requests.RequestException as e:
        print(f'Error downloading {link}: {e}')
