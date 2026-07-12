from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from mergenvision.config.storage import QdrantSettings
from mergenvision.domain.errors import VectorContractError, VectorIndexError
from mergenvision.ports.vector_index import (
    FaceVectorPoint,
    VectorCandidate,
    VectorIndexPort,
    VectorPointState,
)

_PII_PAYLOAD_FIELDS = frozenset(
    {"firstName", "lastName", "nationalId", "nationalIdMasked", "originalFilename"}
)


class QdrantVectorIndexAdapter(VectorIndexPort):
    def __init__(self, settings: QdrantSettings) -> None:
        self._settings = settings
        self._client = AsyncQdrantClient(**settings.client_kwargs)
        self._collection_name = settings.face_collection
        self._index_fields = ("faceIdentityId", "personId", "inferenceProfileId", "active")

    async def close(self) -> None:
        await self._client.close()

    async def ensure_ready(self) -> None:
        collection = self._collection_name
        try:
            exists = await self._client.collection_exists(collection)
        except Exception as exc:
            raise VectorIndexError(
                "Failed to check Qdrant collection existence",
                retryable=True,
            ) from exc

        if not exists:
            try:
                await self._client.create_collection(
                    collection_name=collection,
                    vectors_config=models.VectorParams(
                        size=512,
                        distance=models.Distance.COSINE,
                    ),
                    hnsw_config=models.HnswConfigDiff(
                        m=16,
                        ef_construct=128,
                        full_scan_threshold=10000,
                    ),
                )
            except Exception as exc:
                raise VectorIndexError(
                    "Failed to create Qdrant collection",
                    retryable=True,
                ) from exc
        else:
            try:
                info = await self._client.get_collection(collection)
            except Exception as exc:
                raise VectorIndexError(
                    "Failed to read Qdrant collection info",
                    retryable=True,
                ) from exc
            vectors = info.config.params.vectors
            if not isinstance(vectors, models.VectorParams):
                raise VectorContractError(
                    "Qdrant collection uses named vectors; expected single default vector"
                )
            if vectors.size != 512:
                raise VectorContractError(
                    f"Qdrant collection vector size {vectors.size} != 512"
                )
            if vectors.distance != models.Distance.COSINE:
                raise VectorContractError(
                    f"Qdrant collection distance {vectors.distance} != COSINE"
                )

        for field_name in self._index_fields:
            if field_name == "active":
                schema = models.PayloadSchemaType.BOOL
            else:
                schema = models.PayloadSchemaType.KEYWORD
            try:
                await self._client.create_payload_index(
                    collection_name=collection,
                    field_name=field_name,
                    field_schema=schema,
                )
            except UnexpectedResponse as exc:
                if exc.status_code != 409:
                    raise VectorIndexError(
                        f"Failed to create payload index {field_name}",
                        retryable=True,
                    ) from None
            except VectorContractError:
                raise
            except Exception:
                raise VectorIndexError(
                    f"Failed to create payload index {field_name}",
                    retryable=True,
                ) from None

        try:
            info = await self._client.get_collection(collection)
        except Exception as exc:
            raise VectorIndexError(
                "Failed to read final collection info",
                retryable=True,
            ) from exc

        self._validate_payload_indexes(info)

    def _validate_payload_indexes(self, info: Any) -> None:
        schema = info.payload_schema or {}
        expected = {
            "faceIdentityId": models.PayloadSchemaType.KEYWORD,
            "personId": models.PayloadSchemaType.KEYWORD,
            "inferenceProfileId": models.PayloadSchemaType.KEYWORD,
            "active": models.PayloadSchemaType.BOOL,
        }
        for field, kind in expected.items():
            if field not in schema:
                raise VectorContractError(f"Missing payload index {field}")
            if schema[field].data_type != kind:
                raise VectorContractError(
                    f"Payload index {field} has type {schema[field].data_type}; expected {kind}"
                )
        if "sampleId" in schema:
            raise VectorContractError("Unexpected payload index sampleId")

    async def upsert_points(self, points: Sequence[FaceVectorPoint]) -> None:
        if not points:
            return
        collection = self._collection_name
        batch_size = max(1, self._settings.upsert_batch_size)

        qdrant_points = [self._to_point_struct(point) for point in points]

        for i in range(0, len(qdrant_points), batch_size):
            batch = qdrant_points[i : i + batch_size]
            try:
                await self._client.upsert(
                    collection_name=collection,
                    points=batch,
                    wait=True,
                )
            except VectorContractError:
                raise
            except Exception as exc:
                raise VectorIndexError(
                    "Failed to upsert points into Qdrant",
                    retryable=True,
                ) from exc

    def _to_point_struct(self, point: FaceVectorPoint) -> models.PointStruct:
        self._validate_embedding(point.embedding)
        payload = {
            "faceIdentityId": str(point.face_identity_id),
            "sampleId": str(point.sample_id),
            "personId": str(point.person_id),
            "inferenceProfileId": str(point.inference_profile_id),
            "active": point.active,
        }
        for forbidden in _PII_PAYLOAD_FIELDS:
            if forbidden in payload:
                raise VectorContractError(f"Forbidden PII field {forbidden!r} in payload")
        return models.PointStruct(
            id=str(point.sample_id),
            vector=list(point.embedding),
            payload=payload,
        )

    @staticmethod
    def _validate_embedding(embedding: Sequence[float]) -> None:
        if len(embedding) != 512:
            raise VectorContractError("Embedding must have exactly 512 dimensions")
        for value in embedding:
            if not math.isfinite(value):
                raise VectorContractError("Embedding contains NaN or infinite values")
        norm = math.sqrt(sum(value * value for value in embedding))
        if norm == 0:
            raise VectorContractError("Embedding is a zero vector")
        if abs(norm - 1.0) > 1e-3:
            raise VectorContractError("Embedding is not L2-normalized")

    async def get_points(
        self,
        sample_ids: Sequence[UUID],
        *,
        with_vectors: bool = False,
    ) -> list[VectorPointState]:
        if not sample_ids:
            return []
        collection = self._collection_name
        try:
            records = await self._client.retrieve(
                collection_name=collection,
                ids=[str(sample_id) for sample_id in sample_ids],
                with_payload=True,
                with_vectors=with_vectors,
            )
        except Exception as exc:
            raise VectorIndexError(
                "Failed to retrieve points from Qdrant",
                retryable=True,
            ) from exc

        return [self._record_to_state(record) for record in records]

    def _record_to_state(self, record: Any) -> VectorPointState:
        payload = record.payload or {}
        vector = record.vector if hasattr(record, "vector") else None
        return VectorPointState(
            sample_id=UUID(payload["sampleId"]),
            face_identity_id=UUID(payload["faceIdentityId"]),
            person_id=UUID(payload["personId"]),
            inference_profile_id=UUID(payload["inferenceProfileId"]),
            active=bool(payload["active"]),
            vector=vector,
            present=True,
        )

    async def search(
        self,
        embedding: Sequence[float],
        inference_profile_id: UUID,
        *,
        limit: int | None = None,
    ) -> list[VectorCandidate]:
        self._validate_embedding(embedding)
        collection = self._collection_name
        search_limit = limit if limit is not None else self._settings.search_limit
        try:
            response = await self._client.query_points(
                collection_name=collection,
                query=list(embedding),
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="active",
                            match=models.MatchValue(value=True),
                        ),
                        models.FieldCondition(
                            key="inferenceProfileId",
                            match=models.MatchValue(value=str(inference_profile_id)),
                        ),
                    ]
                ),
                search_params=models.SearchParams(
                    hnsw_ef=self._settings.hnsw_ef,
                    exact=False,
                ),
                limit=search_limit,
                with_payload=True,
            )
        except VectorContractError:
            raise
        except Exception as exc:
            raise VectorIndexError(
                "Failed to search Qdrant",
                retryable=True,
            ) from exc

        candidates: list[VectorCandidate] = []
        for point in response.points:
            payload = point.payload or {}
            candidates.append(
                VectorCandidate(
                    sample_id=UUID(payload["sampleId"]),
                    face_identity_id=UUID(payload["faceIdentityId"]),
                    person_id=UUID(payload["personId"]),
                    inference_profile_id=UUID(payload["inferenceProfileId"]),
                    score=float(point.score),
                    active=bool(payload.get("active", True)),
                )
            )
        return candidates

    async def set_active(self, sample_ids: Sequence[UUID], *, active: bool) -> None:
        if not sample_ids:
            return
        collection = self._collection_name
        try:
            await self._client.set_payload(
                collection_name=collection,
                payload={"active": active},
                points=[str(sample_id) for sample_id in sample_ids],
                wait=True,
            )
        except VectorContractError:
            raise
        except Exception as exc:
            raise VectorIndexError(
                f"Failed to set active={active} in Qdrant",
                retryable=True,
            ) from exc

    async def delete_points(self, sample_ids: Sequence[UUID]) -> None:
        if not sample_ids:
            return
        collection = self._collection_name
        try:
            await self._client.delete(
                collection_name=collection,
                points_selector=[str(sample_id) for sample_id in sample_ids],
                wait=True,
            )
        except VectorContractError:
            raise
        except Exception as exc:
            raise VectorIndexError(
                "Failed to delete points from Qdrant",
                retryable=True,
            ) from exc
