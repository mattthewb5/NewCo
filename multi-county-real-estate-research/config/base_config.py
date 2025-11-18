"""
Base configuration class for county-specific implementations

All county configurations must inherit from BaseCountyConfig and implement
the required abstract methods.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SchoolInfo:
    """Standardized school information structure"""
    elementary: str
    middle: str
    high: str
    elementary_data: Optional[Dict[str, Any]] = None
    middle_data: Optional[Dict[str, Any]] = None
    high_data: Optional[Dict[str, Any]] = None


@dataclass
class CrimeAnalysis:
    """Standardized crime analysis structure"""
    safety_score: Any  # SafetyScore object
    statistics: Any  # CrimeStatistics object
    trends: Any  # CrimeTrends object
    comparison: Optional[Any] = None  # AreaComparison object
    time_period_months: int = 12
    radius_miles: float = 0.5


@dataclass
class ZoningInfo:
    """Standardized zoning information structure"""
    current_zoning: str
    current_zoning_description: str
    future_land_use: Optional[str] = None
    future_land_use_description: Optional[str] = None
    acres: float = 0.0
    split_zoned: bool = False
    future_changed: bool = False
    nearby_zones: Optional[list] = None


@dataclass
class NearbyZoning:
    """Enhanced nearby zoning analysis"""
    current_parcel: Optional[ZoningInfo] = None
    total_nearby_parcels: int = 0
    unique_zones: list = None
    zone_diversity_score: float = 0.0
    residential_only: bool = False
    commercial_nearby: bool = False
    mixed_use_nearby: bool = False
    industrial_nearby: bool = False
    potential_concerns: list = None

    def __post_init__(self):
        if self.unique_zones is None:
            self.unique_zones = []
        if self.potential_concerns is None:
            self.potential_concerns = []


class BaseCountyConfig(ABC):
    """
    Abstract base class for county configurations

    Each county must implement this interface to provide data for:
    - School assignments and performance
    - Crime statistics and safety analysis
    - Zoning information and land use

    Example:
        class LoudounConfig(BaseCountyConfig):
            def get_schools(self, address: str) -> SchoolInfo:
                # Implementation for Loudoun County
                ...
    """

    def __init__(self):
        """Initialize county configuration"""
        self.name = self.get_county_name()
        self.state = self.get_state()

    @abstractmethod
    def get_county_name(self) -> str:
        """
        Return the county name

        Example:
            return "Loudoun County"
        """
        pass

    @abstractmethod
    def get_state(self) -> str:
        """
        Return the state abbreviation

        Example:
            return "VA"
        """
        pass

    @abstractmethod
    def get_schools(self, address: str) -> Optional[SchoolInfo]:
        """
        Get school assignments and performance data for an address

        Args:
            address: Full street address (e.g., "123 Main St, City, STATE ZIP")

        Returns:
            SchoolInfo object with elementary, middle, high school assignments
            and optional performance data

        Raises:
            ValueError: If address cannot be geocoded
            APIError: If data source is unavailable

        Example:
            schools = config.get_schools("43875 Centergate Drive, Ashburn, VA 20148")
            print(schools.elementary)  # "Mill Run Elementary"
        """
        pass

    @abstractmethod
    def get_crime(self, address: str, radius_miles: float = 0.5, months_back: int = 12) -> Optional[CrimeAnalysis]:
        """
        Get crime statistics and safety analysis for an address

        Args:
            address: Full street address
            radius_miles: Search radius in miles (default: 0.5)
            months_back: Historical period in months (default: 12)

        Returns:
            CrimeAnalysis object with safety score, statistics, trends

        Raises:
            ValueError: If address cannot be geocoded
            APIError: If data source is unavailable

        Example:
            crime = config.get_crime("123 Main St, City, STATE", radius_miles=0.5)
            print(crime.safety_score.score)  # 75
        """
        pass

    @abstractmethod
    def get_zoning(self, address: str) -> Optional[ZoningInfo]:
        """
        Get zoning information for an address

        Args:
            address: Full street address

        Returns:
            ZoningInfo object with current zoning, future land use, etc.

        Raises:
            ValueError: If address cannot be geocoded
            APIError: If data source is unavailable

        Example:
            zoning = config.get_zoning("123 Main St, City, STATE")
            print(zoning.current_zoning)  # "R-1"
        """
        pass

    @abstractmethod
    def get_nearby_zoning(self, address: str, radius_meters: int = 250) -> Optional[NearbyZoning]:
        """
        Get nearby zoning analysis for an address

        Args:
            address: Full street address
            radius_meters: Search radius in meters (default: 250)

        Returns:
            NearbyZoning object with pattern analysis and concerns

        Raises:
            ValueError: If address cannot be geocoded
            APIError: If data source is unavailable

        Example:
            nearby = config.get_nearby_zoning("123 Main St, City, STATE")
            print(nearby.potential_concerns)  # ["Industrial zoning nearby"]
        """
        pass

    def has_incorporated_areas(self) -> bool:
        """
        Does this county have incorporated towns/cities with separate jurisdictions?

        Default: False (most counties are unified)

        Override this in county config if applicable:
            def has_incorporated_areas(self) -> bool:
                return True  # Loudoun has 7 incorporated towns
        """
        return False

    def get_incorporated_areas(self) -> list:
        """
        Get list of incorporated town/city names

        Default: Empty list

        Override if has_incorporated_areas() returns True:
            def get_incorporated_areas(self) -> list:
                return ["Leesburg", "Purcellville", "Hamilton", ...]
        """
        return []

    def detect_jurisdiction(self, address: str) -> Dict[str, str]:
        """
        Detect which jurisdiction (county or incorporated area) handles an address

        Default implementation: Always county

        Override if has_incorporated_areas() returns True to implement
        boundary detection logic

        Args:
            address: Full street address

        Returns:
            Dictionary with 'type' and 'name' keys
            Example: {'type': 'town', 'name': 'Leesburg'}
                     {'type': 'county', 'name': 'Loudoun County'}
        """
        return {
            'type': 'county',
            'name': self.name
        }

    def get_ai_context(self) -> str:
        """
        Get county-specific context for AI prompts

        This allows customizing the AI analysis with local knowledge,
        common issues, and county-specific considerations.

        Default: Empty string (no additional context)

        Override to provide county-specific context:
            def get_ai_context(self) -> str:
                return '''
                Loudoun County context:
                - Data Center Alley: Eastern Loudoun has massive data center development
                - Western Loudoun: Rural, historic, agricultural preservation
                - Route 7 corridor: High-density mixed-use development
                - LCPS: Rapid growth, frequent boundary changes
                '''
        """
        return ""

    def validate_address(self, address: str) -> bool:
        """
        Validate that an address is within this county

        Default implementation: Always True (no validation)

        Override to implement county boundary checking:
            def validate_address(self, address: str) -> bool:
                lat, lon = geocode(address)
                return self.point_in_county_boundary(lat, lon)
        """
        return True

    def get_data_sources(self) -> Dict[str, str]:
        """
        Get dictionary of data sources used by this county

        Useful for documentation and citations

        Returns:
            Dictionary mapping data type to source URL

        Example:
            return {
                'schools': 'https://dashboards.lcps.org/...',
                'crime': 'https://www.loudoun.gov/crimedashboard',
                'zoning': 'https://logis.loudoun.gov/gis/...'
            }
        """
        return {}

    def __str__(self) -> str:
        """String representation of config"""
        return f"{self.name}, {self.state}"

    def __repr__(self) -> str:
        """Debug representation of config"""
        return f"{self.__class__.__name__}(name='{self.name}', state='{self.state}')"
