"""Tests for the YAML seed loader."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Table,
    delete,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugins.yaml_loader import (
    SeedEntry,
    SeedLoader,
    UnresolvedReferenceError,
    parse_seed_file,
)
from app.database import Base

# Register the demo table with Base.metadata so conftest's
# create_all/drop_all handles it per-test — giving each test a
# clean table and isolating rows.
if "seed_demo_items" not in Base.metadata.tables:
    Table(
        "seed_demo_items",
        Base.metadata,
        Column("id", PG_UUID(as_uuid=True), primary_key=True),
        Column("name", String(100), nullable=False),
        Column("price", Numeric(10, 2), nullable=True),
        Column("qty", Integer, nullable=True),
    )


def test_parse_basic_yaml(tmp_path: Path) -> None:
    path = tmp_path / "data.yaml"
    path.write_text(
        """
- xml_id: demo.item_a
  table: demo_items
  noupdate: false
  values:
    name: "Item A"
    price: 10
- xml_id: demo.item_b
  table: demo_items
  values:
    name: "Item B"
        """.strip()
    )
    entries = parse_seed_file(path)
    assert len(entries) == 2
    assert entries[0].xml_id == "demo.item_a"
    assert entries[0].values["name"] == "Item A"
    assert entries[1].noupdate is False  # default


@pytest.fixture
async def demo_table(db_session: AsyncSession) -> Table:
    table = Base.metadata.tables["seed_demo_items"]
    # Clean slate per test in case another test file also touched it.
    await db_session.execute(delete(table))
    await db_session.commit()
    return table


@pytest.mark.asyncio
async def test_loader_inserts_and_is_idempotent(
    db_session: AsyncSession, demo_table: Table
) -> None:
    entries = [
        SeedEntry(
            xml_id="demo.a",
            table="seed_demo_items",
            values={"name": "Alpha", "price": 10, "qty": 2},
        ),
        SeedEntry(
            xml_id="demo.b",
            table="seed_demo_items",
            values={"name": "Beta", "price": 20, "qty": 5},
        ),
    ]

    loader = SeedLoader(db_session, module_name="demo")
    first = await loader.load(entries)
    await db_session.commit()
    assert set(first.keys()) == {"demo.a", "demo.b"}

    rows = (await db_session.execute(select(demo_table))).all()
    assert len(rows) == 2

    # Second load with updated values: same xml_ids, updated price.
    entries[0] = SeedEntry(
        xml_id="demo.a",
        table="seed_demo_items",
        values={"name": "Alpha", "price": 11, "qty": 2},
    )
    loader = SeedLoader(db_session, module_name="demo")
    second = await loader.load(entries)
    await db_session.commit()

    assert second["demo.a"] == first["demo.a"]
    rows = (await db_session.execute(select(demo_table))).all()
    assert len(rows) == 2  # no duplicates
    updated = await db_session.execute(
        select(demo_table.c.price).where(demo_table.c.id == first["demo.a"])
    )
    assert float(updated.scalar_one()) == 11.0


@pytest.mark.asyncio
async def test_loader_respects_noupdate(db_session: AsyncSession, demo_table: Table) -> None:
    entry = SeedEntry(
        xml_id="demo.locked",
        table="seed_demo_items",
        values={"name": "Locked", "price": 5},
        noupdate=True,
    )
    loader = SeedLoader(db_session, module_name="demo")
    await loader.load([entry])
    await db_session.commit()

    # Try to update — value should stay at 5.
    entry.values["price"] = 999
    loader = SeedLoader(db_session, module_name="demo")
    await loader.load([entry])
    await db_session.commit()

    price = (
        await db_session.execute(select(demo_table.c.price).where(demo_table.c.name == "Locked"))
    ).scalar_one()
    assert float(price) == 5.0


@pytest.mark.asyncio
async def test_loader_raises_on_unresolved_ref(db_session: AsyncSession, demo_table: Table) -> None:
    entry = SeedEntry(
        xml_id="demo.ref",
        table="seed_demo_items",
        values={"name": "$xmlref:does.not.exist"},
    )
    loader = SeedLoader(db_session, module_name="demo")
    with pytest.raises(UnresolvedReferenceError):
        await loader.load([entry])
