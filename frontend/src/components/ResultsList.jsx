// frontend/src/components/ResultsList.jsx
// Phase 5 — Results grid: Gemini review + restaurant cards + skeleton loading

import RestaurantCard from "./RestaurantCard";

function SkeletonCard() {
    return (
        <div className="rounded-2xl bg-zinc-900 border border-zinc-800 p-5 space-y-3">
            <div className="skeleton h-5 w-3/4" />
            <div className="skeleton h-4 w-1/2" />
            <div className="flex gap-2">
                <div className="skeleton h-5 w-16 rounded-full" />
                <div className="skeleton h-5 w-16 rounded-full" />
            </div>
            <div className="skeleton h-px w-full" />
            <div className="flex justify-between">
                <div className="skeleton h-4 w-24" />
                <div className="skeleton h-4 w-16" />
            </div>
        </div>
    );
}

export default function ResultsList({ restaurants, loading }) {
    // Loading skeletons
    if (loading) {
        return (
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
        );
    }

    if (!restaurants || restaurants.length === 0) return null;

    return (
        <div className="animate-fade-up mt-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">
                    Top {restaurants.length} Matches
                </h2>
                <span className="text-xs text-zinc-500 bg-zinc-800 px-3 py-1 rounded-full">
                    Sorted by rating
                </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {restaurants.map((r, idx) => (
                    <RestaurantCard key={r.name + r.location} restaurant={r} index={idx} />
                ))}
            </div>
        </div>
    );
}
