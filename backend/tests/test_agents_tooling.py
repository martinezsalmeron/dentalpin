"""jsonify helper + the tool-contract guard.

The guard converts two latent debts into checked contracts:
* every permission a tool declares must actually exist (no typo/drift);
* every registered tool's result coerces to JSON via ``jsonify``.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel

from app.core.agents.tooling import jsonify
from app.core.agents.tools.registry import tool_registry
from app.core.auth.permissions import CORE_PERMISSIONS
from app.core.plugins.registry import module_registry


class _Model(BaseModel):
    n: int
    when: datetime


def test_jsonify_coerces_native_types() -> None:
    uid = uuid4()
    now = datetime(2026, 6, 5, 10, 30, tzinfo=UTC)
    payload = {
        "id": uid,
        "amount": Decimal("12.50"),
        "when": now,
        "day": date(2026, 1, 2),
        "nested": [{"x": uid}, {"y": Decimal("1")}],
        "model": _Model(n=1, when=now),
        "ok": True,
        "nothing": None,
    }
    out = jsonify(payload)
    # Round-trips through json without error.
    json.dumps(out)
    assert out["id"] == str(uid)
    assert out["amount"] == 12.5
    assert out["when"] == now.isoformat()
    assert out["day"] == "2026-01-02"
    assert out["nested"][0]["x"] == str(uid)
    assert out["model"] == {"n": 1, "when": now.isoformat()}


def test_jsonify_passthrough_primitives() -> None:
    assert jsonify("x") == "x"
    assert jsonify(3) == 3
    assert jsonify(None) is None


def test_every_tool_permission_exists() -> None:
    """No tool may gate on a permission the system doesn't know — catches
    typos and renames that would otherwise silently always-deny."""
    known = set(module_registry.get_all_permissions()) | set(CORE_PERMISSIONS)
    for name in tool_registry.list():
        tool = tool_registry.get(name)
        assert tool is not None
        for perm in tool.permissions:
            assert perm in known, f"tool {name!r} declares unknown permission {perm!r}"
