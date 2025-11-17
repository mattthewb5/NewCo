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


@dataclass
class NearbyZoning:
    """Container for nearby zoning analysis"""
    # Current property
    current_parcel: Optional[ZoningInfo]

    # Surrounding parcels
    nearby_parcels: List[ZoningInfo]

    # Analysis flags
    mixed_use_nearby: bool
    residential_only: bool
    commercial_nearby: bool
    industrial_nearby: bool

    # Identified concerns
    potential_concerns: List[str]

    # Summary metrics
    total_nearby_parcels: int
    unique_zones: List[str]
    zone_diversity_score: float  # 0.0 (all same) to 1.0 (all different)


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


def _is_residential(zoning_code: str) -> bool:
    """
    Check if a zoning code is residential

    Args:
        zoning_code: Zoning code to check

    Returns:
        True if residential, False otherwise
    """
    if not zoning_code:
        return False

    code_upper = zoning_code.upper().strip()

    # Residential patterns
    residential_prefixes = ['RS-', 'RM-', 'R-', 'A-R', 'PRD']

    for prefix in residential_prefixes:
        if code_upper.startswith(prefix):
            return True

    return False


def _is_commercial_or_mixed(zoning_code: str) -> bool:
    """
    Check if a zoning code is commercial or mixed use

    Args:
        zoning_code: Zoning code to check

    Returns:
        True if commercial/mixed, False otherwise
    """
    if not zoning_code:
        return False

    code_upper = zoning_code.upper().strip()

    # Commercial and mixed use patterns
    commercial_prefixes = ['C-', 'MU-', 'MU']

    for prefix in commercial_prefixes:
        if code_upper.startswith(prefix):
            return True

    # Exact matches for mixed use
    if code_upper in ['MU', 'MIXED USE']:
        return True

    return False


def _is_industrial(zoning_code: str) -> bool:
    """
    Check if a zoning code is industrial

    Args:
        zoning_code: Zoning code to check

    Returns:
        True if industrial, False otherwise
    """
    if not zoning_code:
        return False

    code_upper = zoning_code.upper().strip()

    # Industrial patterns
    industrial_prefixes = ['I-', 'IN-', 'IND-']

    for prefix in industrial_prefixes:
        if code_upper.startswith(prefix):
            return True

    return False


def _identify_concerns(current_zoning: Optional[ZoningInfo], nearby_parcels: List[ZoningInfo]) -> List[str]:
    """
    Identify potential zoning concerns

    Args:
        current_zoning: The current property's zoning info
        nearby_parcels: List of nearby parcel zoning info

    Returns:
        List of concern strings
    """
    concerns = []

    if not current_zoning:
        return concerns

    current_code = current_zoning.current_zoning
    current_is_residential = _is_residential(current_code)

    # Check for residential next to commercial
    if current_is_residential:
        commercial_nearby = [p for p in nearby_parcels if _is_commercial_or_mixed(p.current_zoning)]
        if commercial_nearby:
            concerns.append(f"Residential property has {len(commercial_nearby)} commercial/mixed-use parcel(s) nearby")

    # Check for residential next to industrial
    if current_is_residential:
        industrial_nearby = [p for p in nearby_parcels if _is_industrial(p.current_zoning)]
        if industrial_nearby:
            concerns.append(f"Residential property has {len(industrial_nearby)} industrial parcel(s) nearby - potential noise/traffic concerns")

    # Check for future land use changes
    if current_zoning.future_changed:
        concerns.append(f"Future land use plan has been updated - area may be in transition")

    # Check if future land use differs significantly from current zoning
    if current_is_residential and current_zoning.future_land_use:
        future_lower = current_zoning.future_land_use.lower()
        if 'commercial' in future_lower or 'mixed' in future_lower:
            concerns.append(f"Future land use ({current_zoning.future_land_use}) differs from current residential zoning - possible redevelopment area")

    # Check for split zoning
    if current_zoning.split_zoned:
        concerns.append("Property has split zoning - different regulations apply to different parts")

    # Check for very diverse nearby zoning (might indicate transitional area)
    unique_zones = set(p.current_zoning for p in nearby_parcels if p.current_zoning)
    if len(unique_zones) >= 5:
        concerns.append(f"High zoning diversity nearby ({len(unique_zones)} different zones) - may indicate transitional neighborhood")

    return concerns


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


def get_nearby_zoning(address: str, radius_meters: int = 250) -> Optional[NearbyZoning]:
    """
    Get comprehensive nearby zoning analysis for an address

    Args:
        address: Street address in Athens-Clarke County
        radius_meters: Search radius in meters (default: 250)

    Returns:
        NearbyZoning object with detailed analysis or None if address not found
    """
    # Step 1: Get the current parcel's zoning
    current_parcel = get_zoning_info(address)
    if not current_parcel:
        print(f"Could not get zoning for address: {address}")
        return None

    # Step 2: Query for nearby parcels with wider radius
    latitude, longitude = current_parcel.latitude, current_parcel.longitude

    zoning_data = query_zoning_api(latitude, longitude, distance_meters=radius_meters)
    future_data = query_future_land_use_api(latitude, longitude, distance_meters=radius_meters)

    if not zoning_data or not zoning_data.get('features'):
        print("No nearby zoning data found")
        return None

    # Step 3: Build ZoningInfo objects for all nearby parcels
    nearby_parcels = []

    for feature in zoning_data['features']:
        attrs = feature['attributes']

        # Skip the current parcel (match by PIN or parcel number)
        pin = attrs.get('PIN', '') or ''
        pin = pin.strip() if pin else ''
        if pin and pin == current_parcel.pin:
            continue

        parcel_number = attrs.get('PARCEL_NO', '') or ''
        parcel_number = parcel_number.strip() if parcel_number else ''
        if parcel_number and parcel_number == current_parcel.parcel_number:
            continue

        # Extract zoning info (handle None values)
        current_zoning = attrs.get('CurrentZn', '') or ''
        current_zoning = current_zoning.strip() if current_zoning else ''

        combined_zoning = attrs.get('CombinedZn', '') or ''
        combined_zoning = combined_zoning.strip() if combined_zoning else ''

        acres = attrs.get('Acres', 0.0) or 0.0

        split_zoned_value = attrs.get('SplitZoned', '') or ''
        split_zoned = str(split_zoned_value).strip() != ''

        # Get description
        current_zoning_description = get_zoning_code_description(current_zoning)

        # Try to find matching future land use
        future_land_use = ''
        future_land_use_description = ''
        future_changed = False

        if future_data and future_data.get('features'):
            for future_feature in future_data['features']:
                future_attrs = future_feature['attributes']
                if future_attrs.get('PARCEL_NO', '').strip() == parcel_number:
                    future_land_use = future_attrs.get('Updated_FL', '') or ''
                    future_land_use = future_land_use.strip() if future_land_use else ''
                    change_value = future_attrs.get('Change', '') or ''
                    future_changed = str(change_value).strip().lower() == 'yes'
                    future_land_use_description = get_future_land_use_description(future_land_use)
                    break

        # Create ZoningInfo for this nearby parcel
        nearby_info = ZoningInfo(
            parcel_number=parcel_number,
            pin=pin,
            address=f"Near {address}",
            current_zoning=current_zoning,
            current_zoning_description=current_zoning_description,
            combined_zoning=combined_zoning,
            split_zoned=split_zoned,
            future_land_use=future_land_use,
            future_land_use_description=future_land_use_description,
            future_changed=future_changed,
            acres=acres,
            nearby_zones=[],  # Not needed for nearby parcels
            nearby_future_use=[],
            latitude=latitude,
            longitude=longitude
        )

        nearby_parcels.append(nearby_info)

    # Step 4: Analyze the zoning patterns
    total_nearby = len(nearby_parcels)
    unique_zones = list(set(p.current_zoning for p in nearby_parcels if p.current_zoning))

    # Calculate diversity score
    if total_nearby > 0:
        zone_diversity_score = len(unique_zones) / total_nearby
    else:
        zone_diversity_score = 0.0

    # Check for different use types
    mixed_use_nearby = any(_is_commercial_or_mixed(p.current_zoning) for p in nearby_parcels)
    residential_only = all(_is_residential(p.current_zoning) for p in nearby_parcels) if nearby_parcels else False
    commercial_nearby = any(_is_commercial_or_mixed(p.current_zoning) for p in nearby_parcels)
    industrial_nearby = any(_is_industrial(p.current_zoning) for p in nearby_parcels)

    # Identify potential concerns
    potential_concerns = _identify_concerns(current_parcel, nearby_parcels)

    # Step 5: Create NearbyZoning object
    nearby_zoning = NearbyZoning(
        current_parcel=current_parcel,
        nearby_parcels=nearby_parcels,
        mixed_use_nearby=mixed_use_nearby,
        residential_only=residential_only,
        commercial_nearby=commercial_nearby,
        industrial_nearby=industrial_nearby,
        potential_concerns=potential_concerns,
        total_nearby_parcels=total_nearby,
        unique_zones=unique_zones,
        zone_diversity_score=zone_diversity_score
    )

    return nearby_zoning


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


def format_nearby_zoning_report(nearby_zoning: NearbyZoning) -> str:
    """
    Format nearby zoning analysis as a readable text report

    Args:
        nearby_zoning: NearbyZoning object

    Returns:
        Formatted text report
    """
    report = []
    report.append("=" * 80)
    report.append("NEARBY ZONING ANALYSIS")
    report.append("=" * 80)
    report.append("")

    if nearby_zoning.current_parcel:
        current = nearby_zoning.current_parcel
        report.append(f"Address: {current.address}")
        report.append(f"Current Zoning: {current.current_zoning} - {current.current_zoning_description}")
        report.append("")

    # Summary statistics
    report.append("NEIGHBORHOOD ZONING SUMMARY:")
    report.append(f"  Total Nearby Parcels: {nearby_zoning.total_nearby_parcels}")
    report.append(f"  Unique Zoning Types: {len(nearby_zoning.unique_zones)}")
    report.append(f"  Zone Diversity Score: {nearby_zoning.zone_diversity_score:.2f} (0.0=uniform, 1.0=all different)")
    report.append("")

    # Zoning pattern flags
    report.append("ZONING PATTERNS:")
    if nearby_zoning.residential_only:
        report.append("  ✓ Residential Only - All nearby parcels are residential")
    if nearby_zoning.commercial_nearby:
        report.append("  ⚠️  Commercial/Mixed Use Nearby")
    if nearby_zoning.industrial_nearby:
        report.append("  ⚠️  Industrial Zoning Nearby")
    if nearby_zoning.mixed_use_nearby:
        report.append("  • Mixed Use Development Nearby")
    report.append("")

    # Unique zones breakdown
    if nearby_zoning.unique_zones:
        report.append("NEARBY ZONING TYPES:")
        for zone in sorted(nearby_zoning.unique_zones):
            description = get_zoning_code_description(zone)
            count = sum(1 for p in nearby_zoning.nearby_parcels if p.current_zoning == zone)
            report.append(f"  • {zone}: {description} ({count} parcels)")
        report.append("")

    # Potential concerns
    if nearby_zoning.potential_concerns:
        report.append("⚠️  POTENTIAL CONCERNS:")
        for i, concern in enumerate(nearby_zoning.potential_concerns, 1):
            report.append(f"  {i}. {concern}")
        report.append("")
    else:
        report.append("✓ No significant zoning concerns identified")
        report.append("")

    # Detailed nearby parcel list (limit to first 10)
    if nearby_zoning.nearby_parcels:
        report.append("NEARBY PARCELS (showing up to 10):")
        for i, parcel in enumerate(nearby_zoning.nearby_parcels[:10], 1):
            report.append(f"  {i}. Parcel {parcel.parcel_number}")
            report.append(f"     Zoning: {parcel.current_zoning} - {parcel.current_zoning_description}")
            report.append(f"     Size: {parcel.acres:.2f} acres")
            if parcel.future_land_use:
                report.append(f"     Future: {parcel.future_land_use}")
        report.append("")

    return "\n".join(report)


# Test functions
def test_zoning_lookup():
    """Test the basic zoning lookup with sample addresses"""
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


def test_nearby_zoning_analysis():
    """Test the nearby zoning analysis feature"""
    print("\n" + "=" * 80)
    print("TESTING NEARBY ZONING ANALYSIS")
    print("=" * 80)
    print()

    test_address = "1398 W Hancock Avenue, Athens, GA 30606"
    print(f"Analyzing nearby zoning for: {test_address}")
    print(f"Search radius: 250 meters")
    print()

    nearby_zoning = get_nearby_zoning(test_address, radius_meters=250)

    if nearby_zoning:
        print(format_nearby_zoning_report(nearby_zoning))
    else:
        print(f"❌ Could not retrieve nearby zoning analysis for: {test_address}")


if __name__ == "__main__":
    # Run basic test
    test_zoning_lookup()

    print("\n\n")

    # Run nearby zoning analysis test
    test_nearby_zoning_analysis()
