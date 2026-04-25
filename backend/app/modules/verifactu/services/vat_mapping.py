"""Per-clinic AEAT VAT classification overrides.

Reads ``verifactu_vat_classifications`` rows and turns them into a
lookup the hook can consult while building the desglose. When a row is
missing for a given ``vat_type_id`` the runtime falls back to
:func:`services.iva_classifier.classify` heuristics — overrides are
opt-in.

The catalog ``vat_types`` table stays country-agnostic on purpose;
adding AEAT taxonomy there would force every other country compliance
module (Italy, France…) to share Spanish concepts. Instead, each
country module ships its own mapping table with the same shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import VerifactuVatClassification
from .iva_classifier import DesgloseClassification, classify


@dataclass(frozen=True)
class ClassificationOverride:
    classification: str
    exemption_cause: str | None


async def load_overrides(
    db: AsyncSession, clinic_id: UUID
) -> dict[UUID, ClassificationOverride]:
    """Return ``{vat_type_id: override}`` for the given clinic."""

    result = await db.execute(
        select(VerifactuVatClassification).where(
            VerifactuVatClassification.clinic_id == clinic_id
        )
    )
    return {
        row.vat_type_id: ClassificationOverride(
            classification=row.classification,
            exemption_cause=row.exemption_cause,
        )
        for row in result.scalars()
    }


def apply_override(
    *,
    vat_rate: Decimal,
    override: ClassificationOverride | None,
) -> DesgloseClassification:
    """Build a ``DesgloseClassification`` honouring the override.

    Falls back to heuristic ``classify`` (for the currently-known case
    where ``is_exento_sanitario`` is encoded as the override being an
    ``E*`` code) when no override is set.
    """

    if override is None:
        # Heuristic: vat_rate>0 → S1, vat_rate=0 → N1.
        # ``is_exento_sanitario`` only kicks in when the caller
        # explicitly tags the line; mapping overrides supersede it
        # so the heuristic only matters for un-mapped vat_types.
        return classify(vat_rate=vat_rate, is_exento_sanitario=False)

    code = override.classification
    if code in ("S1", "S2"):
        # Sujeto, no exento. Tipo impositivo viene del rate; cuota
        # se calcula en el caller (no aquí).
        return DesgloseClassification(
            impuesto="01",
            clave_regimen="01",
            calificacion_operacion=code,
            operacion_exenta=False,
            causa_exencion=None,
            tipo_impositivo=vat_rate if vat_rate > 0 else None,
        )

    if code.startswith("E"):
        # Exenta. La causa explícita gana sobre el code (ambos suelen
        # coincidir, pero permitimos divergencia para casos como E3
        # sin que la causa esté en la lista AEAT estándar).
        cause = override.exemption_cause or code
        return DesgloseClassification(
            impuesto="01",
            clave_regimen="01",
            calificacion_operacion=None,
            operacion_exenta=True,
            causa_exencion=cause,
            tipo_impositivo=None,
        )

    # N1 / N2 — no sujeta. AEAT validation 1237: prohibido emitir
    # TipoImpositivo o CuotaRepercutida.
    return DesgloseClassification(
        impuesto="01",
        clave_regimen="01",
        calificacion_operacion=code,
        operacion_exenta=False,
        causa_exencion=None,
        tipo_impositivo=None,
    )
