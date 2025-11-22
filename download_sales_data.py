#!/usr/bin/env python3
"""
Download and analyze Loudoun County Real Property Sales Report
"""

import requests
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Loudoun County Real Property Sales Report URL
SALES_REPORT_URL = "https://www.loudoun.gov/DocumentCenter/View/212992/Real-Property-Sales-Cumulative-Report-as-of-November-3-2025-XLSX?bidId="
OUTPUT_DIR = Path(__file__).parent / "data"
EXCEL_FILE = OUTPUT_DIR / "loudoun_sales_raw.xlsx"

def download_sales_report():
    """Download the latest Loudoun County sales report."""
    logger.info("Downloading Loudoun County Real Property Sales Report...")

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    try:
        # Download with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(SALES_REPORT_URL, headers=headers, timeout=30)
        response.raise_for_status()

        # Save to file
        with open(EXCEL_FILE, 'wb') as f:
            f.write(response.content)

        logger.info(f"✓ Downloaded {len(response.content):,} bytes to {EXCEL_FILE}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to download: {e}")
        return False

def analyze_excel_structure():
    """Analyze the structure of the downloaded Excel file."""
    logger.info("\nAnalyzing Excel file structure...")

    if not EXCEL_FILE.exists():
        logger.error(f"File not found: {EXCEL_FILE}")
        return

    try:
        # Read Excel file (try first sheet)
        xl = pd.ExcelFile(EXCEL_FILE)

        logger.info(f"\n{'='*60}")
        logger.info(f"Sheet names: {xl.sheet_names}")
        logger.info(f"{'='*60}")

        for sheet_name in xl.sheet_names:
            logger.info(f"\n--- Sheet: {sheet_name} ---")
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, nrows=5)

            logger.info(f"Rows (sample): {len(df)}")
            logger.info(f"Columns: {len(df.columns)}")
            logger.info(f"\nColumn names:")
            for i, col in enumerate(df.columns, 1):
                logger.info(f"  {i:2d}. {col}")

            logger.info(f"\nFirst few rows:")
            logger.info(df.head())
            logger.info(f"\nData types:")
            logger.info(df.dtypes)

        # Get full count
        df_full = pd.read_excel(EXCEL_FILE, sheet_name=xl.sheet_names[0])
        logger.info(f"\n{'='*60}")
        logger.info(f"Total records in dataset: {len(df_full):,}")
        logger.info(f"{'='*60}")

        # Check for recent sales (last 12 months)
        if 'Sale Date' in df_full.columns or 'SALE DATE' in df_full.columns:
            sale_date_col = 'Sale Date' if 'Sale Date' in df_full.columns else 'SALE DATE'
            df_full[sale_date_col] = pd.to_datetime(df_full[sale_date_col], errors='coerce')
            recent_sales = df_full[df_full[sale_date_col] >= '2024-11-01']
            logger.info(f"Sales since Nov 2024: {len(recent_sales):,}")

    except Exception as e:
        logger.error(f"✗ Failed to analyze: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("Loudoun County Property Sales Data Downloader")
    logger.info("=" * 60)

    if download_sales_report():
        analyze_excel_structure()
    else:
        logger.error("Download failed. Please check the URL and try again.")
