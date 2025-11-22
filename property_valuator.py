"""
Property Valuation Engine for Loudoun County

Provides property valuation estimates using:
- Comparable sales analysis
- Machine learning predictions (when available)
- Market statistics
- Confidence scoring

Author: NewCo Real Estate Intelligence
Date: November 2024
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ComparableSale:
    """Comparable property sale"""
    address: str
    sale_price: float
    sale_date: str
    sqft: int
    bedrooms: int
    bathrooms: float
    year_built: int
    lot_acres: float
    distance: float  # miles from subject
    lat: float
    lon: float
    price_per_sqft: float


class PropertyValuator:
    """Property valuation engine"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize valuator

        Args:
            db_path: Path to sales database (optional - will use mock data if not provided)
        """
        self.db_path = db_path
        self.use_mock_data = db_path is None

    def estimate_property_value(self, property_data: Dict) -> Dict:
        """
        Estimate property value

        Args:
            property_data: Dictionary with property characteristics
                - sqft: Square footage
                - bedrooms: Number of bedrooms
                - bathrooms: Number of bathrooms
                - year_built: Year built
                - lot_size_acres: Lot size in acres
                - address: Property address
                - latitude: Latitude (optional)
                - longitude: Longitude (optional)

        Returns:
            Dictionary with valuation results
        """
        # Get comparable sales
        comps = self._get_comparable_sales(property_data)

        # Calculate estimated value
        estimated_value = self._calculate_value_from_comps(property_data, comps)

        # Calculate confidence score
        confidence = self._calculate_confidence(comps, property_data)

        # Generate valuation range
        low_estimate = int(estimated_value * 0.95)
        high_estimate = int(estimated_value * 1.05)

        # Calculate price per sqft
        price_per_sqft = estimated_value / property_data.get('sqft', 1)

        # Get market statistics
        market_stats = self._get_market_statistics(comps)

        return {
            'estimated_value': int(estimated_value),
            'valuation_range': {
                'low': low_estimate,
                'high': high_estimate
            },
            'price_per_sqft': round(price_per_sqft, 2),
            'confidence_score': confidence,
            'confidence_level': self._get_confidence_level(confidence),
            'comparables': [self._comp_to_dict(c) for c in comps],
            'comp_count': len(comps),
            'market_statistics': market_stats,
            'methodology': 'Comparable Sales Analysis',
            'analysis_date': '2024-11-22'
        }

    def _get_comparable_sales(self, property_data: Dict) -> List[ComparableSale]:
        """Get comparable sales"""
        if self.use_mock_data:
            return self._generate_mock_comparables(property_data)
        else:
            # TODO: Query actual sales database
            return self._generate_mock_comparables(property_data)

    def _generate_mock_comparables(self, property_data: Dict) -> List[ComparableSale]:
        """Generate mock comparable sales for demo"""
        comps = []

        # Get property characteristics
        target_sqft = property_data.get('sqft', 3200)
        target_beds = property_data.get('bedrooms', 4)
        target_baths = property_data.get('bathrooms', 3.5)
        target_year = property_data.get('year_built', 2015)
        lat = property_data.get('latitude', 39.0437)
        lon = property_data.get('longitude', -77.4875)

        # Generate 5-8 comparable sales
        num_comps = random.randint(5, 8)

        # Base price per sqft for Loudoun County (realistic range)
        base_price_per_sqft = random.uniform(280, 350)

        for i in range(num_comps):
            # Similar sqft (within 20%)
            comp_sqft = int(target_sqft * random.uniform(0.85, 1.15))

            # Similar beds/baths
            comp_beds = target_beds if random.random() > 0.3 else target_beds + random.choice([-1, 1])
            comp_baths = target_baths if random.random() > 0.3 else target_baths + random.choice([-0.5, 0.5])

            # Similar year
            comp_year = target_year + random.randint(-5, 5)

            # Price per sqft with variation
            ppf = base_price_per_sqft * random.uniform(0.92, 1.08)
            sale_price = comp_sqft * ppf

            # Distance
            distance = random.uniform(0.2, 2.5)

            # Random location offset
            offset_lat = (distance / 69.0) * random.uniform(-1, 1)
            offset_lon = (distance / 69.0) * random.uniform(-1, 1)

            comp = ComparableSale(
                address=f"{random.randint(100, 9999)} {random.choice(['Oak', 'Maple', 'Cedar', 'Willow', 'Pine', 'Birch'])} {random.choice(['St', 'Dr', 'Ct', 'Way'])}",
                sale_price=int(sale_price),
                sale_date=f"2024-{random.randint(1, 11):02d}-{random.randint(1, 28):02d}",
                sqft=comp_sqft,
                bedrooms=comp_beds,
                bathrooms=comp_baths,
                year_built=comp_year,
                lot_acres=round(random.uniform(0.2, 0.5), 2),
                distance=round(distance, 2),
                lat=lat + offset_lat,
                lon=lon + offset_lon,
                price_per_sqft=round(ppf, 2)
            )
            comps.append(comp)

        # Sort by distance
        comps.sort(key=lambda c: c.distance)

        return comps

    def _calculate_value_from_comps(self, property_data: Dict,
                                     comps: List[ComparableSale]) -> float:
        """Calculate estimated value from comparables"""
        target_sqft = property_data.get('sqft', 3200)

        # Calculate weighted average price per sqft
        # Weight by distance (closer = more weight)
        total_weight = 0
        weighted_ppf = 0

        for comp in comps:
            # Distance weight (inverse of distance)
            weight = 1.0 / (comp.distance + 0.5)  # Add 0.5 to avoid division by very small numbers
            total_weight += weight
            weighted_ppf += comp.price_per_sqft * weight

        avg_ppf = weighted_ppf / total_weight if total_weight > 0 else 300

        # Calculate estimated value
        estimated_value = target_sqft * avg_ppf

        return estimated_value

    def _calculate_confidence(self, comps: List[ComparableSale],
                              property_data: Dict) -> int:
        """Calculate confidence score (0-100)"""
        confidence = 100

        # Deduct for lack of comps
        if len(comps) < 3:
            confidence -= 20
        elif len(comps) < 5:
            confidence -= 10

        # Deduct for price variance in comps
        if comps:
            prices_per_sqft = [c.price_per_sqft for c in comps]
            avg_ppf = sum(prices_per_sqft) / len(prices_per_sqft)
            variance = sum((p - avg_ppf) ** 2 for p in prices_per_sqft) / len(prices_per_sqft)
            std_dev = variance ** 0.5

            # High variance reduces confidence
            cv = (std_dev / avg_ppf) * 100  # Coefficient of variation
            if cv > 15:
                confidence -= 15
            elif cv > 10:
                confidence -= 10
            elif cv > 5:
                confidence -= 5

        # Deduct if comps are far away
        if comps:
            avg_distance = sum(c.distance for c in comps) / len(comps)
            if avg_distance > 2.0:
                confidence -= 10
            elif avg_distance > 1.5:
                confidence -= 5

        return max(50, min(100, confidence))

    def _get_confidence_level(self, score: int) -> str:
        """Convert confidence score to level"""
        if score >= 90:
            return "Very High"
        elif score >= 75:
            return "High"
        elif score >= 60:
            return "Moderate"
        else:
            return "Low"

    def _get_market_statistics(self, comps: List[ComparableSale]) -> Dict:
        """Calculate market statistics from comparables"""
        if not comps:
            return {}

        prices = [c.sale_price for c in comps]
        ppf_values = [c.price_per_sqft for c in comps]

        return {
            'median_sale_price': int(sorted(prices)[len(prices) // 2]),
            'median_price_per_sqft': round(sorted(ppf_values)[len(ppf_values) // 2], 2),
            'days_on_market_avg': random.randint(15, 45),  # Mock
            'market_trend': random.choice(['Appreciating', 'Stable', 'Cooling']),
            'market_description': 'Active seller\'s market with strong demand in Loudoun County'
        }

    def _comp_to_dict(self, comp: ComparableSale) -> Dict:
        """Convert comparable to dictionary"""
        return {
            'address': comp.address,
            'sale_price': comp.sale_price,
            'sale_date': comp.sale_date,
            'sqft': comp.sqft,
            'bedrooms': comp.bedrooms,
            'bathrooms': comp.bathrooms,
            'year_built': comp.year_built,
            'lot_acres': comp.lot_acres,
            'distance': comp.distance,
            'lat': comp.lat,
            'lon': comp.lon,
            'price_per_sqft': comp.price_per_sqft
        }


# Example usage
if __name__ == "__main__":
    valuator = PropertyValuator()

    # Test property
    property_data = {
        'address': '43500 Tuckaway Pl, Leesburg, VA 20176',
        'sqft': 3200,
        'bedrooms': 4,
        'bathrooms': 3.5,
        'year_built': 2015,
        'lot_size_acres': 0.35,
        'latitude': 39.0437,
        'longitude': -77.4875
    }

    result = valuator.estimate_property_value(property_data)

    print("\n" + "="*70)
    print("PROPERTY VALUATION")
    print("="*70)
    print(f"\nAddress: {property_data['address']}")
    print(f"Property: {property_data['bedrooms']} bed, {property_data['bathrooms']} bath, {property_data['sqft']:,} sqft")
    print(f"\nEstimated Value: ${result['estimated_value']:,}")
    print(f"Valuation Range: ${result['valuation_range']['low']:,} - ${result['valuation_range']['high']:,}")
    print(f"Price per Sqft: ${result['price_per_sqft']}")
    print(f"\nConfidence: {result['confidence_level']} ({result['confidence_score']}%)")
    print(f"Methodology: {result['methodology']}")

    print(f"\n{'COMPARABLE SALES:':^70}")
    print("-"*70)
    for i, comp in enumerate(result['comparables'][:5], 1):
        print(f"\n{i}. {comp['address']}")
        print(f"   Sold: {comp['sale_date']} | Price: ${comp['sale_price']:,} | {comp['sqft']:,} sqft")
        print(f"   ${comp['price_per_sqft']}/sqft | {comp['distance']} mi away")

    print(f"\n{'MARKET STATISTICS:':^70}")
    print("-"*70)
    stats = result['market_statistics']
    print(f"  Median Sale Price: ${stats['median_sale_price']:,}")
    print(f"  Median Price/Sqft: ${stats['median_price_per_sqft']}")
    print(f"  Avg Days on Market: {stats['days_on_market_avg']}")
    print(f"  Market Trend: {stats['market_trend']}")

    print("\n" + "="*70)
