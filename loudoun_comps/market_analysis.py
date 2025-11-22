#!/usr/bin/env python3
"""
Market factor calculation and analysis for property valuations.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Analyze property sales to calculate market adjustment factors."""

    def __init__(self, database):
        """
        Initialize market analyzer.

        Args:
            database: SalesDatabase instance
        """
        self.db = database

    def calculate_market_adjustments(self, zip_code: str, min_sales=20) -> Optional[Dict]:
        """
        Calculate market adjustment factors for a ZIP code.

        Args:
            zip_code: ZIP code to analyze
            min_sales: Minimum number of sales required

        Returns:
            Dictionary of market factors or None if insufficient data
        """
        logger.info(f"Calculating market factors for ZIP {zip_code}...")

        # Check for cached factors first
        cached = self.db.get_market_factors(zip_code, max_age_days=30)
        if cached:
            logger.info("✓ Using cached market factors (less than 30 days old)")
            return {
                'price_per_sqft': cached['price_per_sqft'],
                'bedroom_value': cached['bedroom_value'],
                'bathroom_value': cached['bathroom_value'],
                'lot_value_per_acre': cached['lot_value_per_acre'],
                'age_depreciation_rate': cached['age_depreciation_rate'],
                'pool_premium': cached['pool_premium'],
                'garage_premium': cached['garage_premium'],
                'monthly_appreciation': cached['monthly_appreciation'],
                'sample_size': cached['sample_size'],
                'calculation_date': cached['calculation_date']
            }

        # Get recent sales (last 12 months)
        sales = self.db.get_sales_by_zip(zip_code, days=365)

        if len(sales) < min_sales:
            logger.warning(f"Insufficient data: only {len(sales)} sales (need {min_sales})")
            return None

        # Convert to DataFrame
        df = pd.DataFrame([dict(sale) for sale in sales])

        # Clean data
        df = df.dropna(subset=['sale_price', 'sqft', 'bedrooms', 'bathrooms'])
        df = df[df['sale_price'] > 0]
        df = df[df['sqft'] > 0]

        logger.info(f"Analyzing {len(df)} sales records...")

        # Calculate basic price per sqft
        price_per_sqft = self._calculate_price_per_sqft(df)

        # Calculate bedroom value using regression
        bedroom_value = self._calculate_bedroom_value(df)

        # Calculate bathroom value
        bathroom_value = self._calculate_bathroom_value(df)

        # Calculate lot value per acre
        lot_value_per_acre = self._calculate_lot_value(df)

        # Calculate age depreciation rate
        age_depreciation_rate = self._calculate_age_depreciation(df)

        # Calculate feature premiums
        pool_premium = self._calculate_pool_premium(df)
        garage_premium = self._calculate_garage_premium(df)

        # Calculate monthly appreciation rate
        monthly_appreciation = self._calculate_appreciation_rate(df)

        factors = {
            'price_per_sqft': round(price_per_sqft, 2),
            'bedroom_value': round(bedroom_value, 2),
            'bathroom_value': round(bathroom_value, 2),
            'lot_value_per_acre': round(lot_value_per_acre, 2),
            'age_depreciation_rate': round(age_depreciation_rate, 4),
            'pool_premium': round(pool_premium, 2),
            'garage_premium': round(garage_premium, 2),
            'monthly_appreciation': round(monthly_appreciation, 4),
            'sample_size': len(df)
        }

        # Cache the factors
        self.db.save_market_factors(zip_code, factors, len(df))

        logger.info("✓ Market factors calculated successfully")
        return factors

    def _calculate_price_per_sqft(self, df: pd.DataFrame) -> float:
        """Calculate median price per square foot."""
        df['price_per_sqft'] = df['sale_price'] / df['sqft']
        median_ppsf = df['price_per_sqft'].median()
        logger.debug(f"  Price/sqft: ${median_ppsf:.2f} (median)")
        return median_ppsf

    def _calculate_bedroom_value(self, df: pd.DataFrame) -> float:
        """Calculate average value per bedroom using regression."""
        try:
            # Prepare features
            X = df[['sqft', 'bedrooms']].values
            y = df['sale_price'].values

            # Fit regression model
            model = LinearRegression()
            model.fit(X, y)

            # Bedroom coefficient is the value per bedroom
            bedroom_coef = model.coef_[1]
            logger.debug(f"  Bedroom value: ${bedroom_coef:,.0f}")

            return max(0, bedroom_coef)  # Ensure non-negative

        except Exception as e:
            logger.warning(f"Could not calculate bedroom value: {e}")
            # Fallback: simple average
            avg_price_diff = df.groupby('bedrooms')['sale_price'].mean().diff().mean()
            return max(0, avg_price_diff) if not np.isnan(avg_price_diff) else 15000

    def _calculate_bathroom_value(self, df: pd.DataFrame) -> float:
        """Calculate average value per bathroom."""
        try:
            # Prepare features
            X = df[['sqft', 'bathrooms']].values
            y = df['sale_price'].values

            # Fit regression model
            model = LinearRegression()
            model.fit(X, y)

            # Bathroom coefficient
            bathroom_coef = model.coef_[1]
            logger.debug(f"  Bathroom value: ${bathroom_coef:,.0f}")

            return max(0, bathroom_coef)

        except Exception as e:
            logger.warning(f"Could not calculate bathroom value: {e}")
            # Fallback
            avg_price_diff = df.groupby('bathrooms')['sale_price'].mean().diff().mean()
            return max(0, avg_price_diff) if not np.isnan(avg_price_diff) else 10000

    def _calculate_lot_value(self, df: pd.DataFrame) -> float:
        """Calculate value per acre of lot size."""
        df_lot = df[df['lot_size_acres'].notna() & (df['lot_size_acres'] > 0)]

        if len(df_lot) < 10:
            logger.debug("  Lot value: Insufficient data")
            return 50000  # Default assumption

        try:
            # Regression with lot size
            X = df_lot[['sqft', 'lot_size_acres']].values
            y = df_lot['sale_price'].values

            model = LinearRegression()
            model.fit(X, y)

            lot_coef = model.coef_[1]
            logger.debug(f"  Lot value/acre: ${lot_coef:,.0f}")

            return max(0, lot_coef)

        except Exception as e:
            logger.warning(f"Could not calculate lot value: {e}")
            return 50000

    def _calculate_age_depreciation(self, df: pd.DataFrame) -> float:
        """Calculate annual depreciation rate based on property age."""
        current_year = datetime.now().year
        df_age = df[df['year_built'].notna() & (df['year_built'] > 1800)]

        if len(df_age) < 10:
            logger.debug("  Age depreciation: Insufficient data")
            return 0.005  # 0.5% per year default

        try:
            df_age['age'] = current_year - df_age['year_built']

            # Regression: price vs age (controlling for size)
            X = df_age[['sqft', 'age']].values
            y = df_age['sale_price'].values

            model = LinearRegression()
            model.fit(X, y)

            age_coef = model.coef_[1]
            median_price = df_age['sale_price'].median()

            # Convert to annual depreciation rate
            depreciation_rate = abs(age_coef) / median_price if median_price > 0 else 0.005
            logger.debug(f"  Age depreciation: {depreciation_rate*100:.2f}% per year")

            return min(depreciation_rate, 0.02)  # Cap at 2% per year

        except Exception as e:
            logger.warning(f"Could not calculate age depreciation: {e}")
            return 0.005

    def _calculate_pool_premium(self, df: pd.DataFrame) -> float:
        """Calculate premium for having a pool."""
        df_pool = df[df['has_pool'].notna()]

        if len(df_pool) < 10:
            logger.debug("  Pool premium: Insufficient data")
            return 15000  # Default assumption

        try:
            with_pool = df_pool[df_pool['has_pool'] == 1]['sale_price'].median()
            without_pool = df_pool[df_pool['has_pool'] == 0]['sale_price'].median()

            premium = with_pool - without_pool
            logger.debug(f"  Pool premium: ${premium:,.0f}")

            return max(0, premium)

        except Exception as e:
            logger.warning(f"Could not calculate pool premium: {e}")
            return 15000

    def _calculate_garage_premium(self, df: pd.DataFrame) -> float:
        """Calculate premium for having a garage."""
        df_garage = df[df['has_garage'].notna()]

        if len(df_garage) < 10:
            logger.debug("  Garage premium: Insufficient data")
            return 10000  # Default assumption

        try:
            with_garage = df_garage[df_garage['has_garage'] == 1]['sale_price'].median()
            without_garage = df_garage[df_garage['has_garage'] == 0]['sale_price'].median()

            premium = with_garage - without_garage
            logger.debug(f"  Garage premium: ${premium:,.0f}")

            return max(0, premium)

        except Exception as e:
            logger.warning(f"Could not calculate garage premium: {e}")
            return 10000

    def _calculate_appreciation_rate(self, df: pd.DataFrame) -> float:
        """Calculate monthly market appreciation rate."""
        try:
            # Convert sale_date to datetime
            df['sale_date_dt'] = pd.to_datetime(df['sale_date'])

            # Calculate months ago from most recent sale
            max_date = df['sale_date_dt'].max()
            df['months_ago'] = ((max_date - df['sale_date_dt']).dt.days / 30.44).astype(int)

            # Regression: price vs months_ago (controlling for size)
            X = df[['sqft', 'months_ago']].values
            y = df['sale_price'].values

            model = LinearRegression()
            model.fit(X, y)

            months_coef = model.coef_[1]
            median_price = df['sale_price'].median()

            # Convert to monthly appreciation rate
            # Negative coef means older sales were cheaper (appreciation)
            appreciation_rate = -months_coef / median_price if median_price > 0 else 0.008

            logger.debug(f"  Monthly appreciation: {appreciation_rate*100:.2f}%")

            # Cap at reasonable bounds (-1% to +2% per month)
            return max(-0.01, min(appreciation_rate, 0.02))

        except Exception as e:
            logger.warning(f"Could not calculate appreciation rate: {e}")
            return 0.008  # Default 0.8% per month


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Market Analysis module loaded successfully")
