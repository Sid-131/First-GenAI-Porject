// frontend/src/components/SearchForm.jsx
// Phase 5 — Search form with Places dropdown fetched from backend

import { useState, useEffect } from "react";
import { fetchPlaces } from "../services/api";

const CUISINE_OPTIONS = [
    "North Indian", "South Indian", "Chinese", "Italian", "Continental",
    "Fast Food", "Biryani", "Cafe", "Desserts", "Pizza", "Seafood",
    "Mughlai", "Japanese", "Mexican", "Thai", "American", "Bakery",
];

export default function SearchForm({ onSearch, loading }) {
    const [places, setPlaces] = useState([]);
    const [placesLoading, setPlacesLoading] = useState(true);
    const [form, setForm] = useState({
        place: "",
        cuisine: "",
        max_price: "",
        min_rating: "",
    });

    // Fetch places from backend on mount
    useEffect(() => {
        fetchPlaces()
            .then(setPlaces)
            .catch(() => setPlaces([]))
            .finally(() => setPlacesLoading(false));
    }, []);

    const handleChange = (e) =>
        setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

    const handleSubmit = (e) => {
        e.preventDefault();
        onSearch({
            place: form.place,
            cuisine: form.cuisine || undefined,
            max_price: form.max_price ? parseInt(form.max_price, 10) : undefined,
            min_rating: form.min_rating ? parseFloat(form.min_rating) : undefined,
        });
    };

    const inputCls =
        "w-full px-4 py-3 rounded-xl bg-zinc-800 border border-zinc-700 " +
        "text-white placeholder-zinc-500 focus:outline-none focus:ring-2 " +
        "focus:ring-red-500 focus:border-transparent transition-all duration-200 " +
        "appearance-none cursor-pointer";

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {/* ── Places Dropdown ── */}
            <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-lg pointer-events-none">
                    📍
                </span>
                <select
                    name="place"
                    value={form.place}
                    onChange={handleChange}
                    required
                    disabled={placesLoading}
                    className={`${inputCls} pl-10 text-${form.place ? "white" : "zinc-500"}`}
                >
                    <option value="" disabled>
                        {placesLoading ? "Loading locations…" : "Select a location"}
                    </option>
                    {places.map((p) => (
                        <option key={p} value={p} className="bg-zinc-900 text-white">
                            {p}
                        </option>
                    ))}
                </select>
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none">
                    ▾
                </span>
            </div>

            {/* ── Cuisine Dropdown ── */}
            <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-lg pointer-events-none">
                    🍽️
                </span>
                <select
                    name="cuisine"
                    value={form.cuisine}
                    onChange={handleChange}
                    className={`${inputCls} pl-10`}
                >
                    <option value="">Any cuisine</option>
                    {CUISINE_OPTIONS.map((c) => (
                        <option key={c} value={c} className="bg-zinc-900 text-white">
                            {c}
                        </option>
                    ))}
                </select>
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none">
                    ▾
                </span>
            </div>

            {/* ── Budget + Rating row ── */}
            <div className="grid grid-cols-2 gap-4">
                <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 text-sm font-semibold">
                        ₹
                    </span>
                    <input
                        name="max_price"
                        type="number"
                        min="1"
                        placeholder="Max budget"
                        value={form.max_price}
                        onChange={handleChange}
                        className={`${inputCls} pl-7`}
                    />
                </div>
                <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-base pointer-events-none">
                        ⭐
                    </span>
                    <input
                        name="min_rating"
                        type="number"
                        step="0.1"
                        min="0"
                        max="5"
                        placeholder="Min rating (0–5)"
                        value={form.min_rating}
                        onChange={handleChange}
                        className={`${inputCls} pl-9`}
                    />
                </div>
            </div>

            {/* ── Submit ── */}
            <button
                type="submit"
                disabled={loading || !form.place}
                className="w-full py-3.5 rounded-xl font-semibold text-base tracking-wide
                           bg-gradient-to-r from-red-600 to-rose-500
                           hover:from-red-500 hover:to-rose-400
                           disabled:opacity-50 disabled:cursor-not-allowed
                           text-white transition-all duration-200
                           shadow-lg shadow-red-900/30
                           flex items-center justify-center gap-2"
            >
                {loading ? (
                    <>
                        <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Finding restaurants…
                    </>
                ) : (
                    <>🔍 Find Restaurants</>
                )}
            </button>
        </form>
    );
}
