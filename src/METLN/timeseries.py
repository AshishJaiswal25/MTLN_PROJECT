"""
Time Series Analysis Module for MTLN Project
Performs comprehensive time series analysis on subscription data
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] : %(message)s:')

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CLEAN_FILE = PROCESSED_DATA_DIR / "cleaned_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "timeseries"


class TimeSeriesAnalyzer:
    """
    Comprehensive Time Series Analysis for subscription data
    """
    
    def __init__(self, data_path=None):
        """
        Initialize the TimeSeriesAnalyzer
        
        Args:
            data_path: Path to the clean data CSV file
        """
        self.data_path = data_path or CLEAN_FILE
        self.df = None
        self.ts_data = None
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logging.info(f"TimeSeriesAnalyzer initialized. Output directory: {OUTPUT_DIR}")
    
    def load_data(self):
        """Load and prepare data for time series analysis"""
        logging.info(f"Loading data from {self.data_path}")
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        # Load data with optimized memory usage
        self.df = pd.read_csv(self.data_path, low_memory=False)
        logging.info(f"Loaded {len(self.df):,} rows and {len(self.df.columns)} columns")
        
        # Convert date columns to datetime
        self.df['date_of_extract'] = pd.to_datetime(self.df['date_of_extract'])
        
        # Convert LastStartDate and OriginalStartDate
        for col in ['LastStartDate', 'OriginalStartDate']:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
        
        logging.info(f"Date range: {self.df['date_of_extract'].min()} to {self.df['date_of_extract'].max()}")
        logging.info(f"Unique extraction dates: {self.df['date_of_extract'].nunique()}")
        
        return self.df
    
    def create_daily_aggregations(self):
        """
        Create daily time series aggregations
        """
        logging.info("Creating daily aggregations...")
        
        # Group by date and calculate various metrics
        daily_stats = self.df.groupby('date_of_extract').agg({
            'accoutid': 'count',  # Total subscriptions
            'status': lambda x: (x == 'A').sum(),  # Active subscriptions
            'publication': 'nunique',  # Number of publications
            'city': 'nunique',  # Number of cities
            'state': 'nunique',  # Number of states
            'route_id': 'nunique',  # Number of routes
        }).rename(columns={
            'accoutid': 'total_subscriptions',
            'status': 'active_subscriptions',
            'publication': 'unique_publications',
            'city': 'unique_cities',
            'state': 'unique_states',
            'route_id': 'unique_routes'
        })
        
        # Calculate inactive subscriptions
        daily_stats['inactive_subscriptions'] = (
            daily_stats['total_subscriptions'] - daily_stats['active_subscriptions']
        )
        
        # Calculate activation rate
        daily_stats['activation_rate'] = (
            daily_stats['active_subscriptions'] / daily_stats['total_subscriptions'] * 100
        )
        
        self.ts_data = daily_stats
        logging.info(f"Created daily aggregations for {len(daily_stats)} days")
        
        return daily_stats
    
    def calculate_growth_metrics(self):
        """
        Calculate growth metrics over time
        """
        if self.ts_data is None:
            self.create_daily_aggregations()
        
        logging.info("Calculating growth metrics...")
        
        # Sort by date
        ts_sorted = self.ts_data.sort_index()
        
        # Calculate day-over-day change
        ts_sorted['dod_change'] = ts_sorted['total_subscriptions'].diff()
        ts_sorted['dod_pct_change'] = ts_sorted['total_subscriptions'].pct_change() * 100
        
        # Calculate week-over-week change (if we have enough data)
        if len(ts_sorted) >= 7:
            ts_sorted['wow_change'] = ts_sorted['total_subscriptions'].diff(7)
            ts_sorted['wow_pct_change'] = ts_sorted['total_subscriptions'].pct_change(7) * 100
        
        # Calculate rolling averages
        for window in [7, 14, 30]:
            if len(ts_sorted) >= window:
                ts_sorted[f'rolling_avg_{window}d'] = (
                    ts_sorted['total_subscriptions'].rolling(window=window).mean()
                )
        
        self.ts_data = ts_sorted
        
        return ts_sorted
    
    def analyze_trends(self):
        """
        Analyze trends in the time series data
        """
        if self.ts_data is None:
            self.calculate_growth_metrics()
        
        logging.info("Analyzing trends...")
        
        results = {
            'overall_trend': None,
            'avg_daily_growth': None,
            'total_growth': None,
            'growth_rate': None,
            'volatility': None
        }
        
        # Calculate overall trend
        if len(self.ts_data) > 1:
            first_value = self.ts_data['total_subscriptions'].iloc[0]
            last_value = self.ts_data['total_subscriptions'].iloc[-1]
            
            results['total_growth'] = last_value - first_value
            results['growth_rate'] = (last_value / first_value - 1) * 100 if first_value > 0 else 0
            results['avg_daily_growth'] = results['total_growth'] / len(self.ts_data)
            results['overall_trend'] = 'Growing' if results['total_growth'] > 0 else 'Declining'
            
            # Calculate volatility (standard deviation of daily changes)
            results['volatility'] = self.ts_data['dod_change'].std()
        
        logging.info(f"Trend Analysis Results:")
        for key, value in results.items():
            if isinstance(value, (int, float)):
                logging.info(f"  {key}: {value:.2f}")
            else:
                logging.info(f"  {key}: {value}")
        
        return results
    
    def analyze_by_status(self):
        """
        Analyze time series by subscription status
        """
        logging.info("Analyzing by subscription status...")
        
        status_ts = self.df.groupby(['date_of_extract', 'status']).size().unstack(fill_value=0)
        
        # Calculate percentages
        status_pct = status_ts.div(status_ts.sum(axis=1), axis=0) * 100
        
        return status_ts, status_pct
    
    def analyze_by_publication(self):
        """
        Analyze time series by publication
        """
        logging.info("Analyzing by publication...")
        
        pub_ts = self.df.groupby(['date_of_extract', 'publication']).size().unstack(fill_value=0)
        
        return pub_ts
    
    def analyze_by_geography(self):
        """
        Analyze time series by geography (State and City)
        """
        logging.info("Analyzing by geography...")
        
        # By State
        state_ts = self.df.groupby(['date_of_extract', 'state']).size().unstack(fill_value=0)
        
        # Top cities over time
        top_cities = self.df['city'].value_counts().head(10).index
        city_ts = self.df[self.df['city'].isin(top_cities)].groupby(
            ['date_of_extract', 'city']
        ).size().unstack(fill_value=0)
        
        return state_ts, city_ts
    
    def analyze_new_vs_existing(self):
        """
        Analyze new subscriptions vs existing subscriptions over time
        """
        logging.info("Analyzing new vs existing subscriptions...")
        
        if 'LastStartDate' not in self.df.columns:
            logging.warning("LastStartDate column not found. Skipping new vs existing analysis.")
            return None
        
        # For each extraction date, categorize subscriptions
        results = []
        
        for date in sorted(self.df['date_of_extract'].unique()):
            date_data = self.df[self.df['date_of_extract'] == date].copy()
            
            # New subscriptions: LastStartDate is same as extraction date or within last 30 days
            date_pd = pd.to_datetime(date)
            threshold = date_pd - timedelta(days=30)
            
            new_subs = date_data[date_data['LastStartDate'] >= threshold].shape[0]
            existing_subs = date_data.shape[0] - new_subs
            
            results.append({
                'date': date,
                'new_subscriptions': new_subs,
                'existing_subscriptions': existing_subs,
                'total': date_data.shape[0]
            })
        
        new_vs_existing = pd.DataFrame(results).set_index('date')
        
        return new_vs_existing
    
    def detect_anomalies(self, threshold=3):
        """
        Detect anomalies in the time series using statistical methods
        
        Args:
            threshold: Number of standard deviations for anomaly detection
        """
        if self.ts_data is None:
            self.calculate_growth_metrics()
        
        logging.info(f"Detecting anomalies (threshold: {threshold} std devs)...")
        
        # Calculate z-scores
        mean = self.ts_data['total_subscriptions'].mean()
        std = self.ts_data['total_subscriptions'].std()
        
        self.ts_data['z_score'] = (self.ts_data['total_subscriptions'] - mean) / std
        self.ts_data['is_anomaly'] = np.abs(self.ts_data['z_score']) > threshold
        
        anomalies = self.ts_data[self.ts_data['is_anomaly']]
        
        logging.info(f"Found {len(anomalies)} anomalies")
        
        return anomalies
    
    def plot_overall_trends(self, save=True):
        """
        Create comprehensive trend visualizations
        """
        if self.ts_data is None:
            self.calculate_growth_metrics()
        
        logging.info("Creating trend visualizations...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Time Series Analysis - Overall Trends', fontsize=16, fontweight='bold')
        
        # Plot 1: Total Subscriptions Over Time
        ax1 = axes[0, 0]
        ax1.plot(self.ts_data.index, self.ts_data['total_subscriptions'], 
                marker='o', linewidth=2, markersize=6, label='Total Subscriptions')
        
        # Add rolling average if available
        if 'rolling_avg_7d' in self.ts_data.columns:
            ax1.plot(self.ts_data.index, self.ts_data['rolling_avg_7d'], 
                    linestyle='--', linewidth=2, alpha=0.7, label='7-day Moving Avg')
        
        ax1.set_title('Total Subscriptions Over Time', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Number of Subscriptions')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Active vs Inactive Subscriptions
        ax2 = axes[0, 1]
        ax2.plot(self.ts_data.index, self.ts_data['active_subscriptions'], 
                marker='o', linewidth=2, label='Active', color='green')
        ax2.plot(self.ts_data.index, self.ts_data['inactive_subscriptions'], 
                marker='s', linewidth=2, label='Inactive', color='red')
        ax2.set_title('Active vs Inactive Subscriptions', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Number of Subscriptions')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Activation Rate Over Time
        ax3 = axes[1, 0]
        ax3.plot(self.ts_data.index, self.ts_data['activation_rate'], 
                marker='o', linewidth=2, color='orange')
        ax3.set_title('Activation Rate Over Time', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Date')
        ax3.set_ylabel('Activation Rate (%)')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Day-over-Day Change
        ax4 = axes[1, 1]
        colors = ['green' if x >= 0 else 'red' for x in self.ts_data['dod_change'].fillna(0)]
        ax4.bar(self.ts_data.index, self.ts_data['dod_change'].fillna(0), color=colors, alpha=0.7)
        ax4.set_title('Day-over-Day Change in Subscriptions', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Date')
        ax4.set_ylabel('Change in Subscriptions')
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            plot_path = OUTPUT_DIR / 'overall_trends.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            logging.info(f"Saved plot to {plot_path}")
        
        plt.show()
        
        return fig
    
    def plot_status_analysis(self, save=True):
        """
        Visualize subscription status distribution over time
        """
        status_ts, status_pct = self.analyze_by_status()
        
        logging.info("Creating status analysis visualizations...")
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Subscription Status Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Stacked Area Chart (Counts)
        ax1 = axes[0]
        status_ts.plot(kind='area', stacked=True, ax=ax1, alpha=0.7)
        ax1.set_title('Subscription Count by Status', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Number of Subscriptions')
        ax1.legend(title='status', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Stacked Area Chart (Percentages)
        ax2 = axes[1]
        status_pct.plot(kind='area', stacked=True, ax=ax2, alpha=0.7)
        ax2.set_title('Subscription Percentage by Status', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Percentage (%)')
        ax2.legend(title='status', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            plot_path = OUTPUT_DIR / 'status_analysis.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            logging.info(f"Saved plot to {plot_path}")
        
        plt.show()
        
        return fig
    
    def plot_publication_trends(self, top_n=10, save=True):
        """
        Visualize trends by publication
        """
        pub_ts = self.analyze_by_publication()
        
        # Get top N publications by total count
        top_pubs = pub_ts.sum().nlargest(top_n).index
        pub_ts_top = pub_ts[top_pubs]
        
        logging.info(f"Creating publication trends visualization (top {top_n})...")
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        for pub in top_pubs:
            ax.plot(pub_ts_top.index, pub_ts_top[pub], marker='o', linewidth=2, label=pub)
        
        ax.set_title(f'Top {top_n} Publications - Subscription Trends', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Subscriptions')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            plot_path = OUTPUT_DIR / 'publication_trends.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            logging.info(f"Saved plot to {plot_path}")
        
        plt.show()
        
        return fig
    
    def plot_geographic_distribution(self, save=True):
        """
        Visualize geographic distribution over time
        """
        state_ts, city_ts = self.analyze_by_geography()
        
        logging.info("Creating geographic distribution visualizations...")
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 12))
        fig.suptitle('Geographic Distribution Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: States
        ax1 = axes[0]
        top_states = state_ts.sum().nlargest(10).index
        state_ts[top_states].plot(ax=ax1, marker='o', linewidth=2)
        ax1.set_title('Top 10 States - Subscription Trends', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Number of Subscriptions')
        ax1.legend(title='state', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Cities
        ax2 = axes[1]
        city_ts.plot(ax=ax2, marker='o', linewidth=2)
        ax2.set_title('Top 10 Cities - Subscription Trends', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Number of Subscriptions')
        ax2.legend(title='city', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            plot_path = OUTPUT_DIR / 'geographic_distribution.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            logging.info(f"Saved plot to {plot_path}")
        
        plt.show()
        
        return fig
    
    def generate_summary_report(self):
        """
        Generate a comprehensive summary report
        """
        logging.info("Generating summary report...")
        
        if self.df is None:
            self.load_data()
        
        if self.ts_data is None:
            self.calculate_growth_metrics()
        
        trends = self.analyze_trends()
        
        report = {
            'data_summary': {
                'total_records': len(self.df),
                'date_range': f"{self.df['date_of_extract'].min()} to {self.df['date_of_extract'].max()}",
                'unique_dates': self.df['date_of_extract'].nunique(),
                'unique_accounts': self.df['accoutid'].nunique(),
                'unique_publications': self.df['publication'].nunique(),
                'unique_states': self.df['state'].nunique(),
                'unique_cities': self.df['city'].nunique(),
            },
            'subscription_status': {
                'total_subscriptions': len(self.df),
                'active_subscriptions': (self.df['status'] == 'A').sum(),
                'inactive_subscriptions': (self.df['status'] != 'A').sum(),
                'activation_rate': (self.df['status'] == 'A').sum() / len(self.df) * 100,
            },
            'trend_analysis': trends,
            'top_publications': self.df['publication'].value_counts().head(10).to_dict(),
            'top_states': self.df['state'].value_counts().head(10).to_dict(),
            'top_cities': self.df['city'].value_counts().head(10).to_dict(),
        }
        
        # Print report
        print("\n" + "="*80)
        print("TIME SERIES ANALYSIS SUMMARY REPORT")
        print("="*80)
        
        print("\n📊 DATA SUMMARY")
        print("-" * 80)
        for key, value in report['data_summary'].items():
            print(f"  {key.replace('_', ' ').title()}: {value:,}" if isinstance(value, int) else f"  {key.replace('_', ' ').title()}: {value}")
        
        print("\n📈 SUBSCRIPTION STATUS")
        print("-" * 80)
        for key, value in report['subscription_status'].items():
            if isinstance(value, float):
                print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")
            else:
                print(f"  {key.replace('_', ' ').title()}: {value:,}")
        
        print("\n📉 TREND ANALYSIS")
        print("-" * 80)
        for key, value in report['trend_analysis'].items():
            if isinstance(value, float):
                print(f"  {key.replace('_', ' ').title()}: {value:.2f}")
            else:
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print("\n📰 TOP 10 PUBLICATIONS")
        print("-" * 80)
        for i, (pub, count) in enumerate(report['top_publications'].items(), 1):
            print(f"  {i:2d}. {pub:20s}: {count:,} subscriptions")
        
        print("\n🗺️  TOP 10 STATES")
        print("-" * 80)
        for i, (state, count) in enumerate(report['top_states'].items(), 1):
            print(f"  {i:2d}. {state:20s}: {count:,} subscriptions")
        
        print("\n🏙️  TOP 10 CITIES")
        print("-" * 80)
        for i, (city, count) in enumerate(report['top_cities'].items(), 1):
            print(f"  {i:2d}. {city:20s}: {count:,} subscriptions")
        
        print("\n" + "="*80)
        
        # Save report to file
        report_path = OUTPUT_DIR / 'summary_report.txt'
        with open(report_path, 'w') as f:
            f.write("TIME SERIES ANALYSIS SUMMARY REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for section, data in report.items():
                f.write(f"\n{section.upper().replace('_', ' ')}\n")
                f.write("-" * 80 + "\n")
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")
        
        logging.info(f"Report saved to {report_path}")
        
        return report
    
    def run_full_analysis(self):
        """
        Run complete time series analysis pipeline
        """
        logging.info("Starting full time series analysis...")
        
        # Load data
        self.load_data()
        
        # Create aggregations and calculate metrics
        self.create_daily_aggregations()
        self.calculate_growth_metrics()
        
        # Analyze trends
        self.analyze_trends()
        
        # Detect anomalies
        anomalies = self.detect_anomalies()
        
        # Generate all visualizations
        self.plot_overall_trends()
        self.plot_status_analysis()
        self.plot_publication_trends()
        self.plot_geographic_distribution()
        
        # Generate summary report
        report = self.generate_summary_report()
        
        logging.info("Full analysis complete!")
        
        return report


def main():
    """
    Main function to run time series analysis
    """
    analyzer = TimeSeriesAnalyzer()
    report = analyzer.run_full_analysis()
    
    print("\n✅ Time series analysis complete!")
    print(f"📁 All outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
