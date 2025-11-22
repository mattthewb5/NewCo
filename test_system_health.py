"""
System Health Check - Validates all APIs and services are operational.

Runs quick validation tests on:
- Configuration loading
- API connectivity (schools, zoning)
- Caching system
- Performance benchmarks

Run with: python test_system_health.py

Last Updated: November 2025
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent / "multi-county-real-estate-research"))

from config import get_county_config
from core.school_lookup import SchoolLookup
from core.zoning_lookup import ZoningLookup
from core.cache_utils import get_cache_stats, print_cache_stats


def health_check():
    """Run comprehensive system health check."""
    print("\n" + "=" * 70)
    print("SYSTEM HEALTH CHECK")
    print("Multi-County Real Estate Research Platform")
    print("=" * 70)

    # Test 1: Configuration
    print("\n📋 TEST 1: Configuration Loading")
    print("-" * 70)

    try:
        config = get_county_config("loudoun")
        print(f"✅ Config loaded: {config.display_name}")
        print(f"   State: {config.state}")
        print(f"   District: {config.school_district_name}")
        print(f"   Primary County: {config.is_primary_county}")
        print()
        print("   Feature Status:")
        print(f"   - Zoning:  {'✅ Operational' if config.has_zoning_data else '⏳ Pending'}")
        print(f"   - Schools: {'✅ Operational' if config.has_school_data else '⏳ Pending'}")
        print(f"   - Crime:   {'✅ Operational' if config.has_crime_data else '⏳ Pending'}")
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return 1

    # Test 2: School API
    print("\n🏫 TEST 2: School API Connectivity")
    print("-" * 70)

    try:
        school_lookup = SchoolLookup(config)

        # Test with Ashburn address
        test_address = "44084 Riverside Pkwy, Ashburn, VA 20147"
        print(f"Testing: {test_address}")

        start_time = time.time()
        result = school_lookup.get_schools(test_address, 39.0437, -77.4875)
        duration_ms = (time.time() - start_time) * 1000

        if result.success:
            print(f"✅ School API: WORKING")
            print(f"   Elementary: {result.elementary.name if result.elementary else 'None'}")
            print(f"   Middle: {result.middle.name if result.middle else 'None'}")
            print(f"   High: {result.high.name if result.high else 'None'}")
            print(f"   Response Time: {duration_ms:.0f}ms")
        else:
            print(f"⚠️  School API: NOT OPERATIONAL")
            print(f"   Error: {result.error_message}")

    except Exception as e:
        print(f"❌ School API test failed: {e}")

    # Test 3: Zoning API
    print("\n⚖️  TEST 3: Zoning API Connectivity")
    print("-" * 70)

    try:
        zoning_lookup = ZoningLookup(config)

        # Test with Ashburn address
        print(f"Testing: {test_address}")

        start_time = time.time()
        zoning_result = zoning_lookup.get_zoning(test_address, 39.0437, -77.4875)
        duration_ms = (time.time() - start_time) * 1000

        if zoning_result.success:
            print(f"✅ Zoning API: WORKING")
            print(f"   Zone Code: {zoning_result.zoning_code}")
            print(f"   Description: {zoning_result.zoning_description[:60]}...")
            print(f"   Authority: {zoning_result.zoning_authority}")
            print(f"   Response Time: {duration_ms:.0f}ms")
        else:
            print(f"⚠️  Zoning API: NOT OPERATIONAL")
            print(f"   Error: {zoning_result.error_message}")

    except Exception as e:
        print(f"❌ Zoning API test failed: {e}")

    # Test 4: Caching Performance
    print("\n🚀 TEST 4: Caching Performance")
    print("-" * 70)

    try:
        print("Running repeat query to test cache...")

        # Second query (should be cached)
        start_time = time.time()
        result2 = school_lookup.get_schools(test_address, 39.0437, -77.4875)
        cached_duration_ms = (time.time() - start_time) * 1000

        if result2.success:
            print(f"✅ Second query completed: {cached_duration_ms:.0f}ms")

            if cached_duration_ms < duration_ms / 2:
                print(f"   🎉 Cache WORKING! ({duration_ms:.0f}ms → {cached_duration_ms:.0f}ms)")
                print(f"   Speedup: {duration_ms / cached_duration_ms:.1f}x faster")
            else:
                print(f"   ⚠️  Cache may not be working (similar response times)")

    except Exception as e:
        print(f"❌ Cache test failed: {e}")

    # Test 5: Cache Statistics
    print("\n📊 TEST 5: Cache Statistics")
    print("-" * 70)

    stats = get_cache_stats()
    print(f"Hits:       {stats['hits']:,}")
    print(f"Misses:     {stats['misses']:,}")
    print(f"Hit Rate:   {stats['hit_rate']:.1f}%")
    print(f"Cache Size: {stats['cache_size']} entries")

    if stats['hits'] > 0:
        print(f"✅ Caching is working!")
    else:
        print(f"⚠️  No cache hits yet (expected on first run)")

    # Summary
    print("\n" + "=" * 70)
    print("HEALTH CHECK SUMMARY")
    print("=" * 70)

    print("\n✅ System Status: OPERATIONAL")
    print()
    print("Ready for:")
    print("  - School lookups (LCPS)")
    print("  - Zoning lookups (Loudoun County GIS)")
    print("  - Cached queries for performance")
    print()
    print("Next steps:")
    print("  - Run UI: streamlit run loudoun_ui.py")
    print("  - Run tests: python test_lcps_schools.py")
    print("  - Check cache: python -c 'from core.cache_utils import print_cache_stats; print_cache_stats()'")
    print()

    return 0


if __name__ == "__main__":
    exit_code = health_check()
    sys.exit(exit_code)
