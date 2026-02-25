// frontend/src/components/GeminiReview.jsx
// Phase 5 — Gemini AI expert food critic review panel

export default function GeminiReview({ review }) {
    if (!review) return null;

    // Split into numbered paragraphs for nicer layout
    const paragraphs = review.split(/\n+/).filter((p) => p.trim().length > 0);

    return (
        <div className="animate-fade-up mt-8 rounded-2xl border border-red-900/40 bg-gradient-to-br
                        from-zinc-900 to-zinc-950 overflow-hidden">
            {/* Header */}
            <div className="flex items-center gap-3 px-5 py-4 bg-red-950/30 border-b border-red-900/30">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-red-500 to-rose-600
                                flex items-center justify-center text-xl flex-shrink-0 shadow-md">
                    🤖
                </div>
                <div>
                    <p className="text-sm font-bold text-red-400 uppercase tracking-wider">
                        Gemini AI · Expert Food Critic
                    </p>
                    <p className="text-xs text-zinc-500 mt-0.5">
                        Personalised review based on your preferences
                    </p>
                </div>
                <span className="ml-auto px-2 py-0.5 rounded-full bg-red-900/40 text-red-400
                                 text-xs font-semibold border border-red-800/50">
                    AI-generated
                </span>
            </div>

            {/* Body */}
            <div className="px-5 py-5 space-y-2.5 text-[15px] leading-relaxed text-zinc-300">
                {paragraphs.map((para, i) => (
                    <p key={i} className="text-zinc-300">{para}</p>
                ))}
            </div>
        </div>
    );
}
