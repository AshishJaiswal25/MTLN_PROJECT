"""
Data cleaning and standardization module for MTLN project
Converts numbered column headers to proper named headers
"""
import pandas as pd
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROCESSED_FILE = PROCESSED_DATA_DIR / "processed_data.csv"
CLEAN_FILE = PROCESSED_DATA_DIR / "clean_data.csv"

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] : %(message)s:')


# Column mapping from numbered headers to proper names
COLUMN_MAPPING = {
    '0': 'Publication',
    '1': 'AccoutID',
    '2': 'Status',
    '3': 'Bill Method',
    '4': 'Dist ID',
    '5': 'Route ID',
    '6': 'Day pattern',
    '7': 'City',
    '8': 'State',
    '9': 'Zip',
    '10': 'Rate Code',
    '11': 'LastStartDate',
    '12': 'OriginalStartDate',
    '13': 'OccupantID',
    '14': 'RouteType ID'
}


def standardize_columns():
    """
    Standardize column names in the processed data file.
    Converts numbered columns (0-14) to proper descriptive names.
    """
    logging.info("Starting column standardization...")
    
    if not PROCESSED_FILE.exists():
        logging.error(f"Processed file not found: {PROCESSED_FILE}")
        raise FileNotFoundError(f"Processed file not found: {PROCESSED_FILE}")
    
    # Read the processed data
    logging.info(f"Reading processed data from {PROCESSED_FILE}")
    df = pd.read_csv(PROCESSED_FILE, low_memory=False)
    logging.info(f"Loaded {len(df):,} rows and {len(df.columns)} columns")
    
    # Identify rows that have numbered columns vs named columns
    has_numbered = df['0'].notna()
    has_named = df['Publication'].notna()
    
    logging.info(f"Rows with numbered columns: {has_numbered.sum():,}")
    logging.info(f"Rows with named columns: {has_named.sum():,}")
    
    # For rows with numbered columns, map the values to the proper named columns
    for num_col, name_col in COLUMN_MAPPING.items():
        # Copy values from numbered columns to named columns where numbered exists
        mask = df[num_col].notna()
        df.loc[mask, name_col] = df.loc[mask, num_col]
    
    # Define the final column order (keeping date_of_extract first, then the 15 main columns)
    final_columns = ['date_of_extract'] + list(COLUMN_MAPPING.values())
    
    # Keep only the standardized columns
    df_clean = df[final_columns].copy()
    
    logging.info(f"Standardized data shape: {df_clean.shape}")
    logging.info(f"Columns in clean data: {list(df_clean.columns)}")
    
    # Save the cleaned data
    df_clean.to_csv(CLEAN_FILE, index=False)
    logging.info(f"Clean data saved to {CLEAN_FILE}")
    
    # Print summary statistics
    print("\n" + "="*80)
    print("DATA CLEANING SUMMARY")
    print("="*80)
    print(f"Total rows: {len(df_clean):,}")
    print(f"Total columns: {len(df_clean.columns)}")
    print(f"\nColumn names:")
    for i, col in enumerate(df_clean.columns, 1):
        non_null = df_clean[col].notna().sum()
        print(f"  {i:2d}. {col:25s} - {non_null:,} non-null values ({non_null/len(df_clean)*100:.1f}%)")
    
    print(f"\nData by extract date:")
    print(df_clean['date_of_extract'].value_counts().sort_index())
    
    print(f"\nFirst 5 rows:")
    print(df_clean.head().to_string())
    
    print(f"\nData types:")
    print(df_clean.dtypes)
    
    print("\n" + "="*80)
    print(f"✅ Clean data ready for analysis at: {CLEAN_FILE}")
    print("="*80)
    
    return df_clean


if __name__ == "__main__":
    standardize_columns()
