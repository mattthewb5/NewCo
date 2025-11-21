# Loudoun County Crime Data API Investigation

**Date:** November 21, 2025
**Purpose:** Investigate potential API endpoints for Loudoun County crime data (Phase 2)
**Status:** ⚠️ CHALLENGING - No official public API available

---

## Executive Summary

Loudoun County Sheriff's Office (LCSO) provides crime data through **two primary platforms**:
1. **Power BI Crime Dashboard** (launched August 2024)
2. **CityProtect.com** (third-party service)

**Key Finding:** Neither platform offers an **official, documented public API** for programmatic access. However, both use undocumented APIs that could potentially be reverse-engineered.

**Recommendation:** Explore alternative approaches or contact LCSO directly for data sharing agreement.

---

## Investigation Results

### 1. Power BI Crime Dashboard

**URL:** https://sheriff.loudoun.gov/crimedashboard
**Platform:** Microsoft Power BI Government Cloud
**Launch Date:** August 2024
**Update Frequency:** Nightly at ~12:00 AM EST

#### Technical Details

**Power BI Embed URL:**
```
https://app.powerbigov.us/view?r=eyJrIjoiZTgyMTFiZjktMDg4MC00MmZjLTlmZGQtMjg1YjQ5ODY3NmNhIiwidCI6IjU5MGYxNzAyLThhMzYtNDkzMS04ZjJmLWQzNWEwNmRkYzRjOCJ9
```

**Extracted IDs:**
- **Report ID:** `e8211bf9-0880-42fc-9fdd-285b498676ca`
- **Tenant ID:** `590f1702-8a36-4931-8f2f-d35a06ddc4c8`
- **Cloud:** US Government (`usgovcloudapi.net`)

**API Endpoints Identified:**
- `/public/reports/querydata` - Data query endpoint (undocumented)
- `/public/reports/conceptualschema` - Schema endpoint
- `/public/reports/modelsAndExploration` - Models endpoint
- **Cluster URI:** `https://wabi-us-gov-virginia-redirect.analysis.usgovcloudapi.net/`

**Access Type:** Public/Anonymous Embed (no authentication required)

#### Challenges

1. **Undocumented API:** Microsoft does not officially document the `/querydata` endpoint
2. **Official Recommendation:** Use ADOMD.NET or OleDb provider (requires .NET framework)
3. **Complex Query Structure:** Requires SemanticQueryDataShapeCommand JSON structures
4. **No Examples:** Zero public documentation or code examples for public reports
5. **Risk:** Undocumented APIs can change without notice

**Stack Overflow Finding:**
> "I can't find any documentation on this anywhere. I don't know if this is some secret API or what."
> Microsoft Response: "The only documented way to use this API is through the ADOMD.NET or OleDb provider."

---

### 2. CityProtect Platform

**URL:** https://cityprotect.com
**Provider:** Motorola Solutions
**Loudoun Integration:** Primary public crime mapping interface

#### Background

- **CityProtect** replaced **CrimeReports.com** in 2019
- **API Discontinuation:** When Motorola parted with Socrata (acquired by Tyler Technologies), all public APIs were discontinued
- **Impact:** Over 400 open crime datasets nationwide lost public API access
- **Current Status:** Web-based interface only (officially)

#### Technical Details

**Data Access Methods:**
1. **Web Interface:** Interactive map and search (public)
2. **Daily Incident Reports:** PDF archives (Monday-Friday)
3. **Undocumented API:** Used internally by CityProtect web app

**Reverse Engineering:**
- GitHub repository `EricTurner3/CrimeAnalysis` contains Python scripts
- Scripts access CityProtect's undocumented API using same endpoints as web app
- Retrieves incident data with lat/lng coordinates for GIS use
- **Note:** Indianapolis PD example, not Loudoun-specific

**Challenges:**
1. **No Official API:** Motorola discontinued all public APIs
2. **Undocumented Endpoints:** Requires reverse engineering browser network traffic
3. **Agency-Specific:** Each agency may have different endpoint structures
4. **Terms of Service Risk:** Undocumented API use may violate ToS
5. **Maintenance Burden:** Endpoints can change without notice

---

### 3. Loudoun County GIS Services

**Investigated:** Loudoun County GeoHub and Public Safety MapServer

**GeoHub:** https://geohub-loudoungis.opendata.arcgis.com/
**Public Safety Hub:** https://publicsafety-loudoungis.opendata.arcgis.com/
**MapServer:** https://logis.loudoun.gov/gis/rest/services/COL/PublicSafety/MapServer

#### MapServer Layers (12 total)

| Layer ID | Name | Contains Crime Data? |
|----------|------|---------------------|
| 0 | Public Safety Station | No (facilities) |
| 1 | Rural Water Supply | No (infrastructure) |
| 2-5, 7-8 | Fire Hydrants | No (infrastructure) |
| 9 | Fire Box Areas | No (zones) |
| 10 | Fire First Due Area | No (zones) |
| 11 | LCSO Patrol Sectors | No (boundaries) |
| 12 | EMS First Due Areas | No (zones) |

**Finding:** ❌ **No crime incident data layers available** in Loudoun County GIS services

The Public Safety MapServer contains only:
- Infrastructure (fire hydrants, water supply)
- Jurisdictional boundaries (patrol sectors, fire districts)
- Facility locations (stations)

**Contrast with Athens-Clarke:**
- Athens has direct ArcGIS FeatureServer with crime incidents
- Loudoun relies on Power BI dashboard and CityProtect instead

---

### 4. Official Data Sources Summary

| Source | Format | Update Frequency | Programmatic Access |
|--------|--------|------------------|-------------------|
| **Power BI Dashboard** | Interactive visualization | Daily (12 AM) | ❌ No official API |
| **CityProtect** | Web map + search | Real-time | ❌ No official API |
| **Daily Incident Reports** | PDF | Mon-Fri | ❌ Manual download |
| **GIS Services** | ArcGIS REST | N/A | ❌ No crime layers |
| **Quarterly Reports** | PDF | Quarterly | ❌ Manual download |

---

## Comparison: Athens-Clarke vs Loudoun

| Feature | Athens-Clarke County | Loudoun County |
|---------|---------------------|----------------|
| **Data Platform** | ArcGIS FeatureServer | Power BI + CityProtect |
| **API Type** | Documented REST API | Undocumented only |
| **Authentication** | None (public) | None (public embeds) |
| **Query Format** | Standard ArcGIS | Complex JSON structures |
| **Geographic Search** | Built-in spatial queries | Requires reverse engineering |
| **Documentation** | Extensive (Esri) | None (Microsoft/Motorola) |
| **Stability** | High (standard API) | Low (undocumented) |
| **Implementation Difficulty** | Easy | Very Difficult |

**Athens Advantage:** Standard, documented, stable ArcGIS REST API makes implementation straightforward.

**Loudoun Challenge:** No standard API requires reverse engineering or data sharing agreements.

---

## Recommended Approaches

### Option 1: Official Data Sharing Agreement ⭐ **RECOMMENDED**

**Approach:** Contact LCSO directly to request:
1. Bulk data export (CSV/JSON)
2. API access credentials
3. Data sharing agreement for research/public service

**Pros:**
- ✅ Legal and compliant
- ✅ Stable and supported
- ✅ May include additional fields not in public dashboard
- ✅ Official documentation and support
- ✅ Sustainable long-term

**Cons:**
- ⏱️ Requires negotiation and approval process
- ⏱️ May take weeks/months
- ❓ May be denied for privacy/policy reasons

**Contact:**
- Loudoun County Sheriff's Office
- Data/Technology Services Division
- Reference: Public benefit research project

---

### Option 2: Reverse Engineer CityProtect API ⚠️ **RISKY**

**Approach:** Analyze browser network traffic to identify CityProtect endpoints

**Steps:**
1. Open CityProtect for Loudoun in browser
2. Use DevTools Network tab to capture API calls
3. Identify query patterns and parameters
4. Replicate requests in Python
5. Reference: `EricTurner3/CrimeAnalysis` GitHub repo

**Pros:**
- ✅ No approval needed
- ✅ Immediate access
- ✅ Can query by location/date

**Cons:**
- ❌ May violate Terms of Service
- ❌ Endpoints can change without notice
- ❌ High maintenance burden
- ❌ Legal risk
- ❌ No support or documentation
- ❌ Ethical concerns (using undocumented APIs)

**Risk Level:** 🔴 **HIGH**

---

### Option 3: Reverse Engineer Power BI Dashboard ⚠️ **VERY RISKY**

**Approach:** Construct SemanticQueryDataShapeCommand queries for Power BI

**Requirements:**
1. Understand Power BI query language structure
2. Extract schema from `/conceptualschema` endpoint
3. Build complex JSON query structures
4. Handle pagination and result limits

**Pros:**
- ✅ Data is public (anonymous embed)
- ✅ Updated nightly by LCSO

**Cons:**
- ❌ Extremely complex query format
- ❌ Zero documentation
- ❌ Microsoft explicitly discourages this approach
- ❌ Likely to break with Power BI updates
- ❌ May require reverse engineering significant JavaScript
- ❌ Very high technical complexity

**Risk Level:** 🔴 **VERY HIGH**

---

### Option 4: Manual/Semi-Automated PDF Parsing ⚠️ **LIMITED**

**Approach:** Parse Daily Incident Reports (PDFs)

**Pros:**
- ✅ Officially provided data
- ✅ Legal and compliant
- ✅ Regular updates (Mon-Fri)

**Cons:**
- ❌ PDFs are summary reports, not detailed incident data
- ❌ Requires OCR/PDF parsing
- ❌ Limited geographic detail
- ❌ No historical data beyond archives
- ❌ Labor-intensive
- ❌ Data quality/consistency issues

**Feasibility:** 🟡 **LOW** - Not suitable for real-time address queries

---

### Option 5: Defer Phase 2 (Crime) for Loudoun 💡 **PRAGMATIC**

**Approach:** Launch Loudoun with schools + zoning only (Phase 1 + Phase 3)

**Rationale:**
- Phase 1 (Zoning): ✅ Already working with ArcGIS REST API
- Phase 3 (Schools): ✅ Already complete with LCPS API
- Phase 2 (Crime): ⏸️ Defer until official API available

**Pros:**
- ✅ Avoid legal/ethical risks
- ✅ Focus on what works well (schools + zoning)
- ✅ Athens still has full crime data
- ✅ Can add Loudoun crime later when API available
- ✅ Honest assessment: Multi-county UI shows feature availability per county

**Implementation:**
```python
# config/loudoun.py
LOUDOUN_CONFIG = CountyConfig(
    county_name="loudoun",
    # ...
    has_crime_data=False,  # Defer Phase 2
    crime_data_source=None,
    crime_api_endpoint=None,
    # ...
)
```

**User Experience:**
```
Multi-County UI:
┌─────────────────────────────┐
│ Select County: ▼ Loudoun    │
├─────────────────────────────┤
│ ✅ Schools                   │
│ ❌ Crime (Coming Soon)       │
│ ✅ Zoning                    │
└─────────────────────────────┘
```

---

## Decision Matrix

| Approach | Difficulty | Risk | Time to Implement | Sustainability | Recommendation |
|----------|-----------|------|-------------------|----------------|----------------|
| **Official Agreement** | Medium | Low | Weeks-Months | High | ⭐⭐⭐⭐⭐ |
| **Defer Phase 2** | None | None | 0 hours | High | ⭐⭐⭐⭐ |
| **CityProtect Reverse** | High | High | Days-Weeks | Low | ⭐⭐ |
| **Power BI Reverse** | Very High | Very High | Weeks | Very Low | ⭐ |
| **PDF Parsing** | High | Low | Weeks | Medium | ⭐ |

---

## Recommendations Summary

### Immediate Action (Next 48 hours):

**Proceed with multi-county UI using Option 5 (Defer Phase 2 for Loudoun)**

1. ✅ **Launch Loudoun with Schools + Zoning** (Phases 1 & 3)
2. ✅ **Keep Athens with full suite** (Schools + Crime + Zoning)
3. ✅ **Feature flags in UI** show what's available per county
4. ✅ **Honest communication** to users about data availability

### Medium-Term (Next 1-3 months):

**Pursue Option 1 (Official Data Sharing Agreement)**

1. 📧 **Contact LCSO** Technology/Data Services Division
2. 📄 **Explain use case:** Public benefit research tool
3. 🤝 **Request:** API access or bulk data export
4. 📋 **Offer:** Data citation, usage statistics, feedback

### Long-Term:

**Monitor for official API releases:**
- Power BI public report API documentation (Microsoft)
- Loudoun County open data initiatives
- Virginia state-level crime data APIs

---

## Technical Notes

### Power BI Query Example (Theoretical)

```json
{
  "version": "1.0.0",
  "queries": [{
    "Query": {
      "Commands": [{
        "SemanticQueryDataShapeCommand": {
          "Query": {
            "Version": 2,
            "From": [{"Name": "c", "Entity": "Crimes"}],
            "Select": [
              {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Date"}},
              {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Type"}}
            ],
            "Where": [{
              "Condition": {
                "In": {
                  "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Location"}}],
                  "Values": [[{"Literal": {"Value": "'Ashburn'"}}]]
                }
              }
            }]
          }
        }
      }]
    }
  }]
}
```

**Reality:** Above is simplified conceptual example. Actual queries are far more complex and require schema knowledge.

---

## Athens-Clarke API Reference (For Comparison)

**Working Example:**
```python
# Athens Crime API - Simple and Documented
CRIME_API_URL = "https://services2.arcgis.com/xSEULKvB31odt3XQ/arcgis/rest/services/Crime_Web_Layer_CAU_view/FeatureServer/0/query"

params = {
    'where': '1=1',
    'outFields': '*',
    'geometry': f'{lon},{lat}',
    'geometryType': 'esriGeometryPoint',
    'inSR': '4326',
    'distance': 804.67,  # 0.5 miles in meters
    'units': 'esriSRUnit_Meter',
    'spatialRel': 'esriSpatialRelIntersects',
    'returnGeometry': 'true',
    'outSR': '4326',
    'f': 'json'
}

response = requests.get(CRIME_API_URL, params=params)
```

**Key Differences:**
- ✅ Standard REST API with query parameters
- ✅ Documented by Esri (ArcGIS REST API documentation)
- ✅ Spatial queries built-in
- ✅ Stable and widely used
- ✅ No authentication required
- ✅ Returns standard GeoJSON

**Loudoun Equivalent:** Does not exist

---

## Resources

### Official Sources:
- Loudoun Sheriff Crime Dashboard: https://sheriff.loudoun.gov/crimedashboard
- CityProtect: https://cityprotect.com
- Loudoun GeoHub: https://geohub-loudoungis.opendata.arcgis.com/
- Daily Incident Reports: https://sheriff.loudoun.gov/4727/Daily-Incident-Community-Reports

### Technical References:
- Stack Overflow - Power BI querydata: https://stackoverflow.com/questions/56767004/need-documentation-for-analysis-windows-net-public-reports-querydata
- Microsoft Power BI REST API Docs: https://learn.microsoft.com/en-us/rest/api/power-bi/
- GitHub - CrimeAnalysis: https://github.com/EricTurner3/CrimeAnalysis

### News/Background:
- LCSO Launches Crime Dashboard (Aug 2024): https://sheriff.loudoun.gov/m/newsflash/home/detail/10064
- Motorola Ends Open Crime APIs (2019): https://www.govtech.com/biz/Motorola-Parts-with-Socrata-Ends-Access-to-Open-Crime-APIs.html

---

## Conclusion

**For Athens-specific demo:** ✅ Keep as-is with working crime API

**For multi-county expansion:**
- ✅ **Immediate:** Launch with Loudoun schools + zoning (defer crime)
- 🎯 **Medium-term:** Pursue official LCSO data sharing agreement
- 🔮 **Long-term:** Add Loudoun crime when official API becomes available

**Architecture Note:** The county-agnostic design (from compatibility audit) perfectly supports this approach:
```python
if county_config.has_crime_data:
    crime_analysis = analyze_crime(...)
else:
    # Show "Crime data not available for this county" message
```

This maintains system integrity while being honest about data availability.

---

**Investigation Status:** ✅ **COMPLETE**
**Next Steps:** Proceed with multi-county UI using deferred Phase 2 approach
**Revisit:** When LCSO releases official API or grants data access
