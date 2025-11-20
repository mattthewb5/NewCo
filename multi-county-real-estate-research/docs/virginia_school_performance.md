# Virginia School Performance Data Integration

**Last Updated:** November 20, 2025
**Status:** 🟡 In Progress - Data source integration framework complete, awaiting data access

## Overview

This document describes the integration of Virginia school performance metrics to enrich LCPS school assignments with academic data valuable for home buyers.

## Data Sources

### Primary Source: Virginia Department of Education (VDOE)

**Official Data Portal:**
- **Statistics & Reports**: https://www.doe.virginia.gov/data-policy-funding/data-reports/statistics-reports
- **Enrollment & Demographics**: https://www.doe.virginia.gov/data-policy-funding/data-reports/statistics-reports/enrollment-demographics
- **Open Data Portal**: https://data.virginia.gov/dataset/virginia-department-of-education-statistics-reports
- **Researchers & Developers**: http://www.pen.k12.va.us/statistics_reports/research_data/index.shtml

**Virginia School Quality Profiles:**
- **Website**: https://schoolquality.virginia.gov
- **Individual School Pages**: https://schoolquality.virginia.gov/schools/{school-name}
- **Data Downloads**: https://schoolquality.virginia.gov/download-data

### Secondary Source: Virginia Open Data Portal

**Available Datasets:**
- **State Test-by-Test 2017-2023**: SOL test results by subject with pass rates
  - URL: https://data.virginia.gov/dataset/state-test-by-test
  - Format: CSV (state_pass_rates_by_test_2017-2023.CSV)
  - Note: 2019-2020 data unavailable due to COVID

- **Division Test-by-Test 2020-2023**: District-level SOL pass rates
  - URL: https://data.virginia.gov/dataset/division-test-by-test-2020-2023
  - Format: CSV
  - Level: Division (district) aggregated

- **Fall Membership Enrollment**: Student counts by school, grade, ethnicity, gender
  - Collected annually on September 30
  - Format: CSV
  - Level: School-level detail available

**API Access:**
- Socrata Open Data API (SODA) provides programmatic access
- CKAN API for catalog access

## Available Performance Metrics

Based on research (verified via SchoolDigger for Cedar Lane Elementary):

### Core Metrics Available:

| Metric | Source | Example (Cedar Lane ES) | Notes |
|--------|--------|-------------------------|-------|
| **Enrollment** | VDOE Fall Membership | 698 students (2023-24) | Annual snapshot Sept 30 |
| **Student-Teacher Ratio** | VDOE Staffing Data | 12.9:1 | Lower is typically better |
| **SOL Test Scores** | VDOE SOL Results | Math, Reading, Science pass rates | By grade and subject |
| **School Rankings** | Calculated from SOL | Top 15% in Virginia | Relative performance |
| **Demographics** | VDOE Enrollment | 44% White, 29% Asian, 12% Hispanic, 8% Two or more, 7% African American | Student population breakdown |
| **Accreditation Status** | Virginia School Quality Profiles | Accredited / Accredited with Conditions / etc. | State accountability |

### Additional Metrics (When Available):

- Average Standard Score (SchoolDigger calculated metric)
- College Readiness Index (high schools)
- Graduation Rates (high schools)
- Chronic Absenteeism Rates
- Teacher Quality Indicators
- School Safety Metrics

## School Identification System

**Virginia uses a dual identifier system:**

1. **Division Number** (3 digits): School district code
   - Example: Loudoun County = Division 053

2. **School Number** (3 digits): School within division
   - Example: Cedar Lane Elementary = 109
   - Elementary: 100-199
   - Middle: 200-299
   - High: 300-399
   - Other: 400+, 500+ (admin)

3. **Combined Identifier**: Division Number + School Number
   - Example: 053109 = Loudoun County, Cedar Lane Elementary

4. **School Code** (3-4 characters): Short code used by LCPS
   - Example: CED (Cedar Lane Elementary), TMS (Trailside Middle), SBH (Stone Bridge High)

## Data Access Strategy

### Current Status (November 2025)

**Connection Issues:**
- Virginia School Quality Profiles: 503 Service Unavailable
- VDOE Enrollment pages: 403 Forbidden / SSL errors
- SchoolDigger: 403 Forbidden (bot protection)

**Recommended Approach:**

1. **Short-term (Phase 3A - Current)**:
   - Implement data structure and enrichment framework
   - Create stub implementation with mock data for testing
   - Document integration points

2. **Medium-term (Phase 3B - Next)**:
   - Download VDOE CSV files when sites are accessible
   - Create local data cache (JSON or SQLite)
   - Implement CSV parsing and school matching logic

3. **Long-term (Future Enhancement)**:
   - Integrate Socrata API for automated updates
   - Set up periodic data refresh (annually after Sept 30 enrollment)
   - Add Virginia School Quality Profiles API if/when available

### Implementation Pattern

```python
# Pattern: Try multiple sources in order of preference
def get_performance_data(school_id, school_name):
    # 1. Try local cache (fast, reliable)
    data = check_local_cache(school_id)
    if data:
        return data

    # 2. Try official API (if available)
    data = query_virginia_api(school_id)
    if data:
        cache_data(school_id, data)
        return data

    # 3. Try CSV data files (batch import)
    data = lookup_csv_data(school_id)
    if data:
        cache_data(school_id, data)
        return data

    # 4. Fallback to third-party (SchoolDigger, GreatSchools)
    # Note: Respect rate limits and terms of service
    data = query_third_party(school_name)
    if data:
        cache_data(school_id, data)
        return data

    # 5. Return None if all sources fail
    return None
```

## Integration Status

### ✅ Completed

- [x] Research Virginia data sources
- [x] Document available metrics
- [x] Identify school identifier system
- [x] Design data enrichment architecture

### 🔄 In Progress

- [ ] Download VDOE CSV files (blocked by site access issues)
- [ ] Implement CSV parsing and caching
- [ ] Create school matching logic (LCPS code → VDOE school number)

### ⏳ Pending

- [ ] Integrate real performance data
- [ ] Test with all 3 LCPS addresses
- [ ] Add data freshness indicators
- [ ] Implement automated data updates

## Test Results

### Cedar Lane Elementary (Ashburn)

**School Identifiers:**
- LCPS Code: CED
- School Number: 109
- Division: 053 (Loudoun County)
- Full ID: 053109

**Expected Performance Data** (from SchoolDigger research):
- Enrollment: 698 students (2023-24)
- Student-Teacher Ratio: 12.9:1
- Ranking: Top 15% in Virginia (150th of 1114 elementary schools)
- Average Standard Score: 83.12
- Demographics:
  - White: 44%
  - Asian: 29%
  - Hispanic: 12%
  - Two or more races: 8%
  - African American: 7%

### Tuscarora High School (Leesburg)

**School Identifiers:**
- LCPS Code: THS
- School Number: 314
- Division: 053
- Full ID: 053314

**Expected Performance Data:**
- Enrollment: TBD
- Graduation Rate: TBD
- College Readiness: TBD
- SOL Pass Rates: TBD

### Mountain View Elementary (Purcellville)

**School Identifiers:**
- LCPS Code: MTV
- School Number: 132
- Division: 053
- Full ID: 053132

**Expected Performance Data:**
- Enrollment: TBD
- Student-Teacher Ratio: TBD
- SOL Pass Rates: TBD

## Sample Data Format

### JSON Structure for Cached Data

```json
{
  "school_id": "053109",
  "lcps_code": "CED",
  "school_name": "Cedar Lane Elementary",
  "division": "053",
  "division_name": "Loudoun County Public Schools",
  "school_type": "Elementary",

  "performance": {
    "enrollment": 698,
    "student_teacher_ratio": 12.9,
    "accreditation_status": "Fully Accredited",

    "sol_scores": {
      "reading": {
        "grade_3": 85.2,
        "grade_4": 87.5,
        "grade_5": 89.1
      },
      "math": {
        "grade_3": 82.3,
        "grade_4": 84.7,
        "grade_5": 86.2
      },
      "science": {
        "grade_5": 88.4
      }
    },

    "demographics": {
      "white": 44,
      "asian": 29,
      "hispanic": 12,
      "two_or_more": 8,
      "african_american": 7
    },

    "rankings": {
      "state_rank": 150,
      "state_total": 1114,
      "percentile": 86.5
    }
  },

  "metadata": {
    "data_source": "VDOE",
    "school_year": "2023-2024",
    "last_updated": "2025-11-20",
    "cache_expires": "2026-09-30"
  }
}
```

## Next Steps

1. **Monitor VDOE site availability** - Check periodically for data access
2. **Create data cache structure** - Design local storage for performance metrics
3. **Implement stub enrichment** - Add framework with mock data for testing
4. **Document limitations** - Clearly communicate when live data is/isn't available
5. **Plan data refresh strategy** - Annual updates after fall enrollment

## Resources

- **VDOE Contact**: Susan M. Williams (dataset publisher)
- **LCPS Planning**: (571) 252-1000, lcpsplan@lcps.org
- **Virginia School Quality Profiles**: Individual school pages provide detailed metrics

## Notes

**Current Challenges:**
- VDOE websites experiencing intermittent connection issues (Nov 2025)
- No public API currently available (file downloads only)
- School identifier matching requires careful mapping between LCPS codes and VDOE school numbers

**Advantages of Integrated Performance Data:**
- Significantly increases value for home buyers
- Provides objective academic quality metrics
- Enables comparison across neighborhoods
- Shows enrollment trends and school capacity

**Privacy & Ethics:**
- All data is publicly available from VDOE
- Aggregated metrics only (no student-level data)
- Demographic data helps understand school diversity
- Rankings should be contextualized, not used in isolation
