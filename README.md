# Hotel Project Leads Scraper

Automated Python script to extract hotel project leads from hotelprojectleads.com
in batches of 15, download each batch as CSV, then merge into one master file.

## Project Structure

```
hotel_leads_scraper/
├── config.py           # All settings: credentials, batch size, URLs
├── scraper.py          # Main automation script (Playwright)
├── merge_csvs.py       # Merge all batch CSVs into one master file
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── csv_exports/        # Downloaded CSV files (created automatically)
└── screenshots/        # Debug screenshots (created automatically)
```

## Setup

### 1. (Recommended) Create a virtual environment (no Conda required)

```bash
cd /Users/samarthpatil/Desktop/hotel_leads_scraper

python3 -m venv .venv
source .venv/bin/activate
```

Each time you come back to the project, re-activate it with:

```bash
cd /Users/samarthpatil/Desktop/hotel_leads_scraper
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browsers

```bash
python -m playwright install chromium
```

### 4. Configure credentials

Set your Hotel Project Leads credentials via environment variables (recommended and required):

```python
HPL_USERNAME = "your_email@example.com"
HPL_PASSWORD = "your_password"
```

The scraper will exit with an error if these variables are not set.

```bash
export HPL_USERNAME="your_email@example.com"
export HPL_PASSWORD="your_password"
```

### 5. Adjust settings (optional)

In `config.py`:
- `BATCH_SIZE` = 15 (leads per CSV, max 20)
- `MAX_PAGES` = None (set to a number to limit, e.g. 5 for testing)
- You can also override `MAX_PAGES` via the `HPL_MAX_PAGES` environment variable, e.g.:

  ```bash
  export HPL_MAX_PAGES=1  # Only process the first page
  ```
- `SEARCH_FROM_DATE` = "2025-01-01"

## Usage

### Step 1: Run the scraper

```bash
python scraper.py
```

This will:
1. Log in to hotelprojectleads.com
2. Run a search with your filters
3. Open each lead, click Mark, return to results
4. After 15 leads, download the batch CSV
5. Move to the next page and repeat
6. Save all CSVs to `csv_exports/`

### Step 2: Merge all CSVs

```bash
python merge_csvs.py
```

This creates `csv_exports/hotel_leads_MASTER.csv` with all leads combined.

### Step 3: Import into Clay

Upload `hotel_leads_MASTER.csv` to Clay for enrichment.

## Full run (9000+ leads)

- **Yes, you can run it for all results.** Remove or leave `HPL_MAX_PAGES` unset so the scraper processes every page.
- **Rough time:** ~3–6+ minutes per batch (15 leads). For 9000 leads (~600 batches) that’s on the order of **30–60+ hours**. Run on a stable connection and avoid closing the browser or machine.
- **Optional:** In `scraper.py` set `headless=True` for long runs so the browser runs in the background.
- **Chunked runs (recommended for 602 pages):** Use `HPL_START_PAGE` and `HPL_MAX_PAGES` so each run processes a range of pages. Batch files are named by global page number (e.g. `hotel_leads_batch_0101.csv` … `hotel_leads_batch_0200.csv`). Run each chunk, then run merge once at the end (or after each chunk to inspect). Example:

  | Chunk | Pages    | Command |
  |-------|----------|---------|
  | 1     | 1–100    | `export HPL_START_PAGE=1; export HPL_MAX_PAGES=100; bash run.sh` |
  | 2     | 101–200  | `export HPL_START_PAGE=101; export HPL_MAX_PAGES=100; bash run.sh` |
  | 3     | 201–300  | `export HPL_START_PAGE=201; export HPL_MAX_PAGES=100; bash run.sh` |
  | …     | …        | … |
  | 7     | 601–602  | `export HPL_START_PAGE=601; export HPL_MAX_PAGES=2; bash run.sh` |

  After all chunks, run `python3 merge_csvs.py` once to build `hotel_leads_MASTER.csv` from all batch files.

## Testing

Start with a small test first:

```python
# In config.py, set:
MAX_PAGES = 1  # Only process the first page
```

Run `python scraper.py`, verify the CSV downloads correctly,
then remove the limit for the full run.

## Troubleshooting

- **Login fails**: Check credentials in config.py
- **Selectors not found**: The site may have changed its HTML structure.
  Check screenshots/ for debug images and update selectors in scraper.py.
- **CSV not downloading**: Ensure accept_downloads=True in browser context.
- **Slow performance**: Reduce ACTION_DELAY and MARK_DELAY in config.py.

## Notes

- The site limits CSV downloads to 20 leads at a time.
- BATCH_SIZE=15 matches the visible results per page.
- The scraper runs in visible browser mode by default.
  Set `headless=True` in scraper.py for production runs.
- Selectors may need adjustment based on actual site HTML.
  Run a test batch first and check screenshots.
