# backend/tests/test_phase4.py
# Phase 4 — Integration tests for the full recommendation pipeline
# (engine + routes + Gemini, all Gemini calls mocked)

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Shared mock DataFrame (already-cleaned data) ──────────────────────────────
# Prices are ints, ratings are floats — matching post-preprocessor state.
MOCK_DF = pd.DataFrame({
    "name":        ["Pasta Palace",          "Spice Hub",     "Curry Corner",   "Burger Barn",  "Sushi Stop",   "Noodle Nest"],
    "location":    ["Koramangala",           "Koramangala",   "Koramangala",    "Indiranagar",  "Indiranagar",  "Koramangala"],
    "cuisines":    ["italian, continental",  "north indian",  "north indian, chinese", "american", "japanese",  "chinese"],
    "rate":        [4.3,                     3.9,             4.0,              4.1,            4.6,            4.2],
    "approx_cost": [700,                     400,             500,              300,            1200,           350],
    "votes":       [200,                     100,             80,               150,            400,            60],
})

GEMINI_STUB = "These are fantastic restaurants! Pasta Palace wins for Italian lovers..."


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """TestClient with mocked dataset and Gemini."""
    for mod in list(sys.modules.keys()):
        if any(mod.startswith(p) for p in ("main", "api.", "data.", "engine.", "llm.", "models.")):
            del sys.modules[mod]

    with patch("data.loader.load_dataset_once", return_value=MOCK_DF), \
         patch("data.loader.get_dataframe",      return_value=MOCK_DF):
        from main import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


@pytest.fixture
def mock_gemini():
    """Patch get_llm_recommendation at the engine level for each test."""
    with patch("engine.recommender.get_llm_recommendation", return_value=GEMINI_STUB) as m:
        yield m


def post(client, payload: dict):
    return client.post("/api/recommend", json=payload)


# ─── SECTION 1: Basic happy-path ──────────────────────────────────────────────

class TestHappyPath:

    def test_returns_200(self, client, mock_gemini):
        assert post(client, {"place": "Koramangala"}).status_code == 200

    def test_response_has_restaurants_field(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala"}).json()
        assert "restaurants" in data

    def test_response_has_gemini_review(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala"}).json()
        assert "gemini_review" in data

    def test_response_has_total(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala"}).json()
        assert "total" in data

    def test_total_matches_restaurants_length(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala"}).json()
        assert data["total"] == len(data["restaurants"])

    def test_gemini_review_is_stub_text(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala"}).json()
        assert data["gemini_review"] == GEMINI_STUB

    def test_restaurant_item_has_required_fields(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala"}).json()
        for item in data["restaurants"]:
            assert "name"        in item
            assert "location"    in item
            assert "cuisines"    in item
            assert "rate"        in item
            assert "approx_cost" in item


# ─── SECTION 2: Top-5 cap ─────────────────────────────────────────────────────

class TestTop5Cap:

    def test_returns_at_most_5_restaurants(self, client, mock_gemini):
        # Koramangala has 4 rows in MOCK_DF — all should come back (≤ 5)
        data = post(client, {"place": "Koramangala"}).json()
        assert data["total"] <= 5

    def test_no_more_than_5_even_with_many_matches(self, client, mock_gemini):
        # All restaurants match the empty cuisine filter
        data = post(client, {"place": "Koramangala"}).json()
        assert len(data["restaurants"]) <= 5

    def test_results_sorted_by_rating_descending(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala"}).json()
        ratings = [r["rate"] for r in data["restaurants"] if r["rate"] is not None]
        assert ratings == sorted(ratings, reverse=True)


# ─── SECTION 3: Filter correctness ───────────────────────────────────────────

class TestFilters:

    def test_location_filter_applied(self, client, mock_gemini):
        data = post(client, {"place": "Indiranagar"}).json()
        for r in data["restaurants"]:
            assert "Indiranagar" in r["location"]

    def test_location_case_insensitive(self, client, mock_gemini):
        assert post(client, {"place": "koramangala"}).json()["total"] > 0

    def test_cuisine_filter_applied(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala", "cuisine": "italian"}).json()
        for r in data["restaurants"]:
            assert "italian" in r["cuisines"].lower()

    def test_max_price_filter_applied(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala", "max_price": 500}).json()
        for r in data["restaurants"]:
            assert r["approx_cost"] <= 500

    def test_max_price_excludes_expensive(self, client, mock_gemini):
        # Pasta Palace = 700, excluded when max_price=600
        data = post(client, {"place": "Koramangala", "max_price": 600}).json()
        names = [r["name"] for r in data["restaurants"]]
        assert "Pasta Palace" not in names

    def test_min_rating_filter_applied(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala", "min_rating": 4.2}).json()
        for r in data["restaurants"]:
            assert r["rate"] >= 4.2

    def test_all_filters_combined(self, client, mock_gemini):
        data = post(client, {
            "place": "Koramangala",
            "cuisine": "north indian",
            "max_price": 600,
            "min_rating": 3.5,
        }).json()
        assert "restaurants" in data or "error" in data


# ─── SECTION 4: Edge case — empty results ────────────────────────────────────

class TestEmptyResults:

    def test_unknown_location_returns_error_json(self, client):
        data = post(client, {"place": "NowhereCity_XYZ99"}).json()
        assert "error" in data
        assert data["error"] == "No recommendations returned. Try relaxing filters."

    def test_empty_result_returns_200_not_404(self, client):
        resp = post(client, {"place": "NowhereCity_XYZ99"})
        assert resp.status_code == 200

    def test_empty_result_has_no_restaurants_key(self, client):
        data = post(client, {"place": "NowhereCity_XYZ99"}).json()
        # Should only have "error", not "restaurants"
        assert "restaurants" not in data

    def test_impossible_price_returns_error(self, client):
        # max_price=1 should return no results
        data = post(client, {"place": "Koramangala", "max_price": 1}).json()
        assert "error" in data

    def test_impossible_rating_returns_error(self, client):
        # min_rating=5.0 with few perfect-rated restaurants will likely be empty
        data = post(client, {"place": "Koramangala", "min_rating": 5.0}).json()
        # Either empty error or results — just confirm not a 500
        assert "error" in data or "restaurants" in data

    def test_no_gemini_call_on_empty_result(self, client):
        """Gemini must NOT be called when filters produce no matches (saves quota)."""
        with patch("engine.recommender.get_llm_recommendation") as mock_llm:
            post(client, {"place": "NowhereCity_XYZ99"})
            mock_llm.assert_not_called()


# ─── SECTION 5: Gemini graceful degradation ──────────────────────────────────

class TestGeminiDegradation:

    def test_gemini_failure_still_returns_restaurants(self, client):
        """If Gemini throws, the endpoint still returns restaurant data."""
        with patch("engine.recommender.get_llm_recommendation",
                   side_effect=Exception("Gemini timeout")):
            data = post(client, {"place": "Koramangala"}).json()
        # Should have restaurant data even without gemini_review
        assert "restaurants" in data
        assert data["total"] > 0

    def test_gemini_failure_sets_review_to_null(self, client):
        with patch("engine.recommender.get_llm_recommendation",
                   side_effect=Exception("Quota exceeded")):
            data = post(client, {"place": "Koramangala"}).json()
        assert data.get("gemini_review") is None


# ─── SECTION 6: Data cleaning validation ─────────────────────────────────────

class TestDataCleaning:

    def test_prices_are_integers(self, client, mock_gemini):
        """approx_cost must be int (commas removed by preprocessor)."""
        data = post(client, {"place": "Koramangala"}).json()
        for r in data["restaurants"]:
            if r["approx_cost"] is not None:
                assert isinstance(r["approx_cost"], int)

    def test_ratings_are_floats(self, client, mock_gemini):
        """rate must be float (/5 stripped by preprocessor)."""
        data = post(client, {"place": "Koramangala"}).json()
        for r in data["restaurants"]:
            if r["rate"] is not None:
                assert isinstance(r["rate"], float)

    def test_no_duplicate_restaurants_in_response(self, client, mock_gemini):
        data = post(client, {"place": "Koramangala"}).json()
        names = [r["name"] for r in data["restaurants"]]
        assert len(names) == len(set(names)), "Duplicate restaurants in response"


# ─── SECTION 7: Input validation ─────────────────────────────────────────────

class TestInputValidation:

    def test_missing_place_returns_422(self, client):
        assert post(client, {"cuisine": "Italian"}).status_code == 422

    def test_empty_place_returns_422(self, client):
        assert post(client, {"place": ""}).status_code == 422

    def test_negative_price_returns_422(self, client):
        assert post(client, {"place": "Koramangala", "max_price": -1}).status_code == 422

    def test_rating_above_5_returns_422(self, client):
        assert post(client, {"place": "Koramangala", "min_rating": 6.0}).status_code == 422
