from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from mergenvision.domain.ids import new_uuid7
from mergenvision.infrastructure.database.base import Base


class Person(Base):
    __tablename__ = "person"

    person_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    first_name: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    last_name: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    national_id_ciphertext: sa.orm.Mapped[bytes] = sa.orm.mapped_column(
        sa.LargeBinary, nullable=False
    )
    national_id_lookup_hash: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(64), nullable=False, unique=True
    )
    national_id_masked: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    additional_details: sa.orm.Mapped[dict[str, Any]] = sa.orm.mapped_column(
        JSONB, nullable=False, default=dict
    )
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    deleted_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.Index("ix_person_status", "status"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
    )


class FaceIdentity(Base):
    __tablename__ = "face_identity"

    face_identity_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    person_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True),
        sa.ForeignKey("person.person_id"),
        nullable=False,
        unique=True,
    )
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    deleted_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.Index("ix_face_identity_status", "status"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
    )


class InferenceProfile(Base):
    __tablename__ = "inference_profile"

    inference_profile_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    profile_name: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(255), nullable=False, unique=True
    )
    detector_name: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    detector_version: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    detector_artifact_sha256: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(64), nullable=False
    )
    alignment_version: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    embedder_name: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(255), nullable=False)
    embedder_version: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    embedder_artifact_sha256: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(64), nullable=False
    )
    preprocessing_version: sa.orm.Mapped[str] = sa.orm.mapped_column(
        sa.String(64), nullable=False
    )
    embedding_dimension: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    distance_metric: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    match_threshold: sa.orm.Mapped[float] = sa.orm.mapped_column(sa.REAL, nullable=False)
    is_active: sa.orm.Mapped[bool] = sa.orm.mapped_column(sa.Boolean, nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    retired_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.CheckConstraint("embedding_dimension > 0", name="embedding_dimension_positive"),
    )


class ProcessRecord(Base):
    __tablename__ = "process_record"

    process_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    process_type: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    inference_profile_id: sa.orm.Mapped[UUID | None] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("inference_profile.inference_profile_id"), nullable=True
    )
    input_object_key: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.Text, nullable=True)
    input_sha256: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.String(64), nullable=True)
    input_mime_type: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.String(64), nullable=True)
    input_size_bytes: sa.orm.Mapped[int | None] = sa.orm.mapped_column(sa.BigInteger, nullable=True)
    input_width: sa.orm.Mapped[int | None] = sa.orm.mapped_column(sa.Integer, nullable=True)
    input_height: sa.orm.Mapped[int | None] = sa.orm.mapped_column(sa.Integer, nullable=True)
    retention_until: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    detected_face_count: sa.orm.Mapped[int | None] = sa.orm.mapped_column(sa.Integer, nullable=True)
    error_code: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.String(64), nullable=True)
    error_message_sanitized: sa.orm.Mapped[str | None] = sa.orm.mapped_column(sa.Text, nullable=True)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    started_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    completed_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.Index("ix_process_record_process_type_status_created_at", "process_type", "status", "created_at"),
        sa.Index("ix_process_record_created_at", "created_at"),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="status",
        ),
        sa.CheckConstraint(
            "input_size_bytes IS NULL OR input_size_bytes > 0",
            name="input_size_positive",
        ),
        sa.CheckConstraint(
            "input_width IS NULL OR input_width > 0",
            name="input_width_positive",
        ),
        sa.CheckConstraint(
            "input_height IS NULL OR input_height > 0",
            name="input_height_positive",
        ),
        sa.CheckConstraint(
            "detected_face_count IS NULL OR detected_face_count >= 0",
            name="detected_face_count_nonnegative",
        ),
    )


class PersonPhoto(Base):
    __tablename__ = "person_photo"

    photo_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    person_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("person.person_id"), nullable=False
    )
    enrollment_process_id: sa.orm.Mapped[UUID | None] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("process_record.process_id"), nullable=True
    )
    object_key: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.Text, nullable=False, unique=True)
    content_sha256: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    mime_type: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    file_size_bytes: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.BigInteger, nullable=False)
    width: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    height: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    is_primary: sa.orm.Mapped[bool] = sa.orm.mapped_column(sa.Boolean, nullable=False)
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    deleted_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.UniqueConstraint("person_id", "content_sha256", name="uq_person_photo_person_id_content_sha256"),
        sa.Index("ix_person_photo_person_id_status", "person_id", "status"),
        sa.Index(
            "ix_uq_person_photo_active_primary",
            "person_id",
            unique=True,
            postgresql_where=sa.and_(
                sa.text("is_primary = true"),
                sa.text("status = 'active'"),
                sa.text("deleted_at IS NULL"),
            ),
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
        sa.CheckConstraint("file_size_bytes > 0", name="file_size_positive"),
        sa.CheckConstraint("width > 0", name="width_positive"),
        sa.CheckConstraint("height > 0", name="height_positive"),
    )


class FaceSample(Base):
    __tablename__ = "face_sample"

    sample_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    face_identity_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("face_identity.face_identity_id"), nullable=False
    )
    photo_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("person_photo.photo_id"), nullable=False
    )
    inference_profile_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("inference_profile.inference_profile_id"), nullable=False
    )
    bbox_x: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_y: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_width: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_height: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    landmarks: sa.orm.Mapped[dict[str, Any]] = sa.orm.mapped_column(JSONB, nullable=False, default=dict)
    detection_confidence: sa.orm.Mapped[float] = sa.orm.mapped_column(sa.REAL, nullable=False)
    quality_score: sa.orm.Mapped[float | None] = sa.orm.mapped_column(sa.REAL, nullable=True)
    status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(32), nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    deleted_at: sa.orm.Mapped[datetime | None] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "photo_id", "inference_profile_id", name="uq_face_sample_photo_id_inference_profile_id"
        ),
        sa.Index("ix_face_sample_face_identity_id_status", "face_identity_id", "status"),
        sa.Index("ix_face_sample_inference_profile_id_status", "inference_profile_id", "status"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
        sa.CheckConstraint("bbox_width > 0", name="bbox_width_positive"),
        sa.CheckConstraint("bbox_height > 0", name="bbox_height_positive"),
        sa.CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="detection_confidence_range",
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="quality_score_range",
        ),
    )


class RecognitionResult(Base):
    __tablename__ = "recognition_result"

    result_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    process_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("process_record.process_id"), nullable=False
    )
    face_index: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    matched_face_identity_id: sa.orm.Mapped[UUID | None] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("face_identity.face_identity_id"), nullable=True
    )
    matched_sample_id: sa.orm.Mapped[UUID | None] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("face_sample.sample_id"), nullable=True
    )
    recognition_status: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(16), nullable=False)
    bbox_x: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_y: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_width: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    bbox_height: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    detection_confidence: sa.orm.Mapped[float] = sa.orm.mapped_column(sa.REAL, nullable=False)
    similarity_score: sa.orm.Mapped[float | None] = sa.orm.mapped_column(sa.REAL, nullable=True)
    threshold_used: sa.orm.Mapped[float] = sa.orm.mapped_column(sa.REAL, nullable=False)
    created_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        sa.UniqueConstraint("process_id", "face_index", name="uq_recognition_result_process_id_face_index"),
        sa.Index("ix_recognition_result_matched_face_identity_id_created_at", "matched_face_identity_id", "created_at"),
        sa.Index("ix_recognition_result_matched_sample_id", "matched_sample_id"),
        sa.Index("ix_recognition_result_recognition_status_created_at", "recognition_status", "created_at"),
        sa.CheckConstraint(
            "recognition_status IN ('known', 'unknown')",
            name="status_values",
        ),
        sa.CheckConstraint("bbox_width > 0", name="bbox_width_positive"),
        sa.CheckConstraint("bbox_height > 0", name="bbox_height_positive"),
        sa.CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="detection_confidence_range",
        ),
        sa.CheckConstraint(
            """
            (
                recognition_status = 'known'
                AND matched_face_identity_id IS NOT NULL
                AND matched_sample_id IS NOT NULL
                AND similarity_score IS NOT NULL
            )
            OR
            (
                recognition_status = 'unknown'
                AND matched_face_identity_id IS NULL
                AND matched_sample_id IS NULL
                AND similarity_score IS NULL
            )
            """,
            name="status_consistency",
        ),
        sa.CheckConstraint("face_index >= 0", name="face_index_nonnegative"),
    )


class ProcessEvent(Base):
    __tablename__ = "process_event"

    event_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    process_id: sa.orm.Mapped[UUID] = sa.orm.mapped_column(
        PG_UUID(as_uuid=True), sa.ForeignKey("process_record.process_id"), nullable=False
    )
    sequence_no: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, nullable=False)
    event_type: sa.orm.Mapped[str] = sa.orm.mapped_column(sa.String(64), nullable=False)
    details: sa.orm.Mapped[dict[str, Any]] = sa.orm.mapped_column(
        JSONB, nullable=False, default=dict
    )
    occurred_at: sa.orm.Mapped[datetime] = sa.orm.mapped_column(
        sa.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        sa.UniqueConstraint("process_id", "sequence_no", name="uq_process_event_process_id_sequence_no"),
        sa.Index("ix_process_event_occurred_at", "occurred_at"),
    )
