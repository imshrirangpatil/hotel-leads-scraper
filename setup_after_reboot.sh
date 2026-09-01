#!/bin/bash
# Run AFTER rebooting your Mac (required to clear stuck Playwright driver processes).
set -e

cd "$(dirname "$0")"

echo "=== Hotel Leads Scraper — fresh setup ==="
echo ""

# Playwright requires Python 3.9+; macOS default python3 is often 3.7
PYTHON=""
for candidate in python3.11 python3.12 python3.10 python3; do
  if command -v "$candidate" &>/dev/null; then
    if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo "ERROR: Python 3.9+ required. Install with: brew install python@3.11"
  exit 1
fi

echo "Using $PYTHON ($($PYTHON --version))"

# Fresh venv avoids a corrupted Playwright driver copy
if [[ -d .venv ]]; then
  echo "Removing old .venv..."
  rm -rf .venv
fi

echo "Creating new virtual environment..."
"$PYTHON" -m venv .venv
source .venv/bin/activate

echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing Chromium for Playwright..."
python3 -m playwright install chromium

if [[ "$(uname)" == "Darwin" ]]; then
  echo "Clearing macOS quarantine on Playwright..."
  xattr -dr com.apple.quarantine .venv/lib/python3.*/site-packages/playwright/ 2>/dev/null || true
fi

echo "Testing Playwright launch..."
python3 -u -c "
from playwright.sync_api import sync_playwright
print('Starting test...', flush=True)
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, timeout=120000)
    b.close()
print('Playwright OK')
"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next, run the scraper (resume from page 12):"
echo ""
echo "  source .venv/bin/activate"
echo "  export HPL_USERNAME=\"your_email\""
echo "  export HPL_PASSWORD=\"your_password\""
echo "  export HPL_START_PAGE=12"
echo "  python3 -u scraper.py"
echo ""
echo "Do NOT press Ctrl+C while it says 'Starting Playwright...'"
