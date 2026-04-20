"""Tests for the ``dentalpin modules`` CLI commands.

Exercises the command handlers directly with the test ``db_session``
fixture, avoiding ``asyncio.run`` re-entrance inside the pytest event
loop. The subprocess path (``python -m app.cli modules list``) is
covered via the parser smoke test plus manual verification.
"""

from __future__ import annotations

import argparse
import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli.__main__ import build_parser
from app.cli.modules import _cmd_doctor, _cmd_info, _cmd_list, _cmd_status
from app.core.plugins.loader import discover_modules
from app.core.plugins.registry import module_registry
from app.core.plugins.service import ModuleService


def _seed_registry() -> None:
    if module_registry.list_modules():
        return
    for module in discover_modules():
        try:
            module_registry.register(module)
        except ValueError:
            pass


@pytest.mark.asyncio
async def test_cli_list_json(db_session: AsyncSession, capsys) -> None:
    _seed_registry()
    await ModuleService(db_session).reconcile_with_db()

    exit_code = await _cmd_list(
        ModuleService(db_session),
        argparse.Namespace(as_json=True),
    )
    assert exit_code == 0

    out = capsys.readouterr().out
    data = json.loads(out)
    names = {entry["name"] for entry in data}
    assert "clinical" in names
    assert "billing" in names


@pytest.mark.asyncio
async def test_cli_list_text_table(db_session: AsyncSession, capsys) -> None:
    _seed_registry()
    await ModuleService(db_session).reconcile_with_db()

    exit_code = await _cmd_list(
        ModuleService(db_session),
        argparse.Namespace(as_json=False),
    )
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "NAME" in out
    assert "clinical" in out


@pytest.mark.asyncio
async def test_cli_info_unknown_returns_nonzero(db_session: AsyncSession, capsys) -> None:
    _seed_registry()
    await ModuleService(db_session).reconcile_with_db()

    exit_code = await _cmd_info(
        ModuleService(db_session),
        argparse.Namespace(name="does-not-exist", as_json=False),
    )
    assert exit_code == 2


@pytest.mark.asyncio
async def test_cli_info_known_module(db_session: AsyncSession, capsys) -> None:
    _seed_registry()
    await ModuleService(db_session).reconcile_with_db()

    exit_code = await _cmd_info(
        ModuleService(db_session),
        argparse.Namespace(name="clinical", as_json=True),
    )
    assert exit_code == 0

    data = json.loads(capsys.readouterr().out)
    assert data["name"] == "clinical"
    assert data["state"] == "installed"


@pytest.mark.asyncio
async def test_cli_status_reports_counts(db_session: AsyncSession, capsys) -> None:
    _seed_registry()
    await ModuleService(db_session).reconcile_with_db()

    exit_code = await _cmd_status(
        ModuleService(db_session),
        argparse.Namespace(as_json=True),
    )
    assert exit_code == 0

    data = json.loads(capsys.readouterr().out)
    assert data["total"] >= 9
    assert data["by_state"].get("installed", 0) >= 9


@pytest.mark.asyncio
async def test_cli_doctor_clean(db_session: AsyncSession, capsys) -> None:
    _seed_registry()
    await ModuleService(db_session).reconcile_with_db()

    exit_code = await _cmd_doctor(
        ModuleService(db_session),
        argparse.Namespace(as_json=True),
    )
    # All modules discovered + reconciled → doctor should be happy.
    assert exit_code == 0

    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_parser_has_modules_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["modules", "list"])
    assert args.command == "modules"
    assert args.modules_command == "list"


def test_parser_supports_all_subcommands() -> None:
    parser = build_parser()
    for cmd in ("list", "info", "status", "doctor"):
        args = parser.parse_args(["modules", cmd] + (["x"] if cmd == "info" else []))
        assert args.modules_command == cmd
