"""Phase 1 initial schema: eight frozen business tables.

This revision is fully explicit. It does not depend on runtime ORM metadata,
so future model changes cannot silently alter the initial schema.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001_phase1_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "person",
        sa.Column("person_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("national_id_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("national_id_lookup_hash", sa.String(64), nullable=False),
        sa.Column("national_id_masked", sa.String(255), nullable=False),
        sa.Column("additional_details", JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("person_id", name="pk_person"),
        sa.UniqueConstraint("national_id_lookup_hash", name="uq_person_national_id_lookup_hash"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
    )
    op.create_index("ix_person_status", "person", ["status"])

    op.create_table(
        "face_identity",
        sa.Column("face_identity_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("face_identity_id", name="pk_face_identity"),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["person.person_id"],
            name="fk_face_identity_person_id_person",
        ),
        sa.UniqueConstraint("person_id", name="uq_face_identity_person_id"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
    )
    op.create_index("ix_face_identity_status", "face_identity", ["status"])

    op.create_table(
        "inference_profile",
        sa.Column("inference_profile_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_name", sa.String(255), nullable=False),
        sa.Column("detector_name", sa.String(255), nullable=False),
        sa.Column("detector_version", sa.String(64), nullable=False),
        sa.Column("detector_artifact_sha256", sa.String(64), nullable=False),
        sa.Column("alignment_version", sa.String(64), nullable=False),
        sa.Column("embedder_name", sa.String(255), nullable=False),
        sa.Column("embedder_version", sa.String(64), nullable=False),
        sa.Column("embedder_artifact_sha256", sa.String(64), nullable=False),
        sa.Column("preprocessing_version", sa.String(64), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("distance_metric", sa.String(32), nullable=False),
        sa.Column("match_threshold", sa.REAL(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("inference_profile_id", name="pk_inference_profile"),
        sa.UniqueConstraint("profile_name", name="uq_inference_profile_profile_name"),
        sa.CheckConstraint("embedding_dimension > 0", name="embedding_dimension_positive"),
    )

    op.create_table(
        "process_record",
        sa.Column("process_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("process_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("inference_profile_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("input_object_key", sa.Text(), nullable=True),
        sa.Column("input_sha256", sa.String(64), nullable=True),
        sa.Column("input_mime_type", sa.String(64), nullable=True),
        sa.Column("input_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("input_width", sa.Integer(), nullable=True),
        sa.Column("input_height", sa.Integer(), nullable=True),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detected_face_count", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message_sanitized", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("process_id", name="pk_process_record"),
        sa.ForeignKeyConstraint(
            ["inference_profile_id"],
            ["inference_profile.inference_profile_id"],
            name="fk_process_record_inference_profile_id_inference_profile",
        ),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="status"),
        sa.CheckConstraint(
            "input_size_bytes IS NULL OR input_size_bytes > 0",
            name="input_size_positive",
        ),
        sa.CheckConstraint("input_width IS NULL OR input_width > 0", name="input_width_positive"),
        sa.CheckConstraint("input_height IS NULL OR input_height > 0", name="input_height_positive"),
        sa.CheckConstraint(
            "detected_face_count IS NULL OR detected_face_count >= 0",
            name="detected_face_count_nonnegative",
        ),
    )
    op.create_index(
        "ix_process_record_process_type_status_created_at",
        "process_record",
        ["process_type", "status", "created_at"],
    )
    op.create_index("ix_process_record_created_at", "process_record", ["created_at"])

    op.create_table(
        "person_photo",
        sa.Column("photo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_process_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("photo_id", name="pk_person_photo"),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["person.person_id"],
            name="fk_person_photo_person_id_person",
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_process_id"],
            ["process_record.process_id"],
            name="fk_person_photo_enrollment_process_id_process_record",
        ),
        sa.UniqueConstraint("object_key", name="uq_person_photo_object_key"),
        sa.UniqueConstraint(
            "person_id",
            "content_sha256",
            name="uq_person_photo_person_id_content_sha256",
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="status"),
        sa.CheckConstraint("file_size_bytes > 0", name="file_size_positive"),
        sa.CheckConstraint("width > 0", name="width_positive"),
        sa.CheckConstraint("height > 0", name="height_positive"),
    )
    op.create_index(
        "ix_person_photo_person_id_status",
        "person_photo",
        ["person_id", "status"],
    )
    op.create_index(
        "ix_uq_person_photo_active_primary",
        "person_photo",
        ["person_id"],
        unique=True,
        postgresql_where=sa.text(
            "is_primary = true AND status = 'active' AND deleted_at IS NULL"
        ),
    )

    op.create_table(
        "face_sample",
        sa.Column("sample_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("face_identity_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("photo_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("inference_profile_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("bbox_x", sa.Integer(), nullable=False),
        sa.Column("bbox_y", sa.Integer(), nullable=False),
        sa.Column("bbox_width", sa.Integer(), nullable=False),
        sa.Column("bbox_height", sa.Integer(), nullable=False),
        sa.Column("landmarks", JSONB(), nullable=False),
        sa.Column("detection_confidence", sa.REAL(), nullable=False),
        sa.Column("quality_score", sa.REAL(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("sample_id", name="pk_face_sample"),
        sa.ForeignKeyConstraint(
            ["face_identity_id"],
            ["face_identity.face_identity_id"],
            name="fk_face_sample_face_identity_id_face_identity",
        ),
        sa.ForeignKeyConstraint(
            ["photo_id"],
            ["person_photo.photo_id"],
            name="fk_face_sample_photo_id_person_photo",
        ),
        sa.ForeignKeyConstraint(
            ["inference_profile_id"],
            ["inference_profile.inference_profile_id"],
            name="fk_face_sample_inference_profile_id_inference_profile",
        ),
        sa.UniqueConstraint(
            "photo_id",
            "inference_profile_id",
            name="uq_face_sample_photo_id_inference_profile_id",
        ),
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
    op.create_index(
        "ix_face_sample_face_identity_id_status",
        "face_sample",
        ["face_identity_id", "status"],
    )
    op.create_index(
        "ix_face_sample_inference_profile_id_status",
        "face_sample",
        ["inference_profile_id", "status"],
    )

    op.create_table(
        "recognition_result",
        sa.Column("result_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("process_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("face_index", sa.Integer(), nullable=False),
        sa.Column("matched_face_identity_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("matched_sample_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("recognition_status", sa.String(16), nullable=False),
        sa.Column("bbox_x", sa.Integer(), nullable=False),
        sa.Column("bbox_y", sa.Integer(), nullable=False),
        sa.Column("bbox_width", sa.Integer(), nullable=False),
        sa.Column("bbox_height", sa.Integer(), nullable=False),
        sa.Column("detection_confidence", sa.REAL(), nullable=False),
        sa.Column("similarity_score", sa.REAL(), nullable=True),
        sa.Column("threshold_used", sa.REAL(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("result_id", name="pk_recognition_result"),
        sa.ForeignKeyConstraint(
            ["process_id"],
            ["process_record.process_id"],
            name="fk_recognition_result_process_id_process_record",
        ),
        sa.ForeignKeyConstraint(
            ["matched_face_identity_id"],
            ["face_identity.face_identity_id"],
            name="fk_recognition_result_matched_face_identity_id_face_identity",
        ),
        sa.ForeignKeyConstraint(
            ["matched_sample_id"],
            ["face_sample.sample_id"],
            name="fk_recognition_result_matched_sample_id_face_sample",
        ),
        sa.UniqueConstraint(
            "process_id",
            "face_index",
            name="uq_recognition_result_process_id_face_index",
        ),
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
    op.create_index(
        "ix_recognition_result_matched_face_identity_id_created_at",
        "recognition_result",
        ["matched_face_identity_id", "created_at"],
    )
    op.create_index(
        "ix_recognition_result_matched_sample_id",
        "recognition_result",
        ["matched_sample_id"],
    )
    op.create_index(
        "ix_recognition_result_recognition_status_created_at",
        "recognition_result",
        ["recognition_status", "created_at"],
    )

    op.create_table(
        "process_event",
        sa.Column("event_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("process_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("details", JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id", name="pk_process_event"),
        sa.ForeignKeyConstraint(
            ["process_id"],
            ["process_record.process_id"],
            name="fk_process_event_process_id_process_record",
        ),
        sa.UniqueConstraint(
            "process_id",
            "sequence_no",
            name="uq_process_event_process_id_sequence_no",
        ),
    )
    op.create_index(
        "ix_process_event_occurred_at",
        "process_event",
        ["occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("process_event")
    op.drop_table("recognition_result")
    op.drop_table("face_sample")
    op.drop_table("person_photo")
    op.drop_table("process_record")
    op.drop_table("inference_profile")
    op.drop_table("face_identity")
    op.drop_table("person")
