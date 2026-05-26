"""SEPA periodontal indices.

Denominators are anchored to the **theoretical** site count of every
present tooth (six sites per tooth — MV/V/DV/ML/L/DL), not just the
sites the dentist has filled in. A half-finished exam should not report
inflated percentages; unmeasured sites count as "no finding" (0) until
proven otherwise.

Formulas (with ``total_sites = 6 × #(present teeth)``):

- BoP %        = 100 · #(sites with BoP)   / total_sites
- PI %         = 100 · #(sites with plaque)/ total_sites
- Mean CAL (mm)= Σ(probing_depth + gingival_margin where both present)
                 / total_sites
- Deep-pocket count = # of distinct present teeth with at least one
  site whose ``probing_depth_mm >= threshold`` (default 5 mm).

Implants are still counted as present; clinical probing is performed
around fixtures. Teeth flagged ``is_present=False`` (extracted, missing)
contribute neither numerator nor denominator.
"""

from __future__ import annotations

from typing import Protocol

from .constants import DEEP_POCKET_THRESHOLD_MM, SITES_PER_TOOTH


class SiteLike(Protocol):
    """Structural type covering ORM rows and pydantic ``SiteValue``."""

    probing_depth_mm: int | None
    gingival_margin_mm: int | None
    bleeding_on_probing: bool
    plaque: bool


class ToothLike(Protocol):
    """Structural type covering ORM rows and pydantic ``PerioTooth``."""

    tooth_number: int
    is_present: bool
    sites: list[SiteLike]


def _present_teeth(teeth: list[ToothLike]) -> list[ToothLike]:
    return [t for t in teeth if t.is_present]


def _total_sites(teeth: list[ToothLike]) -> int:
    return SITES_PER_TOOTH * len(_present_teeth(teeth))


def compute_bop_pct(teeth: list[ToothLike]) -> float:
    total = _total_sites(teeth)
    if total == 0:
        return 0.0
    bleeders = sum(1 for t in _present_teeth(teeth) for s in t.sites if s.bleeding_on_probing)
    return 100.0 * bleeders / total


def compute_pi_pct(teeth: list[ToothLike]) -> float:
    total = _total_sites(teeth)
    if total == 0:
        return 0.0
    plaqued = sum(1 for t in _present_teeth(teeth) for s in t.sites if s.plaque)
    return 100.0 * plaqued / total


def compute_cal_mean_mm(teeth: list[ToothLike]) -> float:
    total = _total_sites(teeth)
    if total == 0:
        return 0.0
    cal_sum = sum(
        s.probing_depth_mm + s.gingival_margin_mm
        for t in _present_teeth(teeth)
        for s in t.sites
        if s.probing_depth_mm is not None and s.gingival_margin_mm is not None
    )
    return cal_sum / total


def count_deep_pockets(teeth: list[ToothLike], threshold: int = DEEP_POCKET_THRESHOLD_MM) -> int:
    return sum(
        1
        for t in _present_teeth(teeth)
        if any(s.probing_depth_mm is not None and s.probing_depth_mm >= threshold for s in t.sites)
    )


def compute_indices(teeth: list[ToothLike]) -> dict[str, float | int]:
    """Bundle of indices persisted on the snapshot at close time."""
    return {
        "bop_pct": round(compute_bop_pct(teeth), 2),
        "pi_pct": round(compute_pi_pct(teeth), 2),
        "cal_mean_mm": round(compute_cal_mean_mm(teeth), 2),
        "deep_pockets_count": count_deep_pockets(teeth),
    }
