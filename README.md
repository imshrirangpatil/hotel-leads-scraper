# Hotel Project Leads Scraper

Automates hotel project lead extraction from [hotelprojectleads.com](https://hotelprojectleads.com): login, search, mark 15 leads per page, download CSV per batch, merge into one master file.

## Quick start

```bash
cd hotel_leads_scraper
bash setup_after_reboot.sh   # first time only (Python 3.11+ venv)

source .venv/bin/activate
export HPL_USERNAME="your_email"
export HPL_PASSWORD="your_password"

python3 -u scraper.py
python3 merge_csvs.py
```

Or: `bash run.sh` (requires credentials in env).

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `HPL_USERNAME` | — | **Required** login email |
| `HPL_PASSWORD` | — | **Required** login password |
| `HPL_FROM_DATE` | `2026-03-01` | Search from date (`yyyy-mm-dd`) |
| `HPL_OUTPUT_DIR` | `csv_exports` | Batch CSV folder (use `csv_exports_aug2026` for incremental runs) |
| `HPL_MASTER_DIR` | `csv_exports` | Where `hotel_leads_MASTER.csv` is written |
| `HPL_START_PAGE` | `1` | Resume from this results page |
| `HPL_MAX_PAGES` | all | Limit pages per run (testing). **Unset for full runs.** |
| `HPL_AUTO_RESUME` | off | Set `1` to auto-detect next page from highest batch in `HPL_OUTPUT_DIR` |
| `HPL_INCLUDE_EXPIRED` | off | Set `1` to check "Include expired leads" |
| `HPL_HEADLESS` | off | Set `1` to run browser in background |

**toDate** is always set to **today** when the scraper runs.

## Common workflows

### Full run (first time)

```bash
export HPL_FROM_DATE=2026-03-01
export HPL_OUTPUT_DIR=csv_exports
unset HPL_MAX_PAGES
unset HPL_START_PAGE
python3 -u scraper.py
python3 merge_csvs.py
```

### Incremental run (new leads since last scrape)

```bash
export HPL_FROM_DATE=2026-07-31      # day after last full scrape
export HPL_OUTPUT_DIR=csv_exports_aug2026
unset HPL_START_PAGE
unset HPL_MAX_PAGES
python3 -u scraper.py
python3 merge_csvs.py                # merges csv_exports + csv_exports_*
```

### Resume after crash

```bash
bash resume.sh                       # prints export HPL_START_PAGE=N
# or
export HPL_AUTO_RESUME=1             # auto-detect from batch files
python3 -u scraper.py
```

Progress is saved to `scrape_progress.json` after each batch.

### Test one page

```bash
export HPL_MAX_PAGES=1
python3 -u scraper.py
unset HPL_MAX_PAGES                  # before full run!
```

## Project structure

```
hotel_leads_scraper/
├── scraper.py              # Main Playwright automation
├── config.py               # Settings (overridden by env vars)
├── merge_csvs.py           # Merge all batch CSVs → MASTER
├── run.sh                  # Install + scrape + merge
├── setup_after_reboot.sh   # Fresh venv + Playwright (after Mac reboot)
├── fix_playwright.sh       # Repair stuck Playwright driver
├── resume.sh               # Show next HPL_START_PAGE from batch files
├── csv_exports/            # Primary batch output
├── csv_exports_*/          # Incremental run folders
└── scrape_progress.json    # Last completed page (auto-written)
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Hangs at "Starting Playwright..." | Reboot Mac, then `bash setup_after_reboot.sh`. Don't Ctrl+C during startup. |
| `No module named playwright` | Use `.venv`: `source .venv/bin/activate`. Need Python **3.9+** (not system 3.7). |
| Only 1 page scraped | `HPL_MAX_PAGES=1` still set — run `unset HPL_MAX_PAGES` |
| 0 leads on resume page | Wrong `HPL_START_PAGE` for a **new** date search — use page `1` |
| `ERR_HTTP2` / network errors | Scraper retries 3×; resume with `bash resume.sh` |
| Playwright driver stuck | `bash fix_playwright.sh` or reboot + `setup_after_reboot.sh` |

## Notes

- Site limit: ~20 marked leads per CSV download; batch size is 15.
- Resume uses **pagination clicks**, not URL jumps (more reliable).
- Merge dedupes on hotel name + city + state + project scope.
- Upload `csv_exports/hotel_leads_MASTER.csv` to Clay for enrichment.
