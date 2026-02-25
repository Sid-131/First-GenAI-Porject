# backend/engine/recommender.py
# Phase 4 — Full Recommendation Engine
# Pipeline: Load dataset → Filter → (empty check) → Top-5 → Gemini → Response

from typing import Optional, Union

import pandas as pd

from data.loader import get_dataframe
from llm.gemini_client import get_llm_recommendation
from models.schemas import ErrorResponse, RecommendResponse, RestaurantItem


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_dict(row: pd.Series) -> dict:
    """Convert a DataFrame row to a plain dict for the LLM prompt."""
    return {
        "name":        str(row.get("name", "")),
        "location":    str(row.get("location", "")),
        "cuisines":    str(row.get("cuisines", "")),
        "rate":        float(row["rate"])       if pd.notna(row.get("rate"))        else None,
        "approx_cost": int(row["approx_cost"]) if pd.notna(row.get("approx_cost")) else None,
        "votes":       int(row["votes"])        if "votes" in row and pd.notna(row.get("votes")) else None,
    }


def _row_to_item(row: pd.Series) -> RestaurantItem:
    """Convert a DataFrame row to a RestaurantItem Pydantic model."""
    return RestaurantItem(
        name=str(row.get("name", "Unknown")),
        location=str(row.get("location", "")),
        cuisines=str(row.get("cuisines", "")),
        rate=float(row["rate"])       if pd.notna(row.get("rate"))        else None,
        approx_cost=int(row["approx_cost"]) if pd.notna(row.get("approx_cost")) else None,
        votes=int(row["votes"])       if "votes" in row and pd.notna(row.get("votes")) else None,
    )


# ── Main pipeline ─────────────────────────────────────────────────────────────

def get_recommendations(
    place: str,
    cuisine: Optional[str],
    max_price: Optional[int],
    min_rating: Optional[float],
) -> Union[RecommendResponse, ErrorResponse]:
    """
    Full Phase 4 pipeline:

    1. Load the pre-cleaned Zomato dataset (data already cleaned by preprocessor:
       price commas removed, rating /5 stripped, duplicates dropped).
    2. Apply user filters: place (required), cuisine, max_price, min_rating.
    3. If no matches → return ErrorResponse immediately (no LLM call).
    4. Sort by rating ↓ then votes ↓, take top 5.
    5. Format top-5 as a text block and call Gemini (expert food critic).
    6. Return RecommendResponse with both raw restaurant data + Gemini review.
    """
    df = get_dataframe()

    # ── Step 1: Build filter mask ─────────────────────────────────────────────
    mask = pd.Series([True] * len(df), index=df.index)

    # Place (required) — case-insensitive substring match
    if "location" in df.columns:
        mask &= df["location"].str.contains(place, case=False, na=False)

    # Cuisine (optional) — case-insensitive substring match
    if cuisine and "cuisines" in df.columns:
        mask &= df["cuisines"].str.contains(cuisine, case=False, na=False)

    # Max price (optional) — dataset already cleaned: '1,500' → 1500
    if max_price is not None and "approx_cost" in df.columns:
        mask &= df["approx_cost"] <= max_price

    # Min rating (optional) — dataset already cleaned: '4.1/5' → 4.1
    if min_rating is not None and "rate" in df.columns:
        mask &= df["rate"] >= min_rating

    filtered = df[mask].copy()

    # ── Step 2: Edge case — no matches ───────────────────────────────────────
    if filtered.empty:
        return ErrorResponse(
            error="No recommendations returned. Try relaxing filters."
        )

    # ── Step 3: Sort & take top 5 ────────────────────────────────────────────
    sort_cols = [c for c in ["rate", "votes"] if c in filtered.columns]
    if sort_cols:
        filtered.sort_values(by=sort_cols, ascending=False, inplace=True)

    top5 = filtered.head(5)

    # ── Step 4: Call Gemini ───────────────────────────────────────────────────
    restaurant_dicts = [_row_to_dict(row) for _, row in top5.iterrows()]

    gemini_review: Optional[str] = None
    try:
        gemini_review = get_llm_recommendation(
            place=place,
            cuisine=cuisine,
            max_price=max_price,
            min_rating=min_rating,
            restaurants=restaurant_dicts,
        )
    except Exception as exc:
        # Degrade gracefully — never let LLM failure block the response
        print(f"[recommender] Gemini call failed (non-fatal): {type(exc).__name__}: {exc}")
        gemini_review = None

    # ── Step 5: Build response ────────────────────────────────────────────────
    items = [_row_to_item(row) for _, row in top5.iterrows()]

    return RecommendResponse(
        total=len(items),
        restaurants=items,
        gemini_review=gemini_review,
    )
