"""
Merge all batch CSV files into one master CSV.
Run after the scraper finishes all batches.
"""

import os
import glob
import pandas as pd
from config import OUTPUT_DIR, MASTER_OUTPUT_DIR

DEDUP_COLUMNS = ["hotel name", "hotel city", "hotel state", "project scope"]


def find_batch_files():
    csv_files = glob.glob("csv_exports/hotel_leads_batch_*.csv")
    csv_files.extend(glob.glob("csv_exports_*/hotel_leads_batch_*.csv"))
    if OUTPUT_DIR not in ("csv_exports",) and not OUTPUT_DIR.startswith("csv_exports_"):
        csv_files.extend(glob.glob(os.path.join(OUTPUT_DIR, "hotel_leads_batch_*.csv")))
    return sorted(set(csv_files))


def merge_all_csvs():
    csv_files = find_batch_files()

    if not csv_files:
        print("No batch CSV files found.")
        return

    print(f"Found {len(csv_files)} batch files.")

    all_dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            df["_source_file"] = os.path.basename(f)
            df["_source_dir"] = os.path.dirname(f)
            all_dfs.append(df)
            print(f"  Loaded {len(df)} rows from {f}")
        except Exception as e:
            print(f"  ERROR reading {f}: {e}")

    if not all_dfs:
        print("No data to merge.")
        return

    master = pd.concat(all_dfs, ignore_index=True)
    before = len(master)

    dedup_cols = [c for c in DEDUP_COLUMNS if c in master.columns]
    if dedup_cols:
        master.drop_duplicates(subset=dedup_cols, keep="last", inplace=True)
    else:
        master.drop_duplicates(inplace=True)

    removed = before - len(master)
    if removed:
        print(f"  Removed {removed} duplicate row(s) (key: {dedup_cols or 'all columns'})")

    os.makedirs(MASTER_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(MASTER_OUTPUT_DIR, "hotel_leads_MASTER.csv")
    master.to_csv(output_path, index=False)
    print(f"\nMaster CSV saved: {output_path}")
    print(f"Total unique leads: {len(master)}")


if __name__ == "__main__":
    merge_all_csvs()
