from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .shortener import shorten_url

import os

app = FastAPI(
    title="LinkPulse API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
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

class URL(BaseModel):
    original_url: str


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "linkpulse-api"}


@app.post("/api/url")
async def shorten(url: URL) -> dict[str, str]:
    input_url: str = url.original_url
    shortened_code = shorten_url(input_url)[:8]
    shortened_url = "".join(["linkpul.se", "/", shortened_code])

    return {"status": "ok", "shortened_url": shortened_url}
