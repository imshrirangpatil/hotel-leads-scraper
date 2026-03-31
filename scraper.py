"""
Hotel Project Leads Scraper
Automates: Login → Search → Mark leads in batches → Download CSV
Uses Playwright (Python) for browser automation.
"""

import os
import time
import glob
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import (
    HPL_URL, HPL_LOGIN_URL, HPL_SEARCH_URL,
    HPL_USERNAME, HPL_PASSWORD,
    SEARCH_FROM_DATE, BATCH_SIZE, MAX_PAGES, START_PAGE,
    OUTPUT_DIR, SCREENSHOTS_DIR,
    PAGE_LOAD_WAIT, ACTION_DELAY, MARK_DELAY, NAVIGATION_TIMEOUT_MS
)


def setup_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def results_url_with_page(base_url, page_num):
    """Set or replace pnum in the search results URL for chunked runs."""
    parsed = urlparse(base_url)
    qs = parse_qs(parsed.query)
    qs["pnum"] = [str(page_num)]
    new_query = urlencode(qs, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def get_latest_download(download_dir, before_files):
    """Find the newest file in download_dir that wasn't there before."""
    after_files = set(glob.glob(os.path.join(download_dir, "*.csv")))
    new_files = after_files - before_files
    if new_files:
        return max(new_files, key=os.path.getmtime)
    return None


def login(page):
    """Log in to Hotel Project Leads."""
    print("[1] Navigating to login page...")
    page.goto(HPL_LOGIN_URL, wait_until="networkidle")
    time.sleep(ACTION_DELAY)

    page.fill('input[name="log"], input[type="text"]', HPL_USERNAME)
    page.fill('input[name="pwd"], input[type="password"]', HPL_PASSWORD)
    page.click('input[type="submit"], button[type="submit"]')
    page.wait_for_load_state("networkidle")
    time.sleep(ACTION_DELAY)

    print("[1] Login successful.")
    page.screenshot(path=f"{SCREENSHOTS_DIR}/01_after_login.png")


def run_search(page):
    """Navigate to search page, apply filters, and click Search."""
    print("[2] Navigating to search page...")
    page.goto(HPL_SEARCH_URL, wait_until="networkidle")
    time.sleep(ACTION_DELAY)

    # Try to configure location filter: select "North America" and move all
    # locations on the left list into the right list.
    try:
        print("[2] Configuring location filter for North America...")

        # Click the "North America" radio/tab if present.
        try:
            na_tab = page.get_by_text("North America", exact=True).first
            if na_tab.is_visible():
                na_tab.click()
                time.sleep(0.5)
        except Exception as e:
            print(f'[2] Warning: Could not activate "North America" tab: {e}')

        # Focus the left-hand multi-select list containing US states.
        left_list = page.locator("select[multiple]").first
        left_list.click()
        time.sleep(0.2)

        # Select all options in that list programmatically (more reliable than keyboard).
        options = left_list.locator("option").all()
        values = []
        for opt in options:
            value = opt.get_attribute("value")
            if value:
                values.append(value)
        if values:
            left_list.select_option(values)
        else:
            # Fallback: try keyboard shortcuts (both Control+A and Meta+A for macOS).
            page.keyboard.press("Control+A")
            time.sleep(0.3)
            page.keyboard.press("Meta+A")
        time.sleep(0.5)

        # Click the ">>" button to move all selected locations to the right-hand list.
        move_right_btn = page.locator(
            'input[type="button"][value=">>"], button:has-text(">>")'
        ).first
        move_right_btn.click()
        time.sleep(0.5)

        print("[2] Location filter configured for North America.")
    except Exception as e:
        print(f"[2] Warning: Could not configure North America location filter: {e}")

    # Select all project types
    try:
        select_all_buttons = page.locator('text="Select All"').all()
        for btn in select_all_buttons:
            btn.click()
            time.sleep(0.5)
        print("[2] Selected all filter options.")
    except Exception as e:
        print(f"[2] Warning: Could not click Select All: {e}")

    # Set the from date
    try:
        date_input = page.locator('input[name="fromDate"], input[placeholder*="date"], input[type="date"]').first
        date_input.fill(SEARCH_FROM_DATE)
        print(f"[2] Set from date to {SEARCH_FROM_DATE}.")
    except Exception as e:
        print(f"[2] Warning: Could not set date: {e}")

    time.sleep(ACTION_DELAY)

    # Click Search
    page.click('input[value="Search"], button:has-text("Search")')
    page.wait_for_load_state("networkidle")
    time.sleep(PAGE_LOAD_WAIT)

    print("[2] Search completed.")
    page.screenshot(path=f"{SCREENSHOTS_DIR}/02_search_results.png")

    return page.url


def get_lead_links(page):
    """Extract all clickable lead links from the current results page."""
    # Adjust this selector to match the actual lead-detail link pattern
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
    """Open a lead detail page, click Mark, then return to results."""
    # Go to lead page (use "load" to avoid timeout; retry once; skip lead if both fail)
    for attempt in range(2):
        try:
            page.goto(lead_url, wait_until="load", timeout=NAVIGATION_TIMEOUT_MS)
            break
        except PlaywrightTimeout:
            if attempt == 0:
                print("    Timeout loading lead page, retrying...")
            else:
                print(f"    WARNING: Skipping lead (timeout), continuing...")
                return
    time.sleep(ACTION_DELAY)

    # Click Mark (exact text so we don't hit "Marketplace" or other links containing "Mark")
    try:
        mark_link = page.locator("a").filter(has=page.get_by_text("Mark", exact=True)).first
        mark_link.click()
        time.sleep(MARK_DELAY)
        print(f"    Marked: {lead_url.split('/')[-1][:50]}...")
    except Exception as e:
        print(f"    WARNING: Could not mark lead: {e}")

    # Return to results page (use "load"; retry up to 2 times on timeout)
    for attempt in range(3):
        try:
            page.goto(
                results_url,
                wait_until="load",
                timeout=NAVIGATION_TIMEOUT_MS,
            )
            break
        except PlaywrightTimeout:
            if attempt < 2:
                print("    Timeout returning to results, retrying...")
            else:
                raise
    time.sleep(ACTION_DELAY)


def download_marked_csv(page, batch_number, download_dir):
    """Click 'View your marked leads', then 'Download CSV'."""
    print(f"[4] Downloading CSV for batch {batch_number}...")

    # Click "View your marked leads"
    try:
        view_marked = page.locator('a:has-text("View your marked leads"), a:has-text("view your marked")').first
        view_marked.click()
        page.wait_for_load_state("load", timeout=NAVIGATION_TIMEOUT_MS)
        time.sleep(ACTION_DELAY)
    except Exception as e:
        print(f"    WARNING: Could not find 'View your marked leads': {e}")
        return None

    # Track existing CSV files before download
    before_files = set(glob.glob(os.path.join(download_dir, "*.csv")))

    # Click "Download CSV"
    try:
        with page.expect_download(timeout=NAVIGATION_TIMEOUT_MS) as download_info:
            download_csv = page.locator('a:has-text("Download CSV")').first
            download_csv.click()
        download = download_info.value
        # Save with batch name
        batch_filename = f"hotel_leads_batch_{batch_number:04d}.csv"
        save_path = os.path.join(OUTPUT_DIR, batch_filename)
        download.save_as(save_path)
        print(f"    Saved: {save_path}")
        return save_path
    except Exception as e:
        print(f"    WARNING: Download failed: {e}")
        # Fallback: check download directory
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
    """On the 'View your marked leads' page, click Clear marked so the list is reset for the next batch."""
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
    """Click the Next button on the results page. Returns True if successful."""
    try:
        next_btn = page.locator('a:has-text("Next"), a:has-text(">>"), a:has-text("›")').first
        if next_btn.is_visible():
            next_btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(PAGE_LOAD_WAIT)
            return True
    except Exception:
        pass
    return False


def run_full_extraction():
    """Main extraction loop: mark leads in batches, download CSV per batch."""
    setup_dirs()

    with sync_playwright() as p:
        # Launch browser (visible for debugging; set headless=True for production)
        browser = p.chromium.launch(
            headless=False,
            downloads_path=os.path.abspath(OUTPUT_DIR)
        )
        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
        page.set_default_timeout(NAVIGATION_TIMEOUT_MS)

        # Step 1: Login
        login(page)

        # Step 2: Search
        results_url = run_search(page)

        # If chunked run: jump to start page (e.g. 101 for chunk 2)
        if START_PAGE > 1:
            start_url = results_url_with_page(results_url, START_PAGE)
            print(f"[2] Chunked run: jumping to page {START_PAGE}...")
            page.goto(start_url, wait_until="networkidle")
            time.sleep(PAGE_LOAD_WAIT)

        # Step 3: Batch loop
        batch_number = START_PAGE
        total_leads_processed = 0
        pages_processed = 0

        while True:
            if MAX_PAGES and pages_processed >= MAX_PAGES:
                print(f"\nReached max pages limit ({MAX_PAGES}). Stopping.")
                break

            current_page_num = START_PAGE + pages_processed
            print(f"\n{'='*60}")
            print(f"BATCH {batch_number} | Page {current_page_num}")
            print(f"{'='*60}")

            # Get all lead links on current page
            lead_links = get_lead_links(page)
            if not lead_links:
                print("No more leads found on this page. Done.")
                break

            leads_to_process = lead_links[:BATCH_SIZE]
            print(f"[3] Found {len(lead_links)} leads on page, processing {len(leads_to_process)}...")

            # Save current results URL for returning after each mark
            current_results_url = page.url

            # Mark each lead
            for i, lead_url in enumerate(leads_to_process, 1):
                print(f"  [{i}/{len(leads_to_process)}] Opening lead...")
                mark_single_lead(page, lead_url, current_results_url)

            total_leads_processed += len(leads_to_process)

            # Download the CSV for this batch
            csv_path = download_marked_csv(page, batch_number, os.path.abspath(OUTPUT_DIR))

            if csv_path:
                print(f"  Batch {batch_number} complete: {len(leads_to_process)} leads -> {csv_path}")
            else:
                print(f"  Batch {batch_number}: marking done but CSV download may have failed.")

            # Clear marked leads so the next batch only contains the next 15 (site limit ~20 per CSV)
            clear_marked(page)

            # Screenshot after batch (non-fatal if it times out)
            try:
                page.screenshot(path=f"{SCREENSHOTS_DIR}/batch_{batch_number:04d}_done.png", timeout=15000)
            except Exception as e:
                print(f"    Screenshot skipped: {e}")

            # Navigate back to results and go to next page
            page.goto(current_results_url, wait_until="load", timeout=NAVIGATION_TIMEOUT_MS)
            time.sleep(ACTION_DELAY)

            has_next = go_to_next_page(page)
            pages_processed += 1
            batch_number += 1

            if not has_next:
                print("\nNo more pages. Extraction complete.")
                break

        # Summary
        print(f"\n{'='*60}")
        print(f"EXTRACTION COMPLETE")
        print(f"Total leads processed: {total_leads_processed}")
        print(f"Total batches (CSVs) this run: {pages_processed}")
        print(f"Files saved in: {os.path.abspath(OUTPUT_DIR)}/")
        print(f"{'='*60}")

        browser.close()


if __name__ == "__main__":
    run_full_extraction()
