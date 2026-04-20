"""Append-only log of install / uninstall / upgrade steps.

Each step ("migrate", "seed", "lifecycle", "finalize", ...) writes a
``started`` row before the work and flips it to ``completed`` (or
``failed``) afterwards. On process restart the lifespan processor can
use the log to detect crashes mid-operation and decide whether to
retry or bail out.

Every write commits on its own to survive unexpected termination of
the main unit of work.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db_models import ModuleOperationLog

logger = logging.getLogger(__name__)


Operation = str  # install | uninstall | upgrade
Step = str  # migrate | seed | lifecycle | backup | delete_data | migrate_down | finalize
Status = str  # started | completed | failed


@dataclass
class LogEntry:
    id: int
    module_name: str
    operation: Operation
    step: Step
    status: Status
    details: dict[str, Any] | None


class OperationLog:
    """Persistent step log. Each call commits its own transaction.

    The isolated commits are intentional: the main unit of work
    (lifespan processor) keeps a single logical transaction for data
    mutation, but audit rows have to survive rollbacks.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def started(
        self,
        *,
        module_name: str,
        operation: Operation,
        step: Step,
        details: dict[str, Any] | None = None,
    ) -> int:
        async with self._session_factory() as session:
            row = ModuleOperationLog(
                module_name=module_name,
                operation=operation,
                step=step,
                status="started",
                details=details,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            logger.debug(
                "op_log started: module=%s op=%s step=%s id=%s",
                module_name,
                operation,
                step,
                row.id,
            )
            return row.id

    async def completed(self, log_id: int, details: dict[str, Any] | None = None) -> None:
        await self._finalize(log_id, "completed", details)

    async def failed(self, log_id: int, error: str, details: dict[str, Any] | None = None) -> None:
        payload = dict(details or {})
        payload["error"] = error
        await self._finalize(log_id, "failed", payload)

    async def last_for_module(self, db: AsyncSession, module_name: str) -> LogEntry | None:
        result = await db.execute(
            select(ModuleOperationLog)
            .where(ModuleOperationLog.module_name == module_name)
            .order_by(ModuleOperationLog.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return _to_entry(row) if row else None

    async def _finalize(self, log_id: int, status: Status, details: dict[str, Any] | None) -> None:
        async with self._session_factory() as session:
            row = await session.get(ModuleOperationLog, log_id)
            if row is None:
                logger.warning("op_log finalize: missing id=%s (status=%s)", log_id, status)
                return
            row.status = status
            if details is not None:
                merged = dict(row.details or {})
                merged.update(details)
                row.details = merged
            await session.commit()
            logger.debug(
                "op_log %s: id=%s module=%s step=%s", status, log_id, row.module_name, row.step
            )


def _to_entry(row: ModuleOperationLog) -> LogEntry:
    return LogEntry(
        id=row.id,
        module_name=row.module_name,
        operation=row.operation,
        step=row.step,
        status=row.status,
        details=dict(row.details) if row.details else None,
    )
