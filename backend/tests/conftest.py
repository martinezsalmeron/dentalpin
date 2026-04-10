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
from app.modules.budget.models import (  # noqa: F401
    Budget,
    BudgetHistory,
    BudgetItem,
    BudgetSignature,
)
from app.modules.catalog.models import (  # noqa: F401
    TreatmentCatalogItem,
    TreatmentCategory,
    TreatmentOdontogramMapping,
)
from app.modules.clinical.models import Appointment, Patient  # noqa: F401
from app.modules.odontogram.models import OdontogramHistory, ToothRecord  # noqa: F401

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


@pytest_asyncio.fixture
async def test_clinic(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> Clinic:
    """Create a test clinic and assign the test user as admin."""
    from uuid import uuid4

    # Get user from /me endpoint
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = response.json()["data"]["user"]["id"]

    # Create clinic
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        tax_id="B12345678",
        address={"street": "Test St", "city": "Madrid"},
        settings={"slot_duration_min": 15},
        cabinets=[{"name": "Gabinete 1", "color": "#3B82F6"}],
    )
    db_session.add(clinic)
    await db_session.flush()

    # Create admin membership
    membership = ClinicMembership(
        id=uuid4(),
        user_id=user_id,
        clinic_id=clinic.id,
        role="admin",
    )
    db_session.add(membership)
    await db_session.commit()

    return clinic


@pytest_asyncio.fixture
async def test_patient(db_session: AsyncSession, test_clinic: Clinic) -> Patient:
    """Create a test patient in the test clinic."""
    from uuid import uuid4

    patient = Patient(
        id=uuid4(),
        clinic_id=test_clinic.id,
        first_name="Test",
        last_name="Patient",
        email="patient@test.com",
        phone="+34666123456",
    )
    db_session.add(patient)
    await db_session.commit()

    return patient
