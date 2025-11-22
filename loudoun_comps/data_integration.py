#!/usr/bin/env python3
"""
Data Integration Layer for Loudoun County Property Sales System

Provides data enrichment, geocoding, distance calculations, and export capabilities.
Integrates with OpenStreetMap Nominatim API for geocoding (free, no API key needed).

Author: Property Valuation System
Version: 1.0.0
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import json
import time
import re

# Geospatial
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Robust SQLite database connector with query builder."""

    def __init__(self, db_path: str):
        """Initialize connector with database path."""
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to database with error handling."""
        try:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database not found: {self.db_path}")

            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

            logger.info(f"Connected to database: {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def execute_query(self, query: str, params: tuple = None) -> List[sqlite3.Row]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            return self.cursor.fetchall()

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Execute an UPDATE/INSERT/DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of rows affected
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            self.conn.commit()
            return self.cursor.rowcount

        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            self.conn.rollback()
            raise

    def query_builder(
        self,
        table: str,
        columns: List[str] = None,
        where: Dict = None,
        order_by: str = None,
        limit: int = None
    ) -> List[sqlite3.Row]:
        """
        Flexible query builder for common queries.

        Args:
            table: Table name
            columns: List of columns to select (None = all)
            where: Dictionary of WHERE conditions
            order_by: ORDER BY clause
            limit: LIMIT clause

        Returns:
            List of result rows
        """
        # Build SELECT clause
        cols = ', '.join(columns) if columns else '*'
        query = f"SELECT {cols} FROM {table}"

        # Build WHERE clause
        params = []
        if where:
            conditions = []
            for key, value in where.items():
                if value is None:
                    conditions.append(f"{key} IS NULL")
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        # Add ORDER BY
        if order_by:
            query += f" ORDER BY {order_by}"

        # Add LIMIT
        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, tuple(params) if params else None)

    def get_sales_by_filters(
        self,
        zip_code: str = None,
        property_type: str = None,
        date_from: str = None,
        date_to: str = None,
        min_price: int = None,
        max_price: int = None
    ) -> pd.DataFrame:
        """
        Get sales data with flexible filtering.

        Args:
            zip_code: Filter by ZIP code
            property_type: Filter by property type
            date_from: Filter by sale date (from)
            date_to: Filter by sale date (to)
            min_price: Minimum sale price
            max_price: Maximum sale price

        Returns:
            DataFrame of filtered sales
        """
        query = "SELECT * FROM sales WHERE 1=1"
        params = []

        if zip_code:
            query += " AND zip_code = ?"
            params.append(zip_code)

        if property_type:
            query += " AND property_type = ?"
            params.append(property_type)

        if date_from:
            query += " AND sale_date >= ?"
            params.append(date_from)

        if date_to:
            query += " AND sale_date <= ?"
            params.append(date_to)

        if min_price:
            query += " AND sale_price >= ?"
            params.append(min_price)

        if max_price:
            query += " AND sale_price <= ?"
            params.append(max_price)

        df = pd.read_sql_query(query, self.conn, params=params)
        return df

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class GeocodingModule:
    """
    Geocoding module using OpenStreetMap Nominatim API.

    Features:
    - Free API, no key required
    - Result caching to minimize API calls
    - Rate limiting (1 request/second per ToS)
    - Graceful error handling
    """

    def __init__(self, cache_file: str = "geocoding_cache.json", user_agent: str = "loudoun_property_analyzer"):
        """
        Initialize geocoding module.

        Args:
            cache_file: Path to JSON cache file
            user_agent: User agent string for Nominatim
        """
        self.cache_file = Path(cache_file)
        self.user_agent = user_agent
        self.geocoder = Nominatim(user_agent=user_agent, timeout=10)
        self.cache = self._load_cache()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests

    def _load_cache(self) -> Dict:
        """Load geocoding cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached geocoding results")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save geocoding cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _rate_limit(self):
        """Enforce rate limiting for Nominatim API."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address to lat/lon coordinates.

        Args:
            address: Full address string

        Returns:
            Tuple of (latitude, longitude) or None if failed
        """
        # Check cache first
        if address in self.cache:
            cached = self.cache[address]
            if cached:
                return (cached['lat'], cached['lon'])
            else:
                return None

        # Rate limit
        self._rate_limit()

        try:
            # Geocode address
            location = self.geocoder.geocode(address)

            if location:
                lat, lon = location.latitude, location.longitude
                self.cache[address] = {'lat': lat, 'lon': lon}
                self._save_cache()

                logger.debug(f"Geocoded: {address} → ({lat:.6f}, {lon:.6f})")
                return (lat, lon)
            else:
                # Cache negative results to avoid repeated failures
                self.cache[address] = None
                self._save_cache()

                logger.warning(f"Geocoding failed for: {address}")
                return None

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding error for {address}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected geocoding error: {e}")
            return None

    def batch_geocode(self, addresses: List[str], progress_callback=None) -> Dict[str, Optional[Tuple[float, float]]]:
        """
        Geocode multiple addresses with progress tracking.

        Args:
            addresses: List of address strings
            progress_callback: Optional callback function(current, total)

        Returns:
            Dictionary mapping address to (lat, lon) or None
        """
        results = {}

        for i, address in enumerate(addresses, 1):
            results[address] = self.geocode_address(address)

            if progress_callback:
                progress_callback(i, len(addresses))

        return results

    def get_cache_stats(self) -> Dict:
        """Get statistics about geocoding cache."""
        total = len(self.cache)
        successful = sum(1 for v in self.cache.values() if v is not None)
        failed = total - successful

        return {
            'total_cached': total,
            'successful': successful,
            'failed': failed,
            'hit_rate': (successful / total * 100) if total > 0 else 0
        }


class DistanceCalculator:
    """Calculate distances between properties using Haversine formula."""

    @staticmethod
    def calculate_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float,
        unit: str = 'miles'
    ) -> float:
        """
        Calculate distance between two points.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            unit: 'miles' or 'km'

        Returns:
            Distance in specified unit
        """
        point1 = (lat1, lon1)
        point2 = (lat2, lon2)

        distance_km = geodesic(point1, point2).kilometers

        if unit == 'miles':
            return distance_km * 0.621371  # Convert to miles
        else:
            return distance_km

    @staticmethod
    def find_properties_within_radius(
        center_lat: float,
        center_lon: float,
        properties: pd.DataFrame,
        radius_miles: float = 3.0
    ) -> pd.DataFrame:
        """
        Find all properties within a radius of a center point.

        Args:
            center_lat, center_lon: Center point coordinates
            properties: DataFrame with 'latitude' and 'longitude' columns
            radius_miles: Search radius in miles

        Returns:
            Filtered DataFrame with 'distance_miles' column added
        """
        # Filter out properties without coordinates
        valid_props = properties[
            properties['latitude'].notna() & properties['longitude'].notna()
        ].copy()

        if valid_props.empty:
            return pd.DataFrame()

        # Calculate distances
        distances = []
        for _, row in valid_props.iterrows():
            dist = DistanceCalculator.calculate_distance(
                center_lat, center_lon,
                row['latitude'], row['longitude'],
                unit='miles'
            )
            distances.append(dist)

        valid_props['distance_miles'] = distances

        # Filter by radius
        within_radius = valid_props[valid_props['distance_miles'] <= radius_miles]

        return within_radius.sort_values('distance_miles')

    @staticmethod
    def create_distance_matrix(properties: pd.DataFrame) -> pd.DataFrame:
        """
        Create distance matrix for all properties.

        Args:
            properties: DataFrame with 'id', 'latitude', 'longitude'

        Returns:
            DataFrame with pairwise distances (property_id x property_id)
        """
        # Filter valid coordinates
        valid_props = properties[
            properties['latitude'].notna() & properties['longitude'].notna()
        ][['id', 'latitude', 'longitude']].copy()

        n = len(valid_props)
        ids = valid_props['id'].tolist()

        # Initialize matrix
        distance_matrix = pd.DataFrame(
            np.zeros((n, n)),
            index=ids,
            columns=ids
        )

        # Calculate pairwise distances
        coords = valid_props[['latitude', 'longitude']].values

        for i in range(n):
            for j in range(i+1, n):
                dist = DistanceCalculator.calculate_distance(
                    coords[i][0], coords[i][1],
                    coords[j][0], coords[j][1],
                    unit='miles'
                )
                distance_matrix.iloc[i, j] = dist
                distance_matrix.iloc[j, i] = dist

        return distance_matrix


class DataEnricher:
    """Enrich sales data with calculated fields and standardization."""

    @staticmethod
    def add_calculated_fields(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add calculated fields to dataframe.

        Args:
            df: Sales dataframe

        Returns:
            Enriched dataframe
        """
        df = df.copy()
        current_year = datetime.now().year

        # Price per square foot
        if 'sale_price' in df.columns and 'sqft' in df.columns:
            valid_mask = (df['sale_price'] > 0) & (df['sqft'] > 0)
            df.loc[valid_mask, 'price_per_sqft'] = (
                df.loc[valid_mask, 'sale_price'] / df.loc[valid_mask, 'sqft']
            )

        # Property age
        if 'year_built' in df.columns:
            df['property_age'] = current_year - df['year_built']

        # Days since sale
        if 'sale_date' in df.columns:
            df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')
            df['days_since_sale'] = (datetime.now() - df['sale_date']).dt.days

        # Sale year and month
        if 'sale_date' in df.columns:
            df['sale_year'] = df['sale_date'].dt.year
            df['sale_month'] = df['sale_date'].dt.month
            df['sale_year_month'] = df['sale_date'].dt.to_period('M').astype(str)

        logger.info("Added calculated fields")
        return df

    @staticmethod
    def standardize_addresses(df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize address formats.

        Args:
            df: DataFrame with 'address' column

        Returns:
            DataFrame with standardized addresses
        """
        df = df.copy()

        if 'address' not in df.columns:
            return df

        def standardize(address):
            if pd.isna(address):
                return address

            # Convert to string and strip
            addr = str(address).strip()

            # Standardize common abbreviations
            replacements = {
                r'\bSt\b': 'Street',
                r'\bAve\b': 'Avenue',
                r'\bRd\b': 'Road',
                r'\bDr\b': 'Drive',
                r'\bLn\b': 'Lane',
                r'\bCt\b': 'Court',
                r'\bPl\b': 'Place',
                r'\bPkwy\b': 'Parkway',
                r'\bBlvd\b': 'Boulevard',
            }

            for pattern, replacement in replacements.items():
                addr = re.sub(pattern, replacement, addr, flags=re.IGNORECASE)

            return addr

        df['address_standardized'] = df['address'].apply(standardize)

        logger.info("Standardized addresses")
        return df

    @staticmethod
    def extract_zip_from_address(df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract ZIP codes from addresses if missing.

        Args:
            df: DataFrame with 'address' column

        Returns:
            DataFrame with filled ZIP codes
        """
        df = df.copy()

        if 'address' not in df.columns:
            return df

        def extract_zip(row):
            # If ZIP already exists, keep it
            if pd.notna(row.get('zip_code')):
                return row.get('zip_code')

            # Extract from address
            address = str(row.get('address', ''))
            match = re.search(r'\b(\d{5})\b', address)

            if match:
                return match.group(1)

            return None

        missing_zip_count = df['zip_code'].isna().sum()

        df['zip_code'] = df.apply(extract_zip, axis=1)

        filled_count = missing_zip_count - df['zip_code'].isna().sum()
        logger.info(f"Filled {filled_count} missing ZIP codes from addresses")

        return df

    @staticmethod
    def infer_property_type(df: pd.DataFrame) -> pd.DataFrame:
        """
        Infer property type from characteristics if missing.

        Args:
            df: Sales dataframe

        Returns:
            DataFrame with inferred property types
        """
        df = df.copy()

        def infer_type(row):
            # If type already exists, keep it
            if pd.notna(row.get('property_type')):
                return row.get('property_type')

            # Infer from characteristics
            sqft = row.get('sqft', 0)
            lot_size = row.get('lot_size_acres', 0)

            if sqft > 0:
                if sqft < 1500:
                    return 'Townhouse'
                elif lot_size > 0.5:
                    return 'Single Family'
                else:
                    return 'Condo'

            return 'Single Family'  # Default

        missing_count = df['property_type'].isna().sum()

        df['property_type'] = df.apply(infer_type, axis=1)

        filled_count = missing_count - df['property_type'].isna().sum()
        logger.info(f"Inferred {filled_count} missing property types")

        return df


class DataExporter:
    """Export cleaned and enriched data."""

    @staticmethod
    def export_to_database(df: pd.DataFrame, db_path: str, table_name: str = 'sales'):
        """
        Export dataframe to new SQLite database.

        Args:
            df: DataFrame to export
            db_path: Path to output database
            table_name: Table name
        """
        output_path = Path(db_path)

        # Remove existing file if it exists
        if output_path.exists():
            logger.warning(f"Removing existing database: {output_path}")
            output_path.unlink()

        # Export to SQLite
        conn = sqlite3.connect(output_path)

        df.to_sql(table_name, conn, if_exists='replace', index=False)

        conn.close()

        logger.info(f"Exported {len(df)} records to {output_path}")

    @staticmethod
    def export_to_csv(df: pd.DataFrame, csv_path: str):
        """
        Export dataframe to CSV.

        Args:
            df: DataFrame to export
            csv_path: Path to output CSV
        """
        output_path = Path(csv_path)

        df.to_csv(output_path, index=False)

        logger.info(f"Exported {len(df)} records to {output_path}")

    @staticmethod
    def export_subset(
        df: pd.DataFrame,
        output_path: str,
        zip_code: str = None,
        date_from: str = None,
        date_to: str = None
    ):
        """
        Export filtered subset of data.

        Args:
            df: Source dataframe
            output_path: Output file path (.csv or .db)
            zip_code: Filter by ZIP code
            date_from: Filter by date (from)
            date_to: Filter by date (to)
        """
        subset = df.copy()

        # Apply filters
        if zip_code:
            subset = subset[subset['zip_code'] == zip_code]

        if date_from:
            subset = subset[subset['sale_date'] >= date_from]

        if date_to:
            subset = subset[subset['sale_date'] <= date_to]

        # Export based on file extension
        output_path = Path(output_path)

        if output_path.suffix == '.csv':
            DataExporter.export_to_csv(subset, str(output_path))
        elif output_path.suffix == '.db':
            DataExporter.export_to_database(subset, str(output_path))
        else:
            raise ValueError(f"Unsupported file extension: {output_path.suffix}")

    @staticmethod
    def create_audit_trail(
        transformations: List[str],
        output_path: str = "data_integration_audit.json"
    ):
        """
        Create audit trail of all transformations.

        Args:
            transformations: List of transformation descriptions
            output_path: Path to audit file
        """
        audit = {
            'timestamp': datetime.now().isoformat(),
            'transformations': transformations
        }

        with open(output_path, 'w') as f:
            json.dump(audit, f, indent=2)

        logger.info(f"Audit trail saved to {output_path}")


def integrate_and_enrich_data(
    input_db: str = "loudoun_sales.db",
    output_db: str = "loudoun_sales_clean.db",
    geocode: bool = True,
    skip_cached: bool = True
) -> pd.DataFrame:
    """
    Main integration pipeline: load, geocode, enrich, and export.

    Args:
        input_db: Input database path
        output_db: Output database path
        geocode: Whether to geocode addresses
        skip_cached: Skip geocoding for addresses already in cache

    Returns:
        Enriched DataFrame
    """
    logger.info("="*80)
    logger.info("STARTING DATA INTEGRATION PIPELINE")
    logger.info("="*80)

    transformations = []

    # 1. Load data
    logger.info("\n1. Loading data from database...")
    with DatabaseConnector(input_db) as db:
        df = pd.read_sql_query("SELECT * FROM sales", db.conn)

    logger.info(f"Loaded {len(df)} records")
    transformations.append(f"Loaded {len(df)} records from {input_db}")

    # 2. Geocode addresses
    if geocode:
        logger.info("\n2. Geocoding addresses...")
        geocoder = GeocodingModule()

        # Get addresses that need geocoding
        needs_geocoding = df[
            (df['latitude'].isna()) | (df['longitude'].isna())
        ]['address'].unique().tolist()

        logger.info(f"Found {len(needs_geocoding)} addresses to geocode")

        if needs_geocoding:
            def progress(current, total):
                if current % 10 == 0 or current == total:
                    logger.info(f"Geocoded {current}/{total} addresses")

            results = geocoder.batch_geocode(needs_geocoding, progress_callback=progress)

            # Update dataframe with geocoded coordinates
            for address, coords in results.items():
                if coords:
                    lat, lon = coords
                    mask = (df['address'] == address) & (df['latitude'].isna() | df['longitude'].isna())
                    df.loc[mask, 'latitude'] = lat
                    df.loc[mask, 'longitude'] = lon

            successful = sum(1 for v in results.values() if v is not None)
            transformations.append(f"Geocoded {successful}/{len(needs_geocoding)} addresses")

        # Show cache stats
        stats = geocoder.get_cache_stats()
        logger.info(f"Geocoding cache: {stats['total_cached']} entries, {stats['hit_rate']:.1f}% hit rate")

    # 3. Add calculated fields
    logger.info("\n3. Adding calculated fields...")
    df = DataEnricher.add_calculated_fields(df)
    transformations.append("Added calculated fields: price_per_sqft, property_age, days_since_sale")

    # 4. Standardize addresses
    logger.info("\n4. Standardizing addresses...")
    df = DataEnricher.standardize_addresses(df)
    transformations.append("Standardized address formats")

    # 5. Fill missing ZIP codes
    logger.info("\n5. Filling missing ZIP codes...")
    df = DataEnricher.extract_zip_from_address(df)
    transformations.append("Extracted ZIP codes from addresses")

    # 6. Infer property types
    logger.info("\n6. Inferring property types...")
    df = DataEnricher.infer_property_type(df)
    transformations.append("Inferred missing property types")

    # 7. Export cleaned data
    logger.info("\n7. Exporting cleaned data...")
    DataExporter.export_to_database(df, output_db)
    transformations.append(f"Exported {len(df)} records to {output_db}")

    # Also export to CSV
    csv_path = output_db.replace('.db', '.csv')
    DataExporter.export_to_csv(df, csv_path)
    transformations.append(f"Exported to {csv_path}")

    # 8. Create audit trail
    DataExporter.create_audit_trail(transformations)

    logger.info("\n" + "="*80)
    logger.info("DATA INTEGRATION COMPLETE")
    logger.info("="*80)
    logger.info(f"Output database: {output_db}")
    logger.info(f"Output CSV: {csv_path}")
    logger.info(f"Audit trail: data_integration_audit.json")
    logger.info("="*80)

    return df


if __name__ == "__main__":
    import sys

    input_db = sys.argv[1] if len(sys.argv) > 1 else "loudoun_sales.db"
    output_db = sys.argv[2] if len(sys.argv) > 2 else "loudoun_sales_clean.db"

    df = integrate_and_enrich_data(input_db, output_db, geocode=True)

    print(f"\n✓ Integration complete!")
    print(f"  Records processed: {len(df)}")
    print(f"  Output: {output_db}")
