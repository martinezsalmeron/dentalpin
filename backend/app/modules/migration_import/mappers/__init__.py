"""Mapper registry — one mapper per DPMF entity type.

A mapper is anything with an ``async apply(...)`` method (duck-typed via
:class:`base.Mapper`). The :data:`MAPPERS` dict maps DPMF entity_type →
mapper instance; entries missing from the dict fall back to
:data:`FALLBACK_MAPPER` (writes a :class:`RawEntity` row for forward-compat).

Adding a new mapper:

1. Drop a module under ``mappers/`` with a class implementing
   ``async apply(ctx, *, entity_type, payload, raw, canonical_uuid,
   source_id, source_system)``.
2. Add it to :data:`MAPPERS` below.
3. Ensure the target module is listed in
   ``MigrationImportModule.manifest['depends']`` (unless integration is
   runtime-tolerant like ``verifactu``).
"""

from __future__ import annotations

from .base import MapperContext, MappingResolver
from .document import DocumentMapper
from .fiscal_document import FiscalDocumentMapper
from .patient import PatientMapper
from .payment import PaymentMapper
from .professional import ProfessionalMapper
from .raw import RawEntityMapper

PatientMapperInst = PatientMapper()
ProfessionalMapperInst = ProfessionalMapper()
DocumentMapperInst = DocumentMapper()
PaymentMapperInst = PaymentMapper()
FiscalDocumentMapperInst = FiscalDocumentMapper()
FALLBACK_MAPPER = RawEntityMapper()

MAPPERS: dict[str, object] = {
    "patient": PatientMapperInst,
    "professional": ProfessionalMapperInst,
    "patient_document": DocumentMapperInst,
    "payment": PaymentMapperInst,
    "fiscal_document": FiscalDocumentMapperInst,
}

__all__ = [
    "FALLBACK_MAPPER",
    "MAPPERS",
    "MapperContext",
    "MappingResolver",
]
