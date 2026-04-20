"""Tests for ExternalIdHelper."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugins.external_id import ExternalIdHelper


@pytest.mark.asyncio
async def test_upsert_inserts_then_updates(db_session: AsyncSession) -> None:
    helper = ExternalIdHelper(db_session)
    rec_id = uuid4()

    ref = await helper.upsert(
        module_name="inventory",
        xml_id="inventory.item_a",
        table_name="inventory_items",
        record_id=rec_id,
    )
    assert ref.record_id == rec_id
    assert ref.noupdate is False

    # Upsert again with different table + noupdate flag.
    ref = await helper.upsert(
        module_name="inventory",
        xml_id="inventory.item_a",
        table_name="inventory_items",
        record_id=rec_id,
        noupdate=True,
    )
    assert ref.noupdate is True

    same = await helper.get("inventory", "inventory.item_a")
    assert same is not None
    assert same.noupdate is True


@pytest.mark.asyncio
async def test_list_and_purge_for_module(db_session: AsyncSession) -> None:
    helper = ExternalIdHelper(db_session)
    ids = [uuid4() for _ in range(3)]

    for idx, rid in enumerate(ids):
        await helper.upsert(
            module_name="mod",
            xml_id=f"mod.item_{idx}",
            table_name="any_table",
            record_id=rid,
        )
    await db_session.commit()

    rows = await helper.list_for_module("mod")
    assert len(rows) == 3

    pairs = await helper.purge_for_module("mod")
    await db_session.commit()
    assert [p[1] for p in pairs] == ids
    assert await helper.list_for_module("mod") == []
