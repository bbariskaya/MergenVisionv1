import math
from uuid import UUID

import pytest

from mergenvision.domain.errors import VectorContractError
from mergenvision.ports.vector_index import FaceVectorPoint, VectorPointState
from tests.unit.fakes import FakeVectorIndex


def _norm(v: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(x * x for x in v))
    return [x / magnitude for x in v]


def _sample_vector(values: list[float] | None = None) -> list[float]:
    base = values if values is not None else list(range(512))
    return _norm(base)


@pytest.fixture
def index():
    return FakeVectorIndex()


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
    assert isinstance(state, VectorPointState)
    assert state.sample_id == sample_id
    assert state.active is True


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
async def test_nan_inf_rejected(index):
    for bad in ([float("nan")] + [0.0] * 511, [float("inf")] + [0.0] * 511):
        with pytest.raises(VectorContractError):
            await index.upsert_points(
                [
                    FaceVectorPoint(
                        sample_id=UUID("12345678-1234-5678-1234-567812345678"),
                        face_identity_id=UUID("22345678-1234-5678-1234-567812345678"),
                        person_id=UUID("32345678-1234-5678-1234-567812345678"),
                        inference_profile_id=UUID("42345678-1234-5678-1234-567812345678"),
                        embedding=bad,
                        active=True,
                    )
                ]
            )


@pytest.mark.asyncio
async def test_zero_vector_rejected(index):
    with pytest.raises(VectorContractError):
        await index.upsert_points(
            [
                FaceVectorPoint(
                    sample_id=UUID("12345678-1234-5678-1234-567812345678"),
                    face_identity_id=UUID("22345678-1234-5678-1234-567812345678"),
                    person_id=UUID("32345678-1234-5678-1234-567812345678"),
                    inference_profile_id=UUID("42345678-1234-5678-1234-567812345678"),
                    embedding=[0.0] * 512,
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
    assert len(index.points) == 0


@pytest.mark.asyncio
async def test_search_filters_active_and_profile(index):
    profile_a = UUID("AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA")
    profile_b = UUID("BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB")
    sample_a = UUID("11111111-1111-1111-1111-111111111111")
    sample_b = UUID("22222222-2222-2222-2222-222222222222")
    sample_c = UUID("33333333-3333-3333-3333-333333333333")

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
                    embedding=_sample_vector(list(range(512, 1024))),
                    active=active,
                )
            ]
        )

    results = await index.search(
        _sample_vector(list(range(512))), profile_a, limit=10
    )
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
    payload = index.points[sample_id]["payload"]
    assert set(payload.keys()) == {
        "faceIdentityId",
        "sampleId",
        "personId",
        "inferenceProfileId",
        "active",
    }
    assert payload["sampleId"] == str(sample_id)
    assert "firstName" not in payload
    assert "nationalId" not in payload


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
