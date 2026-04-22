# ---------- Base ----------
FROM python:3.12-slim AS base

WORKDIR /app

# System deps for asyncpg (PostgreSQL C bindings)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Development (default) ----------
FROM base AS dev

COPY . .

EXPOSE 8000

# Uvicorn with hot-reload — watches /app/app for changes
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------- Production ----------
FROM base AS prod

COPY . .

EXPOSE 8000

# Gunicorn with Uvicorn workers for production
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000"]
