#!/usr/bin/env python3
"""
Location Quality Analyzer for Loudoun County

Sophisticated location analysis system that evaluates property location quality
based on highway proximity, data center corridor, road type, and commercial backing.

This is a KEY DIFFERENTIATOR - no other real estate platform provides this level
of location-specific analysis with value impact estimates.

Features:
- Highway proximity warnings (noise levels, distance)
- Data Center Corridor detection (unique to Loudoun!)
- Road type classification (cul-de-sac, interior, collector, arterial)
- Metro station proximity (positive factor)
- Commercial backing detection
- Quality score (1-10) with value impact estimate
- Neighborhood comparison

Author: Property Valuation System
Version: 2.0.0 (Phase 2 - Location Intelligence)
Date: November 2025
"""

import sqlite3
import logging
from typing import Dict, List, Tuple, Optional
from geopy.distance import geodesic
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# LOUDOUN COUNTY INFRASTRUCTURE DATA
# ============================================================================

# Major highways (multiple points along each route for accuracy)
MAJOR_HIGHWAYS = {
    'Route 7 (Leesburg Pike)': [
        (39.1157, -77.5636),  # Leesburg
        (39.0842, -77.4364),  # Sterling area
        (39.0456, -77.4234),  # Ashburn area
        (39.0234, -77.3987),  # Eastern Loudoun
        (39.0067, -77.3654),  # Near Fairfax border
    ],
    'Route 28 (Sully Road)': [
        (39.0789, -77.4567),  # Northern section
        (39.0456, -77.4456),  # Ashburn area
        (39.0123, -77.4345),  # Central section
        (38.9876, -77.4234),  # Southern section
    ],
    'Dulles Toll Road (Route 267)': [
        (39.0345, -77.4523),  # Western section
        (39.0234, -77.4123),  # Central section
        (39.0156, -77.3876),  # Eastern section
    ],
    'Route 50 (Lee-Jackson Memorial Highway)': [
        (39.0756, -77.5234),  # Aldie area
        (39.0456, -77.4876),  # South Riding
    ],
    'Loudoun County Parkway': [
        (39.0567, -77.5123),  # Northern section
        (39.0234, -77.4765),  # Central section
        (39.0012, -77.4456),  # Southern section
    ],
    'Waxpool Road': [
        (39.0456, -77.4567),  # Major collector in Ashburn
    ],
    'Belmont Ridge Road': [
        (39.0678, -77.5234),  # North-south collector
    ]
}

# Metro stations (Silver Line)
METRO_STATIONS = {
    'Ashburn Metro': (39.0408, -77.4875),
    'Loudoun Gateway Metro': (39.0678, -77.5234),
    'Dulles Airport Metro': (38.9531, -77.4565)
}

# Data Center Corridor (unique to Loudoun County!)
DATA_CENTER_CORRIDOR = {
    'center': (39.0234, -77.4567),  # Route 28 corridor
    'radius_miles': 2.5,
    'description': 'Route 28 Data Center Corridor - World\'s largest data center market'
}

# Commercial zones (for backing detection)
MAJOR_COMMERCIAL_ZONES = {
    'One Loudoun': (39.0234, -77.4876),
    'Ashburn Village Shopping Center': (39.0456, -77.4765),
    'Dulles Town Center': (39.0234, -77.4321),
    'Leesburg Premium Outlets': (39.0876, -77.5234),
}


class LocationQualityAnalyzer:
    """Analyze property location quality and proximity factors."""

    def __init__(self, db_path: str = "loudoun_development.db"):
        """
        Initialize location analyzer.

        Args:
            db_path: Development database path
        """
        self.db_path = db_path

    def analyze_location(
        self,
        lat: float,
        lon: float,
        address: str,
        subdivision: Optional[str] = None
    ) -> Dict:
        """
        Comprehensive location quality analysis.

        This is the A++ feature! Analyzes multiple location factors and
        provides a quality score (1-10) with specific warnings and positives.

        Args:
            lat: Property latitude
            lon: Property longitude
            address: Property address
            subdivision: Subdivision name (for neighborhood comparison)

        Returns:
            Dictionary with quality score, rating, warnings, positives, and details
        """
        logger.info(f"Analyzing location quality for: {address}")

        score = 10.0  # Start perfect
        warnings = []
        positives = []

        # ============================================================
        # 1. HIGHWAY PROXIMITY ANALYSIS
        # ============================================================
        highway_results = self.analyze_highway_proximity(lat, lon)

        if highway_results['nearest_distance'] < 0.1:  # < 528 feet
            score -= 3.0
            warnings.append({
                'severity': 'high',
                'icon': '⚠️',
                'title': 'Highway Noise Concern',
                'message': f"Within 500ft of {highway_results['nearest_highway']} - expect significant road noise (65-70dB)",
                'impact': 'Noise pollution may affect quality of life and property value'
            })
        elif highway_results['nearest_distance'] < 0.2:  # 528-1056 feet
            score -= 1.5
            warnings.append({
                'severity': 'medium',
                'icon': '⚠️',
                'title': 'Moderate Highway Proximity',
                'message': f"Within 1000ft of {highway_results['nearest_highway']} - moderate road noise possible",
                'impact': 'Some noise may be noticeable, especially at night'
            })
        elif highway_results['nearest_distance'] < 0.5:
            warnings.append({
                'severity': 'low',
                'icon': 'ℹ️',
                'title': 'Highway Proximity',
                'message': f"{highway_results['nearest_distance']:.2f} miles from {highway_results['nearest_highway']}",
                'impact': 'Minimal noise impact expected'
            })

        # ============================================================
        # 2. DATA CENTER CORRIDOR (UNIQUE TO LOUDOUN!)
        # ============================================================
        dc_proximity = self.analyze_data_center_proximity(lat, lon)

        if dc_proximity['in_corridor']:
            if dc_proximity['distance'] < 0.5:
                score -= 1.0
                warnings.append({
                    'severity': 'medium',
                    'icon': '🏢',
                    'title': 'Data Center Corridor Location',
                    'message': 'Within active Data Center Corridor - heavy commercial truck traffic',
                    'impact': 'Expect increased commercial traffic and industrial development'
                })
            else:
                warnings.append({
                    'severity': 'low',
                    'icon': 'ℹ️',
                    'title': 'Near Data Center Corridor',
                    'message': f"{dc_proximity['distance']:.1f} miles from corridor - active commercial area",
                    'impact': 'Area experiencing significant commercial development'
                })

        # ============================================================
        # 3. ROAD TYPE CLASSIFICATION
        # ============================================================
        road_type = self.classify_road_type(address)

        if road_type == 'Cul-de-sac':
            score += 0.5
            positives.append({
                'icon': '✓',
                'title': 'Cul-de-sac Location',
                'message': 'Property on cul-de-sac street - minimal through traffic',
                'impact': 'Excellent for families, very low traffic, high desirability'
            })
        elif road_type == 'Interior':
            positives.append({
                'icon': '✓',
                'title': 'Interior Residential Street',
                'message': 'Low-traffic residential street',
                'impact': 'Quiet location with minimal through traffic'
            })
        elif road_type == 'Collector':
            score -= 1.0
            warnings.append({
                'severity': 'medium',
                'icon': '⚠️',
                'title': 'Collector Road Location',
                'message': 'Property on collector road - moderate traffic volume',
                'impact': 'More traffic than interior streets, some noise'
            })
        elif road_type == 'Arterial':
            score -= 2.0
            warnings.append({
                'severity': 'high',
                'icon': '⚠️',
                'title': 'Arterial Road Location',
                'message': 'Property on major arterial road - high traffic volume',
                'impact': 'Significant traffic noise, safety concerns for children/pets'
            })

        # ============================================================
        # 4. METRO PROXIMITY (POSITIVE FACTOR)
        # ============================================================
        metro_results = self.analyze_metro_proximity(lat, lon)

        if metro_results['nearest_distance'] < 1.0:
            score += 1.0
            positives.append({
                'icon': '✓',
                'title': 'Metro Proximity - Excellent',
                'message': f"{metro_results['nearest_distance']:.1f} miles from {metro_results['nearest_station']}",
                'impact': 'Premium location - easy metro commute to DC/Tysons'
            })
        elif metro_results['nearest_distance'] < 2.0:
            score += 0.5
            positives.append({
                'icon': '✓',
                'title': 'Metro Proximity - Good',
                'message': f"{metro_results['nearest_distance']:.1f} miles from {metro_results['nearest_station']}",
                'impact': 'Convenient metro access for commuters'
            })
        elif metro_results['nearest_distance'] < 3.0:
            positives.append({
                'icon': 'ℹ️',
                'title': 'Metro Proximity - Fair',
                'message': f"{metro_results['nearest_distance']:.1f} miles from {metro_results['nearest_station']}",
                'impact': 'Metro accessible but may require driving to station'
            })

        # ============================================================
        # 5. COMMERCIAL BACKING DETECTION
        # ============================================================
        commercial_backing = self.check_commercial_backing(lat, lon)

        if commercial_backing['backs_to_commercial']:
            score -= 2.0
            warnings.append({
                'severity': 'high',
                'icon': '⚠️',
                'title': 'Commercial Backing',
                'message': f"Property backs to commercial zone - {commercial_backing['type']}",
                'impact': 'Noise, lights, reduced privacy. Typically -10-15% value impact'
            })

        # ============================================================
        # CALCULATE FINAL RESULTS
        # ============================================================

        # Clamp score to 1-10 range
        final_score = max(1.0, min(10.0, score))

        # Convert to rating
        rating = self.score_to_rating(final_score)

        # Calculate value impact
        value_impact = self.calculate_value_impact(final_score)

        # Neighborhood comparison (if subdivision provided)
        neighborhood_comparison = None
        if subdivision:
            neighborhood_comparison = self.compare_to_neighborhood(
                final_score, subdivision
            )

        result = {
            'quality_score': round(final_score, 1),
            'rating': rating,
            'value_impact_pct': value_impact,
            'warnings': warnings,
            'positives': positives,
            'details': {
                'highway_proximity': highway_results,
                'metro_proximity': metro_results,
                'data_center_proximity': dc_proximity,
                'road_classification': road_type,
                'commercial_backing': commercial_backing,
                'neighborhood_comparison': neighborhood_comparison
            }
        }

        logger.info(f"✓ Location quality score: {final_score:.1f}/10 ({rating})")

        return result

    def analyze_highway_proximity(self, lat: float, lon: float) -> Dict:
        """
        Calculate distance to nearest major highway.

        Args:
            lat: Property latitude
            lon: Property longitude

        Returns:
            Dictionary with nearest highway and distances to all highways
        """
        nearest_highway = None
        nearest_distance = float('inf')
        all_distances = {}

        for highway_name, points in MAJOR_HIGHWAYS.items():
            # Calculate distance to nearest point on this highway
            min_distance = min([
                geodesic((lat, lon), point).miles
                for point in points
            ])

            all_distances[highway_name] = round(min_distance, 2)

            if min_distance < nearest_distance:
                nearest_distance = min_distance
                nearest_highway = highway_name

        return {
            'nearest_highway': nearest_highway,
            'nearest_distance': round(nearest_distance, 2),
            'all_highways': all_distances
        }

    def analyze_metro_proximity(self, lat: float, lon: float) -> Dict:
        """
        Calculate distance to nearest Metro station.

        Args:
            lat: Property latitude
            lon: Property longitude

        Returns:
            Dictionary with nearest station and all station distances
        """
        nearest_station = None
        nearest_distance = float('inf')
        all_distances = {}

        for station_name, coords in METRO_STATIONS.items():
            distance = geodesic((lat, lon), coords).miles
            all_distances[station_name] = round(distance, 2)

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_station = station_name

        return {
            'nearest_station': nearest_station,
            'nearest_distance': round(nearest_distance, 2),
            'all_stations': all_distances
        }

    def analyze_data_center_proximity(self, lat: float, lon: float) -> Dict:
        """
        Check if property is in/near Data Center Corridor.

        This is UNIQUE to Loudoun County - world's largest data center market!

        Args:
            lat: Property latitude
            lon: Property longitude

        Returns:
            Dictionary with corridor proximity info
        """
        dc_center = DATA_CENTER_CORRIDOR['center']
        dc_radius = DATA_CENTER_CORRIDOR['radius_miles']

        distance = geodesic((lat, lon), dc_center).miles
        in_corridor = distance <= dc_radius

        return {
            'in_corridor': in_corridor,
            'distance': round(distance, 2),
            'corridor_name': DATA_CENTER_CORRIDOR['description']
        }

    def classify_road_type(self, address: str) -> str:
        """
        Classify road type from address.

        Patterns:
        - Cul-de-sac: CT, CIR, COURT, CIRCLE, PLACE
        - Arterial: Major road names (Route 7, Route 28, etc.)
        - Collector: BLVD, PKWY, PIKE, PARKWAY
        - Interior: Everything else

        Args:
            address: Property address

        Returns:
            Road type classification
        """
        address_upper = address.upper()

        # Cul-de-sac indicators
        cul_de_sac_indicators = [
            ' CT', ' CIR', 'COURT', 'CIRCLE', 'PLACE', ' PL'
        ]
        if any(indicator in address_upper for indicator in cul_de_sac_indicators):
            return 'Cul-de-sac'

        # Arterial roads (major highways)
        arterial_names = [
            'ROUTE 7', 'ROUTE 28', 'ROUTE 50', 'LEESBURG PIKE',
            'SULLY RD', 'BELMONT RIDGE', 'WAXPOOL RD'
        ]
        if any(name in address_upper for name in arterial_names):
            return 'Arterial'

        # Collector roads
        collector_indicators = ['BLVD', 'PKWY', 'PIKE', 'PARKWAY', 'BOULEVARD']
        if any(indicator in address_upper for indicator in collector_indicators):
            return 'Collector'

        # Default to interior residential
        return 'Interior'

    def check_commercial_backing(self, lat: float, lon: float) -> Dict:
        """
        Detect if property backs to commercial zone.

        Args:
            lat: Property latitude
            lon: Property longitude

        Returns:
            Dictionary with commercial backing info
        """
        nearest_commercial = None
        nearest_distance = float('inf')

        for zone_name, coords in MAJOR_COMMERCIAL_ZONES.items():
            distance = geodesic((lat, lon), coords).miles

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_commercial = zone_name

        # If within 0.1 miles (528 feet), likely backs to commercial
        backs_to_commercial = nearest_distance < 0.1

        return {
            'backs_to_commercial': backs_to_commercial,
            'type': nearest_commercial if backs_to_commercial else None,
            'distance_to_nearest': round(nearest_distance, 2)
        }

    def score_to_rating(self, score: float) -> str:
        """
        Convert 1-10 score to rating.

        Args:
            score: Quality score (1-10)

        Returns:
            Rating string
        """
        if score >= 9.0:
            return 'Excellent'
        elif score >= 8.0:
            return 'Very Good'
        elif score >= 7.0:
            return 'Good'
        elif score >= 6.0:
            return 'Fair'
        elif score >= 4.0:
            return 'Below Average'
        else:
            return 'Poor'

    def calculate_value_impact(self, score: float) -> int:
        """
        Estimate value impact vs average interior location.

        Score-based value adjustment:
        - 9.5+: +5% premium (cul-de-sac, near metro, quiet)
        - 8-9.4: 0% (standard interior location)
        - 7-7.9: 0% (standard)
        - 6-6.9: -5% (collector road or minor issues)
        - 4-5.9: -10% (arterial road or multiple issues)
        - <4: -15% (major issues: highway noise, commercial backing)

        Args:
            score: Quality score (1-10)

        Returns:
            Value impact percentage (-15 to +5)
        """
        if score >= 9.5:
            return 5
        elif score >= 8.0:
            return 0
        elif score >= 7.0:
            return 0
        elif score >= 6.0:
            return -5
        elif score >= 4.0:
            return -10
        else:
            return -15

    def compare_to_neighborhood(
        self,
        property_score: float,
        subdivision: str
    ) -> Optional[Dict]:
        """
        Compare property location to neighborhood average.

        Queries all properties in same subdivision and calculates
        average location score to show percentile ranking.

        Args:
            property_score: This property's quality score
            subdivision: Subdivision name

        Returns:
            Comparison dictionary or None if not enough data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            query = """
                SELECT latitude, longitude, address
                FROM building_permits
                WHERE subdivision = ?
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
                LIMIT 100
            """

            cursor = conn.cursor()
            cursor.execute(query, (subdivision,))
            properties = cursor.fetchall()
            conn.close()

            if len(properties) < 5:
                # Not enough data for meaningful comparison
                return None

            # Calculate score for each property
            scores = []
            for prop in properties:
                result = self.analyze_location(
                    prop['latitude'],
                    prop['longitude'],
                    prop['address']
                )
                scores.append(result['quality_score'])

            avg_score = np.mean(scores)
            percentile = (sum(s < property_score for s in scores) / len(scores)) * 100

            comparison = 'Above Average' if property_score > avg_score else 'Below Average'
            if abs(property_score - avg_score) < 0.5:
                comparison = 'Average'

            return {
                'neighborhood_average': round(avg_score, 1),
                'your_score': property_score,
                'percentile': round(percentile, 0),
                'comparison': comparison,
                'sample_size': len(scores)
            }

        except Exception as e:
            logger.warning(f"Neighborhood comparison failed: {e}")
            return None


if __name__ == "__main__":
    # Test with sample property
    print("\n" + "="*80)
    print("LOCATION QUALITY ANALYZER - TEST")
    print("="*80)

    analyzer = LocationQualityAnalyzer()

    # Test property in Ashburn
    test_address = "43500 Cloister Pl, Ashburn, VA 20147"
    test_lat = 39.0437
    test_lon = -77.4875

    result = analyzer.analyze_location(test_lat, test_lon, test_address)

    print(f"\nProperty: {test_address}")
    print(f"Quality Score: {result['quality_score']}/10")
    print(f"Rating: {result['rating']}")
    print(f"Value Impact: {result['value_impact_pct']:+d}%")

    print(f"\nWarnings ({len(result['warnings'])}):")
    for warning in result['warnings']:
        print(f"  {warning['icon']} {warning['title']}: {warning['message']}")

    print(f"\nPositives ({len(result['positives'])}):")
    for positive in result['positives']:
        print(f"  {positive['icon']} {positive['title']}: {positive['message']}")

    print("\n" + "="*80)
