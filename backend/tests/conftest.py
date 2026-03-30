"""Pytest configuration and fixtures."""

import os
from collections.abc import AsyncGenerator

# Set TESTING before importing settings
os.environ["TESTING"] = "true"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Import all models so SQLAlchemy can configure relationships
from app.core.auth.models import Clinic, ClinicMembership, User  # noqa: F401
from app.core.plugins.loader import load_modules
from app.database import Base, get_db
from app.main import app
from app.modules.clinical.models import Appointment, Patient  # noqa: F401

# Load modules manually for tests (normally done in lifespan)
load_modules(app)

# Use the DATABASE_URL directly - CI already provides the test database URL
# For local development, ensure DATABASE_URL points to test database
TEST_DATABASE_URL = settings.DATABASE_URL


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create a new engine for each test to avoid connection conflicts
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    test_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_maker() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP client for testing."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a test user and return auth headers."""
    # Register user
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass1234",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
