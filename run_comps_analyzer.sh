#!/bin/bash
# Quick start script for Loudoun County Comps Analyzer

cd "$(dirname "$0")/loudoun_comps"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              LOUDOUN COUNTY PROPERTY VALUATION SYSTEM                        ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if database exists
if [ ! -f "loudoun_sales.db" ] || [ ! -s "loudoun_sales.db" ]; then
    echo "No database found. Generating sample data..."
    python3 generate_sample_data.py
    echo ""
fi

echo "Running property valuation tests..."
echo ""

# Run the test
python3 test_valuation.py
