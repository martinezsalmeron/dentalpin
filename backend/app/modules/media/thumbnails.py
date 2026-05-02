"""Thumbnail generation for the media module.

Photos and X-rays are precomputed into three sizes on upload:

- ``thumb``  — 256px max edge, JPEG quality 80, used in grid cards.
- ``medium`` — 1024px max edge, JPEG quality 85, used in lightbox preview.
- ``full``   — original bytes, untouched.

The original is preserved so we never lose source quality. Thumbnails
are written alongside via ``{path}.thumb.jpg`` / ``{path}.medium.jpg``
suffixes — this works for any ``StorageBackend`` because we only use
``store(bytes, path)`` (no path schema knowledge).

Pillow handles JPEG / PNG / WebP / HEIC* (HEIC requires pillow-heif but
we accept the MIME so iOS uploads land; if Pillow can't open it, we
skip thumbnails and the gallery falls back to the original — never a
hard failure).
"""

from __future__ import annotations

import io
import logging
from collections.abc import Awaitable, Callable

from PIL import Image, ImageOps

from .storage import StorageBackend

logger = logging.getLogger(__name__)

THUMB_SIZE = (256, 256)
MEDIUM_SIZE = (1024, 1024)

THUMB_SUFFIX = ".thumb.jpg"
MEDIUM_SUFFIX = ".medium.jpg"

# MIME types we attempt to thumbnail. Anything else is skipped silently.
THUMBNAILABLE_MIME = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
        "image/gif",
    }
)


def is_thumbnailable(mime_type: str) -> bool:
    return mime_type.lower() in THUMBNAILABLE_MIME


def _render(file_data: bytes, size: tuple[int, int], quality: int) -> bytes | None:
    """Return JPEG bytes of ``file_data`` resized to fit ``size``.

    Returns None if Pillow cannot decode the input — caller logs and
    skips.
    """
    try:
        with Image.open(io.BytesIO(file_data)) as img:
            # Apply EXIF rotation so portrait phone photos display
            # correctly without per-client rotation logic.
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.thumbnail(size, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            return buf.getvalue()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Thumbnail generation failed: %s", exc)
        return None


async def store_thumbnails(
    storage: StorageBackend,
    base_path: str,
    file_data: bytes,
    mime_type: str,
) -> dict[str, str]:
    """Generate + store thumb and medium next to ``base_path``.

    Returns a dict with keys ``thumb`` and ``medium`` mapping to the
    storage paths actually written. Missing keys mean that size could
    not be generated (caller falls back to the original).
    """
    if not is_thumbnailable(mime_type):
        return {}

    written: dict[str, str] = {}

    thumb_bytes = _render(file_data, THUMB_SIZE, quality=80)
    if thumb_bytes is not None:
        thumb_path = f"{base_path}{THUMB_SUFFIX}"
        await storage.store(thumb_bytes, thumb_path)
        written["thumb"] = thumb_path

    medium_bytes = _render(file_data, MEDIUM_SIZE, quality=85)
    if medium_bytes is not None:
        medium_path = f"{base_path}{MEDIUM_SUFFIX}"
        await storage.store(medium_bytes, medium_path)
        written["medium"] = medium_path

    return written


# Type alias for an injected thumbnail generator (lets tests stub Pillow
# without monkeypatching the module-level function).
ThumbnailGenerator = Callable[[StorageBackend, str, bytes, str], Awaitable[dict[str, str]]]
