// All REST calls to the Django API live here. Pages never call fetch directly.
import { mockIdentify, mockPlants, mockPlant } from "./mock.js";

const BASE = (import.meta.env.VITE_API_URL || "") + "/api";
const MOCK = import.meta.env.VITE_USE_MOCK === "true";

async function request(path, options = {}) {
  const res = await fetch(BASE + path, options);
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail; } catch { /* body was not JSON */ }
    throw new Error(detail || `Request failed (${res.status}).`);
  }
  return res.json();
}

// POST /api/identify/  (multipart: image, latitude?, longitude?)
export function identifyPlant(file, coords) {
  if (MOCK) return mockIdentify();
  const body = new FormData();
  body.append("image", file);
  if (coords) {
    body.append("latitude", coords.latitude);
    body.append("longitude", coords.longitude);
  }
  return request("/identify/", { method: "POST", body });
}

// GET /api/plants/?search=  (plain array or DRF paginated {results: []})
export async function listPlants(search = "") {
  if (MOCK) return mockPlants(search);
  const data = await request(`/plants/?search=${encodeURIComponent(search)}`);
  return data.results ?? data;
}

// GET /api/plants/:id/
export function getPlant(id) {
  return MOCK ? mockPlant(id) : request(`/plants/${id}/`);
}

// POST /api/feedback/  (json: identification_id, plant_id, is_correct)
export function sendFeedback(payload) {
  if (MOCK) return Promise.resolve({});
  return request("/feedback/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
