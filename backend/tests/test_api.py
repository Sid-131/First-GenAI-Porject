# backend/tests/test_api.py
# Phase 2/4 — FastAPI endpoint tests (schema updated for Phase 4 field names)

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MOCK_DF = pd.DataFrame({
    "name":        ["Pasta Palace", "Spice Hub",    "Curry Corner",  "Burger Barn",   "Sushi Stop"],
    "location":    ["Koramangala",  "Koramangala",  "Koramangala",   "Indiranagar",   "Indiranagar"],
    "cuisines":    ["italian, continental", "north indian", "north indian, chinese", "american, fast food", "japanese"],
    "rate":        [4.3,            3.9,            4.0,             4.1,             4.6],
    "approx_cost": [700,            400,            500,             300,             1200],
    "votes":       [200,            100,            80,              150,             400],
})


@pytest.fixture(scope="module")
def client():
    for mod in list(sys.modules.keys()):
        if any(mod.startswith(p) for p in ("main", "api.", "data.", "engine.", "llm.", "models.")):
            del sys.modules[mod]

    with patch("data.loader.load_dataset_once", return_value=MOCK_DF), \
         patch("data.loader.get_dataframe",      return_value=MOCK_DF), \
         patch("engine.recommender.get_llm_recommendation", return_value="Great picks!"):
        from main import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


class TestHealthCheck:
    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_body(self, client):
        assert client.get("/health").json()["status"] == "ok"


class TestGetPlaces:
    def test_returns_200(self, client):
        assert client.get("/api/places").status_code == 200

    def test_response_has_places_list(self, client):
        data = client.get("/api/places").json()
        assert "places" in data
        assert isinstance(data["places"], list)

    def test_places_are_sorted(self, client):
        places = client.get("/api/places").json()["places"]
        assert places == sorted(places)

    def test_places_are_unique(self, client):
        places = client.get("/api/places").json()["places"]
        assert len(places) == len(set(places))

    def test_total_matches_list_length(self, client):
        data = client.get("/api/places").json()
        assert data["total"] == len(data["places"])

    def test_known_locations_present(self, client):
        places = client.get("/api/places").json()["places"]
        assert "Koramangala" in places
        assert "Indiranagar" in places


class TestPostRecommend:

    def _post(self, client, payload: dict):
        return client.post("/api/recommend", json=payload)

    def test_basic_request_returns_200(self, client):
        assert self._post(client, {"place": "Koramangala"}).status_code == 200

    def test_response_has_restaurants_field(self, client):
        data = self._post(client, {"place": "Koramangala"}).json()
        assert "restaurants" in data

    def test_response_has_total(self, client):
        data = self._post(client, {"place": "Koramangala"}).json()
        assert "total" in data

    def test_response_has_gemini_review(self, client):
        data = self._post(client, {"place": "Koramangala"}).json()
        assert "gemini_review" in data

    def test_total_matches_restaurants_length(self, client):
        data = self._post(client, {"place": "Koramangala"}).json()
        assert data["total"] == len(data["restaurants"])

    def test_restaurant_item_has_required_fields(self, client):
        data = self._post(client, {"place": "Koramangala"}).json()
        for item in data["restaurants"]:
            for field in ("name", "location", "cuisines"):
                assert field in item

    def test_location_filter(self, client):
        data = self._post(client, {"place": "Indiranagar"}).json()
        for item in data["restaurants"]:
            assert "Indiranagar" in item["location"]

    def test_location_case_insensitive(self, client):
        assert self._post(client, {"place": "koramangala"}).json()["total"] > 0

    def test_cuisine_filter(self, client):
        data = self._post(client, {"place": "Koramangala", "cuisine": "italian"}).json()
        for item in data["restaurants"]:
            assert "italian" in item["cuisines"].lower()

    def test_max_price_filter(self, client):
        data = self._post(client, {"place": "Koramangala", "max_price": 500}).json()
        for item in data["restaurants"]:
            assert item["approx_cost"] <= 500

    def test_max_price_excludes_expensive(self, client):
        data = self._post(client, {"place": "Koramangala", "max_price": 600}).json()
        names = [r["name"] for r in data["restaurants"]]
        assert "Pasta Palace" not in names
        assert any(r["approx_cost"] <= 600 for r in data["restaurants"])

    def test_min_rating_filter(self, client):
        data = self._post(client, {"place": "Koramangala", "min_rating": 4.2}).json()
        for item in data["restaurants"]:
            assert item["rate"] >= 4.2

    def test_results_sorted_by_rating_desc(self, client):
        data = self._post(client, {"place": "Koramangala"}).json()
        ratings = [r["rate"] for r in data["restaurants"] if r["rate"] is not None]
        assert ratings == sorted(ratings, reverse=True)

    def test_unknown_location_returns_error_json(self, client):
        data = self._post(client, {"place": "NowhereCity_XYZ"}).json()
        assert "error" in data
        assert data["error"] == "No recommendations returned. Try relaxing filters."

    def test_missing_place_returns_422(self, client):
        assert self._post(client, {"cuisine": "Italian"}).status_code == 422

    def test_invalid_rating_above_5_returns_422(self, client):
        assert self._post(client, {"place": "Koramangala", "min_rating": 6.0}).status_code == 422

    def test_invalid_negative_price_returns_422(self, client):
        assert self._post(client, {"place": "Koramangala", "max_price": -100}).status_code == 422

    def test_empty_place_returns_422(self, client):
        assert self._post(client, {"place": ""}).status_code == 422

    def test_nonexistent_location_returns_200_not_500(self, client):
        response = self._post(client, {"place": "NowhereCity_XYZ"})
        assert response.status_code == 200

    def test_all_filters_combined(self, client):
        data = self._post(client, {
            "place": "Koramangala",
            "cuisine": "north indian",
            "max_price": 600,
            "min_rating": 3.5,
        }).json()
        assert "restaurants" in data or "error" in data
