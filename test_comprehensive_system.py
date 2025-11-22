"""
Comprehensive System Test Suite

Tests for the unified property analysis system including:
- Location Quality Analysis
- Development Pressure Analysis
- Property Valuation
- Report Generation
- End-to-end integration

Author: NewCo Real Estate Intelligence
Date: November 2024
"""

import os
import sys
import time
from typing import Dict

from location_analyzer import LocationQualityAnalyzer
from development_pressure_analyzer import DevelopmentPressureAnalyzer
from property_valuator import PropertyValuator
from enhanced_report_generator import EnhancedReportGenerator
from combined_property_analysis import CombinedPropertyAnalyzer


def test_location_analyzer():
    """Test location quality analyzer"""
    print("\n" + "="*70)
    print("TEST 1: Location Quality Analyzer")
    print("="*70)

    analyzer = LocationQualityAnalyzer()

    # Test property: 43500 Tuckaway Pl, Leesburg, VA 20176
    result = analyzer.analyze_location(
        lat=39.0437,
        lon=-77.4875,
        address="43500 Tuckaway Pl, Leesburg, VA 20176"
    )

    # Assertions
    assert result['quality_score'] >= 0 and result['quality_score'] <= 10, "Quality score out of range"
    assert result['rating'] in ['Excellent', 'Very Good', 'Good', 'Fair', 'Poor'], "Invalid rating"
    assert 'highway_distances' in result, "Missing highway distances"
    assert 'metro_distances' in result, "Missing metro distances"
    assert 'warnings' in result, "Missing warnings list"
    assert 'positives' in result, "Missing positives list"

    print(f"✓ Location Score: {result['quality_score']}/10")
    print(f"✓ Rating: {result['rating']}")
    print(f"✓ Value Impact: {result['value_impact_pct']:+d}%")
    print(f"✓ Road Classification: {result['road_classification']}")
    print("✓ PASSED")

    return True


def test_development_analyzer():
    """Test development pressure analyzer"""
    print("\n" + "="*70)
    print("TEST 2: Development Pressure Analyzer")
    print("="*70)

    analyzer = DevelopmentPressureAnalyzer()

    result = analyzer.calculate_development_pressure(
        lat=39.0437,
        lon=-77.4875
    )

    # Assertions
    assert result['pressure_score'] >= 0 and result['pressure_score'] <= 100, "Pressure score out of range"
    assert result['classification'] in ['Very Low', 'Low', 'Medium', 'High', 'Very High'], "Invalid classification"
    assert 'components' in result, "Missing components"
    assert 'activity_counts' in result, "Missing activity counts"
    assert len(result.get('zone_0_1', [])) >= 0, "Invalid zone data"

    print(f"✓ Pressure Score: {result['pressure_score']}/100")
    print(f"✓ Classification: {result['classification']}")
    print(f"✓ Total Activities: {result['activity_counts']['total']}")
    print(f"✓ 0-1 mile: {result['activity_counts']['zone_0_1_miles']} activities")
    print("✓ PASSED")

    return True


def test_property_valuator():
    """Test property valuator"""
    print("\n" + "="*70)
    print("TEST 3: Property Valuator")
    print("="*70)

    valuator = PropertyValuator()

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

    # Assertions
    assert result['estimated_value'] > 0, "Invalid estimated value"
    assert result['confidence_score'] >= 0 and result['confidence_score'] <= 100, "Invalid confidence"
    assert 'comparables' in result, "Missing comparables"
    assert len(result['comparables']) > 0, "No comparables generated"
    assert 'market_statistics' in result, "Missing market statistics"

    print(f"✓ Estimated Value: ${result['estimated_value']:,}")
    print(f"✓ Confidence: {result['confidence_level']} ({result['confidence_score']}%)")
    print(f"✓ Price/Sqft: ${result['price_per_sqft']}")
    print(f"✓ Comparables: {result['comp_count']}")
    print("✓ PASSED")

    return True


def test_report_generator():
    """Test enhanced report generator"""
    print("\n" + "="*70)
    print("TEST 4: Enhanced Report Generator")
    print("="*70)

    # Generate sample data
    location_analyzer = LocationQualityAnalyzer()
    dev_analyzer = DevelopmentPressureAnalyzer()
    valuator = PropertyValuator()

    property_data = {
        'address': '43500 Tuckaway Pl, Leesburg, VA 20176',
        'lat': 39.0437,
        'lon': -77.4875,
        'sqft': 3200,
        'bedrooms': 4,
        'bathrooms': 3.5,
        'year_built': 2015,
        'lot_size_acres': 0.35,
        'latitude': 39.0437,
        'longitude': -77.4875
    }

    location_result = location_analyzer.analyze_location(39.0437, -77.4875, property_data['address'])
    development_result = dev_analyzer.calculate_development_pressure(39.0437, -77.4875)
    valuation_result = valuator.estimate_property_value(property_data)

    # Generate report
    generator = EnhancedReportGenerator()
    report_path = "test_comprehensive_report.html"

    generator.generate_comprehensive_report(
        property_data=property_data,
        valuation_result=valuation_result,
        location_result=location_result,
        development_result=development_result,
        output_path=report_path
    )

    # Assertions
    assert os.path.exists(report_path), "Report file not created"

    with open(report_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Check for key sections
    assert 'Location Quality' in html_content, "Missing Location Quality section"
    assert 'Development' in html_content or 'Development Pressure' in html_content, "Missing Development section"
    assert 'Executive Summary' in html_content, "Missing Executive Summary"
    assert 'map' in html_content.lower(), "Missing map"
    assert 'Chart.js' in html_content or 'chart' in html_content.lower(), "Missing charts"
    assert 'Leaflet' in html_content or 'leaflet' in html_content.lower(), "Missing Leaflet"
    assert property_data['address'] in html_content, "Address not in report"

    file_size = os.path.getsize(report_path)
    print(f"✓ Report generated: {report_path}")
    print(f"✓ File size: {file_size:,} bytes")
    print(f"✓ Contains all required sections")
    print("✓ PASSED")

    return True


def test_combined_analyzer_basic():
    """Test combined analyzer without valuation"""
    print("\n" + "="*70)
    print("TEST 5: Combined Analyzer (Basic - No Valuation)")
    print("="*70)

    analyzer = CombinedPropertyAnalyzer()

    start_time = time.time()
    result = analyzer.analyze_property(
        address="43500 Tuckaway Pl, Leesburg, VA 20176",
        lat=39.0437,
        lon=-77.4875
    )
    execution_time = time.time() - start_time

    # Assertions
    assert result['success'], "Analysis failed"
    assert result['location']['quality_score'] > 0, "Invalid location score"
    assert result['development']['pressure_score'] >= 0, "Invalid development score"
    assert os.path.exists(result['report_path']), "Report not generated"

    print(f"✓ Execution time: {execution_time:.2f}s")
    print(f"✓ Location Score: {result['location']['quality_score']}/10")
    print(f"✓ Development Pressure: {result['development']['pressure_score']}/100")
    print(f"✓ Report: {result['report_path']}")

    if execution_time < 5.0:
        print(f"✓ DEMO-READY: Completed in {execution_time:.2f}s (target: <5s)")
    else:
        print(f"⚠️  Execution time {execution_time:.2f}s exceeds 5s target")

    print("✓ PASSED")

    return True


def test_combined_analyzer_full():
    """Test combined analyzer with full valuation"""
    print("\n" + "="*70)
    print("TEST 6: Combined Analyzer (Full - With Valuation)")
    print("="*70)

    analyzer = CombinedPropertyAnalyzer()

    property_data = {
        'address': '43500 Tuckaway Pl, Leesburg, VA 20176',
        'sqft': 3200,
        'bedrooms': 4,
        'bathrooms': 3.5,
        'year_built': 2015,
        'lot_size_acres': 0.35
    }

    start_time = time.time()
    result = analyzer.analyze_property(
        address=property_data['address'],
        lat=39.0437,
        lon=-77.4875,
        property_data=property_data
    )
    execution_time = time.time() - start_time

    # Assertions
    assert result['success'], "Analysis failed"
    assert result['valuation']['estimated_value'] > 0, "Invalid valuation"
    assert result['location']['quality_score'] > 0, "Invalid location score"
    assert result['development']['pressure_score'] >= 0, "Invalid development score"
    assert os.path.exists(result['report_path']), "Report not generated"

    print(f"✓ Execution time: {execution_time:.2f}s")
    print(f"✓ Estimated Value: ${result['valuation']['estimated_value']:,}")
    print(f"✓ Location Score: {result['location']['quality_score']}/10")
    print(f"✓ Development Pressure: {result['development']['pressure_score']}/100")
    print(f"✓ Report: {result['report_path']}")

    if execution_time < 5.0:
        print(f"✓ DEMO-READY: Completed in {execution_time:.2f}s (target: <5s)")
    else:
        print(f"⚠️  Execution time {execution_time:.2f}s exceeds 5s target")

    print("✓ PASSED")

    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE PROPERTY ANALYSIS SYSTEM - TEST SUITE")
    print("="*70)
    print("\nRunning automated tests...")

    tests = [
        ("Location Quality Analyzer", test_location_analyzer),
        ("Development Pressure Analyzer", test_development_analyzer),
        ("Property Valuator", test_property_valuator),
        ("Enhanced Report Generator", test_report_generator),
        ("Combined Analyzer (Basic)", test_combined_analyzer_basic),
        ("Combined Analyzer (Full)", test_combined_analyzer_full),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ FAILED: {e}")

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    for test_name, success, error in results:
        status = "✓ PASSED" if success else f"❌ FAILED: {error}"
        print(f"{test_name:50s} {status}")

    print("\n" + "-"*70)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is DEMO-READY!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review errors above.")

    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
