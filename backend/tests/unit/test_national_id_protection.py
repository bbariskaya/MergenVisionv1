import base64
import os

import pytest

from mergenvision.domain.errors import SecurityError
from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector
from mergenvision.ports.national_id import NationalIdProtectedValue


def _key_b64() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


@pytest.fixture
def protector() -> AesGcmNationalIdProtector:
    return AesGcmNationalIdProtector(
        encryption_key_b64=_key_b64(),
        hmac_key_b64=_key_b64(),
    )


def test_encrypt_then_decrypt_round_trip(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    protected = protector.protect(raw)
    assert protector.reveal(protected) == raw


def test_repeated_encryption_produces_different_ciphertexts(
    protector: AesGcmNationalIdProtector,
) -> None:
    raw = "12345678901"
    first = protector.protect(raw)
    second = protector.protect(raw)
    assert first.ciphertext != second.ciphertext
    assert first.lookup_hash == second.lookup_hash


def test_hmac_is_deterministic_for_same_key(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    a = protector.protect(raw)
    b = protector.protect(raw)
    assert a.lookup_hash == b.lookup_hash


def test_different_hmac_key_produces_different_hash() -> None:
    raw = "12345678901"
    encryption_key = _key_b64()
    hmac_key_a = _key_b64()
    hmac_key_b = _key_b64()
    p1 = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key,
        hmac_key_b64=hmac_key_a,
    )
    p2 = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key,
        hmac_key_b64=hmac_key_b,
    )
    assert p1.protect(raw).lookup_hash != p2.protect(raw).lookup_hash


def test_masking_reveals_last_four_digits(protector: AesGcmNationalIdProtector) -> None:
    protected = protector.protect("12345678901")
    assert protected.masked == "*******8901"


def test_masking_short_value_is_fully_masked(protector: AesGcmNationalIdProtector) -> None:
    protected = protector.protect("1234")
    assert protected.masked == "****"


def test_normalization_trims_and_nfkc(protector: AesGcmNationalIdProtector) -> None:
    raw = "\u00A0  123456789  \u00A0"
    protected = protector.protect(raw)
    assert protector.reveal(protected) == "123456789"


def test_protected_repr_does_not_contain_raw_id(protector: AesGcmNationalIdProtector) -> None:
    raw = "12345678901"
    protected = protector.protect(raw)
    representation = repr(protected)
    assert raw not in representation
    assert "lookup_hash" in representation or "protected" in representation


def test_invalid_encryption_key_size_fails_closed() -> None:
    with pytest.raises(SecurityError):
        AesGcmNationalIdProtector(
            encryption_key_b64=base64.b64encode(os.urandom(16)).decode("ascii"),
            hmac_key_b64=_key_b64(),
        )


def test_invalid_hmac_key_size_fails_closed() -> None:
    with pytest.raises(SecurityError):
        AesGcmNationalIdProtector(
            encryption_key_b64=_key_b64(),
            hmac_key_b64=base64.b64encode(os.urandom(16)).decode("ascii"),
        )


def test_tampered_ciphertext_raises_security_error(
    protector: AesGcmNationalIdProtector,
) -> None:
    protected = protector.protect("12345678901")
    tampered = NationalIdProtectedValue(
        ciphertext=protected.ciphertext[:-1] + bytes([protected.ciphertext[-1] ^ 1]),
        lookup_hash=protected.lookup_hash,
        masked=protected.masked,
    )
    with pytest.raises(SecurityError):
        protector.reveal(tampered)


def test_wrong_encryption_key_raises_security_error() -> None:
    raw = "12345678901"
    encryption_key_a = _key_b64()
    encryption_key_b = _key_b64()
    hmac_key = _key_b64()
    p1 = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key_a,
        hmac_key_b64=hmac_key,
    )
    p2 = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key_b,
        hmac_key_b64=hmac_key,
    )
    protected = p1.protect(raw)
    with pytest.raises(SecurityError):
        p2.reveal(protected)


def test_same_encryption_and_hmac_key_rejected() -> None:
    key_b64 = _key_b64()
    with pytest.raises(SecurityError):
        AesGcmNationalIdProtector(
            encryption_key_b64=key_b64,
            hmac_key_b64=key_b64,
        )


def test_adapter_has_no_public_key_export_methods() -> None:
    protector = AesGcmNationalIdProtector(
        encryption_key_b64=_key_b64(),
        hmac_key_b64=_key_b64(),
    )
    assert not hasattr(protector, "encryption_key_b64")
    assert not hasattr(protector, "hmac_key_b64")


def test_protection_does_not_leak_raw_id_or_keys_in_errors_and_repr(
    caplog: pytest.LogCaptureFixture,
) -> None:
    raw = "12345678901"
    encryption_key_b64 = _key_b64()
    hmac_key_b64 = _key_b64()
    protector = AesGcmNationalIdProtector(
        encryption_key_b64=encryption_key_b64,
        hmac_key_b64=hmac_key_b64,
    )

    protected = protector.protect(raw)
    protected_repr = repr(protected)
    assert raw not in protected_repr
    assert encryption_key_b64 not in protected_repr
    assert hmac_key_b64 not in protected_repr

    tampered = NationalIdProtectedValue(
        ciphertext=protected.ciphertext[:-1] + bytes([protected.ciphertext[-1] ^ 1]),
        lookup_hash=protected.lookup_hash,
        masked=protected.masked,
    )
    with pytest.raises(SecurityError) as exc_info:
        protector.reveal(tampered)
    error_text = str(exc_info.value)
    assert raw not in error_text
    assert encryption_key_b64 not in error_text
    assert hmac_key_b64 not in error_text

    for record in caplog.records:
        message = record.getMessage()
        assert raw not in message
        assert encryption_key_b64 not in message
        assert hmac_key_b64 not in message
