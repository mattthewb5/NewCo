#!/usr/bin/env python3
"""
Crime proximity lookup for Athens-Clarke County
Query crimes near a specific address with distance calculations
"""

import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


# ArcGIS REST API endpoint for Athens-Clarke County crime data
CRIME_API_URL = "https://services2.arcgis.com/xSEULKvB31odt3XQ/arcgis/rest/services/Crime_Web_Layer_CAU_view/FeatureServer/0/query"

# Athens-Clarke County approximate boundaries for validation
ATHENS_BOUNDS = {
    'lat_min': 33.85,
    'lat_max': 34.05,
    'lon_min': -83.50,
    'lon_max': -83.25
}


@dataclass
class CrimeIncident:
    """Represents a single crime incident"""
    date: datetime
    crime_type: str
    address: str
    case_number: str
    distance_miles: float
    latitude: float
    longitude: float
    district: str
    beat: str
    offense_count: int

    def __str__(self):
        return (f"{self.date.strftime('%Y-%m-%d')} - {self.crime_type} at {self.address} "
                f"({self.distance_miles:.2f} miles away)")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth (in miles)

    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point

    Returns:
        Distance in miles
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Earth radius in miles
    radius_miles = 3959

    return radius_miles * c


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Geocode an address to latitude/longitude coordinates

    Args:
        address: Street address to geocode

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    try:
        geolocator = Nominatim(user_agent="athens_home_buyer_research")

        # Add Athens, GA if not present
        if 'athens' not in address.lower():
            address = f"{address}, Athens, GA"

        location = geolocator.geocode(address, timeout=10)

        if not location:
            return None

        lat, lon = location.latitude, location.longitude

        # Validate it's in Athens-Clarke County
        if not (ATHENS_BOUNDS['lat_min'] <= lat <= ATHENS_BOUNDS['lat_max'] and
                ATHENS_BOUNDS['lon_min'] <= lon <= ATHENS_BOUNDS['lon_max']):
            return None

        return (lat, lon)

    except GeocoderTimedOut:
        print("⚠️  Geocoding service timed out. Please try again.")
        return None
    except GeocoderServiceError as e:
        print(f"⚠️  Geocoding service error: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected geocoding error: {e}")
        return None


def query_crimes_in_radius(center_lat: float, center_lon: float,
                           radius_miles: float, months_back: int) -> Optional[List[Dict]]:
    """
    Query crimes within a radius of a point

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        radius_miles: Search radius in miles
        months_back: How many months back to search

    Returns:
        List of crime dictionaries or None if error
    """
    try:
        # Calculate date threshold for client-side filtering
        date_threshold = datetime.now() - timedelta(days=months_back * 30)
        date_threshold_ms = int(date_threshold.timestamp() * 1000)

        # Convert miles to meters for API (ArcGIS uses meters)
        radius_meters = radius_miles * 1609.34

        # Build query parameters
        # Note: We do date filtering client-side because the API date syntax is unreliable
        params = {
            'geometry': f'{center_lon},{center_lat}',
            'geometryType': 'esriGeometryPoint',
            'inSR': '4326',  # WGS84 coordinate system
            'spatialRel': 'esriSpatialRelIntersects',
            'distance': radius_meters,
            'units': 'esriSRUnit_Meter',
            'where': '1=1',  # Get all records (filter by date client-side)
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'json'
        }

        response = requests.get(CRIME_API_URL, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        if 'features' in data:
            all_crimes = [feature['attributes'] for feature in data['features']]

            # Filter by date client-side
            filtered_crimes = []
            for crime in all_crimes:
                crime_date_ms = crime.get('Date')
                if crime_date_ms and crime_date_ms >= date_threshold_ms:
                    filtered_crimes.append(crime)

            return filtered_crimes
        else:
            return []

    except requests.exceptions.Timeout:
        print("⚠️  API request timed out")
        return None
    except requests.exceptions.ConnectionError:
        print("⚠️  Connection error - check internet connection")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"⚠️  HTTP error: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected error querying crimes: {e}")
        return None


def get_crimes_near_address(address: str, radius_miles: float = 0.5,
                            months_back: int = 60) -> Optional[List[CrimeIncident]]:
    """
    Get all crimes near a specific address

    Args:
        address: Street address in Athens-Clarke County
        radius_miles: Search radius in miles (default: 0.5)
        months_back: How many months of history to search (default: 60 = 5 years)
                     Common values: 12 (1 year), 36 (3 years), 60 (5 years)

    Returns:
        List of CrimeIncident objects sorted by distance, or None if error

    Raises:
        ValueError: If address is invalid or outside Athens-Clarke County
    """
    # Validate inputs
    if not address or not address.strip():
        raise ValueError("Address cannot be empty")

    if radius_miles <= 0 or radius_miles > 10:
        raise ValueError("Radius must be between 0 and 10 miles")

    if months_back <= 0 or months_back > 120:
        raise ValueError("months_back must be between 1 and 120 months")

    # Geocode the address
    print(f"🔍 Geocoding address: {address}")
    coords = geocode_address(address)

    if not coords:
        raise ValueError(
            f"Could not geocode address: {address}\n"
            "Please check:\n"
            "  - Address is in Athens-Clarke County, GA\n"
            "  - Street name is spelled correctly\n"
            "  - Street number is valid"
        )

    center_lat, center_lon = coords
    print(f"✓ Geocoded to: {center_lat:.6f}, {center_lon:.6f}")

    # Query crimes in radius
    print(f"🔍 Searching for crimes within {radius_miles} miles (last {months_back} months)...")
    crime_data = query_crimes_in_radius(center_lat, center_lon, radius_miles, months_back)

    if crime_data is None:
        raise RuntimeError("Failed to query crime data - API error")

    if not crime_data:
        # No crimes found - return empty list (not an error)
        return []

    # Convert to CrimeIncident objects with distance calculations
    incidents = []
    for crime in crime_data:
        try:
            # Parse date (Unix timestamp in milliseconds)
            date_ms = crime.get('Date')
            if date_ms:
                date = datetime.fromtimestamp(date_ms / 1000)
            else:
                continue  # Skip if no date

            # Get location
            crime_lat = crime.get('Lat')
            crime_lon = crime.get('Lon')

            if not crime_lat or not crime_lon:
                continue  # Skip if no coordinates

            # Calculate distance
            distance = haversine_distance(center_lat, center_lon, crime_lat, crime_lon)

            # Only include crimes within the specified radius
            # (API might return slightly more due to bounding box)
            if distance > radius_miles:
                continue

            incident = CrimeIncident(
                date=date,
                crime_type=crime.get('Crime_Description', 'Unknown'),
                address=crime.get('Address_Line_1', 'Location not specified'),
                case_number=crime.get('Case_Number', 'N/A'),
                distance_miles=distance,
                latitude=crime_lat,
                longitude=crime_lon,
                district=crime.get('District', 'N/A'),
                beat=crime.get('Beat', 'N/A'),
                offense_count=crime.get('Total_Offense_Counts', 1)
            )

            incidents.append(incident)

        except Exception as e:
            # Skip malformed records
            print(f"⚠️  Skipping malformed crime record: {e}")
            continue

    # Sort by distance (closest first)
    incidents.sort(key=lambda x: x.distance_miles)

    return incidents


def format_crime_summary(address: str, crimes: List[CrimeIncident],
                        radius_miles: float, months_back: int) -> str:
    """
    Format a summary report of crimes near an address

    Args:
        address: The searched address
        crimes: List of crime incidents
        radius_miles: Search radius used
        months_back: Time period searched

    Returns:
        Formatted string report
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"CRIME REPORT FOR: {address}")
    lines.append("=" * 80)
    lines.append(f"Search radius: {radius_miles} miles")
    lines.append(f"Time period: Last {months_back} months")
    lines.append(f"Total crimes found: {len(crimes)}")
    lines.append("")

    if not crimes:
        lines.append("✅ No crimes reported in this area during the specified time period.")
        lines.append("")
        lines.append("⚠️  Note: This is based on publicly available data only.")
        return "\n".join(lines)

    # Summary by crime type
    crime_types = {}
    for crime in crimes:
        crime_types[crime.crime_type] = crime_types.get(crime.crime_type, 0) + 1

    lines.append("📊 CRIMES BY TYPE:")
    for crime_type, count in sorted(crime_types.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"   • {crime_type}: {count}")
    lines.append("")

    # Show closest 10 crimes
    lines.append("📍 CLOSEST INCIDENTS (up to 10):")
    for i, crime in enumerate(crimes[:10], 1):
        lines.append(f"\n{i}. {crime.crime_type}")
        lines.append(f"   Date: {crime.date.strftime('%B %d, %Y')}")
        lines.append(f"   Location: {crime.address}")
        lines.append(f"   Distance: {crime.distance_miles:.3f} miles away")
        lines.append(f"   Case: {crime.case_number}")

    if len(crimes) > 10:
        lines.append(f"\n   ... and {len(crimes) - 10} more incidents")

    lines.append("")
    lines.append("=" * 80)
    lines.append("⚠️  DATA NOTES:")
    lines.append("   • Data from Athens-Clarke County Police Department")
    lines.append("   • Some sensitive crimes may be excluded from public data")
    lines.append("   • Locations may be approximate for privacy protection")
    lines.append("   • For detailed crime statistics, contact ACCPD directly")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """Test the crime lookup functionality"""
    test_addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "585 Reese Street, Athens, GA 30601",
        "195 Hoyt Street, Athens, GA 30601"
    ]

    print("=" * 80)
    print("TESTING CRIME PROXIMITY LOOKUP")
    print("=" * 80)
    print()

    for address in test_addresses:
        print(f"\n{'='*80}")
        print(f"Testing: {address}")
        print(f"{'='*80}\n")

        try:
            # Use default: 0.5 miles, 60 months (5 years)
            crimes = get_crimes_near_address(address, radius_miles=0.5)

            if crimes is None:
                print(f"❌ Failed to get crime data for {address}")
                continue

            print(f"✅ Found {len(crimes)} crimes within 0.5 miles (last 60 months / 5 years)")

            # Show summary
            summary = format_crime_summary(address, crimes, 0.5, 60)
            print("\n" + summary)

        except ValueError as e:
            print(f"❌ Invalid address: {e}")
        except RuntimeError as e:
            print(f"❌ Runtime error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

        print("\n")


if __name__ == "__main__":
    main()
