#!/usr/bin/env python3
"""
Test the property valuation system with sample addresses.
"""

import logging
from valuation import PropertyValuator
from generate_sample_data import populate_database
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Test properties in Loudoun County
TEST_PROPERTIES = [
    {
        'address': '43423 Cloister Pl, Ashburn, VA 20147',
        'latitude': 39.0450,
        'longitude': -77.4890,
        'sqft': 3200,
        'bedrooms': 4,
        'bathrooms': 3.5,
        'year_built': 2015,
        'lot_size_acres': 0.35,
        'has_pool': 0,
        'has_garage': 1,
        'property_type': 'Single Family',
        'zip_code': '20147'
    },
    {
        'address': '12345 Riverside Pkwy, Ashburn, VA 20148',
        'latitude': 39.0220,
        'longitude': -77.4810,
        'sqft': 2800,
        'bedrooms': 3,
        'bathrooms': 2.5,
        'year_built': 2010,
        'lot_size_acres': 0.25,
        'has_pool': 1,
        'has_garage': 1,
        'property_type': 'Single Family',
        'zip_code': '20148'
    },
    {
        'address': '5678 Davenport Dr, Sterling, VA 20165',
        'latitude': 39.0070,
        'longitude': -77.4290,
        'sqft': 2200,
        'bedrooms': 3,
        'bathrooms': 2.0,
        'year_built': 2005,
        'lot_size_acres': 0.20,
        'has_pool': 0,
        'has_garage': 1,
        'property_type': 'Townhouse',
        'zip_code': '20165'
    },
    {
        'address': '9876 Harrison St, Leesburg, VA 20175',
        'latitude': 39.1160,
        'longitude': -77.5640,
        'sqft': 2600,
        'bedrooms': 4,
        'bathrooms': 2.5,
        'year_built': 2000,
        'lot_size_acres': 0.40,
        'has_pool': 0,
        'has_garage': 1,
        'property_type': 'Single Family',
        'zip_code': '20175'
    },
    {
        'address': '4321 Main St, Purcellville, VA 20132',
        'latitude': 39.1370,
        'longitude': -77.7150,
        'sqft': 2400,
        'bedrooms': 3,
        'bathrooms': 2.0,
        'year_built': 1995,
        'lot_size_acres': 1.00,
        'has_pool': 0,
        'has_garage': 1,
        'property_type': 'Single Family',
        'zip_code': '20132'
    }
]


def test_single_property(valuator, property_data, show_details=True):
    """Test valuation for a single property."""
    print(f"\n{'='*80}")
    print(f"VALUING: {property_data['address']}")
    print(f"{'='*80}")
    print(f"Property Details:")
    print(f"  Square Feet:    {property_data['sqft']:,}")
    print(f"  Bedrooms:       {property_data['bedrooms']}")
    print(f"  Bathrooms:      {property_data['bathrooms']}")
    print(f"  Year Built:     {property_data['year_built']}")
    print(f"  Lot Size:       {property_data['lot_size_acres']} acres")
    print(f"  Pool:           {'Yes' if property_data.get('has_pool') else 'No'}")
    print(f"  Garage:         {'Yes' if property_data.get('has_garage') else 'No'}")
    print(f"  ZIP Code:       {property_data['zip_code']}")

    # Run valuation
    result = valuator.estimate_property_value(property_data)

    if not result:
        print("\n❌ Valuation failed - insufficient data")
        return None

    # Display results
    print(f"\n{'='*80}")
    print("VALUATION RESULTS")
    print(f"{'='*80}")
    print(f"\n💰 Estimated Value:    ${result['estimated_value']:,}")
    print(f"📊 Confidence Range:   ${result['confidence_range'][0]:,} - ${result['confidence_range'][1]:,}")
    print(f"✅ Confidence Score:   {result['confidence_score']}/100")
    print(f"🏠 Comparables Used:   {len(result['comps_used'])}")

    # Market factors
    print(f"\n📈 MARKET FACTORS (ZIP {property_data['zip_code']}):")
    mf = result['market_factors']
    print(f"  Price/sqft:           ${mf['price_per_sqft']:.2f}")
    print(f"  Bedroom value:        ${mf['bedroom_value']:,.0f}")
    print(f"  Bathroom value:       ${mf['bathroom_value']:,.0f}")
    print(f"  Lot value/acre:       ${mf['lot_value_per_acre']:,.0f}")
    print(f"  Age depreciation:     {mf['age_depreciation_rate']*100:.2f}% per year")
    print(f"  Pool premium:         ${mf['pool_premium']:,.0f}")
    print(f"  Garage premium:       ${mf['garage_premium']:,.0f}")
    print(f"  Monthly appreciation: {mf['monthly_appreciation']*100:.2f}%")
    print(f"  Sample size:          {mf['sample_size']} sales")

    if show_details:
        # Top 3 comparables
        print(f"\n🔍 TOP COMPARABLES:")
        for i, comp in enumerate(result['comps_used'][:3], 1):
            print(f"\n  {i}. {comp['address']}")
            print(f"     Sale Price:    ${comp['sale_price']:,}  ({comp['sale_date']})")
            print(f"     Adjusted:      ${comp['adjusted_price']:,}")
            print(f"     Similarity:    {comp['similarity_score']}/100")
            print(f"     Distance:      {comp['distance_miles']} miles")
            print(f"     Size:          {comp['sqft']:,} sqft, {comp['bedrooms']}BR/{comp['bathrooms']}BA")

            if comp['adjustments']:
                print(f"     Adjustments:")
                for adj_type, adj_value in comp['adjustments'].items():
                    if adj_value != 0:
                        sign = '+' if adj_value > 0 else ''
                        print(f"       {adj_type.capitalize():12s}: {sign}${adj_value:,}")

    print(f"\n{'='*80}\n")

    return result


def main():
    """Main test function."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              LOUDOUN COUNTY PROPERTY VALUATION SYSTEM - TEST                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    # Step 1: Populate database with sample data
    print("Step 1: Generating sample data...")
    print("-" * 80)
    populate_database(
        db_path="loudoun_sales.db",
        num_sales=200,
        clear_existing=True
    )

    # Step 2: Test valuations
    print(f"\n\nStep 2: Running valuations on {len(TEST_PROPERTIES)} test properties...")
    print("-" * 80)

    results = []
    with PropertyValuator("loudoun_sales.db") as valuator:
        for i, property_data in enumerate(TEST_PROPERTIES, 1):
            result = test_single_property(valuator, property_data, show_details=(i <= 2))
            if result:
                results.append(result)

            if i < len(TEST_PROPERTIES):
                input("\nPress Enter to continue to next property...")

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Properties tested:     {len(TEST_PROPERTIES)}")
    print(f"Successful valuations: {len(results)}")
    print(f"Average confidence:    {sum(r['confidence_score'] for r in results) / len(results):.1f}/100")

    # Save results to file
    output_file = "valuation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")

    print(f"\n{'='*80}")
    print("TEST COMPLETE ✓")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
