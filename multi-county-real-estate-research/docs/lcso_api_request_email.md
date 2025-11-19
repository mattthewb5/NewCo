# LCSO API Access Request Email

**Created:** November 19, 2025
**Purpose:** Request API access to Loudoun County crime data
**Status:** Draft ready to send

---

## Contact Information

**Primary Contact:**
- **Email:** mapping@loudoun.gov
- **Department:** Loudoun County GIS (OMAGI - Office of Mapping and Geographic Information)
- **Source:** Virginia Open Data Portal listing

**Secondary Contact (CC):**
- **Email:** sheriff@loudoun.gov
- **Department:** Loudoun County Sheriff's Office

**Subject Line:**
```
API Access Request: Crime Data for Public Safety Research Tool
```

---

## Email Draft

```
Dear Loudoun County GIS Team and Sheriff's Office,

I am developing a comprehensive real estate research platform that provides prospective homebuyers with detailed neighborhood information for Loudoun County. This tool helps families make informed decisions by combining multiple county data sources into an integrated analysis.

## What I'm Building

A multi-county real estate research platform that integrates:

1. **Zoning Information** (✅ Already Integrated)
   - Successfully using Loudoun County GIS REST API
   - Endpoint: logis.loudoun.gov/gis/rest/services/COL/Zoning/MapServer/3
   - Provides zoning codes, descriptions, and land use data

2. **School Zone Assignments** (In Development)
   - LCPS school boundary data
   - Virginia School Quality Profiles integration

3. **Crime Statistics & Safety Analysis** (Requesting Access)
   - Neighborhood safety trends
   - Crime type categorization
   - Year-over-year comparisons
   - Safety scoring algorithm

## Why Crime Data Matters

Current real estate platforms (Zillow, Realtor.com, etc.) provide minimal crime information, forcing buyers to research safety on their own. My tool will:

- Help families understand neighborhood safety objectively
- Show crime trends over time (increasing/stable/decreasing)
- Compare different areas using consistent methodology
- Provide context homebuyers currently lack

## What I've Discovered

I found the excellent LCSO Crime Dashboard (https://www.loudoun.gov/crimedashboard) launched in August 2025. The Power BI dashboard provides great visualizations, but I need programmatic access to the underlying data for API integration.

My research revealed:
- Data.gov catalog entry (dataset/crime-reports-1cea8) is outdated (2018-2022)
- Old ArcGIS GeoService endpoints are no longer accessible
- CrimeReports.com platform has been superseded
- New Power BI dashboard doesn't offer public API access

## What I'm Requesting

Access to Loudoun County crime incident data via one of these methods:

### Option A: REST API Access (Preferred)
- ArcGIS FeatureServer or MapServer endpoint
- Similar to existing zoning API access
- Query by location (lat/lon + radius)
- Filter by date range
- Returns JSON with incident details

### Option B: Periodic Data Exports
- Weekly or monthly CSV/JSON exports
- Basic incident information (type, date, general location)
- Email delivery or FTP access

### Option C: Alternative API
- If there's an existing API I haven't found
- Documentation for current data access methods

## Data Fields Needed

**Required:**
- Incident type (crime category)
- Date/time of incident
- General location (approximate coordinates or zone)
- Jurisdiction (LCSO vs town PD)

**Optional but Helpful:**
- Incident description
- Crime severity category
- Beat/patrol area
- Case status (if public)

## Privacy & Data Use Commitments

I understand the sensitivity of crime data and commit to:

✅ **Aggregate Only:** Display only summary statistics and trends
✅ **No Exact Addresses:** Use approximate locations or heat maps
✅ **No Case Details:** No victim information or investigation details
✅ **Proper Attribution:** Credit LCSO as data source
✅ **Terms Compliance:** Follow all data use restrictions
✅ **Public Benefit:** Free tool for homebuyers (non-commercial)

## About Me

I'm a Loudoun County resident (Leesburg) building this tool to help fellow residents and prospective buyers make informed decisions. As a resident, I can validate results against local knowledge and ensure accuracy.

**Project Details:**
- Open-source development
- Multi-county architecture (expanding beyond Loudoun)
- Already successfully integrated Loudoun County GIS zoning data
- Designed for merge with existing Athens-Clarke County tool (Feb-Mar 2026)

## Timeline

**Ideal:** API access within 2-4 weeks
**Flexible:** I understand it may take longer for approval and setup
**Current Status:** Infrastructure complete and ready to integrate data

## What's Already Working

To demonstrate this is a serious project with working infrastructure:

✅ **Phase 1 - Zoning:** Complete with real Loudoun GIS data
- Ashburn: RC (Rural Commercial)
- Sterling: C1 (Commercial)
- South Riding: PDH4 (Planned Development Housing)
- Dulles: GI (General Industrial)

✅ **Phase 2 - Crime:** Infrastructure complete, awaiting data source
- Safety scoring algorithm implemented and validated
- Multi-jurisdiction routing (Sheriff vs Town PD)
- All tests passing (7/7)
- Ready to integrate real data

⏳ **Phase 3 - Schools:** In development

## Questions I Can Answer

I'm happy to discuss:
- Detailed project architecture
- Data security and privacy measures
- Use case examples
- Data attribution and crediting
- Terms of service compliance
- Any concerns about the project

## Next Steps

Would it be possible to:
1. Schedule a call to discuss the project?
2. Review any existing API documentation?
3. Explore data sharing agreements or MOUs?
4. Connect with the appropriate technical contact?

Thank you for considering this request. I believe this tool will provide valuable public benefit by helping families understand Loudoun County neighborhoods more comprehensively.

I look forward to your response and am happy to provide any additional information needed.

Best regards,

[Your Name]
[Your Email]
[Your Phone Number]
[Optional: GitHub repository link]
[Optional: Project website/demo]

---

**Loudoun County Resident Since:** [Year]
**Address:** Leesburg, VA
**Purpose:** Public Safety Research & Real Estate Analysis Tool
```

---

## Follow-Up Strategy

### Week 1: Initial Outreach
- [ ] Send email to mapping@loudoun.gov (primary)
- [ ] CC: sheriff@loudoun.gov (secondary)
- [ ] Save sent email confirmation
- [ ] Add calendar reminder for 1-week follow-up

### Week 2: First Follow-Up (if no response)
- [ ] Reply to original email thread
- [ ] Keep it brief: "Following up on my request below"
- [ ] Add: "Happy to schedule a call to discuss"
- [ ] Phone call to GIS department: (571) 258-3800

### Week 3: Alternative Contacts
- [ ] Contact IT department
- [ ] Look for data governance or open data coordinator
- [ ] Consider FOIA request if appropriate

### Week 4: Decision Point
- [ ] If approved: Begin integration immediately
- [ ] If declined: Document reason, explore alternatives
- [ ] If no response: Proceed with mock data, revisit later

---

## Alternative Email Recipients

If primary contact doesn't respond:

**Loudoun County IT:**
- General: mapping@loudoun.gov
- Main: (571) 258-3800

**Sheriff's Office:**
- General: sheriff@loudoun.gov
- Main: (703) 777-1021

**Board of Supervisors (escalation):**
- For open data advocacy if needed

---

## Response Scenarios

### Scenario A: Approved ✅
**Action:**
- Request API documentation
- Test endpoint immediately
- Integrate with crime_analysis.py
- Complete Phase 2B
- Send thank you email

### Scenario B: Approved with Restrictions ⚠️
**Action:**
- Review restrictions carefully
- Assess if data is sufficient
- Negotiate if possible
- Comply with all terms

### Scenario C: Declined ❌
**Action:**
- Thank them for consideration
- Ask for reasoning (helps improve request)
- Explore alternatives:
  - Aggregate statistics only?
  - Annual reports?
  - Partnership opportunities?
- Document for future reference

### Scenario D: No Response 📭
**Action:**
- Follow up twice (weeks 2 and 3)
- Phone call week 3
- After week 4:
  - Proceed with mock data
  - Note "real data pending" in documentation
  - Revisit in 3-6 months

---

## Supporting Documents to Attach (Optional)

1. **Project Overview PDF**
   - Architecture diagram
   - Sample outputs
   - Data flow
   - Privacy measures

2. **Technical Specifications**
   - API requirements
   - Field mapping needs
   - Query examples
   - Response format preferences

3. **Data Use Agreement Draft**
   - Proposed terms
   - Attribution language
   - Restrictions acknowledged
   - Update frequency

---

## Key Messages to Emphasize

1. **Legitimate Purpose:** Public benefit tool for homebuyers
2. **Already Working:** Successful GIS integration proves credibility
3. **Privacy Conscious:** No exact addresses or case details
4. **Local Resident:** Invested in Loudoun County community
5. **Professional Approach:** Well-architected, tested infrastructure
6. **Flexible:** Open to any data sharing method that works
7. **Attribution:** Will credit LCSO prominently

---

## What NOT to Say

❌ Don't mention specific addresses (privacy concerns)
❌ Don't ask for case investigation details
❌ Don't imply commercial use
❌ Don't reference specific crimes or incidents
❌ Don't make demands (request, not require)
❌ Don't compare to other counties negatively
❌ Don't rush them ("need ASAP")

---

## Success Indicators

**Good Signs:**
- Response within 1 week ✅
- Request for more information ✅
- Meeting/call scheduled ✅
- Referred to appropriate contact ✅

**Concerning Signs:**
- No response after 3 weeks ⚠️
- Immediate flat rejection ❌
- "We don't provide this data" ❌
- "Check back in 6 months" ⏳

---

## Backup Plan

If LCSO doesn't provide access:

**Phase 2B Alternatives:**
1. Use FBI Crime Data API (national statistics)
2. Aggregate statistics from public reports
3. Mock data with validation plan for later
4. Partnership with existing crime data platforms
5. Focus on zoning + schools only (defer crime)

---

**Status:** Draft completed, ready to send
**Next Action:** Review, personalize, and send email
**Timeline:** Send within 24-48 hours
**Follow-up:** Track in calendar for 1-week check-in
