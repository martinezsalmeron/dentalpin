"""Topological iteration over a DPMF's entity tables.

dental-bridge ships ``docs/migration_order.md`` with the dependency
graph; we encode the same 7-level order here so cross-entity FKs are
resolvable through ``EntityMapping`` by the time a downstream mapper
runs.

Unknown entity types (added in a future DPMF minor) appear at the end —
the catch-all mapper handles them by writing to ``raw_entities``.
"""

from __future__ import annotations

# Per dental-bridge/docs/migration_order.md (7 levels, dependency-safe).
ENTITY_ORDER: tuple[str, ...] = (
    # Level 1 — foundational identity
    "center",
    "professional",
    "user",
    "catalog_item",
    "treatment_catalog_item",
    "treatment_catalog_variant",
    "treatment_phase_template",
    # Level 2 — patient identity
    "patient",
    "client",
    "patient_client_link",
    # Level 3 — schedules
    "work_calendar",
    "work_calendar_day",
    "work_calendar_shift",
    "appointment_recurrence",
    # Level 4 — clinical operations
    "appointment",
    "applied_treatment",
    "applied_treatment_phase",
    "patient_alert",
    "recall",
    "consent",
    "pharmacological_history",
    "prescription",
    "prescription_item",
    "communication",
    # Level 5 — budgets
    "budget",
    "budget_line",
    # Level 6 — receivables
    "debt",
    "payment",
    "debt_payment_application",
    # Level 7 — fiscal
    "fiscal_document",
    "fiscal_document_line",
    # Documents reference rows must come after their parent entities.
    "patient_document",
)


def ordered_entity_types(present: list[str]) -> list[str]:
    """Return ``present`` filtered + sorted per :data:`ENTITY_ORDER`.

    Entities present in the DPMF but not in our order list are appended
    last (alphabetical). The runner's catch-all mapper handles unknown
    ones by writing :class:`RawEntity` rows.
    """
    present_set = set(present)
    ordered = [t for t in ENTITY_ORDER if t in present_set]
    unknown = sorted(t for t in present_set if t not in set(ENTITY_ORDER))
    return ordered + unknown
