#!/usr/bin/env python3
"""
Development Pressure Analyzer

Calculates Development Pressure Score (0-100) using weighted formula based on:
- Rezoning activity (30% weight)
- Building permits (25% weight)
- Large parcel sales (20% weight)
- Property appreciation (15% weight)
- Infrastructure proximity (10% weight)

Author: Property Valuation System
Version: 1.0.0
Date: November 2025
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from geopy.distance import geodesic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DevelopmentPressureAnalyzer:
    """Analyze development pressure around a property."""

    def __init__(self, dev_db_path: str = "loudoun_development.db"):
        """Initialize analyzer."""
        self.dev_db_path = dev_db_path
        self.weights = {
            'rezoning': 0.30,
            'permits': 0.25,
            'land_sales': 0.20,
            'appreciation': 0.15,
            'proximity': 0.10
        }

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in miles between two points."""
        return geodesic((lat1, lon1), (lat2, lon2)).miles

    def get_distance_weight(self, distance_miles: float) -> float:
        """
        Calculate distance weight multiplier.

        Args:
            distance_miles: Distance in miles

        Returns:
            Weight multiplier (0-1 mile: 1.0x, 1-3 miles: 0.5x, 3-5 miles: 0.25x)
        """
        if distance_miles <= 1.0:
            return 1.0
        elif distance_miles <= 3.0:
            return 0.5
        elif distance_miles <= 5.0:
            return 0.25
        else:
            return 0.0

    def calculate_rezoning_score(
        self,
        subject_lat: float,
        subject_lon: float,
        radius_miles: float = 5.0
    ) -> Tuple[float, Dict]:
        """
        Calculate rezoning score (0-100).

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            radius_miles: Search radius

        Returns:
            Tuple of (score, details_dict)
        """
        conn = sqlite3.connect(self.dev_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get rezonings from last 3 years
        cutoff_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT * FROM rezonings
            WHERE decision_date >= ?
        """, (cutoff_date,))

        rezonings = cursor.fetchall()
        conn.close()

        # Calculate weighted count
        weighted_count = 0
        by_distance = {'0-1mi': 0, '1-3mi': 0, '3-5mi': 0}

        for rezoning in rezonings:
            distance = self.calculate_distance(
                subject_lat, subject_lon,
                rezoning['latitude'], rezoning['longitude']
            )

            if distance <= radius_miles:
                weight = self.get_distance_weight(distance)
                weighted_count += weight

                # Track by distance zone
                if distance <= 1.0:
                    by_distance['0-1mi'] += 1
                elif distance <= 3.0:
                    by_distance['1-3mi'] += 1
                else:
                    by_distance['3-5mi'] += 1

        # Scale to 0-100
        if weighted_count == 0:
            score = 0
        elif weighted_count <= 2:
            score = weighted_count / 2 * 25
        elif weighted_count <= 5:
            score = 25 + ((weighted_count - 2) / 3) * 25
        elif weighted_count <= 10:
            score = 50 + ((weighted_count - 5) / 5) * 25
        else:
            score = min(75 + ((weighted_count - 10) / 5) * 25, 100)

        details = {
            'weighted_count': weighted_count,
            'total_rezonings': len([r for r in rezonings if self.calculate_distance(
                subject_lat, subject_lon, r['latitude'], r['longitude']
            ) <= radius_miles]),
            'by_distance': by_distance,
            'score': round(score, 1)
        }

        logger.debug(f"Rezoning score: {score:.1f} (weighted count: {weighted_count:.2f})")

        return round(score, 1), details

    def calculate_permit_score(
        self,
        subject_lat: float,
        subject_lon: float,
        radius_miles: float = 5.0,
        use_real_data: bool = True
    ) -> Tuple[float, Dict]:
        """
        Calculate building permit score (0-100).

        Updated for Phase 2: Uses real permit data with proper categorization
        and weighting for major commercial projects (3x multiplier).

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            radius_miles: Search radius in miles
            use_real_data: If True, use real permit schema; if False, use sample schema

        Returns:
            Tuple of (score, details_dict)
        """
        conn = sqlite3.connect(self.dev_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get permits from last 2 years
        cutoff_date = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')

        # Check if using real data schema or sample data schema
        try:
            cursor.execute("SELECT issue_date FROM building_permits LIMIT 1")
            cursor.fetchone()
            # Real data schema has 'issue_date'
            date_field = 'issue_date'
        except sqlite3.OperationalError:
            # Sample data schema might have different field name
            date_field = 'issue_date'

        cursor.execute(f"""
            SELECT * FROM building_permits
            WHERE {date_field} >= ?
        """, (cutoff_date,))

        permits = cursor.fetchall()
        conn.close()

        # Calculate weighted count
        weighted_count = 0
        by_distance = {'0-1mi': 0, '1-3mi': 0, '3-5mi': 0}
        by_type = {'Residential': 0, 'Commercial': 0, 'Major Commercial': 0, 'Other': 0}

        for permit in permits:
            # Skip if no geolocation
            if not permit['latitude'] or not permit['longitude']:
                continue

            distance = self.calculate_distance(
                subject_lat, subject_lon,
                permit['latitude'], permit['longitude']
            )

            if distance <= radius_miles:
                # Type weighting (Phase 2: Use real data categorization)
                type_weight = 1.0

                # Check for major commercial (3x multiplier)
                if 'is_major_commercial' in permit.keys() and permit['is_major_commercial']:
                    type_weight = 3.0
                    by_type['Major Commercial'] += 1
                elif 'category' in permit.keys():
                    # Use real data category
                    category = permit['category'] or ''
                    if 'Commercial' in category:
                        type_weight = 1.5
                        by_type['Commercial'] += 1
                    elif 'Residential' in category:
                        type_weight = 1.0
                        by_type['Residential'] += 1
                    else:
                        by_type['Other'] += 1
                else:
                    # Fallback to old schema (sample data)
                    project_type = permit.get('project_type', 'Unknown')
                    sqft = permit.get('sqft', 0)

                    if project_type == 'Commercial' and sqft and sqft > 25000:
                        type_weight = 3.0  # Major commercial
                        by_type['Major Commercial'] += 1
                    elif project_type == 'Commercial':
                        type_weight = 1.5
                        by_type['Commercial'] += 1
                    elif project_type == 'Residential':
                        by_type['Residential'] += 1
                    else:
                        by_type['Other'] += 1

                # Distance weighting
                distance_weight = self.get_distance_weight(distance)

                weighted_count += type_weight * distance_weight

                # Track by distance
                if distance <= 1.0:
                    by_distance['0-1mi'] += 1
                elif distance <= 3.0:
                    by_distance['1-3mi'] += 1
                else:
                    by_distance['3-5mi'] += 1

        # Scale to 0-100
        if weighted_count <= 2:
            score = 0
        elif weighted_count <= 5:
            score = ((weighted_count - 2) / 3) * 30
        elif weighted_count <= 10:
            score = 30 + ((weighted_count - 5) / 5) * 30
        elif weighted_count <= 20:
            score = 60 + ((weighted_count - 10) / 10) * 20
        else:
            score = min(80 + ((weighted_count - 20) / 10) * 20, 100)

        details = {
            'weighted_count': weighted_count,
            'total_permits': len([p for p in permits if self.calculate_distance(
                subject_lat, subject_lon, p['latitude'], p['longitude']
            ) <= radius_miles]),
            'by_distance': by_distance,
            'by_type': by_type,
            'score': round(score, 1)
        }

        logger.debug(f"Permit score: {score:.1f} (weighted count: {weighted_count:.2f})")

        return round(score, 1), details

    def calculate_land_sale_score(
        self,
        subject_lat: float,
        subject_lon: float,
        radius_miles: float = 5.0
    ) -> Tuple[float, Dict]:
        """Calculate large parcel sale score (0-100)."""
        conn = sqlite3.connect(self.dev_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get sales from last 2 years
        cutoff_date = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT * FROM large_parcel_sales
            WHERE sale_date >= ?
        """, (cutoff_date,))

        sales = cursor.fetchall()
        conn.close()

        # Calculate weighted count
        weighted_count = 0
        by_distance = {'0-1mi': 0, '1-3mi': 0, '3-5mi': 0}

        for sale in sales:
            distance = self.calculate_distance(
                subject_lat, subject_lon,
                sale['latitude'], sale['longitude']
            )

            if distance <= radius_miles:
                weight = self.get_distance_weight(distance)
                weighted_count += weight

                # Track by distance
                if distance <= 1.0:
                    by_distance['0-1mi'] += 1
                elif distance <= 3.0:
                    by_distance['1-3mi'] += 1
                else:
                    by_distance['3-5mi'] += 1

        # Scale to 0-100
        if weighted_count == 0:
            score = 0
        elif weighted_count <= 2:
            score = weighted_count / 2 * 40
        elif weighted_count <= 5:
            score = 40 + ((weighted_count - 2) / 3) * 30
        else:
            score = min(70 + ((weighted_count - 5) / 3) * 30, 100)

        details = {
            'weighted_count': weighted_count,
            'total_sales': len([s for s in sales if self.calculate_distance(
                subject_lat, subject_lon, s['latitude'], s['longitude']
            ) <= radius_miles]),
            'by_distance': by_distance,
            'score': round(score, 1)
        }

        logger.debug(f"Land sale score: {score:.1f} (weighted count: {weighted_count:.2f})")

        return round(score, 1), details

    def calculate_appreciation_score(
        self,
        subject_lat: float,
        subject_lon: float,
        local_appreciation: float = 0.08,  # Default 8% annual
        county_appreciation: float = 0.06  # Default 6% annual
    ) -> Tuple[float, Dict]:
        """
        Calculate appreciation score (0-100).

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            local_appreciation: Local area appreciation rate
            county_appreciation: County-wide appreciation rate

        Returns:
            Tuple of (score, details_dict)
        """
        # Calculate ratio
        if county_appreciation > 0:
            ratio = local_appreciation / county_appreciation
        else:
            ratio = 1.0

        # Scale to 0-100
        if ratio < 0.8:
            score = 0
        elif ratio < 1.0:
            score = ((ratio - 0.8) / 0.2) * 25
        elif ratio < 1.5:
            score = 25 + ((ratio - 1.0) / 0.5) * 35
        elif ratio < 2.0:
            score = 60 + ((ratio - 1.5) / 0.5) * 25
        else:
            score = min(85 + ((ratio - 2.0) / 1.0) * 15, 100)

        details = {
            'local_rate': local_appreciation,
            'county_rate': county_appreciation,
            'ratio': ratio,
            'score': round(score, 1)
        }

        logger.debug(f"Appreciation score: {score:.1f} (ratio: {ratio:.2f})")

        return round(score, 1), details

    def calculate_proximity_score(
        self,
        subject_lat: float,
        subject_lon: float
    ) -> Tuple[float, Dict]:
        """
        Calculate infrastructure proximity score (0-100).

        Major features:
        - Highways: Route 7, Route 28, Dulles Toll Road, Route 50
        - Metro: Silver Line stations
        - Dulles Airport
        """
        # Major infrastructure coordinates (approximate)
        infrastructure = {
            'route_28': (39.0437, -77.4875),  # Route 28 / Ashburn
            'route_7': (39.0800, -77.5100),   # Route 7 / Leesburg
            'dulles_toll': (38.9600, -77.4500),  # Dulles Toll Road
            'ashburn_metro': (39.0075, -77.4865),  # Ashburn Metro
            'dulles_airport': (38.9531, -77.4565)  # Dulles Airport
        }

        # Calculate distances
        highway_distances = []
        metro_distances = []
        airport_distance = self.calculate_distance(
            subject_lat, subject_lon,
            *infrastructure['dulles_airport']
        )

        # Highways
        for key in ['route_28', 'route_7', 'dulles_toll']:
            dist = self.calculate_distance(subject_lat, subject_lon, *infrastructure[key])
            highway_distances.append(dist)

        # Metro
        metro_distance = self.calculate_distance(
            subject_lat, subject_lon,
            *infrastructure['ashburn_metro']
        )
        metro_distances.append(metro_distance)

        # Calculate scores
        min_highway_dist = min(highway_distances)
        min_metro_dist = min(metro_distances)

        # Highway score
        if min_highway_dist <= 2.0:
            highway_score = 100
        elif min_highway_dist <= 5.0:
            highway_score = 50
        else:
            highway_score = 0

        # Metro score
        if min_metro_dist <= 2.0:
            metro_score = 100
        elif min_metro_dist <= 5.0:
            metro_score = 50
        else:
            metro_score = 0

        # Airport score
        if airport_distance <= 5.0:
            airport_score = 50
        elif airport_distance <= 10.0:
            airport_score = 25
        else:
            airport_score = 0

        # Average the three
        final_score = (highway_score + metro_score + airport_score) / 3

        details = {
            'highway_distance': round(min_highway_dist, 2),
            'metro_distance': round(min_metro_dist, 2),
            'airport_distance': round(airport_distance, 2),
            'highway_score': highway_score,
            'metro_score': metro_score,
            'airport_score': airport_score,
            'score': round(final_score, 1)
        }

        logger.debug(f"Proximity score: {final_score:.1f}")

        return round(final_score, 1), details

    def _get_activity_lists(
        self,
        subject_lat: float,
        subject_lon: float,
        radius_miles: float = 5.0
    ) -> Dict:
        """
        Get lists of actual activity items for reports.

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            radius_miles: Search radius in miles

        Returns:
            Dictionary with lists of rezonings, permits, and land sales
        """
        conn = sqlite3.connect(self.dev_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get rezonings
        cursor.execute("SELECT * FROM rezonings")
        all_rezonings = cursor.fetchall()
        rezonings = []
        for r in all_rezonings:
            distance = self.calculate_distance(
                subject_lat, subject_lon,
                r['latitude'], r['longitude']
            )
            if distance <= radius_miles:
                rezonings.append({
                    'address': r['address'],
                    'previous_zoning': r['previous_zoning'],
                    'new_zoning': r['new_zoning'],
                    'vote_result': r['vote_result'],
                    'decision_date': r['decision_date'],
                    'distance_miles': round(distance, 2)
                })

        # Get building permits
        cursor.execute("SELECT * FROM building_permits")
        all_permits = cursor.fetchall()
        permits = []
        for p in all_permits:
            # Skip if no geolocation
            if not p['latitude'] or not p['longitude']:
                continue

            distance = self.calculate_distance(
                subject_lat, subject_lon,
                p['latitude'], p['longitude']
            )
            if distance <= radius_miles:
                # Handle both real data and sample data schemas
                if 'category' in p.keys():
                    # Real data schema
                    permits.append({
                        'address': p['address'],
                        'project_type': p.get('category', 'Unknown'),
                        'sqft': p.get('sqft', 0) or 0,
                        'valuation': p.get('estimated_cost', 0) or 0,
                        'status': p.get('status', 'Unknown'),
                        'issue_date': p.get('issue_date', ''),
                        'distance_miles': round(distance, 2),
                        'is_major_commercial': p.get('is_major_commercial', False)
                    })
                else:
                    # Sample data schema (fallback)
                    permits.append({
                        'address': p['address'],
                        'project_type': p.get('project_type', 'Unknown'),
                        'sqft': p.get('sqft', 0),
                        'valuation': p.get('valuation', 0),
                        'status': p.get('status', 'Unknown'),
                        'issue_date': p.get('issue_date', ''),
                        'distance_miles': round(distance, 2),
                        'is_major_commercial': False
                    })

        # Get large parcel sales
        cursor.execute("SELECT * FROM large_parcel_sales")
        all_sales = cursor.fetchall()
        land_sales = []
        for s in all_sales:
            distance = self.calculate_distance(
                subject_lat, subject_lon,
                s['latitude'], s['longitude']
            )
            if distance <= radius_miles:
                land_sales.append({
                    'address': s['address'],
                    'acreage': s['acreage'],
                    'sale_price': s['sale_price'],
                    'buyer_type': s['buyer_type'],
                    'sale_date': s['sale_date'],
                    'distance_miles': round(distance, 2)
                })

        conn.close()

        # Sort by distance
        rezonings.sort(key=lambda x: x['distance_miles'])
        permits.sort(key=lambda x: x['distance_miles'])
        land_sales.sort(key=lambda x: x['distance_miles'])

        return {
            'rezonings': rezonings,
            'permits': permits,
            'land_sales': land_sales
        }

    def calculate_development_pressure(
        self,
        subject_lat: float,
        subject_lon: float,
        local_appreciation: float = 0.08,
        county_appreciation: float = 0.06
    ) -> Dict:
        """
        Calculate overall development pressure score.

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            local_appreciation: Local appreciation rate (optional)
            county_appreciation: County appreciation rate (optional)

        Returns:
            Dictionary with scores and details
        """
        logger.info(f"Calculating development pressure for ({subject_lat:.4f}, {subject_lon:.4f})")

        # Calculate component scores
        rezoning_score, rezoning_details = self.calculate_rezoning_score(subject_lat, subject_lon)
        permit_score, permit_details = self.calculate_permit_score(subject_lat, subject_lon)
        land_sale_score, land_sale_details = self.calculate_land_sale_score(subject_lat, subject_lon)
        appreciation_score, appreciation_details = self.calculate_appreciation_score(
            subject_lat, subject_lon, local_appreciation, county_appreciation
        )
        proximity_score, proximity_details = self.calculate_proximity_score(subject_lat, subject_lon)

        # Calculate weighted total
        total_score = (
            rezoning_score * self.weights['rezoning'] +
            permit_score * self.weights['permits'] +
            land_sale_score * self.weights['land_sales'] +
            appreciation_score * self.weights['appreciation'] +
            proximity_score * self.weights['proximity']
        )

        # Determine classification
        if total_score < 20:
            classification = "Very Low"
            risk_level = "Minimal"
        elif total_score < 40:
            classification = "Low"
            risk_level = "Low"
        elif total_score < 60:
            classification = "Medium"
            risk_level = "Moderate"
        elif total_score < 80:
            classification = "High"
            risk_level = "High"
        else:
            classification = "Very High"
            risk_level = "Very High"

        # Fetch activity lists for reports
        activity_lists = self._get_activity_lists(subject_lat, subject_lon)

        result = {
            'total_score': round(total_score, 1),
            'classification': classification,
            'risk_level': risk_level,
            'components': {
                'rezoning_score': rezoning_score,
                'permit_score': permit_score,
                'land_sale_score': land_sale_score,
                'appreciation_score': appreciation_score,
                'proximity_score': proximity_score
            },
            'components_detailed': {
                'rezoning': {
                    'score': rezoning_score,
                    'weight': self.weights['rezoning'],
                    'weighted_contribution': round(rezoning_score * self.weights['rezoning'], 1),
                    'details': rezoning_details
                },
                'permits': {
                    'score': permit_score,
                    'weight': self.weights['permits'],
                    'weighted_contribution': round(permit_score * self.weights['permits'], 1),
                    'details': permit_details
                },
                'land_sales': {
                    'score': land_sale_score,
                    'weight': self.weights['land_sales'],
                    'weighted_contribution': round(land_sale_score * self.weights['land_sales'], 1),
                    'details': land_sale_details
                },
                'appreciation': {
                    'score': appreciation_score,
                    'weight': self.weights['appreciation'],
                    'weighted_contribution': round(appreciation_score * self.weights['appreciation'], 1),
                    'details': appreciation_details
                },
                'proximity': {
                    'score': proximity_score,
                    'weight': self.weights['proximity'],
                    'weighted_contribution': round(proximity_score * self.weights['proximity'], 1),
                    'details': proximity_details
                }
            },
            'details': activity_lists
        }

        logger.info(f"✓ Development Pressure Score: {total_score:.1f} ({classification})")

        return result


if __name__ == "__main__":
    # Test with sample property in Ashburn
    print("\nDevelopment Pressure Analyzer Test")
    print("="*60)

    analyzer = DevelopmentPressureAnalyzer()

    # Test property: 43500 Cloister Pl, Ashburn, VA
    test_lat = 39.0437
    test_lon = -77.4875

    result = analyzer.calculate_development_pressure(test_lat, test_lon)

    print(f"\nDevelopment Pressure Score: {result['total_score']}/100")
    print(f"Classification: {result['classification']}")
    print(f"Risk Level: {result['risk_level']}")

    print(f"\nComponent Scores:")
    for component, data in result['components'].items():
        print(f"  {component.replace('_', ' ').title():15s}: {data['score']:5.1f} "
              f"(weight: {data['weight']:.0%}, contribution: {data['weighted_contribution']:.1f})")

    print("\n✓ Test complete!")
