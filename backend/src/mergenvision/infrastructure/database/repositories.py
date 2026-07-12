from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mergenvision.domain import entities as domain
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
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    SampleStatus,
)
from mergenvision.domain.errors import ConflictError, NotFoundError, RepositoryError
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database import mappers
from mergenvision.infrastructure.database import models as orm
from mergenvision.ports.national_id import NationalIdProtectedValue
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


def _handle_db_error(exc: Exception) -> None:
    if isinstance(exc, IntegrityError):
        raise ConflictError("Resource conflict or constraint violation") from exc
    if isinstance(exc, SQLAlchemyError):
        raise RepositoryError("Database operation failed") from exc
    raise exc


class PostgresPersonRepository(PersonRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, person: Person) -> Person:
        orm_obj = orm.Person(**dataclasses.asdict(person))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(orm_obj)

    async def get_by_id(self, person_id: UUID) -> Person | None:
        stmt = (
            select(orm.Person)
            .where(orm.Person.person_id == person_id)
            .where(orm.Person.status == PersonStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person(row) if row else None

    async def get_by_national_id_lookup_hash(self, lookup_hash: str) -> Person | None:
        stmt = select(orm.Person).where(orm.Person.national_id_lookup_hash == lookup_hash)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person(row) if row else None

    async def list_active(self, *, limit: int, offset: int) -> list[Person]:
        stmt = (
            select(orm.Person)
            .where(orm.Person.status == PersonStatus.ACTIVE)
            .order_by(orm.Person.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_person(row) for row in result.scalars().all()]

    async def update(
        self,
        person_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        additional_details: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> Person | None:
        row = await self._get_active_orm(person_id)
        if row is None:
            return None
        if first_name is not None:
            row.first_name = first_name
        if last_name is not None:
            row.last_name = last_name
        if additional_details is not None:
            row.additional_details = additional_details
        if status is not None:
            row.status = status
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(row)

    async def update_national_id(
        self,
        person_id: UUID,
        protected: NationalIdProtectedValue,
    ) -> Person | None:
        row = await self._get_active_orm(person_id)
        if row is None:
            return None
        row.national_id_ciphertext = protected.ciphertext
        row.national_id_lookup_hash = protected.lookup_hash
        row.national_id_masked = protected.masked
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(row)

    async def deactivate(self, person_id: UUID) -> Person | None:
        row = await self._get_active_orm(person_id)
        if row is None:
            return None
        row.status = PersonStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person(row)

    async def _get_active_orm(self, person_id: UUID) -> orm.Person | None:
        stmt = (
            select(orm.Person)
            .where(orm.Person.person_id == person_id)
            .where(orm.Person.status == PersonStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class PostgresFaceIdentityRepository(FaceIdentityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, face_identity: FaceIdentity) -> FaceIdentity:
        orm_obj = orm.FaceIdentity(**dataclasses.asdict(face_identity))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_identity(orm_obj)

    async def get_by_id(self, face_identity_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.face_identity_id == face_identity_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_identity(row) if row else None

    async def get_by_person_id(self, person_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.person_id == person_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_identity(row) if row else None

    async def deactivate(self, face_identity_id: UUID) -> FaceIdentity | None:
        stmt = (
            select(orm.FaceIdentity)
            .where(orm.FaceIdentity.face_identity_id == face_identity_id)
            .where(orm.FaceIdentity.status == FaceIdentityStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = FaceIdentityStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_identity(row)


class PostgresInferenceProfileRepository(InferenceProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, profile: InferenceProfile) -> InferenceProfile:
        orm_obj = orm.InferenceProfile(**dataclasses.asdict(profile))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_inference_profile(orm_obj)

    async def get_by_id(self, profile_id: UUID) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.inference_profile_id == profile_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_inference_profile(row) if row else None

    async def get_by_name(self, profile_name: str) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.profile_name == profile_name
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_inference_profile(row) if row else None

    async def get_active(self) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.is_active.is_(True)
        )
        result = await self._session.execute(stmt)
        try:
            row = result.scalar_one_or_none()
        except MultipleResultsFound as exc:
            raise RepositoryError(
                "Multiple active inference profiles found; expected at most one"
            ) from exc
        return mappers.map_inference_profile(row) if row else None

    async def retire(self, profile_id: UUID) -> InferenceProfile | None:
        stmt = select(orm.InferenceProfile).where(
            orm.InferenceProfile.inference_profile_id == profile_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.is_active = False
        row.retired_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_inference_profile(row)


class PostgresProcessRecordRepository(ProcessRecordRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, record: ProcessRecord) -> ProcessRecord:
        orm_obj = orm.ProcessRecord(**dataclasses.asdict(record))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(orm_obj)

    async def get_by_id(self, process_id: UUID) -> ProcessRecord | None:
        stmt = select(orm.ProcessRecord).where(orm.ProcessRecord.process_id == process_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_process_record(row) if row else None

    async def mark_started(self, process_id: UUID) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.PROCESSING
        row.started_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def mark_completed(
        self,
        process_id: UUID,
        *,
        detected_face_count: int | None = None,
    ) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.COMPLETED
        row.completed_at = datetime.now(UTC)
        if detected_face_count is not None:
            row.detected_face_count = detected_face_count
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def mark_failed(
        self,
        process_id: UUID,
        *,
        error_code: str,
        error_message_sanitized: str,
    ) -> ProcessRecord | None:
        row = await self._get_orm(process_id)
        if row is None:
            return None
        row.status = ProcessStatus.FAILED
        row.completed_at = datetime.now(UTC)
        row.error_code = error_code
        row.error_message_sanitized = error_message_sanitized
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_record(row)

    async def _get_orm(self, process_id: UUID) -> orm.ProcessRecord | None:
        stmt = select(orm.ProcessRecord).where(orm.ProcessRecord.process_id == process_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class PostgresPersonPhotoRepository(PersonPhotoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, photo: PersonPhoto) -> PersonPhoto:
        orm_obj = orm.PersonPhoto(**dataclasses.asdict(photo))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(orm_obj)

    async def get_by_id(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_person_photo(row) if row else None

    async def list_by_person(self, person_id: UUID, *, limit: int, offset: int) -> list[PersonPhoto]:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.person_id == person_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
            .order_by(orm.PersonPhoto.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_person_photo(row) for row in result.scalars().all()]

    async def set_primary(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        await self._session.execute(
            update(orm.PersonPhoto)
            .where(orm.PersonPhoto.person_id == row.person_id)
            .where(orm.PersonPhoto.photo_id != row.photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
            .values(is_primary=False)
        )
        row.is_primary = True
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(row)

    async def activate(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.INACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = PersonPhotoStatus.ACTIVE
        row.deleted_at = None
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(row)

    async def deactivate(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = (
            select(orm.PersonPhoto)
            .where(orm.PersonPhoto.photo_id == photo_id)
            .where(orm.PersonPhoto.status == PersonPhotoStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = PersonPhotoStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        if row.is_primary:
            row.is_primary = False
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_person_photo(row)


class PostgresFaceSampleRepository(FaceSampleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, sample: FaceSample) -> FaceSample:
        orm_obj = orm.FaceSample(**dataclasses.asdict(sample))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_sample(orm_obj)

    async def get_by_id(self, sample_id: UUID) -> FaceSample | None:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.sample_id == sample_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return mappers.map_face_sample(row) if row else None

    async def list_active_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[FaceSample]:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.face_identity_id == face_identity_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
            .order_by(orm.FaceSample.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_face_sample(row) for row in result.scalars().all()]

    async def activate(self, sample_id: UUID) -> FaceSample | None:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.sample_id == sample_id)
            .where(orm.FaceSample.status == SampleStatus.INACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = SampleStatus.ACTIVE
        row.deleted_at = None
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_sample(row)

    async def deactivate(self, sample_id: UUID) -> FaceSample | None:
        stmt = (
            select(orm.FaceSample)
            .where(orm.FaceSample.sample_id == sample_id)
            .where(orm.FaceSample.status == SampleStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = SampleStatus.INACTIVE
        row.deleted_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_face_sample(row)


class PostgresRecognitionResultRepository(RecognitionResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, result: RecognitionResult) -> RecognitionResult:
        orm_obj = orm.RecognitionResult(**dataclasses.asdict(result))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_recognition_result(orm_obj)

    async def list_by_process(self, process_id: UUID) -> list[RecognitionResult]:
        stmt = (
            select(orm.RecognitionResult)
            .where(orm.RecognitionResult.process_id == process_id)
            .order_by(orm.RecognitionResult.face_index.asc())
        )
        result = await self._session.execute(stmt)
        return [mappers.map_recognition_result(row) for row in result.scalars().all()]

    async def list_history_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[RecognitionResult]:
        stmt = (
            select(orm.RecognitionResult)
            .where(orm.RecognitionResult.matched_face_identity_id == face_identity_id)
            .order_by(orm.RecognitionResult.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_recognition_result(row) for row in result.scalars().all()]


class PostgresProcessEventRepository(ProcessEventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        process_id: UUID,
        *,
        event_type: str,
        details: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> ProcessEvent:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": self._process_lock_id(process_id)},
        )
        process_stmt = select(orm.ProcessRecord).where(
            orm.ProcessRecord.process_id == process_id
        )
        process_result = await self._session.execute(process_stmt)
        if process_result.scalar_one_or_none() is None:
            raise NotFoundError(f"Process {process_id} not found")
        next_sequence = await self._next_sequence_no(process_id)
        event = domain.ProcessEvent(
            event_id=new_uuid7(),
            process_id=process_id,
            sequence_no=next_sequence,
            event_type=event_type,
            details=details if details is not None else {},
            occurred_at=occurred_at if occurred_at is not None else datetime.now(UTC),
        )
        orm_obj = orm.ProcessEvent(**dataclasses.asdict(event))
        self._session.add(orm_obj)
        try:
            await self._session.flush()
        except Exception as exc:
            _handle_db_error(exc)
        return mappers.map_process_event(orm_obj)

    def _process_lock_id(self, process_id: UUID) -> int:
        return int(process_id.int % (1 << 63))

    async def list_by_process(
        self,
        process_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[ProcessEvent]:
        stmt = (
            select(orm.ProcessEvent)
            .where(orm.ProcessEvent.process_id == process_id)
            .order_by(orm.ProcessEvent.sequence_no.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [mappers.map_process_event(row) for row in result.scalars().all()]

    async def _next_sequence_no(self, process_id: UUID) -> int:
        stmt = select(
            func.coalesce(func.max(orm.ProcessEvent.sequence_no), 0) + 1
        ).where(orm.ProcessEvent.process_id == process_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
