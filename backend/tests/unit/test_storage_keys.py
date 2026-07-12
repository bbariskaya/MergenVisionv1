from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from mergenvision.domain.storage_keys import (
    build_person_photo_key,
    build_recognition_input_key,
)

PERSON_ID = UUID("12345678-1234-5678-1234-567812345678")
PHOTO_ID = UUID("87654321-4321-8765-4321-876543218765")
PROCESS_ID = UUID("11111111-2222-3333-4444-555555555555")


def test_jpeg_person_photo_key():
    key = build_person_photo_key(PERSON_ID, PHOTO_ID, "image/jpeg")
    assert key == f"people/{PERSON_ID}/photos/{PHOTO_ID}/source.jpg"


def test_png_person_photo_key():
    key = build_person_photo_key(PERSON_ID, PHOTO_ID, "image/png")
    assert key == f"people/{PERSON_ID}/photos/{PHOTO_ID}/source.png"


def test_recognition_input_key_uses_utc_date():
    created = datetime(2026, 7, 12, 15, 30, tzinfo=UTC)
    key = build_recognition_input_key(PROCESS_ID, created, "image/jpeg")
    assert key == f"processes/2026/07/12/{PROCESS_ID}/input.jpg"


def test_recognition_input_key_converts_to_utc():
    created = datetime(2026, 7, 12, 22, 30, tzinfo=timezone(offset=timedelta(hours=3)))
    key = build_recognition_input_key(PROCESS_ID, created, "image/jpeg")
    assert key == f"processes/2026/07/12/{PROCESS_ID}/input.jpg"


def test_unsupported_mime_rejected():
    with pytest.raises(ValueError):
        build_person_photo_key(PERSON_ID, PHOTO_ID, "image/gif")


def test_no_pii_or_path_traversal_in_key():
    key = build_person_photo_key(PERSON_ID, PHOTO_ID, "image/jpeg")
    assert "../" not in key
    assert "national" not in key.lower()
    assert "name" not in key.lower()
    assert ".filename" not in key
