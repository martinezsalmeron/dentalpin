"""Storage backend factory."""

import tempfile
from functools import lru_cache

from app.config import settings

from .base import StorageBackend
from .local import LocalStorageBackend

__all__ = ["StorageBackend", "get_storage_backend"]

# For testing, use a temp directory
_test_storage_path: str | None = None


def set_test_storage_path(path: str | None) -> None:
    """Set storage path for tests (clears cache)."""
    global _test_storage_path
    _test_storage_path = path
    get_storage_backend.cache_clear()


@lru_cache
def get_storage_backend() -> StorageBackend:
    """Get configured storage backend (singleton).

    Returns:
        StorageBackend instance based on STORAGE_BACKEND setting
    """
    backend = settings.STORAGE_BACKEND

    if backend == "local":
        # Use test path if set, otherwise use configured path
        if settings.TESTING and _test_storage_path is None:
            # Auto-create temp directory for tests
            path = tempfile.mkdtemp(prefix="dentalpin_test_storage_")
            return LocalStorageBackend(path)
        path = _test_storage_path or settings.STORAGE_LOCAL_PATH
        return LocalStorageBackend(path)

    raise ValueError(f"Unknown storage backend: {backend}")
