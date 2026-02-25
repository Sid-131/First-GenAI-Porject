# backend/api/routes.py
# Phase 4 — REST API endpoints

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from data.loader import get_dataframe
from engine.recommender import get_recommendations
from models.schemas import (
    ErrorResponse,
    PlacesResponse,
    RecommendRequest,
    RecommendResponse,
)

router = APIRouter()


# ─── GET /api/places ──────────────────────────────────────────────────────────

@router.get(
    "/places",
    response_model=PlacesResponse,
    summary="List all unique locations",
    tags=["Discovery"],
)
def get_places():
    """
    Returns a sorted list of all distinct restaurant locations in the dataset.
    Useful for populating a location dropdown in the UI.
    """
    df = get_dataframe()
    if "location" not in df.columns:
        return JSONResponse(status_code=500, content={"error": "'location' column missing"})

    places = sorted(df["location"].dropna().unique().tolist())
    return PlacesResponse(total=len(places), places=places)


# ─── POST /api/recommend ──────────────────────────────────────────────────────

@router.post(
    "/recommend",
    summary="Get Gemini-powered restaurant recommendations",
    tags=["Recommendations"],
)
def recommend(request: RecommendRequest):
    """
    Phase 4 pipeline:

    1. **Filter** the Zomato dataset by `place`, `cuisine`, `max_price`, `min_rating`.
       Data is pre-cleaned (prices as ints, ratings as floats, no duplicates).
    2. **Empty result** → returns `{"error": "No recommendations returned. Try relaxing filters."}`
    3. **Top 5** matching restaurants sent to **Gemini** as expert food critic context.
    4. Returns JSON with both raw restaurant data and Gemini's written review.
    """
    result = get_recommendations(
        place=request.place,
        cuisine=request.cuisine,
        max_price=request.max_price,
        min_rating=request.min_rating,
    )

    # Edge case: no matches → return the exact error JSON specified
    if isinstance(result, ErrorResponse):
        return JSONResponse(
            status_code=200,
            content={"error": result.error},
        )

    return result
