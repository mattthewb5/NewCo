#!/usr/bin/env python3
"""
Zoning and Development Database Schema

Creates SQLite database for tracking development activity, permits, rezonings,
and land applications in Loudoun County.

Author: Property Valuation System
Version: 1.0.0
Date: November 2025
"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DevelopmentDatabase:
    """SQLite database for development activity tracking."""

    def __init__(self, db_path: str = "loudoun_development.db"):
        """Initialize database."""
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_schema(self):
        """Create all database tables."""
        logger.info("Creating database schema...")

        # Table 1: Building Permits
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS building_permits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permit_number TEXT UNIQUE,
                issue_date DATE NOT NULL,
                address TEXT NOT NULL,
                project_type TEXT,  -- Residential/Commercial/Mixed-Use
                sqft INTEGER,
                valuation INTEGER,
                status TEXT,  -- Approved/Under Construction/Completed
                latitude REAL,
                longitude REAL,
                scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT valid_sqft CHECK (sqft IS NULL OR sqft > 0),
                CONSTRAINT valid_valuation CHECK (valuation IS NULL OR valuation > 0)
            )
        """)

        # Table 2: Land Applications
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS land_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_number TEXT UNIQUE,
                app_date DATE NOT NULL,
                address TEXT NOT NULL,
                app_type TEXT,  -- Rezoning/Site Plan/Variance/Special Exception
                current_zoning TEXT,
                proposed_zoning TEXT,
                status TEXT,  -- Pending/Approved/Denied
                acreage REAL,
                latitude REAL,
                longitude REAL,
                scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT valid_acreage CHECK (acreage IS NULL OR acreage > 0)
            )
        """)

        # Table 3: Rezoning Decisions
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS rezonings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_date DATE NOT NULL,
                address TEXT NOT NULL,
                previous_zoning TEXT,
                new_zoning TEXT,
                vote_result TEXT,  -- Approved/Denied
                summary TEXT,
                latitude REAL,
                longitude REAL,
                scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 4: Large Parcel Sales
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS large_parcel_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date DATE NOT NULL,
                address TEXT NOT NULL,
                acreage REAL NOT NULL,
                sale_price INTEGER NOT NULL,
                previous_use TEXT,
                buyer_type TEXT,  -- Developer/Individual/Corporation
                latitude REAL,
                longitude REAL,
                CONSTRAINT valid_acreage_sale CHECK (acreage > 5.0),
                CONSTRAINT valid_price CHECK (sale_price > 0)
            )
        """)

        # Table 5: Property Analysis Cache
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                development_pressure_score REAL,
                location_quality_score REAL,
                market_trajectory TEXT,
                neighborhood_name TEXT,
                rezoning_count_1mi INTEGER DEFAULT 0,
                rezoning_count_3mi INTEGER DEFAULT 0,
                rezoning_count_5mi INTEGER DEFAULT 0,
                permit_count_1mi INTEGER DEFAULT 0,
                permit_count_3mi INTEGER DEFAULT 0,
                permit_count_5mi INTEGER DEFAULT 0,
                ml_development_probability REAL,
                ml_value_impact REAL,
                UNIQUE(address, analysis_date)
            )
        """)

        # Create indexes for performance
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_permits_location
            ON building_permits(latitude, longitude)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_permits_date
            ON building_permits(issue_date)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_applications_location
            ON land_applications(latitude, longitude)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rezonings_location
            ON rezonings(latitude, longitude)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sales_location
            ON large_parcel_sales(latitude, longitude)
        """)

        self.conn.commit()
        logger.info("✓ Database schema created successfully")

    def get_stats(self):
        """Get database statistics."""
        stats = {}

        tables = ['building_permits', 'land_applications', 'rezonings',
                  'large_parcel_sales', 'property_analysis']

        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = self.cursor.fetchone()['count']

        return stats

    def clear_all_data(self):
        """Clear all data (for testing)."""
        logger.warning("Clearing all development data...")

        tables = ['building_permits', 'land_applications', 'rezonings',
                  'large_parcel_sales', 'property_analysis']

        for table in tables:
            self.cursor.execute(f"DELETE FROM {table}")

        self.conn.commit()
        logger.info("✓ All data cleared")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def initialize_development_database(
    db_path: str = "loudoun_development.db",
    clear_existing: bool = False
) -> Path:
    """
    Initialize the development database.

    Args:
        db_path: Path to database file
        clear_existing: Whether to clear existing data

    Returns:
        Path to database
    """
    db_path = Path(db_path)

    with DevelopmentDatabase(str(db_path)) as db:
        if clear_existing and db_path.exists():
            logger.warning(f"Clearing existing database: {db_path}")
            db.clear_all_data()

        db.create_schema()

        stats = db.get_stats()
        logger.info("\nDatabase Statistics:")
        for table, count in stats.items():
            logger.info(f"  {table}: {count} records")

    return db_path


if __name__ == "__main__":
    print("Loudoun County Development Database Initializer")
    print("=" * 60)

    db_path = initialize_development_database(clear_existing=False)

    print(f"\n✓ Database ready: {db_path}")
    print("\nTables created:")
    print("  - building_permits")
    print("  - land_applications")
    print("  - rezonings")
    print("  - large_parcel_sales")
    print("  - property_analysis")
