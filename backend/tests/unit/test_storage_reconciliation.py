from __future__ import annotations

import math
from datetime import UTC, datetime
from uuid import UUID

import pytest

from mergenvision.application.storage_reconciliation import (
    ReconciliationOutcome,
    ReconciliationRequiredError,
    StorageReconciliationService,
)
from mergenvision.domain import entities as domain
from mergenvision.domain.enums import PersonPhotoStatus, PersonStatus, SampleStatus
from mergenvision.domain.errors import ObjectStorageError, VectorIndexError
from mergenvision.ports.object_storage import ObjectNamespace
from mergenvision.ports.unit_of_work import UnitOfWork
from mergenvision.ports.vector_index import FaceVectorPoint
from tests.unit.fakes import (
    FakeFaceSampleRepository,
    FakeObjectStorage,
    FakeUnitOfWork,
    FakeVectorIndex,
    make_uow_factory,
)


def _norm(v: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(x * x for x in v))
    return [x / magnitude for x in v]


def _embedding() -> list[float]:
    return _norm(list(range(512)))


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
    return StorageReconciliationService(
        uow_factory=make_uow_factory(uow),
        object_storage=storage,
        vector_index=vector_index,
    )


def _seed(uow: FakeUnitOfWork) -> tuple[UUID, UUID, UUID, UUID, UUID, str]:
    now = datetime.now(UTC)
    person_id = UUID("12345678-1234-5678-1234-567812345678")
    identity_id = UUID("22345678-1234-5678-1234-567812345678")
    profile_id = UUID("32345678-1234-5678-1234-567812345678")
    photo_id = UUID("42345678-1234-5678-1234-567812345678")
    sample_id = UUID("52345678-1234-5678-1234-567812345678")
    object_key = f"people/{person_id}/photos/{photo_id}/source.jpg"

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
    uow.person_photo.photos[photo_id] = domain.PersonPhoto(
        photo_id=photo_id,
        person_id=person_id,
        object_key=object_key,
        content_sha256="sha-1",
        mime_type="image/jpeg",
        file_size_bytes=100,
        width=100,
        height=100,
        is_primary=True,
        status=PersonPhotoStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    uow.face_sample.samples[sample_id] = domain.FaceSample(
        sample_id=sample_id,
        face_identity_id=identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        landmarks={"points": []},
        detection_confidence=0.9,
        quality_score=0.9,
        status=SampleStatus.ACTIVE,
        created_at=now,
    )
    return person_id, identity_id, profile_id, photo_id, sample_id, object_key


async def _seed_object(storage, object_key: str, sha: str = "sha-1") -> None:
    await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        object_key,
        b"data",
        content_sha256=sha,
        content_type="image/jpeg",
        metadata={"person-id": "p", "photo-id": "ph", "schema-version": "1"},
    )


async def _seed_qdrant(
    vector_index, sample_id, identity_id, person_id, profile_id, active=True
):
    await vector_index.upsert_points(
        [
            FaceVectorPoint(
                sample_id=sample_id,
                face_identity_id=identity_id,
                person_id=person_id,
                inference_profile_id=profile_id,
                embedding=_embedding(),
                active=active,
            )
        ]
    )


def _assert_no_raw_exception_details(result):
    assert "error" not in result.details
    for value in result.details.values():
        assert not isinstance(value, str) or "Traceback" not in value


@pytest.mark.asyncio
async def test_healthy(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_identity.identities[
            list(uow.face_identity.identities)[0]
        ].face_identity_id,
        uow.person.persons[list(uow.person.persons)[0]].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.HEALTHY
    assert result.details["sample_id"] == str(sample_id)
    _assert_no_raw_exception_details(result)


@pytest.mark.asyncio
async def test_staged_sample_activated_when_qdrant_active(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].deleted_at = None
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.REPAIRED
    assert uow.face_sample.samples[sample_id].status == SampleStatus.ACTIVE
    assert (
        uow.person_photo.photos[uow.face_sample.samples[sample_id].photo_id].status
        == PersonPhotoStatus.ACTIVE
    )


@pytest.mark.asyncio
async def test_staged_sample_activated_when_qdrant_inactive(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].deleted_at = None
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=False,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.REPAIRED
    assert vector_index.points[sample_id]["payload"]["active"] is True
    assert uow.face_sample.samples[sample_id].status == SampleStatus.ACTIVE
    assert (
        uow.person_photo.photos[uow.face_sample.samples[sample_id].photo_id].status
        == PersonPhotoStatus.ACTIVE
    )


@pytest.mark.asyncio
async def test_staged_sample_missing_qdrant_needs_reinference(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    await _seed_object(storage, object_key)

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.NEEDS_REINFERENCE
    assert uow.face_sample.samples[sample_id].status == SampleStatus.INACTIVE


@pytest.mark.asyncio
async def test_active_sample_missing_qdrant_needs_reindex(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    await _seed_object(storage, object_key)

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.NEEDS_REINDEX


@pytest.mark.asyncio
async def test_explicitly_deleted_sample_deactivates_qdrant(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = datetime.now(UTC)
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].deleted_at = datetime.now(UTC)
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=True,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.DEACTIVATED
    assert vector_index.points[sample_id]["payload"]["active"] is False
    assert uow.face_sample.samples[sample_id].status == SampleStatus.INACTIVE


@pytest.mark.asyncio
async def test_explicitly_deleted_photo_with_staged_sample_no_activation(
    service, uow, storage, vector_index
):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    photo_id = uow.face_sample.samples[sample_id].photo_id
    uow.person_photo.photos[photo_id].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[photo_id].deleted_at = datetime.now(UTC)
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[photo_id].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=True,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.DEACTIVATED
    assert vector_index.points[sample_id]["payload"]["active"] is False
    assert uow.person_photo.photos[photo_id].status == PersonPhotoStatus.INACTIVE
    assert uow.face_sample.samples[sample_id].status == SampleStatus.INACTIVE


@pytest.mark.asyncio
async def test_missing_sample_deactivates_orphan_qdrant(service, uow, storage, vector_index):
    orphan_id = UUID("99999999-9999-9999-9999-999999999999")
    await _seed_qdrant(
        vector_index,
        orphan_id,
        UUID("22345678-1234-5678-1234-567812345678"),
        UUID("12345678-1234-5678-1234-567812345678"),
        UUID("32345678-1234-5678-1234-567812345678"),
        active=True,
    )

    result = await service.reconcile_sample(orphan_id)

    assert result.outcome == ReconciliationOutcome.DEACTIVATED
    assert vector_index.points[orphan_id]["payload"]["active"] is False


@pytest.mark.asyncio
async def test_missing_object(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=True,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.MISSING_OBJECT
    assert vector_index.points[sample_id]["payload"]["active"] is False


@pytest.mark.asyncio
async def test_object_sha_mismatch(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    await _seed_object(storage, object_key, sha="different")
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=True,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.OBJECT_CONFLICT
    assert vector_index.points[sample_id]["payload"]["active"] is False


@pytest.mark.asyncio
async def test_payload_mismatch(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    await _seed_object(storage, object_key)
    await vector_index.upsert_points(
        [
            FaceVectorPoint(
                sample_id=sample_id,
                face_identity_id=UUID("AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"),
                person_id=uow.person_photo.photos[
                    uow.face_sample.samples[sample_id].photo_id
                ].person_id,
                inference_profile_id=uow.face_sample.samples[
                    sample_id
                ].inference_profile_id,
                embedding=_embedding(),
                active=True,
            )
        ]
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.PAYLOAD_CONFLICT
    assert vector_index.points[sample_id]["payload"]["active"] is False


@pytest.mark.asyncio
async def test_active_flag_mismatch_is_repaired(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=False,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.REPAIRED
    assert vector_index.points[sample_id]["payload"]["active"] is True


@pytest.mark.asyncio
async def test_minio_unavailable_does_not_activate(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=True,
    )

    class FailingStorage(FakeObjectStorage):
        async def stat(self, namespace, object_key):
            raise ObjectStorageError("minio unavailable")

    service._object_storage = FailingStorage()
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].deleted_at = None

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.STORAGE_UNAVAILABLE
    assert uow.face_sample.samples[sample_id].status == SampleStatus.INACTIVE
    assert (
        uow.person_photo.photos[uow.face_sample.samples[sample_id].photo_id].status
        == PersonPhotoStatus.INACTIVE
    )


@pytest.mark.asyncio
async def test_qdrant_unavailable_is_not_healthy(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    await _seed_object(storage, object_key)

    class FailingIndex(FakeVectorIndex):
        async def get_points(self, sample_ids, *, with_vectors=False):
            raise VectorIndexError("qdrant unavailable", retryable=True)

    service._vector_index = FailingIndex()

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.STORAGE_UNAVAILABLE
    assert result.outcome not in (
        ReconciliationOutcome.HEALTHY,
        ReconciliationOutcome.NEEDS_REINDEX,
    )


@pytest.mark.asyncio
async def test_payload_identity_mismatch_deactivates_no_db_activation(
    service, uow, storage, vector_index
):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].deleted_at = None
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        UUID("AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"),
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=True,
    )

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.PAYLOAD_CONFLICT
    assert uow.face_sample.samples[sample_id].status == SampleStatus.INACTIVE
    assert vector_index.points[sample_id]["payload"]["active"] is False


@pytest.mark.asyncio
async def test_db_activation_failure_after_qdrant_active_compensates(
    service, uow, storage, vector_index
):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].deleted_at = None
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=False,
    )

    class NonActivatingSampleRepository(FakeFaceSampleRepository):
        async def activate(self, sample_id):
            return None

    failing_uow = FakeUnitOfWork()
    failing_uow.person = uow.person
    failing_uow.face_identity = uow.face_identity
    failing_uow.person_photo = uow.person_photo
    failing_uow.face_sample = NonActivatingSampleRepository()
    failing_uow.face_sample.samples = uow.face_sample.samples
    service._uow_factory = make_uow_factory(failing_uow)

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.MANUAL_REVIEW
    assert vector_index.points[sample_id]["payload"]["active"] is False


@pytest.mark.asyncio
async def test_db_and_qdrant_compensation_failure_preserves_primary(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[
        uow.face_sample.samples[sample_id].photo_id
    ].deleted_at = None
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[
            uow.face_sample.samples[sample_id].photo_id
        ].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=False,
    )

    class FailingUoW(FakeUnitOfWork):
        async def commit(self) -> None:
            raise RuntimeError("primary db failure")

    failing_uow = FailingUoW()
    failing_uow.person = uow.person
    failing_uow.face_identity = uow.face_identity
    failing_uow.person_photo = uow.person_photo
    failing_uow.face_sample = uow.face_sample

    class FailingIndex(FakeVectorIndex):
        async def set_active(self, sample_ids, *, active):
            if not active:
                raise VectorIndexError("compensation failure", retryable=True)
            return await super().set_active(sample_ids, active=active)

    failing_index = FailingIndex()
    failing_index.points = vector_index.points

    service._uow_factory = make_uow_factory(failing_uow)
    service._vector_index = failing_index

    with pytest.raises(ReconciliationRequiredError) as exc_info:
        await service.reconcile_sample(sample_id)

    assert isinstance(exc_info.value.__cause__, RuntimeError)



@pytest.mark.asyncio
async def test_reconcile_photo_finds_active_staged_and_deleted_samples(
    service, uow, storage, vector_index
):
    (
        person_id,
        identity_id,
        profile_id,
        photo_id,
        active_sample_id,
        object_key,
    ) = _seed(uow)
    now = datetime.now(UTC)
    staged_sample_id = UUID("62345678-1234-5678-1234-567812345678")
    deleted_sample_id = UUID("72345678-1234-5678-1234-567812345678")
    uow.face_sample.samples[staged_sample_id] = domain.FaceSample(
        sample_id=staged_sample_id,
        face_identity_id=identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        landmarks={"points": []},
        detection_confidence=0.9,
        quality_score=0.9,
        status=SampleStatus.INACTIVE,
        created_at=now,
    )
    uow.face_sample.samples[deleted_sample_id] = domain.FaceSample(
        sample_id=deleted_sample_id,
        face_identity_id=identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        landmarks={"points": []},
        detection_confidence=0.9,
        quality_score=0.9,
        status=SampleStatus.INACTIVE,
        deleted_at=now,
        created_at=now,
    )
    await _seed_object(storage, object_key)
    for sample_id in (active_sample_id, staged_sample_id, deleted_sample_id):
        await _seed_qdrant(
            vector_index,
            sample_id,
            identity_id,
            person_id,
            profile_id,
            active=True,
        )

    results = await service.reconcile_photo(photo_id)

    outcomes = {r.sample_id: r.outcome for r in results}
    assert len(outcomes) == 3
    assert outcomes[active_sample_id] == ReconciliationOutcome.HEALTHY
    assert outcomes[staged_sample_id] == ReconciliationOutcome.REPAIRED
    assert outcomes[deleted_sample_id] == ReconciliationOutcome.DEACTIVATED


@pytest.mark.asyncio
async def test_reconcile_samples_empty_list_returns_empty(service):
    assert await service.reconcile_samples([]) == []


@pytest.mark.asyncio
async def test_reconcile_samples_respects_batch_limit(service, uow):
    service._max_batch_size = 2
    ids = [UUID(f"{i:08d}-0000-0000-0000-000000000000") for i in range(1, 5)]
    with pytest.raises(ReconciliationRequiredError):
        await service.reconcile_samples(ids)


class _InstrumentedStorage(FakeObjectStorage):
    def __init__(self, wrapped: FakeObjectStorage, uow: UnitOfWork) -> None:
        super().__init__()
        self.objects = wrapped.objects
        self._uow = uow

    async def stat(self, namespace, object_key):
        if self._uow.active:
            raise AssertionError("network call inside active UoW transaction")
        return await super().stat(namespace, object_key)

    async def put_if_absent_or_same(self, *args, **kwargs):
        if self._uow.active:
            raise AssertionError("network call inside active UoW transaction")
        return await super().put_if_absent_or_same(*args, **kwargs)


class _InstrumentedVectorIndex(FakeVectorIndex):
    def __init__(self, wrapped: FakeVectorIndex, uow: UnitOfWork) -> None:
        super().__init__()
        self.points = wrapped.points
        self._uow = uow

    async def get_points(self, sample_ids, *, with_vectors=False):
        if self._uow.active:
            raise AssertionError("network call inside active UoW transaction")
        return await super().get_points(sample_ids, with_vectors=with_vectors)

    async def set_active(self, sample_ids, *, active):
        if self._uow.active:
            raise AssertionError("network call inside active UoW transaction")
        return await super().set_active(sample_ids, active=active)


@pytest.mark.asyncio
async def test_no_network_calls_inside_db_transaction(uow, storage, vector_index):
    _seed(uow)
    instrumented_storage = _InstrumentedStorage(storage, uow)
    instrumented_index = _InstrumentedVectorIndex(vector_index, uow)
    service = StorageReconciliationService(
        uow_factory=make_uow_factory(uow),
        object_storage=instrumented_storage,
        vector_index=instrumented_index,
    )

    await service.reconcile_samples(list(uow.face_sample.samples.keys()))


@pytest.mark.asyncio
async def test_explicitly_deleted_ignores_minio_unavailable(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = datetime.now(UTC)
    await _seed_qdrant(
        vector_index, sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[uow.face_sample.samples[sample_id].photo_id].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=True,
    )

    class UnavailableStorage(FakeObjectStorage):
        async def stat(self, namespace, object_key):
            raise ObjectStorageError("MinIO is unavailable")

    service._object_storage = UnavailableStorage()

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.DEACTIVATED
    point = vector_index.points[sample_id]
    assert point["payload"]["active"] is False


@pytest.mark.asyncio
async def test_staged_repair_deactivates_qdrant_when_lifecycle_drifts(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    uow.person_photo.photos[uow.face_sample.samples[sample_id].photo_id].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[uow.face_sample.samples[sample_id].photo_id].deleted_at = None
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index, sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[uow.face_sample.samples[sample_id].photo_id].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=False,
    )

    class DriftOnActivateVectorIndex(FakeVectorIndex):
        async def set_active(self, sample_ids, *, active):
            if active and sample_ids == [sample_id]:
                uow.face_sample.samples[sample_id].deleted_at = datetime.now(UTC)
            return await super().set_active(sample_ids, active=active)

    drift_index = DriftOnActivateVectorIndex()
    drift_index.points = vector_index.points
    service._vector_index = drift_index

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.MANUAL_REVIEW
    assert result.details.get("reason") == "lifecycle_drifted_during_repair"
    point = vector_index.points[sample_id]
    assert point["payload"]["active"] is False


@pytest.mark.asyncio
async def test_lifecycle_drift_compensation_runs_after_uow_closes(service, uow, storage, vector_index):
    *_, sample_id, object_key = _seed(uow)
    uow.face_sample.samples[sample_id].status = SampleStatus.INACTIVE
    uow.face_sample.samples[sample_id].deleted_at = None
    photo_id = uow.face_sample.samples[sample_id].photo_id
    uow.person_photo.photos[photo_id].status = PersonPhotoStatus.INACTIVE
    uow.person_photo.photos[photo_id].deleted_at = None
    await _seed_object(storage, object_key)
    await _seed_qdrant(
        vector_index,
        sample_id,
        uow.face_sample.samples[sample_id].face_identity_id,
        uow.person_photo.photos[photo_id].person_id,
        uow.face_sample.samples[sample_id].inference_profile_id,
        active=False,
    )

    class UoWActiveGuardVectorIndex(FakeVectorIndex):
        async def set_active(self, sample_ids, *, active):
            if uow.active:
                raise AssertionError("vector_index.set_active called while UoW is active")
            if active and sample_ids == [sample_id]:
                uow.face_sample.samples[sample_id].deleted_at = datetime.now(UTC)
            return await super().set_active(sample_ids, active=active)

    guard = UoWActiveGuardVectorIndex()
    guard.points = vector_index.points
    service._vector_index = guard

    result = await service.reconcile_sample(sample_id)

    assert result.outcome == ReconciliationOutcome.MANUAL_REVIEW
    assert result.details.get("reason") == "lifecycle_drifted_during_repair"
    assert uow.person_photo.photos[photo_id].status == PersonPhotoStatus.INACTIVE
    assert uow.face_sample.samples[sample_id].status == SampleStatus.INACTIVE
    assert not uow.committed
    point = vector_index.points[sample_id]
    assert point["payload"]["active"] is False
