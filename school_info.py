#!/usr/bin/env python3
"""
Combined School Information Lookup
Integrates street index with school performance data
"""

from dataclasses import dataclass
from typing import Optional
from street_index_lookup import lookup_school_district, SchoolAssignment
from school_performance import get_school_performance, format_performance_report, SchoolPerformance


@dataclass
class CompleteSchoolInfo:
    """Complete school information for an address"""
    address: str

    # School assignments
    elementary: str
    middle: str
    high: str

    # Performance data
    elementary_performance: Optional[SchoolPerformance] = None
    middle_performance: Optional[SchoolPerformance] = None
    high_performance: Optional[SchoolPerformance] = None

    # Match info
    street_matched: str = ""
    parameters_matched: str = ""


def get_school_info(address: str) -> Optional[CompleteSchoolInfo]:
    """
    Get complete school information for an address

    This function combines:
    - School district assignments (which schools serve this address)
    - School performance data (test scores, demographics, etc.)

    Args:
        address: Full address (e.g., "150 Hancock Avenue, Athens, GA 30601")

    Returns:
        CompleteSchoolInfo with both assignments and performance data
        None if address not found
    """
    # Step 1: Look up which schools serve this address
    assignment = lookup_school_district(address)

    if not assignment or not assignment.elementary:
        return None

    # Step 2: Get performance data for each school
    elementary_perf = get_school_performance(assignment.elementary)
    middle_perf = get_school_performance(assignment.middle)
    high_perf = get_school_performance(assignment.high)

    # Step 3: Combine into complete info
    info = CompleteSchoolInfo(
        address=address,
        elementary=assignment.elementary,
        middle=assignment.middle,
        high=assignment.high,
        elementary_performance=elementary_perf,
        middle_performance=middle_perf,
        high_performance=high_perf,
        street_matched=assignment.street_matched,
        parameters_matched=assignment.parameters_matched
    )

    return info


def format_complete_report(info: CompleteSchoolInfo) -> str:
    """Format a complete school info report"""
    lines = []

    # Header
    lines.append("\n" + "=" * 80)
    lines.append(f"SCHOOL INFORMATION FOR: {info.address}")
    lines.append("=" * 80)

    # School Assignments
    lines.append("\nSCHOOL ASSIGNMENTS:")
    lines.append("-" * 80)
    lines.append(f"  Elementary School: {info.elementary}")
    lines.append(f"  Middle School:     {info.middle}")
    lines.append(f"  High School:       {info.high}")

    if info.street_matched:
        lines.append(f"\n  Matched Street: {info.street_matched}")
        if info.parameters_matched:
            lines.append(f"  Parameters: {info.parameters_matched}")

    # Performance Reports
    lines.append("\n")
    lines.append("=" * 80)
    lines.append("SCHOOL PERFORMANCE DETAILS")
    lines.append("=" * 80)

    # Elementary
    if info.elementary_performance:
        lines.append("\n" + format_performance_report(info.elementary_performance))
    else:
        lines.append(f"\n{info.elementary}")
        lines.append("  (Performance data not available)")

    # Middle
    if info.middle_performance:
        lines.append("\n" + format_performance_report(info.middle_performance))
    else:
        lines.append(f"\n{info.middle}")
        lines.append("  (Performance data not available)")

    # High
    if info.high_performance:
        lines.append("\n" + format_performance_report(info.high_performance))
    else:
        lines.append(f"\n{info.high}")
        lines.append("  (Performance data not available)")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test with the three original addresses
    import sys

    test_addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "585 Reese Street, Athens, GA 30601",
        "195 Hoyt Street, Athens, GA 30601"
    ]

    # Allow user to provide address via command line
    if len(sys.argv) > 1:
        address = " ".join(sys.argv[1:])
        test_addresses = [address]

    for address in test_addresses:
        print(f"\n{'=' * 80}")
        print(f"Looking up: {address}")
        print('=' * 80)

        info = get_school_info(address)

        if info:
            print(format_complete_report(info))
        else:
            print(f"\n❌ Address not found: {address}")
            print("\nThis could mean:")
            print("  - The street is not in Athens-Clarke County")
            print("  - The street name couldn't be matched in the index")
            print("  - There's a typo in the street name")

        print("\n")
