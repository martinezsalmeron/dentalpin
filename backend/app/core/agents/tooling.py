"""Shared helpers for tool handlers.

The single coercion point for tool results. Handlers return native
values (UUID, Decimal, datetime/date, Pydantic models, nested dicts/
lists); :func:`jsonify` is applied once at the registry chokepoint so
the result is JSONB-safe for persistence + audit and ready for the
redactor (which tokenizes by key name — ``jsonify`` preserves keys).

This keeps tool modules free of repetitive ``str(uuid)`` /
``.isoformat()`` / ``float(Decimal)`` boilerplate. Field selection /
stripping (e.g. the off-books axis separation) stays explicit in each
handler — ``jsonify`` only coerces types, it never drops fields.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


def jsonify(obj: Any) -> Any:
    """Recursively coerce a value into JSON/JSONB-safe primitives."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Decimal):
        return float(obj)
    # datetime is a subclass of date; isoformat() is right for both.
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, BaseModel):
        return jsonify(obj.model_dump())
    if isinstance(obj, dict):
        return {str(k): jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [jsonify(v) for v in obj]
    return str(obj)
