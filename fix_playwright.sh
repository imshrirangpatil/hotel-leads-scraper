#!/bin/bash
# Fix Playwright hang / "Connection closed while reading from the driver"
set -e

cd "$(dirname "$0")"

# Detect unkillable stuck driver processes (macOS UE state)
if ps aux 2>/dev/null | grep -q "[p]laywright/driver/node"; then
  echo "WARNING: Stuck Playwright driver processes detected."
  echo ""
  echo "These cannot be killed with Ctrl+C or kill -9."
  echo "You MUST reboot your Mac, then run:"
  echo ""
  echo "  bash setup_after_reboot.sh"
  echo ""
  exit 1
fi

source .venv/bin/activate

echo "Reinstalling Playwright..."
pip install --force-reinstall playwright

echo "Installing Chromium browser..."
python3 -m playwright install chromium

# macOS: remove quarantine flags that block the Playwright driver
if [[ "$(uname)" == "Darwin" ]]; then
  echo "Clearing macOS quarantine on Playwright..."
  xattr -dr com.apple.quarantine .venv/lib/python3.*/site-packages/playwright/ 2>/dev/null || true
fi

echo "Testing launch..."
python3 -u -c "
from playwright.sync_api import sync_playwright
print('Starting test...', flush=True)
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, timeout=120000)
    b.close()
print('Playwright OK')
"

echo ""
echo "Done. Resume scraper with:"
echo "  export HPL_START_PAGE=12"
echo "  python3 -u scraper.py"
