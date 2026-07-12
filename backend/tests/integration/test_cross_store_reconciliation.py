from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mergenvision.application.enrollment_persistence import (
    EnrollmentPersistenceService,
    PersistEnrollmentArtifactCommand,
)
from mergenvision.application.storage_reconciliation import (
    ReconciliationOutcome,
    StorageReconciliationService,
)
from mergenvision.config.storage import MinioSettings, QdrantSettings
from mergenvision.domain import storage_keys
from mergenvision.domain.enums import PersonPhotoStatus, SampleStatus
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database.models import FaceSample, PersonPhoto
from mergenvision.infrastructure.database.unit_of_work import PostgresUnitOfWork
from mergenvision.infrastructure.object_storage.minio_adapter import MinioObjectStorageAdapter
from mergenvision.infrastructure.vector_index.qdrant_adapter import QdrantVectorIndexAdapter
from mergenvision.ports.object_storage import ObjectNamespace
from mergenvision.ports.unit_of_work import UnitOfWork
from mergenvision.ports.vector_index import FaceVectorPoint
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


@pytest_asyncio.fixture
async def reconciliation_service(uow_factory, object_storage, vector_index):
    return StorageReconciliationService(
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
    source_bytes = b"reconciliation-enrollment-photo"
    mime = "image/jpeg"
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
        embedding=sample_vector(),
    )


async def _persist_active(
    persistence_service,
    uow_factory,
    photo_id: UUID,
    sample_id: UUID,
) -> EnrollmentSeed:
    seed = await _seed_base(uow_factory)
    command = _build_command(seed, photo_id, sample_id)
    await persistence_service.persist(command)
    return seed


@pytest.mark.asyncio
async def test_healthy(
    persistence_service,
    reconciliation_service,
    uow_factory,
):
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    await _persist_active(persistence_service, uow_factory, photo_id, sample_id)

    result = await reconciliation_service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.HEALTHY


@pytest.mark.asyncio
async def test_active_flag_mismatch_is_repaired(
    persistence_service,
    reconciliation_service,
    uow_factory,
    vector_index,
):
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    await _persist_active(persistence_service, uow_factory, photo_id, sample_id)
    await vector_index.set_active([sample_id], active=False)

    result = await reconciliation_service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.REPAIRED
    states = await vector_index.get_points([sample_id])
    assert states[0].active is True


@pytest.mark.asyncio
async def test_explicitly_deleted_sample_deactivates_qdrant(
    persistence_service,
    reconciliation_service,
    uow_factory,
    vector_index,
):
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    await _persist_active(persistence_service, uow_factory, photo_id, sample_id)

    async with uow_factory() as uow:
        await uow.person_photo.deactivate(photo_id)
        await uow.face_sample.deactivate(sample_id)
        await uow.commit()

    result = await reconciliation_service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.DEACTIVATED
    states = await vector_index.get_points([sample_id])
    assert states[0].active is False

    async with uow_factory() as uow:
        photo = await uow.person_photo.get_by_id_any_status(photo_id)
        sample = await uow.face_sample.get_by_id_any_status(sample_id)
    assert photo.status == PersonPhotoStatus.INACTIVE
    assert sample.status == SampleStatus.INACTIVE


@pytest.mark.asyncio
async def test_missing_object(
    persistence_service,
    reconciliation_service,
    uow_factory,
    object_storage,
    vector_index,
):
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    seed = await _persist_active(persistence_service, uow_factory, photo_id, sample_id)
    object_key = storage_keys.build_person_photo_key(
        seed.person_id, photo_id, "image/jpeg"
    )

    await object_storage.delete_if_matches(
        ObjectNamespace.PERSON_PHOTOS, object_key, content_sha256=sha256_bytes(b"reconciliation-enrollment-photo")
    )

    result = await reconciliation_service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.MISSING_OBJECT
    states = await vector_index.get_points([sample_id])
    assert states[0].active is False


@pytest.mark.asyncio
async def test_missing_sample_deactivates_orphan_qdrant(
    reconciliation_service,
    vector_index,
):
    orphan_id = uuid4()
    await vector_index.upsert_points(
        [
            FaceVectorPoint(
                sample_id=orphan_id,
                face_identity_id=uuid4(),
                person_id=uuid4(),
                inference_profile_id=uuid4(),
                embedding=sample_vector(),
                active=True,
            )
        ]
    )

    result = await reconciliation_service.reconcile_sample(orphan_id)

    assert result.outcome == ReconciliationOutcome.DEACTIVATED
    states = await vector_index.get_points([orphan_id])
    assert states[0].active is False


@pytest.mark.asyncio
async def test_reconcile_photo_active_sample(
    persistence_service,
    reconciliation_service,
    uow_factory,
):
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    await _persist_active(persistence_service, uow_factory, photo_id, sample_id)

    results = await reconciliation_service.reconcile_photo(photo_id)

    assert len(results) == 1
    assert results[0].sample_id == sample_id
    assert results[0].outcome == ReconciliationOutcome.HEALTHY


@pytest.mark.asyncio
async def test_object_sha_mismatch_no_db_activation(
    persistence_service,
    reconciliation_service,
    uow_factory,
    object_storage,
    vector_index,
):
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    seed = await _persist_active(persistence_service, uow_factory, photo_id, sample_id)
    object_key = storage_keys.build_person_photo_key(seed.person_id, photo_id, "image/jpeg")

    await object_storage.delete_if_matches(
        ObjectNamespace.PERSON_PHOTOS,
        object_key,
        content_sha256=sha256_bytes(b"reconciliation-enrollment-photo"),
    )
    await object_storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        object_key,
        b"tampered-content",
        content_sha256=sha256_bytes(b"tampered-content"),
        content_type="image/jpeg",
        metadata={},
    )

    result = await reconciliation_service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.OBJECT_CONFLICT
    states = await vector_index.get_points([sample_id])
    assert states[0].active is False


@pytest.mark.asyncio
async def test_payload_mismatch_no_db_activation(
    persistence_service,
    reconciliation_service,
    uow_factory,
    vector_index,
):
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    await _persist_active(persistence_service, uow_factory, photo_id, sample_id)

    await vector_index.upsert_points(
        [
            FaceVectorPoint(
                sample_id=sample_id,
                face_identity_id=uuid4(),
                person_id=uuid4(),
                inference_profile_id=uuid4(),
                embedding=sample_vector(),
                active=True,
            )
        ]
    )

    result = await reconciliation_service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.PAYLOAD_CONFLICT
    states = await vector_index.get_points([sample_id])
    assert states[0].active is False


@pytest.mark.asyncio
async def test_explicitly_deleted_photo_with_staged_sample_no_activation(
    persistence_service,
    reconciliation_service,
    uow_factory,
    session_factory,
    vector_index,
):
    photo_id = new_uuid7()
    sample_id = new_uuid7()
    await _persist_active(persistence_service, uow_factory, photo_id, sample_id)

    async with session_factory() as session:
        await session.execute(
            sa.update(FaceSample)
            .where(FaceSample.sample_id == sample_id)
            .values(status=SampleStatus.INACTIVE, deleted_at=None)
        )
        await session.execute(
            sa.update(PersonPhoto)
            .where(PersonPhoto.photo_id == photo_id)
            .values(status=PersonPhotoStatus.INACTIVE, deleted_at=datetime.now(UTC))
        )
        await session.commit()

    result = await reconciliation_service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.DEACTIVATED
    states = await vector_index.get_points([sample_id])
    assert states[0].active is False

    async with uow_factory() as uow:
        photo = await uow.person_photo.get_by_id_any_status(photo_id)
        sample = await uow.face_sample.get_by_id_any_status(sample_id)
    assert photo.status == PersonPhotoStatus.INACTIVE
    assert sample.status == SampleStatus.INACTIVE


