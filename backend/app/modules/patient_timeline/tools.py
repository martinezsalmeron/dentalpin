"""Agent tools for the patient_timeline module.

Thin wrapper over ``TimelineService`` — no business logic here. Returns
only structured event metadata (type, category, title, timestamp); the
free-text ``description`` and ``event_data`` are omitted so no
un-redactable prose reaches the cloud LLM. Clinic-scoped; RBAC via
``patient_timeline.read``.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.core.agents import AgentContext, Tool, ToolCategory

from .service import TimelineService


class PatientTimelineArgs(BaseModel):
    patient_id: UUID
    limit: int = Field(default=20, ge=1, le=50)


async def _get_patient_timeline(ctx: AgentContext, params: PatientTimelineArgs) -> dict:
    entries, total = await TimelineService.get_timeline(
        ctx.db, ctx.clinic_id, params.patient_id, page=1, page_size=params.limit
    )
    return {
        "total": total,
        "events": [
            {
                "event_type": e.event_type,
                "category": e.event_category,
                "title": e.title,
                "occurred_at": e.occurred_at,
            }
            for e in entries
        ],
    }


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="get_patient_timeline",
            description="Actividad reciente de un paciente (citas, presupuestos, tratamientos…).",
            parameters=PatientTimelineArgs,
            handler=_get_patient_timeline,
            permissions=["patient_timeline.read"],
            category=ToolCategory.READ,
        ),
    ]
