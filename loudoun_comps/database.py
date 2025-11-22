#!/usr/bin/env python3
"""
Database schema and setup for Loudoun County property sales analyzer.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SalesDatabase:
    """SQLite database for property sales data."""

    def __init__(self, db_path="loudoun_sales.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_schema(self):
        """Create database tables."""
        logger.info("Creating database schema...")

        # Main sales table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                sale_date DATE NOT NULL,
                sale_price INTEGER NOT NULL,
                sqft INTEGER,
                lot_size_acres REAL,
                bedrooms INTEGER,
                bathrooms REAL,
                year_built INTEGER,
                has_pool BOOLEAN DEFAULT 0,
                has_garage BOOLEAN DEFAULT 0,
                property_type TEXT,
                zip_code TEXT,
                latitude REAL,
                longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT valid_price CHECK (sale_price > 0),
                CONSTRAINT valid_sqft CHECK (sqft IS NULL OR sqft > 0),
                CONSTRAINT valid_lot CHECK (lot_size_acres IS NULL OR lot_size_acres > 0)
            )
        """)

        # Index for faster queries
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sale_date ON sales(sale_date)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_zip_code ON sales(zip_code)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_type ON sales(property_type)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_location ON sales(latitude, longitude)
        """)

        # Market factors cache table (for storing calculated adjustment factors)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_factors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zip_code TEXT NOT NULL,
                calculation_date DATE NOT NULL,
                price_per_sqft REAL,
                bedroom_value REAL,
                bathroom_value REAL,
                lot_value_per_acre REAL,
                age_depreciation_rate REAL,
                pool_premium REAL,
                garage_premium REAL,
                monthly_appreciation REAL,
                sample_size INTEGER,
                UNIQUE(zip_code, calculation_date)
            )
        """)

        self.conn.commit()
        logger.info("✓ Database schema created successfully")

    def insert_sale(self, **kwargs):
        """Insert a single sale record."""
        fields = ['address', 'sale_date', 'sale_price', 'sqft', 'lot_size_acres',
                  'bedrooms', 'bathrooms', 'year_built', 'has_pool', 'has_garage',
                  'property_type', 'zip_code', 'latitude', 'longitude']

        placeholders = ', '.join(['?' for _ in fields])
        field_names = ', '.join(fields)
        values = [kwargs.get(field) for field in fields]

        self.cursor.execute(f"""
            INSERT INTO sales ({field_names})
            VALUES ({placeholders})
        """, values)

        self.conn.commit()
        return self.cursor.lastrowid

    def insert_sales_batch(self, sales_list):
        """Insert multiple sales records efficiently."""
        logger.info(f"Inserting {len(sales_list)} sales records...")

        fields = ['address', 'sale_date', 'sale_price', 'sqft', 'lot_size_acres',
                  'bedrooms', 'bathrooms', 'year_built', 'has_pool', 'has_garage',
                  'property_type', 'zip_code', 'latitude', 'longitude']

        placeholders = ', '.join(['?' for _ in fields])
        field_names = ', '.join(fields)

        values_list = [[sale.get(field) for field in fields] for sale in sales_list]

        self.cursor.executemany(f"""
            INSERT INTO sales ({field_names})
            VALUES ({placeholders})
        """, values_list)

        self.conn.commit()
        logger.info(f"✓ Inserted {len(sales_list)} records")

    def get_sales_count(self):
        """Get total number of sales in database."""
        self.cursor.execute("SELECT COUNT(*) as count FROM sales")
        return self.cursor.fetchone()['count']

    def get_recent_sales(self, days=365):
        """Get sales from the last N days."""
        self.cursor.execute("""
            SELECT * FROM sales
            WHERE sale_date >= date('now', '-' || ? || ' days')
            ORDER BY sale_date DESC
        """, (days,))
        return self.cursor.fetchall()

    def get_sales_by_zip(self, zip_code, days=365):
        """Get recent sales in a specific ZIP code."""
        self.cursor.execute("""
            SELECT * FROM sales
            WHERE zip_code = ?
            AND sale_date >= date('now', '-' || ? || ' days')
            ORDER BY sale_date DESC
        """, (zip_code, days))
        return self.cursor.fetchall()

    def save_market_factors(self, zip_code, factors, sample_size):
        """Save calculated market factors for a ZIP code."""
        self.cursor.execute("""
            INSERT OR REPLACE INTO market_factors
            (zip_code, calculation_date, price_per_sqft, bedroom_value,
             bathroom_value, lot_value_per_acre, age_depreciation_rate,
             pool_premium, garage_premium, monthly_appreciation, sample_size)
            VALUES (?, date('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            zip_code,
            factors.get('price_per_sqft'),
            factors.get('bedroom_value'),
            factors.get('bathroom_value'),
            factors.get('lot_value_per_acre'),
            factors.get('age_depreciation_rate'),
            factors.get('pool_premium'),
            factors.get('garage_premium'),
            factors.get('monthly_appreciation'),
            sample_size
        ))
        self.conn.commit()

    def get_market_factors(self, zip_code, max_age_days=30):
        """Get cached market factors for a ZIP code if recent enough."""
        self.cursor.execute("""
            SELECT * FROM market_factors
            WHERE zip_code = ?
            AND calculation_date >= date('now', '-' || ? || ' days')
            ORDER BY calculation_date DESC
            LIMIT 1
        """, (zip_code, max_age_days))
        return self.cursor.fetchone()

    def clear_all_data(self):
        """Clear all sales data (for testing)."""
        logger.warning("Clearing all sales data...")
        self.cursor.execute("DELETE FROM sales")
        self.cursor.execute("DELETE FROM market_factors")
        self.conn.commit()
        logger.info("✓ All data cleared")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def initialize_database(db_path="loudoun_sales.db", clear_existing=False):
    """Initialize the database with schema."""
    with SalesDatabase(db_path) as db:
        if clear_existing and db.db_path.exists():
            logger.warning(f"Removing existing database: {db_path}")
            db.db_path.unlink()
            db.connect()  # Reconnect to create new file

        db.create_schema()
        count = db.get_sales_count()
        logger.info(f"Database initialized with {count:,} existing records")

    return db_path


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize database
    db_path = initialize_database(clear_existing=False)
    print(f"\n✓ Database ready: {db_path}")
