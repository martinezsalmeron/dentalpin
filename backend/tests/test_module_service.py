"""Tests for ModuleService reconciliation and query methods."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugins.db_models import ModuleRecord
from app.core.plugins.service import ModuleService
from app.core.plugins.state import ModuleState


@pytest.mark.asyncio
async def test_reconcile_empty_db_inserts_all_modules(db_session: AsyncSession) -> None:
    svc = ModuleService(db_session)
    await svc.reconcile_with_db()

    records = (await db_session.execute(select(ModuleRecord))).scalars().all()
    names = {r.name for r in records}

    # All nine modules are loaded in conftest.load_modules.
    expected = {
        "clinical",
        "catalog",
        "budget",
        "billing",
        "odontogram",
        "treatment_plan",
        "media",
        "notifications",
        "reports",
    }
    assert expected.issubset(names)

    for record in records:
        if record.name in expected:
            assert record.state == ModuleState.INSTALLED.value
            assert record.manifest_snapshot["name"] == record.name


@pytest.mark.asyncio
async def test_reconcile_updates_version_change(db_session: AsyncSession) -> None:
    svc = ModuleService(db_session)
    await svc.reconcile_with_db()

    # Tamper with a version to simulate an out-of-date row.
    record = (
        await db_session.execute(select(ModuleRecord).where(ModuleRecord.name == "clinical"))
    ).scalar_one()
    record.version = "0.0.1-old"
    await db_session.commit()

    await svc.reconcile_with_db()
    refreshed = (
        await db_session.execute(select(ModuleRecord).where(ModuleRecord.name == "clinical"))
    ).scalar_one()
    assert refreshed.version != "0.0.1-old"


@pytest.mark.asyncio
async def test_list_modules_combines_disk_and_db(db_session: AsyncSession) -> None:
    svc = ModuleService(db_session)
    await svc.reconcile_with_db()

    infos = await svc.list_modules()
    by_name = {i.name: i for i in infos}

    assert "clinical" in by_name
    assert by_name["clinical"].in_disk is True
    assert by_name["clinical"].state == ModuleState.INSTALLED


@pytest.mark.asyncio
async def test_doctor_flags_orphans(db_session: AsyncSession) -> None:
    svc = ModuleService(db_session)
    await svc.reconcile_with_db()

    # Simulate an orphan: a module row whose code disappeared from disk.
    db_session.add(
        ModuleRecord(
            name="ghost",
            version="0.0.1",
            state=ModuleState.INSTALLED.value,
            category="community",
            removable=True,
            auto_install=False,
            manifest_snapshot={"name": "ghost", "version": "0.0.1"},
        )
    )
    await db_session.commit()

    report = await svc.doctor()
    assert "ghost" in report.orphans
    assert report.ok is False


@pytest.mark.asyncio
async def test_orphan_command_resets_state(db_session: AsyncSession) -> None:
    svc = ModuleService(db_session)
    await svc.reconcile_with_db()

    db_session.add(
        ModuleRecord(
            name="ghost",
            version="0.0.1",
            state=ModuleState.INSTALLED.value,
            category="community",
            removable=True,
            auto_install=False,
            manifest_snapshot={"name": "ghost", "version": "0.0.1"},
        )
    )
    await db_session.commit()

    updated = await svc.orphan("ghost")
    assert updated is True

    record = (
        await db_session.execute(select(ModuleRecord).where(ModuleRecord.name == "ghost"))
    ).scalar_one()
    assert record.state == ModuleState.UNINSTALLED.value


@pytest.mark.asyncio
async def test_status_reports_counts(db_session: AsyncSession) -> None:
    svc = ModuleService(db_session)
    await svc.reconcile_with_db()

    status = await svc.status()
    assert status["total"] >= 9
    assert status["by_state"].get("installed", 0) >= 9
    assert status["pending"] == []
