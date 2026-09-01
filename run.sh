#!/bin/bash
# Quick start — use project venv and Python 3.11+
set -e

cd "$(dirname "$0")"

echo "=== Hotel Project Leads Scraper ==="
echo ""

if [[ ! -d .venv ]]; then
  echo "No .venv found. Run: bash setup_after_reboot.sh"
  exit 1
fi

source .venv/bin/activate

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
  echo "ERROR: Python 3.9+ required. Run: bash setup_after_reboot.sh"
  exit 1
fi

if [[ -z "$HPL_USERNAME" || -z "$HPL_PASSWORD" ]]; then
  echo "ERROR: Set HPL_USERNAME and HPL_PASSWORD before running."
  exit 1
fi

echo "[1/3] Installing dependencies..."
pip install -q -r requirements.txt
python3 -m playwright install chromium

echo ""
echo "[2/3] Starting scraper..."
python3 -u scraper.py

echo ""
echo "[3/3] Merging CSV files..."
python3 merge_csvs.py

echo ""
echo "=== Done! Check csv_exports/hotel_leads_MASTER.csv ==="
