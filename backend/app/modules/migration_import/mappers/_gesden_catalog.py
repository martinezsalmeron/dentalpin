"""Gesdén-specific lookup tables for catalog mapping.

This module lives inside ``migration_import`` because DentalPin is a
global project and Gesdén is a Spanish PMS: all Gesdén-flavoured
heuristics must stay isolated to the importer. The destination
``catalog`` schema is untouched — no new columns, no aliases stored on
``TreatmentCatalogItem``.

Three signals are reduced into these tables, all keyed by Gesdén's
``IdTipoODG`` (the 46-value ``TTipoOdg`` master enum):

1. **Clinical type** — DentalPin ``TreatmentType`` enum (or ``None``
   when the Gesdén row is a non-tooth entry like Higiene/Panorámica).
2. **Treatment scope** — ``tooth`` / ``multi_tooth`` / ``global_mouth``
   / ``global_arch``. Drives how the destination catalog item asks
   the clinician for tooth selection.
3. **Category key** — which seeded ``TreatmentCategory`` the new item
   should land in when fuzzy-match against the seed misses. Falling
   back to ``migrado_gesden`` for the genuinely Gesdén-only entries
   (anotación, nota económica, bonos, primera visita).

A fourth signal, the abbreviation alias map, expands the short labels
Gesdén ships in ``DescripAgd`` (e.g. ``OBTUR COMP``, ``CORONA MC``)
into their full Spanish forms before the fuzzy matcher sees them.
Without this expansion the seed entry ``Obturación composite`` never
scores high enough against ``Obtur. Comp.`` to clear the threshold,
even though they are obviously the same treatment.

The tables are intentionally exhaustive over the 46 IdTipoODG values —
a single source of truth shared between ``catalog.py`` (template
import) and ``applied_treatment.py`` (per-event clinical_type).
Untested coverage = silent fallback to ``migrado_gesden``, so the
module load asserts every documented IdTipoODG is present.
"""

from __future__ import annotations

from typing import Final

from app.modules.odontogram.constants import TreatmentScope, TreatmentType

# ---------------------------------------------------------------------------
# Category keys present in catalog/seed.py. Kept as string literals (not an
# enum) because they're the persisted ``TreatmentCategory.key`` column values
# and the catalog module owns the source of truth — duplicating them here as
# an enum would just risk drift.
# ---------------------------------------------------------------------------
CATEGORY_DIAGNOSTIC: Final[str] = "diagnostico"
CATEGORY_PREVENTIVE: Final[str] = "preventivo"
CATEGORY_RESTORATIVE: Final[str] = "restauradora"
CATEGORY_ENDODONTICS: Final[str] = "endodoncia"
CATEGORY_PERIODONTICS: Final[str] = "periodoncia"
CATEGORY_SURGERY: Final[str] = "cirugia"
CATEGORY_ORTHODONTICS: Final[str] = "ortodoncia"
CATEGORY_COSMETIC: Final[str] = "estetica"
CATEGORY_PROSTHETICS: Final[str] = "protesis"
CATEGORY_PEDIATRIC: Final[str] = "pediatrica"
CATEGORY_MIGRATED: Final[str] = "migrado_gesden"


# ---------------------------------------------------------------------------
# IdTipoODG → DentalPin TreatmentType (clinical_type) string.
# ``None`` means "no odontogram-visible clinical type" — global treatments,
# admin entries, tooth-state markers that are pre-existing conditions rather
# than treatments.
# ---------------------------------------------------------------------------
GESDEN_TIPO_ODG_TO_CLINICAL_TYPE: Final[dict[int, str | None]] = {
    # 1-6: tooth state markers (not treatments)
    1: None,  # Piezas Iniciales
    2: None,  # Posición Diente
    3: None,  # Rotación Diente
    4: None,  # Pieza Niño
    5: None,  # Pieza Adulto
    6: None,  # SuperNumeraria
    # 7-8: orthodontic appliances
    7: TreatmentType.BAND.value,
    8: TreatmentType.BRACKET.value,
    # 9-14: admin / non-clinical
    9: None,  # Nuevo Paciente
    10: None,  # Visita No Atendida
    11: None,  # Anotación
    12: None,  # Nota Económica
    13: None,  # Primera Visita
    14: None,  # Bonos
    # 21-37: clinical treatments
    21: TreatmentType.ROOT_CANAL_FULL.value,
    22: TreatmentType.FILLING_COMPOSITE.value,
    23: TreatmentType.APICOECTOMY.value,
    24: TreatmentType.IMPLANT.value,
    25: TreatmentType.POST.value,
    26: TreatmentType.CROWN.value,
    27: TreatmentType.BRIDGE.value,
    28: None,  # Prótesis Removible — global_arch, no per-tooth clinical_type
    29: None,  # Injertos — surgical, no enum yet (periodontal graft)
    30: None,  # Membranas — adjunct to surgery, no enum
    31: None,  # Fibras — adjunct (fiber posts already covered by 25 POST)
    32: TreatmentType.SEALANT.value,
    33: TreatmentType.VENEER.value,
    34: None,  # Raspado — periodontal SRP, no exact enum (closest is FILLING which is wrong)
    35: TreatmentType.EXTRACTION.value,  # Cirugía — most often extraction
    36: TreatmentType.EXTRACTION.value,
    37: TreatmentType.EXTRACTION.value,
    # 38-42: globals (no tooth-level clinical_type)
    38: None,  # Higiene
    39: None,  # Panorámicas
    40: None,  # Teleradio
    41: None,  # Fluorización
    42: None,  # Genérico
    # 44-46: implant lifecycle
    44: TreatmentType.EXTRACTION.value,  # Rechazo Implante (removal)
    45: TreatmentType.EXTRACTION.value,  # Retirada Implante
    46: TreatmentType.IMPLANT.value,  # Reposición Implante
}


# ---------------------------------------------------------------------------
# IdTipoODG → DentalPin treatment_scope. Drives how the destination catalog
# item asks the clinician for tooth selection on the odontogram.
# ---------------------------------------------------------------------------
GESDEN_TIPO_ODG_TO_SCOPE: Final[dict[int, str]] = {
    # 1-6: tooth state — per tooth
    1: TreatmentScope.TOOTH.value,
    2: TreatmentScope.TOOTH.value,
    3: TreatmentScope.TOOTH.value,
    4: TreatmentScope.TOOTH.value,
    5: TreatmentScope.TOOTH.value,
    6: TreatmentScope.TOOTH.value,
    # 7-8: orthodontic appliances — per tooth
    7: TreatmentScope.TOOTH.value,
    8: TreatmentScope.TOOTH.value,
    # 9-14: admin globals
    9: TreatmentScope.GLOBAL_MOUTH.value,
    10: TreatmentScope.GLOBAL_MOUTH.value,
    11: TreatmentScope.GLOBAL_MOUTH.value,
    12: TreatmentScope.GLOBAL_MOUTH.value,
    13: TreatmentScope.GLOBAL_MOUTH.value,
    14: TreatmentScope.GLOBAL_MOUTH.value,
    # 21-37: per-tooth clinical, except bridges (multi-tooth) and removable prosthesis (arch)
    21: TreatmentScope.TOOTH.value,
    22: TreatmentScope.TOOTH.value,
    23: TreatmentScope.TOOTH.value,
    24: TreatmentScope.TOOTH.value,
    25: TreatmentScope.TOOTH.value,
    26: TreatmentScope.TOOTH.value,
    27: TreatmentScope.MULTI_TOOTH.value,
    28: TreatmentScope.GLOBAL_ARCH.value,
    29: TreatmentScope.TOOTH.value,
    30: TreatmentScope.TOOTH.value,
    31: TreatmentScope.TOOTH.value,
    32: TreatmentScope.TOOTH.value,
    33: TreatmentScope.TOOTH.value,
    34: TreatmentScope.TOOTH.value,
    35: TreatmentScope.TOOTH.value,
    36: TreatmentScope.TOOTH.value,
    37: TreatmentScope.TOOTH.value,
    # 38-42: whole-mouth
    38: TreatmentScope.GLOBAL_MOUTH.value,
    39: TreatmentScope.GLOBAL_MOUTH.value,
    40: TreatmentScope.GLOBAL_MOUTH.value,
    41: TreatmentScope.GLOBAL_MOUTH.value,
    42: TreatmentScope.GLOBAL_MOUTH.value,
    # 44-46: implant lifecycle — per tooth
    44: TreatmentScope.TOOTH.value,
    45: TreatmentScope.TOOTH.value,
    46: TreatmentScope.TOOTH.value,
}


# ---------------------------------------------------------------------------
# IdTipoODG → catalog category key. Drives which seeded TreatmentCategory the
# new item lands in when fuzzy match misses. Genuinely Gesdén-only entries
# (anotación, nota económica, bonos) fall into ``migrado_gesden`` for manual
# operator review.
# ---------------------------------------------------------------------------
GESDEN_TIPO_ODG_TO_CATEGORY_KEY: Final[dict[int, str]] = {
    1: CATEGORY_DIAGNOSTIC,
    2: CATEGORY_DIAGNOSTIC,
    3: CATEGORY_DIAGNOSTIC,
    4: CATEGORY_DIAGNOSTIC,
    5: CATEGORY_DIAGNOSTIC,
    6: CATEGORY_DIAGNOSTIC,
    7: CATEGORY_ORTHODONTICS,
    8: CATEGORY_ORTHODONTICS,
    9: CATEGORY_MIGRATED,
    10: CATEGORY_MIGRATED,
    11: CATEGORY_MIGRATED,
    12: CATEGORY_MIGRATED,
    13: CATEGORY_DIAGNOSTIC,
    14: CATEGORY_MIGRATED,
    21: CATEGORY_ENDODONTICS,
    22: CATEGORY_RESTORATIVE,
    23: CATEGORY_SURGERY,
    24: CATEGORY_SURGERY,
    25: CATEGORY_ENDODONTICS,
    26: CATEGORY_RESTORATIVE,
    27: CATEGORY_RESTORATIVE,
    28: CATEGORY_PROSTHETICS,
    29: CATEGORY_SURGERY,  # Injertos — Gesdén label covers bone grafts + sinus lifts more than gingival grafts in real exports
    30: CATEGORY_SURGERY,
    31: CATEGORY_ENDODONTICS,
    32: CATEGORY_PREVENTIVE,
    33: CATEGORY_RESTORATIVE,
    34: CATEGORY_PERIODONTICS,
    35: CATEGORY_SURGERY,
    36: CATEGORY_SURGERY,
    37: CATEGORY_SURGERY,
    38: CATEGORY_PREVENTIVE,
    39: CATEGORY_DIAGNOSTIC,
    40: CATEGORY_DIAGNOSTIC,
    41: CATEGORY_PREVENTIVE,
    42: CATEGORY_MIGRATED,
    44: CATEGORY_SURGERY,
    45: CATEGORY_SURGERY,
    46: CATEGORY_SURGERY,
}


# ---------------------------------------------------------------------------
# IdTipoODG values that imply surface-level selection on the odontogram.
# Mapped to ``requires_surfaces=True`` on the destination catalog item.
# ---------------------------------------------------------------------------
GESDEN_REQUIRES_SURFACES: Final[frozenset[int]] = frozenset(
    {
        22,  # Obturaciones — M/O/D/V/L surfaces
        32,  # Sellado — occlusal (and pits/fissures)
        33,  # Carilla — vestibular
    }
)


# ---------------------------------------------------------------------------
# Clinical types whose natural billing axis is "per tooth" (one charge per
# affected piece). Used to pick pricing_strategy when creating an inferred
# catalog item.
# ---------------------------------------------------------------------------
PER_TOOTH_CLINICAL_TYPES: Final[frozenset[str]] = frozenset(
    {
        TreatmentType.CROWN.value,
        TreatmentType.CROWN_ON_IMPLANT.value,
        TreatmentType.PROVISIONAL_CROWN_ON_IMPLANT.value,
        TreatmentType.VENEER.value,
        TreatmentType.IMPLANT.value,
        TreatmentType.BRACKET.value,
        TreatmentType.BAND.value,
        TreatmentType.TUBE.value,
        TreatmentType.ATTACHMENT.value,
        TreatmentType.SEALANT.value,
    }
)


# ---------------------------------------------------------------------------
# Abbreviation alias map. Token-level: every Gesdén short token on the left
# is rewritten to the longer Spanish form on the right BEFORE the fuzzy
# matcher tokenises. The expansion is applied per token, so order-of-tokens
# in the original label is preserved. Tokens not in the map pass through
# unchanged.
#
# Curated from the most common Gesdén ``DescripAgd`` patterns observed in
# the field. Each entry is a single token (post-normalisation: lowercase,
# accent-stripped, punctuation-collapsed). A token can map to one or more
# replacement tokens.
#
# Examples of expansion this enables:
#   "obtur comp" → "obturacion composite"  matches REST-COMP
#   "corona mc"  → "corona metal ceramica" matches REST-CROWN-MC
#   "endo uni"   → "endodoncia unirradicular" matches ENDO-UNI
#   "impl ti"    → "implante titanio"     matches SURG-IMP-TI
#   "qx tercer"  → "cirugia tercer"       boosts SURG-EXT-3MOLAR
# ---------------------------------------------------------------------------
GESDEN_ABBREVIATION_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    # Restorative
    "obtur": ("obturacion",),
    "obt": ("obturacion",),
    "comp": ("composite",),
    "amalg": ("amalgama",),
    "temp": ("temporal",),
    "prov": ("provisional",),
    "cor": ("corona",),
    "mc": ("metal", "ceramica"),
    "pmf": ("protesis", "metal", "fundida"),
    "zir": ("zirconio",),
    "zirc": ("zirconio",),
    "disi": ("disilicato",),
    "car": ("carilla",),
    "inlay": ("inlay",),
    "over": ("overlay",),
    "fer": ("ferula",),
    # Endodontics
    "endo": ("endodoncia",),
    "uni": ("unirradicular",),
    "bi": ("birradicular",),
    "molar": ("molar",),
    "retrat": ("retratamiento",),
    "pern": ("perno",),
    # Periodontics
    "perio": ("periodontal",),
    "tartrec": ("tartrectomia",),
    "rasp": ("raspado",),
    "rar": ("raspado", "alisado", "radicular"),
    "limp": ("limpieza",),
    # Surgery
    "qx": ("cirugia",),
    "cir": ("cirugia",),
    "ext": ("extraccion",),
    "exo": ("extraccion",),
    "exodoncia": ("extraccion",),
    "extracc": ("extraccion",),
    "cordal": ("tercer", "molar"),
    "impl": ("implante",),
    "ti": ("titanio",),
    "apec": ("apicectomia",),
    "fren": ("frenectomia",),
    "biop": ("biopsia",),
    # Orthodontics
    "orto": ("ortodoncia",),
    "brack": ("brackets",),
    "alin": ("alineadores",),
    "invis": ("invisalign",),
    "ret": ("retenedor",),
    "atach": ("ataches",),
    # Cosmetic / hygiene
    "blanq": ("blanqueamiento",),
    "fluor": ("fluorizacion",),
    # Prosthetics
    "prot": ("protesis",),
    "sup": ("superior",),
    "inf": ("inferior",),
    "esq": ("esqueletica",),
    "acril": ("acrilica",),
    # Diagnostic / general
    "rx": ("radiografia",),
    "rad": ("radiografia",),
    "pan": ("panoramica",),
    "panor": ("panoramica",),
    "minielevacion": ("elevacion",),
    "tele": ("teleradiografia",),
    "cbct": ("cbct",),
    "tac": ("tac",),
    "rev": ("revision",),
    "vis": ("visita",),
    "urg": ("urgencia",),
    "diag": ("diagnostico",),
    "est": ("estudio",),
    # Pediatric
    "ped": ("pediatrico",),
    "pulpot": ("pulpotomia",),
    "pulpec": ("pulpectomia",),
    "sel": ("sellador",),
    "sellado": ("sellador",),
}


def expand_aliases(tokens: list[str]) -> list[str]:
    """Expand tokens through ``GESDEN_ABBREVIATION_ALIASES``.

    Returns a new list. Unknown tokens pass through unchanged. Known
    tokens are replaced by their alias expansion. The original order
    is preserved and per-token expansions are concatenated in place,
    so ``["corona", "mc"]`` → ``["corona", "metal", "ceramica"]``.
    """
    out: list[str] = []
    for tok in tokens:
        replacement = GESDEN_ABBREVIATION_ALIASES.get(tok)
        if replacement is None:
            out.append(tok)
        else:
            out.extend(replacement)
    return out


def category_key_for_tipo_odg(tipo_odg: int | None) -> str:
    """Return the catalog category key for a Gesdén ``IdTipoODG``.

    Unknown / null IdTipoODG values fall back to ``migrado_gesden`` so
    the operator can reclassify manually post-import.
    """
    if tipo_odg is None:
        return CATEGORY_MIGRATED
    return GESDEN_TIPO_ODG_TO_CATEGORY_KEY.get(tipo_odg, CATEGORY_MIGRATED)


def scope_for_tipo_odg(tipo_odg: int | None) -> str:
    """Return the treatment_scope for a Gesdén ``IdTipoODG``.

    Default is ``tooth`` for any unknown value — it's the most common
    scope and forces the operator to confirm tooth selection rather
    than silently dropping a treatment into a non-tooth scope.
    """
    if tipo_odg is None:
        return TreatmentScope.TOOTH.value
    return GESDEN_TIPO_ODG_TO_SCOPE.get(tipo_odg, TreatmentScope.TOOTH.value)


def clinical_type_for_tipo_odg(tipo_odg: int | None) -> str | None:
    """Return the DentalPin ``TreatmentType`` value for a Gesdén
    ``IdTipoODG``, or ``None`` if the row is non-clinical."""
    if tipo_odg is None:
        return None
    return GESDEN_TIPO_ODG_TO_CLINICAL_TYPE.get(tipo_odg)


def requires_surfaces_for_tipo_odg(tipo_odg: int | None) -> bool:
    if tipo_odg is None:
        return False
    return tipo_odg in GESDEN_REQUIRES_SURFACES


def pricing_strategy_for(
    tipo_odg: int | None,
    clinical_type: str | None,
    requires_surfaces: bool,
) -> str:
    """Pick a sensible pricing strategy for an inferred catalog item.

    Per-surface for filling-flavour treatments (surface count drives
    cost). Per-tooth for atomic per-piece treatments (crowns, veneers,
    implants, sealants, brackets). Flat for everything else — globals,
    radiology, hygiene, prosthetics.
    """
    if requires_surfaces:
        return "per_surface"
    if clinical_type and clinical_type in PER_TOOTH_CLINICAL_TYPES:
        return "per_tooth"
    return "flat"


# ---------------------------------------------------------------------------
# Module-load sanity: every documented IdTipoODG must appear in all three
# core tables. Drift would otherwise silently dump entries into
# ``migrado_gesden``.
# ---------------------------------------------------------------------------
_DOCUMENTED_TIPO_ODG: Final[frozenset[int]] = frozenset(
    {
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
)

assert _DOCUMENTED_TIPO_ODG == GESDEN_TIPO_ODG_TO_CLINICAL_TYPE.keys(), (
    "GESDEN_TIPO_ODG_TO_CLINICAL_TYPE drift: "
    f"missing={_DOCUMENTED_TIPO_ODG - GESDEN_TIPO_ODG_TO_CLINICAL_TYPE.keys()} "
    f"extra={GESDEN_TIPO_ODG_TO_CLINICAL_TYPE.keys() - _DOCUMENTED_TIPO_ODG}"
)
assert _DOCUMENTED_TIPO_ODG == GESDEN_TIPO_ODG_TO_SCOPE.keys(), "GESDEN_TIPO_ODG_TO_SCOPE drift"
assert _DOCUMENTED_TIPO_ODG == GESDEN_TIPO_ODG_TO_CATEGORY_KEY.keys(), (
    "GESDEN_TIPO_ODG_TO_CATEGORY_KEY drift"
)
