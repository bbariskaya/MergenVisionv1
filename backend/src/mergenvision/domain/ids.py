import secrets
import time
import uuid


def _uuid7_from_builtin() -> uuid.UUID | None:
    fn = getattr(uuid, "uuid7", None)
    if fn is None:
        return None
    return fn()


def _uuid7_rfc9562() -> uuid.UUID:
    timestamp_ms = int(time.time_ns() // 1_000_000)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    uuid_int = (
        (timestamp_ms << 80)
        | (0x7 << 76)
        | (rand_a << 64)
        | (0x2 << 62)
        | rand_b
    )
    value = uuid.UUID(int=uuid_int)
    if value.version != 7 or value.variant != uuid.RFC_4122:
        raise RuntimeError("UUIDv7 fallback produced an invalid UUID")
    return value


def new_uuid7() -> uuid.UUID:
    value = _uuid7_from_builtin()
    return value if value is not None else _uuid7_rfc9562()
