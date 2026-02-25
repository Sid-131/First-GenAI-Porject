// frontend/src/components/ErrorBanner.jsx
// Phase 5 — Clean warning banner for "no results" and network errors

export default function ErrorBanner({ message }) {
    if (!message) return null;

    const isNoResults = message.toLowerCase().includes("no recommendations");

    return (
        <div className={`animate-fade-up mt-8 rounded-2xl border px-5 py-4 flex items-start gap-4
            ${isNoResults
                ? "bg-amber-950/30 border-amber-800/40 text-amber-300"
                : "bg-red-950/30  border-red-800/40  text-red-300"
            }`}
        >
            <span className="text-2xl flex-shrink-0 mt-0.5">
                {isNoResults ? "🔍" : "⚠️"}
            </span>
            <div>
                <p className="font-semibold text-[15px]">
                    {isNoResults ? "No restaurants found" : "Something went wrong"}
                </p>
                <p className="mt-1 text-sm opacity-80">
                    {isNoResults
                        ? "Try broadening your search — relax the price limit, lower the minimum rating, or pick a different location."
                        : message}
                </p>
            </div>
        </div>
    );
}
