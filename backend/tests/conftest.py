"""
Shared pytest fixtures for the LinkPulse backend test suite.

Design notes:
- DATABASE_URL is set to SQLite *before* any app import so that database.py's
  module-level create_async_engine never tries to load asyncpg. This means the
  test environment needs only aiosqlite, not asyncpg.
- Uses sqlite+aiosqlite:///:memory: so no PostgreSQL instance is required.
- DateTime(timezone=True) columns silently become bare DATETIME in SQLite.
  This is harmless — `created_at` is never exposed in any API response.
  Do not write tests that compare created_at against datetime.now(timezone.utc).
- The `client` fixture patches app.main.engine with the test engine to prevent
  the FastAPI lifespan from running create_all against a different engine.
- All fixtures are function-scoped for complete isolation between tests.
"""

import os

# Must be set before any app module is imported — database.py calls
# create_async_engine at module level using this value.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from unittest.mock import patch  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """
    Create a fresh in-memory SQLite engine and schema for each test.
    Function scope ensures zero row leakage between tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """
    Yields a live AsyncSession for direct database assertions.
    Shares the same in-memory database as the `client` fixture when both
    are used in the same test — rows written by route handlers are visible here.
    """
    TestSessionLocal = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_engine):
    """
    Yields an httpx.AsyncClient that talks to the FastAPI app in-process.

    Two overrides are applied:
      1. app.dependency_overrides[get_db] — injects SQLite sessions.
      2. patch("app.main.engine", test_engine) — redirects the lifespan's
         create_all away from the module-level engine to our isolated test engine.
    """
    TestSessionLocal = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.main.engine", test_engine):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()
