#!/usr/bin/env python3
"""
Data Validation Suite for Loudoun County Property Sales Database

Provides comprehensive data quality analysis, outlier detection, and market statistics.
Generates detailed validation reports with visualizations.

Author: Property Valuation System
Version: 1.0.0
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json

# Visualization
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Container for validation results."""
    completeness_score: float
    total_records: int
    flagged_records: int
    missing_values: Dict[str, int]
    outliers: Dict[str, List[int]]
    quality_issues: List[str]
    market_stats: Dict


class DatabaseInspector:
    """Inspects database structure and validates schema."""

    def __init__(self, db_path: str):
        """Initialize inspector with database path."""
        self.db_path = Path(db_path)
        self.conn = None

    def connect(self):
        """Connect to database."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def inspect_schema(self) -> Dict:
        """Inspect database schema and structure."""
        cursor = self.conn.cursor()

        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        schema_info = {}

        for table in tables:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]

            schema_info[table] = {
                'columns': [
                    {
                        'name': col[1],
                        'type': col[2],
                        'nullable': not col[3],
                        'primary_key': bool(col[5])
                    }
                    for col in columns
                ],
                'row_count': row_count
            }

        return schema_info

    def validate_required_fields(self, table: str, required_fields: List[str]) -> Tuple[bool, List[str]]:
        """Validate that required fields exist in table."""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]

        missing = [field for field in required_fields if field not in columns]

        return len(missing) == 0, missing

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class DataQualityAnalyzer:
    """Analyzes data quality and detects issues."""

    def __init__(self, db_path: str):
        """Initialize analyzer with database path."""
        self.db_path = db_path
        self.df = None

    def load_data(self) -> pd.DataFrame:
        """Load sales data from database."""
        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM sales"
        self.df = pd.read_sql_query(query, conn)

        conn.close()

        logger.info(f"Loaded {len(self.df)} records from database")
        return self.df

    def analyze_missing_values(self) -> Dict[str, int]:
        """Analyze missing values by field."""
        missing = {}

        for column in self.df.columns:
            null_count = self.df[column].isnull().sum()
            if null_count > 0:
                missing[column] = int(null_count)

        return missing

    def detect_price_outliers(self, method: str = 'zscore', threshold: float = 3.0) -> List[int]:
        """
        Detect outliers in sale prices.

        Args:
            method: 'zscore' or 'iqr'
            threshold: Z-score threshold or IQR multiplier

        Returns:
            List of record IDs that are outliers
        """
        if 'sale_price' not in self.df.columns:
            return []

        prices = self.df['sale_price'].dropna()

        if method == 'zscore':
            z_scores = np.abs((prices - prices.mean()) / prices.std())
            outlier_mask = z_scores > threshold

        elif method == 'iqr':
            Q1 = prices.quantile(0.25)
            Q3 = prices.quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR

            outlier_mask = (prices < lower_bound) | (prices > upper_bound)

        else:
            raise ValueError(f"Unknown method: {method}")

        outlier_ids = self.df.loc[outlier_mask[outlier_mask].index, 'id'].tolist()

        logger.info(f"Detected {len(outlier_ids)} price outliers using {method} method")
        return outlier_ids

    def flag_suspicious_data(self) -> Dict[str, List[int]]:
        """Flag suspicious data based on business rules."""
        flagged = {
            'unrealistic_price': [],
            'unrealistic_sqft': [],
            'invalid_date': [],
            'price_per_sqft_outlier': []
        }

        # Flag unrealistic prices
        if 'sale_price' in self.df.columns:
            unrealistic_price = self.df[
                (self.df['sale_price'] < 50000) | (self.df['sale_price'] > 5000000)
            ]
            flagged['unrealistic_price'] = unrealistic_price['id'].tolist()

        # Flag unrealistic square footage
        if 'sqft' in self.df.columns:
            unrealistic_sqft = self.df[
                (self.df['sqft'] < 500) | (self.df['sqft'] > 10000)
            ]
            flagged['unrealistic_sqft'] = unrealistic_sqft['id'].tolist()

        # Flag invalid dates
        if 'sale_date' in self.df.columns:
            self.df['sale_date'] = pd.to_datetime(self.df['sale_date'], errors='coerce')

            min_date = datetime.now() - timedelta(days=3*365)  # 3 years ago
            max_date = datetime.now() + timedelta(days=30)  # 30 days future

            invalid_dates = self.df[
                (self.df['sale_date'] < min_date) | (self.df['sale_date'] > max_date)
            ]
            flagged['invalid_date'] = invalid_dates['id'].tolist()

        # Flag price per sqft outliers
        if 'sale_price' in self.df.columns and 'sqft' in self.df.columns:
            df_valid = self.df[(self.df['sale_price'] > 0) & (self.df['sqft'] > 0)].copy()
            df_valid['price_per_sqft'] = df_valid['sale_price'] / df_valid['sqft']

            median_ppsf = df_valid['price_per_sqft'].median()
            std_ppsf = df_valid['price_per_sqft'].std()

            ppsf_outliers = df_valid[
                np.abs(df_valid['price_per_sqft'] - median_ppsf) > 3 * std_ppsf
            ]
            flagged['price_per_sqft_outlier'] = ppsf_outliers['id'].tolist()

        # Log summary
        total_flagged = sum(len(ids) for ids in flagged.values())
        logger.info(f"Flagged {total_flagged} suspicious records across {len(flagged)} categories")

        return flagged

    def detect_duplicates(self) -> pd.DataFrame:
        """Detect potential duplicate records."""
        # Check for exact duplicates on key fields
        key_fields = ['address', 'sale_date', 'sale_price']
        existing_fields = [f for f in key_fields if f in self.df.columns]

        if not existing_fields:
            return pd.DataFrame()

        duplicates = self.df[self.df.duplicated(subset=existing_fields, keep=False)]

        logger.info(f"Found {len(duplicates)} potential duplicate records")
        return duplicates


class MarketStatisticsCalculator:
    """Calculates market statistics and trends."""

    def __init__(self, df: pd.DataFrame):
        """Initialize calculator with dataframe."""
        self.df = df.copy()

        # Ensure sale_date is datetime
        if 'sale_date' in self.df.columns:
            self.df['sale_date'] = pd.to_datetime(self.df['sale_date'], errors='coerce')

        # Calculate price per sqft
        if 'sale_price' in self.df.columns and 'sqft' in self.df.columns:
            valid_mask = (self.df['sale_price'] > 0) & (self.df['sqft'] > 0)
            self.df.loc[valid_mask, 'price_per_sqft'] = (
                self.df.loc[valid_mask, 'sale_price'] / self.df.loc[valid_mask, 'sqft']
            )

    def calculate_by_zip(self) -> pd.DataFrame:
        """Calculate statistics by ZIP code."""
        if 'zip_code' not in self.df.columns:
            return pd.DataFrame()

        stats = self.df.groupby('zip_code').agg({
            'sale_price': ['count', 'median', 'mean', 'std'],
            'price_per_sqft': ['median', 'mean', 'std'],
            'sqft': ['median', 'mean']
        }).round(2)

        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        stats = stats.reset_index()

        return stats

    def calculate_overall_stats(self) -> Dict:
        """Calculate overall market statistics."""
        stats = {}

        if 'sale_price' in self.df.columns:
            prices = self.df['sale_price'].dropna()
            stats['total_sales'] = len(prices)
            stats['median_price'] = float(prices.median())
            stats['mean_price'] = float(prices.mean())
            stats['std_price'] = float(prices.std())
            stats['min_price'] = float(prices.min())
            stats['max_price'] = float(prices.max())

        if 'price_per_sqft' in self.df.columns:
            ppsf = self.df['price_per_sqft'].dropna()
            stats['median_price_per_sqft'] = float(ppsf.median())
            stats['mean_price_per_sqft'] = float(ppsf.mean())
            stats['std_price_per_sqft'] = float(ppsf.std())

        if 'sqft' in self.df.columns:
            sqft = self.df['sqft'].dropna()
            stats['median_sqft'] = float(sqft.median())
            stats['mean_sqft'] = float(sqft.mean())

        return stats

    def calculate_monthly_trends(self) -> pd.DataFrame:
        """Calculate monthly price trends."""
        if 'sale_date' not in self.df.columns or 'sale_price' not in self.df.columns:
            return pd.DataFrame()

        df_valid = self.df[self.df['sale_date'].notna() & self.df['sale_price'].notna()].copy()

        df_valid['year_month'] = df_valid['sale_date'].dt.to_period('M')

        monthly = df_valid.groupby('year_month').agg({
            'sale_price': ['count', 'median', 'mean'],
            'price_per_sqft': ['median', 'mean']
        }).round(2)

        monthly.columns = ['_'.join(col).strip() for col in monthly.columns.values]
        monthly = monthly.reset_index()
        monthly['year_month'] = monthly['year_month'].astype(str)

        return monthly

    def calculate_volume_by_property_type(self) -> pd.DataFrame:
        """Calculate sales volume by property type."""
        if 'property_type' not in self.df.columns:
            return pd.DataFrame()

        volume = self.df.groupby('property_type').agg({
            'sale_price': ['count', 'median', 'mean']
        }).round(2)

        volume.columns = ['_'.join(col).strip() for col in volume.columns.values]
        volume = volume.reset_index()

        return volume


class ValidationReportGenerator:
    """Generates comprehensive validation report with visualizations."""

    def __init__(self, output_path: str = "validation_report.html"):
        """Initialize report generator."""
        self.output_path = Path(output_path)
        self.figures = []

    def create_visualizations(self, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Create visualization charts."""
        plt.style.use('seaborn-v0_8-darkgrid')
        fig_paths = []

        # 1. Price distribution histogram
        if 'sale_price' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            df['sale_price'].dropna().hist(bins=50, ax=ax, edgecolor='black')
            ax.set_xlabel('Sale Price ($)')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Sale Prices')
            ax.ticklabel_format(style='plain', axis='x')

            fig_path = 'price_distribution.png'
            plt.tight_layout()
            plt.savefig(fig_path, dpi=100, bbox_inches='tight')
            plt.close()
            fig_paths.append(fig_path)

        # 2. Price per sqft distribution
        if 'price_per_sqft' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            df['price_per_sqft'].dropna().hist(bins=50, ax=ax, edgecolor='black')
            ax.set_xlabel('Price per Sqft ($)')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Price per Square Foot')

            fig_path = 'price_per_sqft_distribution.png'
            plt.tight_layout()
            plt.savefig(fig_path, dpi=100, bbox_inches='tight')
            plt.close()
            fig_paths.append(fig_path)

        # 3. Sales by ZIP code
        if 'zip_code' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            zip_counts = df['zip_code'].value_counts().sort_index()
            zip_counts.plot(kind='bar', ax=ax, color='steelblue', edgecolor='black')
            ax.set_xlabel('ZIP Code')
            ax.set_ylabel('Number of Sales')
            ax.set_title('Sales Volume by ZIP Code')
            plt.xticks(rotation=45)

            fig_path = 'sales_by_zip.png'
            plt.tight_layout()
            plt.savefig(fig_path, dpi=100, bbox_inches='tight')
            plt.close()
            fig_paths.append(fig_path)

        # 4. Price vs Square Footage scatter
        if 'sale_price' in df.columns and 'sqft' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            df_plot = df[(df['sale_price'] > 0) & (df['sqft'] > 0)]
            ax.scatter(df_plot['sqft'], df_plot['sale_price'], alpha=0.5, s=20)
            ax.set_xlabel('Square Footage')
            ax.set_ylabel('Sale Price ($)')
            ax.set_title('Sale Price vs Square Footage')
            ax.ticklabel_format(style='plain', axis='y')

            fig_path = 'price_vs_sqft.png'
            plt.tight_layout()
            plt.savefig(fig_path, dpi=100, bbox_inches='tight')
            plt.close()
            fig_paths.append(fig_path)

        # 5. Monthly sales trend
        if 'sale_date' in df.columns:
            df_valid = df[df['sale_date'].notna()].copy()
            if len(df_valid) > 0:
                df_valid['year_month'] = df_valid['sale_date'].dt.to_period('M')
                monthly_counts = df_valid.groupby('year_month').size()

                fig, ax = plt.subplots(figsize=(12, 6))
                monthly_counts.plot(kind='line', ax=ax, marker='o', linewidth=2)
                ax.set_xlabel('Month')
                ax.set_ylabel('Number of Sales')
                ax.set_title('Sales Volume Over Time')
                plt.xticks(rotation=45)

                fig_path = 'monthly_sales_trend.png'
                plt.tight_layout()
                plt.savefig(fig_path, dpi=100, bbox_inches='tight')
                plt.close()
                fig_paths.append(fig_path)

        return fig_paths

    def generate_html_report(
        self,
        validation_result: ValidationResult,
        df: pd.DataFrame,
        zip_stats: pd.DataFrame,
        monthly_trends: pd.DataFrame,
        flagged_records: pd.DataFrame
    ):
        """Generate comprehensive HTML validation report."""

        # Create visualizations
        fig_paths = self.create_visualizations(df, validation_result.market_stats)

        # Build HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Loudoun County Sales Data Validation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        .metric-box {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            min-width: 200px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .chart {{
            margin: 20px 0;
            text-align: center;
        }}
        .chart img {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .issue-list {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Loudoun County Sales Data Validation Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Summary Metrics</h2>
        <div class="metric-box success">
            <div class="metric-value">{validation_result.completeness_score:.1f}%</div>
            <div class="metric-label">Data Completeness</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{validation_result.total_records:,}</div>
            <div class="metric-label">Total Records</div>
        </div>
        <div class="metric-box {'warning' if validation_result.flagged_records > 0 else 'success'}">
            <div class="metric-value">{validation_result.flagged_records:,}</div>
            <div class="metric-label">Flagged for Review</div>
        </div>

        <h2>Data Quality Issues</h2>
"""

        if validation_result.quality_issues:
            html += "<div class='issue-list'><ul>"
            for issue in validation_result.quality_issues:
                html += f"<li>{issue}</li>"
            html += "</ul></div>"
        else:
            html += "<p>✓ No major quality issues detected!</p>"

        # Missing values
        if validation_result.missing_values:
            html += "<h3>Missing Values by Field</h3><table>"
            html += "<tr><th>Field</th><th>Missing Count</th><th>Percentage</th></tr>"
            for field, count in validation_result.missing_values.items():
                pct = (count / validation_result.total_records * 100)
                html += f"<tr><td>{field}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>"
            html += "</table>"

        # Market statistics
        html += "<h2>Market Statistics</h2>"
        if validation_result.market_stats:
            html += "<table><tr><th>Metric</th><th>Value</th></tr>"
            for key, value in validation_result.market_stats.items():
                if isinstance(value, float):
                    formatted_value = f"${value:,.2f}" if 'price' in key.lower() else f"{value:,.2f}"
                else:
                    formatted_value = f"{value:,}"
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{formatted_value}</td></tr>"
            html += "</table>"

        # ZIP code statistics
        if not zip_stats.empty:
            html += "<h2>Statistics by ZIP Code</h2>"
            html += zip_stats.to_html(index=False, classes='dataframe', border=0)

        # Monthly trends
        if not monthly_trends.empty:
            html += "<h2>Monthly Trends</h2>"
            html += monthly_trends.head(12).to_html(index=False, classes='dataframe', border=0)

        # Visualizations
        html += "<h2>Data Visualizations</h2>"
        for fig_path in fig_paths:
            html += f"<div class='chart'><img src='{fig_path}' alt='Chart'></div>"

        # Flagged records
        if not flagged_records.empty:
            html += f"<h2>Flagged Records ({len(flagged_records)} total)</h2>"
            html += "<p>Top 50 flagged records shown below. Full list exported to flagged_records.csv</p>"
            html += flagged_records.head(50).to_html(index=False, classes='dataframe', border=0)

        html += """
    </div>
</body>
</html>
"""

        # Write HTML file
        with open(self.output_path, 'w') as f:
            f.write(html)

        logger.info(f"HTML report generated: {self.output_path}")


def validate_database(
    db_path: str = "loudoun_sales.db",
    output_html: str = "validation_report.html"
) -> ValidationResult:
    """
    Run comprehensive database validation.

    Args:
        db_path: Path to SQLite database
        output_html: Path for HTML report output

    Returns:
        ValidationResult object
    """
    logger.info("="*80)
    logger.info("STARTING DATA VALIDATION")
    logger.info("="*80)

    # 1. Inspect database
    logger.info("\n1. Inspecting database schema...")
    with DatabaseInspector(db_path) as inspector:
        schema = inspector.inspect_schema()

        logger.info(f"Tables found: {list(schema.keys())}")
        for table, info in schema.items():
            logger.info(f"  {table}: {info['row_count']} rows, {len(info['columns'])} columns")

        # Validate required fields
        required_fields = ['address', 'sale_date', 'sale_price', 'sqft', 'zip_code']
        is_valid, missing = inspector.validate_required_fields('sales', required_fields)

        if not is_valid:
            logger.warning(f"Missing required fields: {missing}")

    # 2. Load and analyze data
    logger.info("\n2. Analyzing data quality...")
    analyzer = DataQualityAnalyzer(db_path)
    df = analyzer.load_data()

    missing_values = analyzer.analyze_missing_values()
    logger.info(f"Missing values detected in {len(missing_values)} fields")

    # 3. Detect outliers and suspicious data
    logger.info("\n3. Detecting outliers and suspicious data...")
    price_outliers = analyzer.detect_price_outliers(method='zscore', threshold=3.0)
    flagged_data = analyzer.flag_suspicious_data()
    duplicates = analyzer.detect_duplicates()

    # 4. Calculate market statistics
    logger.info("\n4. Calculating market statistics...")
    calc = MarketStatisticsCalculator(df)
    overall_stats = calc.calculate_overall_stats()
    zip_stats = calc.calculate_by_zip()
    monthly_trends = calc.calculate_monthly_trends()

    logger.info(f"Overall median price: ${overall_stats.get('median_price', 0):,.2f}")
    logger.info(f"Overall median price/sqft: ${overall_stats.get('median_price_per_sqft', 0):,.2f}")

    # 5. Calculate completeness score
    total_fields = len(df.columns)
    total_cells = len(df) * total_fields
    missing_cells = sum(missing_values.values())
    completeness_score = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0

    # 6. Compile quality issues
    quality_issues = []

    if len(price_outliers) > 0:
        quality_issues.append(f"{len(price_outliers)} price outliers detected")

    for issue_type, ids in flagged_data.items():
        if len(ids) > 0:
            quality_issues.append(f"{len(ids)} records with {issue_type.replace('_', ' ')}")

    if len(duplicates) > 0:
        quality_issues.append(f"{len(duplicates)} potential duplicate records")

    # 7. Create flagged records dataframe
    all_flagged_ids = set()
    all_flagged_ids.update(price_outliers)
    for ids in flagged_data.values():
        all_flagged_ids.update(ids)

    flagged_records = df[df['id'].isin(all_flagged_ids)].copy()

    # Add flag reasons
    def get_flag_reasons(row_id):
        reasons = []
        if row_id in price_outliers:
            reasons.append("price_outlier")
        for issue_type, ids in flagged_data.items():
            if row_id in ids:
                reasons.append(issue_type)
        return ", ".join(reasons)

    if not flagged_records.empty:
        flagged_records['flag_reasons'] = flagged_records['id'].apply(get_flag_reasons)

    # Export flagged records
    if not flagged_records.empty:
        flagged_records.to_csv('flagged_records.csv', index=False)
        logger.info(f"Exported {len(flagged_records)} flagged records to flagged_records.csv")

    # 8. Create validation result
    result = ValidationResult(
        completeness_score=completeness_score,
        total_records=len(df),
        flagged_records=len(flagged_records),
        missing_values=missing_values,
        outliers={'price': price_outliers, **flagged_data},
        quality_issues=quality_issues,
        market_stats=overall_stats
    )

    # 9. Generate HTML report
    logger.info("\n5. Generating validation report...")
    report_gen = ValidationReportGenerator(output_html)
    report_gen.generate_html_report(result, df, zip_stats, monthly_trends, flagged_records)

    logger.info("\n" + "="*80)
    logger.info("VALIDATION COMPLETE")
    logger.info("="*80)
    logger.info(f"Completeness Score: {result.completeness_score:.1f}%")
    logger.info(f"Total Records: {result.total_records:,}")
    logger.info(f"Flagged Records: {result.flagged_records:,}")
    logger.info(f"Report: {output_html}")
    logger.info("="*80)

    return result


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "loudoun_sales.db"

    result = validate_database(db_path)

    print(f"\n✓ Validation complete!")
    print(f"  Completeness: {result.completeness_score:.1f}%")
    print(f"  Quality Issues: {len(result.quality_issues)}")
    print(f"  Report: validation_report.html")
