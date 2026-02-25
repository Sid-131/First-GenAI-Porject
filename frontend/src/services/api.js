// frontend/src/services/api.js
// Axios service layer for the FastAPI backend

import axios from "axios";

// In dev, Vite proxies /api/* → http://localhost:8000/api (see vite.config.js).
// In production, set VITE_API_URL to the deployed backend URL.
const BASE_URL = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 30000, // Gemini can take a few seconds
});

/**
 * GET /api/places
 * Returns the sorted list of all unique restaurant locations.
 * @returns {Promise<string[]>}
 */
export async function fetchPlaces() {
    const { data } = await api.get("/places");
    return data.places ?? [];
}

/**
 * POST /api/recommend
 * @param {{ place: string, cuisine?: string, max_price?: number, min_rating?: number }} params
 * @returns {Promise<
 *   | { total: number, restaurants: Array, gemini_review: string|null }
 *   | { error: string }
 * >}
 */
export async function fetchRecommendations(params) {
    const { data } = await api.post("/recommend", params);
    return data;
}
