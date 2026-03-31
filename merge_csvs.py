"""
Merge all batch CSV files into one master CSV.
Run after the scraper finishes all batches.
"""

import os
import glob
import pandas as pd
from config import OUTPUT_DIR


def merge_all_csvs():
    csv_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "hotel_leads_batch_*.csv")))

    if not csv_files:
        print("No batch CSV files found.")
        return

    print(f"Found {len(csv_files)} batch files.")

    all_dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            df["_source_file"] = os.path.basename(f)
            all_dfs.append(df)
            print(f"  Loaded {len(df)} rows from {os.path.basename(f)}")
        except Exception as e:
            print(f"  ERROR reading {f}: {e}")

    if all_dfs:
        master = pd.concat(all_dfs, ignore_index=True)
        master.drop_duplicates(inplace=True)

        output_path = os.path.join(OUTPUT_DIR, "hotel_leads_MASTER.csv")
        master.to_csv(output_path, index=False)
        print(f"\nMaster CSV saved: {output_path}")
        print(f"Total unique leads: {len(master)}")
    else:
        print("No data to merge.")


if __name__ == "__main__":
    merge_all_csvs()
