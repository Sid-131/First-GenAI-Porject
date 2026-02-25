#!/usr/bin/env python
"""
download_dataset.py — Phase 1 standalone CLI script.

Usage (from the `backend/` directory):
    python data/download_dataset.py

Downloads the Zomato dataset from HuggingFace, applies all cleaning rules,
and saves the result to data/zomato_cleaned.csv.
"""

import sys
from pathlib import Path

# Allow running from backend/ directory without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from datasets import load_dataset
import os

from data.preprocessor import clean_dataframe
from data.loader import CSV_PATH


def main():
    dataset_name = os.getenv("HF_DATASET", "ManikaSaini/zomato-restaurant-recommendation")

    print("=" * 60)
    print("  Zomato Dataset Downloader — Phase 1")
    print("=" * 60)
    print(f"\n[1/3] Downloading from HuggingFace: {dataset_name}")

    dataset = load_dataset(dataset_name, split="train")
    raw_df = dataset.to_pandas()
    print(f"      Raw rows: {len(raw_df)}")
    print(f"      Columns : {list(raw_df.columns)}\n")

    print("[2/3] Cleaning dataset...")
    cleaned_df = clean_dataframe(raw_df)

    print(f"\n[3/3] Saving to {CSV_PATH}")
    cleaned_df.to_csv(CSV_PATH, index=False)

    print("\n" + "=" * 60)
    print(f"  ✅  Done! {len(cleaned_df)} clean rows saved.")
    print(f"       Columns: {list(cleaned_df.columns)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
