"""Photo / media taxonomy for the media module.

Single source of truth for the controlled vocabulary describing what
kind of file a Document is, and (for clinical photos and X-rays) which
dental category and subtype it belongs to.

Validation lives here so the API layer stays thin. If a future module
needs to extend the taxonomy, swap this for a registry — the API call
sites only depend on ``validate_media_classification``.
"""

from __future__ import annotations

from fastapi import HTTPException, status

# Top-level kind. Drives the UI gallery rail and the thumbnail pipeline.
MEDIA_KIND_DOCUMENT = "document"
MEDIA_KIND_PHOTO = "photo"
MEDIA_KIND_XRAY = "xray"
MEDIA_KIND_SCAN = "scan"
MEDIA_KIND_VIDEO = "video"

MEDIA_KINDS: tuple[str, ...] = (
    MEDIA_KIND_DOCUMENT,
    MEDIA_KIND_PHOTO,
    MEDIA_KIND_XRAY,
    MEDIA_KIND_SCAN,
    MEDIA_KIND_VIDEO,
)

# Categories. Only meaningful when kind ∈ {photo, xray}.
MEDIA_CATEGORIES: tuple[str, ...] = (
    "intraoral",
    "extraoral",
    "xray",
    "clinical",
    "other",
)

# Subtypes per category. Hardcoded here; if a clinic asks for more,
# add them to this map. Validation rejects anything else.
MEDIA_SUBTYPES: dict[str, tuple[str, ...]] = {
    "intraoral": (
        "frontal",
        "lateral_left",
        "lateral_right",
        "occlusal_upper",
        "occlusal_lower",
        "palatal",
        "lingual",
    ),
    "extraoral": (
        "profile_left",
        "profile_right",
        "frontal_face",
        "smile",
        "rest",
        "three_quarter_left",
        "three_quarter_right",
    ),
    "xray": (
        "panoramic",
        "periapical",
        "bitewing",
        "cephalometric_lateral",
        "cephalometric_pa",
        "cbct",
        "occlusal_xray",
    ),
    "clinical": (
        "before",
        "after",
        "progress",
        "reference",
    ),
    "other": (
        "portrait",
        "document_scan",
        "model_photo",
    ),
}


def validate_media_classification(
    media_kind: str,
    media_category: str | None,
    media_subtype: str | None,
) -> None:
    """Raise 400 if the (kind, category, subtype) triple is invalid.

    Rules:
    - kind must be in MEDIA_KINDS
    - kind=document/scan/video → category and subtype must be None
    - kind=photo → category required (any except 'xray'), subtype optional
      but when present must belong to category
    - kind=xray → category must be 'xray', subtype optional but when
      present must belong to 'xray'
    """
    if media_kind not in MEDIA_KINDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid media_kind '{media_kind}'. Allowed: {', '.join(MEDIA_KINDS)}",
        )

    if media_kind in (MEDIA_KIND_DOCUMENT, MEDIA_KIND_SCAN, MEDIA_KIND_VIDEO):
        if media_category is not None or media_subtype is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"media_kind '{media_kind}' must not carry category/subtype",
            )
        return

    if media_kind == MEDIA_KIND_XRAY:
        if media_category not in (None, "xray"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="media_kind 'xray' requires media_category='xray' or null",
            )
        category = "xray"
    else:  # photo
        if media_category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="media_kind 'photo' requires media_category",
            )
        if media_category == "xray":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use media_kind='xray' for radiographs, not photo+category=xray",
            )
        if media_category not in MEDIA_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid media_category '{media_category}'. "
                    f"Allowed: {', '.join(MEDIA_CATEGORIES)}"
                ),
            )
        category = media_category

    if media_subtype is not None and media_subtype not in MEDIA_SUBTYPES[category]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid media_subtype '{media_subtype}' for category '{category}'. "
                f"Allowed: {', '.join(MEDIA_SUBTYPES[category])}"
            ),
        )
