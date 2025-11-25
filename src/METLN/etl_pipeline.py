import pandas as pd
import logging
import glob
import re
import os

from tqdm import tqdm
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROCESSED_FILE = PROCESSED_DATA_DIR / "processed_data.csv"


logging.basicConfig(level = logging.INFO,
                     format= '[%(asctime)s] : %(message)s:')


# check for presence of raw data folder
def check_raw_dir():   
    if not RAW_DATA_DIR.exists():
        logging.error(f"Raw directory does not exists {RAW_DATA_DIR}")
        raise FileNotFoundError(f"Raw directory not found {RAW_DATA_DIR}")
    
    logging.info(f"Raw directory exists {RAW_DATA_DIR}")


# check if data files for preprocessing are added here
def get_raw_data():
    raw_files = list(RAW_DATA_DIR.glob('*.xlsx'))

    if not raw_files:
        logging.error(f"No data files found in folder {RAW_DATA_DIR}")
        raise FileNotFoundError("No data files found")
    else:
        logging.info(f"{len(raw_files)} data files present in folder")
    return raw_files


# to store data date wise and access accordingly
def extract_date(filename):
    pattern = r"(\d{1,2})\.(\d{1,2})\.(\d{2})"
    match = re.search(pattern, filename)

    if not match:
        logging.error(f"Date not found in {filename}")
        raise ValueError(f"Date not found in {filename}")
    
    month, day, yr = match.groups()
    year = f"20{yr}"
    dt = pd.to_datetime(f"{month}-{day}-{year}", format = "%m-%d-%Y")
    return dt.date()


def load_processed_dates():
    if not PROCESSED_FILE.exists():
        logging.error(f"No processed file exists yet. All data files are new.")
        return set()
    
    df = pd.read_csv(PROCESSED_FILE)
    if "date_of_extract" not in df.columns:
        raise ValueError("Processed file must contain date_of_extract column")
    processed_dates = set(df['date_of_extract'].unique())
    logging.info(f"Data is already processed for - {processed_dates}")
    return processed_dates
    

# combine all raw data files together to perform data cleaning and preprocessing before saving it to SQL Table
def combine_data_files():
    PROCESSED_DATA_DIR.mkdir(exist_ok = True)

    check_raw_dir()
    raw_data_files = get_raw_data()
    if not raw_data_files:
        logging.info("No data files to combine")
        return
    
    processed_dates = load_processed_dates()
    new_dataframes = []
    skipped_files = []

    for file in tqdm(raw_data_files,desc="Processing files"):
        try:
            date_str = extract_date(file.name)

            if date_str in processed_dates:
                skipped_files.append(file.name)
                continue

            df = pd.read_excel(file)
            df.insert(0,"date_of_extract",date_str)
            new_dataframes.append(df)
        except Exception as e:
            logging.error(f"Error processing file {file.name} : {e}")
    
    if not new_dataframes:
        logging.info("No new data found. All data files were previously processed")
        if skipped_files:
            logging.info(f"Skipped files already processed {skipped_files}")
    
    combined_new = pd.concat(new_dataframes, ignore_index=True)
    if PROCESSED_FILE.exists():
        existing = pd.read_csv(PROCESSED_FILE)
        final_df = pd.concat([existing, new_dataframes], ignore_index=True)
    else:
        final_df = combined_new
    
    final_df.to_csv(PROCESSED_FILE, index = False)
    logging.info(f"Processed data saved to {PROCESSED_FILE}")
    
    if skipped_files:
        logging.info(f"Skipped already processed files: {skipped_files}")