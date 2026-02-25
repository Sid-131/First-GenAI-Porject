# backend/data/loader.py
# Phase 1 — HuggingFace dataset loader with local CSV caching

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent          # backend/data/
CSV_PATH = _DATA_DIR / "zomato_cleaned.csv"

# ── In-memory cache ────────────────────────────────────────────────────────
_df: pd.DataFrame | None = None


def _download_and_clean() -> pd.DataFrame:
    """Download dataset from HuggingFace, clean it, and return the DataFrame."""
    from datasets import load_dataset  # lazy import — heavy dependency
    from data.preprocessor import clean_dataframe

    dataset_name = os.getenv("HF_DATASET", "ManikaSaini/zomato-restaurant-recommendation")
    print(f"[loader] Downloading dataset from HuggingFace: {dataset_name}")
    dataset = load_dataset(dataset_name, split="train")
    raw_df = dataset.to_pandas()
    print(f"[loader] Raw dataset fetched — {len(raw_df)} rows")

    cleaned = clean_dataframe(raw_df)

    # Persist locally so future startups skip the download
    cleaned.to_csv(CSV_PATH, index=False)
    print(f"[loader] Saved cleaned dataset → {CSV_PATH}  ({len(cleaned)} rows)")
    return cleaned


def load_dataset_once() -> pd.DataFrame:
    """
    Load the cleaned Zomato dataset, using a local CSV cache when available.

    Fast path  : reads  `data/zomato_cleaned.csv`  (already cleaned)
    Slow path  : downloads from HuggingFace → cleans → saves CSV → returns df

    Idempotent: subsequent calls return the in-memory singleton immediately.
    """
    global _df
    if _df is not None:
        return _df

    if CSV_PATH.exists():
        print(f"[loader] Loading from local cache: {CSV_PATH}")
        _df = pd.read_csv(CSV_PATH)
        print(f"[loader] Loaded {len(_df)} rows from cache")
    else:
        _df = _download_and_clean()

    return _df


def get_dataframe() -> pd.DataFrame:
    """Return the cached, cleaned DataFrame. Auto-loads if not yet initialised."""
    global _df
    if _df is None:
        load_dataset_once()
    return _df
