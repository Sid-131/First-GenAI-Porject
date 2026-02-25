// frontend/src/App.jsx
// Phase 5 — Root component: state management & full API orchestration

import { useState } from "react";
import SearchForm from "./components/SearchForm";
import GeminiReview from "./components/GeminiReview";
import ResultsList from "./components/ResultsList";
import ErrorBanner from "./components/ErrorBanner";
import { fetchRecommendations } from "./services/api";

export default function App() {
    const [restaurants, setRestaurants] = useState(null);
    const [geminiReview, setGeminiReview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [hasSearched, setHasSearched] = useState(false);

    const handleSearch = async (formData) => {
        setLoading(true);
        setError(null);
        setRestaurants(null);
        setGeminiReview(null);
        setHasSearched(true);

        try {
            const data = await fetchRecommendations(formData);

            // Backend returns { error: "..." } when no matches found
            if (data.error) {
                setError(data.error);
                return;
            }

            setRestaurants(data.restaurants ?? []);
            setGeminiReview(data.gemini_review ?? null);
        } catch (err) {
            const msg =
                err?.response?.data?.detail ||
                err?.response?.data?.error ||
                err?.message ||
                "Cannot reach the backend. Please ensure the server is running.";
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen hero-gradient">
            {/* ── Hero Header ─────────────────────────────────────── */}
            <header className="pt-14 pb-10 text-center px-4">
                <div className="inline-flex items-center gap-3 mb-4">
                    <span className="text-5xl">🍽️</span>
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white">
                        AI Restaurant
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-rose-500">
                            {" "}Finder
                        </span>
                    </h1>
                </div>
                <p className="text-zinc-400 text-base md:text-lg max-w-md mx-auto mt-2 leading-relaxed">
                    Powered by{" "}
                    <span className="text-red-400 font-semibold">Gemini AI</span>
                    {" "}×{" "}
                    <span className="text-zinc-300 font-semibold">Zomato Data</span>
                    {" "}— discover your next favourite spot.
                </p>
            </header>

            {/* ── Search Panel ────────────────────────────────────── */}
            <main className="max-w-2xl mx-auto px-4 pb-20">
                <div className="rounded-3xl bg-zinc-900/80 border border-zinc-800 p-6 md:p-8
                                shadow-2xl backdrop-blur-sm">
                    <SearchForm onSearch={handleSearch} loading={loading} />
                </div>

                {/* ── Loading state (while waiting for Gemini) ──── */}
                {loading && (
                    <div className="mt-10 flex flex-col items-center gap-3 text-zinc-400">
                        <div className="flex gap-1.5">
                            {[0, 1, 2].map((i) => (
                                <span
                                    key={i}
                                    className="w-2.5 h-2.5 rounded-full bg-red-500 animate-bounce"
                                    style={{ animationDelay: `${i * 0.15}s` }}
                                />
                            ))}
                        </div>
                        <p className="text-sm">Asking Gemini for recommendations…</p>
                    </div>
                )}

                {/* ── Error / no-results banner ─────────────────── */}
                {!loading && error && <ErrorBanner message={error} />}

                {/* ── Results: Gemini review first, then cards ──── */}
                {!loading && !error && restaurants && (
                    <>
                        <GeminiReview review={geminiReview} />
                        <ResultsList restaurants={restaurants} />
                    </>
                )}

                {/* ── Empty state after search with no LLM error ── */}
                {!loading && !error && hasSearched && restaurants?.length === 0 && (
                    <ErrorBanner message="No recommendations returned. Try relaxing filters." />
                )}

                {/* ── Initial empty state ───────────────────────── */}
                {!hasSearched && !loading && (
                    <div className="mt-12 text-center text-zinc-600 text-sm">
                        <p>Select a location above to get started 👆</p>
                    </div>
                )}
            </main>

            {/* ── Footer ──────────────────────────────────────────── */}
            <footer className="py-6 text-center text-xs text-zinc-700">
                AI Restaurant Finder · Powered by Google Gemini &amp; Zomato Open Data
            </footer>
        </div>
    );
}
