"""
Integration tests for the LinkPulse API endpoints.

All tests use the `client` fixture (httpx.AsyncClient over ASGI) backed by an
in-memory SQLite database — no real PostgreSQL or network required.

Key quirk: Pydantic's HttpUrl normalises URLs, so "https://example.com" is
stored and returned as "https://example.com/" (trailing slash added).
"""

from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.models import Url


# ── GET /api/health ───────────────────────────────────────────────────────────


class TestHealthEndpoint:
    async def test_returns_200(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200

    async def test_response_body(self, client):
        resp = await client.get("/api/health")
        assert resp.json() == {"status": "ok", "service": "linkpulse-api"}

    async def test_content_type_is_json(self, client):
        resp = await client.get("/api/health")
        assert "application/json" in resp.headers["content-type"]


# ── POST /api/url ─────────────────────────────────────────────────────────────


class TestShortenEndpoint:
    async def test_returns_201_for_new_url(self, client):
        resp = await client.post("/api/url", json={"original_url": "https://example.com"})
        assert resp.status_code == 201

    async def test_response_has_all_required_fields(self, client):
        resp = await client.post("/api/url", json={"original_url": "https://example.com"})
        assert set(resp.json().keys()) == {"status", "code", "shortened_url", "original_url"}

    async def test_status_field_is_ok(self, client):
        resp = await client.post("/api/url", json={"original_url": "https://example.com"})
        assert resp.json()["status"] == "ok"

    async def test_code_is_7_char_alphanumeric(self, client):
        resp = await client.post("/api/url", json={"original_url": "https://example.com"})
        code = resp.json()["code"]
        assert len(code) == 7
        assert code.isalnum()

    async def test_shortened_url_uses_linkpulse_domain(self, client):
        """shortened_url must start with the hardcoded linkpul.se/r/ prefix."""
        resp = await client.post("/api/url", json={"original_url": "https://example.com"})
        assert resp.json()["shortened_url"].startswith("linkpul.se/r/")

    async def test_pydantic_normalises_trailing_slash(self, client):
        """
        Pydantic HttpUrl normalises 'https://example.com' → 'https://example.com/'.
        The stored and returned original_url must reflect the normalised form.
        """
        resp = await client.post("/api/url", json={"original_url": "https://example.com"})
        assert resp.json()["original_url"] == "https://example.com/"

    async def test_deduplication_returns_same_code(self, client):
        """POSTing the same URL twice must return the identical short code."""
        url = "https://dedup-test.example.com/page"
        r1 = await client.post("/api/url", json={"original_url": url})
        r2 = await client.post("/api/url", json={"original_url": url})
        assert r1.json()["code"] == r2.json()["code"]

    async def test_deduplication_creates_only_one_db_row(self, client, db_session):
        """Deduplication must not insert a second row for the same URL."""
        url = "https://dedup-rows.example.com/path"
        await client.post("/api/url", json={"original_url": url})
        await client.post("/api/url", json={"original_url": url})

        # Pydantic normalises the URL — query with the trailing slash form
        result = await db_session.execute(
            select(Url).where(Url.original_url == "https://dedup-rows.example.com/path")
        )
        rows = result.scalars().all()
        assert len(rows) == 1

    async def test_different_urls_get_different_codes(self, client):
        r1 = await client.post("/api/url", json={"original_url": "https://site-a.example.com"})
        r2 = await client.post("/api/url", json={"original_url": "https://site-b.example.com"})
        assert r1.json()["code"] != r2.json()["code"]

    async def test_invalid_url_returns_422(self, client):
        """Non-URL strings must be rejected by Pydantic with a 422 response."""
        resp = await client.post("/api/url", json={"original_url": "not-a-url"})
        assert resp.status_code == 422

    async def test_missing_original_url_field_returns_422(self, client):
        resp = await client.post("/api/url", json={})
        assert resp.status_code == 422

    async def test_collision_exhaustion_returns_500(self, client, db_session):
        """
        When generate_code always returns a code that is already taken and all
        _MAX_RETRIES attempts fail, the endpoint must return 500.
        """
        taken_code = "AAAAAAA"
        # Pre-seed the DB with the code that the mock will always return
        db_session.add(Url(code=taken_code, original_url="https://pre-seeded.example.com/"))
        await db_session.commit()

        with patch("app.main.generate_code", return_value=taken_code):
            resp = await client.post(
                "/api/url", json={"original_url": "https://collision-trigger.example.com"}
            )

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Could not generate a unique code"


# ── GET /r/{code} ─────────────────────────────────────────────────────────────


class TestRedirectEndpoint:
    async def _shorten(self, client, url: str) -> str:
        """Helper: shorten a URL and return the generated code."""
        resp = await client.post("/api/url", json={"original_url": url})
        assert resp.status_code == 201
        return resp.json()["code"]

    async def test_valid_code_returns_302(self, client):
        code = await self._shorten(client, "https://redirect-test.example.com")
        resp = await client.get(f"/r/{code}", follow_redirects=False)
        assert resp.status_code == 302

    async def test_redirect_location_header(self, client):
        """Location header must point to the original (normalised) URL."""
        code = await self._shorten(client, "https://redirect-target.example.com")
        resp = await client.get(f"/r/{code}", follow_redirects=False)
        assert resp.headers["location"] == "https://redirect-target.example.com/"

    async def test_unknown_code_returns_404(self, client):
        resp = await client.get("/r/XXXXXXX", follow_redirects=False)
        assert resp.status_code == 404

    async def test_404_detail_message(self, client):
        resp = await client.get("/r/XXXXXXX", follow_redirects=False)
        assert resp.json()["detail"] == "Short URL not found"

    async def test_click_count_starts_at_zero(self, client, db_session):
        """A freshly shortened URL must have click_count == 0 before any redirect."""
        code = await self._shorten(client, "https://fresh-url.example.com")
        result = await db_session.execute(select(Url).where(Url.code == code))
        row = result.scalar_one()
        assert row.click_count == 0

    async def test_click_count_increments_on_each_redirect(self, client, db_session):
        """Each successful redirect must increment click_count by exactly 1."""
        code = await self._shorten(client, "https://click-count.example.com")

        for _ in range(3):
            await client.get(f"/r/{code}", follow_redirects=False)

        result = await db_session.execute(select(Url).where(Url.code == code))
        row = result.scalar_one()
        assert row.click_count == 3

    async def test_404_does_not_increment_click_count(self, client, db_session):
        """A 404 hit must not affect any existing row's click_count."""
        await self._shorten(client, "https://unaffected.example.com")
        await client.get("/r/NOTEXIST", follow_redirects=False)  # 404

        result = await db_session.execute(select(Url))
        rows = result.scalars().all()
        assert all(r.click_count == 0 for r in rows)
