// frontend/src/components/RestaurantCard.jsx
// Phase 5 — Premium restaurant card with rating badge, cuisine chips, price tag

function ratingBadgeClass(rate) {
    if (rate >= 4.0) return "bg-green-600 text-white";
    if (rate >= 3.0) return "bg-yellow-500 text-black";
    return "bg-red-600 text-white";
}

export default function RestaurantCard({ restaurant, index }) {
    const { name, location, cuisines, rate, approx_cost, votes } = restaurant;

    const cuisineList = cuisines
        ? cuisines.split(",").map((c) => c.trim()).filter(Boolean)
        : [];

    return (
        <div className="card-hover rounded-2xl bg-zinc-900 border border-zinc-800 p-5 flex flex-col gap-3">
            {/* ── Header row ── */}
            <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-bold text-red-500 uppercase tracking-widest">
                            #{index + 1}
                        </span>
                    </div>
                    <h3 className="text-[17px] font-semibold text-white leading-tight truncate">
                        {name}
                    </h3>
                </div>

                {/* Rating badge */}
                {rate != null && (
                    <span className={`flex-shrink-0 px-2.5 py-1 text-sm font-bold rounded-lg ${ratingBadgeClass(rate)}`}>
                        ★ {rate.toFixed(1)}
                    </span>
                )}
            </div>

            {/* ── Location ── */}
            <p className="text-zinc-400 text-sm flex items-center gap-1.5">
                <span>📍</span>
                <span className="truncate">{location}</span>
            </p>

            {/* ── Cuisine chips ── */}
            {cuisineList.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {cuisineList.slice(0, 4).map((c) => (
                        <span
                            key={c}
                            className="px-2 py-0.5 rounded-full bg-zinc-800 border border-zinc-700
                                       text-zinc-300 text-xs capitalize"
                        >
                            {c}
                        </span>
                    ))}
                </div>
            )}

            {/* ── Footer: cost + votes ── */}
            <div className="flex items-center justify-between mt-auto pt-2 border-t border-zinc-800">
                {approx_cost != null ? (
                    <span className="text-sm font-medium text-zinc-300">
                        💰 <span className="font-bold text-white">₹{approx_cost.toLocaleString()}</span>
                        <span className="text-zinc-500 text-xs ml-1">for two</span>
                    </span>
                ) : (
                    <span className="text-zinc-600 text-sm">Price N/A</span>
                )}

                {votes != null && (
                    <span className="text-xs text-zinc-500">
                        {votes.toLocaleString()} votes
                    </span>
                )}
            </div>
        </div>
    );
}
