#!/usr/bin/env python3
"""
Loudoun County Building Permit Importer

Imports building permit data from Loudoun County Excel reports into SQLite database.
Supports geocoding, categorization, and major commercial project identification.

Author: NewCo Real Estate Intelligence
Date: November 2024

Usage:
    # Import Excel file (clear existing data)
    python3 import_loudoun_permits.py --file permits.xlsx --clear

    # Show database statistics
    python3 import_loudoun_permits.py --stats

    # Import without clearing (append)
    python3 import_loudoun_permits.py --file permits.xlsx
"""

import pandas as pd
import sqlite3
import time
import logging
import argparse
from datetime import datetime
from typing import Tuple, Optional

# Optional geocoding (install with: pip install geopy)
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOCODING_AVAILABLE = True
except ImportError:
    GEOCODING_AVAILABLE = False
    print("⚠️  Warning: geopy not installed. Install with: pip install geopy")
    print("⚠️  Geocoding will be skipped. Permits will be imported without coordinates.")


class LoudounPermitImporter:
    """Import building permits from Loudoun County Excel reports"""

    def __init__(self, db_path: str = "loudoun_development.db"):
        """
        Initialize importer

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.geocoding_cache = {}

        if GEOCODING_AVAILABLE:
            self.geolocator = Nominatim(user_agent="loudoun_permit_importer_newco")
        else:
            self.geolocator = None

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('permit_import.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_database_schema(self):
        """Create database tables and indexes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create building_permits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS building_permits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permit_number TEXT UNIQUE,
                issue_date DATE,
                address TEXT,
                parcel_number TEXT,
                subdivision TEXT,
                permit_type TEXT,
                work_class TEXT,
                description TEXT,
                status TEXT,
                sqft REAL,
                structure_type TEXT,
                estimated_cost REAL,
                contact_company TEXT,
                contact_first_name TEXT,
                contact_last_name TEXT,
                latitude REAL,
                longitude REAL,
                category TEXT,
                is_major_commercial BOOLEAN DEFAULT 0,
                import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue_date ON building_permits(issue_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_location ON building_permits(latitude, longitude)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON building_permits(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_permit_type ON building_permits(permit_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_major_commercial ON building_permits(is_major_commercial)")

        conn.commit()
        conn.close()

        self.logger.info("Database schema created successfully")

    def import_excel_file(self, file_path: str, clear_existing: bool = False,
                         skip_geocoding: bool = False) -> int:
        """
        Import Excel file into database

        Args:
            file_path: Path to Excel file
            clear_existing: If True, clear existing data first
            skip_geocoding: If True, skip geocoding step (faster)

        Returns:
            Number of permits imported
        """
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"LOUDOUN COUNTY BUILDING PERMIT IMPORT")
        self.logger.info(f"{'='*70}\n")
        self.logger.info(f"File: {file_path}")
        self.logger.info(f"Database: {self.db_path}")
        self.logger.info(f"Clear existing: {clear_existing}")
        self.logger.info(f"Geocoding: {'Disabled' if skip_geocoding else 'Enabled'}")

        # Read Excel file
        try:
            self.logger.info("\nReading Excel file...")
            df = pd.read_excel(file_path)
            self.logger.info(f"✓ Loaded {len(df)} permits from Excel")
            self.logger.info(f"  Columns: {', '.join(df.columns.tolist()[:5])}...")
        except Exception as e:
            self.logger.error(f"Failed to read Excel file: {e}")
            return 0

        # Clean addresses
        if 'Address' in df.columns:
            df['Address'] = df['Address'].astype(str)
            df['Address'] = df['Address'].str.replace('_x000D_\\n', ' ', regex=False)
            df['Address'] = df['Address'].str.replace('\n', ' ', regex=False)
            df['Address'] = df['Address'].str.replace('\r', ' ', regex=False)
            df['Address'] = df['Address'].str.strip()

        # Parse dates
        if 'Permit Issue Date' in df.columns:
            df['Permit Issue Date'] = pd.to_datetime(df['Permit Issue Date'], errors='coerce')

        # Initialize database
        self.create_database_schema()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Clear existing data if requested
        if clear_existing:
            cursor.execute("DELETE FROM building_permits")
            self.logger.info("✓ Cleared existing permit data")
            conn.commit()

        # Import permits
        imported = 0
        failed_geocode = 0
        skipped = 0

        self.logger.info(f"\nImporting {len(df)} permits...")
        start_time = time.time()

        for idx, row in df.iterrows():
            # Geocode address (if not skipped)
            lat, lon = None, None
            if not skip_geocoding and GEOCODING_AVAILABLE and 'Address' in row:
                lat, lon = self.geocode_address(row['Address'])
                if lat is None:
                    failed_geocode += 1

            # Categorize permit
            category = self.categorize_permit(row)
            is_major = self.is_major_commercial(row)

            # Insert into database
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO building_permits (
                        permit_number, issue_date, address, parcel_number, subdivision,
                        permit_type, work_class, description, status, sqft,
                        structure_type, estimated_cost, contact_company,
                        contact_first_name, contact_last_name,
                        latitude, longitude, category, is_major_commercial
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('Permit Number'),
                    row.get('Permit Issue Date'),
                    row.get('Address'),
                    str(row.get('Parcel Number', '')),
                    row.get('Subdivision'),
                    row.get('Permit Type'),
                    row.get('Permit Work Class'),
                    row.get('Permit Description'),
                    row.get('Permit Status'),
                    row.get('Permit Square Feet'),
                    row.get('Structure Type'),
                    row.get('Estimated Construction Cost'),
                    row.get('Contact Company Name'),
                    row.get('Contact First Name'),
                    row.get('Contact Last Name'),
                    lat, lon, category, 1 if is_major else 0
                ))
                imported += 1

                if imported % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = imported / elapsed
                    remaining = (len(df) - imported) / rate if rate > 0 else 0
                    self.logger.info(f"  Progress: {imported}/{len(df)} ({imported/len(df)*100:.1f}%) - "
                                   f"{rate:.1f} permits/sec - ETA: {remaining/60:.1f} min")

            except Exception as e:
                self.logger.error(f"Failed to insert permit {row.get('Permit Number', 'unknown')}: {e}")
                skipped += 1

        conn.commit()
        conn.close()

        elapsed_time = time.time() - start_time

        # Summary
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"IMPORT COMPLETE")
        self.logger.info(f"{'='*70}")
        self.logger.info(f"Total permits imported: {imported}")
        self.logger.info(f"Skipped (errors): {skipped}")
        if not skip_geocoding and GEOCODING_AVAILABLE:
            geocoded_success = imported - failed_geocode
            self.logger.info(f"Geocoded successfully: {geocoded_success} ({geocoded_success/imported*100:.1f}%)")
            self.logger.info(f"Failed geocoding: {failed_geocode} ({failed_geocode/imported*100:.1f}%)")
        self.logger.info(f"Import time: {elapsed_time/60:.1f} minutes")
        self.logger.info(f"{'='*70}\n")

        return imported

    def geocode_address(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode address with caching and rate limiting

        Args:
            address: Street address

        Returns:
            Tuple of (latitude, longitude) or (None, None) if failed
        """
        if not self.geolocator:
            return None, None

        # Check cache
        if address in self.geocoding_cache:
            return self.geocoding_cache[address]

        # Skip invalid addresses
        if not address or address == 'nan' or address == 'None':
            return None, None

        # Geocode
        try:
            full_address = f"{address}, Loudoun County, VA"
            location = self.geolocator.geocode(full_address, timeout=10)

            if location:
                lat, lon = location.latitude, location.longitude
                self.geocoding_cache[address] = (lat, lon)

                # Rate limit (Nominatim requires 1 request per second)
                time.sleep(1.1)

                return lat, lon
            else:
                # Try without county
                location = self.geolocator.geocode(f"{address}, Virginia", timeout=10)
                if location:
                    lat, lon = location.latitude, location.longitude
                    self.geocoding_cache[address] = (lat, lon)
                    time.sleep(1.1)
                    return lat, lon

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.warning(f"Geocoding timeout/error for {address}: {e}")
        except Exception as e:
            self.logger.warning(f"Geocoding error for {address}: {e}")

        self.geocoding_cache[address] = (None, None)
        return None, None

    def categorize_permit(self, row: pd.Series) -> str:
        """
        Categorize permit type

        Args:
            row: DataFrame row with permit data

        Returns:
            Category string
        """
        permit_type = str(row.get('Permit Type', ''))
        work_class = str(row.get('Permit Work Class', ''))
        structure_type = str(row.get('Structure Type', ''))
        sqft = row.get('Permit Square Feet', 0) or 0

        # Data centers (special category)
        if 'Data Center' in structure_type:
            return 'Major Commercial - Data Center'

        # Large commercial
        if 'Commercial' in permit_type and sqft > 25000:
            return 'Major Commercial'

        # New construction
        if 'New Construction' in work_class or 'New' in work_class:
            if 'Residential' in permit_type:
                return 'Residential - New Construction'
            else:
                return 'Commercial - New Construction'

        # Renovations/additions
        if 'Residential' in permit_type:
            return 'Residential - Renovation'
        elif 'Commercial' in permit_type:
            return 'Commercial - Renovation'

        return 'Other'

    def is_major_commercial(self, row: pd.Series) -> bool:
        """
        Check if permit is major commercial (for 3x weighting in scoring)

        Args:
            row: DataFrame row with permit data

        Returns:
            True if major commercial
        """
        category = self.categorize_permit(row)
        sqft = row.get('Permit Square Feet', 0) or 0
        cost = row.get('Estimated Construction Cost', 0) or 0

        # Data centers are always major
        if 'Data Center' in category:
            return True

        # Large square footage
        if sqft > 50000:
            return True

        # High construction cost
        if cost > 5000000:  # $5M+
            return True

        return False

    def show_stats(self):
        """Show database statistics"""
        conn = sqlite3.connect(self.db_path)

        print(f"\n{'='*70}")
        print("LOUDOUN COUNTY BUILDING PERMITS - DATABASE STATISTICS")
        print(f"{'='*70}\n")

        try:
            # Total count
            total = pd.read_sql("SELECT COUNT(*) as count FROM building_permits", conn).iloc[0]['count']
            print(f"Total Permits: {total:,}")

            if total == 0:
                print("\n⚠️  No permits in database. Import data first.")
                conn.close()
                return

            # By permit type
            by_type = pd.read_sql("""
                SELECT permit_type, COUNT(*) as count
                FROM building_permits
                WHERE permit_type IS NOT NULL
                GROUP BY permit_type
                ORDER BY count DESC
            """, conn)
            print(f"\nBy Permit Type:")
            for _, row in by_type.iterrows():
                print(f"  • {row['permit_type']}: {row['count']:,}")

            # By category
            by_category = pd.read_sql("""
                SELECT category, COUNT(*) as count
                FROM building_permits
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """, conn)
            print(f"\nBy Category:")
            for _, row in by_category.iterrows():
                print(f"  • {row['category']}: {row['count']:,}")

            # Major commercial count
            major = pd.read_sql("""
                SELECT COUNT(*) as count
                FROM building_permits
                WHERE is_major_commercial = 1
            """, conn).iloc[0]['count']
            print(f"\nMajor Commercial Projects: {major:,} ({major/total*100:.1f}%)")

            # Date range
            dates = pd.read_sql("""
                SELECT MIN(issue_date) as min_date, MAX(issue_date) as max_date
                FROM building_permits
                WHERE issue_date IS NOT NULL
            """, conn)
            if not dates.empty:
                print(f"\nDate Range: {dates.iloc[0]['min_date']} to {dates.iloc[0]['max_date']}")

            # Total value
            total_value = pd.read_sql("""
                SELECT SUM(estimated_cost) as total
                FROM building_permits
                WHERE estimated_cost IS NOT NULL
            """, conn).iloc[0]['total']
            if total_value:
                print(f"\nTotal Construction Value: ${total_value:,.0f} ({total_value/1e6:.1f}M)")

            # Geocoding success
            geocoded = pd.read_sql("""
                SELECT COUNT(*) as count
                FROM building_permits
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """, conn).iloc[0]['count']
            print(f"\nGeocoded Successfully: {geocoded:,}/{total:,} ({geocoded/total*100:.1f}%)")

            # Top subdivisions
            top_subdivisions = pd.read_sql("""
                SELECT subdivision, COUNT(*) as count
                FROM building_permits
                WHERE subdivision IS NOT NULL AND subdivision != ''
                GROUP BY subdivision
                ORDER BY count DESC
                LIMIT 5
            """, conn)
            if not top_subdivisions.empty:
                print(f"\nTop 5 Subdivisions:")
                for _, row in top_subdivisions.iterrows():
                    print(f"  • {row['subdivision']}: {row['count']:,} permits")

        except Exception as e:
            print(f"\n❌ Error reading statistics: {e}")

        conn.close()
        print(f"\n{'='*70}\n")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Import Loudoun County Building Permits from Excel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import Excel file (replace existing data)
  python3 import_loudoun_permits.py --file permits.xlsx --clear

  # Import without clearing (append)
  python3 import_loudoun_permits.py --file permits.xlsx

  # Skip geocoding (faster import)
  python3 import_loudoun_permits.py --file permits.xlsx --skip-geocoding

  # Show database statistics
  python3 import_loudoun_permits.py --stats
        """
    )

    parser.add_argument('--file', help='Path to Excel file to import')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before import')
    parser.add_argument('--skip-geocoding', action='store_true', help='Skip geocoding (faster import)')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--db', default='loudoun_development.db', help='Database path (default: loudoun_development.db)')

    args = parser.parse_args()

    importer = LoudounPermitImporter(db_path=args.db)

    if args.stats:
        importer.show_stats()
    elif args.file:
        imported = importer.import_excel_file(
            args.file,
            clear_existing=args.clear,
            skip_geocoding=args.skip_geocoding
        )
        if imported > 0:
            print("\n" + "="*70)
            print("Showing updated database statistics:")
            print("="*70)
            importer.show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
