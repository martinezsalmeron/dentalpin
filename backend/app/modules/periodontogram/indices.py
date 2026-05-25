"""SEPA periodontal indices.

PR-1 ships the formulas with a typing-friendly protocol so they can be
imported and unit-tested without depending on the SQLAlchemy models.
PR-3 wires them to the closing endpoint.

Formulas (only sites with ``probing_depth_mm`` recorded count toward the
percentage denominators — empty sites are not measurements):

- BoP % = 100 · #(sites with BoP) / #(measured sites)
- PI %  = 100 · #(sites with plaque) / #(measured sites)
- Mean CAL (mm) = mean(probing_depth + gingival_margin) over sites
  where both values are recorded.
- Deep-pocket count = # of distinct teeth with at least one site with
  ``probing_depth_mm >= threshold`` (default 5 mm).
"""

from __future__ import annotations

from typing import Protocol

from .constants import DEEP_POCKET_THRESHOLD_MM


class SiteLike(Protocol):
    """Structural type covering both ORM rows and pydantic ``SiteValue``."""

    tooth_number: int
    probing_depth_mm: int | None
    gingival_margin_mm: int | None
    bleeding_on_probing: bool
    plaque: bool


def _measured_sites(sites: list[SiteLike]) -> list[SiteLike]:
    return [s for s in sites if s.probing_depth_mm is not None]


def compute_bop_pct(sites: list[SiteLike]) -> float:
    measured = _measured_sites(sites)
    if not measured:
        return 0.0
    return 100.0 * sum(1 for s in measured if s.bleeding_on_probing) / len(measured)


def compute_pi_pct(sites: list[SiteLike]) -> float:
    measured = _measured_sites(sites)
    if not measured:
        return 0.0
    return 100.0 * sum(1 for s in measured if s.plaque) / len(measured)


def compute_cal_mean_mm(sites: list[SiteLike]) -> float:
    cals = [
        s.probing_depth_mm + s.gingival_margin_mm
        for s in sites
        if s.probing_depth_mm is not None and s.gingival_margin_mm is not None
    ]
    if not cals:
        return 0.0
    return sum(cals) / len(cals)


def count_deep_pockets(sites: list[SiteLike], threshold: int = DEEP_POCKET_THRESHOLD_MM) -> int:
    teeth = {
        s.tooth_number
        for s in sites
        if s.probing_depth_mm is not None and s.probing_depth_mm >= threshold
    }
    return len(teeth)


def compute_indices(sites: list[SiteLike]) -> dict[str, float | int]:
    """Bundle of indices persisted on the snapshot at close time."""
    return {
        "bop_pct": round(compute_bop_pct(sites), 2),
        "pi_pct": round(compute_pi_pct(sites), 2),
        "cal_mean_mm": round(compute_cal_mean_mm(sites), 2),
        "deep_pockets_count": count_deep_pockets(sites),
    }
