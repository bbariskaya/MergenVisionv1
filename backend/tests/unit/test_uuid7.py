from uuid import RFC_4122, UUID

import pytest

from mergenvision.domain.ids import new_uuid7


def test_new_uuid7_returns_version7():
    value = new_uuid7()
    assert isinstance(value, UUID)
    assert value.version == 7
    assert value.variant == RFC_4122


def test_new_uuid7_generates_unique_values():
    values = {new_uuid7() for _ in range(1000)}
    assert len(values) == 1000


def test_new_uuid7_timestamp_field_is_non_decreasing():
    ids = [new_uuid7() for _ in range(50)]
    timestamps = [value.int >> 80 for value in ids]
    for previous, current in zip(timestamps, timestamps[1:], strict=False):
        assert current >= previous
    for value in ids:
        assert value.version == 7
        assert value.variant == RFC_4122


def test_new_uuid7_fallback_path_produces_version7(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delattr("uuid.uuid7", raising=True)
    value = new_uuid7()
    assert isinstance(value, UUID)
    assert value.version == 7
    assert value.variant == RFC_4122


def test_new_uuid7_fallback_with_frozen_time_produces_unique_valid_uuids(
    monkeypatch: pytest.MonkeyPatch,
):
    fixed_ns = 1_725_000_000_000_000_000
    expected_ms = fixed_ns // 1_000_000

    monkeypatch.delattr("uuid.uuid7", raising=True)
    monkeypatch.setattr("time.time_ns", lambda: fixed_ns)

    values = [new_uuid7() for _ in range(1000)]
    assert len(set(values)) == 1000

    for value in values:
        assert value.version == 7
        assert value.variant == RFC_4122
        assert value.int >> 80 == expected_ms
