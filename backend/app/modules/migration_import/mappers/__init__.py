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

from .applied_treatment import AppliedTreatmentMapper
from .applied_treatment_phase import AppliedTreatmentPhaseMapper
from .appointment import AppointmentMapper
from .base import MapperContext, MappingResolver
from .budget import BudgetMapper
from .budget_line import BudgetLineMapper
from .catalog import CatalogItemMapper
from .catalog_variant import CatalogVariantMapper
from .document import DocumentMapper
from .fiscal_document import FiscalDocumentMapper
from .fiscal_document_line import FiscalDocumentLineMapper
from .patient import PatientMapper
from .patient_alert import PatientAlertMapper
from .patient_client_link import PatientClientLinkMapper
from .payment import PaymentMapper
from .pharmacological_history import PharmacologicalHistoryMapper
from .professional import ProfessionalMapper
from .raw import RawEntityMapper
from .user import UserMapper

PatientMapperInst = PatientMapper()
ProfessionalMapperInst = ProfessionalMapper()
UserMapperInst = UserMapper()
DocumentMapperInst = DocumentMapper()
PaymentMapperInst = PaymentMapper()
FiscalDocumentMapperInst = FiscalDocumentMapper()
FiscalDocumentLineMapperInst = FiscalDocumentLineMapper()
AppointmentMapperInst = AppointmentMapper()
CatalogItemMapperInst = CatalogItemMapper()
CatalogVariantMapperInst = CatalogVariantMapper()
BudgetMapperInst = BudgetMapper()
BudgetLineMapperInst = BudgetLineMapper()
AppliedTreatmentMapperInst = AppliedTreatmentMapper()
AppliedTreatmentPhaseMapperInst = AppliedTreatmentPhaseMapper()
PatientClientLinkMapperInst = PatientClientLinkMapper()
PatientAlertMapperInst = PatientAlertMapper()
PharmacologicalHistoryMapperInst = PharmacologicalHistoryMapper()
FALLBACK_MAPPER = RawEntityMapper()

MAPPERS: dict[str, object] = {
    "patient": PatientMapperInst,
    "professional": ProfessionalMapperInst,
    "user": UserMapperInst,
    "patient_document": DocumentMapperInst,
    "payment": PaymentMapperInst,
    "fiscal_document": FiscalDocumentMapperInst,
    "fiscal_document_line": FiscalDocumentLineMapperInst,
    "appointment": AppointmentMapperInst,
    "treatment_catalog_item": CatalogItemMapperInst,
    "treatment_catalog_variant": CatalogVariantMapperInst,
    "budget": BudgetMapperInst,
    "budget_line": BudgetLineMapperInst,
    "applied_treatment": AppliedTreatmentMapperInst,
    "applied_treatment_phase": AppliedTreatmentPhaseMapperInst,
    "patient_client_link": PatientClientLinkMapperInst,
    "patient_alert": PatientAlertMapperInst,
    "pharmacological_history": PharmacologicalHistoryMapperInst,
}

__all__ = [
    "FALLBACK_MAPPER",
    "MAPPERS",
    "MapperContext",
    "MappingResolver",
]
