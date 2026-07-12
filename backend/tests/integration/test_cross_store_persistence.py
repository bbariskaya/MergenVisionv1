from __future__ import annotations

import os
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mergenvision.application.enrollment_persistence import (
    EnrollmentPersistenceService,
    PersistEnrollmentArtifactCommand,
)
from mergenvision.config.storage import MinioSettings, QdrantSettings
from mergenvision.domain import storage_keys
from mergenvision.domain.enums import PersonPhotoStatus, SampleStatus
from mergenvision.domain.errors import (
    CrossStoreConsistencyError,
    ReconciliationRequiredError,
    VectorIndexError,
)
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database.unit_of_work import PostgresUnitOfWork
from mergenvision.infrastructure.object_storage.minio_adapter import MinioObjectStorageAdapter
from mergenvision.infrastructure.vector_index.qdrant_adapter import QdrantVectorIndexAdapter
from mergenvision.ports.object_storage import ObjectNamespace
from mergenvision.ports.unit_of_work import UnitOfWork
from tests.integration.storage_helpers import (
    EnrollmentSeed,
    make_landmarks,
    retire_active_seed_profiles,
    sample_vector,
    seed_enrollment_base,
    sha256_bytes,
)

if not os.environ.get("MERGENVISION_DATABASE_URL"):
    pytest.skip(
        "MERGENVISION_DATABASE_URL not set; skipping cross-store integration tests",
        allow_module_level=True,
    )

if not os.environ.get("MINIO_ENDPOINT"):
    pytest.skip(
        "MINIO_ENDPOINT not set; skipping cross-store integration tests",
        allow_module_level=True,
    )

if not os.environ.get("QDRANT_URL"):
    pytest.skip(
        "QDRANT_URL not set; skipping cross-store integration tests",
        allow_module_level=True,
    )


@pytest_asyncio.fixture
async def session_factory(db_engine):
    return async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def uow_factory(session_factory):
    def factory() -> UnitOfWork:
        return PostgresUnitOfWork(session_factory)

    return factory


@pytest_asyncio.fixture
async def object_storage():
    settings = MinioSettings()
    adapter = MinioObjectStorageAdapter(settings)
    await adapter.ensure_ready()
    try:
        yield adapter
    finally:
        pass


@pytest_asyncio.fixture
async def vector_index():
    settings = QdrantSettings()
    adapter = QdrantVectorIndexAdapter(settings)
    await adapter.ensure_ready()
    try:
        yield adapter
    finally:
        await adapter.close()


@pytest_asyncio.fixture
async def persistence_service(uow_factory, object_storage, vector_index):
    return EnrollmentPersistenceService(
        uow_factory=uow_factory,
        object_storage=object_storage,
        vector_index=vector_index,
    )


@pytest_asyncio.fixture(autouse=True)
async def _retire_seed_profiles_after_test(uow_factory):
    yield
    await retire_active_seed_profiles(uow_factory)


async def _seed_base(uow_factory) -> EnrollmentSeed:
    async with uow_factory() as uow:
        seed = await seed_enrollment_base(uow)
        await uow.commit()
    return seed


def _build_command(seed: EnrollmentSeed, photo_id: UUID, sample_id: UUID) -> PersistEnrollmentArtifactCommand:
    source_bytes = b"cross-store-enrollment-photo"
    mime = "image/jpeg"
    embedding = sample_vector()
    return PersistEnrollmentArtifactCommand(
        process_id=seed.process_id,
        person_id=seed.person_id,
        face_identity_id=seed.face_identity_id,
        inference_profile_id=seed.inference_profile_id,
        photo_id=photo_id,
        sample_id=sample_id,
        source_bytes=source_bytes,
        verified_mime_type=mime,
        content_sha256=sha256_bytes(source_bytes),
        file_size_bytes=len(source_bytes),
        width=640,
        height=480,
        is_primary=False,
        bbox_x=100,
        bbox_y=80,
        bbox_width=200,
        bbox_height=200,
        landmarks=make_landmarks(),
        detection_confidence=0.99,
        quality_score=0.95,
        embedding=embedding,
    )


async def _activated_record_statuses(uow_factory, photo_id: UUID, sample_id: UUID):
    async with uow_factory() as uow:
        photo = await uow.person_photo.get_by_id_any_status(photo_id)
        sample = await uow.face_sample.get_by_id_any_status(sample_id)
    return photo, sample


@pytest.mark.asyncio
async def test_happy_path_persists_to_all_three_stores(
    persistence_service,
    uow_factory,
    object_storage,
    vector_index,
):
    seed = await _seed_base(uow_factory)
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    command = _build_command(seed, photo_id, sample_id)

    result = await persistence_service.persist(command)

    assert result.photo_id == photo_id
    assert result.sample_id == sample_id
    assert result.created_new_object is True

    photo, sample = await _activated_record_statuses(uow_factory, photo_id, sample_id)
    assert photo is not None
    assert sample is not None
    assert photo.status == PersonPhotoStatus.ACTIVE
    assert sample.status == SampleStatus.ACTIVE
    assert photo.deleted_at is None
    assert sample.deleted_at is None

    info = await object_storage.stat(ObjectNamespace.PERSON_PHOTOS, result.object_key)
    assert info is not None
    assert info.content_sha256 == command.content_sha256

    states = await vector_index.get_points([sample_id])
    assert len(states) == 1
    assert states[0].active is True


@pytest.mark.asyncio
async def test_retry_is_idempotent(
    persistence_service,
    uow_factory,
    vector_index,
):
    seed = await _seed_base(uow_factory)
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    command = _build_command(seed, photo_id, sample_id)

    first = await persistence_service.persist(command)
    second = await persistence_service.persist(command)

    assert first.photo_id == second.photo_id
    assert first.sample_id == second.sample_id
    assert second.created_new_object is False

    async with uow_factory() as uow:
        photos = await uow.person_photo.list_by_person(seed.person_id, limit=10, offset=0)
        samples = await uow.face_sample.list_active_by_identity(
            seed.face_identity_id, limit=10, offset=0
        )
    assert len(photos) == 1
    assert len(samples) == 1

    states = await vector_index.get_points([sample_id])
    assert len(states) == 1


@pytest.mark.asyncio
async def test_staging_failure_compensates_minio(
    persistence_service,
    uow_factory,
    object_storage,
):
    seed = await _seed_base(uow_factory)
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    command = _build_command(seed, photo_id, sample_id)
    object_key = storage_keys.build_person_photo_key(
        seed.person_id, photo_id, command.verified_mime_type
    )

    original_stage = persistence_service._stage_postgresql

    async def failing_stage(metadata, key, cmd):
        raise RuntimeError("database unavailable")

    persistence_service._stage_postgresql = failing_stage

    with pytest.raises(ReconciliationRequiredError):
        await persistence_service.persist(command)

    assert await object_storage.stat(ObjectNamespace.PERSON_PHOTOS, object_key) is None

    persistence_service._stage_postgresql = original_stage


@pytest.mark.asyncio
async def test_qdrant_failure_leaves_inactive_staging(
    persistence_service,
    uow_factory,
    object_storage,
    vector_index,
):
    seed = await _seed_base(uow_factory)
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    command = _build_command(seed, photo_id, sample_id)

    original_upsert = vector_index.upsert_points

    async def failing_upsert(points):
        raise VectorIndexError("qdrant down", retryable=True)

    vector_index.upsert_points = failing_upsert

    with pytest.raises(CrossStoreConsistencyError):
        await persistence_service.persist(command)

    photo, sample = await _activated_record_statuses(uow_factory, photo_id, sample_id)
    assert photo is not None
    assert sample is not None
    assert photo.status == PersonPhotoStatus.INACTIVE
    assert sample.status == SampleStatus.INACTIVE
    assert photo.deleted_at is None
    assert sample.deleted_at is None

    vector_index.upsert_points = original_upsert
