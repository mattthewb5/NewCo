# Data Import Guide - Loudoun County Building Permits

## Quick Start

### Option 1: Import Uploaded October 2025 File

```bash
cd /home/user/NewCo/loudoun_comps/zoning

# If you have the file uploaded, import it:
python import_loudoun_permits.py \
    --file /path/to/Permits_-_Issued_Building_Report_OCTOBER_2025.xlsx \
    --clear

# This will take 15-20 minutes due to geocoding rate limits
```

### Option 2: Import Multiple Historical Files

```bash
# 1. Create directory for permit data
mkdir -p ./permit_data/

# 2. Download files from Loudoun County website
# Visit: https://www.loudoun.gov/1164/Issued-Building-Permit-Reports
# Save Excel files to ./permit_data/

# 3. Import all files
python import_loudoun_permits.py --import-all --directory ./permit_data/
```

## Downloading Loudoun County Permit Data

### Official Source

**Website**: https://www.loudoun.gov/1164/Issued-Building-Permit-Reports

### Available Data

- **Date Range**: 2015 - Present
- **Frequency**: Monthly reports
- **Format**: Excel (.xlsx)
- **File Size**: 500KB - 2MB per file
- **Records per File**: 500-1,000 permits

### File Naming Convention

```
Permits_-_Issued_Building_Report_[MONTH]_[YEAR].xlsx
```

Examples:
- `Permits_-_Issued_Building_Report_OCTOBER_2025.xlsx`
- `Permits_-_Issued_Building_Report_SEPTEMBER_2025.xlsx`
- `Permits_-_Issued_Building_Report_JANUARY_2024.xlsx`

### Recommended Downloads for January 2025 Demo

**Minimum** (12 months):
- October 2024 through October 2025
- ~9,000 permits
- ~2 hours to import (due to geocoding)

**Recommended** (24 months):
- November 2023 through October 2025
- ~18,000 permits
- ~4 hours to import

**Ideal** (All available):
- January 2015 through October 2025
- ~100,000+ permits
- ~20 hours to import
- Foundation for robust ML training

## Import Process Details

### Step-by-Step Process

1. **Schema Update**: Creates/updates database tables
2. **Excel Reading**: Loads all 16 columns from "Permits - Issued Building" sheet
3. **Address Cleaning**: Removes `_x000D_\n` line breaks
4. **Date Parsing**: Converts "Permit Issue Date" to proper datetime
5. **Geocoding**: Geocodes each address (1/second rate limit)
   - Uses OpenStreetMap Nominatim API
   - Adds "Loudoun County, VA" for accuracy
   - Caches results in `geocoding_cache.json`
   - Expected 90-95% success rate
6. **Categorization**: Classifies each permit
   - Residential - New Construction
   - Residential - Renovation
   - Commercial - New Construction
   - Commercial - Renovation
   - Major Commercial (>25k sqft or data centers)
   - Industrial
   - Other
7. **Database Insert**: Inserts all records with duplicate detection
8. **Statistics**: Shows import summary

### Geocoding Cache

The geocoding cache (`geocoding_cache.json`) stores all geocoded addresses to avoid repeated API calls.

**Benefits**:
- Speeds up re-imports dramatically
- Respects Nominatim rate limits
- Persists across sessions

**Size**: ~100KB per 1,000 addresses

**Location**: Same directory as import script

### Import Time Estimates

| File Count | Permits | First Import | Re-import (with cache) |
|------------|---------|--------------|------------------------|
| 1 (Oct 2025) | 785 | 15-20 min | <1 min |
| 12 months | ~9,000 | 2-3 hours | <5 min |
| 24 months | ~18,000 | 4-5 hours | <10 min |
| All (2015-2025) | ~100,000 | 20-24 hours | <30 min |

**Pro Tip**: Run large imports overnight!

## Command Reference

### Basic Import

```bash
# Import single file
python import_loudoun_permits.py \
    --file /path/to/file.xlsx

# Import with clear existing data
python import_loudoun_permits.py \
    --file /path/to/file.xlsx \
    --clear
```

### Batch Import

```bash
# Import all files from directory
python import_loudoun_permits.py \
    --import-all \
    --directory ./permit_data/
```

### Database Management

```bash
# Show database statistics
python import_loudoun_permits.py --stats

# Specify custom database path
python import_loudoun_permits.py \
    --file /path/to/file.xlsx \
    --db /custom/path/loudoun_development.db
```

### Help & Guides

```bash
# Show all command-line options
python import_loudoun_permits.py --help

# Show download guide
python import_loudoun_permits.py --download-guide
```

## Verifying Import Success

### Check Statistics

```bash
python import_loudoun_permits.py --stats
```

Expected output:
```
================================================================================
DATABASE STATISTICS
================================================================================
Total Permits: 785

By Permit Type:
  Building (Residential): 459
  Building (Commercial): 317
  Other: 9

By Category:
  Residential - New Construction: 234
  Commercial - New Construction: 156
  Residential - Renovation: 225
  Commercial - Renovation: 161
  Major Commercial: 5
  Other: 4

Major Commercial Projects: 5
Total Construction Value: $229.4M
Geocoding Success Rate: 92.5% (726/785)

Date Range: 2025-10-01 to 2025-10-31
================================================================================
```

### Check Geocoding Success

Open `geocoding_cache.json` and verify addresses are geocoded:

```json
{
  "123 Main St, Ashburn": {
    "lat": 39.0437,
    "lon": -77.4875
  },
  ...
}
```

### Test Analysis

```bash
python run_development_analysis.py \
    --address "43500 Cloister Pl, Ashburn, VA 20147" \
    --lat 39.0437 \
    --lon -77.4875 \
    --report-only
```

Should generate `development_analysis_report.html` with real permit data!

## Troubleshooting

### Error: "No such file or directory"

**Cause**: Excel file path is incorrect

**Solution**:
```bash
# Use absolute path
python import_loudoun_permits.py \
    --file /absolute/path/to/file.xlsx

# Or verify file exists
ls -la /path/to/file.xlsx
```

### Error: "Sheet 'Permits - Issued Building' not found"

**Cause**: Excel file has different sheet name

**Solution**:
- Open Excel file and verify sheet name
- Loudoun County files should have "Permits - Issued Building" sheet
- Make sure you downloaded the correct report type

### Error: "Geocoding failed for [address]"

**Cause**: Nominatim API timeout or rate limit

**Solution**:
- This is normal for some addresses
- Geocoding will be retried on next import
- Expected 5-10% failure rate is acceptable

### Error: "Database is locked"

**Cause**: Another process is using the database

**Solution**:
```bash
# Close any other connections
# Check for running processes
ps aux | grep loudoun

# Delete journal file if present
rm loudoun_development.db-journal
```

### Geocoding Too Slow

**Not an error** - this is expected behavior

**Why**: Nominatim rate limit is 1 request/second

**Solutions**:
- Run overnight for large imports
- Geocoding cache speeds up subsequent imports
- Consider batch processing multiple files

### Import Statistics Look Wrong

**Check**:
1. Verify correct database: `python import_loudoun_permits.py --stats`
2. Check date range in output
3. Verify Excel file contents manually
4. Look for duplicate skips in import log

## Data Quality

### What Gets Imported

✓ All 16 Excel columns preserved
✓ Dates parsed correctly
✓ Addresses cleaned (line breaks removed)
✓ Duplicate permits skipped automatically
✓ Null values handled gracefully

### What Gets Added

✓ Latitude/longitude (geocoded)
✓ Category (our classification)
✓ is_major_commercial flag (for 3x weighting)
✓ import_date (timestamp)

### Quality Checks

Run these queries to verify data quality:

```sql
-- Check for records without geocoding
SELECT COUNT(*) FROM building_permits WHERE latitude IS NULL;

-- Check date distribution
SELECT
    strftime('%Y-%m', issue_date) as month,
    COUNT(*) as permits
FROM building_permits
GROUP BY month
ORDER BY month DESC;

-- Check for major commercial projects
SELECT
    address,
    structure_type,
    sqft,
    estimated_cost
FROM building_permits
WHERE is_major_commercial = 1;
```

## Best Practices

### For Demo Preparation

1. **Import October 2025 first** - Shows most recent data
2. **Test with known address** - Verify results make sense
3. **Generate sample report** - Make sure it looks good
4. **Prepare backup** - Copy database before demo

### For Production

1. **Import historical data** - At least 12 months for trends
2. **Set up monthly updates** - Download new data each month
3. **Back up database regularly** - Before large imports
4. **Monitor geocoding cache** - Clean up if it gets too large
5. **Verify statistics** - After each import

### For Development

1. **Use sample data for testing** - Faster iteration
2. **Import real data for validation** - Ensure compatibility
3. **Keep separate test database** - Avoid corrupting production data
4. **Cache geocoding results** - Save API calls during testing

## Advanced Usage

### Custom Geocoding

If you need to use a different geocoding service:

```python
# Edit import_loudoun_permits.py
# Modify geocode_address() method
# Replace Nominatim with your preferred service
```

### Custom Categorization

If you want different permit categories:

```python
# Edit import_loudoun_permits.py
# Modify categorize_permit() method
# Add your custom logic
```

### Batch Processing with Progress

```bash
# Create a batch import script
#!/bin/bash

for file in ./permit_data/*.xlsx; do
    echo "Importing: $file"
    python import_loudoun_permits.py --file "$file"
    sleep 5  # Brief pause between files
done

echo "All imports complete!"
python import_loudoun_permits.py --stats
```

## Next Steps

After importing data:

1. ✓ Run `--stats` to verify
2. ✓ Test location analyzer: `python location_analyzer.py`
3. ✓ Generate test report with real data
4. ✓ Review PHASE_2_GUIDE.md for full capabilities
5. ✓ Prepare demo script for January 2025

---

## Questions?

Check:
- PHASE_2_GUIDE.md - Comprehensive Phase 2 documentation
- `python import_loudoun_permits.py --help` - Command reference
- Loudoun County website for data source questions

**You're ready to import real data!** 🚀
