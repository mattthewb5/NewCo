# NewCo - Real Estate Tools
Real Estate NewCo 2025

## Athens-Clarke County School District Lookup Tool

A comprehensive Python tool to help home buyers in Athens-Clarke County, Georgia research which school attendance zones properties belong to **AND** get detailed school performance data.

### Features

**School Assignment:**
- ✅ **Street Index Lookup**: Uses official Clarke County Schools street index for accurate assignments
- ✅ **Address Normalization**: Handles variations like "St" vs "Street", "Ave" vs "Avenue"
- ✅ **Parameter Matching**: Handles complex address ranges ("497 and below", "odd numbers only", etc.)
- ✅ **Multi-Level**: Returns Elementary, Middle, and High school assignments

**School Performance Data (NEW!):**
- ✅ **Test Scores**: Georgia Milestones EOG/EOC proficiency rates by subject
- ✅ **Graduation Rates**: 4-year cohort graduation rates for high schools
- ✅ **SAT Scores**: Average SAT scores for high schools
- ✅ **Demographics**: Student enrollment, economic status, racial composition
- ✅ **Trend Analysis**: Automated identification of achievements and areas for improvement
- ✅ **Complete Reports**: Combined school assignment + performance data in one lookup

### Quick Start

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `shapely` - For spatial/geometric operations
- `geopy` - For geocoding addresses
- `requests` - For downloading data

#### 2. Data Setup

The tool uses:
- **Street Index**: Official Clarke County Schools street index (included in `data/street_index.pdf`)
- **Performance Data**: Downloaded from Georgia GOSA (Governor's Office of Student Achievement)

The street index data is already extracted and ready to use in `data/street_index.json`.

The performance data is already downloaded and stored in `data/performance/`.

#### 3. Run the Complete Lookup Tool

```bash
python3 school_info.py
```

This will show school assignments AND performance data for three test addresses.

Or look up a specific address:

```bash
python3 school_info.py "123 Main Street, Athens, GA 30601"
```

### Usage

#### Method 1: Complete School Information (RECOMMENDED)

Get both school assignments AND performance data:

```python
from school_info import get_school_info, format_complete_report

# Get complete information
info = get_school_info("150 Hancock Avenue, Athens, GA 30601")

# Display formatted report
print(format_complete_report(info))

# Or access data programmatically
print(f"Elementary: {info.elementary}")
print(f"Test Scores: {info.elementary_performance.test_scores}")
print(f"Demographics: {info.elementary_performance.demographics}")
```

#### Method 2: School Assignment Only

If you only need to know which schools serve an address:

```python
from street_index_lookup import lookup_school_district

assignment = lookup_school_district("150 Hancock Avenue, Athens, GA 30601")

print(f"Elementary: {assignment.elementary}")
print(f"Middle: {assignment.middle}")
print(f"High: {assignment.high}")
```

#### Method 3: School Performance Only

If you already know the school name and want performance data:

```python
from school_performance import get_school_performance, format_performance_report

perf = get_school_performance("Barrow Elementary")

print(format_performance_report(perf))

# Or access specific data
for score in perf.test_scores:
    print(f"{score.subject}: {score.total_proficient_pct}% proficient")
```

### How It Works

**School Assignment:**
1. **Address Parsing**: Extracts house number and street name
2. **Street Normalization**: Standardizes street names (Avenue→ave, Street→st, etc.)
3. **Index Lookup**: Searches official Clarke County Schools street index
4. **Parameter Matching**: Verifies house number matches address range rules
5. **Results**: Returns elementary, middle, and high school assignments

**Performance Data:**
1. **Data Loading**: Parses CSV files from Georgia GOSA (2023-24 school year)
2. **School Matching**: Flexible name matching handles variations
3. **Metric Extraction**: Pulls test scores, demographics, graduation rates, SAT scores
4. **Analysis**: Automatically identifies achievements and areas for improvement
5. **Reporting**: Formats comprehensive performance reports

### Test Results

The tool was tested and verified with these Athens addresses:

| Address | Elementary | Middle | High |
|---------|-----------|--------|------|
| 150 Hancock Avenue, Athens, GA 30601 | Barrow Elementary | Clarke Middle | Clarke Central High |
| 585 Reese Street, Athens, GA 30601 | Johnnie L. Burks Elementary | Clarke Middle | Clarke Central High |
| 195 Hoyt Street, Athens, GA 30601 | Barrow Elementary | Clarke Middle | Clarke Central High |

**Performance data includes:**
- Test proficiency rates (Georgia Milestones EOG/EOC)
- Student demographics and enrollment
- Graduation rates (high schools)
- SAT scores (high schools)
- Automated achievement/concern analysis

### Files

**Main Tools:**
- `school_info.py` - **MAIN TOOL**: Combined lookup (assignments + performance)
- `school_performance.py` - School performance data module (test scores, demographics, etc.)
- `street_index_lookup.py` - Street index-based school assignment lookup
- `extract_full_street_index.py` - PDF parser to extract street index data
- `school_district_lookup.py` - Legacy GIS-based lookup tool

**Data:**
- `data/street_index.json` - Extracted street-to-school mappings (1,957 entries)
- `data/street_index.pdf` - Official Clarke County Schools street index
- `data/performance/*.csv` - Georgia GOSA school performance data (2023-24)

**Utilities:**
- `parse_street_index.py` - Street index parsing utilities
- `requirements.txt` - Python package dependencies

### Troubleshooting

**"No school zone data found"**: The GeoJSON files aren't in the `data/` directory. Follow the download instructions above.

**Geocoding Errors**: Check internet connection or verify the address is in Athens-Clarke County, GA.

**Import Errors**: Install dependencies with `pip install shapely geopy requests`

### Data Sources

- **Clarke County Schools Street Index**: https://www.clarke.k12.ga.us/page/school-attendance-zones
- **Georgia GOSA (School Performance Data)**: https://gosa.georgia.gov/dashboards-data-report-card/downloadable-data
  - Test Scores (Georgia Milestones EOG/EOC)
  - Graduation Rates
  - SAT Scores
  - Student Demographics
- **Athens-Clarke County Open Data Portal**: https://data-athensclarke.opendata.arcgis.com/

### Important Notes

⚠️ **Disclaimer**:
- School attendance zones and performance data can change year-to-year
- Performance data is from the 2023-24 school year
- Always verify school assignments with Clarke County School District official sources
- This tool is for research and informational purposes only
- Not affiliated with Clarke County School District, Athens-Clarke County government, or Georgia Department of Education
- School performance should be considered as one of many factors in housing decisions
