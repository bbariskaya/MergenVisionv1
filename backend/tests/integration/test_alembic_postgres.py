import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import inspect

from mergenvision.config.settings import Settings

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

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC = REPO_ROOT / ".venv" / "bin" / "alembic"


def _run_alembic(*command: str) -> None:
    settings = Settings()
    env = os.environ.copy()
    env["MERGENVISION_DATABASE_URL"] = settings.database_url
    subprocess.run(
        [str(ALEMBIC), "-c", "backend/alembic.ini", *command],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )


def _table_names(sync_conn):
    return set(inspect(sync_conn).get_table_names())


@pytest.mark.asyncio
async def test_alembic_upgrade_downgrade_reupgrade(db_engine):
    async with db_engine.begin() as conn:
        _run_alembic("downgrade", "base")
        tables_after_downgrade = await conn.run_sync(_table_names)
        assert EXPECTED_TABLES.isdisjoint(tables_after_downgrade)

        _run_alembic("upgrade", "head")
        tables_after_upgrade = await conn.run_sync(_table_names)
        assert tables_after_upgrade == EXPECTED_TABLES | {"alembic_version"}

        _run_alembic("downgrade", "base")
        _run_alembic("upgrade", "head")
        tables_after_reupgrade = await conn.run_sync(_table_names)
        assert tables_after_reupgrade == EXPECTED_TABLES | {"alembic_version"}


@pytest.mark.asyncio
async def test_alembic_check_is_clean_after_upgrade(db_engine):
    _run_alembic("upgrade", "head")
    _run_alembic("check")


def _gather_constraints_and_indexes(sync_conn):
    inspector = inspect(sync_conn)
    data = {}
    for table in [
        "person",
        "face_identity",
        "person_photo",
        "face_sample",
        "recognition_result",
        "process_event",
    ]:
        data[table] = {
            "unique": {c["name"] for c in inspector.get_unique_constraints(table)},
            "indexes": {idx["name"] for idx in inspector.get_indexes(table)},
            "checks": {c["name"] for c in inspector.get_check_constraints(table)},
        }
    return data


@pytest.mark.asyncio
async def test_required_constraints_and_indexes_exist(db_engine):
    _run_alembic("upgrade", "head")

    async with db_engine.begin() as conn:
        data = await conn.run_sync(_gather_constraints_and_indexes)

    assert "uq_person_national_id_lookup_hash" in data["person"]["unique"]
    assert "ix_person_status" in data["person"]["indexes"]

    assert "uq_face_identity_person_id" in data["face_identity"]["unique"]

    assert "uq_person_photo_object_key" in data["person_photo"]["unique"]
    assert "uq_person_photo_person_id_content_sha256" in data["person_photo"]["unique"]
    assert "ix_person_photo_person_id_status" in data["person_photo"]["indexes"]
    assert "ix_uq_person_photo_active_primary" in data["person_photo"]["indexes"]

    assert "uq_face_sample_photo_id_inference_profile_id" in data["face_sample"]["unique"]
    assert "ix_face_sample_face_identity_id_status" in data["face_sample"]["indexes"]
    assert "ix_face_sample_inference_profile_id_status" in data["face_sample"]["indexes"]

    assert "uq_recognition_result_process_id_face_index" in data["recognition_result"]["unique"]
    assert "ix_recognition_result_matched_face_identity_id_created_at" in data["recognition_result"]["indexes"]
    assert "ix_recognition_result_matched_sample_id" in data["recognition_result"]["indexes"]
    assert "ix_recognition_result_recognition_status_created_at" in data["recognition_result"]["indexes"]

    assert "uq_process_event_process_id_sequence_no" in data["process_event"]["unique"]
    assert "ix_process_event_occurred_at" in data["process_event"]["indexes"]

    assert "ck_recognition_result_status_consistency" in data["recognition_result"]["checks"]
    assert "ck_recognition_result_status_values" in data["recognition_result"]["checks"]
