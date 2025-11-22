"""
Development Pressure Analyzer for Loudoun County

Analyzes development activity and pressure including:
- Rezoning activity
- Building permits (residential & commercial)
- Land sales
- Property appreciation
- Proximity to development activity

Calculates a Development Pressure Score (0-100) to indicate
how much development pressure exists in an area.

Author: NewCo Real Estate Intelligence
Date: November 2024
"""

import math
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DevelopmentActivity:
    """Single development activity record"""
    activity_type: str  # Rezoning/Permit/Land Sale
    description: str
    address: str
    distance: float  # miles from subject property
    lat: float
    lon: float
    date: str
    value: Optional[float] = None  # dollar value if applicable
    sqft: Optional[int] = None  # square footage if applicable


class DevelopmentPressureAnalyzer:
    """Analyzes development pressure for properties"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize analyzer

        Args:
            db_path: Path to development database (optional - will use mock data if not provided)
        """
        self.db_path = db_path
        self.use_mock_data = db_path is None

    def calculate_development_pressure(self, lat: float, lon: float) -> Dict:
        """
        Calculate development pressure score and details

        Args:
            lat: Property latitude
            lon: Property longitude

        Returns:
            Dictionary with pressure score, classification, and activity details
        """
        # Get nearby development activities
        activities = self._get_nearby_activities(lat, lon)

        # Organize by distance zones
        zone_0_1 = [a for a in activities if a.distance <= 1.0]
        zone_1_3 = [a for a in activities if 1.0 < a.distance <= 3.0]
        zone_3_5 = [a for a in activities if 3.0 < a.distance <= 5.0]

        # Calculate component scores
        rezoning_score = self._calculate_rezoning_score(activities)
        permit_score = self._calculate_permit_score(activities)
        land_sale_score = self._calculate_land_sale_score(activities)
        appreciation_score = self._calculate_appreciation_score(activities)
        proximity_score = self._calculate_proximity_score(zone_0_1, zone_1_3, zone_3_5)

        # Calculate weighted overall pressure score
        pressure_score = self._calculate_overall_pressure(
            rezoning_score, permit_score, land_sale_score,
            appreciation_score, proximity_score
        )

        # Classify pressure level
        classification = self._classify_pressure(pressure_score)

        # Generate interpretation
        interpretation = self._generate_interpretation(
            pressure_score, classification, zone_0_1, zone_1_3, zone_3_5
        )

        return {
            'pressure_score': round(pressure_score, 1),
            'classification': classification,
            'interpretation': interpretation,
            'components': {
                'rezoning_score': round(rezoning_score, 1),
                'permit_score': round(permit_score, 1),
                'land_sale_score': round(land_sale_score, 1),
                'appreciation_score': round(appreciation_score, 1),
                'proximity_score': round(proximity_score, 1)
            },
            'component_weights': {
                'rezoning': 30,
                'permits': 25,
                'land_sales': 20,
                'appreciation': 15,
                'proximity': 10
            },
            'activity_counts': {
                'zone_0_1_miles': len(zone_0_1),
                'zone_1_3_miles': len(zone_1_3),
                'zone_3_5_miles': len(zone_3_5),
                'total': len(activities)
            },
            'zone_0_1': [self._activity_to_dict(a) for a in zone_0_1[:10]],  # Limit to 10
            'zone_1_3': [self._activity_to_dict(a) for a in zone_1_3[:10]],
            'zone_3_5': [self._activity_to_dict(a) for a in zone_3_5[:10]],
            'all_activities': [self._activity_to_dict(a) for a in activities]
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

    def _get_nearby_activities(self, lat: float, lon: float,
                               radius_miles: float = 5.0) -> List[DevelopmentActivity]:
        """Get development activities within radius"""
        if self.use_mock_data:
            return self._generate_mock_activities(lat, lon, radius_miles)
        else:
            # TODO: Query actual database
            return self._generate_mock_activities(lat, lon, radius_miles)

    def _generate_mock_activities(self, lat: float, lon: float,
                                  radius_miles: float) -> List[DevelopmentActivity]:
        """Generate mock development activities for demo purposes"""
        activities = []

        # Generate some mock permits
        permit_types = [
            ("Residential Building Permit", "New Single Family Home", 4500, 650000),
            ("Residential Building Permit", "New Townhome Development", 2200, 380000),
            ("Commercial Building Permit", "Data Center Construction", 125000, 45000000),
            ("Commercial Building Permit", "Retail Shopping Center", 35000, 8500000),
            ("Residential Addition", "Home Addition/Renovation", 800, 125000),
        ]

        # Generate 15-25 mock activities
        num_activities = random.randint(15, 25)

        for i in range(num_activities):
            # Random location within radius
            # Simple random offset (not perfect distribution but good enough for demo)
            offset_miles = random.uniform(0.1, radius_miles)
            angle = random.uniform(0, 2 * math.pi)

            # Convert miles to degrees (approximate)
            offset_lat = (offset_miles / 69.0) * math.cos(angle)
            offset_lon = (offset_miles / 69.0) * math.sin(angle)

            activity_lat = lat + offset_lat
            activity_lon = lon + offset_lon

            distance = self._calculate_distance_miles(lat, lon, activity_lat, activity_lon)

            # Random permit type
            ptype, desc, sqft, value = random.choice(permit_types)

            # Random recent date
            days_ago = random.randint(1, 365)
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            activity = DevelopmentActivity(
                activity_type="Building Permit",
                description=desc,
                address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Commerce'])} {random.choice(['St', 'Dr', 'Blvd', 'Way'])}",
                distance=distance,
                lat=activity_lat,
                lon=activity_lon,
                date=date,
                value=value,
                sqft=sqft
            )
            activities.append(activity)

        # Add a few rezoning activities
        for i in range(random.randint(2, 5)):
            offset_miles = random.uniform(0.5, radius_miles)
            angle = random.uniform(0, 2 * math.pi)

            offset_lat = (offset_miles / 69.0) * math.cos(angle)
            offset_lon = (offset_miles / 69.0) * math.sin(angle)

            activity_lat = lat + offset_lat
            activity_lon = lon + offset_lon

            distance = self._calculate_distance_miles(lat, lon, activity_lat, activity_lon)

            days_ago = random.randint(30, 730)
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            activity = DevelopmentActivity(
                activity_type="Rezoning",
                description=random.choice([
                    "Rezoning from Residential to Mixed Use",
                    "Rezoning for Planned Development",
                    "Rezoning to Commercial"
                ]),
                address=f"{random.randint(100, 9999)} {random.choice(['Route 7', 'Route 28', 'Sycolin', 'Waxpool'])} Rd",
                distance=distance,
                lat=activity_lat,
                lon=activity_lon,
                date=date
            )
            activities.append(activity)

        # Sort by distance
        activities.sort(key=lambda a: a.distance)

        return activities

    def _calculate_rezoning_score(self, activities: List[DevelopmentActivity]) -> float:
        """Calculate rezoning activity score (0-100)"""
        rezoning_activities = [a for a in activities if a.activity_type == "Rezoning"]

        # Weight by recency and proximity
        score = 0
        for activity in rezoning_activities:
            # Distance weight (closer = higher impact)
            dist_weight = max(0, 100 - (activity.distance * 20))

            # Recency weight (more recent = higher impact)
            try:
                days_ago = (datetime.now() - datetime.strptime(activity.date, "%Y-%m-%d")).days
                recency_weight = max(0, 100 - (days_ago / 10))
            except:
                recency_weight = 50

            score += (dist_weight + recency_weight) / 2

        # Normalize to 0-100
        return min(100, score / 2)

    def _calculate_permit_score(self, activities: List[DevelopmentActivity]) -> float:
        """Calculate building permit activity score (0-100)"""
        permit_activities = [a for a in activities if a.activity_type == "Building Permit"]

        # Count recent permits within different zones
        recent_permits = [a for a in permit_activities if self._is_recent(a.date, days=365)]

        if len(recent_permits) == 0:
            return 0

        # Score based on count and proximity
        close_permits = len([a for a in recent_permits if a.distance <= 1.0])
        medium_permits = len([a for a in recent_permits if 1.0 < a.distance <= 3.0])
        far_permits = len([a for a in recent_permits if 3.0 < a.distance <= 5.0])

        score = (close_permits * 10) + (medium_permits * 5) + (far_permits * 2)

        return min(100, score)

    def _calculate_land_sale_score(self, activities: List[DevelopmentActivity]) -> float:
        """Calculate land sale activity score (0-100)"""
        # Mock implementation - would use actual land sale data
        land_sales = [a for a in activities if a.activity_type == "Land Sale"]

        # For now, return moderate score
        return random.uniform(20, 50)

    def _calculate_appreciation_score(self, activities: List[DevelopmentActivity]) -> float:
        """Calculate property appreciation score (0-100)"""
        # Mock implementation - would use actual appreciation data
        # Loudoun County has been appreciating rapidly
        return random.uniform(60, 85)

    def _calculate_proximity_score(self, zone_0_1: List, zone_1_3: List,
                                   zone_3_5: List) -> float:
        """Calculate proximity score based on activity concentration"""
        # Weight by zone proximity
        score = (len(zone_0_1) * 15) + (len(zone_1_3) * 5) + (len(zone_3_5) * 2)

        return min(100, score)

    def _calculate_overall_pressure(self, rezoning: float, permits: float,
                                    land_sales: float, appreciation: float,
                                    proximity: float) -> float:
        """Calculate weighted overall pressure score"""
        # Weights from spec
        weights = {
            'rezoning': 0.30,
            'permits': 0.25,
            'land_sales': 0.20,
            'appreciation': 0.15,
            'proximity': 0.10
        }

        overall = (
            rezoning * weights['rezoning'] +
            permits * weights['permits'] +
            land_sales * weights['land_sales'] +
            appreciation * weights['appreciation'] +
            proximity * weights['proximity']
        )

        return min(100, max(0, overall))

    def _classify_pressure(self, score: float) -> str:
        """Classify pressure level"""
        if score >= 75:
            return "Very High"
        elif score >= 60:
            return "High"
        elif score >= 40:
            return "Medium"
        elif score >= 20:
            return "Low"
        else:
            return "Very Low"

    def _generate_interpretation(self, score: float, classification: str,
                                 zone_0_1: List, zone_1_3: List,
                                 zone_3_5: List) -> str:
        """Generate human-readable interpretation"""
        interpretation = f"Development pressure is {classification.lower()} ({score:.0f}/100). "

        total_nearby = len(zone_0_1) + len(zone_1_3)

        if total_nearby == 0:
            interpretation += "The area shows minimal development activity. "
        elif total_nearby < 5:
            interpretation += "The area has light development activity. "
        elif total_nearby < 15:
            interpretation += "The area has moderate development activity. "
        else:
            interpretation += "The area is experiencing significant development activity. "

        if len(zone_0_1) > 5:
            interpretation += f"There are {len(zone_0_1)} permits within 1 mile, indicating active nearby development. "

        return interpretation

    def _is_recent(self, date_str: str, days: int = 365) -> bool:
        """Check if date is within recent period"""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            days_ago = (datetime.now() - date).days
            return days_ago <= days
        except:
            return False

    def _activity_to_dict(self, activity: DevelopmentActivity) -> Dict:
        """Convert activity to dictionary for JSON serialization"""
        return {
            'type': activity.activity_type,
            'description': activity.description,
            'address': activity.address,
            'distance': round(activity.distance, 2),
            'lat': activity.lat,
            'lon': activity.lon,
            'date': activity.date,
            'value': activity.value,
            'sqft': activity.sqft
        }


# Example usage
if __name__ == "__main__":
    analyzer = DevelopmentPressureAnalyzer()

    # Test with 43500 Tuckaway Pl, Leesburg, VA 20176
    result = analyzer.calculate_development_pressure(
        lat=39.0437,
        lon=-77.4875
    )

    print("\n" + "="*70)
    print("DEVELOPMENT PRESSURE ANALYSIS")
    print("="*70)
    print(f"\nOverall Pressure Score: {result['pressure_score']}/100")
    print(f"Classification: {result['classification']}")
    print(f"\nInterpretation: {result['interpretation']}")

    print(f"\n{'COMPONENT SCORES:':^70}")
    print("-"*70)
    for component, score in result['components'].items():
        weight = result['component_weights'][component.replace('_score', '')]
        print(f"  {component.replace('_', ' ').title():30s}: {score:5.1f}/100 (weight: {weight}%)")

    print(f"\n{'ACTIVITY BY DISTANCE:':^70}")
    print("-"*70)
    print(f"  0-1 mile:  {result['activity_counts']['zone_0_1_miles']} activities")
    print(f"  1-3 miles: {result['activity_counts']['zone_1_3_miles']} activities")
    print(f"  3-5 miles: {result['activity_counts']['zone_3_5_miles']} activities")
    print(f"  Total:     {result['activity_counts']['total']} activities")

    print(f"\n{'NEARBY ACTIVITIES (0-1 MILE):':^70}")
    print("-"*70)
    for activity in result['zone_0_1'][:5]:
        print(f"  [{activity['type']}] {activity['description']}")
        print(f"    {activity['address']} - {activity['distance']} mi - {activity['date']}")
        if activity['value']:
            print(f"    Value: ${activity['value']:,}")
        print()

    print("="*70)
