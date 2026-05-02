"""Polymorphic attachment owner registry.

A ``MediaAttachment`` row links a ``Document`` to an arbitrary owner
(`(owner_type, owner_id)`). Each consuming module (``clinical_notes``,
``treatment_plan``, future ``consent`` / ``budget`` / etc.) registers
the ``owner_type`` strings it owns plus a resolver that returns the
patient_id for a given owner_id.

Why a registry instead of a hardcoded enum?

1. ``media`` is the lowest module in the dependency stack — it cannot
   import from its consumers without inverting the dependency graph.
2. Consumers already declare ``"media"`` in their manifest depends, so
   them registering here at import time is the right direction.
3. CHECK constraints on ``owner_type`` would tie the schema to a fixed
   set; the registry is dynamic so adding a new module never requires
   a media-side migration.

The registry is process-global (module-level singleton). Re-registering
the same ``owner_type`` overrides the resolver — handy for tests and
hot reload, never a problem in production because each owner_type is
owned by exactly one module.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

PatientResolver = Callable[[AsyncSession, UUID, UUID], Awaitable[UUID | None]]
"""``async (db, clinic_id, owner_id) -> patient_id | None``.

Returns the patient_id the owner row belongs to. None means the owner
does not exist for this clinic. The resolver MUST filter by clinic_id
itself — the registry never injects clinic context beyond passing it.
"""


@dataclass(frozen=True)
class OwnerSpec:
    """Declarative owner_type registration."""

    owner_type: str
    resolver: PatientResolver
    label: str = ""  # Human-readable, used by docs/admin UI; optional.


class AttachmentRegistry:
    """In-memory registry of polymorphic attachment owners."""

    def __init__(self) -> None:
        self._specs: dict[str, OwnerSpec] = {}

    def register(self, spec: OwnerSpec) -> None:
        """Add or replace an owner_type registration."""
        self._specs[spec.owner_type] = spec

    def known_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs.keys()))

    def has(self, owner_type: str) -> bool:
        return owner_type in self._specs

    async def resolve_patient_id(
        self,
        db: AsyncSession,
        clinic_id: UUID,
        owner_type: str,
        owner_id: UUID,
    ) -> UUID | None:
        """Return the patient_id of the owner, or None if it does not exist."""
        spec = self._specs.get(owner_type)
        if spec is None:
            return None
        return await spec.resolver(db, clinic_id, owner_id)


attachment_registry = AttachmentRegistry()
"""Process-global singleton. Import and call ``register()`` from each
consuming module's ``__init__.py``."""
