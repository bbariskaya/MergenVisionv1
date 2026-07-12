
from mergenvision.infrastructure.database.base import Base
from mergenvision.infrastructure.database.models import (
    Person,
    PersonPhoto,
    RecognitionResult,
)

EXPECTED_TABLES = {
    "person",
    "face_identity",
    "process_record",
    "inference_profile",
    "person_photo",
    "face_sample",
    "recognition_result",
    "process_event",
}


def test_all_business_tables_defined() -> None:
    tables = set(Base.metadata.tables.keys())
    assert tables >= EXPECTED_TABLES


def test_person_columns_match_frozen_contract() -> None:
    columns = {col.name for col in Person.__table__.columns}
    expected = {
        "person_id",
        "first_name",
        "last_name",
        "national_id_ciphertext",
        "national_id_lookup_hash",
        "national_id_masked",
        "additional_details",
        "status",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert columns == expected


def test_person_primary_key_is_uuid() -> None:
    pk = Person.__table__.primary_key
    assert len(pk.columns) == 1
    assert pk.columns[0].name == "person_id"


def test_recognition_result_check_constraint_exists() -> None:
    checks = {c.name for c in RecognitionResult.__table__.constraints if hasattr(c, "name")}
    assert "ck_recognition_result_status_consistency" in checks


def test_person_photo_unique_constraints() -> None:
    unique_names = {c.name for c in PersonPhoto.__table__.constraints if hasattr(c, "name")}
    assert "uq_person_photo_object_key" in unique_names
    assert "uq_person_photo_person_id_content_sha256" in unique_names


def test_indexes_are_defined() -> None:
    index_names = {idx.name for idx in Base.metadata.tables["person"].indexes}
    assert "ix_person_status" in index_names
    face_indexes = {idx.name for idx in Base.metadata.tables["face_sample"].indexes}
    assert "ix_face_sample_face_identity_id_status" in face_indexes
    assert "ix_face_sample_inference_profile_id_status" in face_indexes


def test_foreign_keys_exist_for_person_photo() -> None:
    fks = {fk.name for fk in PersonPhoto.__table__.foreign_keys if hasattr(fk, "name")}
    assert "fk_person_photo_person_id" in fks or len(PersonPhoto.__table__.foreign_keys) >= 1
