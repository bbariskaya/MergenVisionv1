from __future__ import annotations

import dataclasses
import hashlib
import math
from datetime import UTC, datetime
from uuid import UUID

import pytest

from mergenvision.application.enrollment_persistence import (
    EnrollmentPersistenceService,
    PersistEnrollmentArtifactCommand,
)
from mergenvision.domain import entities as domain
from mergenvision.domain.enums import (
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    SampleStatus,
)
from mergenvision.domain.errors import (
    ConflictError,
    CrossStoreConsistencyError,
    ObjectConflictError,
    ReconciliationRequiredError,
    ValidationError,
)
from mergenvision.ports.object_storage import ObjectNamespace
from tests.unit.fakes import (
    FakeObjectStorage,
    FakeUnitOfWork,
    FakeVectorIndex,
    make_uow_factory,
)


def _norm(v: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(x * x for x in v))
    return [x / magnitude for x in v]


def _embedding(values: list[float] | None = None) -> list[float]:
    base = values if values is not None else list(range(512))
    return _norm(base)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def storage():
    return FakeObjectStorage()


@pytest.fixture
def vector_index():
    return FakeVectorIndex()


@pytest.fixture
def service(uow, storage, vector_index):
    return EnrollmentPersistenceService(
        uow_factory=make_uow_factory(uow),
        object_storage=storage,
        vector_index=vector_index,
    )


def _make_seed_data(uow: FakeUnitOfWork) -> tuple[UUID, UUID, UUID, UUID]:
    now = datetime.now(UTC)
    person_id = UUID("12345678-1234-5678-1234-567812345678")
    identity_id = UUID("22345678-1234-5678-1234-567812345678")
    profile_id = UUID("32345678-1234-5678-1234-567812345678")
    process_id = UUID("42345678-1234-5678-1234-567812345678")

    uow.person.persons[person_id] = domain.Person(
        person_id=person_id,
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=b"ciphertext",
        national_id_lookup_hash="lookup",
        national_id_masked="*******1234",
        additional_details={},
        status=PersonStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    uow.face_identity.identities[identity_id] = domain.FaceIdentity(
        face_identity_id=identity_id,
        person_id=person_id,
        status="active",
        created_at=now,
        updated_at=now,
    )
    uow.inference_profile.profiles[profile_id] = domain.InferenceProfile(
        inference_profile_id=profile_id,
        profile_name="default",
        detector_name="retinaface",
        detector_version="v1",
        detector_artifact_sha256="sha",
        alignment_version="v1",
        embedder_name="arcface",
        embedder_version="v1",
        embedder_artifact_sha256="sha",
        preprocessing_version="v1",
        embedding_dimension=512,
        distance_metric="cosine",
        match_threshold=0.6,
        is_active=True,
        created_at=now,
    )
    uow.process_record.records[process_id] = domain.ProcessRecord(
        process_id=process_id,
        process_type="enrollment",
        status=ProcessStatus.PENDING,
        inference_profile_id=profile_id,
        created_at=now,
    )
    return person_id, identity_id, profile_id, process_id


def _make_command(
    *,
    person_id: UUID,
    identity_id: UUID,
    profile_id: UUID,
    process_id: UUID,
    photo_id: UUID,
    sample_id: UUID,
    data: bytes = b"photo-bytes",
    mime: str = "image/jpeg",
    embedding: list[float] | None = None,
) -> PersistEnrollmentArtifactCommand:
    embedding = embedding if embedding is not None else _embedding()
    return PersistEnrollmentArtifactCommand(
        process_id=process_id,
        person_id=person_id,
        face_identity_id=identity_id,
        inference_profile_id=profile_id,
        photo_id=photo_id,
        sample_id=sample_id,
        source_bytes=data,
        verified_mime_type=mime,
        content_sha256=_sha(data),
        file_size_bytes=len(data),
        width=640,
        height=480,
        is_primary=True,
        bbox_x=100,
        bbox_y=80,
        bbox_width=200,
        bbox_height=200,
        landmarks=[{"x": 1.0, "y": 1.0} for _ in range(5)],
        detection_confidence=0.99,
        quality_score=0.95,
        embedding=embedding,
    )


@pytest.mark.asyncio
async def test_invalid_sha_rejected(service, uow):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=UUID("52345678-1234-5678-1234-567812345678"),
        sample_id=UUID("62345678-1234-5678-1234-567812345678"),
        data=b"x",
    )
    command = dataclasses.replace(command, content_sha256="wrong")
    with pytest.raises(ValidationError):
        await service.persist(command)


@pytest.mark.asyncio
async def test_happy_path(service, uow, storage, vector_index):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )

    result = await service.persist(command)

    assert result.photo_id == photo_id
    assert result.sample_id == sample_id
    assert result.created_new_object is True
    photo = uow.person_photo.photos[photo_id]
    sample = uow.face_sample.samples[sample_id]
    assert photo.status == PersonPhotoStatus.ACTIVE
    assert sample.status == SampleStatus.ACTIVE
    assert vector_index.points[sample_id]["payload"]["active"] is True
    assert (ObjectNamespace.PERSON_PHOTOS, result.object_key) in storage.objects


@pytest.mark.asyncio
async def test_retry_is_idempotent(service, uow, storage, vector_index):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )

    result1 = await service.persist(command)
    result2 = await service.persist(command)

    assert result1.photo_id == result2.photo_id
    assert result1.sample_id == result2.sample_id
    assert result2.created_new_object is False
    assert len(uow.person_photo.photos) == 1
    assert len(uow.face_sample.samples) == 1
    assert len(vector_index.points) == 1


@pytest.mark.asyncio
async def test_minio_failure_does_not_stage_db_or_qdrant(service, uow, storage, vector_index):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )

    class FailingStorage(FakeObjectStorage):
        async def put_if_absent_or_same(self, *args, **kwargs):
            raise CrossStoreConsistencyError("minio down", retryable=True)

    service._object_storage = FailingStorage()

    with pytest.raises(CrossStoreConsistencyError):
        await service.persist(command)

    assert len(uow.person_photo.photos) == 0
    assert len(uow.face_sample.samples) == 0
    assert len(vector_index.points) == 0


@pytest.mark.asyncio
async def test_staging_failure_compensates_minio(service, uow, storage):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )

    class FailingUoW(FakeUnitOfWork):
        async def commit(self) -> None:
            raise RuntimeError("database unavailable")

    failing_uow = FailingUoW()
    failing_uow.person = uow.person
    failing_uow.face_identity = uow.face_identity
    failing_uow.inference_profile = uow.inference_profile
    failing_uow.process_record = uow.process_record
    service._uow_factory = make_uow_factory(failing_uow)

    with pytest.raises(ReconciliationRequiredError):
        await service.persist(command)

    assert len(storage.objects) == 0


@pytest.mark.asyncio
async def test_qdrant_failure_leaves_inactive_staging(service, uow, storage, vector_index):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )

    class FailingVectorIndex(FakeVectorIndex):
        async def upsert_points(self, points):
            raise CrossStoreConsistencyError("qdrant down", retryable=True)

    service._vector_index = FailingVectorIndex()

    with pytest.raises(CrossStoreConsistencyError):
        await service.persist(command)

    photo = uow.person_photo.photos[photo_id]
    sample = uow.face_sample.samples[sample_id]
    assert photo.status == PersonPhotoStatus.INACTIVE
    assert photo.deleted_at is None
    assert sample.status == SampleStatus.INACTIVE
    assert sample.deleted_at is None
    assert len(vector_index.points) == 0


@pytest.mark.asyncio
async def test_process_events_are_pii_free(service, uow, storage, vector_index):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )

    await service.persist(command)

    events = uow.process_event.events.get(process_id, [])
    assert events
    for event in events:
        details = event.details
        assert "firstName" not in details
        assert "lastName" not in details
        assert "nationalId" not in details
        assert "originalFilename" not in details


@pytest.mark.asyncio
async def test_existing_exactly_deleted_photo_is_not_restored(service, uow, storage, vector_index):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )
    existing_photo_id = UUID("72345678-1234-5678-1234-567812345678")
    uow.person_photo.photos[existing_photo_id] = domain.PersonPhoto(
        photo_id=existing_photo_id,
        person_id=person_id,
        object_key=f"people/{person_id}/photos/{existing_photo_id}/source.jpg",
        content_sha256=command.content_sha256,
        mime_type=command.verified_mime_type,
        file_size_bytes=command.file_size_bytes,
        width=command.width,
        height=command.height,
        is_primary=False,
        status=PersonPhotoStatus.INACTIVE,
        deleted_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    with pytest.raises(ConflictError):
        await service.persist(command)

    assert len(storage.objects) == 0
    assert len(vector_index.points) == 0


@pytest.mark.asyncio
async def test_existing_sample_belongs_to_different_identity_is_conflict(service, uow, storage):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    other_identity_id = UUID("72345678-1234-5678-1234-567812345678")
    uow.face_identity.identities[other_identity_id] = domain.FaceIdentity(
        face_identity_id=other_identity_id,
        person_id=person_id,
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )
    existing_photo_id = UUID("82345678-1234-5678-1234-567812345678")
    uow.person_photo.photos[existing_photo_id] = domain.PersonPhoto(
        photo_id=existing_photo_id,
        person_id=person_id,
        object_key=f"people/{person_id}/photos/{existing_photo_id}/source.jpg",
        content_sha256=command.content_sha256,
        mime_type=command.verified_mime_type,
        file_size_bytes=command.file_size_bytes,
        width=command.width,
        height=command.height,
        is_primary=False,
        status=PersonPhotoStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    uow.face_sample.samples[sample_id] = domain.FaceSample(
        sample_id=sample_id,
        face_identity_id=other_identity_id,
        photo_id=existing_photo_id,
        inference_profile_id=profile_id,
        bbox_x=command.bbox_x,
        bbox_y=command.bbox_y,
        bbox_width=command.bbox_width,
        bbox_height=command.bbox_height,
        landmarks={"points": []},
        detection_confidence=command.detection_confidence,
        quality_score=command.quality_score,
        status=SampleStatus.ACTIVE,
        created_at=datetime.now(UTC),
    )

    with pytest.raises(ConflictError):
        await service.persist(command)


@pytest.mark.asyncio
async def test_compensation_retains_object_when_referencing_row_exists(service, uow, storage):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )
    object_key = f"people/{person_id}/photos/{photo_id}/source.jpg"
    uow.person_photo.photos[photo_id] = domain.PersonPhoto(
        photo_id=photo_id,
        person_id=person_id,
        object_key=object_key,
        content_sha256=command.content_sha256,
        mime_type=command.verified_mime_type,
        file_size_bytes=command.file_size_bytes,
        width=command.width,
        height=command.height,
        is_primary=False,
        status=PersonPhotoStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class FailingUoW(FakeUnitOfWork):
        async def commit(self) -> None:
            if not getattr(self, "_failed_once", False):
                self._failed_once = True
                raise RuntimeError("database unavailable")
            return await super().commit()

    failing_uow = FailingUoW()
    failing_uow.person = uow.person
    failing_uow.face_identity = uow.face_identity
    failing_uow.inference_profile = uow.inference_profile
    failing_uow.process_record = uow.process_record
    failing_uow.person_photo = uow.person_photo
    failing_uow.face_sample = uow.face_sample
    service._uow_factory = make_uow_factory(failing_uow)

    with pytest.raises(ReconciliationRequiredError):
        await service.persist(command)

    assert (ObjectNamespace.PERSON_PHOTOS, object_key) in storage.objects


@pytest.mark.asyncio
async def test_compensation_deletes_object_when_no_reference_and_matching_sha(service, uow, storage):
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    sample_id = UUID("62345678-1234-5678-1234-567812345678")
    command = _make_command(
        person_id=person_id,
        identity_id=identity_id,
        profile_id=profile_id,
        process_id=process_id,
        photo_id=photo_id,
        sample_id=sample_id,
    )

    class FailingUoW(FakeUnitOfWork):
        async def commit(self) -> None:
            raise RuntimeError("database unavailable")

    failing_uow = FailingUoW()
    failing_uow.person = uow.person
    failing_uow.face_identity = uow.face_identity
    failing_uow.inference_profile = uow.inference_profile
    failing_uow.process_record = uow.process_record
    service._uow_factory = make_uow_factory(failing_uow)

    with pytest.raises(ReconciliationRequiredError):
        await service.persist(command)

    assert len(storage.objects) == 0


@pytest.mark.asyncio
async def test_compensation_retains_object_on_sha_mismatch(service, uow, storage):
    """SHA mismatch during compensation keeps the object and raises a conflict."""
    person_id, identity_id, profile_id, process_id = _make_seed_data(uow)
    photo_id = UUID("52345678-1234-5678-1234-567812345678")
    object_key = f"people/{person_id}/photos/{photo_id}/source.jpg"
    expected_sha = _sha(b"photo-bytes")
    await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        object_key,
        b"different-content",
        content_sha256="wrong-sha",
        content_type="image/jpeg",
        metadata={},
    )

    with pytest.raises(ObjectConflictError):
        await service._compensate_minio(object_key, expected_sha)

    assert (ObjectNamespace.PERSON_PHOTOS, object_key) in storage.objects
