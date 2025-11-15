#!/usr/bin/env python3
"""
Athens-Clarke County Zoning Lookup
Retrieves zoning and future land use information for properties
"""

import requests
from dataclasses import dataclass
from typing import Optional, List, Tuple
from geopy.geocoders import Nominatim


@dataclass
class ZoningInfo:
    """Container for zoning information"""
    # Property identification
    parcel_number: str
    pin: str
    address: str

    # Current zoning
    current_zoning: str
    current_zoning_description: str
    combined_zoning: str
    split_zoned: bool

    # Future land use
    future_land_use: str
    future_land_use_description: str
    future_changed: bool

    # Property details
    acres: float

    # Nearby parcels context
    nearby_zones: List[str]
    nearby_future_use: List[str]

    # Coordinates
    latitude: float
    longitude: float


def get_zoning_code_description(code: str) -> str:
    """
    Get human-readable description of zoning code

    Args:
        code: Zoning code (e.g., "RS-8", "C-D", "G")

    Returns:
        Description of the zoning classification
    """
    zoning_descriptions = {
        # Residential - Single Family
        'RS-40': 'Single-Family Residential (40,000 sq ft minimum lot)',
        'RS-25': 'Single-Family Residential (25,000 sq ft minimum lot)',
        'RS-15': 'Single-Family Residential (15,000 sq ft minimum lot)',
        'RS-8': 'Single-Family Residential (8,000 sq ft minimum lot)',
        'RS-5': 'Single-Family Residential (5,000 sq ft minimum lot)',

        # Residential - Multi-Family
        'RM-1': 'Multi-Family Residential (Low Density)',
        'RM-2': 'Multi-Family Residential (Medium Density)',
        'RM-3': 'Multi-Family Residential (High Density)',

        # Commercial
        'C-N': 'Commercial-Neighborhood (Local retail and services)',
        'C-G': 'Commercial-General (Broad range of commercial uses)',
        'C-D': 'Commercial-Downtown (Downtown core commercial)',
        'C-R': 'Commercial-Regional (Large-scale retail)',

        # Mixed Use
        'MU': 'Mixed Use (Residential and commercial)',
        'MU-C': 'Mixed Use-Commercial',
        'MU-R': 'Mixed Use-Residential',

        # Industrial
        'I-N': 'Industrial-Neighborhood (Light industrial)',
        'I-G': 'Industrial-General (Heavy industrial)',

        # Government/Institutional
        'G': 'Government/Institutional',
        'G-I': 'Government-Institutional',

        # Agricultural
        'A-R': 'Agricultural-Residential',

        # Special
        'PUD': 'Planned Unit Development',
        'PRD': 'Planned Residential Development',
    }

    # Try exact match first
    if code in zoning_descriptions:
        return zoning_descriptions[code]

    # Try partial match for variants
    code_upper = code.upper().strip()
    for key, description in zoning_descriptions.items():
        if code_upper.startswith(key):
            return description

    # Default if unknown
    return f"Zoning: {code}"


def get_future_land_use_description(land_use: str) -> str:
    """
    Get human-readable description of future land use

    Args:
        land_use: Future land use designation

    Returns:
        Description of planned future use
    """
    future_use_descriptions = {
        'Single-Family Residential': 'Planned for detached single-family homes',
        'Multi-Family Residential': 'Planned for apartments or condos',
        'Mixed Residential': 'Planned for variety of housing types',
        'Neighborhood Commercial': 'Planned for local shops and services',
        'General Commercial': 'Planned for broader commercial development',
        'Downtown Commercial': 'Planned for downtown-style development',
        'Office': 'Planned for office buildings',
        'Industrial': 'Planned for industrial/manufacturing uses',
        'Government': 'Planned for public/institutional uses',
        'Parks and Recreation': 'Planned for parks, trails, recreation',
        'Conservation': 'Planned for environmental conservation',
        'Mixed Use': 'Planned for combination of residential and commercial',
    }

    # Try exact match
    if land_use in future_use_descriptions:
        return future_use_descriptions[land_use]

    # Try case-insensitive partial match
    land_use_lower = land_use.lower()
    for key, description in future_use_descriptions.items():
        if key.lower() in land_use_lower or land_use_lower in key.lower():
            return description

    # Default
    return f"Planned for: {land_use}"


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert address to lat/lon coordinates

    Args:
        address: Street address

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    try:
        geolocator = Nominatim(user_agent="athens_home_buyer_research")

        # Add Athens, GA if not present
        if 'athens' not in address.lower():
            address = f"{address}, Athens, GA"

        location = geolocator.geocode(address, timeout=10)

        if location:
            return (location.latitude, location.longitude)
        else:
            return None

    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def query_zoning_api(latitude: float, longitude: float, distance_meters: int = 100) -> Optional[dict]:
    """
    Query the Parcel Zoning Types API

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        distance_meters: Search radius in meters (default 100)

    Returns:
        API response dict or None if error
    """
    url = "https://enigma.accgov.com/server/rest/services/Parcel_Zoning_Types/FeatureServer/0/query"

    params = {
        'geometry': f'{longitude},{latitude}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',  # WGS84 (standard lat/lon)
        'distance': distance_meters,
        'units': 'esriSRUnit_Meter',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',  # We don't need polygon geometry
        'f': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Zoning API error: {e}")
        return None


def query_future_land_use_api(latitude: float, longitude: float, distance_meters: int = 100) -> Optional[dict]:
    """
    Query the Future Land Use API

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        distance_meters: Search radius in meters (default 100)

    Returns:
        API response dict or None if error
    """
    url = "https://enigma.accgov.com/server/rest/services/FutureLandUse/FeatureServer/0/query"

    params = {
        'geometry': f'{longitude},{latitude}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',  # WGS84 (standard lat/lon)
        'distance': distance_meters,
        'units': 'esriSRUnit_Meter',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',  # We don't need polygon geometry
        'f': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Future Land Use API error: {e}")
        return None


def get_zoning_info(address: str) -> Optional[ZoningInfo]:
    """
    Get comprehensive zoning information for an address

    Args:
        address: Street address in Athens-Clarke County

    Returns:
        ZoningInfo object or None if address not found
    """
    # Step 1: Geocode the address
    coords = geocode_address(address)
    if not coords:
        print(f"Could not geocode address: {address}")
        return None

    latitude, longitude = coords
    print(f"Geocoded to: ({latitude}, {longitude})")

    # Step 2: Query zoning API
    zoning_data = query_zoning_api(latitude, longitude, distance_meters=50)
    if not zoning_data or not zoning_data.get('features'):
        print("No zoning data found")
        return None

    # Step 3: Query future land use API
    future_data = query_future_land_use_api(latitude, longitude, distance_meters=50)

    # Step 4: Find the closest parcel (usually the first one)
    primary_parcel = zoning_data['features'][0]['attributes']

    # Extract zoning info
    current_zoning = primary_parcel.get('CurrentZn', '').strip()
    combined_zoning = primary_parcel.get('CombinedZn', '').strip()
    parcel_number = primary_parcel.get('PARCEL_NO', '').strip()
    pin = primary_parcel.get('PIN', '').strip()
    acres = primary_parcel.get('Acres', 0.0)
    split_zoned = primary_parcel.get('SplitZoned', '').strip() != ''

    # Get description
    current_zoning_description = get_zoning_code_description(current_zoning)

    # Extract future land use
    future_land_use = ''
    future_land_use_description = ''
    future_changed = False

    if future_data and future_data.get('features'):
        future_parcel = future_data['features'][0]['attributes']
        future_land_use = future_parcel.get('Updated_FL', '').strip()
        future_changed = future_parcel.get('Change', '').strip().lower() == 'yes'
        future_land_use_description = get_future_land_use_description(future_land_use)

    # Get nearby parcels for context
    nearby_zones = []
    nearby_future_use = []

    # Collect nearby zoning codes (excluding the primary parcel)
    for feature in zoning_data['features'][1:]:
        zone = feature['attributes'].get('CurrentZn', '').strip()
        if zone and zone not in nearby_zones:
            nearby_zones.append(zone)

    # Collect nearby future land use
    if future_data and future_data.get('features'):
        for feature in future_data['features'][1:]:
            use = feature['attributes'].get('Updated_FL', '').strip()
            if use and use not in nearby_future_use:
                nearby_future_use.append(use)

    # Create ZoningInfo object
    zoning_info = ZoningInfo(
        parcel_number=parcel_number,
        pin=pin,
        address=address,
        current_zoning=current_zoning,
        current_zoning_description=current_zoning_description,
        combined_zoning=combined_zoning,
        split_zoned=split_zoned,
        future_land_use=future_land_use,
        future_land_use_description=future_land_use_description,
        future_changed=future_changed,
        acres=acres,
        nearby_zones=nearby_zones[:5],  # Limit to 5 nearest
        nearby_future_use=nearby_future_use[:5],
        latitude=latitude,
        longitude=longitude
    )

    return zoning_info


def format_zoning_report(zoning_info: ZoningInfo) -> str:
    """
    Format zoning information as a readable text report

    Args:
        zoning_info: ZoningInfo object

    Returns:
        Formatted text report
    """
    report = []
    report.append("=" * 80)
    report.append("ZONING INFORMATION")
    report.append("=" * 80)
    report.append("")

    report.append(f"Address: {zoning_info.address}")
    report.append(f"Parcel: {zoning_info.parcel_number}")
    report.append(f"PIN: {zoning_info.pin}")
    report.append("")

    report.append("CURRENT ZONING:")
    report.append(f"  Code: {zoning_info.current_zoning}")
    report.append(f"  Description: {zoning_info.current_zoning_description}")
    if zoning_info.split_zoned:
        report.append("  ⚠️  Property has split zoning")
    if zoning_info.combined_zoning and zoning_info.combined_zoning != zoning_info.current_zoning:
        report.append(f"  Combined: {zoning_info.combined_zoning}")
    report.append("")

    report.append("FUTURE LAND USE:")
    report.append(f"  Designation: {zoning_info.future_land_use}")
    report.append(f"  Description: {zoning_info.future_land_use_description}")
    if zoning_info.future_changed:
        report.append("  📝 Future land use plan has been updated/changed")
    report.append("")

    report.append("PROPERTY SIZE:")
    report.append(f"  {zoning_info.acres:.2f} acres ({int(zoning_info.acres * 43560)} square feet)")
    report.append("")

    if zoning_info.nearby_zones:
        report.append("NEARBY ZONING:")
        for zone in zoning_info.nearby_zones:
            description = get_zoning_code_description(zone)
            report.append(f"  • {zone}: {description}")
        report.append("")

    if zoning_info.nearby_future_use:
        report.append("NEARBY FUTURE LAND USE:")
        for use in zoning_info.nearby_future_use:
            report.append(f"  • {use}")
        report.append("")

    report.append(f"Coordinates: ({zoning_info.latitude:.4f}, {zoning_info.longitude:.4f})")
    report.append("")

    return "\n".join(report)


# Test function
def test_zoning_lookup():
    """Test the zoning lookup with sample addresses"""
    test_addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "1398 W Hancock Avenue, Athens, GA 30606",
        "220 College Station Road, Athens, GA 30602",
    ]

    for address in test_addresses:
        print("\n" + "=" * 80)
        print(f"Testing: {address}")
        print("=" * 80)

        zoning_info = get_zoning_info(address)

        if zoning_info:
            print(format_zoning_report(zoning_info))
        else:
            print(f"❌ Could not retrieve zoning information for: {address}")


if __name__ == "__main__":
    test_zoning_lookup()
