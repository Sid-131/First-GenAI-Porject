# backend/tests/conftest.py
# Shared pytest fixtures for Phase 1 and Phase 2 tests

import pandas as pd
import pytest


@pytest.fixture
def sample_raw_df() -> pd.DataFrame:
    """
    A small mock DataFrame mimicking the raw Zomato HuggingFace dataset
    with dirty values that the preprocessor must fix:
      - price strings with commas
      - rating strings with '/5' suffix and sentinels
      - mixed-case cuisines
      - duplicate rows
      - a row with a null in a critical field
    """
    data = {
        "name": [
            "Trattoria",      # normal row
            "Spice Garden",   # normal row
            "Trattoria",      # duplicate of row 0 (same name+location)
            "Null Bistro",    # will be dropped — null rating
            "The Diner",      # normal row — cost has comma
        ],
        "location": [
            "Koramangala",
            "Indiranagar",
            "Koramangala",     # duplicate
            "Whitefield",
            "HSR Layout",
        ],
        "cuisines": [
            "North Indian, Chinese",
            "south indian",
            "North Indian, Chinese",  # duplicate
            "Italian",
            "American, Fast Food",
        ],
        "rate": [
            "4.1/5",
            "3.8/5",
            "4.1/5",   # duplicate
            "NEW",     # sentinel → NaN → row dropped
            "4.5/5",
        ],
        "approx_cost(for two people)": [
            "800",
            "1,200",
            "800",    # duplicate
            "500",
            "1,500",
        ],
        "votes": [120, 340, 120, 0, 670],
    }
    return pd.DataFrame(data)
