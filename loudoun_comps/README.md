# Loudoun County Real Estate Comparable Sales Analyzer

A Python-based property valuation system that uses comparable sales analysis (CMA) to estimate property values in Loudoun County, Virginia.

## Features

✅ **Data Collection**
- Downloads official Loudoun County public sales records
- Imports data into SQLite database for fast querying
- Supports sample data generation for testing

✅ **Market Analysis**
- Calculates market-aware adjustment factors using regression analysis
- Determines price per sqft, bedroom/bathroom values, lot premiums
- Measures market appreciation rates and feature premiums
- Caches calculations for performance

✅ **Comparable Sales**
- Finds similar properties by location, size, and features
- Scores comparables by similarity (0-100 scale)
- Filters by distance, recency, and property characteristics

✅ **Property Valuation**
- Adjusts comparables for differences (time, size, features, age)
- Calculates weighted average estimates
- Provides confidence intervals and confidence scores
- Detailed reporting of adjustments and market factors

## Installation

```bash
# Clone or navigate to the project directory
cd loudoun_comps

# Install required packages
pip install pandas openpyxl requests beautifulsoup4 scikit-learn geopy tqdm
```

## Quick Start

### Option 1: Test with Sample Data (Recommended First)

```bash
# Generate sample data and run test valuations
python3 test_valuation.py
```

This will:
1. Generate 200 realistic sample sales
2. Value 5 test properties
3. Show detailed results and market factors
4. Save results to `valuation_results.json`

### Option 2: Import Real Loudoun County Data

```bash
# Download and import official sales data
python3 import_real_data.py

# Then run valuations
python3 test_valuation.py
```

## Usage

### Programmatic API

```python
from valuation import PropertyValuator

# Define subject property
property_data = {
    'address': '43423 Cloister Pl, Ashburn, VA 20147',
    'latitude': 39.0450,
    'longitude': -77.4890,
    'sqft': 3200,
    'bedrooms': 4,
    'bathrooms': 3.5,
    'year_built': 2015,
    'lot_size_acres': 0.35,
    'has_pool': 0,
    'has_garage': 1,
    'property_type': 'Single Family',
    'zip_code': '20147'
}

# Run valuation
with PropertyValuator("loudoun_sales.db") as valuator:
    result = valuator.estimate_property_value(property_data)

print(f"Estimated Value: ${result['estimated_value']:,}")
print(f"Confidence Score: {result['confidence_score']}/100")
```

### Output Format

```json
{
  "address": "43423 Cloister Pl, Ashburn, VA 20147",
  "estimated_value": 850000,
  "confidence_range": [800000, 900000],
  "confidence_score": 85,
  "comps_used": [
    {
      "address": "43500 Cloister Pl, Ashburn, VA 20147",
      "sale_price": 875000,
      "sale_date": "2024-10-15",
      "adjusted_price": 865000,
      "similarity_score": 92,
      "distance_miles": 0.2,
      "sqft": 3150,
      "bedrooms": 4,
      "bathrooms": 3.5,
      "adjustments": {
        "time": 5000,
        "size": -10000,
        "bedrooms": 0,
        "bathrooms": 0
      }
    }
  ],
  "market_factors": {
    "price_per_sqft": 425,
    "bedroom_value": 18000,
    "bathroom_value": 12000,
    "lot_value_per_acre": 50000,
    "age_depreciation_rate": 0.005,
    "pool_premium": 15000,
    "garage_premium": 10000,
    "monthly_appreciation": 0.008,
    "sample_size": 45
  }
}
```

## Project Structure

```
loudoun_comps/
├── database.py              # SQLite database schema and operations
├── market_analysis.py       # Market factor calculations using regression
├── comp_finder.py          # Comparable sales finder with scoring
├── valuation.py            # Main property valuation engine
├── import_real_data.py     # Import official Loudoun County data
├── generate_sample_data.py # Generate sample data for testing
├── test_valuation.py       # Test script with example properties
├── README.md               # This file
└── data/                   # Downloaded data files
    └── loudoun_sales_raw.xlsx
```

## Database Schema

```sql
CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    address TEXT NOT NULL,
    sale_date DATE NOT NULL,
    sale_price INTEGER NOT NULL,
    sqft INTEGER,
    lot_size_acres REAL,
    bedrooms INTEGER,
    bathrooms REAL,
    year_built INTEGER,
    has_pool BOOLEAN,
    has_garage BOOLEAN,
    property_type TEXT,
    zip_code TEXT,
    latitude REAL,
    longitude REAL,
    created_at TIMESTAMP
);

CREATE TABLE market_factors (
    zip_code TEXT NOT NULL,
    calculation_date DATE NOT NULL,
    price_per_sqft REAL,
    bedroom_value REAL,
    bathroom_value REAL,
    lot_value_per_acre REAL,
    age_depreciation_rate REAL,
    pool_premium REAL,
    garage_premium REAL,
    monthly_appreciation REAL,
    sample_size INTEGER
);
```

## Adjustment Methodology

### Time Adjustment
- Uses regression analysis to determine monthly appreciation rate
- Adjusts older sales forward to current market conditions

### Size Adjustment
- Based on market-derived price per square foot
- Adjusts for difference in living area

### Bedroom/Bathroom Adjustment
- Regression-calculated value per bedroom/bathroom
- Adjusts for count differences

### Lot Size Adjustment
- Market-derived value per acre
- Adjusts for lot size differences

### Age Adjustment
- Calculates depreciation rate from sales data
- Adjusts for property age differences

### Feature Adjustments
- Pool premium: ~$15,000 (market-derived)
- Garage premium: ~$10,000 (market-derived)

## Similarity Scoring

Comparables are scored 0-100 based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| Distance | 30 points | Proximity to subject (0-3 miles) |
| Size | 25 points | Sqft difference (+/- 30% tolerance) |
| Recency | 15 points | Age of sale (0-6 months) |
| Bedrooms | 10 points | Bedroom count match |
| Bathrooms | 10 points | Bathroom count match |
| Features | 10 points | Pool/garage match bonuses |

## Confidence Scoring

Valuation confidence (0-100) considers:
- Number of comparables (more is better)
- Average similarity scores (higher is better)
- Price variance among comps (lower is better)
- Recency of comps (more recent is better)
- Market data sample size (larger is better)

## Data Sources

### Official Data
- **Source**: Loudoun County Office of the Commissioner of the Revenue
- **Report**: Real Property Sales Cumulative Report
- **URL**: https://www.loudoun.gov/649/Public-Real-Estate-Reports
- **Format**: Excel (XLSX)
- **Updates**: Monthly

### Supported ZIP Codes
- 20147 (Ashburn)
- 20148 (Ashburn South)
- 20165 (Sterling)
- 20175 (Leesburg)
- 20176 (Leesburg South)
- 20132 (Purcellville)

## Limitations

⚠️ **Important Notes**:
1. Valuations are estimates based on comparable sales only
2. Does not include physical property inspection
3. Geocoding required for location-based features
4. Market factors cached for 30 days
5. Requires minimum 20 sales per ZIP code for analysis

## Future Enhancements

- [ ] Integrate geocoding API for automatic lat/lon lookup
- [ ] Add school district and quality ratings
- [ ] Include crime statistics and walkability scores
- [ ] Web scraping for additional property features (pool, garage)
- [ ] Machine learning models for more accurate adjustments
- [ ] Interactive web interface
- [ ] Integration with MLS data
- [ ] Automated report generation (PDF)

## License

This project is for educational and research purposes. Property valuation should be performed by licensed appraisers for official use.

## Support

For issues or questions:
1. Check the Loudoun County website for data availability
2. Review the test output for debugging information
3. Ensure all required fields are provided for subject property

## Version

**Version 1.0.0** - Initial release (November 2025)
