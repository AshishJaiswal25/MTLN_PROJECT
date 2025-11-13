#!/usr/bin/env python3
"""
Simple ETL script to read Excel files from a folder, clean the combined DataFrame,
and write to a target database table or CSV. Designed to be safe with a --dry-run flag.

Usage examples:
  python etl.py --source ../ --pattern "sublist*.xlsx" --dry-run
  python etl.py --source ../Dataset --pattern "sublist*.xlsx" --table my_table --db-uri postgresql://user:pass@host:5432/dbname

The script looks for Excel files using the provided pattern, concatenates them,
performs simple cleaning (trim strings, normalize column names, drop empty cols/dupes,
parse date-like columns), then writes to the target.
"""
from __future__ import annotations

import argparse
import glob
import logging
import os
import re
from typing import Optional

import pandas as pd

try:
    from sqlalchemy import create_engine
except Exception:
    create_engine = None  # type: ignore


def read_sources(source_dir: str, pattern: str) -> pd.DataFrame:
    path = os.path.abspath(source_dir)
    files = sorted(glob.glob(os.path.join(path, pattern)))
    if not files:
        raise FileNotFoundError(f"No files found in {path} matching pattern {pattern}")
    dfs = []
    for f in files:
        logging.info(f"Reading {f}")
        df = pd.read_excel(f, engine="openpyxl")
        dfs.append(df)
    combined = pd.concat(dfs, ignore_index=True)
    logging.info(f"Combined dataframe shape: {combined.shape}")
    return combined


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # normalize column names
    df.columns = [re.sub(r"\s+", "_", str(c).strip().lower()) for c in df.columns]

    # trim string columns
    obj_cols = df.select_dtypes(include=["object"]).columns
    for col in obj_cols:
        df[col] = df[col].astype("string").str.strip()

    # drop empty columns
    df.dropna(axis=1, how="all", inplace=True)

    # drop duplicate rows
    df.drop_duplicates(inplace=True)

    # parse date-like columns (heuristic: column name contains 'date')
    for col in df.columns:
        if "date" in col:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                logging.debug(f"Could not parse dates in column {col}")

    return df


def write_target(df: pd.DataFrame, db_uri: Optional[str], table_name: str, dry_run: bool) -> None:
    if dry_run:
        logging.info("Dry run - no data will be written. Showing preview below:")
        print(df.head(5).to_string(index=False))
        print(f"\nTotal rows: {len(df)}")
        return

    if db_uri:
        if create_engine is None:
            raise RuntimeError("SQLAlchemy is required to write to a database. Install it in your environment.")
        engine = create_engine(db_uri)
        with engine.begin() as conn:
            df.to_sql(table_name, con=conn, if_exists="append", index=False, method="multi")
        logging.info(f"Wrote {len(df)} rows to table '{table_name}'")
    else:
        out_path = os.path.join(os.getcwd(), "etl_output.csv")
        df.to_csv(out_path, index=False)
        logging.info(f"Wrote output CSV to {out_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Simple ETL from Excel files to DB or CSV")
    p.add_argument("--source", default=".", help="Source directory containing files")
    p.add_argument("--pattern", default="*.xlsx", help="Glob pattern for source files")
    p.add_argument("--db-uri", dest="db_uri", default=None, help="SQLAlchemy DB URI (optional)")
    p.add_argument("--table", default="target_table", help="Target table name")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", help="Don't write, only show preview")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    df = read_sources(args.source, args.pattern)
    df_clean = clean_df(df)
    write_target(df_clean, args.db_uri, args.table, args.dry_run)


if __name__ == "__main__":
    main()
