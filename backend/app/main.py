import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, engine, get_db
from .models import Url
from .shortener import generate_code

_MAX_RETRIES = 5  # collision retry limit


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (dev convenience; swap for Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="LinkPulse API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS — allow the React dev server through
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / response schemas ───────────────────────────────────────────────

class ShortenRequest(BaseModel):
    original_url: HttpUrl


class ShortenResponse(BaseModel):
    status: str
    code: str
    shortened_url: str
    original_url: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "linkpulse-api"}


@app.post("/api/url", response_model=ShortenResponse, status_code=201)
async def shorten(body: ShortenRequest, db: AsyncSession = Depends(get_db)):
    original = str(body.original_url)

    # Return existing code if this URL was already shortened
    result = await db.execute(select(Url).where(Url.original_url == original))
    existing = result.scalar_one_or_none()
    if existing:
        return ShortenResponse(
            status="ok",
            code=existing.code,
            shortened_url=f"linkpul.se/r/{existing.code}",
            original_url=existing.original_url,
        )

    # Generate a unique code (retry on the rare collision)
    for _ in range(_MAX_RETRIES):
        code = generate_code()
        taken = await db.execute(select(Url).where(Url.code == code))
        if taken.scalar_one_or_none() is None:
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate a unique code")

    url_row = Url(code=code, original_url=original)
    db.add(url_row)
    await db.commit()
    await db.refresh(url_row)

    return ShortenResponse(
        status="ok",
        code=url_row.code,
        shortened_url=f"linkpul.se/r/{url_row.code}",
        original_url=url_row.original_url,
    )


@app.get("/r/{code}")
async def redirect(code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Url).where(Url.code == code))
    url_row = result.scalar_one_or_none()
    if url_row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Increment click counter (fire-and-forget; don't block the redirect)
    url_row.click_count += 1
    await db.commit()

    return RedirectResponse(url=url_row.original_url, status_code=302)
