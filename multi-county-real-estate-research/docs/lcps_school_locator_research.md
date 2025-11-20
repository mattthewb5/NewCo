# LCPS School Locator Research

**Last Updated:** November 2025
**Phase:** 3 - School Data
**Status:** Research needed

## Overview

From Prompt 1 research (loudoun_county_data_sources.md):
- LCPS (Loudoun County Public Schools) serves entire county
- 98 schools total (much larger than Athens' ~30)
- School locator tool for finding assigned schools
- No jurisdiction complexity (unlike zoning/crime)

## Research Tasks

### Task 1: Find the School Locator

1. Go to https://www.lcps.org
2. Look for "School Locator", "Boundary Finder", "School Assignment"
3. Document the URL

Expected patterns:
- https://www.lcps.org/boundary-finder
- https://www.lcps.org/school-locator
- https://boundaries.lcps.org

### Task 2: Determine API Access

Check if the school locator has:
- Public API endpoint
- Developer documentation
- GIS-based lookup (ArcGIS REST API)
- Input format (address vs lat/lon)

Common patterns for school district APIs:
- ArcGIS REST service (most common)
- Custom API with address lookup
- Third-party service (SchoolDigger, etc.)
- Direct database query tool

### Task 3: Test the Tool

Test with known addresses:
1. Ashburn area (eastern Loudoun)
2. Leesburg area (central Loudoun)
3. Purcellville area (western Loudoun)

Document:
- What schools are assigned
- How data is returned (HTML, JSON, etc.)
- Whether API is available or just web interface

### Task 4: School Performance Data

Research Virginia School Quality Profiles:
1. Go to https://schoolquality.virginia.gov
2. Look for API or data downloads
3. Document available metrics:
   - Test scores
   - Enrollment
   - Student-teacher ratios
   - Demographics
   - Ratings

### Task 5: Data Format Analysis

Document:
- School ID format
- School names (full vs abbreviated)
- Address formats
- Contact information available
- Performance metrics available

## Research Findings

**Date Completed:** November 20, 2025

### LCPS School Locator Tools

**Primary Tool URLs:**
1. **Dashboard:** https://dashboards.lcps.org/extensions/Dashboards/Label.html (Qlik-based)
2. **E-Listing:** https://webinter.lcps.org/lcps_locate/ (ASP.NET-based)

**API Type:**
- [x] ArcGIS REST API ✅ **FOUND!**
- [ ] Custom API with documentation
- [ ] Web interface only (scraping required)
- [ ] Third-party service

**API Endpoint:**
```
Base: https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer
Layer 0: School Sites (points) - School details
Layer 1: Zones - Elementary (polygons)
Layer 2: Zones - Middle (polygons)
Layer 3: Zones - High (polygons)
```

**Input Format:**
- [ ] Address (street address) - Not directly supported
- [x] Coordinates (lat/lon) ✅ **WGS84 (EPSG:4326)**
- [ ] Both

**Output Format:**
- [x] JSON ✅
- [ ] XML
- [ ] HTML
- [ ] Other

**School Levels Returned:**
- [x] Elementary ✅
- [x] Middle ✅
- [x] High ✅
- [ ] Other (special programs, etc.) - Not in zone layers

**Virginia School Quality Profiles:**
- URL: https://schoolquality.virginia.gov
- API available: Need to research separately
- Metrics available: Test scores, enrollment, demographics (to be researched)

### API Structure Details

**Layer 0: School Sites (Point Features)**
- Fields: SCH_CODE, NAME, CLASS, SCH_NUM, DATE_OPENED
- Purpose: School details (name, number, opening date, type)
- Geometry: Points (school locations)

**Layer 1: Elementary Zones (Polygon Features)**
- Fields: ES_ELEM (int), ES_SCH_CODE (string)
- Purpose: Elementary school attendance boundaries
- Geometry: Polygons

**Layer 2: Middle School Zones (Polygon Features)**
- Fields: MS_INT (int), MS_SCH_CODE (string)
- Purpose: Middle school attendance boundaries
- Geometry: Polygons

**Layer 3: High School Zones (Polygon Features)**
- Fields: HS_HIGH (int), HS_SCH_CODE (string)
- Purpose: High school attendance boundaries
- Geometry: Polygons

### Test Results

**Ashburn (39.0437, -77.4875):**
- Elementary: Cedar Lane ES (CED) - School #109, Opened 1999
- Middle: Trailside MS (TMS) - School #215, Opened 2014
- High: Stone Bridge HS (SBH) - School #308, Opened 2000

**Leesburg (39.1156, -77.5636):**
- Elementary: Leesburg ES (LEE) - School #123, Opened 1980
- Middle: Smart's Mill MS (SMM) - School #211, Opened 2004
- High: Tuscarora HS (THS) - School #314, Opened 2010

**Purcellville (39.1376, -77.7128):**
- Elementary: Mountain View ES (MTV) - School #132, Opened 2003
- Middle: Blue Ridge MS (BRM) - School #202, Opened 1971
- High: Loudoun Valley HS (LVH) - School #305, Opened 1962

**✅ All tests successful! API returns accurate school assignments.**

### Query Method

**Step 1: Query zone layers (1, 2, 3) with coordinates**
```
GET https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer/{layer_id}/query

Parameters:
- geometry: {lon},{lat}
- geometryType: esriGeometryPoint
- inSR: 4326 (WGS84)
- spatialRel: esriSpatialRelIntersects
- outFields: *
- returnGeometry: false
- f: json

Returns: School code (ES_SCH_CODE, MS_SCH_CODE, or HS_SCH_CODE)
```

**Step 2: Query school details (layer 0) with school code**
```
GET https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer/0/query

Parameters:
- where: SCH_CODE = '{school_code}'
- outFields: *
- returnGeometry: false
- f: json

Returns: School name, number, opening date, class
```

## Implementation Plan

Based on findings:

1. ✅ Update `school_api_endpoint` in config/loudoun.py
2. ✅ Implement API query in core/school_api_lcps.py
3. ✅ Parse response format and map to School dataclass
4. ✅ Test with multiple addresses (3/3 successful)
5. ⏳ Integrate into school_lookup.py
6. ⏳ Add Virginia School Quality Profiles data (future enhancement)

## Comparison to Athens

**Athens (Clarke County Schools):**
- Uses CSV street index
- ~30 schools
- Manual data file

**Loudoun (LCPS):**
- API-based (expected)
- 98 schools (3x larger)
- Real-time lookup

**Advantages of API:**
- Always current
- No manual data updates
- More accurate boundaries

## TODO

- [ ] Find LCPS School Locator tool
- [ ] Determine API availability
- [ ] Test with known addresses
- [ ] Document data format
- [ ] Research Virginia School Quality Profiles
- [ ] Update config with findings
- [ ] Implement API integration
