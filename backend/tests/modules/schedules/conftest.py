"""Shared fixtures for schedules tests."""

from __future__ import annotations

from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.auth.service import hash_password


@pytest_asyncio.fixture
async def dentist_user(db_session: AsyncSession, test_clinic: Clinic) -> User:
    """Create a dentist user with membership in the test clinic."""
    user = User(
        id=uuid4(),
        email="dentist@example.com",
        password_hash=hash_password("DentistPass1234"),
        first_name="Dr",
        last_name="Dentist",
        is_active=True,
        token_version=0,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(
        ClinicMembership(
            id=uuid4(),
            user_id=user.id,
            clinic_id=test_clinic.id,
            role="dentist",
        )
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def hygienist_user(db_session: AsyncSession, test_clinic: Clinic) -> User:
    user = User(
        id=uuid4(),
        email="hygienist@example.com",
        password_hash=hash_password("HygienistPass1234"),
        first_name="Hy",
        last_name="Gienist",
        is_active=True,
        token_version=0,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        ClinicMembership(
            id=uuid4(),
            user_id=user.id,
            clinic_id=test_clinic.id,
            role="hygienist",
        )
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def receptionist_user(db_session: AsyncSession, test_clinic: Clinic) -> User:
    user = User(
        id=uuid4(),
        email="reception@example.com",
        password_hash=hash_password("ReceptionPass1234"),
        first_name="Re",
        last_name="Cept",
        is_active=True,
        token_version=0,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        ClinicMembership(
            id=uuid4(),
            user_id=user.id,
            clinic_id=test_clinic.id,
            role="receptionist",
        )
    )
    await db_session.commit()
    return user
