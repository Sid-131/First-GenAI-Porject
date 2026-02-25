# backend/llm/groq_client.py
# Phase 3 — Groq LLM API integration

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        _client = Groq(api_key=api_key)
    return _client


def get_llm_recommendation(
    place: str,
    cuisine: str | None,
    max_price: int | None,
    min_rating: float | None,
    restaurants: list[dict],
) -> str:
    """
    Call Groq API with user preferences + filtered restaurant list.
    Returns a natural-language recommendation string.
    """
    # TODO (Phase 3 Implementation):
    # 1. Build a structured prompt (system + user message)
    # 2. Call groq_client.chat.completions.create(...)
    # 3. Return response content

    model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    restaurant_list_str = json.dumps(restaurants[:10], indent=2)

    user_message = (
        f"I'm looking for {cuisine or 'any'} restaurants in {place}. "
        f"My budget is {f'up to {max_price} INR' if max_price else 'flexible'}. "
        f"Minimum rating: {min_rating or 'any'}.\n\n"
        f"Here are matching restaurants:\n{restaurant_list_str}\n\n"
        "Please provide a friendly recommendation with brief reasoning for each restaurant."
    )

    client = _get_client()
    # Stub return — replace with actual API call in Phase 3
    print(f"[groq_client] Would call model={model} (stub)")
    return "LLM integration pending (Phase 3 implementation)."
