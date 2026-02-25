# streamlit_app.py
# AI Restaurant Recommendation Service — Streamlit UI
# Runs directly on Streamlit Cloud — no FastAPI server needed.

import os
import sys
from pathlib import Path

import streamlit as st

# ── Path setup ───────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# ── Inject secrets into env ──────────────────────────────────────────────────
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
if "GEMINI_MODEL" in st.secrets:
    os.environ["GEMINI_MODEL"] = st.secrets["GEMINI_MODEL"]

# ── Backend imports ──────────────────────────────────────────────────────────
from data.loader import load_dataset_once, get_dataframe
from engine.recommender import get_recommendations
from models.schemas import ErrorResponse

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
# CSS — Pixel-perfect match to the React screenshot
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Global ─────────────────────────────────── */
html, body, .stApp {
    background: radial-gradient(ellipse at 50% 0%,
        #3b0909 0%, #1f0404 35%, #0f0f0f 70%) !important;
    font-family: 'Inter', sans-serif !important;
    min-height: 100vh;
}
.block-container {
    max-width: 580px !important;
    padding: 3rem 1rem 4rem !important;
}
/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Hero text ───────────────────────────────── */
.hero-wrap { text-align: center; margin-bottom: 2.2rem; }
.hero-title {
    font-size: 2.4rem; font-weight: 800;
    color: #fff; letter-spacing: -0.02em;
    margin: 0; line-height: 1.15;
}
.hero-title .red {
    color: #e23744;
}
.hero-sub {
    color: #6b7280; font-size: 0.95rem;
    margin-top: 0.45rem; line-height: 1.6;
}
.hero-sub .accent { color: #e23744; font-weight: 600; }
.hero-sub .white  { color: #d1d5db; font-weight: 600; }

/* ── Form card — target Streamlit's container border wrapper ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1c1c1e !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 20px !important;
    padding: 1.2rem 1.4rem !important;
    margin-bottom: 1.5rem !important;
}

/* ── Hide all Streamlit labels (we embed icons in placeholders) */
.stSelectbox label,
.stNumberInput label,
.stSlider label,
[data-testid="stWidgetLabel"] {
    display: none !important;
}

/* ── Selectbox ───────────────────────────────── */
.stSelectbox > div > div {
    background-color: #2a2a2e !important;
    border: 1px solid #3a3a3e !important;
    border-radius: 12px !important;
    color: #f4f4f5 !important;
    font-size: 0.95rem !important;
    min-height: 52px !important;
    padding: 0 1rem !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
}
.stSelectbox > div > div:hover {
    border-color: #e23744 !important;
}
.stSelectbox > div > div > div { color: #f4f4f5 !important; }
.stSelectbox svg { color: #6b7280 !important; }

/* ── Number input ────────────────────────────── */
.stNumberInput > div > div {
    background-color: #2a2a2e !important;
    border: 1px solid #3a3a3e !important;
    border-radius: 12px !important;
    position: relative !important;
}
.stNumberInput > div > div::before {
    content: "₹";
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: #9ca3af;
    font-size: 1rem;
    pointer-events: none;
    z-index: 1;
}
.stNumberInput input {
    background-color: #2a2a2e !important;
    color: #f4f4f5 !important;
    font-size: 0.95rem !important;
    border: none !important;
    min-height: 52px !important;
    padding-left: 2rem !important;
}
.stNumberInput input::placeholder { color: #6b7280 !important; }
.stNumberInput input:focus { box-shadow: none !important; }
/* Hide spinner arrows */
.stNumberInput button { display: none !important; }


/* ── Slider ──────────────────────────────────── */
.stSlider { padding: 0.2rem 0 !important; }
.stSlider > div > div > div > div {
    background: #e23744 !important;
}
.stSlider [role="slider"] {
    background: #e23744 !important;
    border: 2px solid #fff !important;
    width: 18px !important; height: 18px !important;
}
.stSlider [data-testid="stTickBar"] { display: none !important; }
.stSlider > div > div > div { background: #3a3a3e !important; }
.slider-label {
    color: #9ca3af; font-size: 0.82rem; margin-bottom: 0.15rem;
}
.slider-val {
    color: #f4f4f5; font-weight: 600; font-size: 0.95rem;
    margin-bottom: 0.3rem;
}

/* ── Button ──────────────────────────────────── */
.stButton { margin-top: 0.4rem; }
.stButton > button {
    background: linear-gradient(90deg, #dc2626 0%, #e23744 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    width: 100% !important;
    height: 52px !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 20px rgba(226, 55, 68, 0.35) !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    box-shadow: 0 6px 28px rgba(226,55,68,0.5) !important;
}
.stButton > button:disabled { opacity: 0.45 !important; }

/* ── Gemini review box ───────────────────────── */
.gemini-box {
    background: linear-gradient(135deg, #1c0a0a 0%, #280e0e 100%);
    border: 1px solid #4a1414;
    border-radius: 18px;
    padding: 1.25rem 1.4rem;
    margin: 1.4rem 0;
}
.gemini-header {
    display: flex; align-items: center; gap: 0.6rem;
    margin-bottom: 0.75rem;
}
.gemini-header-text {
    color: #ef4444; font-weight: 700;
    font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em;
}
.gemini-badge {
    background: rgba(226,55,68,0.15); border: 1px solid rgba(226,55,68,0.3);
    color: #ef4444; font-size: 0.7rem; font-weight: 600;
    padding: 2px 8px; border-radius: 20px; text-transform: uppercase;
    letter-spacing: 0.05em;
}
.gemini-text { color: #d1d5db; line-height: 1.75; font-size: 0.93rem; }
.gemini-text p { margin: 0 0 0.5rem; }

/* ── Restaurant cards ────────────────────────── */
.rest-card {
    background: #1c1c1e;
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 1.1rem 1.2rem;
    margin-bottom: 0.85rem;
    transition: border-color 0.2s, transform 0.15s;
}
.rest-card:hover {
    border-color: #e23744;
    transform: translateY(-2px);
}
.rest-rank { color: #e23744; font-size: 0.7rem; font-weight: 700;
             text-transform: uppercase; letter-spacing: 0.1em; }
.rest-name { color: #ffffff; font-weight: 700; font-size: 1.05rem;
             margin: 0.1rem 0 0; line-height: 1.3; }
.rest-meta { color: #9ca3af; font-size: 0.85rem; margin: 0.2rem 0; }
.rest-footer { display: flex; justify-content: space-between;
               margin-top: 0.65rem; padding-top: 0.65rem;
               border-top: 1px solid #2a2a2a; }
.rest-price { color: #d4d4d8; font-size: 0.88rem; font-weight: 500; }
.rest-votes { color: #6b7280; font-size: 0.8rem; }

/* Rating badges */
.badge-hi { background:#16a34a; color:#fff; padding:3px 10px;
             border-radius:7px; font-weight:700; font-size:0.84rem; }
.badge-md  { background:#ca8a04; color:#fff; padding:3px 10px;
             border-radius:7px; font-weight:700; font-size:0.84rem; }
.badge-lo  { background:#dc2626; color:#fff; padding:3px 10px;
             border-radius:7px; font-weight:700; font-size:0.84rem; }

/* ── Banners ─────────────────────────────────── */
.warn-box {
    background: #1c1500; border: 1px solid #713f12;
    border-radius: 14px; padding: 1rem 1.2rem; color: #fbbf24;
    margin: 1rem 0; display: flex; gap: 0.75rem; align-items: flex-start;
}
.err-box {
    background: #1c0000; border: 1px solid #7f1d1d;
    border-radius: 14px; padding: 1rem 1.2rem; color: #fca5a5;
    margin: 1rem 0; display: flex; gap: 0.75rem; align-items: flex-start;
}
.banner-icon { font-size: 1.4rem; flex-shrink: 0; line-height: 1; }
.banner-title { font-weight: 700; font-size: 0.95rem; margin-bottom: 0.2rem; }
.banner-sub { font-size: 0.82rem; opacity: 0.8; line-height: 1.5; }

/* ── Results header ──────────────────────────── */
.results-header {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 0.75rem;
    margin-top: 0;
}
.results-title { color: #fff; font-weight: 600; font-size: 1.05rem; }
.results-badge {
    background: #2a2a2a; color: #6b7280;
    font-size: 0.75rem; padding: 3px 10px; border-radius: 20px;
}

/* ── Info banner ─────────────────────────────── */
.info-box {
    background: #0c1a2e; border: 1px solid #1e3a5f;
    border-radius: 12px; padding: 0.75rem 1rem; color: #60a5fa;
    font-size: 0.88rem; margin: 0.75rem 0;
}

/* ── Footer ──────────────────────────────────── */
.footer-text {
    text-align: center; color: #374151;
    font-size: 0.75rem; margin-top: 2rem;
}
hr { border-color: #1f1f1f !important; }

/* ── Spinner ─────────────────────────────────── */
.stSpinner > div { border-top-color: #e23744 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Load dataset
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="⏳ Loading restaurant data…")
def load_data():
    return load_dataset_once()


@st.cache_data(show_spinner=False)
def get_places():
    df = get_dataframe()
    return sorted(df["location"].dropna().unique().tolist())


load_data()
places = get_places()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def rating_badge(rate):
    if rate is None:
        return ""
    cls = "badge-hi" if rate >= 4.0 else ("badge-md" if rate >= 3.0 else "badge-lo")
    return f'<span class="{cls}">★ {rate:.1f}</span>'


# ─────────────────────────────────────────────────────────────────────────────
# Hero
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <h1 class="hero-title">🍽️ AI Restaurant <span class="red">Finder</span></h1>
    <p class="hero-sub">
        Powered by <span class="accent">Gemini AI</span>
        × <span class="white">Zomato Data</span> — discover<br>your next favourite spot.
    </p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Form card (rendered using HTML wrapper + Streamlit widgets inside)
# ─────────────────────────────────────────────────────────────────────────────
CUISINE_OPTIONS = [
    "", "North Indian", "South Indian", "Chinese", "Italian", "Continental",
    "Fast Food", "Biryani", "Cafe", "Desserts", "Pizza", "Seafood",
    "Mughlai", "Japanese", "Mexican", "Thai", "American", "Bakery",
]

with st.container(border=True):
    place = st.selectbox(
        "Location",
        options=[""] + places,
        index=0,
        format_func=lambda x: "📍  Select a location…" if x == "" else f"📍  {x}",
        label_visibility="collapsed",
    )
    place = place if place else None

    cuisine_raw = st.selectbox(
        "Cuisine",
        options=CUISINE_OPTIONS,
        format_func=lambda x: "🍽️  Any cuisine" if x == "" else f"🍽️  {x}",
        label_visibility="collapsed",
    )
    cuisine = cuisine_raw if cuisine_raw else None

    col3, col4 = st.columns(2)
    with col3:
        max_price_val = st.number_input(
            "Budget",
            min_value=0, value=0, step=100,
            placeholder="₹  Max budget",
            label_visibility="collapsed",
        )
        max_price = int(max_price_val) if max_price_val > 0 else None

    with col4:
        st.markdown(
            '<div class="slider-label">⭐ Min Rating</div>',
            unsafe_allow_html=True,
        )
        min_rating_val = st.slider(
            "Rating", min_value=0.0, max_value=5.0, value=0.0, step=0.1,
            format="%.1f", label_visibility="collapsed",
        )
        min_rating = float(min_rating_val) if min_rating_val > 0.0 else None
        if min_rating_val > 0.0:
            st.markdown(
                f'<div class="slider-val">⭐ {min_rating_val:.1f} / 5.0</div>',
                unsafe_allow_html=True,
            )

    search_clicked = st.button(
        "🔍  Find Restaurants",
        disabled=(place is None),
        use_container_width=True,
    )


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
                f'<div class="err-box">'
                f'<div class="banner-icon">⚠️</div>'
                f'<div><div class="banner-title">Something went wrong</div>'
                f'<div class="banner-sub">{e}</div></div></div>',
                unsafe_allow_html=True,
            )

    if isinstance(result, ErrorResponse):
        st.markdown(
            '<div class="warn-box">'
            '<div class="banner-icon">🔍</div>'
            '<div><div class="banner-title">No restaurants found</div>'
            '<div class="banner-sub">Try broadening your search — relax the price limit, '
            'lower the minimum rating, or pick a different location.</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

    elif result is not None:
        # ── Gemini review ──────────────────────────────────────────────────
        if result.gemini_review:
            paras = "".join(
                f"<p>{p}</p>"
                for p in result.gemini_review.split("\n")
                if p.strip()
            )
            st.markdown(f"""
            <div class="gemini-box">
                <div class="gemini-header">
                    <span style="font-size:1.3rem">🤖</span>
                    <span class="gemini-header-text">Gemini AI · Expert Food Critic</span>
                    <span class="gemini-badge">AI-generated</span>
                </div>
                <div class="gemini-text">{paras}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="info-box">💡 Gemini review unavailable (quota). '
                'Restaurant data shown below.</div>',
                unsafe_allow_html=True,
            )

        # ── Restaurant cards ───────────────────────────────────────────────
        st.markdown(
            f'<div class="results-header">'
            f'<span class="results-title">Top {result.total} Matches</span>'
            f'<span class="results-badge">Sorted by rating ↓</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for i, r in enumerate(result.restaurants):
            cuisines_display = r.cuisines.title() if r.cuisines else "—"
            cost_str = f"₹{r.approx_cost:,} for two" if r.approx_cost else "Price N/A"
            votes_str = f"{r.votes:,} votes" if r.votes else ""
            badge = rating_badge(r.rate)

            st.markdown(f"""
            <div class="rest-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem">
                    <div style="flex:1;min-width:0">
                        <div class="rest-rank">#{i+1}</div>
                        <div class="rest-name">{r.name}</div>
                    </div>
                    {badge}
                </div>
                <div class="rest-meta">📍 {r.location}</div>
                <div class="rest-meta">🍽️ {cuisines_display}</div>
                <div class="rest-footer">
                    <span class="rest-price">💰 {cost_str}</span>
                    <span class="rest-votes">{votes_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="footer-text">AI Restaurant Finder · '
    'Powered by Google Gemini &amp; Zomato Open Data</p>',
    unsafe_allow_html=True,
)
