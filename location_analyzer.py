"""
Location Quality Analyzer for Loudoun County Properties

Analyzes property location characteristics including:
- Highway proximity and noise impact
- Road classification (interior/collector/arterial/cul-de-sac)
- Metro station access
- Data center corridor proximity
- Commercial backing concerns
- Location quality scoring (0-10)

Author: NewCo Real Estate Intelligence
Date: November 2024
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LocationAnalysisResult:
    """Results from location quality analysis"""
    quality_score: float  # 0-10 scale
    rating: str  # Excellent/Very Good/Good/Fair/Poor
    value_impact_pct: int  # Percentage impact vs comparable properties
    road_classification: str  # Interior/Collector/Arterial/Cul-de-sac
    warnings: List[str]
    positives: List[str]
    highway_distances: Dict[str, float]
    metro_distances: Dict[str, float]
    overall_assessment: str


class LocationQualityAnalyzer:
    """Analyzes location quality for Loudoun County properties"""

    # Major highways in Loudoun County (lat, lon)
    HIGHWAYS = {
        'Route 7 (Leesburg Pike)': (39.0472, -77.4835),
        'Route 28 (Sully Road)': (39.0234, -77.4234),
        'Route 50 (John Mosby Highway)': (38.9956, -77.5345),
        'Dulles Toll Road (267)': (38.9534, -77.4456),
        'Greenway (267 Toll)': (39.0123, -77.4567)
    }

    # Metro stations (Silver Line)
    METRO_STATIONS = {
        'Ashburn': (39.0068, -77.4874),
        'Loudoun Gateway': (39.0087, -77.4426),
        'Dulles Airport': (38.9531, -77.4565),
        'Innovation Center': (38.9589, -77.4294)
    }

    # Data Center Corridor (approximate bounds)
    DATA_CENTER_CORRIDOR = {
        'center': (39.0456, -77.4523),
        'radius_miles': 3.0
    }

    def __init__(self):
        """Initialize the location quality analyzer"""
        pass

    def analyze_location(self, lat: float, lon: float, address: str = "") -> Dict:
        """
        Comprehensive location quality analysis

        Args:
            lat: Property latitude
            lon: Property longitude
            address: Property address (for context)

        Returns:
            Dictionary with analysis results
        """
        # Calculate highway distances
        highway_distances = self._calculate_highway_distances(lat, lon)

        # Calculate metro distances
        metro_distances = self._calculate_metro_distances(lat, lon)

        # Determine road classification
        road_class = self._classify_road_location(lat, lon, highway_distances)

        # Check for data center corridor proximity
        in_data_center_corridor = self._check_data_center_corridor(lat, lon)

        # Generate warnings and positives
        warnings, positives = self._generate_location_insights(
            highway_distances, metro_distances, road_class, in_data_center_corridor
        )

        # Calculate quality score
        quality_score = self._calculate_quality_score(
            highway_distances, metro_distances, road_class, in_data_center_corridor
        )

        # Determine rating
        rating = self._get_rating(quality_score)

        # Calculate value impact
        value_impact_pct = self._calculate_value_impact(quality_score, warnings)

        # Generate overall assessment
        assessment = self._generate_overall_assessment(
            quality_score, rating, road_class, warnings, positives
        )

        return {
            'quality_score': round(quality_score, 1),
            'rating': rating,
            'value_impact_pct': value_impact_pct,
            'road_classification': road_class,
            'warnings': warnings,
            'positives': positives,
            'highway_distances': highway_distances,
            'metro_distances': metro_distances,
            'in_data_center_corridor': in_data_center_corridor,
            'overall_assessment': assessment,
            'address': address,
            'coordinates': {'lat': lat, 'lon': lon}
        }

    def _calculate_distance_miles(self, lat1: float, lon1: float,
                                   lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula"""
        R = 3959  # Earth's radius in miles

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _calculate_highway_distances(self, lat: float, lon: float) -> Dict[str, float]:
        """Calculate distances to major highways"""
        distances = {}
        for highway, (h_lat, h_lon) in self.HIGHWAYS.items():
            dist = self._calculate_distance_miles(lat, lon, h_lat, h_lon)
            distances[highway] = round(dist, 2)
        return distances

    def _calculate_metro_distances(self, lat: float, lon: float) -> Dict[str, float]:
        """Calculate distances to metro stations"""
        distances = {}
        for station, (s_lat, s_lon) in self.METRO_STATIONS.items():
            dist = self._calculate_distance_miles(lat, lon, s_lat, s_lon)
            distances[station] = round(dist, 2)
        return distances

    def _classify_road_location(self, lat: float, lon: float,
                                 highway_distances: Dict[str, float]) -> str:
        """Classify the road type based on location characteristics"""
        # Get closest highway
        min_highway_dist = min(highway_distances.values())

        # Simple classification logic
        if min_highway_dist < 0.3:
            return "Arterial Road"
        elif min_highway_dist < 0.8:
            return "Collector Road"
        else:
            return "Interior/Residential"

    def _check_data_center_corridor(self, lat: float, lon: float) -> bool:
        """Check if property is in the data center corridor"""
        center_lat, center_lon = self.DATA_CENTER_CORRIDOR['center']
        radius = self.DATA_CENTER_CORRIDOR['radius_miles']

        dist = self._calculate_distance_miles(lat, lon, center_lat, center_lon)
        return dist <= radius

    def _generate_location_insights(self, highway_distances: Dict[str, float],
                                    metro_distances: Dict[str, float],
                                    road_class: str,
                                    in_data_center: bool) -> Tuple[List[str], List[str]]:
        """Generate warnings and positive insights"""
        warnings = []
        positives = []

        # Highway proximity warnings
        for highway, dist in highway_distances.items():
            if dist < 0.5:
                warnings.append(
                    f"⚠️ Very close to {highway} ({dist} mi) - potential noise and air quality concerns"
                )
            elif dist < 1.0:
                warnings.append(
                    f"⚠️ Near {highway} ({dist} mi) - minor traffic noise possible"
                )

        # Data center corridor
        if in_data_center:
            warnings.append(
                "⚠️ Located in Data Center Corridor - ongoing commercial development activity"
            )

        # Positives based on road classification
        if road_class == "Interior/Residential":
            positives.append(
                "✓ Interior residential location - quieter neighborhood with less through traffic"
            )

        # Metro accessibility positives
        min_metro_dist = min(metro_distances.values())
        closest_metro = min(metro_distances, key=metro_distances.get)

        if min_metro_dist < 2.0:
            positives.append(
                f"✓ Excellent metro access - {closest_metro} station only {min_metro_dist} mi away"
            )
        elif min_metro_dist < 4.0:
            positives.append(
                f"✓ Good metro access - {closest_metro} station {min_metro_dist} mi away"
            )

        # General highway access (not too close, not too far)
        min_highway_dist = min(highway_distances.values())
        if 1.0 <= min_highway_dist <= 3.0:
            positives.append(
                "✓ Optimal highway access - convenient but buffered from traffic noise"
            )

        return warnings, positives

    def _calculate_quality_score(self, highway_distances: Dict[str, float],
                                 metro_distances: Dict[str, float],
                                 road_class: str,
                                 in_data_center: bool) -> float:
        """Calculate overall location quality score (0-10)"""
        score = 10.0  # Start with perfect score

        # Deduct for highway proximity
        min_highway_dist = min(highway_distances.values())
        if min_highway_dist < 0.3:
            score -= 3.0  # Major deduction for very close
        elif min_highway_dist < 0.5:
            score -= 2.0
        elif min_highway_dist < 1.0:
            score -= 1.0
        elif min_highway_dist > 5.0:
            score -= 0.5  # Slight deduction for being too far

        # Bonus for interior location
        if road_class == "Interior/Residential":
            score += 1.0
        elif road_class == "Arterial Road":
            score -= 1.5

        # Metro accessibility
        min_metro_dist = min(metro_distances.values())
        if min_metro_dist < 2.0:
            score += 1.5  # Excellent metro access
        elif min_metro_dist < 4.0:
            score += 0.5  # Good metro access
        elif min_metro_dist > 8.0:
            score -= 1.0  # Poor metro access

        # Data center corridor slight deduction
        if in_data_center:
            score -= 0.5

        # Ensure score is within 0-10
        return max(0.0, min(10.0, score))

    def _get_rating(self, score: float) -> str:
        """Convert numeric score to rating"""
        if score >= 8.5:
            return "Excellent"
        elif score >= 7.0:
            return "Very Good"
        elif score >= 5.5:
            return "Good"
        elif score >= 4.0:
            return "Fair"
        else:
            return "Poor"

    def _calculate_value_impact(self, quality_score: float, warnings: List[str]) -> int:
        """Calculate estimated value impact percentage"""
        # Base impact on quality score
        if quality_score >= 8.5:
            impact = 5  # 5% premium for excellent locations
        elif quality_score >= 7.0:
            impact = 2  # 2% premium for very good
        elif quality_score >= 5.5:
            impact = 0  # Neutral
        elif quality_score >= 4.0:
            impact = -3  # 3% discount for fair
        else:
            impact = -7  # 7% discount for poor

        # Additional penalty for severe highway proximity
        severe_highway_warnings = sum(1 for w in warnings if "Very close to" in w)
        impact -= severe_highway_warnings * 2

        return impact

    def _generate_overall_assessment(self, quality_score: float, rating: str,
                                     road_class: str, warnings: List[str],
                                     positives: List[str]) -> str:
        """Generate overall location assessment narrative"""
        assessment = f"This property has a {rating.lower()} location with a quality score of {quality_score}/10. "

        assessment += f"The property is situated on a {road_class.lower()}. "

        if positives:
            assessment += f"Key advantages include: {positives[0].replace('✓ ', '')}. "

        if warnings:
            assessment += f"Important considerations: {warnings[0].replace('⚠️ ', '')}. "

        return assessment


# Example usage
if __name__ == "__main__":
    analyzer = LocationQualityAnalyzer()

    # Test with 43500 Tuckaway Pl, Leesburg, VA 20176
    # Approximate coordinates (would normally geocode)
    result = analyzer.analyze_location(
        lat=39.0437,
        lon=-77.4875,
        address="43500 Tuckaway Pl, Leesburg, VA 20176"
    )

    print("\n" + "="*70)
    print("LOCATION QUALITY ANALYSIS")
    print("="*70)
    print(f"\nAddress: {result['address']}")
    print(f"Quality Score: {result['quality_score']}/10")
    print(f"Rating: {result['rating']}")
    print(f"Value Impact: {result['value_impact_pct']:+d}%")
    print(f"Road Classification: {result['road_classification']}")

    print(f"\n{'WARNINGS:':^70}")
    print("-"*70)
    if result['warnings']:
        for warning in result['warnings']:
            print(f"  {warning}")
    else:
        print("  No significant warnings")

    print(f"\n{'POSITIVES:':^70}")
    print("-"*70)
    if result['positives']:
        for positive in result['positives']:
            print(f"  {positive}")
    else:
        print("  No notable positive factors identified")

    print(f"\n{'HIGHWAY DISTANCES:':^70}")
    print("-"*70)
    for highway, dist in sorted(result['highway_distances'].items(), key=lambda x: x[1]):
        print(f"  {highway}: {dist} miles")

    print(f"\n{'METRO DISTANCES:':^70}")
    print("-"*70)
    for station, dist in sorted(result['metro_distances'].items(), key=lambda x: x[1]):
        print(f"  {station}: {dist} miles")

    print(f"\n{'OVERALL ASSESSMENT:':^70}")
    print("-"*70)
    print(f"  {result['overall_assessment']}")
    print("\n" + "="*70)
