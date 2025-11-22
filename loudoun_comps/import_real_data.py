#!/usr/bin/env python3
"""
Import real property sales data from Loudoun County public records.

Downloads the official Real Property Sales Report (Excel) and imports it into the database.
"""

import pandas as pd
import requests
from pathlib import Path
import logging
from tqdm import tqdm
from database import SalesDatabase, initialize_database
import re

logger = logging.getLogger(__name__)

# Loudoun County Real Property Sales Report URL
SALES_REPORT_URL = "https://www.loudoun.gov/DocumentCenter/View/212992/Real-Property-Sales-Cumulative-Report-as-of-November-3-2025-XLSX?bidId="
DATA_DIR = Path(__file__).parent / "data"
EXCEL_FILE = DATA_DIR / "loudoun_sales_raw.xlsx"


def download_sales_report(force=False):
    """
    Download the latest Loudoun County sales report.

    Args:
        force: Force re-download even if file exists

    Returns:
        Path to downloaded file or None if failed
    """
    if EXCEL_FILE.exists() and not force:
        logger.info(f"Using existing file: {EXCEL_FILE}")
        return EXCEL_FILE

    logger.info("Downloading Loudoun County Real Property Sales Report...")
    DATA_DIR.mkdir(exist_ok=True)

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(SALES_REPORT_URL, headers=headers, timeout=60, stream=True)
        response.raise_for_status()

        # Download with progress bar
        total_size = int(response.headers.get('content-length', 0))
        with open(EXCEL_FILE, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading') as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))

        logger.info(f"✓ Downloaded to {EXCEL_FILE}")
        return EXCEL_FILE

    except Exception as e:
        logger.error(f"✗ Download failed: {e}")
        return None


def parse_excel_to_sales(excel_path):
    """
    Parse the Excel file and convert to standardized sales records.

    Args:
        excel_path: Path to Excel file

    Returns:
        List of sale dictionaries

    Note: This function will need to be adapted based on the actual Excel structure.
    """
    logger.info(f"Parsing Excel file: {excel_path}")

    try:
        # Read Excel file
        df = pd.read_excel(excel_path, sheet_name=0)

        logger.info(f"Loaded {len(df):,} rows from Excel")
        logger.info(f"Columns: {list(df.columns)}")

        # Clean and standardize data
        sales = []

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing rows"):
            try:
                sale = parse_row_to_sale(row)
                if sale:
                    sales.append(sale)
            except Exception as e:
                logger.warning(f"Error parsing row {idx}: {e}")
                continue

        logger.info(f"✓ Successfully parsed {len(sales):,} sales records")
        return sales

    except Exception as e:
        logger.error(f"✗ Failed to parse Excel: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_row_to_sale(row):
    """
    Parse a single Excel row to a sale dictionary.

    This function needs to be customized based on the actual column names
    in the Loudoun County Excel file.

    Expected columns (names may vary):
    - Address / Property Address
    - Sale Date / Date of Sale
    - Sale Price / Sales Price
    - Square Feet / Living Area / GLA
    - Bedrooms / # Beds
    - Bathrooms / # Baths
    - Year Built / YearBuilt
    - Lot Size / Acreage
    - ZIP Code / Zip
    - etc.
    """
    # Column mapping - UPDATE THESE based on actual Excel columns
    COLUMN_MAP = {
        'address': ['Address', 'Property Address', 'ADDR', 'PROPERTY_ADDRESS'],
        'sale_date': ['Sale Date', 'Date of Sale', 'SALE_DATE', 'DATE'],
        'sale_price': ['Sale Price', 'Sales Price', 'SALE_PRICE', 'PRICE'],
        'sqft': ['Square Feet', 'Living Area', 'GLA', 'SQFT', 'LIVING_AREA'],
        'bedrooms': ['Bedrooms', '# Beds', 'BEDROOMS', 'BEDS'],
        'bathrooms': ['Bathrooms', '# Baths', 'BATHROOMS', 'BATHS'],
        'year_built': ['Year Built', 'YearBuilt', 'YEAR_BUILT', 'YR_BUILT'],
        'lot_size': ['Lot Size', 'Acreage', 'LOT_SIZE', 'ACRES'],
        'zip_code': ['ZIP', 'Zip Code', 'ZIP_CODE', 'ZIPCODE'],
        'property_type': ['Property Type', 'Type', 'PROP_TYPE', 'CLASS'],
    }

    def get_value(row, field_aliases):
        """Get value from row using possible column names."""
        for alias in field_aliases:
            if alias in row.index and pd.notna(row[alias]):
                return row[alias]
        return None

    # Extract values
    address = get_value(row, COLUMN_MAP['address'])
    sale_date = get_value(row, COLUMN_MAP['sale_date'])
    sale_price = get_value(row, COLUMN_MAP['sale_price'])

    # Required fields
    if not address or not sale_date or not sale_price:
        return None

    # Clean and convert
    try:
        sale_price = float(str(sale_price).replace('$', '').replace(',', ''))
        if sale_price <= 0:
            return None
    except:
        return None

    # Parse date
    if isinstance(sale_date, str):
        sale_date = pd.to_datetime(sale_date).strftime('%Y-%m-%d')
    else:
        sale_date = pd.to_datetime(sale_date).strftime('%Y-%m-%d')

    # Extract ZIP code from address if not in separate column
    zip_code = get_value(row, COLUMN_MAP['zip_code'])
    if not zip_code and address:
        zip_match = re.search(r'\b(\d{5})\b', str(address))
        if zip_match:
            zip_code = zip_match.group(1)

    # Other fields (optional)
    sqft = get_value(row, COLUMN_MAP['sqft'])
    if sqft:
        try:
            sqft = int(float(str(sqft).replace(',', '')))
        except:
            sqft = None

    bedrooms = get_value(row, COLUMN_MAP['bedrooms'])
    if bedrooms:
        try:
            bedrooms = int(float(bedrooms))
        except:
            bedrooms = None

    bathrooms = get_value(row, COLUMN_MAP['bathrooms'])
    if bathrooms:
        try:
            bathrooms = float(bathrooms)
        except:
            bathrooms = None

    year_built = get_value(row, COLUMN_MAP['year_built'])
    if year_built:
        try:
            year_built = int(float(year_built))
        except:
            year_built = None

    lot_size = get_value(row, COLUMN_MAP['lot_size'])
    if lot_size:
        try:
            lot_size_acres = float(str(lot_size).replace(',', ''))
        except:
            lot_size_acres = None
    else:
        lot_size_acres = None

    property_type = get_value(row, COLUMN_MAP['property_type'])
    if not property_type:
        property_type = 'Single Family'  # Default

    sale = {
        'address': str(address),
        'sale_date': sale_date,
        'sale_price': int(sale_price),
        'sqft': sqft,
        'lot_size_acres': lot_size_acres,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'year_built': year_built,
        'has_pool': 0,  # Not typically in public records
        'has_garage': 0,  # Not typically in public records
        'property_type': property_type,
        'zip_code': zip_code,
        'latitude': None,  # Would need geocoding
        'longitude': None  # Would need geocoding
    }

    return sale


def import_sales_data(db_path="loudoun_sales.db", force_download=False, clear_existing=False):
    """
    Download and import Loudoun County sales data.

    Args:
        db_path: Path to database
        force_download: Force re-download of Excel file
        clear_existing: Clear existing data before import
    """
    logger.info("Starting Loudoun County data import...")

    # Initialize database
    initialize_database(db_path, clear_existing=clear_existing)

    # Download data
    excel_path = download_sales_report(force=force_download)
    if not excel_path:
        logger.error("Could not download data - aborting import")
        return False

    # Parse Excel
    sales = parse_excel_to_sales(excel_path)
    if not sales:
        logger.error("No sales data parsed - aborting import")
        return False

    # Filter for residential and last 12 months
    from datetime import datetime, timedelta
    cutoff_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    recent_sales = [s for s in sales if s['sale_date'] >= cutoff_date]

    logger.info(f"Filtered to {len(recent_sales):,} sales from last 12 months")

    # Import to database
    with SalesDatabase(db_path) as db:
        if clear_existing:
            db.clear_all_data()

        db.insert_sales_batch(recent_sales)

        # Show statistics
        total = db.get_sales_count()
        logger.info(f"\n✓ Import complete: {total:,} total sales in database")

    return True


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("="*80)
    print("Loudoun County Real Property Sales Data Importer")
    print("="*80)

    success = import_sales_data(
        db_path="loudoun_sales.db",
        force_download=False,
        clear_existing=False
    )

    if success:
        print("\n✓ Import successful!")
        print("\nYou can now run valuations using:")
        print("  python3 test_valuation.py")
    else:
        print("\n✗ Import failed - see errors above")
        print("\nTrying sample data instead...")
        print("  python3 generate_sample_data.py")
