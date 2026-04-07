"""Constants for the odontogram module."""

from enum import StrEnum
from typing import Final

# FDI Notation - Permanent teeth (adults): 11-48
# Quadrant 1 (upper right): 18-17-16-15-14-13-12-11
# Quadrant 2 (upper left): 21-22-23-24-25-26-27-28
# Quadrant 3 (lower left): 38-37-36-35-34-33-32-31
# Quadrant 4 (lower right): 41-42-43-44-45-46-47-48
PERMANENT_TEETH: Final[list[int]] = [
    # Upper right (quadrant 1)
    18,
    17,
    16,
    15,
    14,
    13,
    12,
    11,
    # Upper left (quadrant 2)
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    # Lower left (quadrant 3)
    38,
    37,
    36,
    35,
    34,
    33,
    32,
    31,
    # Lower right (quadrant 4)
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
]

# FDI Notation - Deciduous teeth (children): 51-85
# Quadrant 5 (upper right): 55-54-53-52-51
# Quadrant 6 (upper left): 61-62-63-64-65
# Quadrant 7 (lower left): 75-74-73-72-71
# Quadrant 8 (lower right): 81-82-83-84-85
DECIDUOUS_TEETH: Final[list[int]] = [
    # Upper right (quadrant 5)
    55,
    54,
    53,
    52,
    51,
    # Upper left (quadrant 6)
    61,
    62,
    63,
    64,
    65,
    # Lower left (quadrant 7)
    75,
    74,
    73,
    72,
    71,
    # Lower right (quadrant 8)
    81,
    82,
    83,
    84,
    85,
]

ALL_TEETH: Final[list[int]] = PERMANENT_TEETH + DECIDUOUS_TEETH


class ToothType(StrEnum):
    """Type of tooth dentition."""

    PERMANENT = "permanent"
    DECIDUOUS = "deciduous"


class Surface(StrEnum):
    """Tooth surfaces using standard dental notation."""

    MESIAL = "M"  # Side toward midline
    DISTAL = "D"  # Side away from midline
    OCCLUSAL = "O"  # Chewing surface (molars/premolars) or Incisal (incisors/canines)
    VESTIBULAR = "V"  # Outer surface (toward lips/cheeks)
    LINGUAL = "L"  # Inner surface (toward tongue)


SURFACES: Final[list[str]] = [s.value for s in Surface]


class ToothCondition(StrEnum):
    """Possible conditions for a tooth or surface."""

    HEALTHY = "healthy"
    CARIES = "caries"
    FILLING = "filling"
    CROWN = "crown"
    MISSING = "missing"
    ROOT_CANAL = "root_canal"
    IMPLANT = "implant"
    BRIDGE_PONTIC = "bridge_pontic"
    BRIDGE_ABUTMENT = "bridge_abutment"
    EXTRACTION_INDICATED = "extraction_indicated"
    SEALANT = "sealant"
    FRACTURE = "fracture"


class TreatmentStatus(StrEnum):
    """Status of a tooth treatment."""

    EXISTING = "existing"  # Existing treatment (current state)
    PLANNED = "planned"  # Planned (in budget, to be performed)


class TreatmentCategory(StrEnum):
    """Category of treatment based on what it affects."""

    SURFACE = "surface"  # Affects specific surfaces
    WHOLE_TOOTH = "whole_tooth"  # Affects entire tooth


class TreatmentType(StrEnum):
    """Types of dental treatments organized by clinical category."""

    # Diagnóstico (Diagnostic)
    PULPITIS = "pulpitis"
    CARIES = "caries"
    INCIPIENT_CARIES = "incipient_caries"
    PIGMENTATION = "pigmentation"
    FRACTURE = "fracture"
    MISSING = "missing"
    PERIAPICAL_SMALL = "periapical_small"
    PERIAPICAL_MEDIUM = "periapical_medium"
    PERIAPICAL_LARGE = "periapical_large"
    ROTATED = "rotated"
    DISPLACED = "displaced"
    UNERUPTED = "unerupted"

    # Restauradora (Restorative)
    FILLING_COMPOSITE = "filling_composite"
    FILLING_AMALGAM = "filling_amalgam"
    FILLING_TEMPORARY = "filling_temporary"
    SEALANT = "sealant"
    VENEER = "veneer"
    INLAY = "inlay"
    OVERLAY = "overlay"
    CROWN = "crown"
    PONTIC = "pontic"
    BRIDGE_ABUTMENT = "bridge_abutment"

    # Cirugía (Surgery)
    EXTRACTION = "extraction"
    IMPLANT = "implant"
    APICOECTOMY = "apicoectomy"

    # Endodoncia (Endodontics)
    ROOT_CANAL_FULL = "root_canal_full"
    ROOT_CANAL_TWO_THIRDS = "root_canal_two_thirds"
    ROOT_CANAL_HALF = "root_canal_half"
    POST = "post"
    ROOT_CANAL_OVERFILL = "root_canal_overfill"

    # Ortodoncia (Orthodontics)
    BRACKET = "bracket"
    TUBE = "tube"
    BAND = "band"
    ATTACHMENT = "attachment"
    RETAINER = "retainer"

    # Legacy aliases (for backwards compatibility during migration)
    FILLING = "filling"  # Maps to filling_composite
    ROOT_CANAL = "root_canal"  # Maps to root_canal_full
    BRIDGE_PONTIC = "bridge_pontic"  # Maps to pontic


class VisualizationRule(StrEnum):
    """Visualization rules for rendering treatments."""

    PULP_FILL = "pulp_fill"  # Rule 1: Fill pulp chamber in lateral view
    OCCLUSAL_SURFACE = "occlusal_surface"  # Rule 2: Surface fill/dot in cenital view
    LATERAL_ICON = "lateral_icon"  # Rule 3: SVG icon on lateral view
    PATTERN_FILL = "pattern_fill"  # Rule 4: Pattern fill on cenital view


class TreatmentClinicalCategory(StrEnum):
    """Clinical categories for treatments (used in TreatmentBar)."""

    DIAGNOSTICO = "diagnostico"
    RESTAURADORA = "restauradora"
    CIRUGIA = "cirugia"
    ENDODONCIA = "endodoncia"
    ORTODONCIA = "ortodoncia"


# Treatments by clinical category
TREATMENTS_BY_CATEGORY: Final[dict[str, list[str]]] = {
    TreatmentClinicalCategory.DIAGNOSTICO.value: [
        TreatmentType.PULPITIS.value,
        TreatmentType.CARIES.value,
        TreatmentType.INCIPIENT_CARIES.value,
        TreatmentType.PIGMENTATION.value,
        TreatmentType.FRACTURE.value,
        TreatmentType.MISSING.value,
        TreatmentType.PERIAPICAL_SMALL.value,
        TreatmentType.PERIAPICAL_MEDIUM.value,
        TreatmentType.PERIAPICAL_LARGE.value,
        TreatmentType.ROTATED.value,
        TreatmentType.DISPLACED.value,
        TreatmentType.UNERUPTED.value,
    ],
    TreatmentClinicalCategory.RESTAURADORA.value: [
        TreatmentType.FILLING_COMPOSITE.value,
        TreatmentType.FILLING_AMALGAM.value,
        TreatmentType.FILLING_TEMPORARY.value,
        TreatmentType.SEALANT.value,
        TreatmentType.VENEER.value,
        TreatmentType.INLAY.value,
        TreatmentType.OVERLAY.value,
        TreatmentType.CROWN.value,
        TreatmentType.PONTIC.value,
        TreatmentType.BRIDGE_ABUTMENT.value,
    ],
    TreatmentClinicalCategory.CIRUGIA.value: [
        TreatmentType.EXTRACTION.value,
        TreatmentType.IMPLANT.value,
        TreatmentType.APICOECTOMY.value,
    ],
    TreatmentClinicalCategory.ENDODONCIA.value: [
        TreatmentType.ROOT_CANAL_FULL.value,
        TreatmentType.ROOT_CANAL_TWO_THIRDS.value,
        TreatmentType.ROOT_CANAL_HALF.value,
        TreatmentType.POST.value,
        TreatmentType.ROOT_CANAL_OVERFILL.value,
    ],
    TreatmentClinicalCategory.ORTODONCIA.value: [
        TreatmentType.BRACKET.value,
        TreatmentType.TUBE.value,
        TreatmentType.BAND.value,
        TreatmentType.ATTACHMENT.value,
        TreatmentType.RETAINER.value,
    ],
}


# Visualization rules mapping
TREATMENT_VISUALIZATION_RULES: Final[dict[str, list[str]]] = {
    # Rule 1: Pulp fill (lateral view)
    VisualizationRule.PULP_FILL.value: [
        TreatmentType.PULPITIS.value,
        TreatmentType.ROOT_CANAL_FULL.value,
        TreatmentType.ROOT_CANAL_TWO_THIRDS.value,
        TreatmentType.ROOT_CANAL_HALF.value,
        TreatmentType.ROOT_CANAL_OVERFILL.value,  # Also uses LATERAL_ICON
    ],
    # Rule 2: Occlusal surface (cenital view)
    VisualizationRule.OCCLUSAL_SURFACE.value: [
        TreatmentType.CARIES.value,
        TreatmentType.INCIPIENT_CARIES.value,
        TreatmentType.PIGMENTATION.value,
        TreatmentType.FILLING_COMPOSITE.value,
        TreatmentType.FILLING_AMALGAM.value,
        TreatmentType.FILLING_TEMPORARY.value,
        TreatmentType.SEALANT.value,
        TreatmentType.VENEER.value,
    ],
    # Rule 3: Lateral icon (lateral view)
    VisualizationRule.LATERAL_ICON.value: [
        TreatmentType.FRACTURE.value,
        TreatmentType.MISSING.value,
        TreatmentType.PERIAPICAL_SMALL.value,
        TreatmentType.PERIAPICAL_MEDIUM.value,
        TreatmentType.PERIAPICAL_LARGE.value,
        TreatmentType.ROTATED.value,
        TreatmentType.DISPLACED.value,
        TreatmentType.IMPLANT.value,
        TreatmentType.APICOECTOMY.value,
        TreatmentType.EXTRACTION.value,
        TreatmentType.POST.value,
        TreatmentType.ROOT_CANAL_OVERFILL.value,  # Also uses PULP_FILL
        TreatmentType.BRACKET.value,
        TreatmentType.TUBE.value,
        TreatmentType.BAND.value,
        TreatmentType.ATTACHMENT.value,
        TreatmentType.RETAINER.value,
    ],
    # Rule 4: Pattern fill (cenital view)
    VisualizationRule.PATTERN_FILL.value: [
        TreatmentType.UNERUPTED.value,
        TreatmentType.INLAY.value,
        TreatmentType.PONTIC.value,
        TreatmentType.BRIDGE_ABUTMENT.value,
        TreatmentType.OVERLAY.value,
        TreatmentType.CROWN.value,
    ],
}


# Treatment type categorization (surface vs whole tooth)
SURFACE_TREATMENTS: Final[set[str]] = {
    TreatmentType.CARIES.value,
    TreatmentType.INCIPIENT_CARIES.value,
    TreatmentType.PIGMENTATION.value,
    TreatmentType.FILLING_COMPOSITE.value,
    TreatmentType.FILLING_AMALGAM.value,
    TreatmentType.FILLING_TEMPORARY.value,
    TreatmentType.SEALANT.value,
    TreatmentType.VENEER.value,
    TreatmentType.INLAY.value,
    # Legacy
    TreatmentType.FILLING.value,
}

WHOLE_TOOTH_TREATMENTS: Final[set[str]] = {
    TreatmentType.PULPITIS.value,
    TreatmentType.FRACTURE.value,
    TreatmentType.MISSING.value,
    TreatmentType.PERIAPICAL_SMALL.value,
    TreatmentType.PERIAPICAL_MEDIUM.value,
    TreatmentType.PERIAPICAL_LARGE.value,
    TreatmentType.ROTATED.value,
    TreatmentType.DISPLACED.value,
    TreatmentType.UNERUPTED.value,
    TreatmentType.OVERLAY.value,
    TreatmentType.CROWN.value,
    TreatmentType.PONTIC.value,
    TreatmentType.BRIDGE_ABUTMENT.value,
    TreatmentType.EXTRACTION.value,
    TreatmentType.IMPLANT.value,
    TreatmentType.APICOECTOMY.value,
    TreatmentType.ROOT_CANAL_FULL.value,
    TreatmentType.ROOT_CANAL_TWO_THIRDS.value,
    TreatmentType.ROOT_CANAL_HALF.value,
    TreatmentType.POST.value,
    TreatmentType.ROOT_CANAL_OVERFILL.value,
    TreatmentType.BRACKET.value,
    TreatmentType.TUBE.value,
    TreatmentType.BAND.value,
    TreatmentType.ATTACHMENT.value,
    TreatmentType.RETAINER.value,
    # Legacy
    TreatmentType.ROOT_CANAL.value,
    TreatmentType.BRIDGE_PONTIC.value,
}


# Legacy treatment type mapping (old -> new)
LEGACY_TREATMENT_MAPPING: Final[dict[str, str]] = {
    "filling": TreatmentType.FILLING_COMPOSITE.value,
    "root_canal": TreatmentType.ROOT_CANAL_FULL.value,
    "bridge_pontic": TreatmentType.PONTIC.value,
}


def normalize_treatment_type(treatment_type: str) -> str:
    """Normalize legacy treatment type to new naming.

    Returns the normalized type or the original if not a legacy type.
    """
    return LEGACY_TREATMENT_MAPPING.get(treatment_type, treatment_type)


def get_visualization_rules(treatment_type: str) -> list[str]:
    """Get the visualization rules for a treatment type."""
    rules = []
    normalized = normalize_treatment_type(treatment_type)
    for rule, treatments in TREATMENT_VISUALIZATION_RULES.items():
        if normalized in treatments:
            rules.append(rule)
    return rules


def get_treatment_category(treatment_type: str) -> TreatmentCategory:
    """Determine if a treatment affects surfaces or whole tooth."""
    if treatment_type in SURFACE_TREATMENTS:
        return TreatmentCategory.SURFACE
    return TreatmentCategory.WHOLE_TOOTH


def is_valid_treatment_type(treatment_type: str) -> bool:
    """Check if a treatment type is valid."""
    return treatment_type in SURFACE_TREATMENTS or treatment_type in WHOLE_TOOTH_TREATMENTS


# Color mapping for each condition (for frontend reference)
CONDITION_COLORS: Final[dict[str, str]] = {
    ToothCondition.HEALTHY.value: "#FFFFFF",
    ToothCondition.CARIES.value: "#EF4444",
    ToothCondition.FILLING.value: "#3B82F6",
    ToothCondition.CROWN.value: "#F59E0B",
    ToothCondition.MISSING.value: "#9CA3AF",
    ToothCondition.ROOT_CANAL.value: "#8B5CF6",
    ToothCondition.IMPLANT.value: "#10B981",
    ToothCondition.BRIDGE_PONTIC.value: "#F97316",
    ToothCondition.BRIDGE_ABUTMENT.value: "#FBBF24",
    ToothCondition.EXTRACTION_INDICATED.value: "#DC2626",
    ToothCondition.SEALANT.value: "#06B6D4",
    ToothCondition.FRACTURE.value: "#BE185D",
}


def get_tooth_type(tooth_number: int) -> ToothType:
    """Determine if a tooth is permanent or deciduous based on FDI number."""
    if tooth_number in PERMANENT_TEETH:
        return ToothType.PERMANENT
    elif tooth_number in DECIDUOUS_TEETH:
        return ToothType.DECIDUOUS
    else:
        raise ValueError(f"Invalid tooth number: {tooth_number}")


def is_valid_tooth_number(tooth_number: int) -> bool:
    """Check if a tooth number is valid according to FDI notation."""
    return tooth_number in ALL_TEETH
