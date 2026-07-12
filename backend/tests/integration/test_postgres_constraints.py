import base64
import os
import random

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    RecognitionStatus,
    SampleStatus,
)
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database import models as orm
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector

PROTECTOR = AesGcmNationalIdProtector(
    encryption_key_b64=base64.b64encode(os.urandom(32)).decode("ascii"),
    hmac_key_b64=base64.b64encode(os.urandom(32)).decode("ascii"),
)


def _unique_national_id() -> str:
    return f"nat-{random.randint(100000000, 999999999)}"


def _make_person(national_id: str | None = None) -> orm.Person:
    raw = national_id or _unique_national_id()
    protected = PROTECTOR.protect(raw)
    return orm.Person(
        person_id=new_uuid7(),
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=protected.ciphertext,
        national_id_lookup_hash=protected.lookup_hash,
        national_id_masked=protected.masked,
        additional_details={},
        status=PersonStatus.ACTIVE,
    )


def _make_face_identity(person_id) -> orm.FaceIdentity:
    return orm.FaceIdentity(
        face_identity_id=new_uuid7(),
        person_id=person_id,
        status=FaceIdentityStatus.ACTIVE,
    )


def _make_profile(name: str = "default") -> orm.InferenceProfile:
    return orm.InferenceProfile(
        inference_profile_id=new_uuid7(),
        profile_name=name,
        detector_name="retinaface",
        detector_version="1",
        detector_artifact_sha256="sha",
        alignment_version="v1",
        embedder_name="arcface",
        embedder_version="1",
        embedder_artifact_sha256="sha",
        preprocessing_version="v1",
        embedding_dimension=512,
        distance_metric="cosine",
        match_threshold=0.65,
        is_active=True,
    )


def _make_photo(
    person_id,
    object_key: str,
    *,
    is_primary: bool = False,
    content_sha256: str | None = None,
) -> orm.PersonPhoto:
    return orm.PersonPhoto(
        photo_id=new_uuid7(),
        person_id=person_id,
        object_key=object_key,
        content_sha256=content_sha256 or ("sha" + object_key),
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=100,
        height=100,
        is_primary=is_primary,
        status=PersonPhotoStatus.ACTIVE,
    )


def _make_sample(face_identity_id, photo_id, profile_id) -> orm.FaceSample:
    return orm.FaceSample(
        sample_id=new_uuid7(),
        face_identity_id=face_identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=50,
        bbox_height=50,
        landmarks={},
        detection_confidence=0.99,
        quality_score=0.9,
        status=SampleStatus.ACTIVE,
    )


def _make_process() -> orm.ProcessRecord:
    return orm.ProcessRecord(
        process_id=new_uuid7(),
        process_type="identification",
        status=ProcessStatus.PENDING,
    )


@pytest.mark.asyncio
async def test_duplicate_national_id_lookup_hash_rejected(session):
    person1 = _make_person("same-id")
    person2 = _make_person("same-id")
    session.add(person1)
    await session.flush()
    session.add(person2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_second_face_identity_for_person_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    identity1 = _make_face_identity(person.person_id)
    identity2 = _make_face_identity(person.person_id)
    session.add(identity1)
    await session.flush()
    session.add(identity2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_object_key_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "same-key")
    photo2 = _make_photo(person.person_id, "same-key")
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_photo_content_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "key-1", content_sha256="dup-sha")
    photo2 = _make_photo(person.person_id, "key-2", content_sha256="dup-sha")
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_two_active_primary_photos_rejected(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo1 = _make_photo(person.person_id, "primary-1", is_primary=True)
    photo2 = _make_photo(person.person_id, "primary-2", is_primary=True)
    session.add(photo1)
    await session.flush()
    session.add(photo2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_two_active_primary_photos_different_persons_allowed(session):
    person1 = _make_person()
    person2 = _make_person()
    session.add_all([person1, person2])
    await session.flush()
    photo1 = _make_photo(person1.person_id, "primary-a", is_primary=True)
    photo2 = _make_photo(person2.person_id, "primary-b", is_primary=True)
    session.add_all([photo1, photo2])
    await session.flush()

    result = await session.execute(
        select(orm.PersonPhoto).where(orm.PersonPhoto.is_primary.is_(True))
    )
    assert len(result.scalars().all()) == 2


@pytest.mark.asyncio
async def test_duplicate_face_sample_photo_profile_rejected(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-photo")
    session.add(photo)
    await session.flush()
    sample1 = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample2 = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    session.add(sample1)
    await session.flush()
    session.add(sample2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_recognition_result_process_face_index_rejected(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    result1 = orm.RecognitionResult(
        result_id=new_uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    result2 = orm.RecognitionResult(
        result_id=new_uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result1)
    await session.flush()
    session.add(result2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_duplicate_process_event_sequence_rejected(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    event1 = orm.ProcessEvent(
        event_id=new_uuid7(),
        process_id=process.process_id,
        sequence_no=1,
        event_type="started",
    )
    event2 = orm.ProcessEvent(
        event_id=new_uuid7(),
        process_id=process.process_id,
        sequence_no=1,
        event_type="completed",
    )
    session.add(event1)
    await session.flush()
    session.add(event2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_photo_file_size_must_be_positive(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo = _make_photo(person.person_id, "bad-size")
    photo.file_size_bytes = 0
    session.add(photo)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_photo_dimensions_must_be_positive(session):
    person = _make_person()
    session.add(person)
    await session.flush()
    photo = _make_photo(person.person_id, "bad-width")
    photo.width = 0
    session.add(photo)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_face_sample_bbox_must_be_positive(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-bad")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.bbox_width = 0
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_detection_confidence_must_be_zero_to_one(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-conf")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.detection_confidence = 1.5
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_quality_score_must_be_zero_to_one_or_null(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "sample-quality")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    sample.quality_score = 1.5
    session.add(sample)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_inference_profile_dimension_must_be_positive(session):
    profile = _make_profile()
    profile.embedding_dimension = 0
    session.add(profile)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_input_size_positive(session):
    process = _make_process()
    process.input_size_bytes = 0
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_input_width_positive(session):
    process = _make_process()
    process.input_width = 0
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_process_detected_face_count_nonnegative(session):
    process = _make_process()
    process.detected_face_count = -1
    session.add(process)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_recognition_result_known_requires_references(session):
    process = _make_process()
    session.add(process)
    await session.flush()
    result = orm.RecognitionResult(
        result_id=new_uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.KNOWN,
        matched_face_identity_id=None,
        matched_sample_id=None,
        similarity_score=None,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_recognition_result_unknown_must_not_have_references(session):
    person = _make_person()
    profile = _make_profile()
    session.add_all([person, profile])
    await session.flush()
    identity = _make_face_identity(person.person_id)
    session.add(identity)
    await session.flush()
    photo = _make_photo(person.person_id, "unknown-refs")
    session.add(photo)
    await session.flush()
    sample = _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    session.add(sample)
    await session.flush()
    process = _make_process()
    session.add(process)
    await session.flush()
    result = orm.RecognitionResult(
        result_id=new_uuid7(),
        process_id=process.process_id,
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        matched_face_identity_id=identity.face_identity_id,
        matched_sample_id=sample.sample_id,
        similarity_score=0.5,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
    )
    session.add(result)
    with pytest.raises(IntegrityError):
        await session.flush()


def _get_foreign_keys(sync_conn):
    inspector = inspect(sync_conn)
    return {
        table: inspector.get_foreign_keys(table)
        for table in [
            "face_identity",
            "process_record",
            "person_photo",
            "face_sample",
            "recognition_result",
            "process_event",
        ]
    }


@pytest.mark.asyncio
async def test_no_broad_cascade_on_foreign_keys(db_engine):
    async with db_engine.begin() as conn:
        fks_by_table = await conn.run_sync(_get_foreign_keys)
    for _table, fks in fks_by_table.items():
        for fk in fks:
            assert fk.get("ondelete") is None
            assert fk.get("onupdate") is None
