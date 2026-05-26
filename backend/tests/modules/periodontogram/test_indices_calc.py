"""Unit tests for the SEPA periodontal indices formulas."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from app.modules.periodontogram.indices import (
    compute_bop_pct,
    compute_cal_mean_mm,
    compute_indices,
    compute_pi_pct,
    count_deep_pockets,
)


@dataclass
class FakeSite:
    probing_depth_mm: int | None
    gingival_margin_mm: int | None
    bleeding_on_probing: bool = False
    plaque: bool = False


@dataclass
class FakeTooth:
    tooth_number: int
    is_present: bool = True
    sites: list[FakeSite] = field(default_factory=list)


@pytest.fixture
def sample_teeth() -> list[FakeTooth]:
    """Two present teeth (12 theoretical sites) with 4 measured sites
    plus 1 unmeasured. Denominator anchors to 12 — unmeasured counts
    as zero for BoP / PI / CAL.
    """
    return [
        FakeTooth(
            11,
            sites=[
                FakeSite(3, 0, False, False),
                FakeSite(4, 1, True, False),
                FakeSite(5, 1, True, True),
            ],
        ),
        FakeTooth(
            12,
            sites=[
                FakeSite(7, 2, True, True),
                FakeSite(None, None, False, False),
            ],
        ),
    ]


def test_bop_pct_anchors_denominator_to_total_present_sites(
    sample_teeth: list[FakeTooth],
) -> None:
    # 3 bleeders out of 12 theoretical sites (2 present teeth × 6) → 25%.
    assert compute_bop_pct(sample_teeth) == pytest.approx(25.0)


def test_pi_pct_anchors_denominator_to_total_present_sites(
    sample_teeth: list[FakeTooth],
) -> None:
    # 2 plaque sites out of 12 → ~16.67%.
    assert compute_pi_pct(sample_teeth) == pytest.approx(100.0 * 2 / 12)


def test_cal_mean_mm_averages_over_total_sites(sample_teeth: list[FakeTooth]) -> None:
    # CAL per measured site: 3, 5, 6, 9 → sum 23. Denominator 12 → ~1.917.
    assert compute_cal_mean_mm(sample_teeth) == pytest.approx(23 / 12)


def test_count_deep_pockets_counts_distinct_present_teeth(
    sample_teeth: list[FakeTooth],
) -> None:
    # Tooth 11 has a 5-mm site, tooth 12 has a 7-mm site → 2.
    assert count_deep_pockets(sample_teeth) == 2


def test_compute_indices_returns_full_bundle(sample_teeth: list[FakeTooth]) -> None:
    bundle = compute_indices(sample_teeth)
    assert bundle == {
        "bop_pct": 25.0,
        "pi_pct": round(100.0 * 2 / 12, 2),
        "cal_mean_mm": round(23 / 12, 2),
        "deep_pockets_count": 2,
    }


def test_empty_teeth_returns_zero_indices() -> None:
    bundle = compute_indices([])
    assert bundle == {
        "bop_pct": 0.0,
        "pi_pct": 0.0,
        "cal_mean_mm": 0.0,
        "deep_pockets_count": 0,
    }


def test_absent_teeth_drop_out_of_denominator() -> None:
    teeth = [
        FakeTooth(11, is_present=True, sites=[FakeSite(4, 0, True, False)]),
        FakeTooth(12, is_present=False, sites=[FakeSite(8, 4, True, True)]),
    ]
    # Only tooth 11 is present → denominator 6. 1 bleeder → ~16.67%.
    # Absent tooth's deep pocket (PD=8) does NOT count.
    bundle = compute_indices(teeth)
    assert bundle["bop_pct"] == pytest.approx(100.0 / 6, abs=0.01)
    assert bundle["deep_pockets_count"] == 0


def test_only_unmeasured_sites_returns_zero_indices() -> None:
    teeth = [
        FakeTooth(11, sites=[FakeSite(None, None, False, False)]),
        FakeTooth(12, sites=[FakeSite(None, None, False, False)]),
    ]
    bundle = compute_indices(teeth)
    # No bleeders / plaque / CAL → all zero. Denominator (12) is fine
    # but numerators are zero.
    assert bundle == {
        "bop_pct": 0.0,
        "pi_pct": 0.0,
        "cal_mean_mm": 0.0,
        "deep_pockets_count": 0,
    }
