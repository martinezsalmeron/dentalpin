"""Map ``patient_client_link`` → sidecar resolver entry for payments.

In Gesdén ``DCobros`` (payments) reference a *client* (``IdCli``), not
the patient directly. Clinics use Clients as payers — the same client
may pay for several patients (family accounts) or one patient may have
multiple billing clients (insurance + self-pay). DentalPin's flat
``Payment.patient_id`` model needs a single patient per payment.

This mapper bridges the M:N. For every ``(patient_uuid, client_uuid)``
pair we register a secondary mapping under the synthetic entity_type
``patient_for_client`` keyed by ``client_uuid`` — the first
registration wins so ``PaymentMapper`` can resolve a client to a
patient_id with one ``resolver.get`` lookup. Ambiguous clients (≥ 2
patients linked) silently keep the first patient and surface a
warning so the operator knows.

The mapper also persists a primary mapping under
``patient_client_link`` (with the row's own canonical UUID) so
re-running an import is a no-op for the link rows themselves.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models import EntityMapping, ImportWarning
from .base import MapperContext

_SIDECAR_TYPE = "patient_for_client"


class PatientClientLinkMapper:
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
        existing = await ctx.resolver.get("patient_client_link", canonical_uuid)
        if existing is not None:
            return existing

        patient_uuid = payload.get("patient_uuid")
        client_uuid = payload.get("client_uuid")
        if not patient_uuid or not client_uuid:
            return None

        patient_id = await ctx.resolver.get("patient", str(patient_uuid))
        if patient_id is None:
            return None

        # 1) Primary mapping — makes the link idempotent on re-import.
        await ctx.resolver.set(
            entity_type="patient_client_link",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="patients",
            dentalpin_id=patient_id,
        )

        # In-memory M:N index so ``PaymentMapper`` can split a single
        # ``PagoCli`` across every patient linked to the payer. The
        # SQL sidecar below (``patient_for_client``) keeps the legacy
        # 1:1 "first wins" mapping for callers that want a single
        # patient_id; the in-memory dict carries the full set.
        ctx.client_to_patients.setdefault(str(client_uuid), []).append(patient_id)

        # 2) Sidecar mapping (``patient_for_client``) for the payment
        # mapper to consult. ``INSERT ... ON CONFLICT DO NOTHING`` keeps
        # the first patient registered per client without raising; an
        # ambiguous client (M:N → 1 patient) is logged so the operator
        # can reconcile manually.
        stmt = (
            pg_insert(EntityMapping)
            .values(
                clinic_id=ctx.clinic_id,
                job_id=ctx.job_id,
                source_system=source_system,
                entity_type=_SIDECAR_TYPE,
                source_canonical_uuid=str(client_uuid),
                dentalpin_table="patients",
                dentalpin_id=patient_id,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    "clinic_id",
                    "source_system",
                    "entity_type",
                    "source_canonical_uuid",
                ]
            )
        )
        result = await ctx.db.execute(stmt)
        if result.rowcount == 0:
            # The client already has a primary patient registered —
            # check whether this is a different patient (ambiguous).
            row = await ctx.db.execute(
                select(EntityMapping.dentalpin_id).where(
                    EntityMapping.clinic_id == ctx.clinic_id,
                    EntityMapping.entity_type == _SIDECAR_TYPE,
                    EntityMapping.source_canonical_uuid == str(client_uuid),
                )
            )
            already = row.scalar_one_or_none()
            if already is not None and already != patient_id:
                ctx.db.add(
                    ImportWarning(
                        job_id=ctx.job_id,
                        entity_type="patient_client_link",
                        source_id=source_id,
                        severity="info",
                        code="patient_client_link.ambiguous_payer",
                        message=(
                            f"Cliente {client_uuid} tiene varios pacientes asociados. "
                            "Los pagos posteriores se atribuirán al primero registrado."
                        ),
                    )
                )

        return patient_id
