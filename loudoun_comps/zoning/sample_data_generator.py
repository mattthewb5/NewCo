#!/usr/bin/env python3
"""
Sample Data Generator for Zoning Analysis System

Generates realistic sample data for testing the zoning analysis system without
requiring actual web scraping. Creates permits, applications, rezonings, and
large parcel sales around test properties.

Author: Property Valuation System
Version: 1.0.0
Date: November 2025
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from development_database import DevelopmentDatabase, initialize_development_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Loudoun County major locations
LOUDOUN_LOCATIONS = {
    'ashburn': {'lat': 39.0437, 'lon': -77.4875, 'name': 'Ashburn'},
    'sterling': {'lat': 39.0065, 'lon': -77.4283, 'name': 'Sterling'},
    'leesburg': {'lat': 39.1157, 'lon': -77.5636, 'name': 'Leesburg'},
    'dulles': {'lat': 38.9531, 'lon': -77.4565, 'name': 'Dulles'},
}

# Street names
STREET_NAMES = [
    'Riverside Pkwy', 'Ashburn Village Blvd', 'Waxpool Rd', 'Farmwell Rd',
    'Loudoun County Pkwy', 'Sycolin Rd', 'Belmont Ridge Rd', 'Pacific Blvd',
    'Truro Parish Dr', 'Compass Creek Pkwy', 'Lockridge Dr', 'Summerall Dr'
]

# Project types and typical sizes
PROJECT_TYPES = {
    'Residential': {'sqft_range': (2000, 6000), 'valuation_per_sqft': 200},
    'Commercial': {'sqft_range': (5000, 50000), 'valuation_per_sqft': 150},
    'Mixed-Use': {'sqft_range': (10000, 100000), 'valuation_per_sqft': 180}
}

# Zoning codes
ZONING_CODES = ['R-8', 'R-16', 'AR-1', 'AR-2', 'PD-CC', 'PD-OP', 'CLI', 'JLMA']


def generate_location_near(center_lat: float, center_lon: float, max_miles: float = 5.0) -> tuple:
    """
    Generate random location within max_miles of center point.

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        max_miles: Maximum distance in miles

    Returns:
        Tuple of (lat, lon)
    """
    # Rough approximation: 1 degree lat/lon ≈ 69 miles
    miles_per_degree = 69.0
    max_degrees = max_miles / miles_per_degree

    # Random offset
    lat_offset = random.uniform(-max_degrees, max_degrees)
    lon_offset = random.uniform(-max_degrees, max_degrees)

    return (
        center_lat + lat_offset,
        center_lon + lon_offset
    )


def generate_address(lat: float, lon: float, area_name: str) -> str:
    """Generate realistic address."""
    street_num = random.randint(100, 99999)
    street_name = random.choice(STREET_NAMES)
    zip_code = '20147' if 'ashburn' in area_name.lower() else '20165'

    return f"{street_num} {street_name}, {area_name}, VA {zip_code}"


def generate_building_permits(
    center_lat: float,
    center_lon: float,
    area_name: str,
    count: int = 30
) -> List[Dict]:
    """
    Generate sample building permits.

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        area_name: Area name for addresses
        count: Number of permits to generate

    Returns:
        List of permit dictionaries
    """
    permits = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years

    statuses = ['Approved', 'Under Construction', 'Completed']

    for i in range(count):
        # Random date
        issue_date = start_date + timedelta(
            days=random.randint(0, 730)
        )

        # Random project type
        project_type = random.choice(list(PROJECT_TYPES.keys()))
        sqft_range = PROJECT_TYPES[project_type]['sqft_range']
        val_per_sqft = PROJECT_TYPES[project_type]['valuation_per_sqft']

        sqft = random.randint(*sqft_range)
        valuation = int(sqft * val_per_sqft * random.uniform(0.9, 1.1))

        # Location
        lat, lon = generate_location_near(center_lat, center_lon, max_miles=5.0)
        address = generate_address(lat, lon, area_name)

        permit = {
            'permit_number': f"BP-{issue_date.year}-{i:05d}",
            'issue_date': issue_date.strftime('%Y-%m-%d'),
            'address': address,
            'project_type': project_type,
            'sqft': sqft,
            'valuation': valuation,
            'status': random.choice(statuses),
            'latitude': lat,
            'longitude': lon
        }

        permits.append(permit)

    logger.info(f"Generated {len(permits)} building permits")
    return permits


def generate_land_applications(
    center_lat: float,
    center_lon: float,
    area_name: str,
    count: int = 15
) -> List[Dict]:
    """Generate sample land applications."""
    applications = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095)  # 3 years

    app_types = ['Rezoning', 'Site Plan', 'Variance', 'Special Exception']
    statuses = ['Pending', 'Approved', 'Denied']

    for i in range(count):
        app_date = start_date + timedelta(days=random.randint(0, 1095))

        lat, lon = generate_location_near(center_lat, center_lon, max_miles=5.0)
        address = generate_address(lat, lon, area_name)

        current_zoning = random.choice(ZONING_CODES)
        proposed_zoning = random.choice(ZONING_CODES)

        application = {
            'app_number': f"APP-{app_date.year}-{i:04d}",
            'app_date': app_date.strftime('%Y-%m-%d'),
            'address': address,
            'app_type': random.choice(app_types),
            'current_zoning': current_zoning,
            'proposed_zoning': proposed_zoning,
            'status': random.choice(statuses),
            'acreage': round(random.uniform(1.0, 50.0), 2),
            'latitude': lat,
            'longitude': lon
        }

        applications.append(application)

    logger.info(f"Generated {len(applications)} land applications")
    return applications


def generate_rezonings(
    center_lat: float,
    center_lon: float,
    area_name: str,
    count: int = 10
) -> List[Dict]:
    """Generate sample rezoning decisions."""
    rezonings = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095)  # 3 years

    for i in range(count):
        decision_date = start_date + timedelta(days=random.randint(0, 1095))

        lat, lon = generate_location_near(center_lat, center_lon, max_miles=5.0)
        address = generate_address(lat, lon, area_name)

        previous_zoning = random.choice(ZONING_CODES[:4])  # More rural codes
        new_zoning = random.choice(ZONING_CODES[4:])  # More developed codes

        rezoning = {
            'decision_date': decision_date.strftime('%Y-%m-%d'),
            'address': address,
            'previous_zoning': previous_zoning,
            'new_zoning': new_zoning,
            'vote_result': random.choice(['Approved', 'Approved', 'Approved', 'Denied']),  # 75% approval
            'summary': f"Rezoning from {previous_zoning} to {new_zoning}",
            'latitude': lat,
            'longitude': lon
        }

        rezonings.append(rezoning)

    logger.info(f"Generated {len(rezonings)} rezonings")
    return rezonings


def generate_large_parcel_sales(
    center_lat: float,
    center_lon: float,
    area_name: str,
    count: int = 8
) -> List[Dict]:
    """Generate sample large parcel sales."""
    sales = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years

    buyer_types = ['Developer', 'Developer', 'Corporation', 'Individual']
    previous_uses = ['Agricultural', 'Vacant Land', 'Rural Estate']

    for i in range(count):
        sale_date = start_date + timedelta(days=random.randint(0, 730))

        lat, lon = generate_location_near(center_lat, center_lon, max_miles=5.0)
        address = generate_address(lat, lon, area_name)

        acreage = round(random.uniform(5.5, 100.0), 1)
        price_per_acre = random.randint(100000, 500000)
        sale_price = int(acreage * price_per_acre)

        sale = {
            'sale_date': sale_date.strftime('%Y-%m-%d'),
            'address': address,
            'acreage': acreage,
            'sale_price': sale_price,
            'previous_use': random.choice(previous_uses),
            'buyer_type': random.choice(buyer_types),
            'latitude': lat,
            'longitude': lon
        }

        sales.append(sale)

    logger.info(f"Generated {len(sales)} large parcel sales")
    return sales


def populate_sample_data(
    db_path: str = "loudoun_development.db",
    center_lat: float = 39.0437,
    center_lon: float = -77.4875,
    area_name: str = "Ashburn",
    clear_existing: bool = True
):
    """
    Populate database with sample development data.

    Args:
        db_path: Database path
        center_lat: Center latitude for data generation
        center_lon: Center longitude
        area_name: Area name for addresses
        clear_existing: Whether to clear existing data
    """
    logger.info("="*60)
    logger.info("GENERATING SAMPLE DEVELOPMENT DATA")
    logger.info("="*60)

    # Initialize database
    initialize_development_database(db_path, clear_existing=clear_existing)

    # Generate data
    permits = generate_building_permits(center_lat, center_lon, area_name, count=30)
    applications = generate_land_applications(center_lat, center_lon, area_name, count=15)
    rezonings = generate_rezonings(center_lat, center_lon, area_name, count=10)
    sales = generate_large_parcel_sales(center_lat, center_lon, area_name, count=8)

    # Insert into database
    with DevelopmentDatabase(db_path) as db:
        # Insert permits
        for permit in permits:
            db.cursor.execute("""
                INSERT INTO building_permits
                (permit_number, issue_date, address, project_type, sqft, valuation,
                 status, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                permit['permit_number'], permit['issue_date'], permit['address'],
                permit['project_type'], permit['sqft'], permit['valuation'],
                permit['status'], permit['latitude'], permit['longitude']
            ))

        # Insert applications
        for app in applications:
            db.cursor.execute("""
                INSERT INTO land_applications
                (app_number, app_date, address, app_type, current_zoning, proposed_zoning,
                 status, acreage, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app['app_number'], app['app_date'], app['address'], app['app_type'],
                app['current_zoning'], app['proposed_zoning'], app['status'],
                app['acreage'], app['latitude'], app['longitude']
            ))

        # Insert rezonings
        for rezoning in rezonings:
            db.cursor.execute("""
                INSERT INTO rezonings
                (decision_date, address, previous_zoning, new_zoning, vote_result,
                 summary, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rezoning['decision_date'], rezoning['address'], rezoning['previous_zoning'],
                rezoning['new_zoning'], rezoning['vote_result'], rezoning['summary'],
                rezoning['latitude'], rezoning['longitude']
            ))

        # Insert sales
        for sale in sales:
            db.cursor.execute("""
                INSERT INTO large_parcel_sales
                (sale_date, address, acreage, sale_price, previous_use,
                 buyer_type, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sale['sale_date'], sale['address'], sale['acreage'], sale['sale_price'],
                sale['previous_use'], sale['buyer_type'], sale['latitude'], sale['longitude']
            ))

        db.conn.commit()

        # Show stats
        stats = db.get_stats()

        logger.info("\n" + "="*60)
        logger.info("SAMPLE DATA GENERATION COMPLETE")
        logger.info("="*60)
        logger.info("Database Statistics:")
        for table, count in stats.items():
            if count > 0:
                logger.info(f"  {table}: {count} records")
        logger.info("="*60)


if __name__ == "__main__":
    print("\nLoudoun County Development Data Generator")
    print("="*60)

    # Generate sample data for Ashburn area
    populate_sample_data(
        db_path="loudoun_development.db",
        center_lat=39.0437,  # Ashburn
        center_lon=-77.4875,
        area_name="Ashburn",
        clear_existing=True
    )

    print("\n✓ Sample data generated successfully!")
    print("  Database: loudoun_development.db")
    print("  Center: Ashburn, VA (39.0437, -77.4875)")
    print("\nYou can now run the zoning analysis system with this data.")
