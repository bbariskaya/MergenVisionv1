from __future__ import annotations

import base64
import hmac
import os
import struct
import unicodedata
from hashlib import sha256

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from mergenvision.domain.errors import SecurityError
from mergenvision.ports.national_id import NationalIdProtectedValue, NationalIdProtector

_FORMAT_VERSION = 1
_NONCE_LEN = 12
_AEAD_ASSOCIATED_DATA = b"mergenvision:national-id:v1"
_KEY_LEN = 32


class AesGcmNationalIdProtector(NationalIdProtector):
    def __init__(self, encryption_key_b64: str, hmac_key_b64: str) -> None:
        self._encryption_key = self._decode_key(encryption_key_b64, "encryption_key")
        self._hmac_key = self._decode_key(hmac_key_b64, "hmac_key")
        if self._encryption_key == self._hmac_key:
            raise SecurityError("Encryption key and HMAC key must be distinct")
        self._aesgcm = AESGCM(self._encryption_key)

    def protect(self, raw_national_id: str) -> NationalIdProtectedValue:
        normalized = self._normalize(raw_national_id)
        if not normalized:
            raise SecurityError("National ID is empty after normalization")
        nonce = os.urandom(_NONCE_LEN)
        plaintext = normalized.encode("utf-8")
        ciphertext_with_tag = self._aesgcm.encrypt(nonce, plaintext, _AEAD_ASSOCIATED_DATA)
        payload = struct.pack("!B", _FORMAT_VERSION) + nonce + ciphertext_with_tag
        return NationalIdProtectedValue(
            ciphertext=payload,
            lookup_hash=self._lookup_hash(normalized),
            masked=self._mask(normalized),
        )

    def reveal(self, protected: NationalIdProtectedValue) -> str:
        payload = protected.ciphertext
        if len(payload) < 1 + _NONCE_LEN + 16:
            raise SecurityError("Ciphertext is too short")
        version = payload[0]
        if version != _FORMAT_VERSION:
            raise SecurityError(f"Unsupported ciphertext format version: {version}")
        nonce = payload[1 : 1 + _NONCE_LEN]
        ciphertext_with_tag = payload[1 + _NONCE_LEN :]
        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext_with_tag, _AEAD_ASSOCIATED_DATA)
        except InvalidTag as exc:
            raise SecurityError("National ID decryption failed: authentication tag mismatch") from exc
        return plaintext.decode("utf-8")

    @staticmethod
    def _normalize(raw: str) -> str:
        return unicodedata.normalize("NFKC", raw).strip()

    @staticmethod
    def _mask(normalized: str) -> str:
        if len(normalized) > 4:
            return "*" * (len(normalized) - 4) + normalized[-4:]
        return "*" * len(normalized)

    def _lookup_hash(self, normalized: str) -> str:
        return hmac.new(
            self._hmac_key,
            normalized.encode("utf-8"),
            sha256,
        ).hexdigest()

    @staticmethod
    def _decode_key(key_b64: str, name: str) -> bytes:
        try:
            raw = base64.b64decode(key_b64, validate=True)
        except Exception as exc:
            raise SecurityError(f"Invalid Base64 for {name}") from exc
        if len(raw) != _KEY_LEN:
            raise SecurityError(
                f"{name} must decode to exactly {_KEY_LEN} bytes, got {len(raw)}"
            )
        return raw
