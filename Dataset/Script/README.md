ETL script
----------

This folder contains a simple ETL script `etl.py` that reads Excel files matching a glob
pattern, performs light cleaning, and writes the result to either a database table (via
SQLAlchemy) or a CSV file.

Quickstart
1. Install requirements (recommended in a virtualenv):

   python3 -m pip install -r requirements.txt

2. Dry-run to preview combined and cleaned data:

   python etl.py --source .. --pattern "sublist*.xlsx" --dry-run

3. To write to CSV (default if no DB URI provided):

   python etl.py --source .. --pattern "sublist*.xlsx"

4. To write to a database table:

   python etl.py --source .. --pattern "sublist*.xlsx" --db-uri "postgresql://user:pass@host:5432/db" --table target_table

Notes
- The script normalizes column names, trims string columns, drops empty columns and duplicates,
  and attempts to parse any column with "date" in its name.
- For production workloads you should add more validation and error handling.
