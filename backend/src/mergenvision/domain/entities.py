from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(kw_only=True)
class Person:
    person_id: UUID
    first_name: str
    last_name: str
    national_id_ciphertext: bytes
    national_id_lookup_hash: str
    national_id_masked: str
    additional_details: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(kw_only=True)
class FaceIdentity:
    face_identity_id: UUID
    person_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(kw_only=True)
class ProcessRecord:
    process_id: UUID
    process_type: str
    status: str
    inference_profile_id: UUID | None = None
    input_object_key: str | None = None
    input_sha256: str | None = None
    input_mime_type: str | None = None
    input_size_bytes: int | None = None
    input_width: int | None = None
    input_height: int | None = None
    retention_until: datetime | None = None
    detected_face_count: int | None = None
    error_code: str | None = None
    error_message_sanitized: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(kw_only=True)
class InferenceProfile:
    inference_profile_id: UUID
    profile_name: str
    detector_name: str
    detector_version: str
    detector_artifact_sha256: str
    alignment_version: str
    embedder_name: str
    embedder_version: str
    embedder_artifact_sha256: str
    preprocessing_version: str
    embedding_dimension: int
    distance_metric: str
    match_threshold: float
    is_active: bool
    created_at: datetime
    retired_at: datetime | None = None


@dataclass(kw_only=True)
class PersonPhoto:
    photo_id: UUID
    person_id: UUID
    enrollment_process_id: UUID | None = None
    object_key: str
    content_sha256: str
    mime_type: str
    file_size_bytes: int
    width: int
    height: int
    is_primary: bool
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(kw_only=True)
class FaceSample:
    sample_id: UUID
    face_identity_id: UUID
    photo_id: UUID
    inference_profile_id: UUID
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    landmarks: dict[str, Any]
    detection_confidence: float
    quality_score: float | None = None
    status: str
    created_at: datetime
    deleted_at: datetime | None = None


@dataclass(kw_only=True)
class RecognitionResult:
    result_id: UUID
    process_id: UUID
    face_index: int
    recognition_status: str
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    detection_confidence: float
    threshold_used: float
    matched_face_identity_id: UUID | None = None
    matched_sample_id: UUID | None = None
    similarity_score: float | None = None
    created_at: datetime


@dataclass(kw_only=True)
class ProcessEvent:
    event_id: UUID
    process_id: UUID
    sequence_no: int
    event_type: str
    details: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime
