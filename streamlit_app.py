# streamlit_app.py
# AI Restaurant Recommendation Service — Streamlit UI
# Runs directly on Streamlit Cloud — no FastAPI server needed.
# The backend Python modules (engine, llm, data) are imported directly.

import os
import sys
from pathlib import Path

import streamlit as st

# ── Path setup: let Python find backend modules ─────────────────────────────
BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# ── Inject secrets into env before any backend imports ──────────────────────
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
if "GEMINI_MODEL" in st.secrets:
    os.environ["GEMINI_MODEL"] = st.secrets["GEMINI_MODEL"]

# ── Backend imports (after path + env setup) ────────────────────────────────
from data.loader import load_dataset_once, get_dataframe          # noqa: E402
from engine.recommender import get_recommendations                 # noqa: E402
from models.schemas import ErrorResponse                           # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Restaurant Finder",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — Zomato-inspired dark theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark background */
    .stApp { background-color: #0f0f0f; }
    .block-container { padding-top: 2rem; max-width: 860px; }

    /* Hero title */
    .hero-title {
        font-size: 2.6rem; font-weight: 800;
        background: linear-gradient(90deg, #e23744, #ff6b6b);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .hero-sub {
        color: #9ca3af; font-size: 1rem; margin-top: 0.25rem;
    }

    /* Gemini review box */
    .gemini-box {
        background: linear-gradient(135deg, #1c0a0a, #2a0f0f);
        border: 1px solid #5a1a1a;
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin: 1.2rem 0;
    }
    .gemini-header {
        color: #ef4444; font-weight: 700;
        font-size: 0.85rem; text-transform: uppercase;
        letter-spacing: 0.1em; margin-bottom: 0.6rem;
    }
    .gemini-text { color: #d1d5db; line-height: 1.7; font-size: 0.95rem; }

    /* Restaurant cards */
    .rest-card {
        background: #18181b;
        border: 1px solid #27272a;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s;
    }
    .rest-card:hover { border-color: #e23744; }
    .rest-name { color: #ffffff; font-weight: 700; font-size: 1.05rem; }
    .rest-meta { color: #9ca3af; font-size: 0.85rem; margin: 0.15rem 0; }

    /* Rating badge */
    .badge-high { background:#16a34a; color:#fff; padding:2px 9px;
                  border-radius:6px; font-weight:700; font-size:0.85rem; }
    .badge-mid  { background:#ca8a04; color:#fff; padding:2px 9px;
                  border-radius:6px; font-weight:700; font-size:0.85rem; }
    .badge-low  { background:#dc2626; color:#fff; padding:2px 9px;
                  border-radius:6px; font-weight:700; font-size:0.85rem; }

    /* Warning / error banners */
    .warn-box {
        background: #1c1200; border: 1px solid #78350f;
        border-radius: 12px; padding: 1rem 1.2rem; color: #fbbf24;
        margin: 1rem 0;
    }
    .err-box {
        background: #1c0000; border: 1px solid #7f1d1d;
        border-radius: 12px; padding: 1rem 1.2rem; color: #fca5a5;
        margin: 1rem 0;
    }

    /* Streamlit selectbox / number_input dark override */
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background-color: #18181b !important;
        color: #f4f4f5 !important;
        border-color: #3f3f46 !important;
        border-radius: 10px !important;
    }
    label { color: #a1a1aa !important; font-size: 0.88rem !important; }
    .stButton > button {
        background: linear-gradient(90deg, #dc2626, #e23744) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important; font-weight: 600 !important;
        padding: 0.55rem 1.5rem !important; width: 100%;
    }
    .stButton > button:hover { opacity: 0.9 !important; }
    div[data-testid="stMarkdownContainer"] p { color: #d4d4d8; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Load dataset (cached across reruns)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading restaurant data…")
def load_data():
    return load_dataset_once()


@st.cache_data(show_spinner=False)
def get_places():
    df = get_dataframe()
    return sorted(df["location"].dropna().unique().tolist())


load_data()  # Trigger on first load
places = get_places()


# ─────────────────────────────────────────────────────────────────────────────
# Helper: rating badge HTML
# ─────────────────────────────────────────────────────────────────────────────
def rating_badge(rate):
    if rate is None:
        return ""
    cls = "badge-high" if rate >= 4.0 else ("badge-mid" if rate >= 3.0 else "badge-low")
    return f'<span class="{cls}">★ {rate:.1f}</span>'


# ─────────────────────────────────────────────────────────────────────────────
# UI — Hero
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">🍽️ AI Restaurant Finder</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Powered by <b style="color:#e23744">Gemini AI</b> '
    '× <b style="color:#d4d4d8">Zomato Data</b> — discover your next favourite spot.</p>',
    unsafe_allow_html=True,
)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# UI — Search form
# ─────────────────────────────────────────────────────────────────────────────
CUISINE_OPTIONS = [
    "", "North Indian", "South Indian", "Chinese", "Italian", "Continental",
    "Fast Food", "Biryani", "Cafe", "Desserts", "Pizza", "Seafood",
    "Mughlai", "Japanese", "Mexican", "Thai", "American", "Bakery",
]

col1, col2 = st.columns(2)
with col1:
    place = st.selectbox("📍 Location", options=places, index=None,
                         placeholder="Select a location…")
with col2:
    cuisine_raw = st.selectbox("🍽️ Cuisine", options=CUISINE_OPTIONS,
                               format_func=lambda x: "Any cuisine" if x == "" else x)
    cuisine = cuisine_raw if cuisine_raw else None

col3, col4 = st.columns(2)
with col3:
    max_price = st.number_input("💰 Max Budget (₹ for two)", min_value=0, value=0, step=100)
    max_price = int(max_price) if max_price > 0 else None
with col4:
    min_rating = st.slider("⭐ Minimum Rating", min_value=0.0, max_value=5.0,
                           value=0.0, step=0.1, format="%.1f")
    min_rating = float(min_rating) if min_rating > 0.0 else None

search_clicked = st.button("🔍 Find Restaurants", disabled=(place is None))

# ─────────────────────────────────────────────────────────────────────────────
# Search & Results
# ─────────────────────────────────────────────────────────────────────────────
if search_clicked and place:
    with st.spinner("Asking Gemini for recommendations…"):
        try:
            result = get_recommendations(
                place=place,
                cuisine=cuisine,
                max_price=max_price,
                min_rating=min_rating,
            )
        except Exception as e:
            result = None
            st.markdown(
                f'<div class="err-box">⚠️ <b>Something went wrong</b><br>'
                f'<span style="font-size:0.88rem">{e}</span></div>',
                unsafe_allow_html=True,
            )

    if isinstance(result, ErrorResponse):
        st.markdown(
            '<div class="warn-box">🔍 <b>No restaurants found</b><br>'
            '<span style="font-size:0.88rem">Try broadening your search — '
            'relax the price limit, lower the minimum rating, or pick a '
            'different location.</span></div>',
            unsafe_allow_html=True,
        )

    elif result is not None:
        # ── Gemini review ──────────────────────────────────────────────────
        if result.gemini_review:
            paras = "\n".join(
                f"<p>{p}</p>"
                for p in result.gemini_review.split("\n")
                if p.strip()
            )
            st.markdown(f"""
            <div class="gemini-box">
                <div class="gemini-header">🤖 Gemini AI · Expert Food Critic</div>
                <div class="gemini-text">{paras}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("💡 Gemini review unavailable (rate limit or quota). Restaurant data shown below.")

        # ── Restaurant cards ───────────────────────────────────────────────
        st.markdown(
            f"<p style='color:#71717a;font-size:0.85rem;margin-bottom:0.5rem'>"
            f"Top {result.total} matches · sorted by rating</p>",
            unsafe_allow_html=True,
        )

        for i, r in enumerate(result.restaurants):
            cuisines_display = r.cuisines.title() if r.cuisines else "—"
            cost_str = f"₹{r.approx_cost:,} for two" if r.approx_cost else "Price N/A"
            votes_str = f"{r.votes:,} votes" if r.votes else ""
            badge = rating_badge(r.rate)

            st.markdown(f"""
            <div class="rest-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                        <span style="color:#e23744;font-size:0.72rem;font-weight:700;
                                     text-transform:uppercase;letter-spacing:0.08em">#{i+1}</span>
                        <div class="rest-name">{r.name}</div>
                    </div>
                    {badge}
                </div>
                <div class="rest-meta">📍 {r.location}</div>
                <div class="rest-meta">🍽️ {cuisines_display}</div>
                <div style="display:flex;justify-content:space-between;
                            margin-top:0.5rem;padding-top:0.5rem;
                            border-top:1px solid #27272a">
                    <span style="color:#d4d4d8;font-size:0.88rem;font-weight:500">
                        💰 {cost_str}
                    </span>
                    <span style="color:#71717a;font-size:0.8rem">{votes_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;color:#3f3f46;font-size:0.78rem'>"
    "AI Restaurant Finder · Powered by Google Gemini &amp; Zomato Open Data</p>",
    unsafe_allow_html=True,
)
