"""
Phase 3 Integration Test — Gemini Connection Verifier
=====================================================
Run directly:  venv\\Scripts\\python.exe tests/test_phase3_integration.py
Or via pytest: venv\\Scripts\\python.exe -m pytest tests/test_phase3_integration.py -v -s -m integration

Tests:
  1. API key is present in environment
  2. Gemini client initialises without errors
  3. The configured model is listed as available
  4. A minimal ping prompt gets a non-empty response
  5. A full restaurant recommendation prompt returns meaningful text
"""

import os
import sys
import time
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from dotenv import load_dotenv

load_dotenv()

from llm.gemini_client import (
    build_prompt,
    get_llm_recommendation,
    reset_client,
)

# Sample restaurant data for the full recommendation test
SAMPLE_RESTAURANTS = [
    {
        "name": "Pasta Palace",
        "location": "Koramangala",
        "cuisines": "italian, continental",
        "rate": 4.3,
        "approx_cost": 700,
        "votes": 200,
    },
    {
        "name": "Spice Hub",
        "location": "Koramangala",
        "cuisines": "north indian",
        "rate": 3.9,
        "approx_cost": 400,
        "votes": 100,
    },
]


def _separator(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ─── Test 1: API key present ───────────────────────────────────────────────────

@pytest.mark.integration
def test_api_key_is_set():
    """GEMINI_API_KEY must be set in the environment."""
    _separator("Test 1 — API key present")
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    assert api_key, "GEMINI_API_KEY not found — check your .env file"
    print(f"  ✅  GEMINI_API_KEY : {'*' * 8}{api_key[-6:]} (redacted)")
    print(f"  ✅  GEMINI_MODEL   : {model}")


# ─── Test 2: Client init ───────────────────────────────────────────────────────

@pytest.mark.integration
def test_client_initialises():
    """genai.Client builds without errors given a valid key."""
    _separator("Test 2 — Client initialisation")
    reset_client()
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)
    assert client is not None
    print("  ✅  genai.Client initialised successfully")


# ─── Test 3: Model is available ───────────────────────────────────────────────

@pytest.mark.integration
def test_model_is_available():
    """The configured model must appear in the models list."""
    _separator("Test 3 — Model availability check")
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    target = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)
    available = [m.name for m in client.models.list() if "gemini" in m.name]

    print(f"  Target model     : {target}")
    print(f"  Available models : {len(available)} found")

    # Model names in the API are returned as "models/gemini-xxx"
    # Match either exact or with prefix
    matched = [m for m in available if target in m]
    assert matched, (
        f"Model '{target}' not found in available models.\n"
        f"Available: {available}"
    )
    print(f"  ✅  Matched: {matched[0]}")


# ─── Test 4: Minimal ping ─────────────────────────────────────────────────────

@pytest.mark.integration
def test_minimal_ping():
    """Send a simple 1-sentence prompt and verify a non-empty response."""
    _separator("Test 4 — Minimal ping (1-sentence prompt)")
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)

    # Retry up to 3 times with backoff for quota errors
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model,
                contents="Say exactly: 'Gemini connection successful!' and nothing else.",
                config=types.GenerateContentConfig(max_output_tokens=32),
            )
            text = response.text.strip()
            assert text, "Gemini returned empty response"
            print(f"  ✅  Model         : {model}")
            print(f"  ✅  Response      : {text!r}")
            return
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < 2:
                wait = 15 * (attempt + 1)
                print(f"  ⏳  Rate limited (attempt {attempt+1}/3) — waiting {wait}s...")
                time.sleep(wait)
            else:
                raise


# ─── Test 5: Full recommendation prompt ───────────────────────────────────────

@pytest.mark.integration
def test_full_recommendation():
    """
    Send a complete restaurant recommendation prompt and verify:
    - Response is a non-empty string
    - It contains at least one restaurant name from the sample data
    - It is longer than 50 characters
    """
    _separator("Test 5 — Full recommendation prompt")
    reset_client()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    print(f"  Using model  : {model}")
    print(f"  Restaurants  : {[r['name'] for r in SAMPLE_RESTAURANTS]}")

    # Retry with backoff for transient quota errors
    for attempt in range(3):
        try:
            result = get_llm_recommendation(
                place="Koramangala",
                cuisine="Italian",
                max_price=800,
                min_rating=3.5,
                restaurants=SAMPLE_RESTAURANTS,
            )

            assert isinstance(result, str), "Result should be a string"
            assert len(result) > 50, f"Response too short ({len(result)} chars): {result!r}"

            print(f"\n  ✅  Response received ({len(result)} chars):")
            print(f"  {'─' * 50}")
            # Print first 500 chars nicely
            for line in result[:500].split("\n"):
                print(f"  {line}")
            if len(result) > 500:
                print(f"  ... [{len(result) - 500} more chars]")
            print(f"  {'─' * 50}")
            return

        except Exception as e:
            err = str(e)
            if "429" in err and attempt < 2:
                wait = 20 * (attempt + 1)
                print(f"  ⏳  Rate limited (attempt {attempt+1}/3) — waiting {wait}s...")
                time.sleep(wait)
                reset_client()  # Clear singleton so retries create a fresh client
            else:
                raise


# ─── Run as standalone script ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🚀 Phase 3 Integration Test — Gemini Connection")
    print("=" * 60)
    tests = [
        test_api_key_is_set,
        test_client_initialises,
        test_model_is_available,
        test_minimal_ping,
        test_full_recommendation,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:
            print(f"\n  ❌  FAILED: {exc}")
            failed += 1
    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}\n")
    sys.exit(0 if failed == 0 else 1)
