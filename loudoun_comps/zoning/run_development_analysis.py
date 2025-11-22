#!/usr/bin/env python3
"""
Loudoun County Development Analysis - Main Orchestrator

Comprehensive CLI for zoning and development analysis with Google Maps-ready
interactive maps and enterprise-grade reporting.

Author: Property Valuation System
Version: 1.0.0
Date: November 2025
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Import all components
from development_database import DevelopmentDatabase, initialize_development_database
from sample_data_generator import populate_sample_data
from development_pressure_analyzer import DevelopmentPressureAnalyzer
from map_generator import MapGenerator
from report_generator import DevelopmentReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DevelopmentAnalysisSystem:
    """Main orchestrator for development analysis system."""

    def __init__(
        self,
        dev_db_path: str = "loudoun_development.db",
        sales_db_path: str = "../loudoun_sales_clean.db"
    ):
        """
        Initialize analysis system.

        Args:
            dev_db_path: Development database path
            sales_db_path: Sales database path (for appreciation)
        """
        self.dev_db_path = dev_db_path
        self.sales_db_path = sales_db_path

    def initialize_database(self, clear_existing: bool = False):
        """
        Initialize the development database.

        Args:
            clear_existing: Whether to clear existing data
        """
        logger.info("="*80)
        logger.info("INITIALIZING DEVELOPMENT DATABASE")
        logger.info("="*80)

        db_path = initialize_development_database(
            db_path=self.dev_db_path,
            clear_existing=clear_existing
        )

        logger.info(f"✓ Database ready: {db_path}")

    def populate_sample_data(
        self,
        center_lat: float,
        center_lon: float,
        area_name: str = "Ashburn"
    ):
        """
        Populate database with sample development data.

        Args:
            center_lat: Center latitude for sample data
            center_lon: Center longitude for sample data
            area_name: Area name for logging
        """
        logger.info("")
        logger.info("="*80)
        logger.info("GENERATING SAMPLE DEVELOPMENT DATA")
        logger.info("="*80)

        populate_sample_data(
            db_path=self.dev_db_path,
            center_lat=center_lat,
            center_lon=center_lon,
            area_name=area_name
        )

        logger.info(f"✓ Sample data populated for {area_name}")

    def analyze_property(
        self,
        subject_lat: float,
        subject_lon: float,
        subject_address: str
    ) -> dict:
        """
        Run complete development analysis for a property.

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            subject_address: Subject property address

        Returns:
            Analysis results dictionary
        """
        logger.info("")
        logger.info("="*80)
        logger.info(f"ANALYZING PROPERTY: {subject_address}")
        logger.info("="*80)

        analyzer = DevelopmentPressureAnalyzer(self.dev_db_path)

        result = analyzer.calculate_development_pressure(
            subject_lat,
            subject_lon
        )

        # Print summary
        logger.info("")
        logger.info("ANALYSIS RESULTS:")
        logger.info(f"  Development Pressure Score: {result['total_score']:.1f}/100")
        logger.info(f"  Classification: {result['classification']}")
        logger.info("")
        logger.info("  Component Scores:")
        logger.info(f"    Rezoning Activity:      {result['components']['rezoning_score']:.1f}/100 (30% weight)")
        logger.info(f"    Building Permits:       {result['components']['permit_score']:.1f}/100 (25% weight)")
        logger.info(f"    Land Sales:             {result['components']['land_sale_score']:.1f}/100 (20% weight)")
        logger.info(f"    Property Appreciation:  {result['components']['appreciation_score']:.1f}/100 (15% weight)")
        logger.info(f"    Infrastructure Proximity: {result['components']['proximity_score']:.1f}/100 (10% weight)")
        logger.info("")
        logger.info("  Activity Detected:")
        logger.info(f"    Rezonings: {len(result['details']['rezonings'])}")
        logger.info(f"    Building Permits: {len(result['details']['permits'])}")
        logger.info(f"    Large Parcel Sales: {len(result['details']['land_sales'])}")

        return result

    def generate_map(
        self,
        subject_lat: float,
        subject_lon: float,
        subject_address: str,
        output_path: str = "development_map.html"
    ) -> str:
        """
        Generate Google Maps-ready interactive map.

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            subject_address: Subject property address
            output_path: Output HTML file path

        Returns:
            Path to generated map
        """
        logger.info("")
        logger.info("="*80)
        logger.info("GENERATING INTERACTIVE MAP")
        logger.info("="*80)

        generator = MapGenerator(self.dev_db_path)

        map_data = generator.create_map_data(
            subject_lat,
            subject_lon,
            subject_address
        )

        output_path = generator.generate_html_map(map_data, output_path)

        logger.info(f"✓ Map saved to: {output_path}")
        logger.info("  Data structure is Google Maps API-ready!")

        return output_path

    def generate_report(
        self,
        subject_lat: float,
        subject_lon: float,
        subject_address: str,
        output_path: str = "development_analysis_report.html"
    ) -> str:
        """
        Generate comprehensive HTML report.

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            subject_address: Subject property address
            output_path: Output HTML file path

        Returns:
            Path to generated report
        """
        logger.info("")
        logger.info("="*80)
        logger.info("GENERATING COMPREHENSIVE REPORT")
        logger.info("="*80)

        generator = DevelopmentReportGenerator(
            self.dev_db_path,
            self.sales_db_path
        )

        output_path = generator.generate_report(
            subject_lat,
            subject_lon,
            subject_address,
            output_path
        )

        logger.info(f"✓ Report saved to: {output_path}")

        return output_path

    def run_full_analysis(
        self,
        subject_lat: float,
        subject_lon: float,
        subject_address: str,
        generate_sample_data: bool = False,
        area_name: str = "Ashburn"
    ) -> dict:
        """
        Run complete analysis pipeline.

        Args:
            subject_lat: Subject property latitude
            subject_lon: Subject property longitude
            subject_address: Subject property address
            generate_sample_data: Whether to generate sample data
            area_name: Area name for sample data

        Returns:
            Complete results dictionary
        """
        logger.info("")
        logger.info("╔" + "="*78 + "╗")
        logger.info("║" + " "*15 + "DEVELOPMENT ANALYSIS SYSTEM" + " "*35 + "║")
        logger.info("╚" + "="*78 + "╝")

        start_time = datetime.now()

        # Initialize database
        self.initialize_database(clear_existing=False)

        # Populate sample data if requested
        if generate_sample_data:
            self.populate_sample_data(
                subject_lat,
                subject_lon,
                area_name
            )

        # Run analysis
        analysis_result = self.analyze_property(
            subject_lat,
            subject_lon,
            subject_address
        )

        # Generate interactive map
        map_path = self.generate_map(
            subject_lat,
            subject_lon,
            subject_address
        )

        # Generate comprehensive report
        report_path = self.generate_report(
            subject_lat,
            subject_lon,
            subject_address
        )

        # Calculate elapsed time
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        logger.info("")
        logger.info("="*80)
        logger.info("ANALYSIS COMPLETE ✓")
        logger.info("="*80)
        logger.info(f"Total time: {elapsed:.1f} seconds")
        logger.info("")
        logger.info("Output Files:")
        logger.info(f"  Comprehensive Report: {report_path}")
        logger.info(f"  Interactive Map: {map_path}")
        logger.info("="*80)

        return {
            'analysis': analysis_result,
            'map_path': map_path,
            'report_path': report_path,
            'elapsed_seconds': elapsed
        }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Loudoun County Development Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full analysis with sample data
  python run_development_analysis.py \\
    --address "43500 Cloister Pl, Ashburn, VA 20147" \\
    --lat 39.0437 --lon -77.4875 \\
    --generate-sample-data

  # Analyze existing data
  python run_development_analysis.py \\
    --address "123 Main St, Leesburg, VA 20175" \\
    --lat 39.1157 --lon -77.5636

  # Initialize database only
  python run_development_analysis.py --init-db

  # Generate sample data only
  python run_development_analysis.py --generate-sample-data \\
    --lat 39.0437 --lon -77.4875

  # Generate map only
  python run_development_analysis.py \\
    --address "43500 Cloister Pl, Ashburn, VA 20147" \\
    --lat 39.0437 --lon -77.4875 \\
    --map-only

  # Generate report only
  python run_development_analysis.py \\
    --address "43500 Cloister Pl, Ashburn, VA 20147" \\
    --lat 39.0437 --lon -77.4875 \\
    --report-only
        """
    )

    # Database options
    parser.add_argument(
        '--dev-db',
        default='loudoun_development.db',
        help='Development database path (default: loudoun_development.db)'
    )

    parser.add_argument(
        '--sales-db',
        default='../loudoun_sales_clean.db',
        help='Sales database path (default: ../loudoun_sales_clean.db)'
    )

    # Property details
    parser.add_argument(
        '--address',
        help='Subject property address'
    )

    parser.add_argument(
        '--lat',
        type=float,
        help='Subject property latitude'
    )

    parser.add_argument(
        '--lon',
        type=float,
        help='Subject property longitude'
    )

    # Operations
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database only'
    )

    parser.add_argument(
        '--generate-sample-data',
        action='store_true',
        help='Generate sample development data'
    )

    parser.add_argument(
        '--area-name',
        default='Ashburn',
        help='Area name for sample data (default: Ashburn)'
    )

    parser.add_argument(
        '--map-only',
        action='store_true',
        help='Generate interactive map only'
    )

    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate comprehensive report only'
    )

    parser.add_argument(
        '--clear-db',
        action='store_true',
        help='Clear existing database data'
    )

    # Output options
    parser.add_argument(
        '--output-map',
        default='development_map.html',
        help='Map output path (default: development_map.html)'
    )

    parser.add_argument(
        '--output-report',
        default='development_analysis_report.html',
        help='Report output path (default: development_analysis_report.html)'
    )

    args = parser.parse_args()

    # Initialize system
    system = DevelopmentAnalysisSystem(
        dev_db_path=args.dev_db,
        sales_db_path=args.sales_db
    )

    try:
        # Initialize database only
        if args.init_db:
            system.initialize_database(clear_existing=args.clear_db)
            return

        # Generate sample data only
        if args.generate_sample_data and not (args.lat and args.lon):
            parser.error("--generate-sample-data requires --lat and --lon")

        if args.generate_sample_data and not args.address:
            system.initialize_database()
            system.populate_sample_data(
                args.lat,
                args.lon,
                args.area_name
            )
            return

        # Map only
        if args.map_only:
            if not all([args.address, args.lat, args.lon]):
                parser.error("--map-only requires --address, --lat, and --lon")

            system.generate_map(
                args.lat,
                args.lon,
                args.address,
                args.output_map
            )
            return

        # Report only
        if args.report_only:
            if not all([args.address, args.lat, args.lon]):
                parser.error("--report-only requires --address, --lat, and --lon")

            system.generate_report(
                args.lat,
                args.lon,
                args.address,
                args.output_report
            )
            return

        # Full analysis
        if not all([args.address, args.lat, args.lon]):
            parser.error("Full analysis requires --address, --lat, and --lon")

        result = system.run_full_analysis(
            args.lat,
            args.lon,
            args.address,
            generate_sample_data=args.generate_sample_data,
            area_name=args.area_name
        )

        # Print result summary
        print("\n" + "="*80)
        print("ANALYSIS SUMMARY")
        print("="*80)
        print(f"Address:               {args.address}")
        print(f"Development Score:     {result['analysis']['total_score']:.1f}/100")
        print(f"Classification:        {result['analysis']['classification']}")
        print(f"Comprehensive Report:  {result['report_path']}")
        print(f"Interactive Map:       {result['map_path']}")
        print("="*80)

    except KeyboardInterrupt:
        logger.warning("\n\nAnalysis interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\n\nAnalysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
