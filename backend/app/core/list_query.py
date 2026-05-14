"""Shared helpers for list endpoints across modules.

Centralises the ``?sort=field:dir`` parsing and the bounded-IDs cap that
the four upgraded list pages (`/patients`, `/budgets`, `/invoices`,
`/payments`) plus the cross-module summary endpoints all need.

Kept deliberately tiny — modules wire the helper into their own router
+ service. No SQLAlchemy session ownership here, just clause builders.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.sql.elements import UnaryExpression

ASC = "asc"
DESC = "desc"
_DIRECTIONS = {ASC, DESC}


def parse_sort(
    value: str | None,
    allow: dict[str, Any],
    default: str,
) -> UnaryExpression:
    """Parse ``field:dir`` against an allow-list of column expressions.

    Args:
        value: The raw ``?sort=`` query param. ``None`` → use ``default``.
        allow: ``{"public_field_name": <sqla column or expr>}``. Public names
            decouple the URL from internal column naming.
        default: Fallback sort, e.g. ``"created_at:desc"``. Must reference a
            field present in ``allow``.

    Returns:
        A SQLAlchemy ``column.asc()`` / ``column.desc()`` clause ready for
        ``query.order_by(...)``.

    Raises:
        HTTPException 422 on unknown field, malformed value or bad direction.
    """
    raw = (value or default).strip()
    if not raw:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty sort value")

    field, _, direction = raw.partition(":")
    field = field.strip()
    direction = (direction or ASC).strip().lower()

    if field not in allow:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(f"Invalid sort field {field!r}. Allowed: {sorted(allow.keys())}"),
        )
    if direction not in _DIRECTIONS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid sort direction {direction!r}. Use 'asc' or 'desc'.",
        )

    col = allow[field]
    return col.asc() if direction == ASC else col.desc()


def cap_ids(ids: list[Any] | None, *, cap: int) -> list[Any] | None:
    """Return ``ids`` unchanged if within the cap, else raise 422.

    Used by endpoints that accept a bounded ID list as a query param or
    body field. ``None`` and ``[]`` pass through (callers decide whether
    those mean "no filter" or "no match").
    """
    if ids is None:
        return None
    if len(ids) > cap:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Too many ids ({len(ids)}); cap is {cap}",
        )
    return ids
