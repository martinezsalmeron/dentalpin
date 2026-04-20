"""Tests for OperationLog."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.plugins.db_models import ModuleOperationLog, ModuleRecord
from app.core.plugins.operation_log import OperationLog
from app.core.plugins.state import ModuleState


@pytest.fixture
async def module_row(db_session: AsyncSession) -> ModuleRecord:
    row = ModuleRecord(
        name="demo_op",
        version="0.1.0",
        state=ModuleState.INSTALLED.value,
        category="official",
        removable=True,
        auto_install=False,
        manifest_snapshot={"name": "demo_op", "version": "0.1.0"},
    )
    db_session.add(row)
    await db_session.commit()
    return row


@pytest.mark.asyncio
async def test_started_completed_roundtrip(
    db_session: AsyncSession, module_row: ModuleRecord
) -> None:
    # OperationLog commits on its own; we pass a factory pointing at the
    # same connection.
    bind = db_session.bind
    factory = async_sessionmaker(bind, expire_on_commit=False)

    log = OperationLog(factory)
    log_id = await log.started(module_name="demo_op", operation="install", step="migrate")
    assert log_id > 0

    await log.completed(log_id, {"applied_revision": "rev123"})

    row = (
        await db_session.execute(select(ModuleOperationLog).where(ModuleOperationLog.id == log_id))
    ).scalar_one()
    assert row.status == "completed"
    assert row.details["applied_revision"] == "rev123"


@pytest.mark.asyncio
async def test_failed_records_error(db_session: AsyncSession, module_row: ModuleRecord) -> None:
    bind = db_session.bind
    factory = async_sessionmaker(bind, expire_on_commit=False)

    log = OperationLog(factory)
    log_id = await log.started(module_name="demo_op", operation="install", step="seed")
    await log.failed(log_id, "permission denied")

    row = (
        await db_session.execute(select(ModuleOperationLog).where(ModuleOperationLog.id == log_id))
    ).scalar_one()
    assert row.status == "failed"
    assert row.details["error"] == "permission denied"


@pytest.mark.asyncio
async def test_last_for_module_returns_most_recent(
    db_session: AsyncSession, module_row: ModuleRecord
) -> None:
    bind = db_session.bind
    factory = async_sessionmaker(bind, expire_on_commit=False)
    log = OperationLog(factory)

    await log.started(module_name="demo_op", operation="install", step="migrate")
    latest = await log.started(module_name="demo_op", operation="install", step="seed")

    entry = await log.last_for_module(db_session, "demo_op")
    assert entry is not None
    assert entry.id == latest
    assert entry.step == "seed"
