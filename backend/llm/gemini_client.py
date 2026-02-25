# backend/llm/gemini_client.py
# Phase 3 / 4 — Google Gemini integration using the google-genai SDK

import os
from typing import Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# ── Lazy singleton client ─────────────────────────────────────────────────────
_client: genai.Client | None = None
_model_name: str | None = None

# System identity: Gemini acts as an expert food critic
SYSTEM_INSTRUCTION = (
    "You are an expert food critic and restaurant guide with deep knowledge of "
    "Indian cuisine and dining culture. When given a list of restaurants and a "
    "user's preferences, write an engaging, opinionated summary of why these spots "
    "are worth visiting. Highlight each restaurant's standout quality — whether it's "
    "the cuisine, ambience, value for money, or crowd-favourite dishes. "
    "Keep your tone warm, confident, and conversational. Be concise but vivid."
)


def _get_client() -> tuple[genai.Client, str]:
    """Initialise the Gemini client once and cache it. Returns (client, model_name)."""
    global _client, _model_name
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Copy backend/.env.example → backend/.env and add your API key."
            )
        _client = genai.Client(api_key=api_key)
        _model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        print(f"[gemini_client] Initialised with model: {_model_name}")
    return _client, _model_name


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(
    place: str,
    cuisine: Optional[str],
    max_price: Optional[int],
    min_rating: Optional[float],
    restaurants: list[dict],
) -> str:
    """
    Build the expert food-critic prompt from user preferences and top-5 restaurants.

    The prompt instructs Gemini to summarise why each restaurant is a great pick,
    given the user's stated filters.
    """
    # ── User preference header ────────────────────────────────────────────────
    prefs = [
        f"📍 Location  : {place}",
        f"🍽️  Cuisine   : {cuisine or 'No preference (all cuisines welcome)'}",
        f"💰 Budget    : {'up to ₹' + str(max_price) + ' for two' if max_price else 'Flexible'}",
        f"⭐ Min rating : {min_rating if min_rating is not None else 'Any'}",
    ]

    # ── Restaurant block ──────────────────────────────────────────────────────
    lines = []
    for i, r in enumerate(restaurants, 1):
        cost_str = f"₹{r['approx_cost']} for two" if r.get("approx_cost") else "Cost N/A"
        rating_str = str(r.get("rate", "N/A"))
        votes_str = f"{r.get('votes', 0):,} votes" if r.get("votes") else ""
        lines.append(
            f"{i}. **{r['name']}** | {r.get('cuisines', '').title()} | "
            f"Rating: {rating_str}/5 ({votes_str}) | {cost_str}"
        )

    restaurant_block = "\n".join(lines)

    return (
        "A user is looking for restaurant recommendations with these preferences:\n"
        + "\n".join(prefs)
        + "\n\n"
        "Here are the top matching restaurants from the Zomato database:\n"
        + restaurant_block
        + "\n\n"
        "As an expert food critic, write a concise, engaging summary of why these "
        "restaurants are great choices for this user. For each one, mention its "
        "standout quality and why it fits their preferences. Use a numbered list "
        "matching the order above. Keep the total response under 300 words."
    )


# ── Main LLM call ─────────────────────────────────────────────────────────────

def get_llm_recommendation(
    place: str,
    cuisine: Optional[str],
    max_price: Optional[int],
    min_rating: Optional[float],
    restaurants: list[dict],
) -> str:
    """
    Call the Gemini API with the food-critic prompt and return its response text.

    Raises:
        ValueError: If GEMINI_API_KEY is not set.
        google.genai.errors.APIError: On API-level failures.
    """
    client, model = _get_client()
    prompt = build_prompt(place, cuisine, max_price, min_rating, restaurants)

    print(f"[gemini_client] Calling {model} — {len(restaurants)} restaurants, "
          f"{len(prompt)} chars...")

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.75,
            top_p=0.95,
            max_output_tokens=512,
        ),
    )

    text = response.text
    if not text:
        raise RuntimeError(f"Gemini returned an empty response: {response}")
    return text.strip()


def reset_client() -> None:
    """Reset the singleton (used in tests to inject a fresh mock)."""
    global _client, _model_name
    _client = None
    _model_name = None
