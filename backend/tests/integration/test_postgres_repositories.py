import asyncio
import base64
import os
import random
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
    ProcessRecord,
    RecognitionResult,
)
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    RecognitionStatus,
    SampleStatus,
)
from mergenvision.domain.errors import ConflictError, RepositoryError
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database import models as orm
from mergenvision.infrastructure.database.repositories import (
    PostgresFaceIdentityRepository,
    PostgresFaceSampleRepository,
    PostgresInferenceProfileRepository,
    PostgresPersonPhotoRepository,
    PostgresPersonRepository,
    PostgresProcessEventRepository,
    PostgresProcessRecordRepository,
    PostgresRecognitionResultRepository,
)
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector
from mergenvision.ports.national_id import NationalIdProtectedValue


def _key() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


@pytest.fixture
def protector() -> AesGcmNationalIdProtector:
    return AesGcmNationalIdProtector(
        encryption_key_b64=_key(),
        hmac_key_b64=_key(),
    )


def _unique_id() -> str:
    return f"id-{random.randint(100000000, 999999999)}"


def _make_person(protector: AesGcmNationalIdProtector, raw: str | None = None) -> Person:
    raw_id = raw or _unique_id()
    protected = protector.protect(raw_id)
    return Person(
        person_id=new_uuid7(),
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=protected.ciphertext,
        national_id_lookup_hash=protected.lookup_hash,
        national_id_masked=protected.masked,
        additional_details={"department": "Research"},
        status=PersonStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_face_identity(person_id) -> FaceIdentity:
    return FaceIdentity(
        face_identity_id=new_uuid7(),
        person_id=person_id,
        status=FaceIdentityStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_profile(name: str = "profile") -> InferenceProfile:
    return InferenceProfile(
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
        created_at=datetime.now(UTC),
    )


def _make_photo(person_id, object_key: str, *, is_primary: bool = False) -> PersonPhoto:
    return PersonPhoto(
        photo_id=new_uuid7(),
        person_id=person_id,
        object_key=object_key,
        content_sha256="sha" + object_key,
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=100,
        height=100,
        is_primary=is_primary,
        status=PersonPhotoStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_process(process_type: str = "identification") -> ProcessRecord:
    return ProcessRecord(
        process_id=new_uuid7(),
        process_type=process_type,
        status=ProcessStatus.PENDING,
        created_at=datetime.now(UTC),
    )


def _make_sample(identity_id, photo_id, profile_id) -> FaceSample:
    return FaceSample(
        sample_id=new_uuid7(),
        face_identity_id=identity_id,
        photo_id=photo_id,
        inference_profile_id=profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=50,
        bbox_height=50,
        landmarks={"left_eye": [10, 10]},
        detection_confidence=0.99,
        quality_score=0.9,
        status=SampleStatus.ACTIVE,
        created_at=datetime.now(UTC),
    )


def _make_result(
    process_id,
    face_index: int,
    status: str,
    *,
    identity_id=None,
    sample_id=None,
    similarity=None,
) -> RecognitionResult:
    return RecognitionResult(
        result_id=new_uuid7(),
        process_id=process_id,
        face_index=face_index,
        recognition_status=status,
        matched_face_identity_id=identity_id,
        matched_sample_id=sample_id,
        similarity_score=similarity,
        bbox_x=0,
        bbox_y=0,
        bbox_width=10,
        bbox_height=10,
        detection_confidence=0.9,
        threshold_used=0.7,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_person_repository_crud(session: AsyncSession, protector: AesGcmNationalIdProtector):
    repo = PostgresPersonRepository(session)
    person = _make_person(protector)
    created = await repo.add(person)
    assert created.person_id == person.person_id

    fetched = await repo.get_by_id(created.person_id)
    assert fetched is not None
    assert fetched.national_id_lookup_hash == person.national_id_lookup_hash

    by_hash = await repo.get_by_national_id_lookup_hash(person.national_id_lookup_hash)
    assert by_hash is not None
    assert by_hash.person_id == person.person_id

    listed = await repo.list_active(limit=10, offset=0)
    assert any(p.person_id == person.person_id for p in listed)

    updated = await repo.update(
        person.person_id,
        first_name="Updated",
        additional_details={"department": "AI"},
    )
    assert updated is not None
    assert updated.first_name == "Updated"
    assert updated.additional_details == {"department": "AI"}

    deactivated = await repo.deactivate(person.person_id)
    assert deactivated is not None
    assert deactivated.status == PersonStatus.INACTIVE

    not_found = await repo.get_by_id(person.person_id)
    assert not_found is None


@pytest.mark.asyncio
async def test_person_repository_duplicate_national_id_raises_conflict(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    repo = PostgresPersonRepository(session)
    person1 = _make_person(protector, raw="duplicate")
    person2 = _make_person(protector, raw="duplicate")
    await repo.add(person1)
    with pytest.raises(ConflictError):
        await repo.add(person2)


@pytest.mark.asyncio
async def test_face_identity_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    repo = PostgresFaceIdentityRepository(session)
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity = _make_face_identity(person.person_id)
    created = await repo.add(identity)
    assert created.face_identity_id == identity.face_identity_id

    fetched = await repo.get_by_id(created.face_identity_id)
    assert fetched is not None

    by_person = await repo.get_by_person_id(person.person_id)
    assert by_person is not None
    assert by_person.face_identity_id == created.face_identity_id

    deactivated = await repo.deactivate(created.face_identity_id)
    assert deactivated is not None
    assert deactivated.status == FaceIdentityStatus.INACTIVE


@pytest.mark.asyncio
async def test_inference_profile_repository(session: AsyncSession):
    repo = PostgresInferenceProfileRepository(session)
    profile = _make_profile("test-profile")
    created = await repo.add(profile)
    assert created.profile_name == "test-profile"

    fetched = await repo.get_by_id(created.inference_profile_id)
    assert fetched is not None

    by_name = await repo.get_by_name("test-profile")
    assert by_name is not None

    active = await repo.get_active()
    assert active is not None

    retired = await repo.retire(created.inference_profile_id)
    assert retired is not None
    assert retired.is_active is False


@pytest.mark.asyncio
async def test_process_record_repository(session: AsyncSession):
    repo = PostgresProcessRecordRepository(session)
    record = _make_process()
    created = await repo.add(record)
    assert created.status == ProcessStatus.PENDING

    started = await repo.mark_started(created.process_id)
    assert started is not None
    assert started.status == ProcessStatus.PROCESSING
    assert started.started_at is not None

    completed = await repo.mark_completed(
        created.process_id,
        detected_face_count=0,
    )
    assert completed is not None
    assert completed.status == ProcessStatus.COMPLETED
    assert completed.completed_at is not None
    assert completed.detected_face_count == 0

    failed_record = await repo.add(_make_process("identification"))
    failed = await repo.mark_failed(
        failed_record.process_id,
        error_code="ERR",
        error_message_sanitized="safe message",
    )
    assert failed is not None
    assert failed.status == ProcessStatus.FAILED


@pytest.mark.asyncio
async def test_person_photo_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo1 = await photo_repo.add(_make_photo(person.person_id, "photo-1"))
    photo2 = await photo_repo.add(_make_photo(person.person_id, "photo-2"))

    listed = await photo_repo.list_by_person(person.person_id, limit=10, offset=0)
    assert len(listed) == 2

    primary = await photo_repo.set_primary(photo1.photo_id)
    assert primary is not None
    assert primary.is_primary is True

    switch = await photo_repo.set_primary(photo2.photo_id)
    assert switch is not None
    assert switch.is_primary is True

    refreshed = await photo_repo.get_by_id(photo1.photo_id)
    assert refreshed is not None
    assert refreshed.is_primary is False

    deactivated = await photo_repo.deactivate(photo2.photo_id)
    assert deactivated is not None
    assert deactivated.status == PersonPhotoStatus.INACTIVE


@pytest.mark.asyncio
async def test_face_sample_repository(session: AsyncSession, protector: AesGcmNationalIdProtector):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity_repo = PostgresFaceIdentityRepository(session)
    identity = await identity_repo.add(_make_face_identity(person.person_id))

    profile_repo = PostgresInferenceProfileRepository(session)
    profile = await profile_repo.add(_make_profile("sample-profile"))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "sample-photo"))

    sample_repo = PostgresFaceSampleRepository(session)
    sample = await sample_repo.add(
        _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    )
    assert sample.sample_id is not None

    listed = await sample_repo.list_active_by_identity(
        identity.face_identity_id, limit=10, offset=0
    )
    assert len(listed) == 1

    deactivated = await sample_repo.deactivate(sample.sample_id)
    assert deactivated is not None
    assert deactivated.status == SampleStatus.INACTIVE


@pytest.mark.asyncio
async def test_recognition_result_repository(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity_repo = PostgresFaceIdentityRepository(session)
    identity = await identity_repo.add(_make_face_identity(person.person_id))

    profile_repo = PostgresInferenceProfileRepository(session)
    profile = await profile_repo.add(_make_profile("result-profile"))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "result-photo"))

    sample_repo = PostgresFaceSampleRepository(session)
    sample = await sample_repo.add(
        _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    )

    process_repo = PostgresProcessRecordRepository(session)
    process = await process_repo.add(_make_process())

    result_repo = PostgresRecognitionResultRepository(session)
    known = await result_repo.add(
        _make_result(
            process.process_id,
            0,
            RecognitionStatus.KNOWN,
            identity_id=identity.face_identity_id,
            sample_id=sample.sample_id,
            similarity=0.85,
        )
    )
    assert known.recognition_status == RecognitionStatus.KNOWN

    unknown = await result_repo.add(
        _make_result(process.process_id, 1, RecognitionStatus.UNKNOWN)
    )
    assert unknown.recognition_status == RecognitionStatus.UNKNOWN

    by_process = await result_repo.list_by_process(process.process_id)
    assert len(by_process) == 2

    history = await result_repo.list_history_by_identity(
        identity.face_identity_id, limit=10, offset=0
    )
    assert len(history) == 1
    assert history[0].result_id == known.result_id


@pytest.mark.asyncio
async def test_process_event_repository(session: AsyncSession):
    process_repo = PostgresProcessRecordRepository(session)
    process = await process_repo.add(_make_process())

    event_repo = PostgresProcessEventRepository(session)
    event1 = await event_repo.append(process.process_id, event_type="started")
    event2 = await event_repo.append(process.process_id, event_type="completed")

    assert event1.sequence_no == 1
    assert event2.sequence_no == 2

    listed = await event_repo.list_by_process(process.process_id, limit=10, offset=0)
    assert len(listed) == 2
    assert listed[0].sequence_no == 1
    assert listed[1].sequence_no == 2


@pytest.mark.asyncio
async def test_repository_does_not_auto_commit(
    session: AsyncSession,
    db_engine,
    protector: AesGcmNationalIdProtector,
):
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector))

    factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as new_session:
        result = await new_session.execute(
            select(orm.Person).where(orm.Person.person_id == person.person_id)
        )
        assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_raw_national_id_not_persisted(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    raw_id = "12345678901"
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector, raw=raw_id))

    result = await session.execute(
        select(
            orm.Person.national_id_ciphertext,
            orm.Person.national_id_lookup_hash,
            orm.Person.national_id_masked,
        ).where(orm.Person.person_id == person.person_id)
    )
    row = result.one()
    assert raw_id not in row.national_id_lookup_hash
    assert row.national_id_masked != raw_id
    assert row.national_id_masked == "*******8901"
    assert protector.reveal(
        protector.protect(raw_id)
    ) == raw_id


@pytest.mark.asyncio
async def test_stored_national_id_decrypts_to_normalized_raw_id_and_does_not_leak(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
    caplog: pytest.LogCaptureFixture,
):
    raw_id = "  12345678901  "
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector, raw=raw_id))

    result = await session.execute(
        select(
            orm.Person.national_id_ciphertext,
            orm.Person.national_id_lookup_hash,
            orm.Person.national_id_masked,
        ).where(orm.Person.person_id == person.person_id)
    )
    row = result.one()
    normalized_id = raw_id.strip()

    reconstructed = NationalIdProtectedValue(
        ciphertext=row.national_id_ciphertext,
        lookup_hash=row.national_id_lookup_hash,
        masked=row.national_id_masked,
    )
    revealed = protector.reveal(reconstructed)
    assert revealed == normalized_id

    assert normalized_id.encode("utf-8") not in row.national_id_ciphertext
    assert normalized_id not in row.national_id_lookup_hash
    assert normalized_id not in row.national_id_masked

    for record in caplog.records:
        message = record.getMessage()
        assert normalized_id not in message


@pytest.mark.asyncio
async def test_person_repository_atomic_national_id_update(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    repo = PostgresPersonRepository(session)
    person = await repo.add(_make_person(protector, raw="old-id-12345"))

    new_raw = "new-id-67890"
    new_protected = protector.protect(new_raw)
    updated = await repo.update_national_id(person.person_id, new_protected)
    assert updated is not None
    assert updated.national_id_lookup_hash == new_protected.lookup_hash
    assert updated.national_id_masked == new_protected.masked

    fetched = await session.execute(
        select(
            orm.Person.national_id_ciphertext,
            orm.Person.national_id_lookup_hash,
            orm.Person.national_id_masked,
        ).where(orm.Person.person_id == person.person_id)
    )
    row = fetched.one()
    assert row.national_id_lookup_hash == new_protected.lookup_hash
    revealed = protector.reveal(
        NationalIdProtectedValue(
            ciphertext=row.national_id_ciphertext,
            lookup_hash=row.national_id_lookup_hash,
            masked=row.national_id_masked,
        )
    )
    assert revealed == new_raw


@pytest.mark.asyncio
async def test_inference_profile_get_active_raises_on_multiple_active(session: AsyncSession):
    repo = PostgresInferenceProfileRepository(session)
    active_a = await repo.add(_make_profile(name="active-a"))
    active_b = await repo.add(_make_profile(name="active-b"))
    assert active_a.is_active is True
    assert active_b.is_active is True

    with pytest.raises(RepositoryError):
        await repo.get_active()


@pytest.mark.asyncio
async def test_person_photo_lifecycle_activate_and_deactivate(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "lifecycle-photo"))

    deactivated = await photo_repo.deactivate(photo.photo_id)
    assert deactivated is not None
    assert deactivated.status == PersonPhotoStatus.INACTIVE

    reactivated = await photo_repo.activate(photo.photo_id)
    assert reactivated is not None
    assert reactivated.status == PersonPhotoStatus.ACTIVE
    assert reactivated.deleted_at is None


@pytest.mark.asyncio
async def test_face_sample_lifecycle_activate_and_deactivate(
    session: AsyncSession,
    protector: AesGcmNationalIdProtector,
):
    person_repo = PostgresPersonRepository(session)
    person = await person_repo.add(_make_person(protector))

    identity_repo = PostgresFaceIdentityRepository(session)
    identity = await identity_repo.add(_make_face_identity(person.person_id))

    profile_repo = PostgresInferenceProfileRepository(session)
    profile = await profile_repo.add(_make_profile("lifecycle-profile"))

    photo_repo = PostgresPersonPhotoRepository(session)
    photo = await photo_repo.add(_make_photo(person.person_id, "lifecycle-sample-photo"))

    sample_repo = PostgresFaceSampleRepository(session)
    sample = await sample_repo.add(
        _make_sample(identity.face_identity_id, photo.photo_id, profile.inference_profile_id)
    )

    deactivated = await sample_repo.deactivate(sample.sample_id)
    assert deactivated is not None
    assert deactivated.status == SampleStatus.INACTIVE

    reactivated = await sample_repo.activate(sample.sample_id)
    assert reactivated is not None
    assert reactivated.status == SampleStatus.ACTIVE
    assert reactivated.deleted_at is None


@pytest.mark.asyncio
async def test_process_event_concurrent_appends_are_unique_and_sequential(db_engine):
    setup_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with setup_factory() as setup_session:
        process_repo = PostgresProcessRecordRepository(setup_session)
        process = await process_repo.add(_make_process())
        await setup_session.commit()

    async def append(event_type: str) -> ProcessEvent:
        factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with factory() as session:
            repo = PostgresProcessEventRepository(session)
            event = await repo.append(process.process_id, event_type=event_type)
            await session.commit()
            return event

    events = await asyncio.gather(append("a"), append("b"))
    sequence_numbers = sorted(e.sequence_no for e in events)
    assert sequence_numbers == [1, 2]

    verify_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with verify_factory() as verify_session:
        repo = PostgresProcessEventRepository(verify_session)
        listed = await repo.list_by_process(process.process_id, limit=10, offset=0)
        assert len(listed) == 2
        assert sorted(e.sequence_no for e in listed) == [1, 2]
