# Tripura Plant Guide: React frontend

React 18 + Vite + React Router. Talks to the Django REST API through `src/api.js`.

## Run

```bash
npm install
cp .env.example .env     # starts in mock mode (no backend needed)
npm run dev              # http://localhost:5173
```

When the Django API is ready, set `VITE_USE_MOCK=false` in `.env`.
In dev, Vite proxies `/api` and `/media` to `http://127.0.0.1:8000`.
For production, build with `npm run build` and set `VITE_API_URL` to the API origin,
then allow that origin in Django with `django-cors-headers`.

## Pages

| Route | Page |
| --- | --- |
| `/` | Take or upload a photo, optional location, identify |
| `/result/:id` | Top match, confidence, other matches, correct/incorrect feedback |
| `/plants` | Searchable plant library |
| `/plants/:id` | Plant details |

## API contract for the backend developer

| Method and path | Request | Response |
| --- | --- | --- |
| `POST /api/identify/` | multipart: `image`, `latitude?`, `longitude?` | `{ "id": 12, "predictions": [{ "plant_id": 1, "scientific_name": "...", "common_name": "...", "confidence": 0.82 }] }` |
| `GET /api/plants/?search=` | none | array of plants, or DRF `{ "results": [...] }` |
| `GET /api/plants/<id>/` | none | `{ id, scientific_name, common_name, local_name, family, description, uses[], parts_used[], properties, habitat, image }` |
| `POST /api/feedback/` | json: `{ identification_id, plant_id, is_correct }` | any 2xx JSON |

Errors: return a non-2xx status with `{ "detail": "message" }`; the UI shows `detail` to the user.
`confidence` is a number from 0 to 1. `image` is a URL or `null`.
