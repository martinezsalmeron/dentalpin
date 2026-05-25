"""Unit tests for the SEPA periodontal indices formulas."""

from __future__ import annotations

from dataclasses import dataclass

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
    tooth_number: int
    probing_depth_mm: int | None
    gingival_margin_mm: int | None
    bleeding_on_probing: bool
    plaque: bool


@pytest.fixture
def sample_sites() -> list[FakeSite]:
    """4 measured sites plus 1 unmeasured to exercise the denominator."""
    return [
        FakeSite(11, 3, 0, False, False),
        FakeSite(12, 4, 1, True, False),
        FakeSite(13, 5, 1, True, True),
        FakeSite(14, 7, 2, True, True),
        FakeSite(15, None, None, False, False),  # unmeasured — excluded
    ]


def test_bop_pct_counts_only_measured_sites(sample_sites: list[FakeSite]) -> None:
    # 3 of 4 measured sites bled — 75%.
    assert compute_bop_pct(sample_sites) == pytest.approx(75.0)


def test_pi_pct_counts_only_measured_sites(sample_sites: list[FakeSite]) -> None:
    # 2 of 4 measured sites had plaque — 50%.
    assert compute_pi_pct(sample_sites) == pytest.approx(50.0)


def test_cal_mean_mm_combines_depth_and_margin(sample_sites: list[FakeSite]) -> None:
    # CAL per site: 3, 5, 6, 9 → mean 5.75.
    assert compute_cal_mean_mm(sample_sites) == pytest.approx(5.75)


def test_count_deep_pockets_counts_distinct_teeth(sample_sites: list[FakeSite]) -> None:
    # Sites with PD ≥ 5 are tooth 13 and tooth 14 → 2.
    assert count_deep_pockets(sample_sites) == 2


def test_compute_indices_returns_full_bundle(sample_sites: list[FakeSite]) -> None:
    bundle = compute_indices(sample_sites)
    assert bundle == {
        "bop_pct": 75.0,
        "pi_pct": 50.0,
        "cal_mean_mm": 5.75,
        "deep_pockets_count": 2,
    }


def test_empty_sites_returns_zero_indices() -> None:
    bundle = compute_indices([])
    assert bundle == {
        "bop_pct": 0.0,
        "pi_pct": 0.0,
        "cal_mean_mm": 0.0,
        "deep_pockets_count": 0,
    }


def test_only_unmeasured_sites_returns_zero_indices() -> None:
    sites = [FakeSite(11, None, None, False, False), FakeSite(12, None, None, True, True)]
    bundle = compute_indices(sites)
    # BoP/PI denominator is 0 → 0%. CAL needs both pd+gm → 0.0. No deep pockets.
    assert bundle == {
        "bop_pct": 0.0,
        "pi_pct": 0.0,
        "cal_mean_mm": 0.0,
        "deep_pockets_count": 0,
    }
