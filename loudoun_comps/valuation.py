#!/usr/bin/env python3
"""
Property valuation engine using comparable sales analysis.
"""

from typing import Dict, List, Optional
import numpy as np
from datetime import datetime
import logging

from database import SalesDatabase
from market_analysis import MarketAnalyzer
from comp_finder import ComparableFinder

logger = logging.getLogger(__name__)


class PropertyValuator:
    """Main property valuation engine."""

    def __init__(self, db_path="loudoun_sales.db"):
        """
        Initialize the valuator.

        Args:
            db_path: Path to SQLite database
        """
        self.db = SalesDatabase(db_path)
        self.db.connect()
        self.analyzer = MarketAnalyzer(self.db)
        self.finder = ComparableFinder(self.db)

    def close(self):
        """Close database connection."""
        self.db.close()

    def estimate_property_value(
        self,
        subject_property: Dict,
        max_comps: int = 10
    ) -> Optional[Dict]:
        """
        Estimate property value using comparable sales analysis.

        Args:
            subject_property: Dict with property details:
                Required: address, latitude, longitude, sqft, property_type, zip_code
                Optional: bedrooms, bathrooms, year_built, lot_size_acres, has_pool, has_garage

        Returns:
            Dictionary with valuation results or None if insufficient data
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Valuing Property: {subject_property.get('address', 'Unknown')}")
        logger.info(f"{'='*60}")

        # Validate required fields
        required = ['address', 'latitude', 'longitude', 'sqft', 'property_type', 'zip_code']
        for field in required:
            if field not in subject_property or subject_property[field] is None:
                logger.error(f"Missing required field: {field}")
                return None

        # Step 1: Calculate market factors
        market_factors = self.analyzer.calculate_market_adjustments(
            subject_property['zip_code']
        )

        if not market_factors:
            logger.error("Could not calculate market factors - insufficient data")
            return None

        # Step 2: Find comparable sales
        comps = self.finder.find_comparable_sales(
            subject_property,
            max_results=max_comps
        )

        if not comps:
            logger.error("No comparable sales found")
            return None

        if len(comps) < 3:
            logger.warning(f"Only found {len(comps)} comps - results may be less reliable")

        # Step 3: Adjust each comp and build results
        adjusted_comps = []

        for comp in comps:
            adjusted_price, adjustments = self.finder.adjust_comp_for_differences(
                comp, subject_property, market_factors
            )

            comp_result = {
                'address': comp['address'],
                'sale_price': comp['sale_price'],
                'sale_date': str(comp['sale_date']).split()[0],
                'adjusted_price': adjusted_price,
                'similarity_score': round(comp['similarity_score'], 1),
                'distance_miles': comp['distance_miles'],
                'sqft': comp['sqft'],
                'bedrooms': comp['bedrooms'],
                'bathrooms': comp['bathrooms'],
                'adjustments': adjustments
            }

            adjusted_comps.append(comp_result)

        # Step 4: Calculate weighted average value
        estimated_value, confidence_range = self._calculate_weighted_estimate(
            adjusted_comps
        )

        # Step 5: Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            adjusted_comps,
            market_factors
        )

        # Build final result
        result = {
            'address': subject_property['address'],
            'estimated_value': estimated_value,
            'confidence_range': confidence_range,
            'confidence_score': confidence_score,
            'comps_used': adjusted_comps,
            'market_factors': market_factors
        }

        self._log_valuation_summary(result)

        return result

    def _calculate_weighted_estimate(
        self,
        adjusted_comps: List[Dict]
    ) -> tuple:
        """
        Calculate weighted average estimate based on similarity scores.

        Args:
            adjusted_comps: List of adjusted comparable sales

        Returns:
            Tuple of (estimated_value, (low_range, high_range))
        """
        # Extract adjusted prices and weights
        prices = np.array([comp['adjusted_price'] for comp in adjusted_comps])
        weights = np.array([comp['similarity_score'] for comp in adjusted_comps])

        # Normalize weights
        weights = weights / weights.sum()

        # Weighted average
        weighted_avg = int(np.average(prices, weights=weights))

        # Confidence range (based on standard deviation)
        std_dev = int(np.std(prices))
        low_range = int(weighted_avg - std_dev)
        high_range = int(weighted_avg + std_dev)

        return weighted_avg, (low_range, high_range)

    def _calculate_confidence_score(
        self,
        adjusted_comps: List[Dict],
        market_factors: Dict
    ) -> int:
        """
        Calculate confidence score (0-100) for the valuation.

        Higher score = more confident in the estimate
        """
        score = 100

        # Penalty for few comps
        num_comps = len(adjusted_comps)
        if num_comps < 5:
            score -= (5 - num_comps) * 5  # -5 points per missing comp

        # Penalty for low similarity scores
        avg_similarity = np.mean([c['similarity_score'] for c in adjusted_comps])
        if avg_similarity < 70:
            score -= (70 - avg_similarity) * 0.5

        # Penalty for high price variance
        prices = [c['adjusted_price'] for c in adjusted_comps]
        coef_variation = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0.5
        if coef_variation > 0.15:  # More than 15% variation
            score -= (coef_variation - 0.15) * 100

        # Penalty for old comps
        months_old = []
        for comp in adjusted_comps:
            sale_date = datetime.strptime(comp['sale_date'], '%Y-%m-%d')
            months_old.append((datetime.now() - sale_date).days / 30.44)

        avg_months_old = np.mean(months_old)
        if avg_months_old > 3:
            score -= (avg_months_old - 3) * 2  # -2 points per month over 3

        # Bonus for large sample size in market factors
        if market_factors.get('sample_size', 0) > 50:
            score += 5

        return int(max(0, min(score, 100)))

    def _log_valuation_summary(self, result: Dict):
        """Log a summary of the valuation results."""
        logger.info(f"\n{'='*60}")
        logger.info("VALUATION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Estimated Value: ${result['estimated_value']:,}")
        logger.info(f"Confidence Range: ${result['confidence_range'][0]:,} - ${result['confidence_range'][1]:,}")
        logger.info(f"Confidence Score: {result['confidence_score']}/100")
        logger.info(f"Comparables Used: {len(result['comps_used'])}")
        logger.info(f"\nTop 3 Comparables:")

        for i, comp in enumerate(result['comps_used'][:3], 1):
            logger.info(f"\n  {i}. {comp['address']}")
            logger.info(f"     Sale Price: ${comp['sale_price']:,}")
            logger.info(f"     Adjusted:   ${comp['adjusted_price']:,}")
            logger.info(f"     Similarity: {comp['similarity_score']}/100")
            logger.info(f"     Distance:   {comp['distance_miles']} miles")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def estimate_property_value(subject_property: Dict, db_path="loudoun_sales.db") -> Optional[Dict]:
    """
    Convenience function to estimate property value.

    Args:
        subject_property: Property details dictionary
        db_path: Path to database

    Returns:
        Valuation result dictionary
    """
    with PropertyValuator(db_path) as valuator:
        return valuator.estimate_property_value(subject_property)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Property Valuation module loaded successfully")
