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
_env_from = os.getenv("HPL_FROM_DATE")
SEARCH_FROM_DATE = _env_from if _env_from else "2026-03-01"

# Include expired leads checkbox (default: unchecked)
INCLUDE_EXPIRED_LEADS = os.getenv("HPL_INCLUDE_EXPIRED", "").lower() in ("1", "true", "yes")

# Batch settings
BATCH_SIZE = 15
_env_start = os.getenv("HPL_START_PAGE")
START_PAGE = int(_env_start) if _env_start else 1
_env_max_pages = os.getenv("HPL_MAX_PAGES")
MAX_PAGES = int(_env_max_pages) if _env_max_pages else None

# Auto-resume: set START_PAGE to (highest batch in OUTPUT_DIR + 1)
AUTO_RESUME = os.getenv("HPL_AUTO_RESUME", "").lower() in ("1", "true", "yes")

NAVIGATION_TIMEOUT_MS = 60_000
GOTO_RETRIES = 3

# Output
OUTPUT_DIR = os.getenv("HPL_OUTPUT_DIR", "csv_exports")
MASTER_OUTPUT_DIR = os.getenv("HPL_MASTER_DIR", "csv_exports")
SCREENSHOTS_DIR = "screenshots"

# Browser
HEADLESS = os.getenv("HPL_HEADLESS", "").lower() in ("1", "true", "yes")

# Timing (seconds)
PAGE_LOAD_WAIT = 5
ACTION_DELAY = 2
MARK_DELAY = 1
