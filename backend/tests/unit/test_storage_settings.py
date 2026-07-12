import pytest
from pydantic import SecretStr, ValidationError

from mergenvision.config.storage import MinioSettings, QdrantSettings


def test_minio_settings_secret_redaction(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "secret")

    settings = MinioSettings()
    assert settings.endpoint == "localhost:9000"
    assert settings.access_key.get_secret_value() == "access"
    assert settings.secret_key.get_secret_value() == "secret"
    assert "secret" not in repr(settings)
    assert "access" not in repr(settings)
    assert "localhost:9000" in repr(settings)


def test_minio_settings_defaults():
    settings = MinioSettings(
        endpoint="localhost:9000",
        access_key=SecretStr("access"),
        secret_key=SecretStr("secret"),
    )
    assert settings.person_photos_bucket == "mergenvision-person-photos"
    assert settings.recognition_inputs_bucket == "mergenvision-recognition-inputs"
    assert settings.secure is False


def test_qdrant_settings_secret_redaction(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "api-key-123")

    settings = QdrantSettings()
    assert settings.url == "http://localhost:6333"
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "api-key-123"
    assert "api-key-123" not in repr(settings)
    assert "http://localhost:6333" in repr(settings)


def test_qdrant_settings_defaults():
    settings = QdrantSettings(url="http://localhost:6333")
    assert settings.face_collection == "mergenvision_face_samples_v1"
    assert settings.search_limit == 10
    assert settings.hnsw_ef == 128
    assert settings.upsert_batch_size == 512


def test_minio_max_concurrency_must_be_positive():
    with pytest.raises(ValidationError):
        MinioSettings(
            endpoint="localhost:9000",
            access_key=SecretStr("access"),
            secret_key=SecretStr("secret"),
            max_concurrency=0,
        )


def test_qdrant_positive_int_settings_rejected():
    with pytest.raises(ValidationError):
        QdrantSettings(url="http://localhost:6333", search_limit=0)
    with pytest.raises(ValidationError):
        QdrantSettings(url="http://localhost:6333", hnsw_ef=0)
    with pytest.raises(ValidationError):
        QdrantSettings(url="http://localhost:6333", upsert_batch_size=0)


def test_qdrant_timeout_must_be_positive():
    with pytest.raises(ValidationError):
        QdrantSettings(url="http://localhost:6333", timeout=0)


def test_endpoint_with_userinfo_is_rejected():
    with pytest.raises(ValidationError):
        MinioSettings(
            endpoint="http://user:pass@localhost:9000",
            access_key=SecretStr("access"),
            secret_key=SecretStr("secret"),
        )
    with pytest.raises(ValidationError):
        QdrantSettings(url="http://user:pass@localhost:6333")
