from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class FaceVectorPoint:
    sample_id: UUID
    face_identity_id: UUID
    person_id: UUID
    inference_profile_id: UUID
    embedding: Sequence[float]
    active: bool


@dataclass(frozen=True)
class VectorCandidate:
    sample_id: UUID
    face_identity_id: UUID
    person_id: UUID
    inference_profile_id: UUID
    score: float
    active: bool


@dataclass(frozen=True)
class VectorPointState:
    sample_id: UUID
    face_identity_id: UUID
    person_id: UUID
    inference_profile_id: UUID
    active: bool
    vector: Sequence[float] | None = None
    present: bool = True


class VectorIndexPort(ABC):
    @abstractmethod
    async def ensure_ready(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_points(self, points: Sequence[FaceVectorPoint]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_points(
        self,
        sample_ids: Sequence[UUID],
        *,
        with_vectors: bool = False,
    ) -> list[VectorPointState]:
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        embedding: Sequence[float],
        inference_profile_id: UUID,
        *,
        limit: int | None = None,
    ) -> list[VectorCandidate]:
        raise NotImplementedError

    @abstractmethod
    async def set_active(self, sample_ids: Sequence[UUID], *, active: bool) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_points(self, sample_ids: Sequence[UUID]) -> None:
        raise NotImplementedError
