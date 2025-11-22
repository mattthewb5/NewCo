#!/usr/bin/env python3
"""
Generate sample property sales data for testing the valuation system.

Creates realistic sales data for Loudoun County, VA with proper geographic distribution.
"""

import random
from datetime import datetime, timedelta
from database import SalesDatabase, initialize_database
import logging

logger = logging.getLogger(__name__)

# Loudoun County ZIP codes with approximate centers
LOUDOUN_ZIPS = {
    '20147': {'name': 'Ashburn', 'lat': 39.0437, 'lon': -77.4875, 'avg_price': 750000},
    '20148': {'name': 'Ashburn (South)', 'lat': 39.0200, 'lon': -77.4800, 'avg_price': 680000},
    '20165': {'name': 'Sterling', 'lat': 39.0065, 'lon': -77.4283, 'avg_price': 550000},
    '20175': {'name': 'Leesburg', 'lat': 39.1157, 'lon': -77.5636, 'avg_price': 600000},
    '20176': {'name': 'Leesburg (South)', 'lat': 39.0800, 'lon': -77.5200, 'avg_price': 720000},
    '20132': {'name': 'Purcellville', 'lat': 39.1368, 'lon': -77.7147, 'avg_price': 580000},
}

# Street names common in Loudoun County
STREET_NAMES = [
    'Riverside Pkwy', 'Davenport Dr', 'Harrison St', 'Cloister Pl', 'Waxpool Rd',
    'Farmwell Rd', 'Ashburn Village Blvd', 'Loudoun County Pkwy', 'Braddock Rd',
    'Sycolin Rd', 'Catoctin Circle', 'Village Market Blvd', 'Pacific Blvd',
    'Truro Parish Dr', 'Belmont Ridge Rd', 'Woodland Pond Rd', 'Summerall Dr',
    'Potomac Station Dr', 'Lockridge Dr', 'Compass Creek Pkwy', 'Demott Dr'
]


def generate_sample_sales(num_sales=200, days_back=365):
    """
    Generate sample property sales data.

    Args:
        num_sales: Number of sales to generate
        days_back: Generate sales over the last N days

    Returns:
        List of sale dictionaries
    """
    logger.info(f"Generating {num_sales} sample sales over last {days_back} days...")

    sales = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    for i in range(num_sales):
        # Random ZIP code
        zip_code = random.choice(list(LOUDOUN_ZIPS.keys()))
        zip_info = LOUDOUN_ZIPS[zip_code]

        # Random location near ZIP center (within ~3 miles)
        lat = zip_info['lat'] + random.uniform(-0.04, 0.04)
        lon = zip_info['lon'] + random.uniform(-0.04, 0.04)

        # Random sale date
        sale_date = start_date + timedelta(
            days=random.randint(0, days_back)
        )

        # Property characteristics
        bedrooms = random.choice([2, 3, 3, 3, 4, 4, 4, 5, 5, 6])
        bathrooms = bedrooms - random.choice([0, 0.5, 1])
        bathrooms = max(1, bathrooms)

        # Square footage (correlated with bedrooms)
        base_sqft = 800 + (bedrooms * 400)
        sqft = int(base_sqft + random.uniform(-200, 400))

        # Year built (Loudoun had boom in 1990s-2010s)
        year_built = random.choice([
            random.randint(1960, 1989),  # 20% older homes
            random.randint(1990, 2005),  # 40% 1990s-2000s
            random.randint(2006, 2020),  # 40% newer homes
        ])

        # Lot size
        lot_size_acres = round(random.uniform(0.15, 1.5), 2)

        # Features
        has_pool = random.random() < 0.15  # 15% have pools
        has_garage = random.random() < 0.80  # 80% have garages

        # Property type
        property_type = random.choice([
            'Single Family', 'Single Family', 'Single Family', 'Single Family',
            'Townhouse', 'Townhouse', 'Condo'
        ])

        # Calculate price (with realistic variance)
        base_price = zip_info['avg_price']

        # Adjust for size
        price_per_sqft = base_price / 2500  # Assume base is 2500 sqft
        price = sqft * price_per_sqft

        # Adjust for bedrooms/bathrooms
        price += (bedrooms - 3) * 25000
        price += (bathrooms - 2.5) * 15000

        # Adjust for age
        age = datetime.now().year - year_built
        price -= age * (price * 0.005)  # 0.5% depreciation per year

        # Adjust for features
        if has_pool:
            price += 20000
        if has_garage:
            price += 15000

        # Adjust for lot size
        price += (lot_size_acres - 0.5) * 40000

        # Market appreciation (1% per month in 2024)
        months_ago = (end_date - sale_date).days / 30.44
        appreciation = price * 0.01 * months_ago
        price -= appreciation  # Sale was in the past, so it was cheaper

        # Add random variance (+/- 10%)
        price *= random.uniform(0.90, 1.10)

        # Round to nearest $5000
        price = int(round(price / 5000) * 5000)

        # Generate address
        street_num = random.randint(100, 99999)
        street_name = random.choice(STREET_NAMES)
        address = f"{street_num} {street_name}, {zip_info['name']}, VA {zip_code}"

        sale = {
            'address': address,
            'sale_date': sale_date.strftime('%Y-%m-%d'),
            'sale_price': price,
            'sqft': sqft,
            'lot_size_acres': lot_size_acres,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'year_built': year_built,
            'has_pool': 1 if has_pool else 0,
            'has_garage': 1 if has_garage else 0,
            'property_type': property_type,
            'zip_code': zip_code,
            'latitude': round(lat, 6),
            'longitude': round(lon, 6)
        }

        sales.append(sale)

    logger.info(f"✓ Generated {len(sales)} sales")
    return sales


def populate_database(db_path="loudoun_sales.db", num_sales=200, clear_existing=False):
    """
    Populate database with sample data.

    Args:
        db_path: Path to database
        num_sales: Number of sales to generate
        clear_existing: Whether to clear existing data first
    """
    logger.info(f"Populating database: {db_path}")

    # Initialize database
    initialize_database(db_path, clear_existing=clear_existing)

    # Generate sample data
    sales = generate_sample_sales(num_sales=num_sales)

    # Insert into database
    with SalesDatabase(db_path) as db:
        if clear_existing:
            db.clear_all_data()

        db.insert_sales_batch(sales)

        # Show statistics
        total = db.get_sales_count()
        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Total sales: {total:,}")

        for zip_code in LOUDOUN_ZIPS.keys():
            zip_sales = db.get_sales_by_zip(zip_code, days=365)
            logger.info(f"  ZIP {zip_code}: {len(zip_sales)} sales")

    logger.info(f"\n✓ Database ready: {db_path}")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Generate sample data
    populate_database(
        db_path="loudoun_sales.db",
        num_sales=200,
        clear_existing=True
    )

    print("\n" + "="*60)
    print("Sample data generation complete!")
    print("="*60)
    print("\nYou can now test the valuation system with this data.")
    print("Run: python3 test_valuation.py")
