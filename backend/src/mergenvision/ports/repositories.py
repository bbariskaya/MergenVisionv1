from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
    ProcessRecord,
    RecognitionResult,
)
from mergenvision.ports.national_id import NationalIdProtectedValue


class PersonRepository(ABC):
    @abstractmethod
    async def add(self, person: Person) -> Person:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, person_id: UUID) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_national_id_lookup_hash(self, lookup_hash: str) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def list_active(self, *, limit: int, offset: int) -> list[Person]:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        person_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        additional_details: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def update_national_id(
        self,
        person_id: UUID,
        protected: NationalIdProtectedValue,
    ) -> Person | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, person_id: UUID) -> Person | None:
        raise NotImplementedError


class FaceIdentityRepository(ABC):
    @abstractmethod
    async def add(self, face_identity: FaceIdentity) -> FaceIdentity:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, face_identity_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_person_id(self, person_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, face_identity_id: UUID) -> FaceIdentity | None:
        raise NotImplementedError


class InferenceProfileRepository(ABC):
    @abstractmethod
    async def add(self, profile: InferenceProfile) -> InferenceProfile:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, profile_id: UUID) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, profile_name: str) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active(self) -> InferenceProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def retire(self, profile_id: UUID) -> InferenceProfile | None:
        raise NotImplementedError


class ProcessRecordRepository(ABC):
    @abstractmethod
    async def add(self, record: ProcessRecord) -> ProcessRecord:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, process_id: UUID) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_started(self, process_id: UUID) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_completed(
        self,
        process_id: UUID,
        *,
        detected_face_count: int | None = None,
    ) -> ProcessRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_failed(
        self,
        process_id: UUID,
        *,
        error_code: str,
        error_message_sanitized: str,
    ) -> ProcessRecord | None:
        raise NotImplementedError


class PersonPhotoRepository(ABC):
    @abstractmethod
    async def add(self, photo: PersonPhoto) -> PersonPhoto:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_any_status(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_person_id_and_sha256(
        self,
        person_id: UUID,
        content_sha256: str,
    ) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_object_key(self, object_key: str) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_person(self, person_id: UUID, *, limit: int, offset: int) -> list[PersonPhoto]:
        raise NotImplementedError

    @abstractmethod
    async def set_primary(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def activate(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, photo_id: UUID) -> PersonPhoto | None:
        raise NotImplementedError


class FaceSampleRepository(ABC):
    @abstractmethod
    async def add(self, sample: FaceSample) -> FaceSample:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, sample_id: UUID) -> FaceSample | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_any_status(self, sample_id: UUID) -> FaceSample | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_photo_id_and_profile_id(
        self,
        photo_id: UUID,
        inference_profile_id: UUID,
    ) -> FaceSample | None:
        raise NotImplementedError

    @abstractmethod
    async def list_active_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[FaceSample]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_photo_id_any_status(
        self,
        photo_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[FaceSample]:
        raise NotImplementedError

    @abstractmethod
    async def activate(self, sample_id: UUID) -> FaceSample | None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(self, sample_id: UUID) -> FaceSample | None:
        raise NotImplementedError


class RecognitionResultRepository(ABC):
    @abstractmethod
    async def add(self, result: RecognitionResult) -> RecognitionResult:
        raise NotImplementedError

    @abstractmethod
    async def list_by_process(self, process_id: UUID) -> list[RecognitionResult]:
        raise NotImplementedError

    @abstractmethod
    async def list_history_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[RecognitionResult]:
        raise NotImplementedError


class ProcessEventRepository(ABC):
    @abstractmethod
    async def append(
        self,
        process_id: UUID,
        *,
        event_type: str,
        details: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> ProcessEvent:
        raise NotImplementedError

    @abstractmethod
    async def list_by_process(self, process_id: UUID, *, limit: int, offset: int) -> list[ProcessEvent]:
        raise NotImplementedError
