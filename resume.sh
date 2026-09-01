#!/bin/bash
# Print the next START_PAGE based on the highest batch CSV in HPL_OUTPUT_DIR.
set -e
cd "$(dirname "$0")"

OUTPUT_DIR="${HPL_OUTPUT_DIR:-csv_exports}"
latest=$(ls "$OUTPUT_DIR"/hotel_leads_batch_*.csv 2>/dev/null | sort | tail -1 || true)

if [[ -z "$latest" ]]; then
  echo "No batch files in $OUTPUT_DIR — start at page 1"
  echo "export HPL_START_PAGE=1"
  exit 0
fi

num=$(basename "$latest" .csv | sed 's/hotel_leads_batch_//')
next=$((10#$num + 1))
echo "Latest batch: $(basename "$latest")"
echo "Resume with:"
echo "  export HPL_OUTPUT_DIR=$OUTPUT_DIR"
echo "  export HPL_START_PAGE=$next"
echo "  unset HPL_MAX_PAGES"
echo "  python3 -u scraper.py"
