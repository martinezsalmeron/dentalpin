"""Attachment owner resolver for the treatment_plan module.

Registers the ``plan_item`` owner_type with ``media.attachment_registry``
so any document can be attached to a planned treatment item via the
generic media endpoints.

Plans themselves are registered by the ``clinical_notes`` module as
``plan`` (because that's where the note polymorphism started). Adding
``plan`` here too would just shadow the same resolver — the registry
is keyed by owner_type and the last writer wins, but both modules
agree on the resolution semantics so this is harmless either way.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.media.attachment_registry import OwnerSpec, attachment_registry

from .models import PlannedTreatmentItem, TreatmentPlan


async def _resolve_plan_item(db: AsyncSession, clinic_id: UUID, owner_id: UUID) -> UUID | None:
    """plan_item → patient_id via the parent treatment_plan."""
    result = await db.execute(
        select(TreatmentPlan.patient_id)
        .join(PlannedTreatmentItem, PlannedTreatmentItem.treatment_plan_id == TreatmentPlan.id)
        .where(
            PlannedTreatmentItem.id == owner_id,
            PlannedTreatmentItem.clinic_id == clinic_id,
            TreatmentPlan.deleted_at.is_(None),
        )
    )
    row = result.first()
    return row[0] if row else None


def register() -> None:
    attachment_registry.register(
        OwnerSpec(
            owner_type="plan_item",
            resolver=_resolve_plan_item,
            label="Tratamiento del plan",
        )
    )
