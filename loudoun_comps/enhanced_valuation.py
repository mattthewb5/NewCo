#!/usr/bin/env python3
"""
Enhanced Valuation Engine for Loudoun County Property Sales

Advanced analytics including machine learning, clustering, time-series analysis,
and multi-method valuation comparison.

Author: Property Valuation System
Version: 1.0.0
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
import pickle
import warnings
warnings.filterwarnings('ignore')

# Machine Learning
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.cluster import KMeans
from sklearn.neighbors import LocalOutlierFactor

# Statistics
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLPricePredictor:
    """Machine learning-based price predictor with multiple models."""

    def __init__(self):
        """Initialize predictor with multiple models."""
        self.models = {
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        self.scaler = StandardScaler()
        self.best_model_name = None
        self.best_model = None
        self.feature_importance = None
        self.training_metrics = {}

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for training.

        Args:
            df: Sales dataframe

        Returns:
            Tuple of (features_df, target_series)
        """
        # Select numeric features
        feature_cols = ['sqft', 'bedrooms', 'bathrooms', 'lot_size_acres', 'year_built']

        # Add property age if not present
        if 'property_age' not in df.columns and 'year_built' in df.columns:
            df['property_age'] = datetime.now().year - df['year_built']

        # ZIP code as categorical (one-hot encoding)
        if 'zip_code' in df.columns:
            zip_dummies = pd.get_dummies(df['zip_code'], prefix='zip')
            df = pd.concat([df, zip_dummies], axis=1)
            feature_cols.extend(zip_dummies.columns.tolist())

        # Filter to valid records
        df_clean = df[feature_cols + ['sale_price']].dropna()

        X = df_clean[feature_cols]
        y = df_clean['sale_price']

        logger.info(f"Prepared {len(X)} training samples with {len(feature_cols)} features")

        return X, y

    def train_models(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Train all models and select the best.

        Args:
            X: Features
            y: Target (sale prices)

        Returns:
            Training metrics dictionary
        """
        logger.info("Training machine learning models...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train and evaluate each model
        results = {}

        for name, model in self.models.items():
            logger.info(f"Training {name}...")

            # Train
            if name == 'linear':
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

            # Evaluate
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            # Cross-validation
            if name == 'linear':
                cv_scores = cross_val_score(
                    model, X_train_scaled, y_train, cv=5, scoring='r2'
                )
            else:
                cv_scores = cross_val_score(
                    model, X_train, y_train, cv=5, scoring='r2'
                )

            results[name] = {
                'mae': mae,
                'r2': r2,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }

            logger.info(f"  {name}: MAE=${mae:,.0f}, R²={r2:.3f}, CV R²={cv_scores.mean():.3f}±{cv_scores.std():.3f}")

        # Select best model (by R²)
        self.best_model_name = max(results, key=lambda x: results[x]['r2'])
        self.best_model = self.models[self.best_model_name]
        self.training_metrics = results

        logger.info(f"Best model: {self.best_model_name}")

        # Feature importance (for tree-based models)
        if self.best_model_name in ['random_forest', 'gradient_boost']:
            self.feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': self.best_model.feature_importances_
            }).sort_values('importance', ascending=False)

            logger.info("\nTop 5 important features:")
            for _, row in self.feature_importance.head().iterrows():
                logger.info(f"  {row['feature']}: {row['importance']:.4f}")

        return results

    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict prices with confidence intervals.

        Args:
            X: Features

        Returns:
            Tuple of (predictions, confidence_intervals)
        """
        if self.best_model is None:
            raise ValueError("Model not trained. Call train_models() first.")

        # Scale if linear model
        if self.best_model_name == 'linear':
            X_scaled = self.scaler.transform(X)
            predictions = self.best_model.predict(X_scaled)
        else:
            predictions = self.best_model.predict(X)

        # Estimate confidence intervals (using training MAE)
        mae = self.training_metrics[self.best_model_name]['mae']
        confidence_intervals = np.column_stack([
            predictions - 2*mae,  # Lower bound (95% CI)
            predictions + 2*mae   # Upper bound (95% CI)
        ])

        return predictions, confidence_intervals

    def save_model(self, path: str = "price_model.pkl"):
        """Save trained model to file."""
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'best_model_name': self.best_model_name,
            'feature_importance': self.feature_importance,
            'training_metrics': self.training_metrics
        }

        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {path}")

    @classmethod
    def load_model(cls, path: str = "price_model.pkl"):
        """Load trained model from file."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        predictor = cls()
        predictor.models = model_data['models']
        predictor.scaler = model_data['scaler']
        predictor.best_model_name = model_data['best_model_name']
        predictor.best_model = predictor.models[predictor.best_model_name]
        predictor.feature_importance = model_data['feature_importance']
        predictor.training_metrics = model_data['training_metrics']

        logger.info(f"Model loaded from {path}")
        return predictor


class OutlierDetector:
    """Advanced outlier detection using multiple methods."""

    @staticmethod
    def detect_zscore_outliers(
        df: pd.DataFrame,
        column: str,
        threshold: float = 3.0
    ) -> List[int]:
        """Detect outliers using z-score method."""
        df_clean = df[[column, 'id']].dropna()

        if len(df_clean) == 0:
            return []

        z_scores = np.abs(stats.zscore(df_clean[column]))
        outlier_mask = z_scores > threshold

        outlier_ids = df_clean.loc[outlier_mask, 'id'].tolist()

        logger.info(f"Z-score method: {len(outlier_ids)} outliers in {column}")
        return outlier_ids

    @staticmethod
    def detect_iqr_outliers(
        df: pd.DataFrame,
        column: str,
        multiplier: float = 1.5
    ) -> List[int]:
        """Detect outliers using IQR method."""
        df_clean = df[[column, 'id']].dropna()

        if len(df_clean) == 0:
            return []

        values = df_clean[column]

        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR

        outlier_mask = (values < lower_bound) | (values > upper_bound)

        outlier_ids = df_clean.loc[outlier_mask, 'id'].tolist()

        logger.info(f"IQR method: {len(outlier_ids)} outliers in {column}")
        return outlier_ids

    @staticmethod
    def detect_local_outliers(
        df: pd.DataFrame,
        features: List[str],
        contamination: float = 0.1
    ) -> List[int]:
        """
        Detect contextual outliers using Local Outlier Factor.

        Args:
            df: Dataframe
            features: List of feature columns
            contamination: Expected proportion of outliers

        Returns:
            List of outlier IDs
        """
        df_clean = df[features + ['id']].dropna()

        if len(df_clean) < 20:
            logger.warning("Insufficient data for LOF detection")
            return []

        X = df_clean[features].values

        lof = LocalOutlierFactor(n_neighbors=20, contamination=contamination)
        outlier_labels = lof.fit_predict(X)

        outlier_ids = df_clean.loc[outlier_labels == -1, 'id'].tolist()

        logger.info(f"LOF method: {len(outlier_ids)} contextual outliers")
        return outlier_ids


class TimeSeriesAnalyzer:
    """Time-series analysis for market trends."""

    @staticmethod
    def calculate_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate monthly price trends."""
        if 'sale_date' not in df.columns:
            return pd.DataFrame()

        df['sale_date'] = pd.to_datetime(df['sale_date'])
        df['year_month'] = df['sale_date'].dt.to_period('M')

        monthly = df.groupby('year_month').agg({
            'sale_price': ['count', 'median', 'mean', 'std'],
            'price_per_sqft': ['median', 'mean']
        }).round(2)

        monthly.columns = ['_'.join(col).strip() for col in monthly.columns.values]
        monthly = monthly.reset_index()
        monthly['year_month'] = monthly['year_month'].astype(str)

        return monthly

    @staticmethod
    def calculate_appreciation_rate(df: pd.DataFrame, zip_code: str = None) -> Dict:
        """
        Calculate market appreciation rate.

        Args:
            df: Sales dataframe
            zip_code: Optional ZIP code filter

        Returns:
            Dictionary with appreciation metrics
        """
        if zip_code:
            df = df[df['zip_code'] == zip_code]

        df = df.copy()
        df['sale_date'] = pd.to_datetime(df['sale_date'])

        # Sort by date
        df = df.sort_values('sale_date')

        # Calculate months since first sale
        min_date = df['sale_date'].min()
        df['months_since_start'] = ((df['sale_date'] - min_date).dt.days / 30.44)

        # Linear regression: price vs time
        X = df[['months_since_start']].values
        y = df['sale_price'].values

        if len(df) < 10:
            return {'monthly_rate': 0, 'annual_rate': 0}

        model = LinearRegression()
        model.fit(X, y)

        # Monthly appreciation in dollars
        monthly_dollars = model.coef_[0]

        # Convert to percentage
        median_price = df['sale_price'].median()
        monthly_rate = (monthly_dollars / median_price) if median_price > 0 else 0
        annual_rate = monthly_rate * 12

        return {
            'monthly_rate': monthly_rate,
            'annual_rate': annual_rate,
            'monthly_dollars': monthly_dollars,
            'sample_size': len(df)
        }

    @staticmethod
    def detect_market_regime(df: pd.DataFrame) -> str:
        """
        Detect current market regime (hot/cold/stable).

        Args:
            df: Sales dataframe

        Returns:
            Market regime string
        """
        # Recent sales (last 3 months)
        df = df.copy()
        df['sale_date'] = pd.to_datetime(df['sale_date'])

        cutoff_date = datetime.now() - pd.Timedelta(days=90)
        recent = df[df['sale_date'] >= cutoff_date]

        if len(recent) < 10:
            return 'insufficient_data'

        # Calculate appreciation rate
        appreciation = TimeSeriesAnalyzer.calculate_appreciation_rate(recent)
        annual_rate = appreciation['annual_rate']

        # Classify regime
        if annual_rate > 0.10:  # >10% annual appreciation
            return 'hot'
        elif annual_rate < -0.05:  # <-5% annual depreciation
            return 'cold'
        else:
            return 'stable'

    @staticmethod
    def forecast_price(
        df: pd.DataFrame,
        months_ahead: int = 6
    ) -> Dict:
        """
        Simple price forecast using moving average.

        Args:
            df: Sales dataframe
            months_ahead: Months to forecast

        Returns:
            Forecast dictionary
        """
        monthly = TimeSeriesAnalyzer.calculate_monthly_trends(df)

        if len(monthly) < 3:
            return {'forecast': None, 'confidence': 'low'}

        # Simple moving average
        recent_prices = monthly['sale_price_median'].tail(3).values
        forecast = np.mean(recent_prices)

        # Trend adjustment
        if len(recent_prices) >= 2:
            trend = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
            forecast += trend * months_ahead

        return {
            'forecast': forecast,
            'confidence': 'medium' if len(monthly) >= 6 else 'low',
            'months_ahead': months_ahead
        }


class NeighborhoodClusterer:
    """Cluster properties into neighborhoods/submarkets."""

    def __init__(self, n_clusters: int = 5):
        """Initialize clusterer."""
        self.n_clusters = n_clusters
        self.kmeans = None
        self.cluster_profiles = None

    def fit_clusters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit K-means clustering on property characteristics.

        Args:
            df: Sales dataframe

        Returns:
            DataFrame with cluster assignments
        """
        # Select features for clustering
        feature_cols = ['latitude', 'longitude', 'sale_price', 'price_per_sqft']
        df_cluster = df[feature_cols].dropna()

        if len(df_cluster) < self.n_clusters:
            logger.warning("Insufficient data for clustering")
            return df

        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_cluster[feature_cols])

        # Fit K-means
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        clusters = self.kmeans.fit_predict(X_scaled)

        # Add cluster labels
        df_result = df.copy()
        df_result.loc[df_cluster.index, 'cluster'] = clusters

        # Calculate cluster profiles
        self.cluster_profiles = df_result.groupby('cluster').agg({
            'sale_price': ['count', 'median', 'mean'],
            'price_per_sqft': ['median'],
            'latitude': ['mean'],
            'longitude': ['mean']
        }).round(2)

        logger.info(f"Created {self.n_clusters} neighborhood clusters")

        return df_result

    def get_cluster_profile(self, cluster_id: int) -> Dict:
        """Get profile for a specific cluster."""
        if self.cluster_profiles is None:
            return {}

        profile = self.cluster_profiles.loc[cluster_id].to_dict()
        return profile


class EnhancedConfidenceScorer:
    """Advanced confidence scoring for valuations."""

    @staticmethod
    def score_valuation(
        num_comps: int,
        avg_similarity: float,
        avg_recency_days: float,
        price_variance: float,
        data_quality_score: float,
        market_regime: str
    ) -> Tuple[int, Dict]:
        """
        Calculate comprehensive confidence score.

        Args:
            num_comps: Number of comparables used
            avg_similarity: Average similarity score (0-100)
            avg_recency_days: Average days since comp sales
            price_variance: Coefficient of variation in comp prices
            data_quality_score: Data quality score (0-100)
            market_regime: Market regime (hot/cold/stable)

        Returns:
            Tuple of (confidence_score, breakdown_dict)
        """
        score = 100
        breakdown = {}

        # 1. Number of comps (max -20 points)
        if num_comps < 5:
            comp_penalty = (5 - num_comps) * 5
            score -= comp_penalty
            breakdown['comp_count_penalty'] = -comp_penalty
        elif num_comps >= 10:
            breakdown['comp_count_bonus'] = 5
            score += 5

        # 2. Similarity score (max -25 points)
        if avg_similarity < 70:
            similarity_penalty = (70 - avg_similarity) * 0.5
            score -= similarity_penalty
            breakdown['similarity_penalty'] = -similarity_penalty

        # 3. Recency (max -15 points)
        if avg_recency_days > 90:
            recency_penalty = min((avg_recency_days - 90) / 30 * 5, 15)
            score -= recency_penalty
            breakdown['recency_penalty'] = -recency_penalty

        # 4. Price variance (max -20 points)
        if price_variance > 0.15:
            variance_penalty = (price_variance - 0.15) * 100
            variance_penalty = min(variance_penalty, 20)
            score -= variance_penalty
            breakdown['variance_penalty'] = -variance_penalty

        # 5. Data quality (max -15 points)
        if data_quality_score < 90:
            quality_penalty = (90 - data_quality_score) / 6
            score -= quality_penalty
            breakdown['quality_penalty'] = -quality_penalty

        # 6. Market regime adjustment
        if market_regime == 'hot':
            score -= 5
            breakdown['market_regime'] = -5  # Less confident in hot market
        elif market_regime == 'cold':
            score -= 3
            breakdown['market_regime'] = -3

        final_score = int(max(0, min(score, 100)))

        return final_score, breakdown


class SensitivityAnalyzer:
    """Sensitivity analysis for valuation adjustments."""

    @staticmethod
    def test_adjustment_sensitivity(
        base_price: float,
        adjustments: Dict[str, float],
        variance_pct: float = 0.20
    ) -> pd.DataFrame:
        """
        Test how different adjustment weights affect final price.

        Args:
            base_price: Base comparable price
            adjustments: Dictionary of adjustments
            variance_pct: Percentage to vary each adjustment

        Returns:
            DataFrame showing sensitivity results
        """
        results = []

        for adj_name, adj_value in adjustments.items():
            # Test with +/- variance
            for multiplier in [1 - variance_pct, 1.0, 1 + variance_pct]:
                test_adjustments = adjustments.copy()
                test_adjustments[adj_name] = adj_value * multiplier

                final_price = base_price + sum(test_adjustments.values())

                results.append({
                    'adjustment': adj_name,
                    'multiplier': multiplier,
                    'adjustment_value': test_adjustments[adj_name],
                    'final_price': final_price,
                    'price_change': final_price - base_price
                })

        df = pd.DataFrame(results)
        return df

    @staticmethod
    def identify_key_drivers(sensitivity_df: pd.DataFrame) -> List[str]:
        """Identify which adjustments have the biggest impact."""
        # Calculate price range for each adjustment
        impact = sensitivity_df.groupby('adjustment')['final_price'].agg(
            lambda x: x.max() - x.min()
        ).sort_values(ascending=False)

        return impact.index.tolist()


class MultiMethodComparator:
    """Compare valuations across multiple methodologies."""

    @staticmethod
    def compare_methods(
        comparable_sales_value: float,
        ml_prediction: float,
        price_per_sqft_value: float,
        weights: Dict[str, float] = None
    ) -> Dict:
        """
        Compare and blend multiple valuation methods.

        Args:
            comparable_sales_value: CMA valuation
            ml_prediction: ML model prediction
            price_per_sqft_value: Simple price/sqft method
            weights: Optional custom weights (must sum to 1.0)

        Returns:
            Comparison results dictionary
        """
        methods = {
            'comparable_sales': comparable_sales_value,
            'ml_prediction': ml_prediction,
            'price_per_sqft': price_per_sqft_value
        }

        # Default equal weights
        if weights is None:
            weights = {
                'comparable_sales': 0.50,
                'ml_prediction': 0.30,
                'price_per_sqft': 0.20
            }

        # Weighted average
        weighted_value = sum(
            methods[method] * weight
            for method, weight in weights.items()
        )

        # Calculate agreement (standard deviation / mean)
        values = list(methods.values())
        mean_value = np.mean(values)
        std_value = np.std(values)
        agreement_score = 100 * (1 - std_value / mean_value) if mean_value > 0 else 0

        # Range
        value_range = (min(values), max(values))

        return {
            'methods': methods,
            'weighted_average': weighted_value,
            'simple_average': mean_value,
            'range': value_range,
            'agreement_score': agreement_score,
            'standard_deviation': std_value
        }


def run_enhanced_valuation(db_path: str = "loudoun_sales_clean.db") -> Dict:
    """
    Run comprehensive enhanced valuation pipeline.

    Args:
        db_path: Path to cleaned database

    Returns:
        Results dictionary
    """
    logger.info("="*80)
    logger.info("STARTING ENHANCED VALUATION ANALYSIS")
    logger.info("="*80)

    # Load data
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()

    logger.info(f"Loaded {len(df)} records from {db_path}")

    results = {}

    # 1. Train ML model
    logger.info("\n1. Training machine learning models...")
    predictor = MLPricePredictor()
    X, y = predictor.prepare_features(df)
    training_results = predictor.train_models(X, y)
    predictor.save_model()

    results['ml_training'] = training_results

    # 2. Outlier detection
    logger.info("\n2. Detecting outliers...")
    outliers = {
        'zscore': OutlierDetector.detect_zscore_outliers(df, 'sale_price', threshold=3.0),
        'iqr': OutlierDetector.detect_iqr_outliers(df, 'sale_price', multiplier=1.5),
        'lof': OutlierDetector.detect_local_outliers(
            df,
            ['sale_price', 'sqft', 'price_per_sqft'],
            contamination=0.1
        )
    }

    results['outliers'] = {k: len(v) for k, v in outliers.items()}

    # 3. Time-series analysis
    logger.info("\n3. Analyzing market trends...")
    monthly_trends = TimeSeriesAnalyzer.calculate_monthly_trends(df)
    appreciation = TimeSeriesAnalyzer.calculate_appreciation_rate(df)
    market_regime = TimeSeriesAnalyzer.detect_market_regime(df)

    results['time_series'] = {
        'monthly_trends': monthly_trends.to_dict('records'),
        'appreciation_rate': appreciation,
        'market_regime': market_regime
    }

    logger.info(f"Market regime: {market_regime}")
    logger.info(f"Annual appreciation: {appreciation['annual_rate']*100:.2f}%")

    # 4. Neighborhood clustering
    logger.info("\n4. Clustering neighborhoods...")
    clusterer = NeighborhoodClusterer(n_clusters=5)
    df_clustered = clusterer.fit_clusters(df)

    results['clusters'] = {
        'n_clusters': 5,
        'profiles': clusterer.cluster_profiles.to_dict() if clusterer.cluster_profiles is not None else {}
    }

    logger.info("\n" + "="*80)
    logger.info("ENHANCED VALUATION COMPLETE")
    logger.info("="*80)
    logger.info(f"Best ML model: {predictor.best_model_name}")
    logger.info(f"ML R² score: {training_results[predictor.best_model_name]['r2']:.3f}")
    logger.info(f"Market regime: {market_regime}")
    logger.info("="*80)

    return results


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "loudoun_sales_clean.db"

    results = run_enhanced_valuation(db_path)

    print(f"\n✓ Enhanced valuation analysis complete!")
    print(f"  Best ML model: {list(results['ml_training'].keys())[0]}")
    print(f"  Market regime: {results['time_series']['market_regime']}")
