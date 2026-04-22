"""Parity test: the frontend copy of the status state machine must match
the backend's ``VALID_TRANSITIONS``.

Duplication is intentional — the frontend needs the machine synchronously
to render quick-action buttons, and a dedicated ``GET /status-machine``
endpoint would add a round trip to every appointment view. This test is
the guardrail that keeps the two copies aligned.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.modules.agenda.service import VALID_TRANSITIONS

FRONTEND_COMPOSABLE = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "modules"
    / "agenda"
    / "frontend"
    / "composables"
    / "useAppointmentStatus.ts"
)


def _parse_frontend_machine() -> dict[str, set[str]]:
    text = FRONTEND_COMPOSABLE.read_text()
    # Grab the object literal between the VALID_TRANSITIONS opening brace
    # and the matching closing brace.
    match = re.search(r"VALID_TRANSITIONS:\s*Record<[^>]+>\s*=\s*\{([^}]*)\}", text)
    assert match is not None, "VALID_TRANSITIONS block not found in composable"
    body = match.group(1)

    machine: dict[str, set[str]] = {}
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if not line or line.startswith("//"):
            continue
        key_match = re.match(r"(\w+):\s*\[(.*)\]", line)
        if not key_match:
            continue
        key = key_match.group(1)
        targets_raw = key_match.group(2).strip()
        if not targets_raw:
            machine[key] = set()
            continue
        targets = {t.strip().strip("'\"") for t in targets_raw.split(",") if t.strip()}
        machine[key] = targets
    return machine


def test_frontend_state_machine_matches_backend() -> None:
    frontend = _parse_frontend_machine()
    backend = {k: set(v) for k, v in VALID_TRANSITIONS.items()}
    assert frontend == backend, (
        "Frontend useAppointmentStatus.ts drifted from backend VALID_TRANSITIONS. "
        f"Backend={backend} Frontend={frontend}"
    )
