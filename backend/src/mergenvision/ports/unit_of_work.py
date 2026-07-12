from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from mergenvision.ports.repositories import (
    FaceIdentityRepository,
    FaceSampleRepository,
    InferenceProfileRepository,
    PersonPhotoRepository,
    PersonRepository,
    ProcessEventRepository,
    ProcessRecordRepository,
    RecognitionResultRepository,
)


class UnitOfWork(ABC):
    person: PersonRepository
    face_identity: FaceIdentityRepository
    inference_profile: InferenceProfileRepository
    process_record: ProcessRecordRepository
    person_photo: PersonPhotoRepository
    face_sample: FaceSampleRepository
    recognition_result: RecognitionResultRepository
    process_event: ProcessEventRepository

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError
