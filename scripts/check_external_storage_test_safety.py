#!/usr/bin/env python3
"""Validate external storage test configuration before destructive integration tests.

Default ephemeral containers are considered safe. If external MinIO/Qdrant endpoints
are configured, an explicit opt-in is required and test bucket/collection names must
use a `test_` prefix or `_test` suffix.
"""

import os
import sys
from urllib.parse import urlparse


_SAFE_HOSTS = {"localhost", "127.0.0.1", "::1"}
_PRODUCTION_BUCKET_NAMES = {
    "mergenvision-person-photos",
    "mergenvision-recognition-inputs",
}
_PRODUCTION_COLLECTION_NAMES = {
    "mergenvision_face_samples_v1",
}


def _is_external_endpoint(url: str | None) -> bool:
    if not url:
        return False
    if "://" not in url:
        url = "//" + url
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return host.lower() not in _SAFE_HOSTS


def _is_test_name(name: str) -> bool:
    return (
        name.startswith("test_")
        or name.startswith("test-")
        or name.endswith("_test")
        or name.endswith("-test")
    )


def validate(
    *,
    allow_destructive: bool = False,
    minio_endpoint: str | None = None,
    qdrant_url: str | None = None,
    person_photos_bucket: str | None = None,
    recognition_inputs_bucket: str | None = None,
    face_collection: str | None = None,
) -> list[str]:
    errors: list[str] = []
    any_external = _is_external_endpoint(minio_endpoint) or _is_external_endpoint(
        qdrant_url
    )

    if any_external and not allow_destructive:
        errors.append(
            "External MinIO/Qdrant endpoints are configured. "
            "Set MERGENVISION_ALLOW_DESTRUCTIVE_EXTERNAL_STORAGE_TESTS=YES to opt in."
        )

    for bucket in (person_photos_bucket, recognition_inputs_bucket):
        if not bucket:
            continue
        if not _is_test_name(bucket):
            errors.append(f"Bucket name '{bucket}' must start with 'test_' or end with '_test'.")
        if bucket in _PRODUCTION_BUCKET_NAMES and not allow_destructive:
            errors.append(f"Bucket name '{bucket}' is a production name.")

    if face_collection and not _is_test_name(face_collection):
        errors.append(
            f"Collection name '{face_collection}' must start with 'test_' or end with '_test'."
        )
    if face_collection in _PRODUCTION_COLLECTION_NAMES and not allow_destructive:
        errors.append(f"Collection name '{face_collection}' is a production name.")

    return errors


def main() -> int:
    allow_destructive = (
        os.environ.get("MERGENVISION_ALLOW_DESTRUCTIVE_EXTERNAL_STORAGE_TESTS") == "YES"
    )
    errors = validate(
        allow_destructive=allow_destructive,
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        qdrant_url=os.environ.get("QDRANT_URL"),
        person_photos_bucket=os.environ.get("MINIO_PERSON_PHOTOS_BUCKET"),
        recognition_inputs_bucket=os.environ.get("MINIO_RECOGNITION_INPUTS_BUCKET"),
        face_collection=os.environ.get("QDRANT_FACE_COLLECTION"),
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
