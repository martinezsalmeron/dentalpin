"""Constants for the periodontogram module.

SEPA standard: 6 sites per tooth, permanent dentition only (FDI 11–48).
"""

from enum import StrEnum
from typing import Final

from app.modules.odontogram.constants import PERMANENT_TEETH

# Reuse FDI list from odontogram — periodontogram tracks only permanent teeth.
PERIO_TEETH: Final[list[int]] = list(PERMANENT_TEETH)


class SiteCode(StrEnum):
    """6 probing sites per tooth (SEPA).

    Vestibular face: MV (mesio-vestibular), V (mid-vestibular), DV (disto-vestibular).
    Palatal/lingual face: ML, L, DL.
    """

    MV = "MV"
    V = "V"
    DV = "DV"
    ML = "ML"
    L = "L"
    DL = "DL"


SITE_CODES: Final[list[str]] = [s.value for s in SiteCode]
SITES_PER_TOOTH: Final[int] = len(SITE_CODES)
VESTIBULAR_SITES: Final[tuple[str, str, str]] = (SiteCode.MV, SiteCode.V, SiteCode.DV)
PALATAL_SITES: Final[tuple[str, str, str]] = (SiteCode.ML, SiteCode.L, SiteCode.DL)


class SnapshotStatus(StrEnum):
    DRAFT = "draft"
    CLOSED = "closed"


class Prognosis(StrEnum):
    """Individual tooth prognosis (Miller / McGuire-style)."""

    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    HOPELESS = "hopeless"


class Furcation(StrEnum):
    """Furcation grade (Hamp). N0 means no furcation involvement detected."""

    N0 = "0"
    I = "I"  # noqa: E741 — clinical grade identifier.
    II = "II"
    III = "III"


# Probing depth ranges used for heatmap rendering on the frontend.
# Backend mirrors them only for documentation and validation purposes.
PROBING_DEPTH_MIN: Final[int] = 0
PROBING_DEPTH_MAX: Final[int] = 15
GINGIVAL_MARGIN_MIN: Final[int] = -5
GINGIVAL_MARGIN_MAX: Final[int] = 10
KERATINIZED_GINGIVA_MAX: Final[int] = 20

DEEP_POCKET_THRESHOLD_MM: Final[int] = 5
