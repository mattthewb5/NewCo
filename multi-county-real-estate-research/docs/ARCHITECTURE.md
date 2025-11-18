# Architecture Documentation

**Project:** Multi-County Real Estate Research Tool
**Created:** November 18, 2025
**Design Philosophy:** Configuration over duplication

---

## 🏗️ Design Principles

### 1. Configuration Layer Pattern

**Problem:** Each county has different data sources, APIs, and quirks

**Solution:** Abstract county-specific logic into configuration classes

```python
# Base class defines interface
class BaseCountyConfig(ABC):
    @abstractmethod
    def get_schools(self, address: str) -> SchoolInfo:
        pass

    @abstractmethod
    def get_crime(self, address: str) -> CrimeAnalysis:
        pass

    @abstractmethod
    def get_zoning(self, address: str) -> ZoningInfo:
        pass

# Each county implements interface
class LoudounConfig(BaseCountyConfig):
    def get_schools(self, address: str) -> SchoolInfo:
        # Loudoun-specific: LCPS API, VA School Quality Profiles
        ...

    def get_crime(self, address: str) -> CrimeAnalysis:
        # Loudoun-specific: LCSO Dashboard, GeoHub
        ...

    def get_zoning(self, address: str) -> ZoningInfo:
        # Loudoun-specific: County GIS + 7 incorporated towns
        ...
```

**Benefits:**
- ✅ Easy to add new counties (just implement interface)
- ✅ County logic isolated and testable
- ✅ Core modules remain county-agnostic
- ✅ Same module names as Athens project (easy merge)

---

## 📁 Directory Structure Explained

```
multi-county-real-estate-research/
│
├── config/                          # County-specific configurations
│   ├── __init__.py
│   ├── base_config.py               # Abstract base class
│   ├── athens_clarke.py             # Athens-Clarke County, GA
│   └── loudoun.py                   # Loudoun County, VA
│
├── core/                            # County-agnostic core logic
│   ├── __init__.py
│   ├── jurisdiction_detector.py     # Detect jurisdiction (county/town)
│   ├── school_lookup.py             # Generic school lookup
│   ├── crime_analysis.py            # Generic crime analysis
│   ├── zoning_lookup.py             # Generic zoning lookup
│   ├── address_extraction.py        # Parse addresses
│   └── unified_ai_assistant.py      # AI synthesis
│
├── data/                            # County-specific static data
│   ├── athens_clarke/
│   │   └── README.md
│   └── loudoun/
│       ├── README.md
│       ├── town_boundaries.geojson  # Incorporated town boundaries
│       └── zoning_codes/
│           ├── leesburg.json
│           └── purcellville.json
│
├── utils/                           # Shared utilities
│   ├── __init__.py
│   ├── data_validation.py           # Validate data structures
│   └── geocoding.py                 # Address → lat/lon
│
├── tests/                           # Test suites
│   ├── __init__.py
│   ├── test_addresses.py            # Test known addresses
│   └── loudoun_validation.py        # Loudoun-specific validation
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md              # This file
│   ├── adding_a_county.md           # How to add a county
│   ├── loudoun_notes.md             # Loudoun implementation notes
│   └── implementation_phases.md     # Development phases
│
├── streamlit_app.py                 # Main web application
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore rules
├── README.md                        # Project overview
└── MERGE_PLAN.md                    # How to merge with Athens
```

---

## 🔄 Data Flow

### User Address → County Data

```
1. User enters address in Streamlit UI
   ↓
2. User selects county (Athens or Loudoun)
   ↓
3. Load county configuration
   config = loudoun.LoudounConfig()
   ↓
4. Parse and validate address
   address = utils.geocoding.parse_address(raw_input)
   ↓
5. Detect jurisdiction (if needed)
   jurisdiction = core.jurisdiction_detector.detect(address, config)
   ↓
6. Fetch data through config
   schools = config.get_schools(address)
   crime = config.get_crime(address)
   zoning = config.get_zoning(address)
   ↓
7. Generate AI synthesis
   analysis = core.unified_ai_assistant.synthesize(
       address, question, schools, crime, zoning
   )
   ↓
8. Display results in UI
   - School summary box
   - Crime summary box
   - Zoning summary box
   - Key Insights at a Glance
   - AI narrative analysis
```

---

## 🎨 Key Design Patterns

### Pattern 1: Configuration Factory

**Purpose:** Create county config based on user selection

```python
# streamlit_app.py
def get_county_config(county_name: str) -> BaseCountyConfig:
    """Factory method to create county configuration"""
    configs = {
        "Athens-Clarke County, GA": athens_clarke.AthensConfig(),
        "Loudoun County, VA": loudoun.LoudounConfig()
    }
    return configs.get(county_name)

# Usage
county = st.selectbox("Select County", list(configs.keys()))
config = get_county_config(county)
```

### Pattern 2: Jurisdiction Detector

**Purpose:** Handle multi-jurisdictional complexity (e.g., Loudoun's 7 towns)

```python
# core/jurisdiction_detector.py
class JurisdictionDetector:
    def detect(self, address: str, config: BaseCountyConfig) -> Jurisdiction:
        """
        Detect which jurisdiction handles this address

        Examples:
        - Loudoun County: Check if address is in incorporated town
        - Athens-Clarke: Unified government (always county)
        """
        if config.has_incorporated_areas():
            return self._check_incorporated_boundaries(address, config)
        return Jurisdiction(type="county", name=config.name)
```

### Pattern 3: Data Source Abstraction

**Purpose:** Hide county-specific APIs behind common interface

```python
# config/loudoun.py
class LoudounConfig(BaseCountyConfig):
    def __init__(self):
        self.school_api = "https://dashboards.lcps.org/..."
        self.crime_api = "https://geohub-loudoungis.opendata.arcgis.com/..."
        self.zoning_api = "https://logis.loudoun.gov/gis/rest/services/..."

    def get_schools(self, address: str) -> SchoolInfo:
        # 1. Geocode address
        # 2. Query LCPS School Locator
        # 3. Fetch VA School Quality Profiles
        # 4. Return standardized SchoolInfo object
        ...
```

---

## 🧩 Module Responsibilities

### config/base_config.py

**Responsibility:** Define interface all counties must implement

**Key Methods:**
- `get_schools(address)` - Return school assignments
- `get_crime(address)` - Return crime statistics
- `get_zoning(address)` - Return zoning information
- `has_incorporated_areas()` - Does county have towns/cities?
- `get_ai_context()` - County-specific context for AI prompts

**Design Notes:**
- Abstract base class (cannot instantiate)
- Enforces consistent interface
- Type hints for all methods
- Docstrings with examples

### config/athens_clarke.py

**Responsibility:** Athens-Clarke County, Georgia configuration

**Data Sources:**
- Schools: CCSD zones + Georgia GOSA
- Crime: Athens-Clarke Open Data portal
- Zoning: ACC GIS REST API

**Special Handling:**
- Unified government (no incorporated towns)
- All addresses handled by county

### config/loudoun.py

**Responsibility:** Loudoun County, Virginia configuration

**Data Sources:**
- Schools: LCPS School Locator + VA School Quality Profiles
- Crime: LCSO Dashboard / GeoHub
- Zoning: Loudoun GIS + 7 town zoning ordinances

**Special Handling:**
- 7 incorporated towns with separate zoning
- Jurisdiction detection required
- Town boundary lookup

### core/jurisdiction_detector.py

**Responsibility:** Detect which jurisdiction (county/town) handles an address

**Use Cases:**
- Loudoun County: Check if address is in Leesburg, Purcellville, etc.
- Athens-Clarke: Always county (no towns)

**Algorithm:**
1. Check if county has incorporated areas
2. If yes, query town boundary GIS layer
3. Return jurisdiction type and name
4. Config uses jurisdiction to route data requests

### core/school_lookup.py

**Responsibility:** Generic school lookup (delegates to county config)

**Interface:**
```python
def get_school_info(address: str, config: BaseCountyConfig) -> SchoolInfo:
    """Get school assignments and performance data"""
    return config.get_schools(address)
```

**Why Needed:**
- Provides consistent interface for UI
- Can add caching, validation, error handling
- Keeps config classes focused on data fetching

### core/crime_analysis.py

**Responsibility:** Generic crime analysis (delegates to county config)

**Features:**
- Radius search (configurable, default 0.5 miles)
- Safety score calculation (reusable across counties)
- Trend analysis (recent vs. previous period)
- Comparison to county average

### core/zoning_lookup.py

**Responsibility:** Generic zoning lookup (delegates to county config)

**Features:**
- Current zoning + future land use
- Nearby zoning pattern analysis
- Concern detection (industrial nearby, etc.)
- Handles multi-jurisdictional complexity

### core/unified_ai_assistant.py

**Responsibility:** Generate rich narrative analysis

**Features:**
- County-aware prompts (uses `config.get_ai_context()`)
- 10-section narrative structure
- Conversational tone
- Data-driven insights

### utils/geocoding.py

**Responsibility:** Convert addresses to coordinates

**Features:**
- Address parsing and validation
- Geocoding via external service (e.g., Nominatim, Google)
- Reverse geocoding (lat/lon → address)
- Error handling for invalid addresses

### utils/data_validation.py

**Responsibility:** Validate data structures

**Features:**
- Schema validation for SchoolInfo, CrimeAnalysis, ZoningInfo
- Defensive checks (hasattr, None checks)
- Data quality warnings

---

## 🔌 Adding a New County

### Step-by-Step Process

1. **Research data sources** (schools, crime, zoning)
2. **Create config class** `config/new_county.py`
3. **Implement required methods**:
   ```python
   class NewCountyConfig(BaseCountyConfig):
       def get_schools(self, address: str) -> SchoolInfo:
           # Your implementation

       def get_crime(self, address: str) -> CrimeAnalysis:
           # Your implementation

       def get_zoning(self, address: str) -> ZoningInfo:
           # Your implementation
   ```
4. **Add county to UI** in `streamlit_app.py`:
   ```python
   county = st.selectbox(
       "Select County",
       ["Athens-Clarke County, GA", "Loudoun County, VA", "New County, STATE"]
   )
   ```
5. **Test with known addresses**
6. **Document county-specific quirks**

See [adding_a_county.md](./adding_a_county.md) for detailed guide.

---

## 🧪 Testing Strategy

### Unit Tests

Test each county config in isolation:

```python
# tests/test_loudoun_config.py
def test_loudoun_schools():
    config = LoudounConfig()
    schools = config.get_schools("43875 Centergate Drive, Ashburn, VA 20148")
    assert schools.elementary is not None
    assert schools.middle is not None
    assert schools.high is not None
```

### Integration Tests

Test full data flow:

```python
# tests/test_integration.py
def test_full_address_lookup():
    config = get_county_config("Loudoun County, VA")
    result = process_address(
        "43875 Centergate Drive, Ashburn, VA 20148",
        config,
        include_schools=True,
        include_crime=True,
        include_zoning=True
    )
    assert result['school_info'] is not None
    assert result['crime_analysis'] is not None
    assert result['zoning_info'] is not None
```

### Validation Tests

Test with known ground truth:

```python
# tests/loudoun_validation.py
def test_personal_address():
    """Test with personal address (known ground truth)"""
    config = LoudounConfig()
    schools = config.get_schools("MY_REAL_ADDRESS")

    # Verify against known school assignments
    assert schools.elementary == "Expected Elementary"
    assert schools.middle == "Expected Middle"
    assert schools.high == "Expected High"
```

---

## 🚀 Performance Considerations

### Caching Strategy

Cache expensive API calls:

```python
# config/loudoun.py
from functools import lru_cache

class LoudounConfig(BaseCountyConfig):
    @lru_cache(maxsize=100)
    def get_schools(self, address: str) -> SchoolInfo:
        # Expensive API call cached
        ...
```

### Parallel Data Fetching

Fetch schools, crime, zoning in parallel:

```python
# core/unified_ai_assistant.py
import concurrent.futures

def get_comprehensive_analysis(address, config):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        school_future = executor.submit(config.get_schools, address)
        crime_future = executor.submit(config.get_crime, address)
        zoning_future = executor.submit(config.get_zoning, address)

        schools = school_future.result()
        crime = crime_future.result()
        zoning = zoning_future.result()
```

### Rate Limiting

Respect API rate limits:

```python
# utils/api_client.py
import time

class RateLimitedClient:
    def __init__(self, calls_per_second=1):
        self.delay = 1.0 / calls_per_second
        self.last_call = 0

    def call(self, func, *args, **kwargs):
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        result = func(*args, **kwargs)
        self.last_call = time.time()
        return result
```

---

## 🔐 Security Considerations

### API Key Management

- Store API keys in `.env` (never commit)
- Use environment variables
- Validate keys before use

### Input Validation

- Sanitize all user inputs
- Validate addresses before geocoding
- Prevent SQL injection (if using databases)
- Escape HTML in outputs

### Error Handling

- Never expose API keys in error messages
- Log errors securely (no sensitive data)
- Provide user-friendly error messages

---

## 📈 Future Enhancements

### Planned Features

1. **Database Layer** - Cache results in local database
2. **Async API Calls** - Use async/await for better performance
3. **Multi-State Support** - Group counties by state
4. **Comparison Tool** - Compare two addresses side-by-side
5. **Historical Data** - Track changes over time
6. **Export to PDF** - Generate PDF reports

### Scalability Considerations

- **Many Counties:** Use database for county configs instead of Python files
- **High Traffic:** Add Redis cache layer
- **Large Data:** Use chunked processing for large datasets

---

## 🤝 Contributing Guidelines

### Code Style

- Follow PEP 8
- Use type hints everywhere
- Write docstrings for all public methods
- Keep functions under 50 lines
- One class per file (unless tightly coupled)

### Commit Messages

Format: `[component] Brief description`

Examples:
- `[config] Add Loudoun County configuration`
- `[docs] Update architecture documentation`
- `[tests] Add validation tests for personal addresses`

### Pull Request Process

1. Create feature branch (`feature/add-{county-name}`)
2. Implement changes
3. Add tests
4. Update documentation
5. Submit PR with description

---

## 📚 References

- **Athens Implementation:** `/home/user/NewCo`
- **Loudoun Research:** `../loudoun_county_data_sources.md`
- **Merge Strategy:** `../MERGE_PLAN.md`

---

**Last Updated:** November 18, 2025
