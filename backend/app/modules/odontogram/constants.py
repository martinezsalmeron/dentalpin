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
    """Types of dental treatments."""

    # Surface treatments
    CARIES = "caries"
    FILLING = "filling"
    SEALANT = "sealant"

    # Whole tooth treatments
    CROWN = "crown"
    ROOT_CANAL = "root_canal"
    IMPLANT = "implant"
    BRIDGE_PONTIC = "bridge_pontic"
    BRIDGE_ABUTMENT = "bridge_abutment"
    EXTRACTION = "extraction"
    MISSING = "missing"
    FRACTURE = "fracture"
    POST = "post"
    VENEER = "veneer"
    APICOECTOMY = "apicoectomy"

    # Orthodontic treatments
    BRACKET = "bracket"
    BAND = "band"
    ATTACHMENT = "attachment"
    RETAINER = "retainer"


# Treatment type categorization
SURFACE_TREATMENTS: Final[set[str]] = {
    TreatmentType.CARIES.value,
    TreatmentType.FILLING.value,
    TreatmentType.SEALANT.value,
}

WHOLE_TOOTH_TREATMENTS: Final[set[str]] = {
    TreatmentType.CROWN.value,
    TreatmentType.ROOT_CANAL.value,
    TreatmentType.IMPLANT.value,
    TreatmentType.BRIDGE_PONTIC.value,
    TreatmentType.BRIDGE_ABUTMENT.value,
    TreatmentType.EXTRACTION.value,
    TreatmentType.MISSING.value,
    TreatmentType.FRACTURE.value,
    TreatmentType.POST.value,
    TreatmentType.VENEER.value,
    TreatmentType.APICOECTOMY.value,
    # Orthodontic treatments
    TreatmentType.BRACKET.value,
    TreatmentType.BAND.value,
    TreatmentType.ATTACHMENT.value,
    TreatmentType.RETAINER.value,
}


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
