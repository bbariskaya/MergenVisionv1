from __future__ import annotations

import contextlib
import enum
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from mergenvision.domain.enums import PersonPhotoStatus, SampleStatus
from mergenvision.domain.errors import (
    ObjectStorageError,
    ReconciliationRequiredError,
    VectorIndexError,
)
from mergenvision.ports.object_storage import ObjectNamespace, ObjectStoragePort
from mergenvision.ports.vector_index import VectorIndexPort, VectorPointState


class ReconciliationOutcome(str, enum.Enum):
    HEALTHY = "healthy"
    REPAIRED = "repaired"
    PENDING_INDEX = "pending_index"
    NEEDS_REINDEX = "needs_reindex"
    NEEDS_REINFERENCE = "needs_reinference"
    MISSING_OBJECT = "missing_object"
    OBJECT_CONFLICT = "object_conflict"
    PAYLOAD_CONFLICT = "payload_conflict"
    DEACTIVATED = "deactivated"
    NOT_FOUND = "not_found"
    MANUAL_REVIEW = "manual_review"
    STORAGE_UNAVAILABLE = "storage_unavailable"


class ObjectStatus(str, enum.Enum):
    VALID = "valid"
    MISSING = "missing"
    SHA_MISMATCH = "sha_mismatch"
    UNAVAILABLE = "unavailable"


class PointStatus(str, enum.Enum):
    PRESENT = "present"
    MISSING = "missing"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ReconciliationResult:
    sample_id: UUID
    outcome: ReconciliationOutcome
    details: dict[str, Any]


@dataclass(frozen=True)
class _LifecycleSnapshot:
    sample_id: UUID
    sample_status: SampleStatus
    sample_deleted_at: datetime | None
    sample_face_identity_id: UUID
    sample_inference_profile_id: UUID
    sample_photo_id: UUID
    photo_status: PersonPhotoStatus
    photo_deleted_at: datetime | None
    photo_person_id: UUID
    photo_object_key: str
    photo_content_sha256: str

    @property
    def is_explicitly_deleted(self) -> bool:
        return (
            self.sample_status == SampleStatus.INACTIVE and self.sample_deleted_at is not None
        ) or (
            self.photo_status == PersonPhotoStatus.INACTIVE and self.photo_deleted_at is not None
        )


@dataclass(frozen=True)
class _ObjectCheck:
    status: ObjectStatus
    object_key: str
    object_sha256: str | None = None


@dataclass(frozen=True)
class _PointCheck:
    status: PointStatus
    point: VectorPointState | None = None


class StorageReconciliationService:
    def __init__(
        self,
        uow_factory: Callable[[], Any],
        object_storage: ObjectStoragePort,
        vector_index: VectorIndexPort,
        max_batch_size: int = 1000,
    ) -> None:
        self._uow_factory = uow_factory
        self._object_storage = object_storage
        self._vector_index = vector_index
        self._max_batch_size = max(1, max_batch_size)

    async def reconcile_sample(self, sample_id: UUID) -> ReconciliationResult:
        snapshot = await self._load_snapshot(sample_id)
        if snapshot is None:
            return await self._reconcile_orphan_qdrant_point(sample_id)
        if isinstance(snapshot, ReconciliationResult):
            return snapshot

        point_check = await self._check_qdrant(sample_id)

        if snapshot.is_explicitly_deleted:
            return await self._handle_explicitly_deleted(snapshot, point_check)

        object_check = await self._check_object(snapshot)

        if object_check.status == ObjectStatus.UNAVAILABLE:
            return self._result(
                sample_id,
                ReconciliationOutcome.STORAGE_UNAVAILABLE,
                {"reason": "minio_unavailable", "object_key": snapshot.photo_object_key},
            )
        if point_check.status == PointStatus.UNAVAILABLE:
            return self._result(
                sample_id,
                ReconciliationOutcome.STORAGE_UNAVAILABLE,
                {"reason": "qdrant_unavailable", "object_key": snapshot.photo_object_key},
            )

        if snapshot.sample_status == SampleStatus.ACTIVE:
            return await self._handle_active(snapshot, object_check, point_check)

        if (
            snapshot.sample_status == SampleStatus.INACTIVE
            and snapshot.sample_deleted_at is None
        ):
            return await self._handle_staged(snapshot, object_check, point_check)

        return self._result(
            sample_id,
            ReconciliationOutcome.MANUAL_REVIEW,
            {"reason": "unexpected_sample_state", "object_key": snapshot.photo_object_key},
        )

    async def reconcile_samples(
        self,
        sample_ids: Sequence[UUID],
    ) -> list[ReconciliationResult]:
        if len(sample_ids) == 0:
            return []
        if len(sample_ids) > self._max_batch_size:
            raise ReconciliationRequiredError(
                f"reconcile_samples batch size {len(sample_ids)} exceeds "
                f"limit {self._max_batch_size}"
            )
        results: list[ReconciliationResult] = []
        for sample_id in sample_ids:
            results.append(await self.reconcile_sample(sample_id))
        return results

    async def reconcile_photo(self, photo_id: UUID) -> list[ReconciliationResult]:
        async with self._uow_factory() as uow:
            photo = await uow.person_photo.get_by_id_any_status(photo_id)
            if photo is None:
                return []
            samples = await uow.face_sample.list_by_photo_id_any_status(
                photo_id,
                limit=self._max_batch_size,
                offset=0,
            )
            sample_ids = [sample.sample_id for sample in samples]
        return await self.reconcile_samples(sample_ids)

    async def _load_snapshot(
        self,
        sample_id: UUID,
    ) -> _LifecycleSnapshot | ReconciliationResult | None:
        async with self._uow_factory() as uow:
            sample = await uow.face_sample.get_by_id_any_status(sample_id)
            if sample is None:
                return None

            photo = await uow.person_photo.get_by_id_any_status(sample.photo_id)
            if photo is None:
                return self._result(
                    sample_id,
                    ReconciliationOutcome.MANUAL_REVIEW,
                    {"reason": "photo_not_found_for_sample"},
                )

            return _LifecycleSnapshot(
                sample_id=sample.sample_id,
                sample_status=sample.status,
                sample_deleted_at=sample.deleted_at,
                sample_face_identity_id=sample.face_identity_id,
                sample_inference_profile_id=sample.inference_profile_id,
                sample_photo_id=sample.photo_id,
                photo_status=photo.status,
                photo_deleted_at=photo.deleted_at,
                photo_person_id=photo.person_id,
                photo_object_key=photo.object_key,
                photo_content_sha256=photo.content_sha256,
            )

    async def _check_object(
        self,
        snapshot: _LifecycleSnapshot,
    ) -> _ObjectCheck:
        try:
            info = await self._object_storage.stat(
                ObjectNamespace.PERSON_PHOTOS,
                snapshot.photo_object_key,
            )
        except ObjectStorageError:
            return _ObjectCheck(
                status=ObjectStatus.UNAVAILABLE,
                object_key=snapshot.photo_object_key,
            )

        if info is None:
            return _ObjectCheck(
                status=ObjectStatus.MISSING,
                object_key=snapshot.photo_object_key,
            )

        if info.content_sha256 != snapshot.photo_content_sha256:
            return _ObjectCheck(
                status=ObjectStatus.SHA_MISMATCH,
                object_key=snapshot.photo_object_key,
                object_sha256=info.content_sha256,
            )

        return _ObjectCheck(
            status=ObjectStatus.VALID,
            object_key=snapshot.photo_object_key,
            object_sha256=info.content_sha256,
        )

    async def _check_qdrant(
        self,
        sample_id: UUID,
    ) -> _PointCheck:
        try:
            points = await self._vector_index.get_points(
                [sample_id], with_vectors=False
            )
        except VectorIndexError:
            return _PointCheck(status=PointStatus.UNAVAILABLE, point=None)

        point = points[0] if points else None
        if point is None:
            return _PointCheck(status=PointStatus.MISSING, point=None)
        return _PointCheck(status=PointStatus.PRESENT, point=point)

    async def _reconcile_orphan_qdrant_point(
        self,
        sample_id: UUID,
    ) -> ReconciliationResult:
        point_check = await self._check_qdrant(sample_id)
        if point_check.status == PointStatus.UNAVAILABLE:
            return self._result(
                sample_id,
                ReconciliationOutcome.STORAGE_UNAVAILABLE,
                {"reason": "qdrant_unavailable"},
            )
        if point_check.point is not None and point_check.point.active:
            deactivated = await self._deactivate_qdrant_if_active(
                sample_id, point_check.point.active
            )
            if not deactivated:
                return self._result(
                    sample_id,
                    ReconciliationOutcome.MANUAL_REVIEW,
                    {"reason": "failed_to_deactivate_orphan"},
                )
            return self._result(
                sample_id,
                ReconciliationOutcome.DEACTIVATED,
                {"reason": "orphan_qdrant_point_deactivated"},
            )
        return self._result(
            sample_id,
            ReconciliationOutcome.NOT_FOUND,
            {},
        )

    async def _handle_explicitly_deleted(
        self,
        snapshot: _LifecycleSnapshot,
        point_check: _PointCheck,
    ) -> ReconciliationResult:
        if point_check.point is not None and point_check.point.active:
            deactivated = await self._deactivate_qdrant_if_active(
                snapshot.sample_id, point_check.point.active
            )
            if not deactivated:
                return self._result(
                    snapshot.sample_id,
                    ReconciliationOutcome.MANUAL_REVIEW,
                    {
                        "reason": "deactivate_failed",
                        "object_key": snapshot.photo_object_key,
                    },
                )
        return self._result(
            snapshot.sample_id,
            ReconciliationOutcome.DEACTIVATED,
            {"reason": "explicitly_deleted"},
        )

    async def _handle_active(
        self,
        snapshot: _LifecycleSnapshot,
        object_check: _ObjectCheck,
        point_check: _PointCheck,
    ) -> ReconciliationResult:
        if object_check.status == ObjectStatus.MISSING:
            await self._deactivate_qdrant_if_active(
                snapshot.sample_id, bool(point_check.point and point_check.point.active)
            )
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.MISSING_OBJECT,
                {"object_key": snapshot.photo_object_key},
            )

        if object_check.status == ObjectStatus.SHA_MISMATCH:
            await self._deactivate_qdrant_if_active(
                snapshot.sample_id, bool(point_check.point and point_check.point.active)
            )
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.OBJECT_CONFLICT,
                {"object_key": snapshot.photo_object_key},
            )

        if point_check.status == PointStatus.MISSING:
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.NEEDS_REINDEX,
                {"object_key": snapshot.photo_object_key},
            )

        if point_check.point is None:
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.MANUAL_REVIEW,
                {"reason": "qdrant_state_unknown"},
            )

        if self._payload_mismatch(point_check.point, snapshot):
            await self._deactivate_qdrant_if_active(
                snapshot.sample_id, point_check.point.active
            )
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.PAYLOAD_CONFLICT,
                {"object_key": snapshot.photo_object_key},
            )

        if not point_check.point.active:
            try:
                await self._vector_index.set_active([snapshot.sample_id], active=True)
                return self._result(
                    snapshot.sample_id,
                    ReconciliationOutcome.REPAIRED,
                    {
                        "reason": "qdrant_active_flag_repaired",
                        "object_key": snapshot.photo_object_key,
                    },
                )
            except VectorIndexError:
                return self._result(
                    snapshot.sample_id,
                    ReconciliationOutcome.MANUAL_REVIEW,
                    {
                        "reason": "failed_to_repair_active_flag",
                        "object_key": snapshot.photo_object_key,
                    },
                )

        return self._result(
            snapshot.sample_id,
            ReconciliationOutcome.HEALTHY,
            {"object_key": snapshot.photo_object_key},
        )

    async def _handle_staged(
        self,
        snapshot: _LifecycleSnapshot,
        object_check: _ObjectCheck,
        point_check: _PointCheck,
    ) -> ReconciliationResult:
        if object_check.status == ObjectStatus.MISSING:
            await self._deactivate_qdrant_if_active(
                snapshot.sample_id, bool(point_check.point and point_check.point.active)
            )
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.MISSING_OBJECT,
                {"object_key": snapshot.photo_object_key},
            )

        if object_check.status == ObjectStatus.SHA_MISMATCH:
            await self._deactivate_qdrant_if_active(
                snapshot.sample_id, bool(point_check.point and point_check.point.active)
            )
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.OBJECT_CONFLICT,
                {"object_key": snapshot.photo_object_key},
            )

        if point_check.status == PointStatus.MISSING:
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.NEEDS_REINFERENCE,
                {
                    "reason": "qdrant_point_missing_for_staged_sample",
                    "object_key": snapshot.photo_object_key,
                },
            )

        if point_check.point is None:
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.MANUAL_REVIEW,
                {"reason": "qdrant_state_unknown"},
            )

        if self._payload_mismatch(point_check.point, snapshot):
            await self._deactivate_qdrant_if_active(
                snapshot.sample_id, point_check.point.active
            )
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.PAYLOAD_CONFLICT,
                {"object_key": snapshot.photo_object_key},
            )

        if not point_check.point.active:
            try:
                await self._vector_index.set_active([snapshot.sample_id], active=True)
            except VectorIndexError:
                return self._result(
                    snapshot.sample_id,
                    ReconciliationOutcome.MANUAL_REVIEW,
                    {
                        "reason": "failed_to_prepare_active_flag",
                        "object_key": snapshot.photo_object_key,
                    },
                )

        return await self._activate_staged_in_postgresql(
            snapshot, qdrant_active=True
        )

    async def _activate_staged_in_postgresql(
        self,
        snapshot: _LifecycleSnapshot,
        qdrant_active: bool,
    ) -> ReconciliationResult:
        manual_review_reason: str | None = None
        commit_error: Exception | None = None

        async with self._uow_factory() as uow:
            photo = await uow.person_photo.get_by_id_any_status(
                snapshot.sample_photo_id
            )
            sample = await uow.face_sample.get_by_id_any_status(snapshot.sample_id)

            if not self._snapshot_unchanged(snapshot, photo, sample):
                manual_review_reason = "lifecycle_drifted_during_repair"
            else:
                if (
                    photo is not None
                    and photo.status == PersonPhotoStatus.INACTIVE
                    and photo.deleted_at is None
                ):
                    await uow.person_photo.activate(snapshot.sample_photo_id)

                if (
                    sample is not None
                    and sample.status == SampleStatus.INACTIVE
                    and sample.deleted_at is None
                ):
                    await uow.face_sample.activate(snapshot.sample_id)

                try:
                    await uow.commit()
                except Exception as commit_exc:
                    commit_error = commit_exc
                else:
                    photo_after = await uow.person_photo.get_by_id_any_status(
                        snapshot.sample_photo_id
                    )
                    sample_after = await uow.face_sample.get_by_id_any_status(
                        snapshot.sample_id
                    )
                    if (
                        photo_after is None
                        or photo_after.status != PersonPhotoStatus.ACTIVE
                    ):
                        manual_review_reason = "photo_not_active_after_repair"
                    elif (
                        sample_after is None or sample_after.status != SampleStatus.ACTIVE
                    ):
                        manual_review_reason = "sample_not_active_after_repair"

        if manual_review_reason is not None:
            with contextlib.suppress(Exception):
                await self._vector_index.set_active([snapshot.sample_id], active=False)
            return self._result(
                snapshot.sample_id,
                ReconciliationOutcome.MANUAL_REVIEW,
                {"reason": manual_review_reason},
            )

        if commit_error is not None:
            with contextlib.suppress(Exception):
                await self._vector_index.set_active([snapshot.sample_id], active=False)
            raise ReconciliationRequiredError(
                "PostgreSQL activation failed during repair"
            ) from commit_error

        return self._result(
            snapshot.sample_id,
            ReconciliationOutcome.REPAIRED,
            {"reason": "staged_sample_activated", "object_key": snapshot.photo_object_key},
        )

    def _snapshot_unchanged(
        self,
        snapshot: _LifecycleSnapshot,
        photo: Any,
        sample: Any,
    ) -> bool:
        return (
            sample is not None
            and sample.status == snapshot.sample_status
            and sample.deleted_at == snapshot.sample_deleted_at
            and photo is not None
            and photo.status == snapshot.photo_status
            and photo.deleted_at == snapshot.photo_deleted_at
        )

    def _payload_mismatch(
        self,
        point: VectorPointState,
        snapshot: _LifecycleSnapshot,
    ) -> bool:
        return (
            point.face_identity_id != snapshot.sample_face_identity_id
            or point.person_id != snapshot.photo_person_id
            or point.inference_profile_id != snapshot.sample_inference_profile_id
        )

    async def _deactivate_qdrant_if_active(
        self,
        sample_id: UUID,
        currently_active: bool,
    ) -> bool:
        if not currently_active:
            return True
        try:
            await self._vector_index.set_active([sample_id], active=False)
            return True
        except VectorIndexError:
            return False

    def _result(
        self,
        sample_id: UUID,
        outcome: ReconciliationOutcome,
        details: dict[str, Any],
    ) -> ReconciliationResult:
        safe_details: dict[str, Any] = {}
        for key in ("reason", "error_code", "object_key"):
            if key in details:
                safe_details[key] = details[key]
        safe_details["sample_id"] = str(sample_id)
        return ReconciliationResult(
            sample_id=sample_id,
            outcome=outcome,
            details=safe_details,
        )
