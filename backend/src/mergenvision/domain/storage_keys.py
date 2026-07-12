from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

_ALLOWED_MIME_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
}


def _normalize_mime_type(mime_type: str) -> str:
    normalized = mime_type.strip().lower()
    if normalized not in _ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported MIME type: {mime_type!r}")
    return normalized


def _extension_for(mime_type: str) -> str:
    return _ALLOWED_MIME_TYPES[_normalize_mime_type(mime_type)]


def build_person_photo_key(person_id: UUID, photo_id: UUID, mime_type: str) -> str:
    extension = _extension_for(mime_type)
    return f"people/{person_id}/photos/{photo_id}/source.{extension}"


def build_recognition_input_key(
    process_id: UUID,
    created_at_utc: datetime,
    mime_type: str,
) -> str:
    extension = _extension_for(mime_type)
    date_part = created_at_utc.astimezone(UTC).strftime("%Y/%m/%d")
    return f"processes/{date_part}/{process_id}/input.{extension}"
