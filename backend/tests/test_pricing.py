"""Unit tests for catalog pricing strategies, in particular tiered surface_prices."""

from decimal import Decimal
from types import SimpleNamespace

from app.modules.catalog.pricing import (
    PricingTooth,
    compute_price_snapshot,
)


def _item(
    *,
    default_price: Decimal | None = Decimal("60"),
    pricing_strategy: str = "flat",
    pricing_config: dict | None = None,
    surface_prices: dict | None = None,
) -> SimpleNamespace:
    """Build a lightweight catalog-item stand-in. SimpleNamespace is enough since
    compute_price_snapshot only reads attributes."""
    return SimpleNamespace(
        default_price=default_price,
        pricing_strategy=pricing_strategy,
        pricing_config=pricing_config,
        surface_prices=surface_prices,
    )


def test_flat_strategy_ignores_teeth() -> None:
    item = _item(default_price=Decimal("100"), pricing_strategy="flat")
    teeth = [PricingTooth(surfaces=["O", "M"])]
    assert compute_price_snapshot(item, teeth) == Decimal("100")


def test_per_tooth_multiplies_by_tooth_count() -> None:
    item = _item(default_price=Decimal("80"), pricing_strategy="per_tooth")
    teeth = [PricingTooth(), PricingTooth(), PricingTooth()]
    assert compute_price_snapshot(item, teeth) == Decimal("240")


def test_per_surface_with_tier_map_exact_hit() -> None:
    item = _item(
        default_price=Decimal("60"),
        pricing_strategy="per_surface",
        surface_prices={
            "1": Decimal("60"),
            "2": Decimal("85"),
            "3": Decimal("110"),
            "4": Decimal("125"),
            "5": Decimal("135"),
        },
    )
    # 1 surface → tier "1"
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O"])]) == Decimal("60")
    # 2 surfaces → tier "2"
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O", "M"])]) == Decimal("85")
    # 3 surfaces → tier "3"
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O", "M", "D"])]) == Decimal("110")


def test_per_surface_falls_back_to_nearest_lower_tier() -> None:
    # Only tiers 1 and 3 populated — 2 and 4+ must fall back to the nearest lower.
    item = _item(
        default_price=Decimal("60"),
        pricing_strategy="per_surface",
        surface_prices={"1": Decimal("60"), "3": Decimal("100")},
    )
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O"])]) == Decimal("60")
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O", "M"])]) == Decimal("60")
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O", "M", "D"])]) == Decimal("100")
    # 4 surfaces → no tier 4, nearest lower is 3 → 100
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O", "M", "D", "B"])]) == Decimal(
        "100"
    )


def test_per_surface_without_tier_map_falls_back_to_linear() -> None:
    # Legacy behavior: default_price * total surfaces.
    item = _item(default_price=Decimal("50"), pricing_strategy="per_surface", surface_prices=None)
    teeth = [PricingTooth(surfaces=["O", "M", "D"])]
    assert compute_price_snapshot(item, teeth) == Decimal("150")


def test_per_surface_zero_surfaces_uses_default_price() -> None:
    item = _item(
        default_price=Decimal("60"),
        pricing_strategy="per_surface",
        surface_prices={"1": Decimal("60"), "2": Decimal("85")},
    )
    assert compute_price_snapshot(item, [PricingTooth(surfaces=[])]) == Decimal("60")


def test_per_surface_sums_across_teeth() -> None:
    item = _item(
        default_price=Decimal("60"),
        pricing_strategy="per_surface",
        surface_prices={"1": Decimal("60"), "2": Decimal("85"), "3": Decimal("110")},
    )
    # 2 teeth × 1 surface each = 2 total surfaces → tier "2"
    teeth = [PricingTooth(surfaces=["O"]), PricingTooth(surfaces=["M"])]
    assert compute_price_snapshot(item, teeth) == Decimal("85")


def test_per_surface_count_below_min_tier_uses_min_tier() -> None:
    # If only tier 2+ is populated and n=1, smallest tier ("2") is used.
    item = _item(
        default_price=Decimal("999"),
        pricing_strategy="per_surface",
        surface_prices={"2": Decimal("85"), "3": Decimal("110")},
    )
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O"])]) == Decimal("85")


def test_missing_default_price_returns_none() -> None:
    item = _item(default_price=None, pricing_strategy="per_surface", surface_prices=None)
    assert compute_price_snapshot(item, [PricingTooth(surfaces=["O"])]) is None


def test_per_role_still_works() -> None:
    item = _item(
        default_price=Decimal("300"),
        pricing_strategy="per_role",
        pricing_config={"pillar": 500, "pontic": 400},
    )
    teeth = [
        PricingTooth(role="pillar"),
        PricingTooth(role="pontic"),
        PricingTooth(role="pontic"),
        PricingTooth(role="pillar"),
    ]
    assert compute_price_snapshot(item, teeth) == Decimal("1800")
