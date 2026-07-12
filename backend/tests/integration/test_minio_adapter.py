from __future__ import annotations

import os
from uuid import UUID

import pytest

from mergenvision.config.storage import MinioSettings
from mergenvision.domain.errors import ObjectConflictError, ObjectStorageError
from mergenvision.infrastructure.object_storage.minio_adapter import MinioObjectStorageAdapter
from mergenvision.ports.object_storage import ObjectNamespace

if not os.environ.get("MINIO_ENDPOINT"):
    pytest.skip(
        "MINIO_ENDPOINT not set; skipping real MinIO integration tests",
        allow_module_level=True,
    )


@pytest.fixture
async def storage():
    settings = MinioSettings()
    adapter = MinioObjectStorageAdapter(settings)
    await adapter.ensure_ready()
    try:
        yield adapter
    finally:
        pass


@pytest.mark.asyncio
async def test_ensure_ready_creates_buckets(storage):
    outcome = await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        "ready-check/key.jpg",
        b"x",
        content_sha256="ready-sha",
        content_type="image/jpeg",
        metadata={"photo-id": str(UUID(int=1))},
    )
    assert outcome.created is True


@pytest.mark.asyncio
async def test_new_object_created(storage):
    outcome = await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        "people/pid/photos/phid/source.jpg",
        b"data",
        content_sha256="sha-1",
        content_type="image/jpeg",
        metadata={
            "person-id": str(UUID(int=1)),
            "photo-id": str(UUID(int=2)),
            "schema-version": "1",
        },
    )
    assert outcome.created is True
    assert outcome.idempotent_reuse is False
    assert outcome.info.content_sha256 == "sha-1"


@pytest.mark.asyncio
async def test_same_key_same_sha_is_idempotent(storage):
    key = "idempotent/key.jpg"
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
    key = "conflict/key.jpg"
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
    key = "delete/key.jpg"
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
        ObjectNamespace.PERSON_PHOTOS, "missing/key.jpg", content_sha256="sha-1"
    )


@pytest.mark.asyncio
async def test_get_bytes_round_trip(storage):
    key = "roundtrip/key.jpg"
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
async def test_get_missing_raises(storage):
    with pytest.raises(ObjectStorageError):
        await storage.get_bytes(ObjectNamespace.PERSON_PHOTOS, "missing/nowhere.jpg")


@pytest.mark.asyncio
async def test_metadata_allowlist_is_pii_free(storage):
    outcome = await storage.put_if_absent_or_same(
        ObjectNamespace.PERSON_PHOTOS,
        "metadata/key.jpg",
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
    assert "firstName" not in outcome.info.metadata
    assert "lastName" not in outcome.info.metadata
    assert "original-filename" not in outcome.info.metadata


@pytest.mark.asyncio
async def test_recognition_inputs_namespace(storage):
    key = "recognition/input.jpg"
    outcome = await storage.put_if_absent_or_same(
        ObjectNamespace.RECOGNITION_INPUTS,
        key,
        b"input",
        content_sha256="input-sha",
        content_type="image/jpeg",
        metadata={"process-id": str(UUID(int=3))},
    )
    assert outcome.created is True
    info = await storage.stat(ObjectNamespace.RECOGNITION_INPUTS, key)
    assert info is not None
    assert info.size_bytes == 5


@pytest.mark.parametrize("bad_key", ["national-id", "first-name", "original-filename"])
@pytest.mark.asyncio
async def test_rejected_pii_metadata_does_not_create_object(storage, bad_key):
    key = f"pii-rejected/{bad_key}.jpg"
    with pytest.raises(ObjectStorageError):
        await storage.put_if_absent_or_same(
            ObjectNamespace.PERSON_PHOTOS,
            key,
            b"data",
            content_sha256="sha-1",
            content_type="image/jpeg",
            metadata={bad_key: "sensitive"},
        )
    assert await storage.stat(ObjectNamespace.PERSON_PHOTOS, key) is None
