#!/usr/bin/env python3
"""
Comparable sales finder with similarity scoring and adjustments.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)


class ComparableFinder:
    """Find and score comparable property sales."""

    def __init__(self, database):
        """
        Initialize comparable finder.

        Args:
            database: SalesDatabase instance
        """
        self.db = database

    def find_comparable_sales(
        self,
        subject_property: Dict,
        max_results: int = 10,
        max_distance_miles: float = 3.0,
        max_age_months: int = 6,
        size_tolerance: float = 0.30
    ) -> List[Dict]:
        """
        Find comparable sales for a subject property.

        Args:
            subject_property: Dict with property details (lat, lon, sqft, property_type, etc.)
            max_results: Maximum number of comps to return
            max_distance_miles: Maximum distance in miles
            max_age_months: Maximum age of sales in months
            size_tolerance: Size difference tolerance (0.30 = +/-30%)

        Returns:
            List of comparable sales with similarity scores
        """
        logger.info(f"Finding comparables for {subject_property.get('address', 'subject property')}...")

        # Validate subject property
        required_fields = ['latitude', 'longitude', 'sqft', 'property_type']
        for field in required_fields:
            if field not in subject_property or subject_property[field] is None:
                logger.error(f"Missing required field: {field}")
                return []

        # Get all recent sales
        cutoff_date = datetime.now() - timedelta(days=max_age_months * 30)
        self.db.cursor.execute("""
            SELECT * FROM sales
            WHERE sale_date >= ?
            AND property_type = ?
            AND latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND sqft IS NOT NULL
        """, (cutoff_date.strftime('%Y-%m-%d'), subject_property['property_type']))

        all_sales = self.db.cursor.fetchall()
        logger.info(f"Found {len(all_sales)} potential comps in database")

        if not all_sales:
            logger.warning("No potential comparables found")
            return []

        # Score each potential comp
        scored_comps = []
        subject_location = (subject_property['latitude'], subject_property['longitude'])
        subject_sqft = subject_property['sqft']

        for sale in all_sales:
            sale_dict = dict(sale)

            # Calculate distance
            comp_location = (sale_dict['latitude'], sale_dict['longitude'])
            distance_miles = geodesic(subject_location, comp_location).miles

            # Skip if too far
            if distance_miles > max_distance_miles:
                continue

            # Calculate size difference
            comp_sqft = sale_dict['sqft']
            size_diff_pct = abs(comp_sqft - subject_sqft) / subject_sqft

            # Skip if size too different
            if size_diff_pct > size_tolerance:
                continue

            # Calculate similarity score
            score = self._calculate_similarity_score(
                subject_property, sale_dict, distance_miles, size_diff_pct
            )

            sale_dict['similarity_score'] = score
            sale_dict['distance_miles'] = round(distance_miles, 2)
            scored_comps.append(sale_dict)

        # Sort by similarity score (highest first)
        scored_comps.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Return top N
        top_comps = scored_comps[:max_results]
        logger.info(f"✓ Found {len(top_comps)} comparable sales")

        return top_comps

    def _calculate_similarity_score(
        self,
        subject: Dict,
        comp: Dict,
        distance: float,
        size_diff_pct: float
    ) -> float:
        """
        Calculate similarity score (0-100) for a comp.

        Higher score = more similar
        """
        score = 100.0

        # Distance penalty (0-30 points)
        # 0 miles = 0 penalty, 3 miles = 30 penalty
        distance_penalty = min(distance / 3.0 * 30, 30)
        score -= distance_penalty

        # Size difference penalty (0-25 points)
        # 0% diff = 0 penalty, 30% diff = 25 penalty
        size_penalty = size_diff_pct / 0.30 * 25
        score -= size_penalty

        # Age of sale penalty (0-15 points)
        # Recent = 0 penalty, 6 months old = 15 penalty
        sale_date = datetime.strptime(str(comp['sale_date']).split()[0], '%Y-%m-%d')
        months_old = (datetime.now() - sale_date).days / 30.44
        age_penalty = min(months_old / 6.0 * 15, 15)
        score -= age_penalty

        # Bedroom/bathroom match (0-10 points each)
        if 'bedrooms' in subject and subject['bedrooms'] is not None:
            if comp['bedrooms'] != subject['bedrooms']:
                bedroom_diff = abs(comp['bedrooms'] - subject['bedrooms'])
                score -= min(bedroom_diff * 5, 10)

        if 'bathrooms' in subject and subject['bathrooms'] is not None:
            if comp['bathrooms'] != subject['bathrooms']:
                bathroom_diff = abs(comp['bathrooms'] - subject['bathrooms'])
                score -= min(bathroom_diff * 5, 10)

        # Feature match bonuses
        if subject.get('has_pool') == comp.get('has_pool'):
            score += 5

        if subject.get('has_garage') == comp.get('has_garage'):
            score += 5

        return max(0, min(score, 100))

    def adjust_comp_for_differences(
        self,
        comp_sale: Dict,
        subject_property: Dict,
        market_factors: Dict
    ) -> Tuple[int, Dict]:
        """
        Adjust a comp's sale price to account for differences from subject.

        Args:
            comp_sale: Comparable sale record
            subject_property: Subject property details
            market_factors: Market adjustment factors

        Returns:
            Tuple of (adjusted_price, adjustments_dict)
        """
        adjustments = {}
        adjusted_price = comp_sale['sale_price']

        # 1. Time adjustment (market appreciation)
        if 'monthly_appreciation' in market_factors:
            sale_date = datetime.strptime(str(comp_sale['sale_date']).split()[0], '%Y-%m-%d')
            months_diff = (datetime.now() - sale_date).days / 30.44

            time_adjustment = int(adjusted_price * market_factors['monthly_appreciation'] * months_diff)
            adjustments['time'] = time_adjustment
            adjusted_price += time_adjustment

        # 2. Size adjustment
        if 'price_per_sqft' in market_factors and comp_sale['sqft'] and subject_property.get('sqft'):
            sqft_diff = subject_property['sqft'] - comp_sale['sqft']
            size_adjustment = int(sqft_diff * market_factors['price_per_sqft'])
            adjustments['size'] = size_adjustment
            adjusted_price += size_adjustment

        # 3. Bedroom adjustment
        if 'bedroom_value' in market_factors and comp_sale['bedrooms'] and subject_property.get('bedrooms'):
            bedroom_diff = subject_property['bedrooms'] - comp_sale['bedrooms']
            bedroom_adjustment = int(bedroom_diff * market_factors['bedroom_value'])
            adjustments['bedrooms'] = bedroom_adjustment
            adjusted_price += bedroom_adjustment

        # 4. Bathroom adjustment
        if 'bathroom_value' in market_factors and comp_sale['bathrooms'] and subject_property.get('bathrooms'):
            bathroom_diff = subject_property['bathrooms'] - comp_sale['bathrooms']
            bathroom_adjustment = int(bathroom_diff * market_factors['bathroom_value'])
            adjustments['bathrooms'] = bathroom_adjustment
            adjusted_price += bathroom_adjustment

        # 5. Lot size adjustment
        if 'lot_value_per_acre' in market_factors:
            if comp_sale.get('lot_size_acres') and subject_property.get('lot_size_acres'):
                lot_diff = subject_property['lot_size_acres'] - comp_sale['lot_size_acres']
                lot_adjustment = int(lot_diff * market_factors['lot_value_per_acre'])
                adjustments['lot'] = lot_adjustment
                adjusted_price += lot_adjustment

        # 6. Age adjustment
        if 'age_depreciation_rate' in market_factors:
            if comp_sale.get('year_built') and subject_property.get('year_built'):
                age_diff = comp_sale['year_built'] - subject_property['year_built']
                # Positive age_diff means comp is newer, so subject is worth less
                age_adjustment = -int(adjusted_price * market_factors['age_depreciation_rate'] * age_diff)
                adjustments['age'] = age_adjustment
                adjusted_price += age_adjustment

        # 7. Pool adjustment
        if 'pool_premium' in market_factors:
            comp_has_pool = comp_sale.get('has_pool', 0)
            subject_has_pool = subject_property.get('has_pool', 0)

            if subject_has_pool and not comp_has_pool:
                adjustments['pool'] = int(market_factors['pool_premium'])
                adjusted_price += adjustments['pool']
            elif not subject_has_pool and comp_has_pool:
                adjustments['pool'] = -int(market_factors['pool_premium'])
                adjusted_price += adjustments['pool']

        # 8. Garage adjustment
        if 'garage_premium' in market_factors:
            comp_has_garage = comp_sale.get('has_garage', 0)
            subject_has_garage = subject_property.get('has_garage', 0)

            if subject_has_garage and not comp_has_garage:
                adjustments['garage'] = int(market_factors['garage_premium'])
                adjusted_price += adjustments['garage']
            elif not subject_has_garage and comp_has_garage:
                adjustments['garage'] = -int(market_factors['garage_premium'])
                adjusted_price += adjustments['garage']

        return int(adjusted_price), adjustments


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Comparable Finder module loaded successfully")
