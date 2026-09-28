# FoodWise

Log what's in your kitchen, get recipes ranked by what's about to expire,
what you actually have, and what you like — with a receipt scanner to
speed up inventory entry.

## How it works

- **Layer 1 — heuristic ranking (always on).** Every recipe is scored on
  ingredient coverage, expiry urgency, preference match, and nutrition fit.
  Fully transparent: the API returns each component so the UI can show
  *why* a recipe was recommended.
- **Layer 2 — learned re-ranking.** Once you've logged at least 12
  cooked/skipped/rated interactions with both outcomes represented, a
  logistic regression model trains on your history and takes over ranking.
  Retrain any time from the "Retrain ranker" button.
- **Substitutions.** Missing an ingredient? If a known substitute is
  already in your inventory, the recipe still counts as available and the
  UI tells you what to swap.
- **Receipt scanning.** Upload a photo, OCR (Tesseract) extracts line
  text, and fuzzy matching resolves it against your ingredient list. You
  review and confirm before anything is added to inventory — nothing is
  auto-committed from OCR alone.

## Project structure

```
backend/
  app/
    main.py              FastAPI app, mounts the frontend as static files
    database.py           SQLAlchemy engine/session
    models.py              ORM models
    schemas.py             Pydantic request/response schemas
    ranking.py             The recommendation engine (heuristic + learned reranker)
    ocr.py                  Receipt text extraction + ingredient matching
    seed.py                 Loads data/recipes.json into the database on first run
    routers/                One file per resource: inventory, recipes,
                             recommendations, interactions, preferences, receipts
  data/
    recipes.json            40 seed recipes (title, ingredients, steps, macros)
    shelf_life.json          Default shelf life in days, by ingredient category
    substitutions.json       Ingredient substitution table
    generate_seed.py         Regenerates the three JSON files above if you want
                              to edit the seed dataset
  requirements.txt
frontend/
  index.html / styles.css / app.js   Plain JS single-page app, no build step
Dockerfile
docker-compose.yml
```

## Run locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000` — the backend serves the frontend directly,
so there's nothing else to start. The SQLite database and seed data are
created automatically on first run.

Receipt scanning requires the Tesseract OCR binary on the host:

```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr
# macOS
brew install tesseract
```

If Tesseract isn't installed, every other feature still works — the
`/api/receipts/scan` endpoint returns a clear 503 explaining what's missing
instead of failing silently.

## Deploy

### Docker (recommended)

```bash
docker compose up --build -d
```

This builds a single image (Tesseract included), runs it on port 8000,
and persists the database in a named volume so it survives restarts.

### Any container host (Render, Railway, Fly.io, etc.)

Point the platform at the included `Dockerfile`. No environment variables
are required to boot; optionally set:

- `DATABASE_URL` — defaults to a local SQLite file. Point this at a
  managed Postgres instance for production (`postgresql://...`); the
  schema is plain SQLAlchemy so no code changes are needed.
- `CORS_ORIGINS` — comma-separated list of allowed origins if you ever
  split the frontend onto a different domain. Defaults to `*`.
- `AZURE_OPENAI_ENDPOINT` — Azure OpenAI endpoint URL (e.g. `https://your-resource-name.openai.azure.com/`).
- `AZURE_OPENAI_API_KEY` — Azure OpenAI API key.
- `AZURE_OPENAI_DEPLOYMENT` — Azure OpenAI model deployment name (e.g. `gpt-5.4`).
- `AZURE_OPENAI_API_VERSION` — Azure OpenAI API version (e.g. `2024-12-01-preview`).


### Plain VM / systemd

```bash
apt-get install tesseract-ocr
pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Put this behind a reverse proxy (nginx/Caddy) for TLS.

## Notes on the ML component

The re-ranker is intentionally simple: pointwise logistic regression over
five features (coverage, expiry urgency, preference score, nutrition fit,
missing ratio), trained on your own interaction history. That's a
deliberate choice — it's real learning-to-rank, but scoped to the amount
of data a single user actually generates, rather than pretending to have
millions of interactions. The heuristic layer is the reliable fallback and
stays fully explainable at all times.

The embedding-based similarity work described in the original design
(cold-start recommendations, ingredient-substitution clustering) is the
natural next step once the interaction and recipe datasets grow — the
`ranking.py` module is structured so that a Layer 3 embedding step can
slot in alongside `train_reranker` without touching the API surface.
