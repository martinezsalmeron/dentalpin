"""zstd unwrap layer.

zstd is mandatory for ``.dpm.zst`` and ``.dpm.zst.enc`` layerings.
We stream-decompress into the destination path to keep peak memory
bounded — a multi-GB DPMF must not materialise as one big bytes.
"""

from __future__ import annotations

from pathlib import Path

import zstandard

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"
_READ_CHUNK = 1 << 20  # 1 MiB


def decompress_to(compressed: Path, destination: Path) -> None:
    """Stream-decompress ``compressed`` (zstd) into ``destination``."""
    dctx = zstandard.ZstdDecompressor()
    with compressed.open("rb") as src, destination.open("wb") as dst:
        # copy_stream handles the framing + checksum verification; raises
        # on truncation or bad payload.
        dctx.copy_stream(src, dst, read_size=_READ_CHUNK, write_size=_READ_CHUNK)
