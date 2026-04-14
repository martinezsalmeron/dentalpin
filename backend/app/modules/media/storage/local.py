"""Local filesystem storage backend."""

from pathlib import Path

import aiofiles
import aiofiles.os

from .base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Store files on local filesystem (Docker volume)."""

    def __init__(self, base_path: str) -> None:
        """Initialize with base storage directory.

        Args:
            base_path: Root directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _full_path(self, path: str) -> Path:
        """Get full filesystem path."""
        return self.base_path / path

    async def store(self, data: bytes, path: str) -> str:
        """Store file data at path."""
        full_path = self._full_path(path)

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)

        return path

    async def retrieve(self, path: str) -> bytes:
        """Retrieve file content."""
        full_path = self._full_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        """Delete file from storage."""
        full_path = self._full_path(path)

        if not full_path.exists():
            return False

        await aiofiles.os.remove(full_path)
        return True

    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        return self._full_path(path).exists()
