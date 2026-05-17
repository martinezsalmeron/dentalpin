"""Topological order — known types ordered per ENTITY_ORDER, unknown last."""

from __future__ import annotations

from app.modules.migration_import.dpmf.iter import ENTITY_ORDER, ordered_entity_types


def test_known_types_keep_dependency_order() -> None:
    out = ordered_entity_types(["payment", "patient", "appointment"])
    assert out == ["patient", "appointment", "payment"]


def test_unknown_types_go_last_alphabetical() -> None:
    out = ordered_entity_types(["patient", "weird_future_entity", "other_future"])
    assert out[0] == "patient"
    assert out[-2:] == ["other_future", "weird_future_entity"]


def test_every_listed_type_known() -> None:
    """Sanity: ENTITY_ORDER has no typos vs the canonical schema list."""
    # spot-check entries
    for required in (
        "center",
        "patient",
        "appointment",
        "budget",
        "payment",
        "fiscal_document",
        "patient_document",
    ):
        assert required in ENTITY_ORDER
