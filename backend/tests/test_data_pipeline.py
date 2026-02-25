# backend/tests/test_data_pipeline.py
# Phase 1 — pytest tests for data loading and cleaning

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

# Allow imports from backend/ root when running with `pytest` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.preprocessor import (
    _clean_cost,
    _clean_cuisines,
    _clean_rate,
    clean_dataframe,
)


# ─── Unit tests for helper functions ──────────────────────────────────────────

class TestCleanRate:
    """Rate string → float conversion"""

    def test_standard_rating_with_suffix(self):
        assert _clean_rate("4.1/5") == pytest.approx(4.1)

    def test_rating_without_suffix(self):
        assert _clean_rate("3.8") == pytest.approx(3.8)

    def test_rating_perfect_score(self):
        assert _clean_rate("5/5") == pytest.approx(5.0)

    def test_sentinel_new(self):
        assert _clean_rate("NEW") is None

    def test_sentinel_dash(self):
        assert _clean_rate("-") is None

    def test_sentinel_empty_string(self):
        assert _clean_rate("") is None

    def test_nan_input(self):
        assert _clean_rate(float("nan")) is None

    def test_numeric_passthrough(self):
        """Already a float — should be returned as-is."""
        assert _clean_rate(4.5) == pytest.approx(4.5)

    def test_whitespace_stripped(self):
        assert _clean_rate("  4.1/5  ") == pytest.approx(4.1)


class TestCleanCost:
    """Cost string → int conversion"""

    def test_comma_separated_cost(self):
        assert _clean_cost("1,500") == 1500

    def test_plain_number_string(self):
        assert _clean_cost("800") == 800

    def test_large_cost_with_comma(self):
        assert _clean_cost("2,000") == 2000

    def test_none_input(self):
        assert _clean_cost(None) is None

    def test_nan_input(self):
        assert _clean_cost(float("nan")) is None

    def test_numeric_passthrough(self):
        assert _clean_cost(600) == 600


class TestCleanCuisines:
    """Cuisine string normalization"""

    def test_mixedcase_to_lowercase(self):
        assert _clean_cuisines("North Indian, Chinese") == "north indian, chinese"

    def test_already_lowercase(self):
        assert _clean_cuisines("italian") == "italian"

    def test_whitespace_stripped(self):
        assert _clean_cuisines("  Biryani , BBQ  ") == "biryani, bbq"

    def test_none_input(self):
        assert _clean_cuisines(None) is None

    def test_single_cuisine(self):
        assert _clean_cuisines("Continental") == "continental"


# ─── Integration tests for clean_dataframe() ──────────────────────────────────

class TestCleanDataframe:
    """End-to-end clean_dataframe() on the shared mock fixture."""

    def test_returns_dataframe(self, sample_raw_df):
        result = clean_dataframe(sample_raw_df)
        assert isinstance(result, pd.DataFrame)

    def test_rate_column_is_float(self, sample_raw_df):
        result = clean_dataframe(sample_raw_df)
        assert pd.api.types.is_float_dtype(result["rate"]) or \
               result["rate"].apply(lambda x: isinstance(x, float) or math.isnan(x)).all()

    def test_price_parsed_correctly(self, sample_raw_df):
        result = clean_dataframe(sample_raw_df)
        # '1,500' and '1,200' must be integers after cleaning
        assert 1500 in result["approx_cost"].values
        assert 1200 in result["approx_cost"].values

    def test_rating_parsed_correctly(self, sample_raw_df):
        result = clean_dataframe(sample_raw_df)
        assert 4.1 in [round(v, 2) for v in result["rate"].values]
        assert 4.5 in [round(v, 2) for v in result["rate"].values]

    def test_cuisine_lowercased(self, sample_raw_df):
        result = clean_dataframe(sample_raw_df)
        for val in result["cuisines"]:
            assert val == val.lower(), f"Cuisine not lowercase: {val!r}"

    def test_null_rows_dropped(self, sample_raw_df):
        """Row with 'NEW' rating (→ NaN) must be removed."""
        result = clean_dataframe(sample_raw_df)
        # 'Null Bistro' had rate='NEW' → should be gone
        assert "Null Bistro" not in result["name"].values

    def test_deduplication(self, sample_raw_df):
        """Duplicate (Trattoria, Koramangala) must appear only once."""
        result = clean_dataframe(sample_raw_df)
        mask = (result["name"] == "Trattoria") & (result["location"] == "Koramangala")
        assert mask.sum() == 1

    def test_row_count_reduced(self, sample_raw_df):
        """5 raw rows → 3 after dropping null+duplicate."""
        result = clean_dataframe(sample_raw_df)
        assert len(result) == 3

    def test_index_reset(self, sample_raw_df):
        """Index must be a clean 0-based RangeIndex."""
        result = clean_dataframe(sample_raw_df)
        assert list(result.index) == list(range(len(result)))

    def test_column_names_normalized(self, sample_raw_df):
        """All column names must be lowercase with no spaces."""
        result = clean_dataframe(sample_raw_df)
        for col in result.columns:
            assert col == col.lower(), f"Column not lowercase: {col!r}"
            assert " " not in col, f"Column has spaces: {col!r}"


# ─── Integration test: full CSV round-trip (requires internet) ─────────────────

@pytest.mark.integration
def test_csv_roundtrip(tmp_path, monkeypatch):
    """
    Downloads the real HF dataset, cleans it, saves to a temp CSV,
    then re-loads it and checks it's non-empty and has expected columns.

    Skipped by default — run with: pytest -m integration
    """
    import os
    from datasets import load_dataset
    from data.preprocessor import clean_dataframe

    dataset_name = os.getenv("HF_DATASET", "ManikaSaini/zomato-restaurant-recommendation")
    dataset = load_dataset(dataset_name, split="train")
    raw_df = dataset.to_pandas()

    cleaned = clean_dataframe(raw_df)
    csv_path = tmp_path / "zomato_cleaned.csv"
    cleaned.to_csv(csv_path, index=False)

    # Verify file exists and is readable
    assert csv_path.exists()
    reloaded = pd.read_csv(csv_path)
    assert len(reloaded) > 1000, "Expected at least 1000 rows after cleaning"
    assert "name" in reloaded.columns
    assert "location" in reloaded.columns
    assert "rate" in reloaded.columns
    assert "approx_cost" in reloaded.columns
    assert "cuisines" in reloaded.columns
    # Verify no sentinel strings survived
    assert not reloaded["rate"].isin(["NEW", "-"]).any()
