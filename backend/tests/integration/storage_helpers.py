from __future__ import annotations

import base64
import hashlib
import math
import os
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from mergenvision.domain.entities import (
    FaceIdentity,
    FaceSample,
    InferenceProfile,
    Person,
    PersonPhoto,
    ProcessRecord,
)
from mergenvision.domain.enums import (
    FaceIdentityStatus,
    PersonPhotoStatus,
    PersonStatus,
    ProcessStatus,
    SampleStatus,
)
from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector
from mergenvision.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class EnrollmentSeed:
    person_id: UUID
    face_identity_id: UUID
    inference_profile_id: UUID
    process_id: UUID


def new_protector() -> AesGcmNationalIdProtector:
    encryption_key = base64.b64encode(os.urandom(32)).decode("ascii")
    hmac_key = base64.b64encode(os.urandom(32)).decode("ascii")
    return AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key,
        hmac_key_b64=hmac_key,
    )


def _norm(values: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(x * x for x in values))
    if magnitude == 0:
        raise ValueError("zero vector")
    return [x / magnitude for x in values]


def sample_vector(values: list[float] | None = None) -> list[float]:
    base = values if values is not None else list(range(512))
    return _norm(base)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def seed_enrollment_base(uow: UnitOfWork) -> EnrollmentSeed:
    now = datetime.now(UTC)
    person_id = new_uuid7()
    face_identity_id = new_uuid7()
    inference_profile_id = new_uuid7()
    process_id = new_uuid7()
    protector = new_protector()
    raw = f"seed-{process_id}"
    protected = protector.protect(raw)

    person = Person(
        person_id=person_id,
        first_name="Ada",
        last_name="Lovelace",
        national_id_ciphertext=protected.ciphertext,
        national_id_lookup_hash=protected.lookup_hash,
        national_id_masked=protected.masked,
        additional_details={"department": "Research"},
        status=PersonStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    identity = FaceIdentity(
        face_identity_id=face_identity_id,
        person_id=person_id,
        status=FaceIdentityStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    profile = InferenceProfile(
        inference_profile_id=inference_profile_id,
        profile_name=f"seed-{inference_profile_id}",
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
        created_at=now,
    )
    process = ProcessRecord(
        process_id=process_id,
        process_type="enrollment",
        status=ProcessStatus.PENDING,
        inference_profile_id=inference_profile_id,
        created_at=now,
    )

    await uow.person.add(person)
    await uow.face_identity.add(identity)
    await uow.inference_profile.add(profile)
    await uow.process_record.add(process)
    return EnrollmentSeed(
        person_id=person_id,
        face_identity_id=face_identity_id,
        inference_profile_id=inference_profile_id,
        process_id=process_id,
    )


def _make_photo(
    photo_id: UUID,
    person_id: UUID,
    object_key: str,
    content_sha256: str,
    *,
    status: str = PersonPhotoStatus.ACTIVE,
) -> PersonPhoto:
    now = datetime.now(UTC)
    return PersonPhoto(
        photo_id=photo_id,
        person_id=person_id,
        enrollment_process_id=None,
        object_key=object_key,
        content_sha256=content_sha256,
        mime_type="image/jpeg",
        file_size_bytes=1234,
        width=100,
        height=100,
        is_primary=False,
        status=status,
        created_at=now,
        updated_at=now,
    )


def _make_sample(
    sample_id: UUID,
    face_identity_id: UUID,
    photo_id: UUID,
    inference_profile_id: UUID,
    *,
    status: str = SampleStatus.ACTIVE,
) -> FaceSample:
    return FaceSample(
        sample_id=sample_id,
        face_identity_id=face_identity_id,
        photo_id=photo_id,
        inference_profile_id=inference_profile_id,
        bbox_x=0,
        bbox_y=0,
        bbox_width=50,
        bbox_height=50,
        landmarks={"points": [{"x": 1.0, "y": 1.0}]},
        detection_confidence=0.99,
        quality_score=0.95,
        status=status,
        created_at=datetime.now(UTC),
    )


async def seed_active_photo_and_sample(
    uow: UnitOfWork,
    seed: EnrollmentSeed,
    photo_id: UUID,
    sample_id: UUID,
    object_key: str,
    content_sha256: str,
) -> None:
    photo = _make_photo(
        photo_id,
        seed.person_id,
        object_key,
        content_sha256,
        status=PersonPhotoStatus.ACTIVE,
    )
    sample = _make_sample(
        sample_id,
        seed.face_identity_id,
        photo_id,
        seed.inference_profile_id,
        status=SampleStatus.ACTIVE,
    )
    await uow.person_photo.add(photo)
    await uow.face_sample.add(sample)


async def retire_active_seed_profiles(
    uow_factory: Callable[[], AbstractAsyncContextManager[UnitOfWork]],
) -> None:
    async with uow_factory() as uow:
        for _ in range(100):
            active = await uow.inference_profile.get_active()
            if active is None or not active.profile_name.startswith("seed-"):
                break
            await uow.inference_profile.retire(active.inference_profile_id)
        await uow.commit()


def make_landmarks(count: int = 5) -> Sequence[dict[str, float]]:
    return [{"x": float(i + 1), "y": float(i + 1)} for i in range(count)]
