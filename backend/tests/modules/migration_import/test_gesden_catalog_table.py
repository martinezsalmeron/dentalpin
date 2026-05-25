"""Lookup tables for Gesdén ``IdTipoODG`` → DentalPin signals.

Locks in the contract: every documented IdTipoODG resolves, the
infer-on-create signals (clinical_type, scope, surfaces) point at real
DentalPin enums, and the alias expansion handles the most common
Gesdén abbreviations the importer sees in the field.
"""

from __future__ import annotations

from app.modules.migration_import.mappers._gesden_catalog import (
    CATEGORY_MIGRATED,
    GESDEN_ABBREVIATION_ALIASES,
    GESDEN_TIPO_ODG_TO_CATEGORY_KEY,
    GESDEN_TIPO_ODG_TO_CLINICAL_TYPE,
    GESDEN_TIPO_ODG_TO_SCOPE,
    category_key_for_tipo_odg,
    clinical_type_for_tipo_odg,
    expand_aliases,
    pricing_strategy_for,
    requires_surfaces_for_tipo_odg,
    scope_for_tipo_odg,
)
from app.modules.odontogram.constants import TreatmentScope, TreatmentType

_VALID_CLINICAL_TYPES = {t.value for t in TreatmentType}
_VALID_SCOPES = {t.value for t in TreatmentScope}


def test_all_documented_tipo_odg_present() -> None:
    """The 46-value TTipoOdg master must be covered in all three tables."""
    documented = {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        44,
        45,
        46,
    }
    assert documented == GESDEN_TIPO_ODG_TO_CLINICAL_TYPE.keys()
    assert documented == GESDEN_TIPO_ODG_TO_SCOPE.keys()
    assert documented == GESDEN_TIPO_ODG_TO_CATEGORY_KEY.keys()


def test_clinical_types_are_valid_enum_values() -> None:
    """Every non-None clinical_type points at a real TreatmentType."""
    for tipo_odg, clinical in GESDEN_TIPO_ODG_TO_CLINICAL_TYPE.items():
        if clinical is not None:
            assert clinical in _VALID_CLINICAL_TYPES, (tipo_odg, clinical)


def test_scopes_are_valid_enum_values() -> None:
    for tipo_odg, scope in GESDEN_TIPO_ODG_TO_SCOPE.items():
        assert scope in _VALID_SCOPES, (tipo_odg, scope)


def test_category_keys_match_seed() -> None:
    """All category keys must match either a seeded TreatmentCategory or
    the migrated catch-all."""
    seeded = {
        "diagnostico",
        "preventivo",
        "restauradora",
        "endodoncia",
        "periodoncia",
        "cirugia",
        "ortodoncia",
        "estetica",
        "protesis",
        "pediatrica",
        CATEGORY_MIGRATED,
    }
    for tipo_odg, key in GESDEN_TIPO_ODG_TO_CATEGORY_KEY.items():
        assert key in seeded, (tipo_odg, key)


def test_admin_codes_have_no_clinical_type() -> None:
    """Anotación / Nota Económica / Bonos / Primera Visita / Genérico
    are admin entries — they should have no odontogram clinical_type."""
    for admin_code in (9, 10, 11, 12, 13, 14, 42):
        assert GESDEN_TIPO_ODG_TO_CLINICAL_TYPE[admin_code] is None


def test_tooth_state_markers_have_no_clinical_type() -> None:
    """Piezas Iniciales / Posición / Rotación / Pieza Niño / Pieza
    Adulto / SuperNumeraria are tooth-state markers, not treatments."""
    for state_code in (1, 2, 3, 4, 5, 6):
        assert GESDEN_TIPO_ODG_TO_CLINICAL_TYPE[state_code] is None


def test_bridge_is_multi_tooth() -> None:
    assert GESDEN_TIPO_ODG_TO_SCOPE[27] == TreatmentScope.MULTI_TOOTH.value


def test_removable_prosthesis_is_global_arch() -> None:
    assert GESDEN_TIPO_ODG_TO_SCOPE[28] == TreatmentScope.GLOBAL_ARCH.value


def test_globals_marked_as_global_mouth() -> None:
    """Higiene / Panorámica / Teleradio / Fluorización / Genérico are
    whole-mouth (not tooth-specific)."""
    for global_code in (38, 39, 40, 41, 42):
        assert GESDEN_TIPO_ODG_TO_SCOPE[global_code] == TreatmentScope.GLOBAL_MOUTH.value


def test_obturacion_requires_surfaces() -> None:
    assert requires_surfaces_for_tipo_odg(22) is True
    assert requires_surfaces_for_tipo_odg(32) is True  # Sellado
    assert requires_surfaces_for_tipo_odg(33) is True  # Carilla


def test_crown_does_not_require_surfaces() -> None:
    assert requires_surfaces_for_tipo_odg(26) is False


def test_helpers_default_safely_on_unknown() -> None:
    """Unknown / null IdTipoODG falls back to safe defaults that the
    operator can later correct in the UI."""
    assert category_key_for_tipo_odg(None) == CATEGORY_MIGRATED
    assert category_key_for_tipo_odg(999) == CATEGORY_MIGRATED
    assert scope_for_tipo_odg(None) == TreatmentScope.TOOTH.value
    assert scope_for_tipo_odg(999) == TreatmentScope.TOOTH.value
    assert clinical_type_for_tipo_odg(None) is None
    assert clinical_type_for_tipo_odg(999) is None
    assert requires_surfaces_for_tipo_odg(None) is False


def test_pricing_strategy_inference() -> None:
    """Per-surface for fillings (requires_surfaces). Per-tooth for atomic
    per-piece treatments (crown, implant). Flat for the rest."""
    # Obturación composite: requires_surfaces → per_surface
    assert pricing_strategy_for(22, TreatmentType.FILLING_COMPOSITE.value, True) == "per_surface"
    # Corona: per-piece pricing
    assert pricing_strategy_for(26, TreatmentType.CROWN.value, False) == "per_tooth"
    # Implante: per-piece pricing
    assert pricing_strategy_for(24, TreatmentType.IMPLANT.value, False) == "per_tooth"
    # Higiene: global, flat
    assert pricing_strategy_for(38, None, False) == "flat"
    # Endodoncia: per tooth in scope but flat in billing axis
    assert pricing_strategy_for(21, TreatmentType.ROOT_CANAL_FULL.value, False) == "flat"


def test_alias_expansion_basic() -> None:
    out = expand_aliases(["corona", "mc"])
    assert out == ["corona", "metal", "ceramica"]


def test_alias_expansion_preserves_order() -> None:
    out = expand_aliases(["mc", "corona"])
    assert out == ["metal", "ceramica", "corona"]


def test_alias_expansion_passes_unknown_tokens_through() -> None:
    out = expand_aliases(["corona", "zirconio"])
    # ``zirconio`` is not in the alias map (already long form); ``corona``
    # isn't either — both pass through unchanged.
    assert out == ["corona", "zirconio"]


def test_alias_expansion_supports_short_tokens() -> None:
    """Two-letter Gesdén codes must expand; otherwise tokens shorter
    than the meaningful-token cutoff would never reach the matcher."""
    assert expand_aliases(["impl", "ti"]) == ["implante", "titanio"]
    assert expand_aliases(["rx"]) == ["radiografia"]


def test_alias_map_keys_are_normalised() -> None:
    """Alias keys must be lowercase and free of punctuation so that the
    expansion runs against ``_normalise`` output without surprises."""
    for key in GESDEN_ABBREVIATION_ALIASES:
        assert key == key.lower(), key
        assert key.replace(" ", "").isalnum(), key
