from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.core.config import Settings

settings = Settings()


class BaseStorage(ABC):
    @abstractmethod
    async def save(self, contents: bytes, destination: Path) -> Path:
        raise NotImplementedError

    @abstractmethod
    async def get(self, path: Path) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, path: Path) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_url(self, path: Path) -> str:
        raise NotImplementedError


class LocalStorage(BaseStorage):
    def __init__(self, root_path: Optional[Path] = None) -> None:
        self.root_path = root_path or settings.local_storage_path
        self.root_path.mkdir(parents=True, exist_ok=True)

    async def save(self, contents: bytes, destination: Path) -> Path:
        full_path = self.root_path / destination
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(contents)
        return full_path

    async def get(self, path: Path) -> bytes:
        full_path = self.root_path / path
        return full_path.read_bytes()

    async def delete(self, path: Path) -> None:
        full_path = self.root_path / path
        if full_path.exists():
            full_path.unlink()

    def get_url(self, path: Path) -> str:
        return str(self.root_path / path)


class S3Storage(BaseStorage):
    async def save(self, contents: bytes, destination: Path) -> Path:
        raise NotImplementedError("S3Storage is not implemented yet")

    async def get(self, path: Path) -> bytes:
        raise NotImplementedError("S3Storage is not implemented yet")

    async def delete(self, path: Path) -> None:
        raise NotImplementedError("S3Storage is not implemented yet")

    def get_url(self, path: Path) -> str:
        raise NotImplementedError("S3Storage is not implemented yet")


def get_storage() -> BaseStorage:
    if settings.storage_backend == "s3":
        return S3Storage()
    return LocalStorage()
