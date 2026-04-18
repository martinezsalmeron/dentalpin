"""Pricing strategies for computing a Treatment's price_snapshot from a CatalogItem.

Strategies:
- flat:        default_price as-is, ignoring tooth count.
- per_tooth:   default_price * teeth.length.
- per_surface: tiered lookup in surface_prices by total surface count. Falls back
               to the highest populated tier <= count. If surface_prices is empty,
               falls back to default_price * count (legacy linear behavior).
- per_role:    sum of pricing_config[role] across teeth; default_price is used
               when no role is set or the role is missing from the config.
"""

from dataclasses import dataclass
from decimal import Decimal

from .models import TreatmentCatalogItem


@dataclass(frozen=True)
class PricingTooth:
    """Lightweight tooth description used by the pricing computation."""

    role: str | None = None
    surfaces: list[str] | None = None


def _resolve_surface_tier_price(
    surface_prices: dict, surface_count: int, fallback: Decimal
) -> Decimal:
    """Pick the price for `surface_count` from the tier map.

    Highest populated tier <= count wins. If count < min populated tier, the
    smallest tier is used. Returns fallback if the map is empty.
    """
    if not surface_prices:
        return fallback
    try:
        keys = sorted(int(k) for k in surface_prices.keys())
    except (TypeError, ValueError):
        return fallback
    if not keys:
        return fallback
    tier = keys[0]
    for k in keys:
        if k <= surface_count:
            tier = k
        else:
            break
    return Decimal(str(surface_prices[str(tier)]))


def compute_price_snapshot(
    catalog_item: TreatmentCatalogItem,
    teeth: list[PricingTooth],
) -> Decimal | None:
    """Compute the price snapshot for a Treatment built from this catalog item.

    Returns None if the catalog item has no default_price. Teeth may be empty for
    global treatments (e.g. a full-mouth cleaning), which always resolves to flat.
    """
    base = catalog_item.default_price
    if base is None:
        return None

    strategy = catalog_item.pricing_strategy or "flat"

    if strategy == "flat" or not teeth:
        return Decimal(base)

    if strategy == "per_tooth":
        return Decimal(base) * len(teeth)

    if strategy == "per_surface":
        surface_count = sum(len(t.surfaces or []) for t in teeth)
        if surface_count == 0:
            return Decimal(base)
        surface_prices = getattr(catalog_item, "surface_prices", None)
        if surface_prices:
            return _resolve_surface_tier_price(surface_prices, surface_count, Decimal(base))
        return Decimal(base) * surface_count

    if strategy == "per_role":
        config = catalog_item.pricing_config or {}
        total = Decimal("0")
        for tooth in teeth:
            role_price = config.get(tooth.role) if tooth.role else None
            total += Decimal(str(role_price)) if role_price is not None else Decimal(base)
        return total

    raise ValueError(f"Unknown pricing strategy: {strategy!r}")


def compute_duration_snapshot(
    catalog_item: TreatmentCatalogItem,
    teeth_count: int,
) -> int | None:
    """Compute the duration snapshot in minutes.

    Mirrors the pricing strategy: per-tooth strategies scale duration; others use
    the raw default duration. Kept separate because scheduling may want independent
    control in the future.
    """
    if catalog_item.default_duration_minutes is None:
        return None

    strategy = catalog_item.pricing_strategy or "flat"
    if strategy in ("per_tooth", "per_role") and teeth_count > 1:
        return catalog_item.default_duration_minutes * teeth_count
    return catalog_item.default_duration_minutes
