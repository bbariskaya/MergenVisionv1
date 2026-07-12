from __future__ import annotations

import asyncio
import io
from typing import Any

from minio import Minio
from minio.error import S3Error

from mergenvision.config.storage import MinioSettings
from mergenvision.domain.errors import ObjectConflictError, ObjectStorageError
from mergenvision.ports.object_storage import (
    ObjectNamespace,
    ObjectStoragePort,
    PutObjectOutcome,
    StoredObjectInfo,
)

_ALLOWED_METADATA_KEYS = {
    ObjectNamespace.PERSON_PHOTOS: frozenset({"person-id", "photo-id", "schema-version"}),
    ObjectNamespace.RECOGNITION_INPUTS: frozenset({"process-id", "schema-version"}),
}

_PII_METADATA_KEYS = frozenset(
    {"national-id", "first-name", "last-name", "original-filename", "national-id-masked"}
)


class MinioObjectStorageAdapter(ObjectStoragePort):
    def __init__(self, settings: MinioSettings) -> None:
        if not settings.access_key.get_secret_value():
            raise ObjectStorageError("MinIO access key is empty")
        if not settings.secret_key.get_secret_value():
            raise ObjectStorageError("MinIO secret key is empty")
        self._settings = settings
        self._client = Minio(**settings.client_kwargs)
        self._semaphore = asyncio.Semaphore(max(1, settings.max_concurrency))

    def _validate_metadata(
        self,
        namespace: ObjectNamespace,
        metadata: dict[str, str],
    ) -> None:
        allowed = _ALLOWED_METADATA_KEYS.get(namespace)
        if allowed is None:
            raise ObjectStorageError(f"Unknown namespace: {namespace}")

        for key in metadata:
            normalized = key.lower()
            if normalized in _PII_METADATA_KEYS:
                raise ObjectStorageError(
                    f"Metadata key {key!r} is not allowed: contains PII"
                )
            if normalized not in allowed:
                raise ObjectStorageError(
                    f"Metadata key {key!r} is not allowed for namespace {namespace.value}"
                )

    def _bucket_for(self, namespace: ObjectNamespace) -> str:
        if namespace == ObjectNamespace.PERSON_PHOTOS:
            return self._settings.person_photos_bucket
        if namespace == ObjectNamespace.RECOGNITION_INPUTS:
            return self._settings.recognition_inputs_bucket
        raise ObjectStorageError(f"Unknown namespace: {namespace}")

    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        async with self._semaphore:
            return await asyncio.to_thread(fn, *args, **kwargs)

    async def ensure_ready(self) -> None:
        for namespace in (ObjectNamespace.PERSON_PHOTOS, ObjectNamespace.RECOGNITION_INPUTS):
            bucket = self._bucket_for(namespace)
            try:
                exists = await self._run(self._client.bucket_exists, bucket)
                if not exists:
                    await self._run(self._client.make_bucket, bucket)
            except S3Error as exc:
                if exc.code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                    raise ObjectStorageError("Failed to prepare bucket") from exc
            except Exception:
                raise ObjectStorageError("Failed to prepare bucket") from None

    async def put_if_absent_or_same(
        self,
        namespace: ObjectNamespace,
        object_key: str,
        data: bytes,
        *,
        content_sha256: str,
        content_type: str,
        metadata: dict[str, str],
    ) -> PutObjectOutcome:
        bucket = self._bucket_for(namespace)
        self._validate_metadata(namespace, metadata)

        existing = await self.stat(namespace, object_key)
        if existing is not None:
            if existing.content_sha256 == content_sha256 and existing.size_bytes == len(data):
                return PutObjectOutcome(
                    info=existing,
                    created=False,
                    idempotent_reuse=True,
                )
            raise ObjectConflictError(
                f"Object {object_key} exists with different content"
            )

        full_metadata = dict(metadata)
        full_metadata["content-sha256"] = content_sha256
        data_stream = io.BytesIO(data)
        try:
            result = await self._run(
                self._client.put_object,
                bucket,
                object_key,
                data_stream,
                length=len(data),
                content_type=content_type,
                metadata=full_metadata,
            )
        except S3Error as exc:
            raise ObjectStorageError(f"Failed to upload object: {exc.code}") from exc
        except Exception:
            raise ObjectStorageError("Failed to upload object") from None

        info = StoredObjectInfo(
            namespace=namespace,
            object_key=object_key,
            size_bytes=len(data),
            content_type=content_type,
            etag=result.etag or "",
            content_sha256=content_sha256,
            metadata=dict(full_metadata),
        )
        return PutObjectOutcome(info=info, created=True, idempotent_reuse=False)

    async def stat(self, namespace: ObjectNamespace, object_key: str) -> StoredObjectInfo | None:
        bucket = self._bucket_for(namespace)
        try:
            result = await self._run(self._client.stat_object, bucket, object_key)
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                return None
            raise ObjectStorageError(f"Failed to stat object: {exc.code}") from exc
        except Exception:
            raise ObjectStorageError("Failed to stat object") from None

        metadata_lower: dict[str, str] = {}
        for key, value in (result.metadata or {}).items():
            normalized = str(key).lower()
            if normalized.startswith("x-amz-meta-"):
                normalized = normalized[len("x-amz-meta-"):]
            metadata_lower[normalized] = str(value)
        content_sha256 = metadata_lower.get("content-sha256", "")
        return StoredObjectInfo(
            namespace=namespace,
            object_key=object_key,
            size_bytes=result.size,
            content_type=result.content_type or "application/octet-stream",
            etag=result.etag or "",
            content_sha256=content_sha256,
            metadata=metadata_lower,
        )

    async def get_bytes(self, namespace: ObjectNamespace, object_key: str) -> bytes:
        bucket = self._bucket_for(namespace)
        response = None
        try:
            response = await self._run(self._client.get_object, bucket, object_key)
            data = await self._run(response.read)
            return data
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                raise ObjectStorageError("Object not found") from exc
            raise ObjectStorageError(f"Failed to get object: {exc.code}") from exc
        except Exception:
            raise ObjectStorageError("Failed to get object") from None
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    async def delete_if_matches(
        self,
        namespace: ObjectNamespace,
        object_key: str,
        *,
        content_sha256: str,
    ) -> None:
        bucket = self._bucket_for(namespace)
        existing = await self.stat(namespace, object_key)
        if existing is None:
            return
        if existing.content_sha256 != content_sha256:
            raise ObjectConflictError(
                f"Object {object_key} content does not match expected SHA"
            )
        try:
            await self._run(self._client.remove_object, bucket, object_key)
        except S3Error as exc:
            raise ObjectStorageError(f"Failed to delete object: {exc.code}") from exc
        except Exception:
            raise ObjectStorageError("Failed to delete object") from None
