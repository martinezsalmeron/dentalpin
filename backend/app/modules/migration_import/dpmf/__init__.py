"""DPMF reader — magic-byte detection, crypto, compression, integrity.

The public surface used by the rest of the module is:

- :class:`Layering` — enum-like description of a file's detected wrapping
- :func:`detect_layering` — peek the first 4 bytes and classify
- :func:`open_dpmf` — full pipeline: detect → decrypt → decompress →
  open SQLite read-only. Returns a context manager yielding a
  :class:`DpmfHandle`.

Everything else (canonical iteration, integrity verification) is exposed
through :class:`DpmfHandle` so call sites never juggle raw connections.
"""

from .integrity import compute_logical_hash
from .reader import DpmfHandle, Layering, detect_layering, open_dpmf

__all__ = [
    "DpmfHandle",
    "Layering",
    "compute_logical_hash",
    "detect_layering",
    "open_dpmf",
]
