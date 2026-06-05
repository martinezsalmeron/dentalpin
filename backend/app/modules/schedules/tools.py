"""Agent tools for the schedules module.

Thin wrappers over ``AvailabilityService`` — no business logic here.
Clinic-scoped; RBAC via the existing ``schedules.availability.read``.

``get_availability`` returns the clinic's (and optionally a
professional's) **open working windows** for a day — it does NOT subtract
already-booked appointments. To find a truly free gap the agent combines
this with ``agenda.get_day_overview``. See
``docs/technical/copilot-agentic-architecture.md`` §3.
"""

from __future__ import annotations

from datetime import date as date_cls
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.agents import AgentContext, Tool, ToolCategory

from .services.availability import AvailabilityService


class AvailabilityArgs(BaseModel):
    date: date_cls = Field(description="Día a consultar (YYYY-MM-DD).")
    professional_id: UUID | None = Field(
        default=None, description="Opcional: restringe a un profesional."
    )


async def _get_availability(ctx: AgentContext, params: AvailabilityArgs) -> dict:
    tz_name, ranges = await AvailabilityService.resolve(
        ctx.db, ctx.clinic_id, params.date, params.date, params.professional_id
    )
    open_windows = [
        {"start": r.start.isoformat(), "end": r.end.isoformat()}
        for r in ranges
        if r.state == "open"
    ]
    return {"date": params.date.isoformat(), "timezone": tz_name, "open_windows": open_windows}


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="get_availability",
            description=(
                "Ventanas de horario abierto de la clínica (o de un profesional) para un día. "
                "No descuenta citas ya reservadas; combínalo con agenda.get_day_overview para "
                "encontrar huecos libres."
            ),
            parameters=AvailabilityArgs,
            handler=_get_availability,
            permissions=["schedules.availability.read"],
            category=ToolCategory.READ,
        ),
    ]
