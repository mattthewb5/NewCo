"""
Integration tests for LCPS School Locator API.

These tests query the real LCPS API via Loudoun County GIS.
They validate end-to-end functionality from coordinates to school assignments.

Test Locations:
- Ashburn (39.0437, -77.4875) - Eastern Loudoun, suburban
- Leesburg (39.1156, -77.5636) - Central Loudoun, town
- Purcellville (39.1376, -77.7128) - Western Loudoun, rural

Expected Results:
Based on research documented in docs/lcps_school_locator_research_FINDINGS.md

Last Updated: November 19, 2025
Phase: 3 - School Data
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_county_config
from core.school_lookup import SchoolLookup


def test_lcps_ashburn():
    """
    Test LCPS API with Ashburn coordinates.

    Expected schools based on API research:
    - Elementary: CEDAR LANE ES (code: CED, opened 1999)
    - Middle: TRAILSIDE MS (code: TMS, opened 2014)
    - High: STONE BRIDGE HS (code: SBH, opened 2000)
    """
    print("\n" + "=" * 70)
    print("TEST 1: ASHBURN, VA (EASTERN LOUDOUN)")
    print("=" * 70)

    config = get_county_config("loudoun")
    lookup = SchoolLookup(config)

    result = lookup.get_schools(
        address="Ashburn, VA",
        lat=39.0437,
        lon=-77.4875
    )

    print(f"\nAddress: Ashburn, VA")
    print(f"Coordinates: 39.0437, -77.4875")
    print(f"District: {result.district_name}")
    print(f"Success: {result.success}")
    print()

    # Verify API call succeeded
    assert result.success, f"API call failed: {result.error_message}"
    print("✅ API call succeeded")

    # Verify district
    assert result.district_name == "Loudoun County Public Schools (LCPS)", \
        f"Expected LCPS, got {result.district_name}"
    print("✅ District verified: LCPS")

    # Verify elementary school
    assert result.elementary is not None, "Elementary school not found"
    assert result.elementary.school_id == "CED", \
        f"Expected CED, got {result.elementary.school_id}"
    assert "CEDAR LANE" in result.elementary.name, \
        f"Expected CEDAR LANE, got {result.elementary.name}"
    assert result.elementary.school_type == "Elementary", \
        f"Expected Elementary, got {result.elementary.school_type}"

    print(f"\nElementary School:")
    print(f"  Name: {result.elementary.name}")
    print(f"  Code: {result.elementary.school_id}")
    print(f"  Type: {result.elementary.school_type}")
    print(f"  Info: {result.elementary.notes}")
    print("✅ Elementary school verified: CEDAR LANE ES")

    # Verify middle school
    assert result.middle is not None, "Middle school not found"
    assert result.middle.school_id == "TMS", \
        f"Expected TMS, got {result.middle.school_id}"
    assert "TRAILSIDE" in result.middle.name, \
        f"Expected TRAILSIDE, got {result.middle.name}"

    print(f"\nMiddle School:")
    print(f"  Name: {result.middle.name}")
    print(f"  Code: {result.middle.school_id}")
    print(f"  Type: {result.middle.school_type}")
    print(f"  Info: {result.middle.notes}")
    print("✅ Middle school verified: TRAILSIDE MS")

    # Verify high school
    assert result.high is not None, "High school not found"
    assert result.high.school_id == "SBH", \
        f"Expected SBH, got {result.high.school_id}"
    assert "STONE BRIDGE" in result.high.name, \
        f"Expected STONE BRIDGE, got {result.high.name}"

    print(f"\nHigh School:")
    print(f"  Name: {result.high.name}")
    print(f"  Code: {result.high.school_id}")
    print(f"  Type: {result.high.school_type}")
    print(f"  Info: {result.high.notes}")
    print("✅ High school verified: STONE BRIDGE HS")

    print(f"\n✅ PASS - All Ashburn schools verified!")


def test_lcps_leesburg():
    """
    Test LCPS API with Leesburg coordinates.

    Expected schools:
    - Elementary: LEESBURG ES (code: LEE)
    - Middle: SMART'S MILL MS (code: SMM)
    - High: TUSCARORA HS (code: THS)
    """
    print("\n" + "=" * 70)
    print("TEST 2: LEESBURG, VA (CENTRAL LOUDOUN)")
    print("=" * 70)

    config = get_county_config("loudoun")
    lookup = SchoolLookup(config)

    result = lookup.get_schools(
        address="Leesburg, VA",
        lat=39.1156,
        lon=-77.5636
    )

    print(f"\nAddress: Leesburg, VA")
    print(f"Coordinates: 39.1156, -77.5636")
    print(f"District: {result.district_name}")
    print(f"Success: {result.success}")
    print()

    # Verify API call succeeded
    assert result.success, f"API call failed: {result.error_message}"
    print("✅ API call succeeded")

    # Verify all three school levels assigned
    assert result.elementary is not None, "Elementary school not found"
    assert result.middle is not None, "Middle school not found"
    assert result.high is not None, "High school not found"

    print(f"\nSchool Assignment:")
    print(f"  Elementary: {result.elementary.name} ({result.elementary.school_id})")
    print(f"  Middle: {result.middle.name} ({result.middle.school_id})")
    print(f"  High: {result.high.name} ({result.high.school_id})")

    # Verify expected schools
    assert result.elementary.school_id == "LEE", \
        f"Expected LEE, got {result.elementary.school_id}"
    print("✅ Elementary verified: LEESBURG ES")

    assert result.middle.school_id == "SMM", \
        f"Expected SMM, got {result.middle.school_id}"
    print("✅ Middle verified: SMART'S MILL MS")

    assert result.high.school_id == "THS", \
        f"Expected THS, got {result.high.school_id}"
    print("✅ High verified: TUSCARORA HS")

    print(f"\n✅ PASS - All Leesburg schools verified!")


def test_lcps_purcellville():
    """
    Test LCPS API with Purcellville coordinates (western Loudoun).

    Expected schools:
    - Elementary: MOUNTAIN VIEW ES
    - Middle: BLUE RIDGE MS
    - High: LOUDOUN VALLEY HS
    """
    print("\n" + "=" * 70)
    print("TEST 3: PURCELLVILLE, VA (WESTERN LOUDOUN)")
    print("=" * 70)

    config = get_county_config("loudoun")
    lookup = SchoolLookup(config)

    result = lookup.get_schools(
        address="Purcellville, VA",
        lat=39.1376,
        lon=-77.7128
    )

    print(f"\nAddress: Purcellville, VA")
    print(f"Coordinates: 39.1376, -77.7128")
    print(f"District: {result.district_name}")
    print(f"Success: {result.success}")
    print()

    # Verify API call succeeded
    assert result.success, f"API call failed: {result.error_message}"
    print("✅ API call succeeded")

    # Verify all three school levels assigned
    assert result.elementary is not None, "Elementary school not found"
    assert result.middle is not None, "Middle school not found"
    assert result.high is not None, "High school not found"

    print(f"\nSchool Assignment:")
    print(f"  Elementary: {result.elementary.name} ({result.elementary.school_id})")
    print(f"  Middle: {result.middle.name} ({result.middle.school_id})")
    print(f"  High: {result.high.name} ({result.high.school_id})")

    # Verify expected schools
    assert "MOUNTAIN VIEW" in result.elementary.name, \
        f"Expected MOUNTAIN VIEW, got {result.elementary.name}"
    print("✅ Elementary verified: MOUNTAIN VIEW ES")

    assert "BLUE RIDGE" in result.middle.name, \
        f"Expected BLUE RIDGE, got {result.middle.name}"
    print("✅ Middle verified: BLUE RIDGE MS")

    assert "LOUDOUN VALLEY" in result.high.name, \
        f"Expected LOUDOUN VALLEY, got {result.high.name}"
    print("✅ High verified: LOUDOUN VALLEY HS")

    print(f"\n✅ PASS - All Purcellville schools verified!")


def test_lcps_data_quality():
    """
    Test data quality across all locations.

    Verifies:
    - School metadata is populated (names, codes, types)
    - Data source is tracked
    - Different locations get different schools
    - School types are correct
    """
    print("\n" + "=" * 70)
    print("TEST 4: DATA QUALITY VERIFICATION")
    print("=" * 70)

    config = get_county_config("loudoun")
    lookup = SchoolLookup(config)

    # Get all three locations
    ashburn = lookup.get_schools("Ashburn, VA", 39.0437, -77.4875)
    leesburg = lookup.get_schools("Leesburg, VA", 39.1156, -77.5636)
    purcellville = lookup.get_schools("Purcellville, VA", 39.1376, -77.7128)

    print("\n1. Verify all locations have complete assignments")
    locations = [
        ("Ashburn", ashburn),
        ("Leesburg", leesburg),
        ("Purcellville", purcellville)
    ]

    for name, result in locations:
        assert result.success, f"{name} lookup failed"
        assert result.elementary is not None, f"{name} missing elementary"
        assert result.middle is not None, f"{name} missing middle"
        assert result.high is not None, f"{name} missing high"
        print(f"  ✅ {name}: Complete (E/M/H)")

    print("\n2. Verify school metadata is populated")
    for name, result in locations:
        # Check elementary
        assert result.elementary.school_id, f"{name} elementary missing code"
        assert result.elementary.name, f"{name} elementary missing name"
        assert result.elementary.school_type == "Elementary", \
            f"{name} elementary wrong type"

        # Check middle
        assert result.middle.school_id, f"{name} middle missing code"
        assert result.middle.name, f"{name} middle missing name"
        assert result.middle.school_type == "Middle", \
            f"{name} middle wrong type"

        # Check high
        assert result.high.school_id, f"{name} high missing code"
        assert result.high.name, f"{name} high missing name"
        assert result.high.school_type == "High", \
            f"{name} high wrong type"

        print(f"  ✅ {name}: All metadata populated")

    print("\n3. Verify different locations get different schools")
    assert ashburn.elementary.school_id != leesburg.elementary.school_id, \
        "Ashburn and Leesburg should have different elementary schools"
    assert leesburg.high.school_id != purcellville.high.school_id, \
        "Leesburg and Purcellville should have different high schools"
    print("  ✅ Different locations have different schools")

    print("\n4. Verify data source tracking")
    for name, result in locations:
        assert result.data_source, f"{name} missing data source"
        assert "API" in result.data_source, f"{name} wrong data source"
        print(f"  ✅ {name}: Data source = {result.data_source}")

    print(f"\n✅ PASS - Data quality verified across all locations!")


if __name__ == "__main__":
    print("=" * 70)
    print("LCPS SCHOOL LOCATOR API - INTEGRATION TESTS")
    print("=" * 70)
    print("Date: November 19, 2025")
    print("Phase: 3 - School Data")
    print("API: Loudoun County GIS ArcGIS REST API")
    print()
    print("Testing real API calls with known coordinates...")
    print()

    try:
        # Run all tests
        test_lcps_ashburn()
        test_lcps_leesburg()
        test_lcps_purcellville()
        test_lcps_data_quality()

        # Summary
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED (4/4)")
        print("=" * 70)
        print()
        print("Summary:")
        print("  - Ashburn schools: ✅ Verified")
        print("  - Leesburg schools: ✅ Verified")
        print("  - Purcellville schools: ✅ Verified")
        print("  - Data quality: ✅ Verified")
        print()
        print("Phase 3 Status:")
        print("  - API endpoint: ✅ Working")
        print("  - Integration: ✅ Complete")
        print("  - Test coverage: ✅ Comprehensive")
        print("  - Real data: ✅ Validated")
        print()
        print("Next steps:")
        print("  - Document Phase 3 completion")
        print("  - Update PROJECT_SUMMARY.md")
        print("  - Create PR for Phase 3")
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
