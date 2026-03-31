#!/bin/bash
# Quick start script

set -e

echo "=== Hotel Project Leads Scraper ==="
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required."
    exit 1
fi

# Check pip3
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is required."
    exit 1
fi

# Install dependencies
echo "[1/3] Installing dependencies..."
pip3 install -r requirements.txt
python3 -m playwright install chromium

# Run scraper (all pages; for a test run set e.g. export HPL_MAX_PAGES=5 before this)
echo ""
echo "[2/3] Starting scraper..."
python3 scraper.py

# Merge CSVs
echo ""
echo "[3/3] Merging CSV files..."
python3 merge_csvs.py

echo ""
echo "=== Done! Check csv_exports/hotel_leads_MASTER.csv ==="
