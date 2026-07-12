from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ObjectNamespace(Enum):
    PERSON_PHOTOS = "person_photos"
    RECOGNITION_INPUTS = "recognition_inputs"


@dataclass(frozen=True)
class StoredObjectInfo:
    namespace: ObjectNamespace
    object_key: str
    size_bytes: int
    content_type: str
    etag: str
    content_sha256: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class PutObjectOutcome:
    info: StoredObjectInfo
    created: bool
    idempotent_reuse: bool


class ObjectStoragePort(ABC):
    @abstractmethod
    async def ensure_ready(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def put_if_absent_or_same(
        self,
        namespace: ObjectNamespace,
        object_key: str,
        data: bytes,
        *,
        content_sha256: str,
        content_type: str,
        metadata: dict[str, str],
    ) -> PutObjectOutcome:
        raise NotImplementedError

    @abstractmethod
    async def stat(self, namespace: ObjectNamespace, object_key: str) -> StoredObjectInfo | None:
        raise NotImplementedError

    @abstractmethod
    async def get_bytes(self, namespace: ObjectNamespace, object_key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def delete_if_matches(
        self,
        namespace: ObjectNamespace,
        object_key: str,
        *,
        content_sha256: str,
    ) -> None:
        raise NotImplementedError
