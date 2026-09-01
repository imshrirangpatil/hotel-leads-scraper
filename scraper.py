"""
Hotel Project Leads Scraper
Automates: Login → Search → Mark leads in batches → Download CSV
Uses Playwright (Python) for browser automation.
"""

import json
import os
import time
import glob
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError
from config import (
    HPL_URL, HPL_LOGIN_URL, HPL_SEARCH_URL,
    HPL_USERNAME, HPL_PASSWORD,
    SEARCH_FROM_DATE, BATCH_SIZE, MAX_PAGES, START_PAGE, AUTO_RESUME,
    INCLUDE_EXPIRED_LEADS, HEADLESS,
    OUTPUT_DIR, SCREENSHOTS_DIR,
    PAGE_LOAD_WAIT, ACTION_DELAY, MARK_DELAY, NAVIGATION_TIMEOUT_MS, GOTO_RETRIES
)

PROGRESS_FILE = "scrape_progress.json"


def setup_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def detect_start_page():
    """Find highest batch number in OUTPUT_DIR and return next page."""
    batches = glob.glob(os.path.join(OUTPUT_DIR, "hotel_leads_batch_*.csv"))
    if not batches:
        return 1
    nums = []
    for path in batches:
        name = os.path.basename(path)
        try:
            nums.append(int(name.replace("hotel_leads_batch_", "").replace(".csv", "")))
        except ValueError:
            continue
    return max(nums) + 1 if nums else 1


def print_run_banner(start_page):
    print(f"\n{'='*60}")
    print("RUN CONFIG")
    print(f"  fromDate:     {SEARCH_FROM_DATE}")
    print(f"  toDate:       {datetime.now().strftime('%Y-%m-%d')} (today)")
    print(f"  expired:      {'included' if INCLUDE_EXPIRED_LEADS else 'excluded'}")
    print(f"  output:       {OUTPUT_DIR}/")
    print(f"  start page:   {start_page}")
    print(f"  max pages:    {MAX_PAGES or 'all'}")
    print(f"  headless:     {HEADLESS}")
    if MAX_PAGES:
        print("  NOTE: HPL_MAX_PAGES is set — unset it for a full run.")
    print(f"{'='*60}\n", flush=True)


def save_progress(start_page, last_completed, total_leads, status="running"):
    progress = {
        "updated_at": datetime.now().isoformat(),
        "from_date": SEARCH_FROM_DATE,
        "output_dir": OUTPUT_DIR,
        "start_page": start_page,
        "last_completed_page": last_completed,
        "next_start_page": last_completed + 1 if last_completed else start_page,
        "total_leads_processed": total_leads,
        "status": status,
    }
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def goto_with_retry(page, url, label="navigation", retries=GOTO_RETRIES):
    """Navigate with retries on transient network errors."""
    for attempt in range(retries):
        try:
            page.goto(url, wait_until="load", timeout=NAVIGATION_TIMEOUT_MS)
            return True
        except (PlaywrightTimeout, PlaywrightError) as e:
            err = str(e)
            retryable = any(
                token in err
                for token in ("ERR_", "Timeout", "timeout", "net::")
            )
            if attempt < retries - 1 and retryable:
                wait = 5 * (attempt + 1)
                print(f"    {label} failed, retry {attempt + 2}/{retries} in {wait}s...")
                time.sleep(wait)
            else:
                print(f"    WARNING: {label} failed after {attempt + 1} attempt(s): {err[:120]}")
                return False
    return False


def get_latest_download(download_dir, before_files):
    after_files = set(glob.glob(os.path.join(download_dir, "*.csv")))
    new_files = after_files - before_files
    if new_files:
        return max(new_files, key=os.path.getmtime)
    return None


def login(page):
    print("[1] Navigating to login page...", flush=True)
    if not goto_with_retry(page, HPL_LOGIN_URL, label="Login page"):
        raise RuntimeError("Could not load login page.")
    time.sleep(ACTION_DELAY)

    page.fill('input[name="log"], input[type="text"]', HPL_USERNAME)
    page.fill('input[name="pwd"], input[type="password"]', HPL_PASSWORD)
    page.click('input[type="submit"], button[type="submit"]')
    page.wait_for_load_state("load", timeout=NAVIGATION_TIMEOUT_MS)
    time.sleep(ACTION_DELAY)

    print("[1] Login successful.")
    try:
        page.screenshot(path=f"{SCREENSHOTS_DIR}/01_after_login.png", timeout=15_000)
    except Exception as e:
        print(f"    Screenshot skipped: {e}")


def run_search(page):
    print("[2] Navigating to search page...")
    page.goto(HPL_SEARCH_URL, wait_until="load", timeout=NAVIGATION_TIMEOUT_MS)
    time.sleep(ACTION_DELAY)

    try:
        print("[2] Configuring location filter for North America...")
        try:
            na_tab = page.get_by_text("North America", exact=True).first
            if na_tab.is_visible():
                na_tab.click()
                time.sleep(0.5)
        except Exception as e:
            print(f'[2] Warning: Could not activate "North America" tab: {e}')

        left_list = page.locator("select[multiple]").first
        left_list.click()
        time.sleep(0.2)

        options = left_list.locator("option").all()
        values = [opt.get_attribute("value") for opt in options if opt.get_attribute("value")]
        if values:
            left_list.select_option(values)
        else:
            page.keyboard.press("Control+A")
            time.sleep(0.3)
            page.keyboard.press("Meta+A")
        time.sleep(0.5)

        move_right_btn = page.locator(
            'input[type="button"][value=">>"], button:has-text(">>")'
        ).first
        move_right_btn.click()
        time.sleep(0.5)
        print("[2] Location filter configured for North America.")
    except Exception as e:
        print(f"[2] Warning: Could not configure North America location filter: {e}")

    try:
        for btn in page.locator('text="Select All"').all():
            btn.click()
            time.sleep(0.5)
        print("[2] Selected all filter options.")
    except Exception as e:
        print(f"[2] Warning: Could not click Select All: {e}")

    today = datetime.now().strftime("%Y-%m-%d")
    try:
        date_input = page.locator('input[name="fromDate"], input[placeholder*="date"], input[type="date"]').first
        date_input.fill(SEARCH_FROM_DATE)
        print(f"[2] Set from date to {SEARCH_FROM_DATE}.")
    except Exception as e:
        print(f"[2] Warning: Could not set from date: {e}")

    try:
        to_date_input = page.locator('input[name="toDate"]').first
        if to_date_input.is_visible():
            to_date_input.fill(today)
            print(f"[2] Set to date to {today}.")
    except Exception as e:
        print(f"[2] Warning: Could not set to date: {e}")

    try:
        expired_cb = page.locator('input[name="incExp"]').first
        if INCLUDE_EXPIRED_LEADS and not expired_cb.is_checked():
            expired_cb.check()
            print("[2] Checked 'Include expired leads'.")
        elif not INCLUDE_EXPIRED_LEADS and expired_cb.is_checked():
            expired_cb.uncheck()
            print("[2] Unchecked 'Include expired leads'.")
    except Exception:
        try:
            expired_cb = page.get_by_role("checkbox", name="Include expired leads")
            if INCLUDE_EXPIRED_LEADS and not expired_cb.is_checked():
                expired_cb.check()
            elif not INCLUDE_EXPIRED_LEADS and expired_cb.is_checked():
                expired_cb.uncheck()
        except Exception as e:
            print(f"[2] Warning: Could not toggle 'Include expired leads': {e}")

    time.sleep(ACTION_DELAY)
    page.click('input[value="Search"], button:has-text("Search")')
    page.wait_for_load_state("load", timeout=NAVIGATION_TIMEOUT_MS)
    if not wait_for_search_results(page):
        raise RuntimeError(
            "Search did not reach the results page. "
            "Check filters/credentials and screenshots/02_search_results.png."
        )
    time.sleep(ACTION_DELAY)

    count_text = page.get_by_text("results were found", exact=False).first
    try:
        if count_text.is_visible():
            print(f"[2] Site reports: {count_text.inner_text().strip()}")
    except Exception:
        pass

    print(f"[2] Search completed ({page.url}).")
    try:
        page.screenshot(path=f"{SCREENSHOTS_DIR}/02_search_results.png", timeout=15_000)
    except Exception as e:
        print(f"    Screenshot skipped: {e}")

    return page.url


def wait_for_search_results(page, timeout_sec=60):
    for _ in range(timeout_sec):
        if page.locator('a[href*="lead-detail"]').count() > 0:
            return True
        if page.get_by_text("results were found", exact=False).count() > 0:
            return True
        time.sleep(1)
    return False


def get_lead_links(page):
    links = page.locator('a[href*="lead-detail"]').all()
    hrefs = []
    seen = set()
    for link in links:
        href = link.get_attribute("href")
        if not href:
            continue
        if not href.startswith("http"):
            href = HPL_URL + href
        if href in seen:
            continue
        seen.add(href)
        hrefs.append(href)

    print(f"[3] Extracted {len(hrefs)} unique lead URLs on this page.")
    return hrefs


def mark_single_lead(page, lead_url, results_url):
    if not goto_with_retry(page, lead_url, label="Lead page", retries=2):
        print("    WARNING: Skipping lead (load failed), continuing...")
        return
    time.sleep(ACTION_DELAY)

    try:
        mark_link = page.locator("a").filter(has=page.get_by_text("Mark", exact=True)).first
        mark_link.click()
        time.sleep(MARK_DELAY)
        print(f"    Marked: {lead_url.split('/')[-1][:50]}...")
    except Exception as e:
        print(f"    WARNING: Could not mark lead: {e}")

    if not goto_with_retry(page, results_url, label="Return to results"):
        raise RuntimeError(f"Could not return to results page after marking lead.")
    time.sleep(ACTION_DELAY)


def download_marked_csv(page, batch_number, download_dir):
    print(f"[4] Downloading CSV for batch {batch_number}...")

    try:
        view_marked = page.locator('a:has-text("View your marked leads"), a:has-text("view your marked")').first
        view_marked.click()
        page.wait_for_load_state("load", timeout=NAVIGATION_TIMEOUT_MS)
        time.sleep(ACTION_DELAY)
    except Exception as e:
        print(f"    WARNING: Could not find 'View your marked leads': {e}")
        return None

    before_files = set(glob.glob(os.path.join(download_dir, "*.csv")))

    try:
        with page.expect_download(timeout=NAVIGATION_TIMEOUT_MS) as download_info:
            page.locator('a:has-text("Download CSV")').first.click()
        download = download_info.value
        batch_filename = f"hotel_leads_batch_{batch_number:04d}.csv"
        save_path = os.path.join(OUTPUT_DIR, batch_filename)
        download.save_as(save_path)
        print(f"    Saved: {save_path}")
        return save_path
    except Exception as e:
        print(f"    WARNING: Download failed: {e}")
        time.sleep(5)
        new_file = get_latest_download(download_dir, before_files)
        if new_file:
            batch_filename = f"hotel_leads_batch_{batch_number:04d}.csv"
            save_path = os.path.join(OUTPUT_DIR, batch_filename)
            os.rename(new_file, save_path)
            print(f"    Saved (fallback): {save_path}")
            return save_path
        return None


def clear_marked(page):
    try:
        clear_btn = page.locator(
            'a:has-text("Clear marked"), a:has-text("Clear Marked"), '
            'button:has-text("Clear marked"), button:has-text("Clear Marked"), '
            'input[value="Clear marked"], input[value="Clear Marked"]'
        ).first
        if clear_btn.is_visible():
            clear_btn.click()
            page.wait_for_load_state("load", timeout=NAVIGATION_TIMEOUT_MS)
            time.sleep(ACTION_DELAY)
            print("    Cleared marked leads for next batch.")
            return True
    except Exception as e:
        print(f"    WARNING: Could not clear marked: {e}")
    return False


def go_to_next_page(page):
    try:
        next_btn = page.locator('a:has-text("Next"), a:has-text(">>"), a:has-text("›")').first
        if next_btn.is_visible():
            next_btn.click()
            page.wait_for_load_state("load", timeout=NAVIGATION_TIMEOUT_MS)
            wait_for_search_results(page, timeout_sec=30)
            time.sleep(ACTION_DELAY)
            return True
    except Exception:
        pass
    return False


def navigate_to_results_page(page, page_num):
    if page_num <= 1:
        return True

    print(f"[2] Paginating to page {page_num} (clicking Next {page_num - 1} times)...")
    for i in range(page_num - 1):
        if not go_to_next_page(page):
            print(f"[2] WARNING: Stopped at page {i + 1}, could not reach page {page_num}.")
            return False
        if (i + 1) % 5 == 0 or i == page_num - 2:
            print(f"[2]   ... now on page {i + 2}")
    return True


def run_full_extraction():
    setup_dirs()

    start_page = START_PAGE
    if AUTO_RESUME and not os.getenv("HPL_START_PAGE"):
        start_page = detect_start_page()
        print(f"[auto-resume] Next page from {OUTPUT_DIR}/: {start_page}")

    print_run_banner(start_page)
    save_progress(start_page, last_completed=start_page - 1, total_leads=0)

    print("Starting Playwright...", flush=True)
    with sync_playwright() as p:
        print("Launching Chromium...", flush=True)
        browser = p.chromium.launch(
            headless=HEADLESS,
            downloads_path=os.path.abspath(OUTPUT_DIR),
            timeout=120_000,
        )
        print("Chromium launched.", flush=True)
        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        page.set_default_timeout(NAVIGATION_TIMEOUT_MS)

        login(page)
        results_url = run_search(page)

        if start_page > 1:
            if not navigate_to_results_page(page, start_page):
                print("Could not reach start page. Stopping.")
                browser.close()
                return
            results_url = page.url

        batch_number = start_page
        total_leads_processed = 0
        pages_processed = 0
        last_completed_page = start_page - 1

        while True:
            if MAX_PAGES and pages_processed >= MAX_PAGES:
                print(f"\nReached max pages limit ({MAX_PAGES}). Stopping.")
                break

            current_page_num = start_page + pages_processed
            print(f"\n{'='*60}")
            print(f"BATCH {batch_number} | Page {current_page_num}")
            print(f"{'='*60}")

            lead_links = get_lead_links(page)
            if not lead_links:
                print("No more leads found on this page. Done.")
                break

            leads_to_process = lead_links[:BATCH_SIZE]
            print(f"[3] Found {len(lead_links)} leads on page, processing {len(leads_to_process)}...")

            current_results_url = page.url

            for i, lead_url in enumerate(leads_to_process, 1):
                print(f"  [{i}/{len(leads_to_process)}] Opening lead...")
                mark_single_lead(page, lead_url, current_results_url)

            total_leads_processed += len(leads_to_process)

            csv_path = download_marked_csv(page, batch_number, os.path.abspath(OUTPUT_DIR))
            if csv_path:
                print(f"  Batch {batch_number} complete: {len(leads_to_process)} leads -> {csv_path}")
            else:
                print(f"  Batch {batch_number}: marking done but CSV download may have failed.")

            clear_marked(page)

            try:
                page.screenshot(
                    path=f"{SCREENSHOTS_DIR}/batch_{batch_number:04d}_done.png",
                    timeout=15_000,
                )
            except Exception as e:
                print(f"    Screenshot skipped: {e}")

            if not goto_with_retry(page, current_results_url, label="Return to results for next page"):
                print("    WARNING: Could not return to results; trying to continue.")

            has_next = go_to_next_page(page)
            pages_processed += 1
            last_completed_page = current_page_num
            batch_number += 1
            save_progress(start_page, last_completed_page, total_leads_processed)

            if not has_next:
                print("\nNo more pages. Extraction complete.")
                break

        save_progress(start_page, last_completed_page, total_leads_processed, status="complete")

        print(f"\n{'='*60}")
        print("EXTRACTION COMPLETE")
        print(f"Total leads processed: {total_leads_processed}")
        print(f"Total batches (CSVs) this run: {pages_processed}")
        print(f"Files saved in: {os.path.abspath(OUTPUT_DIR)}/")
        if last_completed_page >= start_page:
            print(f"Next run: export HPL_START_PAGE={last_completed_page + 1}")
        print(f"{'='*60}")

        browser.close()


if __name__ == "__main__":
    run_full_extraction()
