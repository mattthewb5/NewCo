"""
LCPS (Loudoun County Public Schools) School Locator API Client

Queries the LCPS school assignment tool and parses HTML responses to
extract elementary, middle, and high school assignments for addresses.

API Details:
- Endpoint: https://lcpsplanning.com/loudounlabel/index4.php
- Method: GET
- Returns: HTML with embedded school data
- Parameters: a (street number), y (year), n (street number), z (ZIP)

Created: November 2025
Status: Production
"""

import requests
import re
from typing import Dict, Optional, Tuple
from bs4 import BeautifulSoup
from datetime import datetime


def parse_address_components(address: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract street number and ZIP code from address.

    Args:
        address: Full address string (e.g., "123 Main St, Leesburg, VA 20176")

    Returns:
        Tuple of (street_number, zip_code)
        Returns (None, None) if parsing fails

    Examples:
        >>> parse_address_components("43423 Cloister Pl, Leesburg, VA 20176")
        ("43423", "20176")

        >>> parse_address_components("44084 Riverside Pkwy, Ashburn, VA 20147")
        ("44084", "20147")
    """
    street_number = None
    zip_code = None

    # Extract street number (first number in address)
    number_match = re.search(r'^\s*(\d+)', address)
    if number_match:
        street_number = number_match.group(1)

    # Extract ZIP code (5 digits after state abbreviation or at the very end)
    # Match: VA followed by optional spaces and 5 digits
    zip_match = re.search(r'\bVA\s+(\d{5})(?:-\d{4})?\b', address)
    if not zip_match:
        # Fallback: match 5 digits at the end of string
        zip_match = re.search(r'(\d{5})(?:-\d{4})?\s*$', address)

    if zip_match:
        zip_code = zip_match.group(1)

    return street_number, zip_code


def get_school_year() -> int:
    """
    Get the current school year for API requests.

    LCPS uses the ending year (e.g., 2026 for 2025-2026 school year).
    During fall (Aug-Dec), use next calendar year.
    During spring (Jan-Jul), use current calendar year.

    Returns:
        School year as integer (e.g., 2026)

    Examples:
        >>> # If current date is November 2025
        >>> get_school_year()
        2026

        >>> # If current date is March 2026
        >>> get_school_year()
        2026
    """
    now = datetime.now()
    current_year = now.year

    # If we're in Aug-Dec, school year is next year
    # If we're in Jan-Jul, school year is current year
    if now.month >= 8:  # August or later
        return current_year + 1
    else:
        return current_year


def query_lcps_school_locator(
    street_number: str,
    zip_code: str,
    school_year: Optional[int] = None
) -> Optional[str]:
    """
    Query LCPS school locator API.

    Args:
        street_number: Street number (e.g., "43423")
        zip_code: ZIP code (e.g., "20176")
        school_year: School year (e.g., 2026), defaults to current year

    Returns:
        HTML response as string, or None if request fails

    Raises:
        requests.RequestException: If network request fails
    """
    if not school_year:
        school_year = get_school_year()

    # Build API URL
    base_url = "https://lcpsplanning.com/loudounlabel/index4.php"
    params = {
        'a': street_number,
        'y': school_year,
        'n': street_number,  # API wants street number twice (a and n)
        'z': zip_code
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.text

    except requests.RequestException as e:
        print(f"Error querying LCPS API: {e}")
        return None


def parse_school_data(html: str, school_class: str) -> Optional[Dict[str, str]]:
    """
    Parse school data from HTML for a specific school level.

    Args:
        html: HTML response from LCPS API
        school_class: CSS class name ("sch1", "sch2", or "sch3")

    Returns:
        Dictionary with school data or None if not found

    Expected HTML structure:
        <div class='blk3 sch1 rdd'>
            <b>Elementary School</b>
            <br><br>
            CARDINAL RIDGE ES
            <br>26155 BULLRUN POSTOFFICE RD<BR> CENTREVILLE VA  20120
            <br>571-367-4020
            ...
        </div>

    Returns:
        {
            'name': 'CARDINAL RIDGE ES',
            'address': '26155 BULLRUN POSTOFFICE RD, CENTREVILLE VA 20120',
            'phone': '571-367-4020',
            ...
        }
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Find the school div - it has multiple classes including our target class
    school_div = soup.find('div', class_=lambda c: c and school_class in c.split())
    if not school_div:
        return None

    # Get all text from the div
    text = school_div.get_text(separator='|', strip=True)

    # Split by the separator to get lines
    lines = [line.strip() for line in text.split('|') if line.strip()]

    school_data = {}

    # The school name is typically the line after "Elementary School" / "Middle School" / "High School"
    # and before the address line
    for i, line in enumerate(lines):
        # Skip header lines
        if 'School' in line and i < len(lines) - 1:
            # Next non-empty line should be school name
            if i + 1 < len(lines):
                potential_name = lines[i + 1]
                # School names are usually in caps and contain "ES", "MS", "HS", or "SCHOOL"
                if potential_name and (
                    ' ES' in potential_name or
                    ' MS' in potential_name or
                    ' HS' in potential_name or
                    'SCHOOL' in potential_name or
                    potential_name.isupper()
                ):
                    school_data['name'] = potential_name
                    break

    # If we didn't find a name using the above logic, try a different approach
    if 'name' not in school_data:
        # Look for lines that are all caps and likely school names
        for line in lines:
            if (line.isupper() and
                len(line) > 5 and
                ('ES' in line or 'MS' in line or 'HS' in line or 'SCHOOL' in line) and
                'Elementary' not in line and
                'Middle' not in line and
                'High' not in line):
                school_data['name'] = line
                break

    # Extract address - look for pattern with street number, street name, city, state, ZIP
    full_text = school_div.get_text()
    address_match = re.search(r'(\d+[A-Z\s]+(?:RD|ST|AVE|DR|LN|WAY|PKWY|PL|CT|CIR|BLVD)[A-Z\s]*,?\s*[A-Z\s]+VA\s+\d{5})', full_text, re.IGNORECASE)
    if address_match:
        # Clean up the address
        addr = address_match.group(1)
        # Remove extra spaces and normalize
        addr = re.sub(r'\s+', ' ', addr)
        # Ensure comma between street and city
        addr = re.sub(r'([A-Z]{2,})\s+([A-Z][A-Z\s]+VA)', r'\1, \2', addr)
        school_data['address'] = addr.strip()

    # Extract phone number (571-XXX-XXXX format)
    phone_match = re.search(r'(571-\d{3}-\d{4})', full_text)
    if phone_match:
        school_data['phone'] = phone_match.group(1)

    # Extract website link
    website_link = school_div.find('a', href=re.compile(r'lcps\.org'))
    if website_link and website_link.get('href'):
        school_data['website'] = website_link.get('href')

    # Extract zone map PDF link
    pdf_link = school_div.find('a', href=re.compile(r'\.pdf', re.IGNORECASE))
    if pdf_link and pdf_link.get('href'):
        school_data['zone_map'] = pdf_link.get('href')

    # Return data only if we found at least a name
    return school_data if 'name' in school_data else None


def get_school_assignments(address: str) -> Optional[Dict[str, Optional[Dict[str, str]]]]:
    """
    Get school assignments for a full address.

    This is the main public function for LCPS school lookups.

    Args:
        address: Full address string (e.g., "43423 Cloister Pl, Leesburg, VA 20176")

    Returns:
        Dictionary with 'elementary', 'middle', 'high' keys, or None if lookup fails

    Example:
        >>> result = get_school_assignments("43423 Cloister Pl, Leesburg, VA 20176")
        >>> if result:
        ...     print(result['elementary']['name'])
        ...     print(result['middle']['name'])
        ...     print(result['high']['name'])
        RICHARD AND MILDRED LOVING ES
        HARPER PARK MS
        HERITAGE HS
    """
    # Parse address components
    street_number, zip_code = parse_address_components(address)

    if not street_number or not zip_code:
        print(f"Could not parse address components from: {address}")
        print(f"  Street number: {street_number}")
        print(f"  ZIP code: {zip_code}")
        return None

    # Query API
    html = query_lcps_school_locator(street_number, zip_code)
    if not html:
        print(f"No response from LCPS API for address: {address}")
        return None

    # Parse schools
    elementary = parse_school_data(html, 'sch1')
    middle = parse_school_data(html, 'sch2')
    high = parse_school_data(html, 'sch3')

    # Return structured results
    return {
        'elementary': elementary,
        'middle': middle,
        'high': high
    }


# Test function for development
if __name__ == "__main__":
    # Test with known address
    test_address = "43423 Cloister Pl, Leesburg, VA 20176"
    print(f"Testing LCPS API with address: {test_address}")
    print("=" * 60)

    result = get_school_assignments(test_address)

    if result:
        print("\n✅ SUCCESS - School assignments found:")
        print()

        if result['elementary']:
            print("Elementary School:")
            for key, value in result['elementary'].items():
                print(f"  {key}: {value}")
            print()

        if result['middle']:
            print("Middle School:")
            for key, value in result['middle'].items():
                print(f"  {key}: {value}")
            print()

        if result['high']:
            print("High School:")
            for key, value in result['high'].items():
                print(f"  {key}: {value}")
            print()
    else:
        print("\n❌ FAILED - Could not retrieve school assignments")
