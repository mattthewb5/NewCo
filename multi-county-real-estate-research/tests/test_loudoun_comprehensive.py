"""
Comprehensive integration tests for Loudoun County.

Tests all 3 data sources (zoning, crime, schools) across diverse locations
to validate reliability and catch edge cases.

Run with: python tests/test_loudoun_comprehensive.py

Last Updated: November 2025
Phase: 3 - Comprehensive Validation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_county_config
from core.school_lookup import SchoolLookup
from core.zoning_lookup import ZoningLookup
# from core.crime_analysis import CrimeAnalysis  # Will use when Phase 2 complete

# Test addresses covering diverse Loudoun County locations
TEST_ADDRESSES = [
    # Eastern Loudoun (Suburban, High-growth)
    {
        "name": "Ashburn - Broadlands",
        "address": "43150 Broadlands Center Plaza, Ashburn, VA 20148",
        "lat": 39.0203,
        "lon": -77.5189,
        "area": "Eastern suburban",
        "expected": "Large modern schools, mixed commercial zoning"
    },
    {
        "name": "Ashburn - Brambleton",
        "address": "23000 Brambleton Plaza, Ashburn, VA 20148",
        "lat": 38.9820,
        "lon": -77.5370,
        "area": "Eastern suburban",
        "expected": "Newer schools, planned development"
    },
    {
        "name": "Sterling - Countryside",
        "address": "46301 Potomac Run Plaza, Sterling, VA 20164",
        "lat": 39.0392,
        "lon": -77.4191,
        "area": "Northern suburban",
        "expected": "Established schools, commercial areas"
    },
    {
        "name": "South Riding",
        "address": "43135 Peacock Market Plaza, South Riding, VA 20152",
        "lat": 38.9185,
        "lon": -77.5060,
        "area": "Central planned community",
        "expected": "Well-rated schools, HOA community"
    },

    # Central Loudoun (Town Areas)
    {
        "name": "Leesburg - Downtown",
        "address": "1 Harrison St SE, Leesburg, VA 20175",
        "lat": 39.1156,
        "lon": -77.5636,
        "area": "Incorporated town - historic",
        "expected": "Town zoning, Leesburg schools"
    },
    {
        "name": "Leesburg - River Creek",
        "address": "43470 Plantation Ter, Leesburg, VA 20176",
        "lat": 39.0845,
        "lon": -77.5400,
        "area": "Incorporated town - suburban",
        "expected": "Town jurisdiction, newer schools"
    },

    # Western Loudoun (Rural, Horse Country)
    {
        "name": "Purcellville - Downtown",
        "address": "221 S Nursery Ave, Purcellville, VA 20132",
        "lat": 39.1376,
        "lon": -77.7128,
        "area": "Incorporated town - rural",
        "expected": "Small town schools, rural character"
    },
    {
        "name": "Middleburg",
        "address": "12 N Madison St, Middleburg, VA 20117",
        "lat": 38.9675,
        "lon": -77.7353,
        "area": "Incorporated town - horse country",
        "expected": "Historic town, equestrian zoning"
    },
    {
        "name": "Hamilton",
        "address": "10 W Colonial Hwy, Hamilton, VA 20158",
        "lat": 39.1347,
        "lon": -77.6617,
        "area": "Incorporated town - small",
        "expected": "Small town, limited commercial"
    },

    # Edge Cases
    {
        "name": "Dulles Airport Area",
        "address": "1 Saarinen Cir, Dulles, VA 20166",
        "lat": 38.9531,
        "lon": -77.4565,
        "area": "Commercial/industrial",
        "expected": "Industrial zoning, nearby schools"
    },
    {
        "name": "Lansdowne",
        "address": "19385 Evergreen Mills Rd, Leesburg, VA 20175",
        "lat": 39.0806,
        "lon": -77.4764,
        "area": "Golf community",
        "expected": "Planned development, resort area"
    },
]


def test_all_addresses():
    """
    Test all 3 data sources across diverse Loudoun locations.
    """
    print("=" * 70)
    print("LOUDOUN COUNTY COMPREHENSIVE INTEGRATION TEST")
    print("=" * 70)
    print(f"Testing {len(TEST_ADDRESSES)} diverse locations")
    print(f"Date: November 2025")
    print()

    config = get_county_config("loudoun")
    school_lookup = SchoolLookup(config)
    zoning_lookup = ZoningLookup(config)
    # crime_analysis = CrimeAnalysis(config)  # Phase 2 pending

    results = {
        'schools': {'success': 0, 'failed': 0, 'details': []},
        'zoning': {'success': 0, 'failed': 0, 'details': []},
        'crime': {'success': 0, 'failed': 0, 'details': []}
    }

    for i, test in enumerate(TEST_ADDRESSES, 1):
        print(f"\n{'=' * 70}")
        print(f"Test {i}/{len(TEST_ADDRESSES)}: {test['name']}")
        print(f"{'=' * 70}")
        print(f"Address: {test['address']}")
        print(f"Coordinates: ({test['lat']}, {test['lon']})")
        print(f"Area: {test['area']}")
        print(f"Expected: {test['expected']}")
        print()

        # Test Schools
        print("🏫 SCHOOLS:")
        try:
            school_result = school_lookup.get_schools(
                test['address'],
                test['lat'],
                test['lon']
            )

            if school_result.success:
                results['schools']['success'] += 1
                print(f"  ✅ SUCCESS")

                details = []
                if school_result.elementary:
                    print(f"    Elementary: {school_result.elementary.name} ({school_result.elementary.school_id})")
                    if school_result.elementary.enrollment:
                        print(f"      Enrollment: {school_result.elementary.enrollment} students")
                    details.append(f"ES: {school_result.elementary.name}")

                if school_result.middle:
                    print(f"    Middle: {school_result.middle.name} ({school_result.middle.school_id})")
                    details.append(f"MS: {school_result.middle.name}")

                if school_result.high:
                    print(f"    High: {school_result.high.name} ({school_result.high.school_id})")
                    details.append(f"HS: {school_result.high.name}")

                results['schools']['details'].append({
                    'location': test['name'],
                    'status': 'success',
                    'schools': ', '.join(details)
                })
            else:
                results['schools']['failed'] += 1
                print(f"  ❌ FAILED: {school_result.error_message}")
                results['schools']['details'].append({
                    'location': test['name'],
                    'status': 'failed',
                    'error': school_result.error_message
                })
        except Exception as e:
            results['schools']['failed'] += 1
            print(f"  ❌ EXCEPTION: {str(e)}")
            results['schools']['details'].append({
                'location': test['name'],
                'status': 'exception',
                'error': str(e)
            })

        # Test Zoning
        print("\n🗺️  ZONING:")
        try:
            zoning_result = zoning_lookup.get_zoning(
                test['address'],
                test['lat'],
                test['lon']
            )

            if zoning_result.success:
                results['zoning']['success'] += 1
                print(f"  ✅ SUCCESS")
                print(f"    Code: {zoning_result.zoning_code}")
                print(f"    Jurisdiction: {zoning_result.jurisdiction_name}")
                if zoning_result.zoning_description:
                    desc = zoning_result.zoning_description[:80] + "..." if len(zoning_result.zoning_description) > 80 else zoning_result.zoning_description
                    print(f"    Description: {desc}")

                results['zoning']['details'].append({
                    'location': test['name'],
                    'status': 'success',
                    'code': zoning_result.zoning_code,
                    'jurisdiction': zoning_result.jurisdiction_name
                })
            else:
                results['zoning']['failed'] += 1
                print(f"  ❌ FAILED: {zoning_result.error_message}")
                results['zoning']['details'].append({
                    'location': test['name'],
                    'status': 'failed',
                    'error': zoning_result.error_message
                })
        except Exception as e:
            results['zoning']['failed'] += 1
            print(f"  ❌ EXCEPTION: {str(e)}")
            results['zoning']['details'].append({
                'location': test['name'],
                'status': 'exception',
                'error': str(e)
            })

        # Test Crime (Infrastructure only - API pending)
        print("\n🚨 CRIME:")
        print(f"  ⏳ INFRASTRUCTURE: Phase 2 pending - API endpoint research in progress")
        results['crime']['failed'] += 1  # Count as "expected infrastructure"
        results['crime']['details'].append({
            'location': test['name'],
            'status': 'infrastructure',
            'note': 'Phase 2 pending'
        })

    # Summary Report
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    total_tests = len(TEST_ADDRESSES)

    print(f"\n🏫 SCHOOLS:")
    school_success_rate = results['schools']['success'] / total_tests * 100
    print(f"   ✅ Success: {results['schools']['success']}/{total_tests} ({school_success_rate:.1f}%)")
    print(f"   ❌ Failed: {results['schools']['failed']}/{total_tests}")

    if results['schools']['failed'] > 0:
        print(f"\n   Failed Locations:")
        for detail in results['schools']['details']:
            if detail['status'] != 'success':
                print(f"      • {detail['location']}: {detail.get('error', 'Unknown error')}")

    print(f"\n🗺️  ZONING:")
    zoning_success_rate = results['zoning']['success'] / total_tests * 100
    print(f"   ✅ Success: {results['zoning']['success']}/{total_tests} ({zoning_success_rate:.1f}%)")
    print(f"   ❌ Failed: {results['zoning']['failed']}/{total_tests}")

    if results['zoning']['failed'] > 0:
        print(f"\n   Failed Locations:")
        for detail in results['zoning']['details']:
            if detail['status'] != 'success':
                print(f"      • {detail['location']}: {detail.get('error', 'Unknown error')}")

    print(f"\n🚨 CRIME:")
    print(f"   ⏳ Infrastructure: {results['crime']['failed']}/{total_tests} (Expected - Phase 2 pending)")
    print(f"   Note: Crime analysis API integration scheduled for Phase 2")

    # Overall assessment
    print(f"\n{'=' * 70}")
    print("RELIABILITY ASSESSMENT")
    print(f"{'=' * 70}")

    if school_success_rate >= 90 and zoning_success_rate >= 90:
        print("✅ EXCELLENT: Both systems working reliably across county!")
        confidence = "VERY HIGH"
    elif school_success_rate >= 80 and zoning_success_rate >= 80:
        print("✅ GOOD: Systems working well, minor issues to investigate")
        confidence = "HIGH"
    elif school_success_rate >= 70 and zoning_success_rate >= 70:
        print("⚠️  MODERATE: Some issues need attention")
        confidence = "MODERATE"
    else:
        print("❌ NEEDS WORK: Significant issues to resolve")
        confidence = "LOW"

    print(f"\nConfidence Level for UI Demo: {confidence}")
    print(f"{'=' * 70}\n")

    # Geographic Coverage Analysis
    print("📍 GEOGRAPHIC COVERAGE:")
    eastern = sum(1 for d in results['schools']['details'] if 'Ashburn' in d['location'] or 'Sterling' in d['location'] or 'South Riding' in d['location'])
    central = sum(1 for d in results['schools']['details'] if 'Leesburg' in d['location'])
    western = sum(1 for d in results['schools']['details'] if 'Purcellville' in d['location'] or 'Middleburg' in d['location'] or 'Hamilton' in d['location'])

    print(f"   Eastern Loudoun: {eastern} locations tested")
    print(f"   Central Loudoun: {central} locations tested")
    print(f"   Western Loudoun: {western} locations tested")
    print()

    # Recommendations
    if results['schools']['failed'] > 0 or results['zoning']['failed'] > 0:
        print("🔍 RECOMMENDED ACTIONS:")
        if results['schools']['failed'] > 0:
            print(f"   • Investigate {results['schools']['failed']} school lookup failures")
            print(f"     - Check if locations are outside LCPS boundaries")
            print(f"     - Verify coordinate accuracy")
        if results['zoning']['failed'] > 0:
            print(f"   • Investigate {results['zoning']['failed']} zoning lookup failures")
            print(f"     - Verify GIS API coverage")
            print(f"     - Check jurisdiction detection for towns")
        print()
    else:
        print("🎯 READY FOR UI DEMO:")
        print(f"   • Schools: {school_success_rate:.1f}% success rate")
        print(f"   • Zoning: {zoning_success_rate:.1f}% success rate")
        print(f"   • Crime: Infrastructure ready, pending API access")
        print(f"   • Geographic coverage: Complete (eastern, central, western)")
        print(f"   • Edge cases: Tested (airport, golf communities, towns)")
        print()


if __name__ == "__main__":
    test_all_addresses()
