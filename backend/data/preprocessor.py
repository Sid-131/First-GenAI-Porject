# backend/data/preprocessor.py
# Phase 1 — Data cleaning & normalization

import re
import pandas as pd


def _clean_rate(val) -> float | None:
    """
    Convert messy rating strings to float.
    Examples:  '4.1/5' → 4.1,  'NEW' → NaN,  '-' → NaN,  4.1 → 4.1
    """
    if pd.isna(val):
        return None
    s = str(val).strip()
    # Remove the '/5' suffix if present
    s = re.sub(r"/5\s*$", "", s).strip()
    # Treat non-numeric sentinels as NaN
    if s.lower() in ("new", "-", "", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _clean_cost(val) -> int | None:
    """
    Convert messy cost strings to integer.
    Examples:  '1,500' → 1500,  '800' → 800,  None → NaN
    """
    if pd.isna(val):
        return None
    s = str(val).strip().replace(",", "")
    try:
        return int(float(s))
    except ValueError:
        return None


def _clean_cuisines(val) -> str | None:
    """
    Normalise cuisines to a lowercase, comma-separated string.
    Example:  'North Indian, Chinese' → 'north indian, chinese'
    """
    if pd.isna(val):
        return None
    # Split, strip each part, lowercase, rejoin
    parts = [p.strip().lower() for p in str(val).split(",") if p.strip()]
    return ", ".join(parts) if parts else None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize the raw Zomato DataFrame.

    Cleaning steps applied in order:
    1.  Normalize column names → lowercase snake_case
    2.  Clean 'rate'           → float (strip '/5', map sentinels to NaN)
    3.  Clean 'approx_cost'   → int   (remove commas)
    4.  Clean 'cuisines'      → lowercase comma-separated string
    5.  Drop rows missing any critical field
    6.  Deduplicate on (name, location), keep first
    7.  Reset index
    """
    print(f"[preprocessor] Starting clean — {len(df)} rows, {len(df.columns)} columns")

    # ── 1. Normalize column names ────────────────────────────────────────────
    df = df.copy()
    df.columns = [
        re.sub(r"\s+", "_", col.strip().lower())
        for col in df.columns
    ]

    # Map known HuggingFace column names to canonical names
    # (the HF dataset uses 'approx_cost(for_two_people)' or similar variants)
    col_aliases = {
        "approx_cost(for_two_people)": "approx_cost",
        "approx_cost(for two people)": "approx_cost",
        "approx_cost(for_two_people)": "approx_cost",
        "listed_in(type)": "listed_in_type",
        "listed_in(city)": "listed_in_city",
    }
    df.rename(columns=col_aliases, inplace=True)

    # ── 2. Clean rate ────────────────────────────────────────────────────────
    if "rate" in df.columns:
        df["rate"] = df["rate"].apply(_clean_rate)
        df["rate"] = pd.to_numeric(df["rate"], errors="coerce")

    # ── 3. Clean approx_cost ────────────────────────────────────────────────
    cost_col = next((c for c in df.columns if "approx_cost" in c), None)
    if cost_col:
        df[cost_col] = df[cost_col].apply(_clean_cost)
        if cost_col != "approx_cost":
            df.rename(columns={cost_col: "approx_cost"}, inplace=True)

    # ── 4. Clean cuisines ───────────────────────────────────────────────────
    if "cuisines" in df.columns:
        df["cuisines"] = df["cuisines"].apply(_clean_cuisines)

    # ── 5. Drop critical nulls ──────────────────────────────────────────────
    critical_cols = [c for c in ["name", "location", "cuisines", "rate", "approx_cost"]
                     if c in df.columns]
    before = len(df)
    df.dropna(subset=critical_cols, inplace=True)
    print(f"[preprocessor] Dropped {before - len(df)} rows with nulls in critical columns")

    # ── 6. Deduplicate ──────────────────────────────────────────────────────
    dedup_cols = [c for c in ["name", "location"] if c in df.columns]
    before = len(df)
    df.drop_duplicates(subset=dedup_cols, keep="first", inplace=True)
    print(f"[preprocessor] Removed {before - len(df)} duplicate rows")

    # ── 7. Reset index ──────────────────────────────────────────────────────
    df.reset_index(drop=True, inplace=True)

    print(f"[preprocessor] Done — {len(df)} clean rows remain")
    return df
