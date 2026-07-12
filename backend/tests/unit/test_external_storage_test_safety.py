import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from check_external_storage_test_safety import validate


def test_default_ephemeral_is_safe():
    errors = validate()
    assert errors == []


def test_external_endpoint_requires_opt_in():
    errors = validate(minio_endpoint="http://remote:9000")
    assert any("External" in e for e in errors)


def test_external_endpoint_allowed_with_guard():
    errors = validate(minio_endpoint="http://remote:9000", allow_destructive=True)
    assert not any("External" in e for e in errors)


def test_production_bucket_names_rejected():
    errors = validate(
        person_photos_bucket="mergenvision-person-photos",
        recognition_inputs_bucket="mergenvision-recognition-inputs",
    )
    assert any("production name" in e for e in errors)


def test_test_prefixed_bucket_names_accepted():
    errors = validate(
        person_photos_bucket="test_person_photos",
        recognition_inputs_bucket="recognition_inputs_test",
        face_collection="test_face_samples_v1",
    )
    assert errors == []


def test_production_collection_rejected():
    errors = validate(face_collection="mergenvision_face_samples_v1")
    assert any("production name" in e for e in errors)


def test_guard_rejects_production_names_via_canonical_env():
    """Guard must read the same canonical env names that the harness exports."""
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "check_external_storage_test_safety.py"
    env = os.environ.copy()
    env["MINIO_ENDPOINT"] = "http://localhost:9000"
    env["MINIO_PERSON_PHOTOS_BUCKET"] = "mergenvision-person-photos"
    env["MINIO_RECOGNITION_INPUTS_BUCKET"] = "mergenvision-recognition-inputs"
    env["QDRANT_URL"] = "http://localhost:6333"
    env["QDRANT_FACE_COLLECTION"] = "mergenvision_face_samples_v1"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "production name" in result.stderr
