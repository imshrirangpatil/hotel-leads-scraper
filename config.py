import os

# Hotel Project Leads credentials
HPL_URL = "https://hotelprojectleads.com"
HPL_LOGIN_URL = f"{HPL_URL}/members/"
HPL_SEARCH_URL = f"{HPL_URL}/members/searchprojectdatabase/"

HPL_USERNAME = os.getenv("HPL_USERNAME")
HPL_PASSWORD = os.getenv("HPL_PASSWORD")

if not HPL_USERNAME or not HPL_PASSWORD:
    raise RuntimeError(
        "HPL_USERNAME and HPL_PASSWORD environment variables must be set "
        "before running the scraper."
    )

# Search filters
SEARCH_FROM_DATE = "2025-01-01"

# Batch settings
BATCH_SIZE = 15
# Start page (for chunked runs). 1 = first page. Use HPL_START_PAGE (e.g. 101 for chunk 2).
_env_start = os.getenv("HPL_START_PAGE")
START_PAGE = int(_env_start) if _env_start else 1
# Max pages to process in this run (e.g. 100 per chunk). Use HPL_MAX_PAGES. None = all pages.
_env_max_pages = os.getenv("HPL_MAX_PAGES")
MAX_PAGES = int(_env_max_pages) if _env_max_pages else None

# Output
OUTPUT_DIR = "csv_exports"
SCREENSHOTS_DIR = "screenshots"

# Timing (seconds)
PAGE_LOAD_WAIT = 5
ACTION_DELAY = 2
MARK_DELAY = 1
# Navigation timeout (ms) – increase if the site is slow or timeouts occur mid-run
NAVIGATION_TIMEOUT_MS = 60_000
