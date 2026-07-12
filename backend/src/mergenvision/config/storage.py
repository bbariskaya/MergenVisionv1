from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _assert_no_url_userinfo(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"//{url}")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL must not contain credentials")
    return url


class MinioSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MINIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    endpoint: str
    access_key: SecretStr
    secret_key: SecretStr
    secure: bool = False
    person_photos_bucket: str = "mergenvision-person-photos"
    recognition_inputs_bucket: str = "mergenvision-recognition-inputs"
    max_concurrency: int = 16

    @field_validator("endpoint")
    @classmethod
    def _endpoint_no_credentials(cls, value: str) -> str:
        return _assert_no_url_userinfo(value)

    @field_validator("max_concurrency")
    @classmethod
    def _max_concurrency_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_concurrency must be >= 1")
        return value

    @property
    def client_kwargs(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "access_key": self.access_key.get_secret_value(),
            "secret_key": self.secret_key.get_secret_value(),
            "secure": self.secure,
        }

    def __repr__(self) -> str:
        return (
            f"MinioSettings(endpoint={self.endpoint!r}, "
            f"person_photos_bucket={self.person_photos_bucket!r}, "
            f"recognition_inputs_bucket={self.recognition_inputs_bucket!r})"
        )


class QdrantSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="QDRANT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url: str
    api_key: SecretStr | None = None
    face_collection: str = "mergenvision_face_samples_v1"
    search_limit: int = 10
    hnsw_ef: int = 128
    upsert_batch_size: int = 512
    timeout: int | None = None

    @field_validator("url")
    @classmethod
    def _url_no_credentials(cls, value: str) -> str:
        return _assert_no_url_userinfo(value)

    @field_validator("search_limit", "hnsw_ef", "upsert_batch_size")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("value must be >= 1")
        return value

    @field_validator("timeout")
    @classmethod
    def _timeout_positive(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("timeout must be >= 1")
        return value

    @property
    def client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"url": self.url}
        if self.api_key is not None:
            kwargs["api_key"] = self.api_key.get_secret_value()
        if self.timeout is not None:
            kwargs["timeout"] = self.timeout
        return kwargs

    def __repr__(self) -> str:
        return (
            f"QdrantSettings(url={self.url!r}, "
            f"face_collection={self.face_collection!r})"
        )
