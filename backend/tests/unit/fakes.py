from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from mergenvision.domain import entities as domain
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    SampleStatus,
)
from mergenvision.domain.errors import ObjectConflictError, ObjectStorageError, VectorContractError
from mergenvision.domain.ids import new_uuid7
from mergenvision.ports.object_storage import (
    ObjectNamespace,
    ObjectStoragePort,
    PutObjectOutcome,
    StoredObjectInfo,
)
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
from mergenvision.ports.unit_of_work import UnitOfWork
from mergenvision.ports.vector_index import (
    FaceVectorPoint,
    VectorCandidate,
    VectorIndexPort,
    VectorPointState,
)


class FakeObjectStorage(ObjectStoragePort):
    def __init__(self) -> None:
        self.objects: dict[tuple[ObjectNamespace, str], dict[str, Any]] = {}

    async def ensure_ready(self) -> None:
        return

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
        key = (namespace, object_key)
        existing = self.objects.get(key)
        if existing is not None:
            if existing["sha"] == content_sha256 and existing["size"] == len(data):
                info = StoredObjectInfo(
                    namespace=namespace,
                    object_key=object_key,
                    size_bytes=existing["size"],
                    content_type=existing["content_type"],
                    etag="etag",
                    content_sha256=existing["sha"],
                    metadata=existing["metadata"],
                )
                return PutObjectOutcome(info=info, created=False, idempotent_reuse=True)
            raise ObjectConflictError("object exists with different content")
        full_metadata = dict(metadata)
        full_metadata["content-sha256"] = content_sha256
        self.objects[key] = {
            "data": data,
            "sha": content_sha256,
            "size": len(data),
            "content_type": content_type,
            "metadata": full_metadata,
        }
        info = StoredObjectInfo(
            namespace=namespace,
            object_key=object_key,
            size_bytes=len(data),
            content_type=content_type,
            etag="etag",
            content_sha256=content_sha256,
            metadata=full_metadata,
        )
        return PutObjectOutcome(info=info, created=True, idempotent_reuse=False)

    async def stat(self, namespace: ObjectNamespace, object_key: str) -> StoredObjectInfo | None:
        key = (namespace, object_key)
        entry = self.objects.get(key)
        if entry is None:
            return None
        return StoredObjectInfo(
            namespace=namespace,
            object_key=object_key,
            size_bytes=entry["size"],
            content_type=entry["content_type"],
            etag="etag",
            content_sha256=entry["sha"],
            metadata=dict(entry["metadata"]),
        )

    async def get_bytes(self, namespace: ObjectNamespace, object_key: str) -> bytes:
        key = (namespace, object_key)
        entry = self.objects.get(key)
        if entry is None:
            raise ObjectStorageError("not found")
        return entry["data"]

    async def delete_if_matches(
        self,
        namespace: ObjectNamespace,
        object_key: str,
        *,
        content_sha256: str,
    ) -> None:
        key = (namespace, object_key)
        entry = self.objects.get(key)
        if entry is None:
            return
        if entry["sha"] != content_sha256:
            raise ObjectConflictError("sha mismatch")
        del self.objects[key]


class FakeVectorIndex(VectorIndexPort):
    def __init__(self) -> None:
        self.points: dict[UUID, dict[str, Any]] = {}

    async def ensure_ready(self) -> None:
        return

    @staticmethod
    def _validate(embedding: Sequence[float]) -> None:
        if len(embedding) != 512:
            raise VectorContractError("invalid embedding dimension")
        if any(not math.isfinite(v) for v in embedding):
            raise VectorContractError("embedding has non-finite values")
        norm = math.sqrt(sum(v * v for v in embedding))
        if norm == 0:
            raise VectorContractError("zero vector")
        if abs(norm - 1.0) > 1e-3:
            raise VectorContractError("embedding is not L2-normalized")

    async def upsert_points(self, points: Sequence[FaceVectorPoint]) -> None:
        if not points:
            return
        for point in points:
            self._validate(point.embedding)
            self.points[point.sample_id] = {
                "vector": list(point.embedding),
                "payload": {
                    "faceIdentityId": str(point.face_identity_id),
                    "sampleId": str(point.sample_id),
                    "personId": str(point.person_id),
                    "inferenceProfileId": str(point.inference_profile_id),
                    "active": point.active,
                },
            }

    async def get_points(
        self,
        sample_ids: Sequence[UUID],
        *,
        with_vectors: bool = False,
    ) -> list[VectorPointState]:
        results: list[VectorPointState] = []
        for sample_id in sample_ids:
            entry = self.points.get(sample_id)
            if entry is None:
                continue
            payload = entry["payload"]
            results.append(
                VectorPointState(
                    sample_id=UUID(payload["sampleId"]),
                    face_identity_id=UUID(payload["faceIdentityId"]),
                    person_id=UUID(payload["personId"]),
                    inference_profile_id=UUID(payload["inferenceProfileId"]),
                    active=payload["active"],
                    vector=entry["vector"] if with_vectors else None,
                    present=True,
                )
            )
        return results

    async def search(
        self,
        embedding: Sequence[float],
        inference_profile_id: UUID,
        *,
        limit: int | None = None,
    ) -> list[VectorCandidate]:
        self._validate(embedding)
        scores: list[tuple[UUID, float, dict[str, Any]]] = []
        for sample_id, entry in self.points.items():
            payload = entry["payload"]
            if not payload["active"]:
                continue
            if UUID(payload["inferenceProfileId"]) != inference_profile_id:
                continue
            score = sum(a * b for a, b in zip(embedding, entry["vector"], strict=True))
            scores.append((sample_id, score, payload))
        scores.sort(key=lambda x: x[1], reverse=True)
        search_limit = limit if limit is not None else 10
        return [
            VectorCandidate(
                sample_id=UUID(payload["sampleId"]),
                face_identity_id=UUID(payload["faceIdentityId"]),
                person_id=UUID(payload["personId"]),
                inference_profile_id=UUID(payload["inferenceProfileId"]),
                score=score,
                active=payload["active"],
            )
            for _, score, payload in scores[:search_limit]
        ]

    async def set_active(self, sample_ids: Sequence[UUID], *, active: bool) -> None:
        for sample_id in sample_ids:
            entry = self.points.get(sample_id)
            if entry is not None:
                entry["payload"]["active"] = active

    async def delete_points(self, sample_ids: Sequence[UUID]) -> None:
        for sample_id in sample_ids:
            self.points.pop(sample_id, None)


class FakePersonRepository(PersonRepository):
    def __init__(self) -> None:
        self.persons: dict[UUID, domain.Person] = {}

    async def add(self, person: domain.Person) -> domain.Person:
        self.persons[person.person_id] = person
        return person

    async def get_by_id(self, person_id: UUID) -> domain.Person | None:
        person = self.persons.get(person_id)
        if person is None or person.status != PersonStatus.ACTIVE:
            return None
        return person

    async def get_by_national_id_lookup_hash(self, lookup_hash: str) -> domain.Person | None:
        for person in self.persons.values():
            if person.national_id_lookup_hash == lookup_hash:
                return person
        return None

    async def list_active(self, *, limit: int, offset: int) -> list[domain.Person]:
        return [
            p
            for p in self.persons.values()
            if p.status == PersonStatus.ACTIVE
        ][offset : offset + limit]

    async def update(
        self,
        person_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        additional_details: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> domain.Person | None:
        person = self.persons.get(person_id)
        if person is None:
            return None
        if first_name is not None:
            person.first_name = first_name
        if last_name is not None:
            person.last_name = last_name
        if additional_details is not None:
            person.additional_details = additional_details
        if status is not None:
            person.status = status
        person.updated_at = datetime.now(UTC)
        return person

    async def update_national_id(self, person_id: UUID, protected: Any) -> domain.Person | None:
        return await self.get_by_id(person_id)

    async def deactivate(self, person_id: UUID) -> domain.Person | None:
        person = self.persons.get(person_id)
        if person is None or person.status != PersonStatus.ACTIVE:
            return None
        person.status = PersonStatus.INACTIVE
        person.deleted_at = datetime.now(UTC)
        return person


class FakeFaceIdentityRepository(FaceIdentityRepository):
    def __init__(self) -> None:
        self.identities: dict[UUID, domain.FaceIdentity] = {}

    async def add(self, face_identity: domain.FaceIdentity) -> domain.FaceIdentity:
        self.identities[face_identity.face_identity_id] = face_identity
        return face_identity

    async def get_by_id(self, face_identity_id: UUID) -> domain.FaceIdentity | None:
        identity = self.identities.get(face_identity_id)
        if identity is None or identity.status != FaceIdentityStatus.ACTIVE:
            return None
        return identity

    async def get_by_person_id(self, person_id: UUID) -> domain.FaceIdentity | None:
        for identity in self.identities.values():
            if identity.person_id == person_id and identity.status == FaceIdentityStatus.ACTIVE:
                return identity
        return None

    async def deactivate(self, face_identity_id: UUID) -> domain.FaceIdentity | None:
        identity = self.identities.get(face_identity_id)
        if identity is None or identity.status != FaceIdentityStatus.ACTIVE:
            return None
        identity.status = FaceIdentityStatus.INACTIVE
        identity.deleted_at = datetime.now(UTC)
        return identity


class FakeInferenceProfileRepository(InferenceProfileRepository):
    def __init__(self) -> None:
        self.profiles: dict[UUID, domain.InferenceProfile] = {}

    async def add(self, profile: domain.InferenceProfile) -> domain.InferenceProfile:
        self.profiles[profile.inference_profile_id] = profile
        return profile

    async def get_by_id(self, profile_id: UUID) -> domain.InferenceProfile | None:
        return self.profiles.get(profile_id)

    async def get_by_name(self, profile_name: str) -> domain.InferenceProfile | None:
        for profile in self.profiles.values():
            if profile.profile_name == profile_name:
                return profile
        return None

    async def get_active(self) -> domain.InferenceProfile | None:
        for profile in self.profiles.values():
            if profile.is_active:
                return profile
        return None

    async def retire(self, profile_id: UUID) -> domain.InferenceProfile | None:
        profile = self.profiles.get(profile_id)
        if profile is None:
            return None
        profile.is_active = False
        return profile


class FakeProcessRecordRepository(ProcessRecordRepository):
    def __init__(self) -> None:
        self.records: dict[UUID, domain.ProcessRecord] = {}

    async def add(self, record: domain.ProcessRecord) -> domain.ProcessRecord:
        self.records[record.process_id] = record
        return record

    async def get_by_id(self, process_id: UUID) -> domain.ProcessRecord | None:
        return self.records.get(process_id)

    async def mark_started(self, process_id: UUID) -> domain.ProcessRecord | None:
        record = self.records.get(process_id)
        if record is None:
            return None
        record.status = ProcessStatus.PROCESSING
        return record

    async def mark_completed(
        self,
        process_id: UUID,
        *,
        detected_face_count: int | None = None,
    ) -> domain.ProcessRecord | None:
        record = self.records.get(process_id)
        if record is None:
            return None
        record.status = ProcessStatus.COMPLETED
        if detected_face_count is not None:
            record.detected_face_count = detected_face_count
        return record

    async def mark_failed(
        self,
        process_id: UUID,
        *,
        error_code: str,
        error_message_sanitized: str,
    ) -> domain.ProcessRecord | None:
        record = self.records.get(process_id)
        if record is None:
            return None
        record.status = ProcessStatus.FAILED
        record.error_code = error_code
        record.error_message_sanitized = error_message_sanitized
        return record


class FakePersonPhotoRepository(PersonPhotoRepository):
    def __init__(self) -> None:
        self.photos: dict[UUID, domain.PersonPhoto] = {}

    async def add(self, photo: domain.PersonPhoto) -> domain.PersonPhoto:
        self.photos[photo.photo_id] = photo
        return photo

    async def get_by_id(self, photo_id: UUID) -> domain.PersonPhoto | None:
        photo = self.photos.get(photo_id)
        if photo is None or photo.status != PersonPhotoStatus.ACTIVE:
            return None
        return photo

    async def get_by_id_any_status(self, photo_id: UUID) -> domain.PersonPhoto | None:
        return self.photos.get(photo_id)

    async def get_by_person_id_and_sha256(
        self,
        person_id: UUID,
        content_sha256: str,
    ) -> domain.PersonPhoto | None:
        for photo in self.photos.values():
            if photo.person_id == person_id and photo.content_sha256 == content_sha256:
                return photo
        return None

    async def get_by_object_key(self, object_key: str) -> domain.PersonPhoto | None:
        for photo in self.photos.values():
            if photo.object_key == object_key:
                return photo
        return None

    async def list_by_person(
        self, person_id: UUID, *, limit: int, offset: int
    ) -> list[domain.PersonPhoto]:
        return [
            p
            for p in self.photos.values()
            if p.person_id == person_id and p.status == PersonPhotoStatus.ACTIVE
        ][offset : offset + limit]

    async def set_primary(self, photo_id: UUID) -> domain.PersonPhoto | None:
        return await self.get_by_id(photo_id)

    async def activate(self, photo_id: UUID) -> domain.PersonPhoto | None:
        photo = self.photos.get(photo_id)
        if photo is None or photo.status != PersonPhotoStatus.INACTIVE:
            return None
        photo.status = PersonPhotoStatus.ACTIVE
        photo.deleted_at = None
        photo.updated_at = datetime.now(UTC)
        return photo

    async def deactivate(self, photo_id: UUID) -> domain.PersonPhoto | None:
        photo = self.photos.get(photo_id)
        if photo is None or photo.status != PersonPhotoStatus.ACTIVE:
            return None
        photo.status = PersonPhotoStatus.INACTIVE
        photo.deleted_at = datetime.now(UTC)
        photo.updated_at = datetime.now(UTC)
        if photo.is_primary:
            photo.is_primary = False
        return photo


class FakeFaceSampleRepository(FaceSampleRepository):
    def __init__(self) -> None:
        self.samples: dict[UUID, domain.FaceSample] = {}

    async def add(self, sample: domain.FaceSample) -> domain.FaceSample:
        self.samples[sample.sample_id] = sample
        return sample

    async def get_by_id(self, sample_id: UUID) -> domain.FaceSample | None:
        sample = self.samples.get(sample_id)
        if sample is None or sample.status != SampleStatus.ACTIVE:
            return None
        return sample

    async def get_by_id_any_status(self, sample_id: UUID) -> domain.FaceSample | None:
        return self.samples.get(sample_id)

    async def get_by_photo_id_and_profile_id(
        self,
        photo_id: UUID,
        inference_profile_id: UUID,
    ) -> domain.FaceSample | None:
        for sample in self.samples.values():
            if (
                sample.photo_id == photo_id
                and sample.inference_profile_id == inference_profile_id
            ):
                return sample
        return None

    async def list_active_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[domain.FaceSample]:
        return [
            s
            for s in self.samples.values()
            if s.face_identity_id == face_identity_id and s.status == SampleStatus.ACTIVE
        ][offset : offset + limit]

    async def list_by_photo_id_any_status(
        self,
        photo_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[domain.FaceSample]:
        matches = [
            s for s in self.samples.values() if s.photo_id == photo_id
        ]
        matches.sort(key=lambda s: s.created_at or datetime.min, reverse=True)
        return matches[offset : offset + limit]

    async def activate(self, sample_id: UUID) -> domain.FaceSample | None:
        sample = self.samples.get(sample_id)
        if sample is None or sample.status != SampleStatus.INACTIVE:
            return None
        sample.status = SampleStatus.ACTIVE
        sample.deleted_at = None
        return sample

    async def deactivate(self, sample_id: UUID) -> domain.FaceSample | None:
        sample = self.samples.get(sample_id)
        if sample is None or sample.status != SampleStatus.ACTIVE:
            return None
        sample.status = SampleStatus.INACTIVE
        sample.deleted_at = datetime.now(UTC)
        return sample


class FakeRecognitionResultRepository(RecognitionResultRepository):
    def __init__(self) -> None:
        self.results: dict[UUID, list[domain.RecognitionResult]] = {}

    async def add(self, result: domain.RecognitionResult) -> domain.RecognitionResult:
        self.results.setdefault(result.process_id, []).append(result)
        return result

    async def list_by_process(self, process_id: UUID) -> list[domain.RecognitionResult]:
        return self.results.get(process_id, [])

    async def list_history_by_identity(
        self,
        face_identity_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[domain.RecognitionResult]:
        return []


class FakeProcessEventRepository(ProcessEventRepository):
    def __init__(self) -> None:
        self.events: dict[UUID, list[domain.ProcessEvent]] = {}

    async def append(
        self,
        process_id: UUID,
        *,
        event_type: str,
        details: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> domain.ProcessEvent:
        sequence_no = len(self.events.get(process_id, [])) + 1
        event = domain.ProcessEvent(
            event_id=new_uuid7(),
            process_id=process_id,
            sequence_no=sequence_no,
            event_type=event_type,
            details=details if details is not None else {},
            occurred_at=occurred_at if occurred_at is not None else datetime.now(UTC),
        )
        self.events.setdefault(process_id, []).append(event)
        return event

    async def list_by_process(
        self, process_id: UUID, *, limit: int, offset: int
    ) -> list[domain.ProcessEvent]:
        return self.events.get(process_id, [])[offset : offset + limit]


@dataclass
class FakeUnitOfWork(UnitOfWork):
    person: FakePersonRepository = field(default_factory=FakePersonRepository)
    face_identity: FakeFaceIdentityRepository = field(default_factory=FakeFaceIdentityRepository)
    inference_profile: FakeInferenceProfileRepository = field(
        default_factory=FakeInferenceProfileRepository
    )
    process_record: FakeProcessRecordRepository = field(
        default_factory=FakeProcessRecordRepository
    )
    person_photo: FakePersonPhotoRepository = field(default_factory=FakePersonPhotoRepository)
    face_sample: FakeFaceSampleRepository = field(default_factory=FakeFaceSampleRepository)
    recognition_result: FakeRecognitionResultRepository = field(
        default_factory=FakeRecognitionResultRepository
    )
    process_event: FakeProcessEventRepository = field(default_factory=FakeProcessEventRepository)
    committed: bool = False
    rolled_back: bool = False

    async def __aenter__(self) -> FakeUnitOfWork:
        self._snapshot = self.snapshot()
        self.rolled_back = False
        self._active = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_val is not None:
            self._restore(self._snapshot)
            self.rolled_back = True
        self._active = False

    @property
    def active(self) -> bool:
        return getattr(self, "_active", False)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    def _restore(self, snapshot: FakeUnitOfWork) -> None:
        self.person = snapshot.person
        self.face_identity = snapshot.face_identity
        self.inference_profile = snapshot.inference_profile
        self.process_record = snapshot.process_record
        self.person_photo = snapshot.person_photo
        self.face_sample = snapshot.face_sample
        self.recognition_result = snapshot.recognition_result
        self.process_event = snapshot.process_event
        self.committed = snapshot.committed
        self.rolled_back = snapshot.rolled_back

    def snapshot(self) -> FakeUnitOfWork:
        return FakeUnitOfWork(
            person=deepcopy(self.person),
            face_identity=deepcopy(self.face_identity),
            inference_profile=deepcopy(self.inference_profile),
            process_record=deepcopy(self.process_record),
            person_photo=deepcopy(self.person_photo),
            face_sample=deepcopy(self.face_sample),
            recognition_result=deepcopy(self.recognition_result),
            process_event=deepcopy(self.process_event),
        )


def make_uow_factory(uow: FakeUnitOfWork) -> Callable[[], FakeUnitOfWork]:
    def factory() -> FakeUnitOfWork:
        return uow
    return factory
