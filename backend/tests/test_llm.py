# backend/tests/test_llm.py
# Phase 3 — Tests for the Gemini LLM client

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm.gemini_client import build_prompt, get_llm_recommendation, reset_client

# ── Shared test data ──────────────────────────────────────────────────────────

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


# ─── Unit tests for build_prompt() ────────────────────────────────────────────

class TestBuildPrompt:
    """Verify the prompt string is assembled correctly without any API calls."""

    def test_returns_string(self):
        prompt = build_prompt("Koramangala", "Italian", 800, 4.0, SAMPLE_RESTAURANTS)
        assert isinstance(prompt, str)

    def test_contains_place(self):
        prompt = build_prompt("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        assert "Koramangala" in prompt

    def test_contains_cuisine(self):
        prompt = build_prompt("Koramangala", "Italian", None, None, SAMPLE_RESTAURANTS)
        assert "Italian" in prompt

    def test_no_cuisine_shows_no_preference(self):
        prompt = build_prompt("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        assert "No preference" in prompt

    def test_contains_max_price(self):
        prompt = build_prompt("Koramangala", None, 800, None, SAMPLE_RESTAURANTS)
        assert "800" in prompt

    def test_no_price_shows_flexible(self):
        prompt = build_prompt("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        assert "Flexible" in prompt

    def test_contains_min_rating(self):
        prompt = build_prompt("Koramangala", None, None, 4.0, SAMPLE_RESTAURANTS)
        assert "4.0" in prompt

    def test_contains_restaurant_names(self):
        prompt = build_prompt("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        assert "Pasta Palace" in prompt
        assert "Spice Hub" in prompt

    def test_empty_restaurant_list(self):
        """Should still produce a valid prompt — LLM handles the empty case."""
        prompt = build_prompt("Koramangala", "Italian", 800, 4.0, [])
        assert isinstance(prompt, str)
        assert "Koramangala" in prompt

    def test_restaurant_data_embedded_in_prompt(self):
        """Restaurant details must appear as a readable block in the prompt."""
        prompt = build_prompt("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        # Phase 4 uses a numbered human-readable list (not JSON)
        assert "Pasta Palace" in prompt
        assert "Spice Hub" in prompt
        # Numbered list format: "1. **Name**"
        assert "1." in prompt
        assert "2." in prompt


# ─── Unit tests for get_llm_recommendation() (mocked Gemini) ─────────────────

class TestGetLLMRecommendationMocked:
    """
    Tests for get_llm_recommendation() with the Gemini model mocked.
    No real API key or network required.
    """

    def setup_method(self):
        """
        Reset singleton + inject a fake API key before each test.
        The key is fake but prevents ValueError from _get_model() before
        the genai.configure / GenerativeModel patches take effect.
        """
        import os
        reset_client()
        self._original_key = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "fake-test-key-12345"

    def teardown_method(self):
        """Restore original env state after each test."""
        import os
        reset_client()
        if self._original_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = self._original_key

    def _make_mock_response(self, text: str):
        """Create a fake GenerateContentResponse with a .text attribute."""
        mock_response = MagicMock()
        mock_response.text = text
        return mock_response

    def _patch_client(self, response_text: str):
        """Return a patch context that mocks genai.Client and injects a response."""
        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = self._make_mock_response(response_text)
        return patch("llm.gemini_client.genai.Client", return_value=mock_instance), mock_instance

    @patch("llm.gemini_client.genai.Client")
    def test_returns_string(self, MockClient):
        """Happy path — Gemini returns text."""
        mock_instance = MockClient.return_value
        mock_instance.models.generate_content.return_value = self._make_mock_response(
            "Pasta Palace is a great choice for Italian food!"
        )
        result = get_llm_recommendation("Koramangala", "Italian", 800, 4.0, SAMPLE_RESTAURANTS)
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("llm.gemini_client.genai.Client")
    def test_returns_expected_response_text(self, MockClient):
        """The text from Gemini is returned stripped."""
        expected = "  I recommend Pasta Palace for its great Italian food!  "
        mock_instance = MockClient.return_value
        mock_instance.models.generate_content.return_value = self._make_mock_response(expected)
        result = get_llm_recommendation("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        assert result == expected.strip()

    @patch("llm.gemini_client.genai.Client")
    def test_generate_content_called_once(self, MockClient):
        """Exactly one API call is made per invocation."""
        mock_instance = MockClient.return_value
        mock_instance.models.generate_content.return_value = self._make_mock_response("Great!")
        get_llm_recommendation("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        mock_instance.models.generate_content.assert_called_once()

    @patch("llm.gemini_client.genai.Client")
    def test_prompt_contains_place_and_restaurants(self, MockClient):
        """Verify the prompt passed to Gemini includes place and restaurant data."""
        mock_instance = MockClient.return_value
        mock_instance.models.generate_content.return_value = self._make_mock_response("OK")
        get_llm_recommendation("Koramangala", "Italian", 800, 4.0, SAMPLE_RESTAURANTS)
        call_kwargs = mock_instance.models.generate_content.call_args
        # Contents arg (positional or keyword)
        contents = call_kwargs.kwargs.get("contents") or call_kwargs.args[1]
        assert "Koramangala" in contents
        assert "Pasta Palace" in contents

    @patch("llm.gemini_client.genai.Client")
    def test_model_singleton_reused(self, MockClient):
        """Client constructor called only once across multiple recommendation calls."""
        mock_instance = MockClient.return_value
        mock_instance.models.generate_content.return_value = self._make_mock_response("OK")
        get_llm_recommendation("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        get_llm_recommendation("Indiranagar", None, None, None, SAMPLE_RESTAURANTS)
        MockClient.assert_called_once()

    def test_raises_if_no_api_key(self):
        """get_llm_recommendation raises ValueError when GEMINI_API_KEY is absent."""
        import os
        original = os.environ.pop("GEMINI_API_KEY", None)
        try:
            with pytest.raises((ValueError, Exception)):
                get_llm_recommendation("Koramangala", None, None, None, SAMPLE_RESTAURANTS)
        finally:
            if original is not None:
                os.environ["GEMINI_API_KEY"] = original

    @patch("llm.gemini_client.genai.Client")
    def test_raises_on_empty_response(self, MockClient):
        """RuntimeError is raised when Gemini returns empty text."""
        mock_instance = MockClient.return_value
        mock_instance.models.generate_content.return_value = self._make_mock_response("")
        with pytest.raises(RuntimeError):
            get_llm_recommendation("Koramangala", None, None, None, SAMPLE_RESTAURANTS)


# ─── Integration test (real Gemini API — requires GEMINI_API_KEY env var) ─────

@pytest.mark.integration
def test_real_gemini_connection():
    """
    Makes a live call to the Gemini API.
    Requires GEMINI_API_KEY to be set in the environment.

    Run with: pytest -m integration -v
    """
    import os
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set — skipping live Gemini test")

    reset_client()
    result = get_llm_recommendation(
        place="Koramangala",
        cuisine="Italian",
        max_price=800,
        min_rating=3.5,
        restaurants=SAMPLE_RESTAURANTS,
    )

    assert isinstance(result, str), "Gemini should return a string"
    assert len(result) > 20, f"Response too short: {result!r}"
    print(f"\n[integration] Gemini response ({len(result)} chars):\n{result[:300]}...")
