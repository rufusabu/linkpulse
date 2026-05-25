# LinkPulse

A lightweight URL shortener with a React frontend and a FastAPI backend, backed by PostgreSQL. Paste a long URL, get a short `linkpul.se/r/<code>` link in return. Every redirect increments a click counter automatically.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite |
| Backend | FastAPI (async) + SQLAlchemy 2 |
| Database | PostgreSQL 16 |
| Containers | Docker + Docker Compose |

## Getting started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Run locally

```bash
# 1. Copy the example env file and adjust values if needed
cp .env.example .env

# 2. Start all three services (db, api, ui)
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/api/docs

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/url` | Shorten a URL |
| `GET` | `/r/{code}` | Redirect to original URL |

### Shorten a URL

```bash
curl -X POST http://localhost:8000/api/url \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/some/very/long/path"}'
```

```json
{
  "status": "ok",
  "code": "aB3xYz",
  "shortened_url": "linkpul.se/r/aB3xYz",
  "original_url": "https://example.com/some/very/long/path"
}
```

## Project structure

```
linkpulse/
├── backend/
│   └── app/
│       ├── main.py        # FastAPI routes
│       ├── models.py      # SQLAlchemy models
│       ├── database.py    # Async DB engine & session
│       └── shortener/     # Code generation logic
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/    # URLInput, SubmitButton, ResultCard
└── docker-compose.yml
```
