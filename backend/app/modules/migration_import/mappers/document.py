"""Map ``patient_document`` → register the owning patient for later use.

The DPMF stores file references, never binaries. The `_files` manifest
is persisted as :class:`FileStaging` rows by the service (one pass over
``_files`` after all mappers ran). When the sync agent later POSTs each
binary against ``/jobs/{id}/binaries``, the ingester needs to know
*which patient* the document belongs to. We answer that question by
mapping ``patient_document`` → the resolved ``patients.id``.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from .base import MapperContext

DOCUMENT_ENTITY_TYPE = "patient_document"


class DocumentMapper:
    async def apply(
        self,
        ctx: MapperContext,
        *,
        entity_type: str,
        payload: dict[str, Any],
        raw: dict[str, Any],
        canonical_uuid: str,
        source_id: str,
        source_system: str,
    ) -> UUID | None:
        existing = await ctx.resolver.get(DOCUMENT_ENTITY_TYPE, canonical_uuid)
        if existing is not None:
            return existing

        patient_uuid_external = payload.get("patient_uuid")
        if not patient_uuid_external:
            # Document without an owning patient — useless to us. Let
            # the catch-all mapper persist it as RawEntity instead.
            raise ValueError(f"patient_document {source_id} missing patient_uuid")

        patient_id = await ctx.resolver.get("patient", str(patient_uuid_external))
        if patient_id is None:
            raise ValueError(
                f"patient_document {source_id}: patient {patient_uuid_external} not yet mapped"
            )

        # Store the mapping as (patient_document → patient). The binary
        # ingester reads this to find the patient_id when a sha256 lands.
        # We point dentalpin_table at "patients" because that is what
        # the dentalpin_id resolves to.
        await ctx.resolver.set(
            entity_type=DOCUMENT_ENTITY_TYPE,
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="patients",
            dentalpin_id=patient_id,
        )
        return patient_id
