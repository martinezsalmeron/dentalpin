"""Pydantic schemas for the periodontogram module.

PR-1 ships the skeleton only — service/router endpoints are added in PR-2.
The shapes below define the public contract referenced in
``docs/technical/periodontogram-plan.md`` §7.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .constants import SITE_CODES, SnapshotStatus

SiteCodeLiteral = Literal["MV", "V", "DV", "ML", "L", "DL"]
PrognosisLiteral = Literal["good", "fair", "poor", "hopeless"]
FurcationLiteral = Literal["0", "I", "II", "III"]


class SiteValue(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_code: SiteCodeLiteral
    probing_depth_mm: int | None = Field(None, ge=0, le=15)
    gingival_margin_mm: int | None = Field(None, ge=-5, le=10)
    bleeding_on_probing: bool = False
    plaque: bool = False
    suppuration: bool = False


class SitePatch(BaseModel):
    """Patch payload for ``PATCH /sites/{site_code}``. All fields optional."""

    probing_depth_mm: int | None = Field(default=None, ge=0, le=15)
    gingival_margin_mm: int | None = Field(default=None, ge=-5, le=10)
    bleeding_on_probing: bool | None = None
    plaque: bool | None = None
    suppuration: bool | None = None


class ToothValue(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tooth_number: int = Field(..., ge=11, le=48)
    is_present: bool = True
    is_implant: bool = False
    mobility: int | None = Field(None, ge=0, le=3)
    prognosis: PrognosisLiteral | None = None
    furcation_buccal: FurcationLiteral | None = None
    furcation_lingual: FurcationLiteral | None = None
    keratinized_gingiva_mm: int | None = Field(None, ge=0, le=20)
    sites: list[SiteValue] = Field(default_factory=list)


class ToothPatch(BaseModel):
    """Patch payload for ``PATCH /teeth/{tooth_number}``. All fields optional."""

    is_present: bool | None = None
    is_implant: bool | None = None
    mobility: int | None = Field(default=None, ge=0, le=3)
    prognosis: PrognosisLiteral | None = None
    furcation_buccal: FurcationLiteral | None = None
    furcation_lingual: FurcationLiteral | None = None
    keratinized_gingiva_mm: int | None = Field(default=None, ge=0, le=20)


class IndicesResponse(BaseModel):
    bop_pct: float
    pi_pct: float
    cal_mean_mm: float
    deep_pockets_count: int


class SnapshotSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    status: Literal["draft", "closed"]
    recorded_at: datetime
    closed_at: datetime | None = None


class SnapshotDetail(SnapshotSummary):
    recorded_by: UUID
    closed_by: UUID | None = None
    notes: str | None = None
    indices: IndicesResponse | None = None
    teeth: list[ToothValue] = Field(default_factory=list)


class TimelineEntry(BaseModel):
    snapshot_id: UUID
    date: str  # ISO date YYYY-MM-DD aligned with the odontogram TimelineSlider props.
    change_count: int


class TimelineResponse(BaseModel):
    dates: list[TimelineEntry]
    draft: SnapshotSummary | None = None


__all__ = [
    "IndicesResponse",
    "SITE_CODES",
    "SitePatch",
    "SiteValue",
    "SnapshotDetail",
    "SnapshotStatus",
    "SnapshotSummary",
    "TimelineEntry",
    "TimelineResponse",
    "ToothPatch",
    "ToothValue",
]
