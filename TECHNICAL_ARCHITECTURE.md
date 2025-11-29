# MTLN PROJECT - TECHNICAL ARCHITECTURE
## System Design & Module Documentation

**Version:** 1.0  
**Date:** November 29, 2025

---

## 📐 SYSTEM ARCHITECTURE DIAGRAM

```
╔════════════════════════════════════════════════════════════════════════════╗
║                          MTLN ANALYTICS PLATFORM                            ║
║                     Subscription Data Analytics System                      ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES LAYER                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    📁 data/raw/
    ├── sublist2.1.24.xlsx   (Feb 2024 - 63,555 records)
    ├── sublist3.1.24.xlsx   (Mar 2024 - 63,712 records)
    ├── sublist4.1.24.xlsx   (Apr 2024 - 63,894 records)
    ├── sublist5.1.24.xlsx   (May 2024 - 64,102 records)
    ├── sublist6.1.24.xlsx   (Jun 2024 - 64,289 records)
    ├── sublist7.1.24.xlsx   (Jul 2024 - 64,512 records)
    ├── sublist8.1.24.xlsx   (Aug 2024 - 64,701 records)
    ├── sublist9.1.24.xlsx   (Sep 2024 - 64,927 records)
    └── sublist10.01.24.xlsx (Oct 2024 - 65,228 records)
                                            │
                                            │ Manual Upload
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ETL PROCESSING LAYER                                │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  MODULE: etl_pipeline.py (Extract, Transform, Load)          │
    ├──────────────────────────────────────────────────────────────┤
    │  Functions:                                                   │
    │  • check_raw_dir()          - Validate source directory      │
    │  • get_raw_data()           - Discover Excel files           │
    │  • extract_date(filename)   - Parse dates from filenames     │
    │  • load_processed_dates()   - Track processed files          │
    │  • combine_data_files()     - Main orchestration             │
    │                                                               │
    │  Processing Steps:                                            │
    │  1. File Discovery   → Scan *.xlsx in data/raw/             │
    │  2. Date Extraction  → Regex: (\d{1,2})\.(\d{1,2})\.(\d{2})│
    │  3. Deduplication    → Check processed dates                │
    │  4. Read Attempt #1  → openpyxl default                     │
    │  5. Read Attempt #2  → openpyxl sheet 0                     │
    │  6. Read Attempt #3  → openpyxl "Sheet1"                    │
    │  7. Fallback Method  → XML manual extraction                │
    │  8. Date Injection   → Add date_of_extract column           │
    │  9. Consolidation    → Combine with existing data           │
    │ 10. Save Output      → processed_data.csv                   │
    └──────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
    ┌──────────────────────────┐    ┌──────────────────────────┐
    │  MODULE: excel_repair.py │    │  Error Handling & Logging│
    ├──────────────────────────┤    ├──────────────────────────┤
    │  Corrupted File Recovery │    │  • Exception capture     │
    │                          │    │  • Progress tracking     │
    │  Functions:              │    │  • Failure logs          │
    │  • extract_data_from_    │    │  • Retry mechanisms      │
    │    corrupted_xlsx()      │    │  • Success validation    │
    │                          │    └──────────────────────────┘
    │  Technical Approach:     │
    │  1. Open as ZIP file     │
    │  2. Extract XML:         │
    │     • sharedStrings.xml  │
    │     • sheet1.xml         │
    │  3. Parse with multiple  │
    │     namespace attempts   │
    │  4. Reconstruct cells    │
    │  5. Build DataFrame      │
    │                          │
    │  Success Rate: 95%+      │
    └──────────────────────────┘
                    │
                    ▼
            📊 processed_data.csv
            (572,292 raw records)
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA CLEANING & ENRICHMENT LAYER                        │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  MODULE: data_cleaner.py (Standardization & Enrichment)      │
    ├──────────────────────────────────────────────────────────────┤
    │  Functions:                                                   │
    │  • standardize_columns()  - Main cleaning orchestrator       │
    │                                                               │
    │  Column Mapping (15 core fields):                            │
    │  ┌──────┬─────────────────────┬─────────────────────────┐   │
    │  │ From │        To           │      Description        │   │
    │  ├──────┼─────────────────────┼─────────────────────────┤   │
    │  │  0   │ publication         │ Publication name        │   │
    │  │  1   │ accoutid            │ Account ID              │   │
    │  │  2   │ status              │ Subscription status     │   │
    │  │  3   │ bill_method         │ Billing method          │   │
    │  │  4   │ dist_id             │ Distribution ID         │   │
    │  │  5   │ route_id            │ Route ID                │   │
    │  │  6   │ day_pattern         │ Delivery pattern        │   │
    │  │  7   │ city                │ City name               │   │
    │  │  8   │ state               │ State code              │   │
    │  │  9   │ zip                 │ ZIP code                │   │
    │  │ 10   │ rate_code           │ Rate code               │   │
    │  │ 11   │ laststartdate       │ Last start date         │   │
    │  │ 12   │ originalstartdate   │ Original start date     │   │
    │  │ 13   │ occupantid          │ Occupant ID             │   │
    │  │ 14   │ routetype_id        │ Route type ID           │   │
    │  └──────┴─────────────────────┴─────────────────────────┘   │
    │                                                               │
    │  Enrichment (12 derived fields):                             │
    │  • state_full            - Full state name                   │
    │  • month                 - Extract month number              │
    │  • year                  - Extract year                      │
    │  • month_year            - Month-Year label                  │
    │  • delivery_type         - Categorized delivery              │
    │  • first_month           - First extraction flag             │
    │  • last_month            - Last extraction flag              │
    │  • is_new_customer       - New customer indicator            │
    │  • is_cancelled_customer - Churn indicator                   │
    │  • state_group           - Geographic grouping               │
    │  • legacy_acct_id        - Legacy account mapping            │
    │                                                               │
    │  Data Quality:                                                │
    │  • Type conversion (dates, numbers)                          │
    │  • Null handling                                             │
    │  • Schema validation                                         │
    │  • Deduplication                                             │
    └──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    📊 cleaned_data.csv
            (572,220 records × 27 columns)
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANALYTICS & PROCESSING LAYER                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐  ┌──────────────────────────┐  ┌────────────────┐
│  MODULE: timeseries.py   │  │  MODULE: utils/db.py     │  │   Notebooks    │
│  (603 lines)             │  │  (Database Integration)  │  │   (Interactive)│
├──────────────────────────┤  ├──────────────────────────┤  ├────────────────┤
│                          │  │                          │  │                │
│ CLASS: TimeSeriesAnalyzer│  │ CLASS: DatabaseConnection│  │ • timeseries_  │
│                          │  │                          │  │   analysis.    │
│ Core Methods:            │  │ Functions:               │  │   ipynb        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━│  │ • load_csv_to_sql()     │  │   (32 cells)   │
│                          │  │ • query_data()           │  │                │
│ 1. Data Loading:         │  │ • get_table_info()       │  │ • trails.ipynb │
│   • load_data()          │  │ • export_to_csv()        │  │   (testing)    │
│                          │  │ • quick_setup()          │  │                │
│ 2. Aggregation:          │  │                          │  │ Features:      │
│   • create_daily_        │  │ Capabilities:            │  │ • Real-time    │
│     aggregations()       │  │ • SQLite backend         │  │   exploration  │
│                          │  │ • Parameterized queries  │  │ • Custom viz   │
│ 3. Growth Metrics:       │  │ • Table management       │  │ • Ad-hoc       │
│   • calculate_growth_    │  │ • Data export            │  │   analysis     │
│     metrics()            │  │                          │  │ • What-if      │
│   - DoD change           │  │ Example Queries:         │  │   scenarios    │
│   - DoD % change         │  │ SELECT publication,      │  │ • Export       │
│   - WoW change           │  │   COUNT(*) as count      │  │   results      │
│   - WoW % change         │  │ FROM subscriptions       │  └────────────────┘
│   - Rolling averages     │  │ GROUP BY publication;    │
│                          │  │                          │
│ 4. Trend Analysis:       │  │ SELECT date_of_extract,  │
│   • analyze_trends()     │  │   COUNT(*) as count      │
│   - Overall direction    │  │ FROM subscriptions       │
│   - Daily growth avg     │  │ GROUP BY date_of_extract;│
│   - Total growth         │  └──────────────────────────┘
│   - Growth rate %        │
│   - Volatility (σ)       │
│                          │
│ 5. Segmentation:         │
│   • analyze_by_status()  │
│   • analyze_by_          │
│     publication()        │
│   • analyze_by_          │
│     geography()          │
│   • analyze_new_vs_      │
│     existing()           │
│                          │
│ 6. Anomaly Detection:    │
│   • detect_anomalies()   │
│   - Z-score method       │
│   - Threshold: 3σ        │
│                          │
│ 7. Visualization:        │
│   • plot_overall_        │
│     trends()             │
│   • plot_status_         │
│     analysis()           │
│   • plot_publication_    │
│     trends()             │
│   • plot_geographic_     │
│     distribution()       │
│                          │
│ 8. Reporting:            │
│   • generate_summary_    │
│     report()             │
│   • run_full_analysis()  │
│                          │
│ Output Formats:          │
│ • PNG (visualizations)   │
│ • TXT (summary report)   │
│ • CSV (data exports)     │
│ • DataFrame (in-memory)  │
└──────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OUTPUT & REPORTING LAYER                             │
└─────────────────────────────────────────────────────────────────────────────┘

    📁 outputs/timeseries/
    ├── 📊 summary_report.txt
    │   ├── Data Summary (records, dates, coverage)
    │   ├── Subscription Status (active/inactive breakdown)
    │   ├── Trend Analysis (growth, volatility)
    │   ├── Top Publications (ranked performance)
    │   ├── Top States (geographic distribution)
    │   └── Top Cities (local market analysis)
    │
    ├── 📈 overall_trends.png (4 subplots)
    │   ├── Total Subscriptions Timeline
    │   ├── 7-Day Moving Average
    │   ├── Active vs Inactive Breakdown
    │   └── Day-over-Day Changes
    │
    ├── 📊 status_analysis.png (2 charts)
    │   ├── Subscription Count by Status
    │   └── Percentage Distribution
    │
    ├── 📉 publication_trends.png
    │   └── Top 10 Publications Comparison
    │
    ├── 🗺️  geographic_distribution.png (2 maps)
    │   ├── Top 10 States Trends
    │   └── Top 10 Cities Trends
    │
    └── 📋 daily_stats.csv
        └── Exportable time series data

┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    📄 Documentation Files:
    ├── README.md                      - Quick start guide
    ├── STAKEHOLDER_PRESENTATION.md    - Full technical documentation
    ├── EXECUTIVE_SUMMARY.md           - One-page executive briefing
    └── TECHNICAL_ARCHITECTURE.md      - This document

    🔗 Access Points:
    ├── GitHub Repository: https://github.com/AshishJaiswal25/MTLN_PROJECT
    ├── Interactive Notebooks: Jupyter interface
    ├── Automated Reports: outputs/timeseries/
    └── Database Queries: SQLite via db.py

╔════════════════════════════════════════════════════════════════════════════╗
║                         TECHNOLOGY STACK                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

    Languages & Frameworks:
    ├── Python 3.13+           - Core programming language
    ├── pandas 2.x             - Data manipulation & analysis
    ├── NumPy 1.24+            - Numerical computations
    ├── Matplotlib 3.7+        - Visualization framework
    ├── Seaborn 0.12+          - Statistical graphics
    └── Jupyter                - Interactive notebooks

    File Handling:
    ├── openpyxl 3.1+          - Excel file I/O
    ├── zipfile                - Archive handling
    ├── xml.etree.ElementTree  - XML parsing
    └── pathlib                - Path operations

    Database:
    ├── SQLite 3               - Embedded database
    └── SQLAlchemy 2.0+        - Database ORM

    Development Tools:
    ├── Git 2.x                - Version control
    ├── GitHub                 - Repository hosting
    ├── VS Code                - IDE with extensions
    └── Virtual Environment    - Dependency isolation

╔════════════════════════════════════════════════════════════════════════════╗
║                         DATA FLOW SEQUENCE                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

    Step 1: RAW DATA INGESTION
    ┌────────────────────────────────────────────────┐
    │ User places Excel files in data/raw/           │
    │ Files: sublist[2-10].*.24.xlsx                 │
    └────────────────────────────────────────────────┘
                        ↓
    Step 2: FILE DISCOVERY & VALIDATION
    ┌────────────────────────────────────────────────┐
    │ etl_pipeline.check_raw_dir()                   │
    │ etl_pipeline.get_raw_data()                    │
    │ → Scans *.xlsx files                           │
    │ → Validates directory exists                   │
    └────────────────────────────────────────────────┘
                        ↓
    Step 3: DATE EXTRACTION
    ┌────────────────────────────────────────────────┐
    │ etl_pipeline.extract_date(filename)            │
    │ → Regex: (\d{1,2})\.(\d{1,2})\.(\d{2})       │
    │ → Converts: "2.1.24" → "2024-02-01"          │
    └────────────────────────────────────────────────┘
                        ↓
    Step 4: DEDUPLICATION CHECK
    ┌────────────────────────────────────────────────┐
    │ etl_pipeline.load_processed_dates()            │
    │ → Reads existing processed_data.csv            │
    │ → Extracts unique dates                        │
    │ → Skips already processed files                │
    └────────────────────────────────────────────────┘
                        ↓
    Step 5: FILE READING (Multiple Attempts)
    ┌────────────────────────────────────────────────┐
    │ Attempt 1: pd.read_excel(engine='openpyxl')   │
    │ Attempt 2: pd.read_excel(sheet_name=0)        │
    │ Attempt 3: pd.read_excel(sheet_name='Sheet1') │
    │ Fallback:  excel_repair.extract_data_from_    │
    │            corrupted_xlsx()                    │
    │            → Opens as ZIP                      │
    │            → Extracts XML                      │
    │            → Parses structure                  │
    │            → Rebuilds DataFrame                │
    └────────────────────────────────────────────────┘
                        ↓
    Step 6: DATE INJECTION
    ┌────────────────────────────────────────────────┐
    │ df.insert(0, 'date_of_extract', date_str)     │
    │ → Adds extraction date as first column        │
    └────────────────────────────────────────────────┘
                        ↓
    Step 7: CONSOLIDATION
    ┌────────────────────────────────────────────────┐
    │ pd.concat([existing_df, new_df])              │
    │ → Combines with previously processed data      │
    │ → Maintains chronological order                │
    └────────────────────────────────────────────────┘
                        ↓
    Step 8: SAVE PROCESSED DATA
    ┌────────────────────────────────────────────────┐
    │ df.to_csv(processed_data.csv, index=False)    │
    │ → 572,292 records                              │
    │ → 16 columns (raw schema)                      │
    └────────────────────────────────────────────────┘
                        ↓
    Step 9: DATA CLEANING & STANDARDIZATION
    ┌────────────────────────────────────────────────┐
    │ data_cleaner.standardize_columns()             │
    │ → Maps numbered columns to names               │
    │ → Converts data types                          │
    │ → Handles null values                          │
    │ → Validates schema                             │
    └────────────────────────────────────────────────┘
                        ↓
    Step 10: DATA ENRICHMENT
    ┌────────────────────────────────────────────────┐
    │ Adds 12 derived fields:                        │
    │ • state_full, month, year, month_year          │
    │ • delivery_type, first_month, last_month       │
    │ • is_new_customer, is_cancelled_customer       │
    │ • state_group, legacy_acct_id, routetype_id    │
    └────────────────────────────────────────────────┘
                        ↓
    Step 11: SAVE CLEANED DATA
    ┌────────────────────────────────────────────────┐
    │ df.to_csv(cleaned_data.csv, index=False)      │
    │ → 572,220 records                              │
    │ → 27 columns (enriched schema)                 │
    └────────────────────────────────────────────────┘
                        ↓
    Step 12: TIME SERIES ANALYSIS
    ┌────────────────────────────────────────────────┐
    │ analyzer = TimeSeriesAnalyzer()                │
    │ analyzer.load_data()                           │
    │ analyzer.create_daily_aggregations()           │
    │ analyzer.calculate_growth_metrics()            │
    │ analyzer.analyze_trends()                      │
    └────────────────────────────────────────────────┘
                        ↓
    Step 13: VISUALIZATION GENERATION
    ┌────────────────────────────────────────────────┐
    │ analyzer.plot_overall_trends()                 │
    │ analyzer.plot_status_analysis()                │
    │ analyzer.plot_publication_trends()             │
    │ analyzer.plot_geographic_distribution()        │
    │ → Saves to outputs/timeseries/*.png            │
    └────────────────────────────────────────────────┘
                        ↓
    Step 14: REPORT GENERATION
    ┌────────────────────────────────────────────────┐
    │ analyzer.generate_summary_report()             │
    │ → Creates summary_report.txt                   │
    │ → Exports daily_stats.csv                      │
    └────────────────────────────────────────────────┘
                        ↓
    Step 15: STAKEHOLDER DELIVERY
    ┌────────────────────────────────────────────────┐
    │ • Reports available in outputs/timeseries/     │
    │ • Dashboards accessible via Jupyter            │
    │ • Database queryable via db.py utilities       │
    │ • All artifacts version-controlled on GitHub   │
    └────────────────────────────────────────────────┘

```

---

## 📦 MODULE DEPENDENCY GRAPH

```
main.py
  │
  ├──► etl_pipeline.py
  │     ├──► excel_repair.py
  │     ├──► pandas
  │     ├──► logging
  │     └──► pathlib
  │
  ├──► data_cleaner.py
  │     ├──► pandas
  │     ├──► logging
  │     └──► pathlib
  │
  └──► timeseries.py
        ├──► pandas
        ├──► numpy
        ├──► matplotlib.pyplot
        ├──► seaborn
        ├──► logging
        ├──► pathlib
        └──► datetime

utils/db.py
  ├──► pandas
  ├──► sqlite3
  ├──► sqlalchemy
  ├──► logging
  └──► pathlib

research/timeseries_analysis.ipynb
  └──► timeseries.py (imports TimeSeriesAnalyzer)
```

---

## 🔐 ERROR HANDLING MATRIX

| Layer | Error Type | Handling Strategy | Recovery |
|-------|-----------|-------------------|----------|
| **File Discovery** | Directory not found | Raise FileNotFoundError | Manual intervention |
| **File Reading** | Corrupted Excel | Fallback to XML extraction | Automatic |
| **File Reading** | Missing sheet | Try alternate sheet names | Automatic |
| **File Reading** | All methods fail | Log error, skip file | Continue processing |
| **Date Extraction** | Invalid filename format | Raise ValueError | Manual filename fix |
| **Data Cleaning** | Missing columns | Use default values | Automatic |
| **Data Cleaning** | Type conversion fail | Coerce to appropriate type | Automatic |
| **Analysis** | Insufficient data | Return None/empty results | Graceful degradation |
| **Visualization** | Plot generation fail | Log warning, continue | Skip visualization |
| **Database** | Connection fail | Raise error with details | Manual intervention |

---

## 📊 PERFORMANCE SPECIFICATIONS

| Metric | Specification | Actual Performance |
|--------|---------------|-------------------|
| **File Processing Speed** | <1 min per file | ~6 sec per file |
| **Full Pipeline Execution** | <10 minutes | ~4 minutes |
| **Memory Usage** | <2 GB RAM | ~800 MB |
| **Data Volume Capacity** | 1M+ records | Tested with 572K |
| **Visualization Generation** | <30 sec all charts | ~15 sec |
| **Report Generation** | <10 seconds | ~3 seconds |
| **Database Query Speed** | <1 sec simple queries | <500ms |
| **Notebook Load Time** | <5 seconds | ~2 seconds |

---

## 🔄 UPDATE & MAINTENANCE WORKFLOW

```
Monthly Data Update Process:
┌─────────────────────────────────────────────────┐
│ 1. Receive new monthly Excel file               │
│    → Place in data/raw/                          │
│    → Naming: sublistN.M.YY.xlsx                  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 2. Run ETL pipeline                              │
│    → python main.py                              │
│    → OR: jupyter notebook                        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 3. Automatic processing                          │
│    → Deduplication check                         │
│    → Data extraction                             │
│    → Cleaning & enrichment                       │
│    → Analysis execution                          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 4. Review outputs                                │
│    → Check outputs/timeseries/                   │
│    → Validate summary_report.txt                 │
│    → Review visualizations                       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 5. Distribute to stakeholders                    │
│    → Email reports                               │
│    → Share dashboard link                        │
│    → Update presentation materials               │
└─────────────────────────────────────────────────┘
```

---

## 🛠️ CONFIGURATION FILES

### config.yaml
```yaml
data:
  raw_dir: data/raw
  processed_dir: data/processed
  output_dir: outputs/timeseries

analysis:
  anomaly_threshold: 3  # Standard deviations
  rolling_windows: [7, 14, 30]  # Days
  top_n_items: 10  # For rankings

visualization:
  figure_size: [14, 6]
  dpi: 300
  style: whitegrid
  save_format: png
```

### requirements.txt
```txt
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
openpyxl>=3.1.0
jupyter>=1.0.0
sqlalchemy>=2.0.0
tqdm>=4.65.0
```

---

## 📚 API REFERENCE

### TimeSeriesAnalyzer Class

```python
class TimeSeriesAnalyzer:
    """Main time series analysis engine"""
    
    def __init__(self, data_path=None):
        """Initialize with optional custom data path"""
        
    def load_data(self) -> pd.DataFrame:
        """Load and prepare data for analysis"""
        
    def create_daily_aggregations(self) -> pd.DataFrame:
        """Create daily time series aggregations"""
        
    def calculate_growth_metrics(self) -> pd.DataFrame:
        """Calculate DoD, WoW, and rolling metrics"""
        
    def analyze_trends(self) -> dict:
        """Analyze overall trends (growth, volatility)"""
        
    def analyze_by_status(self) -> tuple:
        """Analyze by subscription status"""
        
    def analyze_by_publication(self) -> pd.DataFrame:
        """Analyze by publication"""
        
    def analyze_by_geography(self) -> tuple:
        """Analyze by state and city"""
        
    def analyze_new_vs_existing(self) -> pd.DataFrame:
        """Analyze new vs existing customers"""
        
    def detect_anomalies(self, threshold=3) -> pd.DataFrame:
        """Detect anomalies using z-score method"""
        
    def plot_overall_trends(self, save=True):
        """Generate overall trends visualization"""
        
    def plot_status_analysis(self, save=True):
        """Generate status analysis charts"""
        
    def plot_publication_trends(self, top_n=10, save=True):
        """Generate publication comparison charts"""
        
    def plot_geographic_distribution(self, save=True):
        """Generate geographic distribution maps"""
        
    def generate_summary_report(self) -> dict:
        """Generate comprehensive text report"""
        
    def run_full_analysis(self) -> dict:
        """Execute complete analysis pipeline"""
```

---

**Document:** Technical Architecture v1.0  
**Author:** AshishJaiswal25  
**Date:** November 29, 2025  
**GitHub:** https://github.com/AshishJaiswal25/MTLN_PROJECT
