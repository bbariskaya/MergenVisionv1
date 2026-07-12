from dataclasses import fields
from datetime import UTC, datetime
from uuid import UUID, uuid7

from mergenvision.domain.entities import (
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessEvent,
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


def test_status_constants_are_strings() -> None:
    assert PersonStatus.ACTIVE == "active"
    assert PersonStatus.INACTIVE == "inactive"
    assert FaceIdentityStatus.ACTIVE == "active"
    assert ProcessStatus.PENDING == "pending"
    assert ProcessStatus.PROCESSING == "processing"
    assert ProcessStatus.COMPLETED == "completed"
    assert ProcessStatus.FAILED == "failed"
    assert RecognitionStatus.KNOWN == "known"
    assert RecognitionStatus.UNKNOWN == "unknown"


def test_person_entity_fields() -> None:
    now = datetime.now(UTC)
    entity = Person(
        person_id=uuid7(),
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=b"ct",
        national_id_lookup_hash="hash",
        national_id_masked="*******1234",
        additional_details={"department": "Research"},
        status=PersonStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    assert isinstance(entity.person_id, UUID)
    assert entity.status == PersonStatus.ACTIVE
    assert len(fields(Person)) == 11


def test_recognition_result_known_requires_references() -> None:
    result = RecognitionResult(
        result_id=uuid7(),
        process_id=uuid7(),
        face_index=0,
        matched_face_identity_id=uuid7(),
        matched_sample_id=uuid7(),
        recognition_status=RecognitionStatus.KNOWN,
        bbox_x=10,
        bbox_y=20,
        bbox_width=100,
        bbox_height=100,
        detection_confidence=0.99,
        similarity_score=0.85,
        threshold_used=0.70,
        created_at=datetime.now(UTC),
    )
    assert result.recognition_status == RecognitionStatus.KNOWN
    assert result.similarity_score is not None


def test_recognition_result_unknown_has_no_references() -> None:
    result = RecognitionResult(
        result_id=uuid7(),
        process_id=uuid7(),
        face_index=0,
        recognition_status=RecognitionStatus.UNKNOWN,
        bbox_x=10,
        bbox_y=20,
        bbox_width=100,
        bbox_height=100,
        detection_confidence=0.99,
        threshold_used=0.70,
        created_at=datetime.now(UTC),
    )
    assert result.recognition_status == RecognitionStatus.UNKNOWN
    assert result.matched_face_identity_id is None
    assert result.matched_sample_id is None
    assert result.similarity_score is None


def test_process_event_default_details() -> None:
    event = ProcessEvent(
        event_id=uuid7(),
        process_id=uuid7(),
        sequence_no=1,
        event_type="started",
        occurred_at=datetime.now(UTC),
    )
    assert event.details == {}


def test_inference_profile_entity() -> None:
    profile = InferenceProfile(
        inference_profile_id=uuid7(),
        profile_name="retinaface-arcface-v1",
        detector_name="retinaface",
        detector_version="1.0",
        detector_artifact_sha256="sha",
        alignment_version="v1",
        embedder_name="arcface",
        embedder_version="1.0",
        embedder_artifact_sha256="sha",
        preprocessing_version="v1",
        embedding_dimension=512,
        distance_metric="cosine",
        match_threshold=0.65,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    assert profile.embedding_dimension == 512
    assert profile.is_active is True


def test_face_sample_entity_landmarks() -> None:
    sample = FaceSample(
        sample_id=uuid7(),
        face_identity_id=uuid7(),
        photo_id=uuid7(),
        inference_profile_id=uuid7(),
        bbox_x=0,
        bbox_y=0,
        bbox_width=100,
        bbox_height=100,
        landmarks={"left_eye": [10, 10]},
        detection_confidence=0.98,
        quality_score=0.91,
        status=SampleStatus.ACTIVE,
        created_at=datetime.now(UTC),
    )
    assert sample.landmarks == {"left_eye": [10, 10]}


def test_person_photo_entity() -> None:
    photo = PersonPhoto(
        photo_id=uuid7(),
        person_id=uuid7(),
        object_key="people/test/source.jpg",
        content_sha256="sha",
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=1920,
        height=1080,
        is_primary=True,
        status=PersonPhotoStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert photo.is_primary is True
