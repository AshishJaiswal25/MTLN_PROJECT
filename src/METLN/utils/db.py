"""
Database utility module for MTLN project
Handles database connections and data loading operations
"""
import pandas as pd
import logging
import sqlite3
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

# Default SQLite database path
DEFAULT_DB_PATH = DATABASE_DIR / "mtln.db"

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] : %(message)s:')

Base = declarative_base()


class DatabaseConnection:
    """
    Database connection manager for MTLN data
    Supports SQLite, PostgreSQL, and MySQL
    """
    
    def __init__(self, db_uri: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            db_uri: Database URI (e.g., 'sqlite:///path/to/db.db' or 'postgresql://user:pass@localhost/dbname')
                   If None, uses default SQLite database
        """
        if db_uri is None:
            db_uri = f"sqlite:///{DEFAULT_DB_PATH}"
        
        self.db_uri = db_uri
        self.engine = None
        self.session = None
        
        logging.info(f"Database URI configured: {db_uri}")
    
    def connect(self):
        """Create database engine and session"""
        try:
            self.engine = create_engine(self.db_uri, echo=False)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            logging.info("Database connection established successfully")
            return self.engine
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise
    
    def create_tables(self):
        """Create all tables defined in the Base metadata"""
        try:
            Base.metadata.create_all(self.engine)
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Failed to create tables: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        logging.info("Database connection closed")


def load_csv_to_sql(
    csv_path: Path,
    table_name: str = "subscriptions",
    db_uri: Optional[str] = None,
    if_exists: str = "replace"
) -> int:
    """
    Load CSV data into SQL database
    
    Args:
        csv_path: Path to CSV file
        table_name: Name of the database table
        db_uri: Database URI (None = use default SQLite)
        if_exists: How to behave if table exists ('fail', 'replace', 'append')
    
    Returns:
        Number of rows loaded
    """
    logging.info(f"Loading data from {csv_path} to table '{table_name}'")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path, low_memory=False)
    logging.info(f"Read {len(df):,} rows from CSV")
    
    # Convert date columns to proper datetime
    date_columns = ['date_of_extract', 'LastStartDate', 'OriginalStartDate']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Create database connection
    if db_uri is None:
        db_uri = f"sqlite:///{DEFAULT_DB_PATH}"
    
    engine = create_engine(db_uri)
    
    try:
        # Load to SQL
        df.to_sql(table_name, con=engine, if_exists=if_exists, index=False, method='multi')
        logging.info(f"Successfully loaded {len(df):,} rows to table '{table_name}'")
        
        # Verify the load
        with engine.connect() as conn:
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = result.fetchone()[0]
            logging.info(f"Verification: Table '{table_name}' contains {count:,} rows")
        
        return len(df)
    
    except Exception as e:
        logging.error(f"Failed to load data to SQL: {e}")
        raise
    finally:
        engine.dispose()


def query_data(
    query: str,
    db_uri: Optional[str] = None,
    params: Optional[dict] = None
) -> pd.DataFrame:
    """
    Execute SQL query and return results as DataFrame
    
    Args:
        query: SQL query string
        db_uri: Database URI (None = use default SQLite)
        params: Query parameters for parameterized queries
    
    Returns:
        Query results as pandas DataFrame
    """
    if db_uri is None:
        db_uri = f"sqlite:///{DEFAULT_DB_PATH}"
    
    engine = create_engine(db_uri)
    
    try:
        df = pd.read_sql(query, con=engine, params=params)
        logging.info(f"Query returned {len(df):,} rows")
        return df
    except Exception as e:
        logging.error(f"Query failed: {e}")
        raise
    finally:
        engine.dispose()


def get_table_info(table_name: str = "subscriptions", db_uri: Optional[str] = None) -> dict:
    """
    Get information about a database table
    
    Args:
        table_name: Name of the table
        db_uri: Database URI (None = use default SQLite)
    
    Returns:
        Dictionary with table information
    """
    if db_uri is None:
        db_uri = f"sqlite:///{DEFAULT_DB_PATH}"
    
    engine = create_engine(db_uri)
    
    try:
        with engine.connect() as conn:
            # Get row count
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = result.fetchone()[0]
            
            # Get column info
            df_sample = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 1", con=conn)
            columns = list(df_sample.columns)
            
            info = {
                'table_name': table_name,
                'row_count': row_count,
                'column_count': len(columns),
                'columns': columns
            }
            
            logging.info(f"Table '{table_name}': {row_count:,} rows, {len(columns)} columns")
            return info
    
    except Exception as e:
        logging.error(f"Failed to get table info: {e}")
        raise
    finally:
        engine.dispose()


def export_to_csv(
    table_name: str,
    output_path: Path,
    db_uri: Optional[str] = None,
    query: Optional[str] = None
) -> int:
    """
    Export table or query results to CSV
    
    Args:
        table_name: Name of the table to export
        output_path: Path for output CSV file
        db_uri: Database URI (None = use default SQLite)
        query: Optional custom query (if None, exports entire table)
    
    Returns:
        Number of rows exported
    """
    if query is None:
        query = f"SELECT * FROM {table_name}"
    
    df = query_data(query, db_uri)
    
    df.to_csv(output_path, index=False)
    logging.info(f"Exported {len(df):,} rows to {output_path}")
    
    return len(df)


# Convenience function for quick setup
def quick_setup(clean_data_path: Optional[Path] = None) -> dict:
    """
    Quick setup: Load clean data to SQLite database
    
    Args:
        clean_data_path: Path to cleaned_data.csv (None = use default location)
    
    Returns:
        Dictionary with setup information
    """
    if clean_data_path is None:
        clean_data_path = PROCESSED_DATA_DIR / "cleaned_data.csv"
    
    logging.info("="*80)
    logging.info("MTLN DATABASE QUICK SETUP")
    logging.info("="*80)
    
    # Load data to SQL
    rows_loaded = load_csv_to_sql(clean_data_path, table_name="subscriptions")
    
    # Get table info
    table_info = get_table_info("subscriptions")
    
    logging.info("="*80)
    logging.info("SETUP COMPLETE!")
    logging.info(f"Database: {DEFAULT_DB_PATH}")
    logging.info(f"Table: subscriptions")
    logging.info(f"Rows: {rows_loaded:,}")
    logging.info("="*80)
    
    return {
        'database_path': str(DEFAULT_DB_PATH),
        'table_name': 'subscriptions',
        'rows_loaded': rows_loaded,
        'table_info': table_info
    }


if __name__ == "__main__":
    # Run quick setup when module is executed directly
    result = quick_setup()
    
    # Example queries
    print("\n" + "="*80)
    print("EXAMPLE QUERIES")
    print("="*80)
    
    # Query 1: Count by publication
    print("\n1. Subscriptions by Publication:")
    df = query_data("""
        SELECT Publication, COUNT(*) as count
        FROM subscriptions
        GROUP BY Publication
        ORDER BY count DESC
    """)
    print(df.to_string(index=False))
    
    # Query 2: Count by status
    print("\n2. Subscriptions by Status:")
    df = query_data("""
        SELECT Status, COUNT(*) as count
        FROM subscriptions
        GROUP BY Status
        ORDER BY count DESC
    """)
    print(df.to_string(index=False))
    
    # Query 3: Monthly trends
    print("\n3. Monthly Subscription Trends:")
    df = query_data("""
        SELECT date_of_extract, COUNT(*) as count
        FROM subscriptions
        GROUP BY date_of_extract
        ORDER BY date_of_extract
    """)
    print(df.to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ Database setup complete and verified!")
    print("="*80)
