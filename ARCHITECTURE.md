# 🍽️ AI Restaurant Recommendation Service — Architecture

> **Project**: AI-powered restaurant recommendation engine using LLM reasoning over real-world Zomato data.
> **Date**: February 2026

---

## 📋 Overview

This service allows users to discover restaurants that match their preferences (price, location, rating, cuisine) by combining structured data filtering with LLM-powered natural language reasoning via Groq. The architecture is divided into **5 distinct phases**, from raw data ingestion through to the user-facing UI.

---

## 🧰 Tech Stack

| Layer              | Technology                                                  |
|--------------------|-------------------------------------------------------------|
| **Frontend**       | React.js, Tailwind CSS, Axios                               |
| **Backend**        | Python 3.11+, FastAPI, Uvicorn                              |
| **LLM Provider**   | Groq API (e.g., `llama3-8b-8192` or `mixtral-8x7b-32768`)  |
| **Data Source**    | Hugging Face — `ManikaSaini/zomato-restaurant-recommendation` |
| **Data Processing**| Pandas, datasets (HuggingFace)                             |
| **API Layer**      | REST (JSON), CORS-enabled FastAPI                           |
| **Environment**    | Python `venv`, `.env` for secrets                           |

---

## 🗂️ Project Folder Structure

```
First-GenAI-Porject/
│
├── ARCHITECTURE.md          ← This document
│
├── backend/
│   ├── main.py              ← FastAPI app entry point
│   ├── requirements.txt     ← Python dependencies
│   ├── .env.example         ← API key template
│   │
│   ├── data/
│   │   ├── loader.py        ← Phase 1: HuggingFace dataset loader
│   │   └── preprocessor.py  ← Phase 1: Data cleaning & normalization
│   │
│   ├── api/
│   │   └── routes.py        ← Phase 2: User input API endpoints
│   │
│   ├── llm/
│   │   └── groq_client.py   ← Phase 3: Groq API integration
│   │
│   ├── engine/
│   │   └── recommender.py   ← Phase 4: Filtering + LLM reasoning engine
│   │
│   └── models/
│       └── schemas.py       ← Pydantic request/response schemas
│
└── frontend/
    ├── package.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    │
    └── src/
        ├── main.jsx             ← React app entry
        ├── App.jsx              ← Root component
        │
        ├── components/
        │   ├── SearchForm.jsx   ← Phase 5: User input form (price, place, rating, cuisine)
        │   ├── RestaurantCard.jsx ← Phase 5: Single restaurant result card
        │   └── ResultsList.jsx  ← Phase 5: List of recommendation cards
        │
        ├── services/
        │   └── api.js           ← Axios calls to FastAPI backend
        │
        └── styles/
            └── index.css        ← Tailwind base styles
```

---

## 🔄 5-Phase Architecture

---

### Phase 1 — Data Input, Preprocessing & Cleaning

**Goal**: Load the raw Zomato dataset from Hugging Face, clean it, and make it available as a structured in-memory DataFrame for the recommendation engine.

**Files**: `backend/data/loader.py`, `backend/data/preprocessor.py`

**Steps**:
1. Use the HuggingFace `datasets` library to stream/download `ManikaSaini/zomato-restaurant-recommendation`.
2. Convert dataset to a Pandas DataFrame.
3. Normalize column names to lowercase snake_case.
4. Handle missing values: drop rows with nulls in critical fields (`name`, `cuisines`, `location`, `rate`, `approx_cost`).
5. Parse and clean the `rate` column (e.g., remove `"/5"`, convert `"NEW"` / `"-"` to `NaN`).
6. Parse `approx_cost` column — remove commas and cast to integer.
7. Expose the cleaned DataFrame as a module-level singleton (loaded once at startup).

**Key Data Fields**:
| Column         | Description                        |
|----------------|------------------------------------|
| `name`         | Restaurant name                    |
| `location`     | City/area of restaurant            |
| `cuisines`     | Comma-separated cuisine types      |
| `rate`         | Numeric rating out of 5            |
| `approx_cost`  | Approximate cost for two (INR)     |
| `rest_type`    | Restaurant category                |
| `votes`        | Number of user votes               |

---

### Phase 2 — User Input API (Price, Place, Rating, Cuisine)

**Goal**: Expose a clean REST endpoint that accepts user preferences and returns LLM-enhanced restaurant recommendations.

**Files**: `backend/api/routes.py`, `backend/models/schemas.py`, `backend/main.py`

**Endpoint**:
```
POST /api/recommend
```

**Request Body (JSON)**:
```json
{
  "place":    "Koramangala",
  "cuisine":  "Italian",
  "max_price": 800,
  "min_rating": 4.0
}
```

**Response Body (JSON)**:
```json
{
  "recommendations": [
    {
      "name": "Trattoria",
      "location": "Koramangala",
      "cuisines": "Italian, Continental",
      "rate": 4.3,
      "approx_cost": 700,
      "llm_summary": "Great cozy spot for Italian food, known for wood-fired pizzas..."
    }
  ],
  "llm_reasoning": "Here are the top restaurants matching your query..."
}
```

**Validation** (via Pydantic `schemas.py`):
- `place`: non-empty string
- `cuisine`: optional string (if omitted, no cuisine filter applied)
- `max_price`: optional positive integer
- `min_rating`: optional float between 0.0–5.0

---

### Phase 3 — LLM Integration (Groq)

**Goal**: Integrate the Groq API to provide natural language summaries and reasoning for restaurant recommendations.

**Files**: `backend/llm/groq_client.py`

**Design**:
- Load Groq API key from environment variable `GROQ_API_KEY` (via `.env`).
- Use the official `groq` Python SDK.
- Provide a function `get_llm_recommendation(user_query: str, restaurants: list[dict]) -> str` that:
  1. Formats a structured prompt with the user's preferences and the filtered restaurant list.
  2. Calls the Groq chat completion endpoint.
  3. Returns the LLM's natural language response.

**Prompt Template**:
```
System: You are a helpful restaurant recommendation assistant.
User: I'm looking for {cuisine} restaurants in {place} with a budget of {max_price} INR 
      and a minimum rating of {min_rating}.

Here are some matching restaurants from our database:
{restaurant_list_json}

Please provide a friendly, concise recommendation with reasoning for each restaurant.
```

**Model**: `llama3-8b-8192` (default; configurable via env var `GROQ_MODEL`)

---

### Phase 4 — Recommendation Engine (Data Filtering + LLM Reasoning)

**Goal**: Combine structured Pandas-based filtering with LLM reasoning to produce the final ranked recommendation list.

**Files**: `backend/engine/recommender.py`

**Algorithm**:
1. **Filter Step** (Pandas):
   - Filter by `location` containing the requested `place` (case-insensitive).
   - Filter by `cuisines` containing the requested `cuisine` (if provided).
   - Filter by `approx_cost <= max_price` (if provided).
   - Filter by `rate >= min_rating` (if provided).
   - Sort by `rate` descending, then `votes` descending.
   - Take top **10** candidates.

2. **LLM Reasoning Step** (Groq):
   - Pass the top 10 filtered restaurants + user query to `groq_client.get_llm_recommendation()`.
   - LLM generates a ranked, human-readable explanation.

3. **Response Assembly**:
   - Return both the structured candidate list (for card rendering) and the LLM's reasoning text.

**Fallback**: If the filter returns 0 results, pass a broader set (top 20 by rating from the full dataset) to the LLM with a note that exact filters weren't met.

---

### Phase 5 — Frontend UI Display

**Goal**: Build a clean, responsive React + Tailwind UI that collects user preferences and displays LLM-enhanced restaurant recommendations.

**Files**: `frontend/src/` (all components, services, styles)

**Pages / Components**:

| Component          | Purpose                                                   |
|--------------------|-----------------------------------------------------------|
| `App.jsx`          | Root layout, state management, API call orchestration     |
| `SearchForm.jsx`   | Input fields: Place, Cuisine, Max Price, Min Rating       |
| `ResultsList.jsx`  | Renders the grid of `RestaurantCard` components           |
| `RestaurantCard.jsx` | Displays name, location, rating, cost, LLM summary     |

**User Flow**:
```
[User fills form] → [Submit] → [POST /api/recommend] → [Loading state]
       → [Results render as cards] → [LLM reasoning shown at top]
```

**UI Features**:
- Dark/vibrant themed design with Tailwind utility classes.
- Loading spinner during API call.
- Error message display on API failure.
- Responsive grid layout (1 col mobile, 2 col tablet, 3 col desktop).
- Each card shows: name, location, cuisines, rating badge, cost, LLM-generated summary.

---

## 🔐 Environment Variables

Create `backend/.env` from `backend/.env.example`:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama3-8b-8192
HF_DATASET=ManikaSaini/zomato-restaurant-recommendation
```

---

## 🚀 High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  SearchForm → Axios POST /api/recommend → ResultsList + Cards   │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP POST (JSON)
┌──────────────────────▼──────────────────────────────────────────┐
│                     BACKEND (FastAPI)                           │
│                                                                 │
│  routes.py → recommender.py ──► Pandas Filter (Phase 4)        │
│                            │                                    │
│                            └──► groq_client.py → Groq API      │
│                                       (Phase 3)                 │
│                                                                 │
│  data/loader.py + preprocessor.py  (Phase 1, runs at startup)  │
└─────────────────────────────────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  Groq LLM API   │
              │ (llama3-8b-8192)│
              └─────────────────┘
                       │
              ┌────────▼──────────────────┐
              │ HuggingFace Dataset       │
              │ ManikaSaini/zomato-...    │
              └───────────────────────────┘
```

---

## 📌 Implementation Phases Summary

| Phase | Name                                | Status  |
|-------|-------------------------------------|---------|
| 1     | Data Input, Preprocessing & Cleaning | 🟡 Pending |
| 2     | User Input API                      | 🟡 Pending |
| 3     | LLM Integration (Groq)              | 🟡 Pending |
| 4     | Recommendation Engine               | 🟡 Pending |
| 5     | Frontend UI Display                 | 🟡 Pending |

---

*Architecture designed for the `First-GenAI-Porject` workspace. Implementation begins in the next phase.*
