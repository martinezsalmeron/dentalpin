"""EXIF metadata extraction (currently: capture timestamp).

Server-side single source of truth — clients can hint, but the backend
re-reads on upload so the value matches what's actually in the file.
"""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime

from PIL import ExifTags, Image

logger = logging.getLogger(__name__)


_DATETIME_TAGS = ("DateTimeOriginal", "DateTime", "DateTimeDigitized")
_EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"


def extract_captured_at(file_data: bytes) -> datetime | None:
    """Return the photo's capture timestamp from EXIF, or None.

    The returned datetime is timezone-aware (UTC). EXIF stores naive
    local time without offset; we treat it as UTC because we have no
    better signal. Manual override via the API is the escape hatch.
    """
    try:
        with Image.open(io.BytesIO(file_data)) as img:
            exif = img.getexif()
            if not exif:
                return None
            tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            for tag in _DATETIME_TAGS:
                value = tag_map.get(tag)
                if not value:
                    continue
                if isinstance(value, bytes):
                    value = value.decode("ascii", errors="ignore")
                try:
                    parsed = datetime.strptime(value, _EXIF_DATETIME_FORMAT)
                except ValueError:
                    continue
                return parsed.replace(tzinfo=UTC)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("EXIF extraction skipped: %s", exc)
    return None
