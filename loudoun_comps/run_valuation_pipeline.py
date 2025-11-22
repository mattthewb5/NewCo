#!/usr/bin/env python3
"""
Loudoun County Property Valuation Pipeline - Main Orchestrator

Runs the complete data pipeline: validation → integration → enhanced valuation

Author: Property Valuation System
Version: 1.0.0
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

# Import pipeline components
from data_validation import validate_database
from data_integration import integrate_and_enrich_data
from enhanced_valuation import run_enhanced_valuation
from valuation import PropertyValuator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'pipeline_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class ValuationPipeline:
    """Main orchestrator for the valuation pipeline."""

    def __init__(
        self,
        input_db: str = "loudoun_sales.db",
        output_db: str = "loudoun_sales_clean.db"
    ):
        """
        Initialize pipeline.

        Args:
            input_db: Input database path
            output_db: Output (cleaned) database path
        """
        self.input_db = input_db
        self.output_db = output_db
        self.results = {}

    def run_validation(self, generate_report: bool = True) -> dict:
        """
        Run data validation phase.

        Args:
            generate_report: Whether to generate HTML report

        Returns:
            Validation results dictionary
        """
        logger.info("")
        logger.info("="*80)
        logger.info("PHASE 1: DATA VALIDATION")
        logger.info("="*80)

        try:
            result = validate_database(
                db_path=self.input_db,
                output_html="validation_report.html" if generate_report else None
            )

            self.results['validation'] = {
                'status': 'success',
                'completeness_score': result.completeness_score,
                'total_records': result.total_records,
                'flagged_records': result.flagged_records,
                'quality_issues': len(result.quality_issues)
            }

            logger.info(f"✓ Validation complete: {result.completeness_score:.1f}% completeness")

            return self.results['validation']

        except Exception as e:
            logger.error(f"✗ Validation failed: {e}")
            self.results['validation'] = {'status': 'failed', 'error': str(e)}
            raise

    def run_integration(self, geocode: bool = True) -> dict:
        """
        Run data integration and enrichment phase.

        Args:
            geocode: Whether to geocode addresses

        Returns:
            Integration results dictionary
        """
        logger.info("")
        logger.info("="*80)
        logger.info("PHASE 2: DATA INTEGRATION & ENRICHMENT")
        logger.info("="*80)

        try:
            df = integrate_and_enrich_data(
                input_db=self.input_db,
                output_db=self.output_db,
                geocode=geocode,
                skip_cached=True
            )

            self.results['integration'] = {
                'status': 'success',
                'records_processed': len(df),
                'output_database': self.output_db
            }

            logger.info(f"✓ Integration complete: {len(df)} records processed")

            return self.results['integration']

        except Exception as e:
            logger.error(f"✗ Integration failed: {e}")
            self.results['integration'] = {'status': 'failed', 'error': str(e)}
            raise

    def run_enhanced_valuation(self) -> dict:
        """
        Run enhanced valuation analysis.

        Returns:
            Enhanced valuation results dictionary
        """
        logger.info("")
        logger.info("="*80)
        logger.info("PHASE 3: ENHANCED VALUATION ANALYSIS")
        logger.info("="*80)

        try:
            results = run_enhanced_valuation(db_path=self.output_db)

            self.results['enhanced_valuation'] = {
                'status': 'success',
                'market_regime': results['time_series']['market_regime'],
                'best_ml_model': list(results['ml_training'].keys())[0],
                'clusters_created': results['clusters']['n_clusters']
            }

            logger.info("✓ Enhanced valuation complete")

            return self.results['enhanced_valuation']

        except Exception as e:
            logger.error(f"✗ Enhanced valuation failed: {e}")
            self.results['enhanced_valuation'] = {'status': 'failed', 'error': str(e)}
            raise

    def value_property(self, address: str, property_data: dict) -> dict:
        """
        Value a specific property using the trained system.

        Args:
            address: Property address
            property_data: Dictionary with property details

        Returns:
            Valuation result dictionary
        """
        logger.info("")
        logger.info("="*80)
        logger.info(f"VALUING PROPERTY: {address}")
        logger.info("="*80)

        try:
            with PropertyValuator(self.output_db) as valuator:
                result = valuator.estimate_property_value(property_data)

            if result:
                logger.info(f"✓ Estimated Value: ${result['estimated_value']:,}")
                logger.info(f"  Confidence Score: {result['confidence_score']}/100")
                logger.info(f"  Comparables Used: {len(result['comps_used'])}")

                return result
            else:
                logger.warning("✗ Valuation failed - insufficient data")
                return None

        except Exception as e:
            logger.error(f"✗ Property valuation failed: {e}")
            raise

    def run_full_pipeline(
        self,
        validate: bool = True,
        integrate: bool = True,
        enhance: bool = True,
        geocode: bool = True
    ) -> dict:
        """
        Run the complete pipeline.

        Args:
            validate: Run validation phase
            integrate: Run integration phase
            enhance: Run enhanced valuation phase
            geocode: Geocode addresses during integration

        Returns:
            Complete results dictionary
        """
        logger.info("")
        logger.info("╔" + "="*78 + "╗")
        logger.info("║" + " "*15 + "LOUDOUN COUNTY VALUATION PIPELINE" + " "*30 + "║")
        logger.info("╚" + "="*78 + "╝")
        logger.info("")

        start_time = datetime.now()

        # Phase 1: Validation
        if validate:
            self.run_validation()

        # Phase 2: Integration
        if integrate:
            self.run_integration(geocode=geocode)

        # Phase 3: Enhanced Valuation
        if enhance:
            self.run_enhanced_valuation()

        # Calculate total time
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        self.results['pipeline'] = {
            'status': 'complete',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'elapsed_seconds': elapsed
        }

        # Save results
        self._save_results()

        logger.info("")
        logger.info("="*80)
        logger.info("PIPELINE COMPLETE ✓")
        logger.info("="*80)
        logger.info(f"Total time: {elapsed:.1f} seconds")
        logger.info(f"Results saved to: pipeline_results.json")
        logger.info("="*80)

        return self.results

    def _save_results(self):
        """Save pipeline results to JSON file."""
        output_file = "pipeline_results.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Loudoun County Property Valuation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python run_valuation_pipeline.py

  # Validation only
  python run_valuation_pipeline.py --validate-only

  # Skip geocoding (faster)
  python run_valuation_pipeline.py --skip-geocoding

  # Value a specific property
  python run_valuation_pipeline.py --property-address "43423 Cloister Pl, Ashburn, VA 20147"

  # Custom database paths
  python run_valuation_pipeline.py --input-db my_sales.db --output-db my_sales_clean.db
        """
    )

    # Database options
    parser.add_argument(
        '--input-db',
        default='loudoun_sales.db',
        help='Input database path (default: loudoun_sales.db)'
    )

    parser.add_argument(
        '--output-db',
        default='loudoun_sales_clean.db',
        help='Output database path (default: loudoun_sales_clean.db)'
    )

    # Pipeline control
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Run validation only'
    )

    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip validation phase'
    )

    parser.add_argument(
        '--skip-integration',
        action='store_true',
        help='Skip integration phase'
    )

    parser.add_argument(
        '--skip-enhancement',
        action='store_true',
        help='Skip enhanced valuation phase'
    )

    parser.add_argument(
        '--skip-geocoding',
        action='store_true',
        help='Skip geocoding during integration (faster)'
    )

    # Property valuation
    parser.add_argument(
        '--property-address',
        help='Value a specific property (requires --property-* parameters)'
    )

    parser.add_argument(
        '--property-lat',
        type=float,
        help='Property latitude'
    )

    parser.add_argument(
        '--property-lon',
        type=float,
        help='Property longitude'
    )

    parser.add_argument(
        '--property-sqft',
        type=int,
        help='Property square footage'
    )

    parser.add_argument(
        '--property-bedrooms',
        type=int,
        help='Number of bedrooms'
    )

    parser.add_argument(
        '--property-bathrooms',
        type=float,
        help='Number of bathrooms'
    )

    parser.add_argument(
        '--property-year-built',
        type=int,
        help='Year built'
    )

    parser.add_argument(
        '--property-zip',
        help='ZIP code'
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = ValuationPipeline(
        input_db=args.input_db,
        output_db=args.output_db
    )

    try:
        # Validate-only mode
        if args.validate_only:
            pipeline.run_validation()
            return

        # Property valuation mode
        if args.property_address:
            # Check for required parameters
            if not all([
                args.property_lat, args.property_lon, args.property_sqft,
                args.property_bedrooms, args.property_bathrooms,
                args.property_year_built, args.property_zip
            ]):
                parser.error("--property-address requires all --property-* parameters")

            property_data = {
                'address': args.property_address,
                'latitude': args.property_lat,
                'longitude': args.property_lon,
                'sqft': args.property_sqft,
                'bedrooms': args.property_bedrooms,
                'bathrooms': args.property_bathrooms,
                'year_built': args.property_year_built,
                'zip_code': args.property_zip,
                'property_type': 'Single Family',
                'has_pool': 0,
                'has_garage': 1
            }

            result = pipeline.value_property(args.property_address, property_data)

            if result:
                # Pretty print result
                print("\n" + "="*80)
                print("VALUATION RESULT")
                print("="*80)
                print(f"Address:          {result['address']}")
                print(f"Estimated Value:  ${result['estimated_value']:,}")
                print(f"Confidence Range: ${result['confidence_range'][0]:,} - ${result['confidence_range'][1]:,}")
                print(f"Confidence Score: {result['confidence_score']}/100")
                print(f"Comparables Used: {len(result['comps_used'])}")
                print("="*80)
            else:
                sys.exit(1)

            return

        # Full pipeline mode
        pipeline.run_full_pipeline(
            validate=not args.skip_validation,
            integrate=not args.skip_integration,
            enhance=not args.skip_enhancement,
            geocode=not args.skip_geocoding
        )

    except KeyboardInterrupt:
        logger.warning("\n\nPipeline interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\n\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
