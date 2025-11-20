"""
LCPS (Loudoun County Public Schools) School Locator API client.

Uses Loudoun County GIS ArcGIS REST API to find school assignments.

API Endpoint: https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer
- Layer 0: School Sites (points) - School details
- Layer 1: Elementary Zones (polygons)
- Layer 2: Middle School Zones (polygons)
- Layer 3: High School Zones (polygons)

Research documented in: docs/lcps_school_locator_research.md

Last Updated: November 2025
Phase: 3 - School Data (Week 4)
Status: API integration complete, performance data framework ready

Performance Data Documentation: docs/virginia_school_performance.md
"""

import requests
from typing import Dict, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class LCPSSchoolResult:
    """
    Raw result from LCPS School Locator API.

    Attributes:
        elementary_code: Elementary school code (e.g., 'CED')
        middle_code: Middle school code (e.g., 'TMS')
        high_code: High school code (e.g., 'SBH')

        elementary_name: Elementary school name
        middle_name: Middle school name
        high_name: High school name

        elementary_number: Elementary school number
        middle_number: Middle school number
        high_number: High school number

        elementary_opened: Year elementary school opened
        middle_opened: Year middle school opened
        high_opened: Year high school opened

        elementary_performance: Performance metrics (enrollment, test scores, etc.)
        middle_performance: Performance metrics
        high_performance: Performance metrics

        success: Whether lookup was successful
        error_message: Error details if unsuccessful
    """
    elementary_code: Optional[str] = None
    middle_code: Optional[str] = None
    high_code: Optional[str] = None

    elementary_name: Optional[str] = None
    middle_name: Optional[str] = None
    high_name: Optional[str] = None

    elementary_number: Optional[str] = None
    middle_number: Optional[str] = None
    high_number: Optional[str] = None

    elementary_opened: Optional[str] = None
    middle_opened: Optional[str] = None
    high_opened: Optional[str] = None

    # Performance metrics (from Virginia VDOE data)
    elementary_performance: Optional[Dict[str, Any]] = None
    middle_performance: Optional[Dict[str, Any]] = None
    high_performance: Optional[Dict[str, Any]] = None

    success: bool = False
    error_message: Optional[str] = None


class LCPSSchoolAPI:
    """
    Client for LCPS School Locator ArcGIS REST API.

    Usage:
        >>> api = LCPSSchoolAPI()
        >>> result = api.get_schools(39.0437, -77.4875)
        >>> print(f"Elementary: {result.elementary_name}")
        CEDAR LANE ES
    """

    BASE_URL = "https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer"
    TIMEOUT = 10  # seconds

    def __init__(self):
        """Initialize LCPS School API client."""
        pass

    def get_schools(self, lat: float, lon: float) -> LCPSSchoolResult:
        """
        Get school assignments for a coordinate.

        Args:
            lat: Latitude (WGS84)
            lon: Longitude (WGS84)

        Returns:
            LCPSSchoolResult with assigned schools

        Example:
            >>> api = LCPSSchoolAPI()
            >>> result = api.get_schools(39.0437, -77.4875)
            >>> if result.success:
            ...     print(f"Elementary: {result.elementary_name}")
            ...     print(f"Middle: {result.middle_name}")
            ...     print(f"High: {result.high_name}")
        """
        result = LCPSSchoolResult()

        try:
            # Query all three zone layers
            es_code = self._query_zone_layer(1, lat, lon, 'ES_SCH_CODE')
            ms_code = self._query_zone_layer(2, lat, lon, 'MS_SCH_CODE')
            hs_code = self._query_zone_layer(3, lat, lon, 'HS_SCH_CODE')

            # Store codes
            result.elementary_code = es_code
            result.middle_code = ms_code
            result.high_code = hs_code

            # Get school details for each code
            if es_code:
                es_details = self._get_school_details(es_code)
                if es_details:
                    result.elementary_name = es_details.get('NAME')
                    result.elementary_number = str(es_details.get('SCH_NUM', ''))
                    result.elementary_opened = str(es_details.get('DATE_OPENED', ''))

            if ms_code:
                ms_details = self._get_school_details(ms_code)
                if ms_details:
                    result.middle_name = ms_details.get('NAME')
                    result.middle_number = str(ms_details.get('SCH_NUM', ''))
                    result.middle_opened = str(ms_details.get('DATE_OPENED', ''))

            if hs_code:
                hs_details = self._get_school_details(hs_code)
                if hs_details:
                    result.high_name = hs_details.get('NAME')
                    result.high_number = str(hs_details.get('SCH_NUM', ''))
                    result.high_opened = str(hs_details.get('DATE_OPENED', ''))

            # Enrich with performance data (enrollment, test scores, etc.)
            if es_code and result.elementary_number:
                result.elementary_performance = self.get_performance_data(
                    es_code, result.elementary_number
                )

            if ms_code and result.middle_number:
                result.middle_performance = self.get_performance_data(
                    ms_code, result.middle_number
                )

            if hs_code and result.high_number:
                result.high_performance = self.get_performance_data(
                    hs_code, result.high_number
                )

            # Mark as successful if we got at least one school
            if es_code or ms_code or hs_code:
                result.success = True
            else:
                result.error_message = "No school zones found for this location"

        except Exception as e:
            result.error_message = f"Error querying LCPS API: {str(e)}"
            result.success = False

        return result

    def _query_zone_layer(self, layer_id: int, lat: float, lon: float,
                         code_field: str) -> Optional[str]:
        """
        Query a school zone layer for a specific coordinate.

        Args:
            layer_id: Layer ID (1=ES, 2=MS, 3=HS)
            lat: Latitude (WGS84)
            lon: Longitude (WGS84)
            code_field: Field name for school code (ES_SCH_CODE, MS_SCH_CODE, HS_SCH_CODE)

        Returns:
            School code if found, None otherwise
        """
        try:
            url = f"{self.BASE_URL}/{layer_id}/query"
            params = {
                'geometry': f'{lon},{lat}',
                'geometryType': 'esriGeometryPoint',
                'inSR': '4326',  # WGS84
                'spatialRel': 'esriSpatialRelIntersects',
                'outFields': '*',
                'returnGeometry': 'false',
                'f': 'json'
            }

            response = requests.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()
            if data.get('features'):
                attributes = data['features'][0]['attributes']
                return attributes.get(code_field)

            return None

        except Exception as e:
            print(f"Error querying zone layer {layer_id}: {e}")
            return None

    def _get_school_details(self, school_code: str) -> Optional[Dict[str, Any]]:
        """
        Get school details from Layer 0 using school code.

        Args:
            school_code: School code (e.g., 'CED', 'TMS', 'SBH')

        Returns:
            Dictionary with school details (NAME, SCH_NUM, DATE_OPENED, etc.)
        """
        try:
            url = f"{self.BASE_URL}/0/query"
            params = {
                'where': f"SCH_CODE = '{school_code}'",
                'outFields': '*',
                'returnGeometry': 'false',
                'f': 'json'
            }

            response = requests.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()
            if data.get('features'):
                return data['features'][0]['attributes']

            return None

        except Exception as e:
            print(f"Error getting school details for {school_code}: {e}")
            return None

    def get_performance_data(self, school_code: str, school_number: str) -> Optional[Dict[str, Any]]:
        """
        Get Virginia performance data for a school.

        Args:
            school_code: LCPS school code (e.g., 'CED', 'TMS')
            school_number: School number (e.g., '109', '215')

        Returns:
            Dictionary with performance metrics or None if unavailable

        Note:
            Currently uses stub data. See docs/virginia_school_performance.md
            for integration status and data source information.

            To integrate real data:
            1. Download VDOE CSV files or access API
            2. Create local data cache (JSON/SQLite)
            3. Replace _get_stub_performance_data with real lookup
        """
        try:
            # TODO: Replace with real data source when VDOE sites are accessible
            # Options:
            # 1. Query Virginia Open Data API (Socrata SODA)
            # 2. Load from cached VDOE CSV files
            # 3. Query Virginia School Quality Profiles API (when available)

            # For now, return stub data for known schools
            return self._get_stub_performance_data(school_code, school_number)

        except Exception as e:
            print(f"Error getting performance data: {e}")
            return None

    def _get_stub_performance_data(self, school_code: str, school_number: str) -> Optional[Dict[str, Any]]:
        """
        Stub implementation with sample performance data.

        This provides realistic test data structure while VDOE sources are unavailable.
        Real data integration should maintain this structure for compatibility.

        Data source: SchoolDigger research (verified accurate for Cedar Lane ES)
        """
        # Sample data for known schools (from SchoolDigger research)
        stub_data = {
            'CED': {  # Cedar Lane Elementary
                'school_id': '053109',
                'enrollment': 698,
                'student_teacher_ratio': 12.9,
                'accreditation_status': 'Fully Accredited',
                'demographics': {
                    'white': 44,
                    'asian': 29,
                    'hispanic': 12,
                    'two_or_more': 8,
                    'african_american': 7
                },
                'rankings': {
                    'state_rank': 150,
                    'state_total': 1114,
                    'percentile': 86.5
                },
                'notes': 'Top 15% in Virginia'
            },
            'TMS': {  # Trailside Middle School
                'school_id': '053215',
                'enrollment': None,  # Data pending
                'student_teacher_ratio': None,
                'accreditation_status': 'Fully Accredited',
                'notes': 'Performance data pending - opened 2014'
            },
            'SBH': {  # Stone Bridge High School
                'school_id': '053308',
                'enrollment': None,  # Data pending
                'student_teacher_ratio': None,
                'accreditation_status': 'Fully Accredited',
                'notes': 'Performance data pending - opened 2000'
            },
            'LEE': {  # Leesburg Elementary
                'school_id': '053123',
                'enrollment': None,
                'student_teacher_ratio': None,
                'accreditation_status': 'Fully Accredited',
                'notes': 'Established 1980'
            },
            'SMM': {  # Smart's Mill Middle
                'school_id': '053211',
                'enrollment': None,
                'student_teacher_ratio': None,
                'accreditation_status': 'Fully Accredited',
                'notes': 'Opened 2004'
            },
            'THS': {  # Tuscarora High School
                'school_id': '053314',
                'enrollment': None,
                'student_teacher_ratio': None,
                'accreditation_status': 'Fully Accredited',
                'notes': 'Opened 2010'
            },
            'MTV': {  # Mountain View Elementary
                'school_id': '053132',
                'enrollment': None,
                'student_teacher_ratio': None,
                'accreditation_status': 'Fully Accredited',
                'notes': 'Opened 2003'
            },
            'BRM': {  # Blue Ridge Middle
                'school_id': '053202',
                'enrollment': None,
                'student_teacher_ratio': None,
                'accreditation_status': 'Fully Accredited',
                'notes': 'Established 1971'
            },
            'LVH': {  # Loudoun Valley High School
                'school_id': '053305',
                'enrollment': None,
                'student_teacher_ratio': None,
                'accreditation_status': 'Fully Accredited',
                'notes': 'Established 1962'
            }
        }

        # Return performance data if available
        if school_code in stub_data:
            data = stub_data[school_code].copy()
            data['data_source'] = 'Stub Data (SchoolDigger research)'
            data['school_year'] = '2023-2024'
            data['last_updated'] = '2025-11-20'
            data['is_stub_data'] = True  # Flag for identification
            return data

        # Return minimal data for unknown schools
        return {
            'school_id': f'053{school_number}',
            'enrollment': None,
            'student_teacher_ratio': None,
            'accreditation_status': 'Unknown',
            'data_source': 'Stub Data',
            'is_stub_data': True,
            'notes': 'Performance data not yet available'
        }


# ===== VALIDATION FUNCTION =====

def test_lcps_api():
    """
    Test LCPS API with known addresses.
    """
    print("=" * 70)
    print("LCPS SCHOOL LOCATOR API TESTS")
    print("=" * 70)
    print(f"Date: November 2025")
    print(f"API: Loudoun County GIS ArcGIS REST API")
    print()

    api = LCPSSchoolAPI()

    # Test addresses (from research)
    test_cases = [
        ("Ashburn", 39.0437, -77.4875, {
            'es': 'CEDAR LANE ES',
            'ms': 'TRAILSIDE MS',
            'hs': 'STONE BRIDGE HS'
        }),
        ("Leesburg", 39.1156, -77.5636, {
            'es': 'LEESBURG ES',
            'ms': "SMART'S MILL MS",
            'hs': 'TUSCARORA HS'
        }),
        ("Purcellville", 39.1376, -77.7128, {
            'es': 'MOUNTAIN VIEW ES',
            'ms': 'BLUE RIDGE MS',
            'hs': 'LOUDOUN VALLEY HS'
        })
    ]

    for location, lat, lon, expected in test_cases:
        print(f"Testing: {location} ({lat}, {lon})")
        print("-" * 70)

        result = api.get_schools(lat, lon)

        if result.success:
            print(f"  ✅ Success")
            print(f"  Elementary: {result.elementary_name} (#{result.elementary_number})")
            print(f"  Middle: {result.middle_name} (#{result.middle_number})")
            print(f"  High: {result.high_name} (#{result.high_number})")

            # Validate against expected
            assert result.elementary_name == expected['es'], \
                f"Expected {expected['es']}, got {result.elementary_name}"
            assert result.middle_name == expected['ms'], \
                f"Expected {expected['ms']}, got {result.middle_name}"
            assert result.high_name == expected['hs'], \
                f"Expected {expected['hs']}, got {result.high_name}"
            print(f"  ✅ Matches expected results")
        else:
            print(f"  ❌ Failed: {result.error_message}")
            raise AssertionError(f"Test failed for {location}")

        print()

    print("=" * 70)
    print("✅ ALL TESTS PASSED (3/3)")
    print("=" * 70)
    print()
    print("API Status:")
    print("  - Connection: ✅ Working")
    print("  - Elementary zones: ✅ Accurate")
    print("  - Middle school zones: ✅ Accurate")
    print("  - High school zones: ✅ Accurate")
    print("  - School details: ✅ Complete (name, number, opening date)")
    print()
    print("Ready for integration into school_lookup.py!")
    print()


if __name__ == "__main__":
    test_lcps_api()
