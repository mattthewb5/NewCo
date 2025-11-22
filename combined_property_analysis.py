#!/usr/bin/env python3
"""
Combined Property Analysis System

Unified property analysis orchestrator that combines:
1. Location Quality Analysis (location_analyzer.py)
2. Development Pressure Analysis (development_pressure_analyzer.py)
3. Property Valuation (property_valuator.py)
4. Enhanced HTML Report Generation (enhanced_report_generator.py)

Provides complete property intelligence in < 5 seconds.

Author: NewCo Real Estate Intelligence
Date: November 2024

Usage:
    # Basic analysis (location + development only)
    python combined_property_analysis.py --address "43500 Tuckaway Pl, Leesburg, VA 20176"

    # Full analysis with valuation
    python combined_property_analysis.py \\
        --address "43500 Tuckaway Pl, Leesburg, VA 20176" \\
        --sqft 3200 --bedrooms 4 --bathrooms 3.5 --year-built 2015

    # Open report in browser
    python combined_property_analysis.py \\
        --address "43500 Tuckaway Pl, Leesburg, VA 20176" \\
        --open
"""

import argparse
import sys
import time
import webbrowser
from typing import Dict, Optional, Tuple

try:
    from geopy.geocoders import Nominatim
    GEOCODING_AVAILABLE = True
except ImportError:
    GEOCODING_AVAILABLE = False

from location_analyzer import LocationQualityAnalyzer
from development_pressure_analyzer import DevelopmentPressureAnalyzer
from property_valuator import PropertyValuator
from enhanced_report_generator import EnhancedReportGenerator


class CombinedPropertyAnalyzer:
    """
    Unified property analysis system

    Combines:
    - Valuation Engine (property_valuator.py)
    - Zoning Analysis (development_pressure_analyzer.py)
    - Location Quality (location_analyzer.py)

    Into one comprehensive analysis with beautiful HTML reports.
    """

    def __init__(self, db_path_valuation: Optional[str] = None,
                 db_path_development: Optional[str] = None):
        """
        Initialize combined analyzer

        Args:
            db_path_valuation: Path to sales database (optional)
            db_path_development: Path to development database (optional)
        """
        self.db_val = db_path_valuation
        self.db_dev = db_path_development

        # Initialize components
        self.location_analyzer = LocationQualityAnalyzer()
        self.dev_analyzer = DevelopmentPressureAnalyzer(db_path_development)
        self.valuator = PropertyValuator(db_path_valuation)
        self.report_generator = EnhancedReportGenerator()

    def analyze_property(self, address: str, lat: Optional[float] = None,
                        lon: Optional[float] = None,
                        property_data: Optional[Dict] = None) -> Dict:
        """
        Complete property analysis

        Args:
            address: Full address string
            lat, lon: Coordinates (optional, will geocode if not provided)
            property_data: Optional dict with sqft, beds, baths, etc.

        Returns:
            dict with:
                - valuation_result
                - location_result
                - development_result
                - report_path (HTML file)
                - execution_time (seconds)
        """
        start_time = time.time()

        print(f"\n{'='*70}")
        print(f"COMPREHENSIVE PROPERTY ANALYSIS")
        print(f"{'='*70}\n")
        print(f"Address: {address}")

        # Step 1: Geocode if needed
        if lat is None or lon is None:
            print("\n📍 Geocoding address...")
            lat, lon = self.geocode_address(address)
            if lat is None:
                print("⚠️  Warning: Could not geocode address. Using default Loudoun County coordinates.")
                lat, lon = 39.0437, -77.4875  # Default to Leesburg area

        print(f"   Coordinates: {lat:.4f}, {lon:.4f}")

        # Step 2: Run location quality analysis
        print("\n📊 Analyzing location quality...")
        location_start = time.time()
        location_result = self.location_analyzer.analyze_location(lat, lon, address)
        location_time = time.time() - location_start
        print(f"   ✓ Location Quality: {location_result['quality_score']}/10 ({location_result['rating']})")
        print(f"   ✓ Completed in {location_time:.2f}s")

        # Step 3: Run development pressure analysis
        print("\n🏗️  Analyzing development pressure...")
        dev_start = time.time()
        development_result = self.dev_analyzer.calculate_development_pressure(lat, lon)
        dev_time = time.time() - dev_start
        print(f"   ✓ Development Pressure: {development_result['pressure_score']}/100 ({development_result['classification']})")
        print(f"   ✓ Completed in {dev_time:.2f}s")

        # Step 4: Run valuation (if property data provided)
        valuation_result = None
        if property_data:
            print("\n💰 Running valuation analysis...")
            val_start = time.time()
            try:
                # Add coordinates to property data
                property_data['latitude'] = lat
                property_data['longitude'] = lon
                property_data['address'] = address

                valuation_result = self.valuator.estimate_property_value(property_data)
                val_time = time.time() - val_start
                print(f"   ✓ Estimated Value: ${valuation_result.get('estimated_value', 0):,}")
                print(f"   ✓ Confidence: {valuation_result.get('confidence_level', 'N/A')} ({valuation_result.get('confidence_score', 0)}%)")
                print(f"   ✓ Completed in {val_time:.2f}s")
            except Exception as e:
                print(f"   ⚠️  Valuation error: {e}")
                valuation_result = {
                    'estimated_value': 0,
                    'confidence_score': 0,
                    'confidence_level': 'N/A',
                    'note': f'Property valuation unavailable: {str(e)}'
                }
        else:
            print("\n💰 Valuation: Skipped (no property data provided)")
            valuation_result = {
                'estimated_value': 0,
                'confidence_score': 0,
                'confidence_level': 'N/A',
                'note': 'Property characteristics not provided',
                'valuation_range': {'low': 0, 'high': 0},
                'price_per_sqft': 0,
                'comparables': [],
                'comp_count': 0,
                'market_statistics': {},
                'methodology': 'Not Available'
            }

        # Step 5: Generate comprehensive report
        print("\n📄 Generating comprehensive HTML report...")
        report_start = time.time()

        # Clean address for filename
        clean_address = address.replace(' ', '_').replace(',', '').replace('.', '')
        report_path = f"comprehensive_report_{clean_address}.html"

        self.report_generator.generate_comprehensive_report(
            property_data={'address': address, 'lat': lat, 'lon': lon},
            valuation_result=valuation_result,
            location_result=location_result,
            development_result=development_result,
            output_path=report_path
        )
        report_time = time.time() - report_start
        print(f"   ✓ Report generated: {report_path}")
        print(f"   ✓ Completed in {report_time:.2f}s")

        total_time = time.time() - start_time

        print(f"\n{'='*70}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*70}")
        print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"📊 Location Score: {location_result['quality_score']}/10")
        print(f"🏗️  Development Pressure: {development_result['pressure_score']}/100")
        if property_data:
            print(f"💰 Estimated Value: ${valuation_result.get('estimated_value', 0):,}")
        print(f"📄 Report: {report_path}\n")

        return {
            'address': address,
            'coordinates': {'lat': lat, 'lon': lon},
            'valuation': valuation_result,
            'location': location_result,
            'development': development_result,
            'report_path': report_path,
            'execution_time': round(total_time, 2),
            'success': True
        }

    def geocode_address(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode address to coordinates

        Args:
            address: Address string

        Returns:
            Tuple of (latitude, longitude) or (None, None) if failed
        """
        if not GEOCODING_AVAILABLE:
            print("   ⚠️  Geocoding library not available. Install with: pip install geopy")
            return None, None

        try:
            geolocator = Nominatim(user_agent="newco_property_analyzer")
            location = geolocator.geocode(address, timeout=10)

            if location:
                return location.latitude, location.longitude
            else:
                return None, None

        except Exception as e:
            print(f"   ⚠️  Geocoding error: {e}")
            return None, None


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Comprehensive Property Analysis for Loudoun County',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis (location + development only)
  python combined_property_analysis.py --address "43500 Tuckaway Pl, Leesburg, VA 20176"

  # Full analysis with valuation
  python combined_property_analysis.py \\
      --address "43500 Tuckaway Pl, Leesburg, VA 20176" \\
      --sqft 3200 --bedrooms 4 --bathrooms 3.5 --year-built 2015

  # Provide coordinates explicitly
  python combined_property_analysis.py \\
      --address "43500 Tuckaway Pl, Leesburg, VA 20176" \\
      --lat 39.0437 --lon -77.4875

  # Open report in browser after generation
  python combined_property_analysis.py \\
      --address "43500 Tuckaway Pl, Leesburg, VA 20176" \\
      --open

  # Complete example with all options
  python combined_property_analysis.py \\
      --address "43500 Tuckaway Pl, Leesburg, VA 20176" \\
      --sqft 3200 --bedrooms 4 --bathrooms 3.5 \\
      --year-built 2015 --lot-acres 0.35 \\
      --open
        """
    )

    # Required arguments
    parser.add_argument('--address', required=True, help='Property address')

    # Optional coordinates
    parser.add_argument('--lat', type=float, help='Latitude (optional, will geocode if not provided)')
    parser.add_argument('--lon', type=float, help='Longitude (optional, will geocode if not provided)')

    # Optional property characteristics (for valuation)
    parser.add_argument('--sqft', type=int, help='Square footage')
    parser.add_argument('--bedrooms', type=int, help='Number of bedrooms')
    parser.add_argument('--bathrooms', type=float, help='Number of bathrooms')
    parser.add_argument('--year-built', type=int, help='Year built')
    parser.add_argument('--lot-acres', type=float, help='Lot size in acres')
    parser.add_argument('--zip-code', help='ZIP code')

    # Options
    parser.add_argument('--open', action='store_true', help='Open report in browser after generation')
    parser.add_argument('--output', help='Output filename (default: auto-generated)')

    # Database paths (advanced)
    parser.add_argument('--db-valuation', help='Path to sales database')
    parser.add_argument('--db-development', help='Path to development database')

    args = parser.parse_args()

    # Build property data dict if characteristics provided
    property_data = None
    if args.sqft:
        property_data = {
            'address': args.address,
            'sqft': args.sqft,
            'bedrooms': args.bedrooms or 3,
            'bathrooms': args.bathrooms or 2.5,
            'year_built': args.year_built or 2015,
            'lot_size_acres': args.lot_acres or 0.25,
            'zip_code': args.zip_code or '20176'
        }

    # Run analysis
    try:
        analyzer = CombinedPropertyAnalyzer(
            db_path_valuation=args.db_valuation,
            db_path_development=args.db_development
        )

        result = analyzer.analyze_property(
            address=args.address,
            lat=args.lat,
            lon=args.lon,
            property_data=property_data
        )

        # Open in browser if requested
        if args.open and result.get('report_path'):
            print(f"\n🌐 Opening report in browser...")
            webbrowser.open('file://' + result['report_path'])

        print(f"\n✅ Analysis complete! Report saved to: {result['report_path']}")

        # Print summary
        if result.get('execution_time', 0) < 5.0:
            print(f"🚀 DEMO-READY: Analysis completed in {result['execution_time']}s (target: <5s) ✓")
        else:
            print(f"⏱️  Analysis completed in {result['execution_time']}s")

        return 0

    except KeyboardInterrupt:
        print("\n\n❌ Analysis interrupted by user")
        return 1

    except Exception as e:
        print(f"\n\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
