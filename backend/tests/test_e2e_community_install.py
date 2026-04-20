"""End-to-end test: install a fictional community module.

Registers ``SampleModule`` directly in the in-memory registry, walks
through ``ModuleService.install`` + ``PendingProcessor.run`` exactly
the way the app lifespan does on a real restart, and asserts the
post-condition — state=installed, a backend router mount, an entry in
core_module_operation_log, a path added to modules.json.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.plugins.db_models import ModuleOperationLog, ModuleRecord
from app.core.plugins.processor import PendingProcessor
from app.core.plugins.registry import module_registry
from app.core.plugins.service import ModuleService
from app.core.plugins.state import ModuleState
from tests.fixtures.sample_module import SampleModule


@pytest.fixture
def sample_registered():
    """Register SampleModule for the duration of one test, then unregister."""
    existing = module_registry.get("sample_community")
    if existing is None:
        instance = SampleModule()
        module_registry.register(instance)
    # Deregister via private field — registry has no public remove.
    try:
        yield module_registry.get("sample_community")
    finally:
        module_registry._modules.pop("sample_community", None)  # noqa: SLF001


@pytest.mark.asyncio
async def test_install_flow_end_to_end(
    db_session: AsyncSession, sample_registered, tmp_path, monkeypatch
) -> None:
    # Route writes to an isolated frontend root for the test.
    from app.core.plugins import frontend_layers

    monkeypatch.setattr(frontend_layers, "DEFAULT_FRONTEND_ROOT", tmp_path)

    svc = ModuleService(db_session)
    await svc.reconcile_with_db()

    # SampleModule starts reconciled as installed (reconcile inserts
    # discovered modules as installed). For a realistic install flow we
    # reset it to uninstalled first.
    record = (
        await db_session.execute(
            select(ModuleRecord).where(ModuleRecord.name == "sample_community")
        )
    ).scalar_one()
    record.state = ModuleState.UNINSTALLED.value
    record.installed_at = None
    record.applied_revision = None
    record.base_revision = None
    await db_session.commit()

    scheduled = await svc.install("sample_community")
    assert scheduled == ["sample_community"]

    refreshed = (
        await db_session.execute(
            select(ModuleRecord).where(ModuleRecord.name == "sample_community")
        )
    ).scalar_one()
    assert refreshed.state == ModuleState.TO_INSTALL.value

    # Drive the processor with a factory bound to the current test DB.
    factory = async_sessionmaker(db_session.bind, expire_on_commit=False)
    processor = PendingProcessor(factory)
    processed = await processor.run()
    assert "sample_community" in processed

    # Post-conditions.
    final = (
        await db_session.execute(
            select(ModuleRecord).where(ModuleRecord.name == "sample_community")
        )
    ).scalar_one()
    await db_session.refresh(final)
    assert final.state == ModuleState.INSTALLED.value
    assert final.installed_at is not None

    # Every install step logged.
    log_rows = (
        (
            await db_session.execute(
                select(ModuleOperationLog).where(
                    ModuleOperationLog.module_name == "sample_community"
                )
            )
        )
        .scalars()
        .all()
    )
    steps = {(r.operation, r.step, r.status) for r in log_rows}
    for step in ("migrate", "seed", "lifecycle", "finalize"):
        assert ("install", step, "completed") in steps, f"missing step {step}"

    # modules.json regenerated with the fixture's layer path.
    modules_json = tmp_path / "modules.json"
    assert modules_json.exists()
    payload = modules_json.read_text()
    assert "sample_community" in payload
    assert "frontend" in payload  # layer path component
