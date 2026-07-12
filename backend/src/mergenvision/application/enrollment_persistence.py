from __future__ import annotations

import hashlib
import math
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from mergenvision.domain import storage_keys
from mergenvision.domain.entities import FaceSample, PersonPhoto
from mergenvision.domain.enums import (
    PersonPhotoStatus,
    ProcessStatus,
    SampleStatus,
)
from mergenvision.domain.errors import (
    ConflictError,
    CrossStoreConsistencyError,
    NotFoundError,
    ObjectConflictError,
    ObjectStorageError,
    ReconciliationRequiredError,
    ValidationError,
    VectorIndexError,
)
from mergenvision.ports.object_storage import ObjectNamespace, ObjectStoragePort
from mergenvision.ports.unit_of_work import UnitOfWork
from mergenvision.ports.vector_index import FaceVectorPoint, VectorIndexPort

_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
_EMBEDDING_DIMENSION = 512
_EMBEDDING_NORMALIZED_TOLERANCE = 1e-3


@dataclass(frozen=True)
class PersistEnrollmentArtifactCommand:
    process_id: UUID
    person_id: UUID
    face_identity_id: UUID
    inference_profile_id: UUID
    photo_id: UUID
    sample_id: UUID
    source_bytes: bytes
    verified_mime_type: str
    content_sha256: str
    file_size_bytes: int
    width: int
    height: int
    is_primary: bool
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    landmarks: Sequence[Mapping[str, float]]
    detection_confidence: float
    quality_score: float | None = None
    embedding: Sequence[float] = ()


@dataclass(frozen=True)
class PersistEnrollmentArtifactResult:
    photo_id: UUID
    sample_id: UUID
    object_key: str
    created_new_photo: bool
    created_new_sample: bool
    created_new_object: bool


class EnrollmentPersistenceService:
    def __init__(
        self,
        uow_factory: Callable[[], AbstractAsyncContextManager[UnitOfWork]],
        object_storage: ObjectStoragePort,
        vector_index: VectorIndexPort,
    ) -> None:
        self._uow_factory = uow_factory
        self._object_storage = object_storage
        self._vector_index = vector_index

    async def persist(
        self,
        command: PersistEnrollmentArtifactCommand,
    ) -> PersistEnrollmentArtifactResult:
        self._validate_command(command)

        metadata = await self._resolve_canonical_metadata(command)
        object_key = storage_keys.build_person_photo_key(
            metadata.person_id,
            metadata.photo_id,
            command.verified_mime_type,
        )

        try:
            object_outcome = await self._object_storage.put_if_absent_or_same(
                ObjectNamespace.PERSON_PHOTOS,
                object_key,
                command.source_bytes,
                content_sha256=command.content_sha256,
                content_type=command.verified_mime_type,
                metadata={
                    "person-id": str(metadata.person_id),
                    "photo-id": str(metadata.photo_id),
                    "schema-version": "1",
                },
            )
        except ObjectStorageError:
            raise
        except Exception as exc:
            raise CrossStoreConsistencyError(
                "Object storage operation failed",
                retryable=True,
            ) from exc

        if object_outcome.info.object_key != object_key:
            raise CrossStoreConsistencyError(
                "Object storage returned an unexpected object key",
                retryable=True,
            )

        try:
            await self._stage_postgresql(metadata, object_key, command)
        except Exception as stage_exc:
            if object_outcome.created:
                try:
                    await self._compensate_minio(
                        object_key,
                        command.content_sha256,
                    )
                except Exception as comp_exc:
                    raise self._wrap_with_primary(
                        primary=stage_exc,
                        compensation=comp_exc,
                        message="PostgreSQL staging failed; MinIO compensation also failed",
                    ) from stage_exc
            raise ReconciliationRequiredError(
                "PostgreSQL staging failed; MinIO object may require reconciliation"
            ) from stage_exc

        try:
            await self._vector_index.upsert_points(
                [
                    FaceVectorPoint(
                        sample_id=metadata.sample_id,
                        face_identity_id=metadata.face_identity_id,
                        person_id=metadata.person_id,
                        inference_profile_id=metadata.inference_profile_id,
                        embedding=command.embedding,
                        active=True,
                    )
                ]
            )
        except (VectorIndexError, CrossStoreConsistencyError):
            await self._append_event_safe(
                command.process_id,
                "enrollment_qdrant_failed",
                {
                    "photo_id": str(metadata.photo_id),
                    "sample_id": str(metadata.sample_id),
                    "stage": "qdrant_upsert",
                    "error_code": "QDRANT_UPSERT_FAILED",
                },
            )
            raise CrossStoreConsistencyError(
                "Qdrant upsert failed; PostgreSQL records remain inactive",
                retryable=True,
            ) from None
        except Exception as exc:
            raise CrossStoreConsistencyError(
                "Qdrant upsert failed unexpectedly",
                retryable=True,
            ) from exc

        try:
            await self._activate_postgresql(metadata, command)
        except Exception as activation_exc:
            try:
                await self._vector_index.set_active(
                    [metadata.sample_id], active=False
                )
            except Exception as compensation_exc:
                raise self._wrap_with_primary(
                    primary=activation_exc,
                    compensation=compensation_exc,
                    message="PostgreSQL activation failed; Qdrant compensation also failed",
                ) from activation_exc
            raise CrossStoreConsistencyError(
                "PostgreSQL activation failed; Qdrant point deactivated",
                retryable=True,
            ) from activation_exc

        return PersistEnrollmentArtifactResult(
            photo_id=metadata.photo_id,
            sample_id=metadata.sample_id,
            object_key=object_outcome.info.object_key,
            created_new_photo=metadata.created_new_photo,
            created_new_sample=metadata.created_new_sample,
            created_new_object=object_outcome.created,
        )

    @dataclass(frozen=True)
    class _CanonicalMetadata:
        person_id: UUID
        face_identity_id: UUID
        inference_profile_id: UUID
        photo_id: UUID
        sample_id: UUID
        process_id: UUID
        created_new_photo: bool
        created_new_sample: bool

    async def _resolve_canonical_metadata(
        self,
        command: PersistEnrollmentArtifactCommand,
    ) -> _CanonicalMetadata:
        async with self._uow_factory() as uow:
            person = await uow.person.get_by_id(command.person_id)
            if person is None:
                raise NotFoundError(f"Person {command.person_id} not found")

            identity = await uow.face_identity.get_by_id(command.face_identity_id)
            if identity is None or identity.person_id != command.person_id:
                raise NotFoundError(
                    f"Face identity {command.face_identity_id} not found for person"
                )

            profile = await uow.inference_profile.get_by_id(
                command.inference_profile_id
            )
            if profile is None:
                raise NotFoundError(
                    f"Inference profile {command.inference_profile_id} not found"
                )
            if not profile.is_active:
                raise ConflictError(
                    f"Inference profile {command.inference_profile_id} is not active"
                )
            if profile.embedding_dimension != _EMBEDDING_DIMENSION:
                raise ConflictError(
                    f"Inference profile dimension {profile.embedding_dimension} != 512"
                )
            if profile.distance_metric.lower() != "cosine":
                raise ConflictError(
                    f"Inference profile metric {profile.distance_metric} != cosine"
                )

            process = await uow.process_record.get_by_id(command.process_id)
            if process is None:
                raise NotFoundError(f"Process {command.process_id} not found")
            if process.status == ProcessStatus.FAILED:
                raise ConflictError(
                    f"Process {command.process_id} is already failed"
                )

            existing_photo = await uow.person_photo.get_by_person_id_and_sha256(
                command.person_id,
                command.content_sha256,
            )

            canonical_photo_id = (
                existing_photo.photo_id if existing_photo else command.photo_id
            )
            created_new_photo = existing_photo is None

            expected_object_key = storage_keys.build_person_photo_key(
                command.person_id,
                canonical_photo_id,
                command.verified_mime_type,
            )

            if existing_photo is not None:
                self._validate_existing_photo(existing_photo, command, expected_object_key)

            existing_sample = None
            if not created_new_photo:
                existing_sample = await uow.face_sample.get_by_photo_id_and_profile_id(
                    canonical_photo_id,
                    command.inference_profile_id,
                )
            canonical_sample_id = (
                existing_sample.sample_id if existing_sample else command.sample_id
            )
            created_new_sample = existing_sample is None

            if existing_sample is not None:
                self._validate_existing_sample(existing_sample, canonical_photo_id, command)

            return self._CanonicalMetadata(
                person_id=command.person_id,
                face_identity_id=command.face_identity_id,
                inference_profile_id=command.inference_profile_id,
                photo_id=canonical_photo_id,
                sample_id=canonical_sample_id,
                process_id=command.process_id,
                created_new_photo=created_new_photo,
                created_new_sample=created_new_sample,
            )

    def _validate_existing_photo(
        self,
        existing_photo: PersonPhoto,
        command: PersistEnrollmentArtifactCommand,
        expected_object_key: str,
    ) -> None:
        if existing_photo.deleted_at is not None:
            raise ConflictError(
                "Existing photo is explicitly deleted; restore via explicit workflow"
            )
        if existing_photo.person_id != command.person_id:
            raise ConflictError("Photo content belongs to another person")
        if existing_photo.content_sha256 != command.content_sha256:
            raise ConflictError("Existing photo SHA does not match command")
        if existing_photo.object_key != expected_object_key:
            raise ConflictError("Existing photo object key does not match canonical key")
        if existing_photo.mime_type != command.verified_mime_type:
            raise ConflictError("Existing photo MIME type does not match command")
        if existing_photo.file_size_bytes != command.file_size_bytes:
            raise ConflictError("Existing photo size does not match command")
        if existing_photo.width != command.width or existing_photo.height != command.height:
            raise ConflictError("Existing photo dimensions do not match command")
        if existing_photo.status not in (
            PersonPhotoStatus.ACTIVE,
            PersonPhotoStatus.INACTIVE,
        ):
            raise ConflictError("Existing photo has an unexpected lifecycle state")

    def _validate_existing_sample(
        self,
        existing_sample: FaceSample,
        canonical_photo_id: UUID,
        command: PersistEnrollmentArtifactCommand,
    ) -> None:
        if existing_sample.deleted_at is not None:
            raise ConflictError(
                "Existing sample is explicitly deleted; restore via explicit workflow"
            )
        if existing_sample.face_identity_id != command.face_identity_id:
            raise ConflictError("Existing sample belongs to a different face identity")
        if existing_sample.photo_id != canonical_photo_id:
            raise ConflictError("Sample exists under a different photo")
        if existing_sample.inference_profile_id != command.inference_profile_id:
            raise ConflictError("Sample exists under a different inference profile")
        if existing_sample.status not in (SampleStatus.ACTIVE, SampleStatus.INACTIVE):
            raise ConflictError("Existing sample has an unexpected lifecycle state")

    async def _stage_postgresql(
        self,
        metadata: _CanonicalMetadata,
        object_key: str,
        command: PersistEnrollmentArtifactCommand,
    ) -> None:
        now = datetime.now(UTC)
        async with self._uow_factory() as uow:
            photo = await uow.person_photo.get_by_id_any_status(metadata.photo_id)
            if photo is None:
                photo = PersonPhoto(
                    photo_id=metadata.photo_id,
                    person_id=metadata.person_id,
                    enrollment_process_id=metadata.process_id,
                    object_key=object_key,
                    content_sha256=command.content_sha256,
                    mime_type=command.verified_mime_type,
                    file_size_bytes=command.file_size_bytes,
                    width=command.width,
                    height=command.height,
                    is_primary=command.is_primary,
                    status=PersonPhotoStatus.INACTIVE,
                    created_at=now,
                    updated_at=now,
                )
                await uow.person_photo.add(photo)

            sample = await uow.face_sample.get_by_id_any_status(metadata.sample_id)
            if sample is None:
                sample = FaceSample(
                    sample_id=metadata.sample_id,
                    face_identity_id=metadata.face_identity_id,
                    photo_id=metadata.photo_id,
                    inference_profile_id=metadata.inference_profile_id,
                    bbox_x=command.bbox_x,
                    bbox_y=command.bbox_y,
                    bbox_width=command.bbox_width,
                    bbox_height=command.bbox_height,
                    landmarks=self._normalize_landmarks(command.landmarks),
                    detection_confidence=command.detection_confidence,
                    quality_score=command.quality_score,
                    status=SampleStatus.INACTIVE,
                    created_at=now,
                )
                await uow.face_sample.add(sample)

            await uow.process_event.append(
                metadata.process_id,
                event_type="enrollment_photo_staged",
                details={
                    "photo_id": str(metadata.photo_id),
                    "sample_id": str(metadata.sample_id),
                    "object_key": object_key,
                    "content_sha256": command.content_sha256,
                    "mime_type": command.verified_mime_type,
                    "stage": "staged",
                },
            )
            await uow.commit()

    async def _activate_postgresql(
        self,
        metadata: _CanonicalMetadata,
        command: PersistEnrollmentArtifactCommand,
    ) -> None:
        async with self._uow_factory() as uow:
            photo = await uow.person_photo.get_by_id_any_status(metadata.photo_id)
            if (
                photo is not None
                and photo.status == PersonPhotoStatus.INACTIVE
                and photo.deleted_at is None
            ):
                await uow.person_photo.activate(metadata.photo_id)

            sample = await uow.face_sample.get_by_id_any_status(metadata.sample_id)
            if (
                sample is not None
                and sample.status == SampleStatus.INACTIVE
                and sample.deleted_at is None
            ):
                await uow.face_sample.activate(metadata.sample_id)

            await uow.process_event.append(
                metadata.process_id,
                event_type="enrollment_activated",
                details={
                    "photo_id": str(metadata.photo_id),
                    "sample_id": str(metadata.sample_id),
                    "stage": "activated",
                },
            )
            await uow.commit()

            photo_after = await uow.person_photo.get_by_id_any_status(metadata.photo_id)
            sample_after = await uow.face_sample.get_by_id_any_status(metadata.sample_id)

        self._assert_activation_postcondition(
            photo_after,
            sample_after,
            metadata,
        )

    def _assert_activation_postcondition(
        self,
        photo: PersonPhoto | None,
        sample: FaceSample | None,
        metadata: _CanonicalMetadata,
    ) -> None:
        if photo is None:
            raise ReconciliationRequiredError("Photo missing after activation commit")
        if photo.status != PersonPhotoStatus.ACTIVE:
            raise ReconciliationRequiredError("Photo is not active after activation commit")
        if photo.deleted_at is not None:
            raise ReconciliationRequiredError("Photo is deleted after activation commit")

        if sample is None:
            raise ReconciliationRequiredError("Sample missing after activation commit")
        if sample.status != SampleStatus.ACTIVE:
            raise ReconciliationRequiredError("Sample is not active after activation commit")
        if sample.deleted_at is not None:
            raise ReconciliationRequiredError("Sample is deleted after activation commit")
        if sample.photo_id != metadata.photo_id:
            raise ReconciliationRequiredError("Sample is linked to the wrong photo")
        if sample.face_identity_id != metadata.face_identity_id:
            raise ReconciliationRequiredError("Sample is linked to the wrong face identity")
        if sample.inference_profile_id != metadata.inference_profile_id:
            raise ReconciliationRequiredError(
                "Sample is linked to the wrong inference profile"
            )

    async def _compensate_minio(
        self,
        object_key: str,
        content_sha256: str,
    ) -> None:
        async with self._uow_factory() as uow:
            photo = await uow.person_photo.get_by_object_key(object_key)
        if photo is not None:
            return

        existing = await self._object_storage.stat(
            ObjectNamespace.PERSON_PHOTOS,
            object_key,
        )
        if existing is None:
            return
        if existing.content_sha256 != content_sha256:
            raise ObjectConflictError(
                "MinIO object SHA does not match expected value; object retained"
            )
        await self._object_storage.delete_if_matches(
            ObjectNamespace.PERSON_PHOTOS,
            object_key,
            content_sha256=content_sha256,
        )

    def _wrap_with_primary(
        self,
        *,
        primary: BaseException,
        compensation: BaseException,
        message: str,
    ) -> ReconciliationRequiredError:
        err = ReconciliationRequiredError(message)
        err.__cause__ = primary
        if hasattr(err, "__notes__"):
            err.__notes__ = [
                f"compensation failure: {type(compensation).__name__}",
            ]
        return err

    async def _append_event_safe(
        self,
        process_id: UUID,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        try:
            async with self._uow_factory() as uow:
                await uow.process_event.append(process_id, event_type=event_type, details=details)
                await uow.commit()
        except Exception:
            pass

    @staticmethod
    def _normalize_landmarks(
        landmarks: Sequence[Mapping[str, float]],
    ) -> dict[str, Any]:
        points = [
            {"x": float(point["x"]), "y": float(point["y"])}
            for point in landmarks
        ]
        return {"points": points}

    def _validate_command(self, command: PersistEnrollmentArtifactCommand) -> None:
        computed_sha = hashlib.sha256(command.source_bytes).hexdigest()
        if computed_sha != command.content_sha256:
            raise ValidationError("content_sha256 does not match source bytes")

        if len(command.source_bytes) != command.file_size_bytes:
            raise ValidationError("file_size_bytes does not match source bytes length")

        if command.verified_mime_type not in _ALLOWED_MIME_TYPES:
            raise ValidationError(f"Unsupported MIME type: {command.verified_mime_type}")

        if command.width <= 0 or command.height <= 0:
            raise ValidationError("width and height must be positive")

        if command.bbox_width <= 0 or command.bbox_height <= 0:
            raise ValidationError("bbox_width and bbox_height must be positive")

        if not 0 <= command.detection_confidence <= 1:
            raise ValidationError("detection_confidence must be in [0, 1]")

        if command.quality_score is not None and not 0 <= command.quality_score <= 1:
            raise ValidationError("quality_score must be in [0, 1]")

        if len(command.landmarks) != 5:
            raise ValidationError("landmarks must contain exactly 5 points")
        for point in command.landmarks:
            if "x" not in point or "y" not in point:
                raise ValidationError("each landmark must have x and y")

        embedding = command.embedding
        if len(embedding) != _EMBEDDING_DIMENSION:
            raise ValidationError("embedding must have exactly 512 dimensions")

        for value in embedding:
            if not math.isfinite(value):
                raise ValidationError("embedding contains NaN or infinite values")

        norm = math.sqrt(sum(value * value for value in embedding))
        if norm == 0:
            raise ValidationError("embedding is a zero vector")
        if abs(norm - 1.0) > _EMBEDDING_NORMALIZED_TOLERANCE:
            raise ValidationError("embedding is not L2-normalized")
