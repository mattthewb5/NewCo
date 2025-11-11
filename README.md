# NewCo - Real Estate Tools
Real Estate NewCo 2025

## Athens-Clarke County School District Lookup Tool

A Python tool to help home buyers in Athens-Clarke County, Georgia research which school attendance zones properties belong to.

### Features

- ✅ **Address Geocoding**: Converts street addresses to coordinates
- ✅ **Address Normalization**: Handles variations like "St" vs "Street"
- ✅ **Spatial Lookup**: Determines which school zone a property falls into
- ✅ **Multi-Level**: Returns Elementary, Middle, and High school assignments
- ✅ **GeoJSON Support**: Works with standard GIS data formats

### Quick Start

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `shapely` - For spatial/geometric operations
- `geopy` - For geocoding addresses
- `requests` - For downloading data

#### 2. Get School Zone Data

The tool needs GeoJSON files with school attendance zone boundaries. You have two options:

**Option A: Use Sample Data (for testing)**

```bash
python3 create_sample_data.py
```

**Note**: This creates sample data for demonstration only - NOT real school assignments!

**Option B: Download Real Data (recommended)**

1. Visit the [Athens-Clarke County Open Data Portal](https://data-athensclarke.opendata.arcgis.com/)
2. Search for "school" or "attendance zone"
3. Look for datasets like:
   - Elementary School Attendance Zones
   - Middle School Attendance Zones
   - High School Attendance Zones
4. For each dataset:
   - Click on the dataset
   - Find the "Download" button
   - Select "GeoJSON" format
   - Save to the `data/` directory with names:
     - `elementary_zones.geojson`
     - `middle_zones.geojson`
     - `high_zones.geojson`

**Alternative**: Visit the [Clarke County Schools website](https://www.clarke.k12.ga.us/page/school-attendance-zones) for zone information

#### 3. Run the Lookup Tool

```bash
python3 school_district_lookup.py
```

This will test the tool with three sample addresses.

### Usage

#### Command Line

```bash
python3 school_district_lookup.py
```

#### Python API

```python
from school_district_lookup import SchoolDistrictLookup

# Initialize the lookup tool
lookup = SchoolDistrictLookup(data_dir="data")

# Look up a school district
assignment = lookup.lookup_school_district("123 Main Street, Athens, GA 30601")

print(f"Elementary: {assignment.elementary}")
print(f"Middle: {assignment.middle}")
print(f"High: {assignment.high}")
```

### How It Works

1. **Address Normalization**: Handles variations (St → Street, Ave → Avenue, etc.)
2. **Geocoding**: Converts address to latitude/longitude using OpenStreetMap
3. **Spatial Lookup**: Checks coordinates against school zone boundary polygons
4. **Results**: Returns the elementary, middle, and high school for that address

### Test Results

The tool was tested with these Athens addresses:

| Address | Elementary | Middle | High |
|---------|-----------|--------|------|
| 150 Hancock Avenue | Barrow Elementary* | Clarke Middle* | Clarke Central High* |
| 585 Reese Street | Chase Street Elementary* | Clarke Middle* | Clarke Central High* |
| 195 Hoyt Street | Barrow Elementary* | Clarke Middle* | Clarke Central High* |

\* Results shown are from sample data - download real zone data for actual assignments

### Files

- `school_district_lookup.py` - Main lookup tool with full functionality
- `create_sample_data.py` - Creates sample GeoJSON data for testing
- `download_school_zones.py` - Attempts automated download from open data portal
- `fetch_zones_api.py` - Attempts to fetch data via ArcGIS REST API
- `download_from_arcgis_hub.py` - Searches ArcGIS Online for datasets
- `requirements.txt` - Python package dependencies
- `data/` - Directory for school zone GeoJSON files

### Troubleshooting

**"No school zone data found"**: The GeoJSON files aren't in the `data/` directory. Follow the download instructions above.

**Geocoding Errors**: Check internet connection or verify the address is in Athens-Clarke County, GA.

**Import Errors**: Install dependencies with `pip install shapely geopy requests`

### Data Sources

- **Athens-Clarke County Open Data Portal**: https://data-athensclarke.opendata.arcgis.com/
- **Clarke County Schools**: https://www.clarke.k12.ga.us/
- **Geocoding**: OpenStreetMap Nominatim

### Important Notes

⚠️ **Disclaimer**:
- School attendance zones can change year-to-year
- Always verify with Clarke County School District official sources
- This tool is for research purposes only
- Not affiliated with Clarke County School District or Athens-Clarke County government
