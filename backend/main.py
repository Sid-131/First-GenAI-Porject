# backend/main.py
# FastAPI application entry point — Phase 2–5

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from data.loader import load_dataset_once

app = FastAPI(
    title="AI Restaurant Recommendation API",
    description=(
        "LLM-powered restaurant recommendations using Gemini AI + Zomato data.\n\n"
        "**Phases**: Data pipeline → REST API → Gemini LLM → Recommendation engine → React UI"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
# Allow the React dev server (Vite default: 5173) and any localhost port.
# Restrict origins to specific domains in production.
ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # CRA / alternate dev port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# ─── Startup: load dataset into memory ───────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """
    Called once when the FastAPI server starts.
    Loads the cleaned dataset (from CSV cache or HuggingFace) into memory.
    """
    load_dataset_once()


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Meta"])
def health_check():
    """Simple liveness probe."""
    return {"status": "ok", "service": "AI Restaurant Recommendation API"}


# ─── Register API routes ──────────────────────────────────────────────────────
app.include_router(router, prefix="/api")


# ─── Dev entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
