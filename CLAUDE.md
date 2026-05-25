# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the full stack

```bash
cp .env.example .env          # first time only
docker compose up --build     # starts db (5432), backend (8000), frontend (5173)
```

Both `backend/app/` and `frontend/src/` are bind-mounted into their containers, so code changes hot-reload without a rebuild.

## Backend

### Running tests (no Docker required)

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m pytest tests/ -v          # all 30 tests
python3 -m pytest tests/test_api.py -v          # API integration tests only
python3 -m pytest tests/test_shortener.py -v    # unit tests only
python3 -m pytest tests/test_api.py::TestRedirectEndpoint::test_click_count_increments_on_each_redirect -v  # single test
```

Tests use SQLite in-memory via `aiosqlite` — no PostgreSQL instance needed. `asyncpg` is not required for the test suite.

### Running the backend standalone

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://linkpulse:changeme@localhost:5432/linkpulse \
  uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/api/docs`.

## Frontend

```bash
cd frontend
npm install
npm run dev      # dev server on http://localhost:5173
npm run build    # production build to dist/
```

The Vite dev server proxies `/api` to the backend (configured via `VITE_API_URL`).

## Architecture

### Request flow

```text
Browser → React (Vite) → POST /api/url → FastAPI → PostgreSQL
                        → GET  /r/{code} → FastAPI → 302 redirect
```

### Backend (FastAPI, async throughout)

- **`app/main.py`** — all three routes plus Pydantic request/response schemas. The lifespan context manager runs `Base.metadata.create_all` on startup (dev convenience; no Alembic migrations are set up yet).
- **`app/database.py`** — module-level `engine` and `AsyncSessionLocal` created from `DATABASE_URL` env var. The `get_db()` async generator is injected as a FastAPI dependency.
- **`app/models.py`** — single `Url` ORM model with `code` (unique, indexed), `original_url`, `created_at`, and `click_count`.
- **`app/shortener/shortener.py`** — `generate_code()` produces a 7-char base-62 token using `secrets.choice`. The route retries up to `_MAX_RETRIES = 5` times on collision before returning 500.

**URL deduplication:** `POST /api/url` checks for an existing row matching `original_url` before inserting, so the same long URL always maps to the same short code.

**Click tracking:** `GET /r/{code}` increments `click_count` and commits before issuing the 302 redirect (not fire-and-forget).

**Pydantic URL normalisation:** `HttpUrl` adds a trailing slash to bare origins — `https://example.com` is stored as `https://example.com/`. Tests and any code asserting on `original_url` must account for this.

### Frontend (React 18 + Vite)

- **`src/App.jsx`** — root component; owns all state (`url`, `result`, `error`, `loading`) and calls `POST /api/url` via axios.
- **`src/components/`** — three presentational components (`URLInput`, `SubmitButton`, `ResultCard`), each with a co-located CSS Module.

### Test infrastructure

- **`backend/tests/conftest.py`** sets `DATABASE_URL=sqlite+aiosqlite:///:memory:` before any app import to prevent asyncpg from loading. Each test gets a fresh `test_engine` fixture (function-scoped) with tables created/dropped around it. The `client` fixture overrides `get_db` and patches `app.main.engine` so the FastAPI lifespan's `create_all` runs against SQLite rather than PostgreSQL.

## Environment variables

| Variable        | Default                                                            | Notes                                                              |
| --------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `DATABASE_URL`  | `postgresql+asyncpg://linkpulse:changeme@localhost:5432/linkpulse` | Set to `sqlite+aiosqlite:///:memory:` automatically during tests   |
| `CORS_ORIGINS`  | `http://localhost:5173`                                            | Comma-separated list                                               |
| `JWT_SECRET`    | `super-secret-change-me`                                           | Auth infrastructure installed but not yet wired to any route       |
| `VITE_API_URL`  | `http://localhost:8000`                                            | Frontend only                                                      |
