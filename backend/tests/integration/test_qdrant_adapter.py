from __future__ import annotations

import contextlib
import math
import os
from uuid import UUID, uuid4

import httpx
import pytest
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from mergenvision.config.storage import QdrantSettings
from mergenvision.domain.errors import VectorContractError, VectorIndexError
from mergenvision.infrastructure.vector_index.qdrant_adapter import QdrantVectorIndexAdapter
from mergenvision.ports.vector_index import FaceVectorPoint

if not os.environ.get("QDRANT_URL"):
    pytest.skip(
        "QDRANT_URL not set; skipping real Qdrant integration tests",
        allow_module_level=True,
    )


def _norm(v: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(x * x for x in v))
    return [x / magnitude for x in v]


def _sample_vector(values: list[float] | None = None) -> list[float]:
    base = values if values is not None else list(range(512))
    return _norm(base)


@pytest.fixture
async def index():
    settings = QdrantSettings()
    adapter = QdrantVectorIndexAdapter(settings)
    await adapter.ensure_ready()
    try:
        yield adapter
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_upsert_and_get_point(index):
    sample_id = UUID("12345678-1234-5678-1234-567812345678")
    embedding = _sample_vector()
    await index.upsert_points(
        [
            FaceVectorPoint(
                sample_id=sample_id,
                face_identity_id=UUID("22345678-1234-5678-1234-567812345678"),
                person_id=UUID("32345678-1234-5678-1234-567812345678"),
                inference_profile_id=UUID("42345678-1234-5678-1234-567812345678"),
                embedding=embedding,
                active=True,
            )
        ]
    )
    states = await index.get_points([sample_id])
    assert len(states) == 1
    state = states[0]
    assert state.sample_id == sample_id
    assert state.active is True
    assert state.present is True


@pytest.mark.asyncio
async def test_wrong_dimensions_rejected(index):
    with pytest.raises(VectorContractError):
        await index.upsert_points(
            [
                FaceVectorPoint(
                    sample_id=UUID("12345678-1234-5678-1234-567812345678"),
                    face_identity_id=UUID("22345678-1234-5678-1234-567812345678"),
                    person_id=UUID("32345678-1234-5678-1234-567812345678"),
                    inference_profile_id=UUID("42345678-1234-5678-1234-567812345678"),
                    embedding=[0.0] * 100,
                    active=True,
                )
            ]
        )


@pytest.mark.asyncio
async def test_non_normalized_vector_rejected(index):
    with pytest.raises(VectorContractError):
        await index.upsert_points(
            [
                FaceVectorPoint(
                    sample_id=UUID("12345678-1234-5678-1234-567812345678"),
                    face_identity_id=UUID("22345678-1234-5678-1234-567812345678"),
                    person_id=UUID("32345678-1234-5678-1234-567812345678"),
                    inference_profile_id=UUID("42345678-1234-5678-1234-567812345678"),
                    embedding=[2.0] + [0.0] * 511,
                    active=True,
                )
            ]
        )


@pytest.mark.asyncio
async def test_empty_batch_is_no_op(index):
    await index.upsert_points([])


@pytest.mark.asyncio
async def test_search_filters_active_and_profile(index):
    profile_a = UUID("AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA")
    profile_b = UUID("BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB")
    sample_a = UUID("11111111-1111-1111-1111-111111111111")
    sample_b = UUID("22222222-2222-2222-2222-222222222222")
    sample_c = UUID("33333333-3333-3333-3333-333333333333")
    vector = _sample_vector(list(range(512)))

    for sample_id, profile_id, active in [
        (sample_a, profile_a, True),
        (sample_b, profile_a, False),
        (sample_c, profile_b, True),
    ]:
        await index.upsert_points(
            [
                FaceVectorPoint(
                    sample_id=sample_id,
                    face_identity_id=UUID("22345678-1234-5678-1234-567812345678"),
                    person_id=UUID("32345678-1234-5678-1234-567812345678"),
                    inference_profile_id=profile_id,
                    embedding=vector,
                    active=active,
                )
            ]
        )

    results = await index.search(vector, profile_a, limit=10)
    ids = {r.sample_id for r in results}
    assert sample_a in ids
    assert sample_b not in ids
    assert sample_c not in ids


@pytest.mark.asyncio
async def test_payload_contains_exact_fields_no_pii(index):
    sample_id = UUID("12345678-1234-5678-1234-567812345678")
    await index.upsert_points(
        [
            FaceVectorPoint(
                sample_id=sample_id,
                face_identity_id=UUID("22345678-1234-5678-1234-567812345678"),
                person_id=UUID("32345678-1234-5678-1234-567812345678"),
                inference_profile_id=UUID("42345678-1234-5678-1234-567812345678"),
                embedding=_sample_vector(),
                active=True,
            )
        ]
    )
    settings = QdrantSettings()
    client = AsyncQdrantClient(settings.url)
    try:
        records = await client.retrieve(
            collection_name=settings.face_collection,
            ids=[str(sample_id)],
            with_payload=True,
            with_vectors=False,
        )
    finally:
        await client.close()
    assert len(records) == 1
    payload = records[0].payload or {}
    assert set(payload.keys()) == {
        "faceIdentityId",
        "sampleId",
        "personId",
        "inferenceProfileId",
        "active",
    }
    assert "firstName" not in payload
    assert "lastName" not in payload
    assert "nationalId" not in payload
    assert "originalFilename" not in payload


@pytest.mark.asyncio
async def test_set_active_and_delete_points(index):
    sample_id = UUID("12345678-1234-5678-1234-567812345678")
    await index.upsert_points(
        [
            FaceVectorPoint(
                sample_id=sample_id,
                face_identity_id=UUID("22345678-1234-5678-1234-567812345678"),
                person_id=UUID("32345678-1234-5678-1234-567812345678"),
                inference_profile_id=UUID("42345678-1234-5678-1234-567812345678"),
                embedding=_sample_vector(),
                active=True,
            )
        ]
    )
    await index.set_active([sample_id], active=False)
    states = await index.get_points([sample_id])
    assert states[0].active is False
    await index.delete_points([sample_id])
    assert len(await index.get_points([sample_id])) == 0


@pytest.mark.asyncio
async def test_collection_contract_mismatch_on_distance():
    qsettings = QdrantSettings()
    bad_collection = f"test_bad_distance_{uuid4().hex}"
    client = AsyncQdrantClient(qsettings.url)
    try:
        with contextlib.suppress(Exception):
            await client.create_collection(
                collection_name=bad_collection,
                vectors_config=models.VectorParams(
                    size=512,
                    distance=models.Distance.EUCLID,
                ),
            )
    finally:
        await client.close()
    bad_settings = QdrantSettings(url=qsettings.url, face_collection=bad_collection)
    adapter = QdrantVectorIndexAdapter(bad_settings)
    try:
        with pytest.raises(VectorContractError):
            await adapter.ensure_ready()
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_collection_contract_mismatch_on_dimension():
    qsettings = QdrantSettings()
    bad_collection = f"test_bad_dimension_{uuid4().hex}"
    client = AsyncQdrantClient(qsettings.url)
    try:
        with contextlib.suppress(Exception):
            await client.create_collection(
                collection_name=bad_collection,
                vectors_config=models.VectorParams(
                    size=256,
                    distance=models.Distance.COSINE,
                ),
            )
    finally:
        await client.close()
    bad_settings = QdrantSettings(url=qsettings.url, face_collection=bad_collection)
    adapter = QdrantVectorIndexAdapter(bad_settings)
    try:
        with pytest.raises(VectorContractError):
            await adapter.ensure_ready()
    finally:
        await adapter.close()
    # Mismatch must raise, never delete or recreate the collection.
    client = AsyncQdrantClient(qsettings.url)
    try:
        assert await client.collection_exists(bad_collection)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_collection_contract_matches_expected():
    settings = QdrantSettings()
    client = AsyncQdrantClient(settings.url)
    try:
        info = await client.get_collection(settings.face_collection)
    finally:
        await client.close()

    vectors = info.config.params.vectors
    assert isinstance(vectors, models.VectorParams)
    assert vectors.size == 512
    assert vectors.distance == models.Distance.COSINE

    hnsw = info.config.hnsw_config
    assert hnsw.m == 16
    assert hnsw.ef_construct == 128
    assert hnsw.full_scan_threshold == 10000


@pytest.mark.asyncio
async def test_payload_indexes_exact():
    settings = QdrantSettings()
    client = AsyncQdrantClient(settings.url)
    try:
        info = await client.get_collection(settings.face_collection)
    finally:
        await client.close()

    schema = info.payload_schema or {}
    expected = {
        "faceIdentityId": models.PayloadSchemaType.KEYWORD,
        "personId": models.PayloadSchemaType.KEYWORD,
        "inferenceProfileId": models.PayloadSchemaType.KEYWORD,
        "active": models.PayloadSchemaType.BOOL,
    }
    for field, kind in expected.items():
        assert field in schema, f"Missing payload index {field}"
        assert schema[field].data_type == kind, f"Unexpected type for {field}"

    assert "sampleId" not in schema


@pytest.mark.asyncio
async def test_payload_index_creation_failure_raises():
    settings = QdrantSettings()
    adapter = QdrantVectorIndexAdapter(settings)

    async def failing_create_payload_index(*args, **kwargs):
        raise UnexpectedResponse(
            status_code=500,
            reason_phrase="Internal Server Error",
            content=b"index creation failed",
            headers=httpx.Headers(),
        )

    adapter._client.create_payload_index = failing_create_payload_index
    try:
        with pytest.raises(VectorIndexError):
            await adapter.ensure_ready()
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_ensure_ready_validates_existing_payload_indexes():
    settings = QdrantSettings()
    adapter = QdrantVectorIndexAdapter(settings)
    await adapter.ensure_ready()
    # Second call must be idempotent and validate exact schema.
    await adapter.ensure_ready()
    with contextlib.suppress(RuntimeError):
        await adapter.close()
