# LCPS School Locator API Research - FINDINGS

**Date:** November 19, 2025
**Status:** ✅ API FOUND AND WORKING
**Phase:** 3 - School Data (Week 4)

---

## ✅ SUCCESS: ArcGIS REST API Found!

### API Endpoint Discovered

**Base Service:** https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer

**Platform:** ArcGIS REST API (same as zoning!)

**Layers:**
- Layer 0: School Sites (point locations with full school information)
- Layer 1: Elementary School Zones (attendance boundaries)
- Layer 2: Middle School Zones (attendance boundaries)
- Layer 3: High School Zones (attendance boundaries)

---

## API Structure

### Layer 0: School Sites

**Purpose:** Contains school details (names, codes, types)

**Key Fields:**
- `NAME` - Full school name (e.g., "CEDAR LANE ES")
- `SCH_CODE` - School code (e.g., "CED")
- `CLASS` - School type (ELEMENTARY, MIDDLE, HIGH)
- `SCH_NUM` - School number (e.g., 109)
- `DATE_OPENED` - Year opened (e.g., "1999")

**Query Format:**
```
https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer/0/query?where=SCH_CODE='CED'&outFields=*&returnGeometry=false&f=json
```

---

### Layer 1: Elementary School Zones

**Purpose:** Polygon boundaries for elementary school attendance zones

**Key Fields:**
- `ES_SCH_CODE` - Elementary school code (links to Layer 0 SCH_CODE)
- `ES_ELEM` - School number
- `SHAPE_Length` - Boundary perimeter
- `SHAPE_Area` - Boundary area

**Query Format (Point-in-Polygon):**
```
https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer/1/query?geometry=-77.4875,39.0437&geometryType=esriGeometryPoint&spatialRel=esriSpatialRelIntersects&inSR=4326&outFields=*&returnGeometry=false&f=json
```

---

### Layer 2: Middle School Zones

**Purpose:** Polygon boundaries for middle school attendance zones

**Key Fields:**
- `MS_SCH_CODE` - Middle school code
- `MS_INT` - School number

**Query Format:** Same as Layer 1, use Layer 2 endpoint

---

### Layer 3: High School Zones

**Purpose:** Polygon boundaries for high school attendance zones

**Key Fields:**
- `HS_SCH_CODE` - High school code
- `HS_HIGH` - School number

**Query Format:** Same as Layer 1, use Layer 3 endpoint

---

## Test Results ✅

**Test Location:** Ashburn, VA (39.0437, -77.4875)

### Elementary School
**Query:** Layer 1 with Ashburn coordinates
**Result:** School code "CED"
**Lookup:** Layer 0 where SCH_CODE='CED'
**School:** ✅ **CEDAR LANE ES** (opened 1999)

### Middle School
**Query:** Layer 2 with Ashburn coordinates
**Result:** School code "TMS"
**Lookup:** Layer 0 where SCH_CODE='TMS'
**School:** ✅ **TRAILSIDE MS** (opened 2014)

### High School
**Query:** Layer 3 with Ashburn coordinates
**Result:** School code "SBH"
**Lookup:** Layer 0 where SCH_CODE='SBH'
**School:** ✅ **STONE BRIDGE HS** (opened 2000)

---

## Integration Strategy

### Two-Step Process

**Step 1: Get School Codes (Zone Lookup)**
- Query Layer 1, 2, and 3 with lat/lon
- Extract school codes from each layer
- 3 API calls (one per level)

**Step 2: Get School Details (Name Lookup)**
- Query Layer 0 with school codes
- Get full school names, types, dates
- 3 API calls (one per school)

**Total:** 6 API calls per address lookup

### Field Mappings

| Our Field | Elementary Layer | Middle Layer | High Layer | School Sites |
|-----------|------------------|--------------|------------|--------------|
| school_code | ES_SCH_CODE | MS_SCH_CODE | HS_SCH_CODE | SCH_CODE |
| school_name | N/A | N/A | N/A | NAME |
| school_type | N/A | N/A | N/A | CLASS |
| school_num | ES_ELEM | MS_INT | HS_HIGH | SCH_NUM |
| date_opened | N/A | N/A | N/A | DATE_OPENED |

---

## Spatial Query Parameters

**Critical Parameters (from Phase 1 zoning success):**
- `geometry`: lon,lat (e.g., "-77.4875,39.0437")
- `geometryType`: "esriGeometryPoint"
- `spatialRel`: "esriSpatialRelIntersects"
- `inSR`: "4326" ⚠️ **CRITICAL** (WGS84 spatial reference)
- `outFields`: "*" (all fields)
- `returnGeometry`: "false" (we only need attributes)
- `f`: "json" (JSON response format)

---

## Comparison to Phase 1 (Zoning) & Phase 2 (Crime)

### Phase 1 (Zoning) ✅
- Platform: ArcGIS REST API
- Data: Real-time from Loudoun GIS
- Integration: Successful
- Status: Operational

### Phase 2 (Crime) ❌
- Platform: Power BI (no API)
- Data: Visualization only
- Integration: Blocked
- Status: Pending LCSO contact

### Phase 3 (Schools) ✅
- Platform: ArcGIS REST API (same as zoning!)
- Data: Real-time from Loudoun GIS
- Integration: Ready to implement
- Status: API found and tested ✅

---

## Implementation Plan

### Step 1: Create school_api_lcps.py ✅ NEXT

**Module:** `core/school_api_lcps.py`

**Functions:**
- `get_schools(lat, lon)` - Main entry point
- `_query_zone(layer_id, lat, lon)` - Get school code from zone
- `_query_school_details(school_code)` - Get school name/info
- `_parse_response()` - Convert JSON to School objects

### Step 2: Update school_lookup.py

**File:** `core/school_lookup.py`

**Change:** Update `_query_school_api()` to use LCPS module for Loudoun

### Step 3: Update config/loudoun.py

**Changes:**
```python
school_api_endpoint="https://logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer",
school_boundary_tool_url="https://www.lcps.org/o/support/page/school-attendance-zone-maps",
has_school_data=True,  # ✅ Phase 3 complete
```

### Step 4: Create Integration Tests

**File:** `tests/test_lcps_integration.py`

**Test Locations:**
1. Ashburn (39.0437, -77.4875) - Suburban
2. Leesburg (39.1156, -77.5636) - Town
3. Purcellville (39.1376, -77.7128) - Rural

### Step 5: Documentation

**Create:** `docs/PHASE_3_COMPLETE.md`

Similar to Phase 1 completion document

---

## Additional School Information

### What's Available

**From GIS Data:**
- ✅ School names
- ✅ School codes
- ✅ School types (Elementary, Middle, High)
- ✅ School numbers
- ✅ Year opened
- ✅ Attendance zone boundaries

**NOT Available from GIS:**
- ❌ School addresses
- ❌ Phone numbers
- ❌ Websites
- ❌ Principal names
- ❌ Enrollment numbers
- ❌ Test scores
- ❌ Student-teacher ratios

### Future Enhancement: Virginia School Quality Profiles

**Source:** https://schoolquality.virginia.gov

**Data Available:**
- Performance metrics
- Test scores
- Demographics
- Ratings

**Status:** Phase 3B (future enhancement)

**Implementation:** Separate API call to enrich school data

---

## Key Findings

1. ✅ LCPS data accessible via ArcGIS REST API
2. ✅ Same platform as successful zoning integration
3. ✅ Spatial queries work perfectly
4. ✅ All three school levels available (E/M/H)
5. ✅ Real-time data from official source
6. ✅ No authentication required (public access)
7. ✅ Tested with real coordinates - works!

---

## Success Criteria Met

- ✅ Found LCPS School Locator (multiple tools)
- ✅ Identified API endpoint (ArcGIS REST)
- ✅ Tested query returns data
- ✅ Mapped field names
- ✅ Verified all three school levels
- ⏳ Update configuration (next step)
- ⏳ Integration code (next step)
- ⏳ Integration tests (next step)

---

## Timeline Estimate

**Remaining Work:** 2-3 hours

**Breakdown:**
- Create school_api_lcps.py - 1 hour
- Update school_lookup.py - 15 min
- Update config/loudoun.py - 5 min
- Create integration tests - 30 min
- Run tests and verify - 15 min
- Documentation - 30 min

**Status:** Ready to implement immediately!

---

## Comparison: Research Time

**Phase 2 (Crime):** 45 minutes
- Result: ❌ No API found
- Outcome: Blocked, requires LCSO contact

**Phase 3 (Schools):** 30 minutes
- Result: ✅ API found and tested
- Outcome: Ready to integrate immediately

**Lesson:** ArcGIS REST APIs are reliable and discoverable

---

## Next Steps

1. ✅ Research complete
2. ⏳ Create school_api_lcps.py
3. ⏳ Integrate with school_lookup.py
4. ⏳ Update config
5. ⏳ Test with real data
6. ⏳ Document Phase 3 completion

---

**Research completed:** November 19, 2025
**API endpoint:** logis.loudoun.gov/gis/rest/services/COL/Schools/MapServer
**Status:** ✅ Ready for integration
**Next:** Create integration module

---

## Sample API Responses

### Elementary Zone Query
```json
{
  "features": [{
    "attributes": {
      "OBJECTID": 9,
      "ES_ELEM": 109,
      "ES_SCH_CODE": "CED"
    }
  }]
}
```

### School Details Query
```json
{
  "features": [{
    "attributes": {
      "OBJECTID": 29,
      "SCH_CODE": "CED",
      "CLASS": "ELEMENTARY",
      "SCH_NUM": 109,
      "NAME": "CEDAR LANE ES",
      "DATE_OPENED": "1999"
    }
  }]
}
```

---

**Success!** Phase 3 API research complete with working endpoint! 🎉
