import asyncio
from uuid import UUID

import pytest
from pydantic import SecretStr

from mergenvision.config.storage import MinioSettings
from mergenvision.domain.errors import ObjectConflictError, ObjectStorageError
from mergenvision.infrastructure.object_storage.minio_adapter import MinioObjectStorageAdapter
from mergenvision.ports.object_storage import ObjectNamespace
from tests.unit.fakes import FakeObjectStorage


@pytest.fixture
def storage():
    return FakeObjectStorage()


@pytest.mark.asyncio
async def test_new_object_created(storage):
    outcome = await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        "people/pid/photos/phid/source.jpg",
        b"data",
        content_sha256="sha-1",
        content_type="image/jpeg",
        metadata={"person-id": "pid", "photo-id": "phid", "schema-version": "1"},
    )
    assert outcome.created is True
    assert outcome.idempotent_reuse is False
    assert outcome.info.content_sha256 == "sha-1"


@pytest.mark.asyncio
async def test_same_key_same_sha_is_idempotent(storage):
    key = "k1"
    await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        key,
        b"data",
        content_sha256="sha-1",
        content_type="image/jpeg",
        metadata={},
    )
    outcome = await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        key,
        b"data",
        content_sha256="sha-1",
        content_type="image/jpeg",
        metadata={},
    )
    assert outcome.created is False
    assert outcome.idempotent_reuse is True


@pytest.mark.asyncio
async def test_same_key_different_sha_raises_conflict(storage):
    key = "k1"
    await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        key,
        b"data",
        content_sha256="sha-1",
        content_type="image/jpeg",
        metadata={},
    )
    with pytest.raises(ObjectConflictError):
        await storage.put_if_absent_or_same(
            ObjectNamespace.PERSON_PHOTOS,
            key,
            b"different",
            content_sha256="sha-2",
            content_type="image/jpeg",
            metadata={},
        )


@pytest.mark.asyncio
async def test_delete_only_expected_sha(storage):
    key = "k1"
    await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        key,
        b"data",
        content_sha256="sha-1",
        content_type="image/jpeg",
        metadata={},
    )
    with pytest.raises(ObjectConflictError):
        await storage.delete_if_matches(
            ObjectNamespace.PERSON_PHOTOS, key, content_sha256="wrong"
        )
    await storage.delete_if_matches(
        ObjectNamespace.PERSON_PHOTOS, key, content_sha256="sha-1"
    )
    assert await storage.stat(ObjectNamespace.PERSON_PHOTOS, key) is None


@pytest.mark.asyncio
async def test_delete_missing_is_idempotent(storage):
    await storage.delete_if_matches(
        ObjectNamespace.PERSON_PHOTOS, "missing", content_sha256="sha-1"
    )


@pytest.mark.asyncio
async def test_get_bytes_round_trip(storage):
    key = "k1"
    await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        key,
        b"hello",
        content_sha256="sha-1",
        content_type="image/jpeg",
        metadata={},
    )
    data = await storage.get_bytes(ObjectNamespace.PERSON_PHOTOS, key)
    assert data == b"hello"


@pytest.mark.asyncio
async def test_metadata_exact_allowlist(storage):
    outcome = await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        "k1",
        b"data",
        content_sha256="sha-1",
        content_type="image/jpeg",
        metadata={
            "person-id": str(UUID(int=1)),
            "photo-id": str(UUID(int=2)),
            "schema-version": "1",
        },
    )
    assert "person-id" in outcome.info.metadata
    assert "photo-id" in outcome.info.metadata
    assert "content-sha256" in outcome.info.metadata
    assert "national-id" not in outcome.info.metadata
    assert "first-name" not in outcome.info.metadata


def _minio_adapter() -> MinioObjectStorageAdapter:
    return MinioObjectStorageAdapter(
        MinioSettings(
            endpoint="localhost:9000",
            access_key=SecretStr("access"),
            secret_key=SecretStr("secret"),
        )
    )


def test_adapter_rejects_national_id_metadata():
    adapter = _minio_adapter()
    with pytest.raises(ObjectStorageError):
        adapter._validate_metadata(
            ObjectNamespace.PERSON_PHOTOS, {"national-id": "123456"}
        )


def test_adapter_rejects_first_name_metadata():
    adapter = _minio_adapter()
    with pytest.raises(ObjectStorageError):
        adapter._validate_metadata(
            ObjectNamespace.PERSON_PHOTOS, {"first-name": "Ali"}
        )


def test_adapter_rejects_original_filename_metadata():
    adapter = _minio_adapter()
    with pytest.raises(ObjectStorageError):
        adapter._validate_metadata(
            ObjectNamespace.PERSON_PHOTOS, {"original-filename": "foo.jpg"}
        )


def test_adapter_accepts_person_photos_allowlist_metadata():
    adapter = _minio_adapter()
    adapter._validate_metadata(
        ObjectNamespace.PERSON_PHOTOS,
        {"person-id": str(UUID(int=1)), "photo-id": str(UUID(int=2)), "schema-version": "1"},
    )


def test_adapter_accepts_recognition_inputs_allowlist_metadata():
    adapter = _minio_adapter()
    adapter._validate_metadata(
        ObjectNamespace.RECOGNITION_INPUTS,
        {"process-id": str(UUID(int=1)), "schema-version": "1"},
    )


def test_adapter_rejects_extra_recognition_inputs_metadata():
    adapter = _minio_adapter()
    with pytest.raises(ObjectStorageError):
        adapter._validate_metadata(
            ObjectNamespace.RECOGNITION_INPUTS,
            {"process-id": str(UUID(int=1)), "photo-id": str(UUID(int=2))},
        )


@pytest.mark.asyncio
async def test_adapter_does_not_create_object_for_rejected_metadata():
    adapter = _minio_adapter()
    with pytest.raises(ObjectStorageError):
        await adapter.put_if_absent_or_same(
            ObjectNamespace.PERSON_PHOTOS,
            "people/pid/photos/phid/source.jpg",
            b"data",
            content_sha256="sha-1",
            content_type="image/jpeg",
            metadata={"national-id": "123456"},
        )


@pytest.mark.asyncio
async def test_bounded_concurrency_does_not_block_event_loop(storage):
    async def worker(n: int) -> int:
        await storage.put_if_absent_or_same(
            ObjectNamespace.PERSON_PHOTOS,
            f"key-{n}",
            b"x",
            content_sha256=f"sha-{n}",
            content_type="image/jpeg",
            metadata={},
        )
        return n

    start = asyncio.get_event_loop().time()
    results = await asyncio.gather(*(worker(i) for i in range(10)))
    elapsed = asyncio.get_event_loop().time() - start
    assert len(results) == 10
    assert elapsed < 1.0
