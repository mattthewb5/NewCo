"""
Test LCPS (Loudoun County Public Schools) School Assignments

Tests the LCPS school API integration with 5 known Loudoun County addresses.

Run with: python test_lcps_schools.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "multi-county-real-estate-research"))

from utils.lcps_school_api import get_school_assignments

# Test addresses
TEST_ADDRESSES = [
    ("Ashburn", "44084 Riverside Pkwy, Ashburn, VA 20147"),
    ("Sterling", "20921 Davenport Dr, Sterling, VA 20165"),
    ("Leesburg Downtown", "1 Harrison St SE, Leesburg, VA 20175"),
    ("Purcellville", "123 N 21st St, Purcellville, VA 20132"),
    ("Developer Test", "43423 Cloister Pl, Leesburg, VA 22075"),
]

print("="*70)
print("LCPS SCHOOL ASSIGNMENT TEST")
print("="*70)

results = []
for name, address in TEST_ADDRESSES:
    print(f"\nTesting: {name}")
    print(f"Address: {address}")
    result = get_school_assignments(address)
    
    if result:
        elem = result.get('elementary', {}).get('name', 'None')
        middle = result.get('middle', {}).get('name', 'None')
        high = result.get('high', {}).get('name', 'None')
        
        print(f"  Elementary: {elem}")
        print(f"  Middle: {middle}")
        print(f"  High: {high}")
        
        results.append({
            'name': name,
            'success': bool(elem != 'None' or middle != 'None' or high != 'None')
        })
    else:
        print("  ❌ FAILED")
        results.append({'name': name, 'success': False})

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
success = sum(1 for r in results if r['success'])
print(f"Passed: {success}/{len(results)}")
for r in results:
    status = "✅" if r['success'] else "❌"
    print(f"{status} {r['name']}")
