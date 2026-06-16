"""Declarative spec for module-owned background jobs.

A module declares its periodic jobs by returning :class:`ScheduledJob`
specs from ``BaseModule.get_scheduled_jobs()``. The scheduler
(:mod:`app.core.scheduler`) iterates the *registered* modules and wires
each spec into APScheduler — so an uninstalled module contributes no job
and the scheduler no longer imports module task functions directly
(removes the import-coupling tech debt recorded in ADR 0014).

The spec is deliberately framework-neutral: it carries trigger *args*,
not an APScheduler trigger object, so modules never import APScheduler.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class ScheduledJob:
    """One periodic job a module wants the scheduler to run.

    ``trigger`` selects the APScheduler trigger; ``trigger_args`` are
    passed straight to ``CronTrigger(**trigger_args)`` /
    ``IntervalTrigger(**trigger_args)``. Example::

        ScheduledJob(
            id="expire_budgets",
            func=expire_budgets,
            trigger="cron",
            trigger_args={"hour": 2, "minute": 0},
            name="Expire stale budgets (daily 02:00)",
        )
    """

    id: str
    func: Callable[..., Any]
    trigger: Literal["cron", "interval"]
    name: str
    trigger_args: dict[str, Any] = field(default_factory=dict)
    max_instances: int = 1
