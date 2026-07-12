# MergenVision Phase 1 — Sprint 003

**Sprint name:** MinIO + Qdrant Adapters + Cross-Store Lifecycle/Reconciliation

**Objective:**
Frozen Phase 1 storage kararlarına göre MinIO object storage adapter’ı, Qdrant vector index adapter’ı, cross-store idempotent enrollment persistence servisi ve targeted reconciliation servisini implement etmek. Bu sprint tam enrollment API’si veya ML inference sprinti değildir; servis zaten doğrulanmış fotoğraf binary’si ve normalize edilmiş 512-D embedding kabul eder.

**Active repository:** `/home/user/Workspace/MergenVisionFinalVersion`

**Frozen inputs (read-only):**
- `requirements/phase1requirements.md`
- `requirements/ProjectRequirements.md`
- `architecture/01-phase1-high-level-architecture.md`
- `architecture/02-phase1-component-diagram.md`
- `architecture/03-phase1-postgresql-erd.md`
- `architecture/04-phase1-minio-object-layout.md`
- `architecture/05-phase1-qdrant-vector-design.md`
- `architecture/06-phase1-api-contract.md`
- `opensourcereferences/references.md`
- `whatwentwrong.md`

---

## Exact deliverables

### Ports
- `backend/src/mergenvision/ports/object_storage.py`
- `backend/src/mergenvision/ports/vector_index.py`
- `backend/src/mergenvision/ports/unit_of_work.py`

### Application services
- `backend/src/mergenvision/application/enrollment_persistence.py`
- `backend/src/mergenvision/application/storage_reconciliation.py`

### Infrastructure adapters
- `backend/src/mergenvision/infrastructure/object_storage/__init__.py`
- `backend/src/mergenvision/infrastructure/object_storage/minio_adapter.py`
- `backend/src/mergenvision/infrastructure/vector_index/__init__.py`
- `backend/src/mergenvision/infrastructure/vector_index/qdrant_adapter.py`
- `backend/src/mergenvision/infrastructure/database/unit_of_work.py`

### Config/helpers
- `backend/src/mergenvision/config/storage.py`
- `backend/src/mergenvision/domain/storage_keys.py`

### Repository extensions
- Targeted any-status read metotları:
  - `PersonPhotoRepository.get_by_id_any_status`
  - `PersonPhotoRepository.get_by_person_id_and_sha256`
  - `PersonPhotoRepository.get_by_object_key`
  - `FaceSampleRepository.get_by_id_any_status`
  - `FaceSampleRepository.get_by_photo_id_and_profile_id`

### Tests
- `backend/tests/unit/test_storage_keys.py`
- `backend/tests/unit/test_object_storage_contract.py`
- `backend/tests/unit/test_vector_index_contract.py`
- `backend/tests/unit/test_enrollment_persistence.py`
- `backend/tests/unit/test_storage_reconciliation.py`
- `backend/tests/unit/test_storage_settings.py`
- `backend/tests/unit/test_external_storage_test_safety.py`
- `backend/tests/integration/test_minio_adapter.py`
- `backend/tests/integration/test_qdrant_adapter.py`
- `backend/tests/integration/test_cross_store_persistence.py`
- `backend/tests/integration/test_cross_store_reconciliation.py`

### Test harness/build
- `scripts/check_external_storage_test_safety.py`
- `scripts/run_storage_integration_tests.sh`
- `Makefile` (storage target’ları)
- `backend/pyproject.toml` (MinIO + Qdrant bağımlılıkları)

### Docs
- `docs/implementation/REFERENCE_DECISION_LOG.md`
- `docs/implementation/IMPLEMENTATION_DETAILS.md`

---

## Exact deliverables (details)

1. PII-free deterministic object key helper (person photo + recognition input).
2. Object storage port + `MinioObjectStorageAdapter`:
   - idempotent bucket creation,
   - `put_if_absent_or_same`, `stat`, `get_bytes`, `delete_if_matches`,
   - sync SDK’nın bounded async offload ile sarılması,
   - metadata allowlist, content conflict detection.
3. Vector index port + `QdrantVectorIndexAdapter`:
   - collection creation with frozen 512-D cosine contract + HNSW baseline,
   - payload index creation,
   - vector validation (512-D, finite, nonzero, L2-normalized),
   - bounded batch upsert with `wait=true`,
   - filtered search (`active=true`, `inferenceProfileId`),
   - `set_active` and explicit `delete_points`.
4. PostgreSQL `UnitOfWork` port + `PostgresUnitOfWork` adapter.
5. Repository any-status extension methods for cross-store idempotency and reconciliation.
6. `EnrollmentPersistenceService` cross-store workflow:
   - canonical identity resolution,
   - MinIO object persistence,
   - PostgreSQL inactive staging,
   - Qdrant upsert,
   - PostgreSQL final activation,
   - MinIO compensation on staging failure,
   - Qdrant compensation on activation failure,
   - idempotent retry.
7. `StorageReconciliationService` targeted reconciliation of a bounded sample/photo list.
8. Sanitized error hierarchy for storage and cross-store errors.
9. Storage config classes (`MinioSettings`, `QdrantSettings`) with secret redaction.
10. Real ephemeral container harness for PostgreSQL + MinIO + Qdrant integration tests.

---

## Test-first plan

1. `test_storage_keys.py` — write keys before helper exists, then implement.
2. `test_object_storage_contract.py` — fake MinIO adapter seam; fail then implement port + fake.
3. `test_storage_settings.py` — fail then implement `MinioSettings`/`QdrantSettings`.
4. `test_vector_index_contract.py` — fail then implement port + adapter contract.
5. `test_enrollment_persistence.py` — inject fake object storage/vector index/UoW; fail then implement.
6. `test_storage_reconciliation.py` — fake repositories/storage/vector index; fail then implement.
7. `test_external_storage_test_safety.py` — fail then implement safety script.
8. `test_minio_adapter.py` — real MinIO container.
9. `test_qdrant_adapter.py` — real Qdrant container.
10. `test_cross_store_persistence.py` / `test_cross_store_reconciliation.py` — real three-store harness.

---

## Real service validation plan

- `make test-storage-unit` storage unit tests.
- `make test-storage-integration` runs `scripts/run_storage_integration_tests.sh`.
- Script starts ephemeral PostgreSQL (`postgres:16-alpine`), MinIO, Qdrant on random free ports, runs Alembic upgrade, runs storage integration tests, stops only its own containers.
- Bucket/collection names use `test_` prefix or `_test` suffix.
- External endpoint opt-in via env vars; destructive tests require explicit guard.

---

## Acceptance commands

```bash
cd /home/user/Workspace/MergenVisionFinalVersion
make bootstrap-foundation
make verify-foundation
make verify-sprint-002
make test-storage-unit
make test-storage-integration
make verify-storage
make verify-sprint-003
.venv/bin/python -m ruff check backend/src backend/tests
.venv/bin/python -m mypy backend/src
bash scripts/verify_repository_boundaries.sh
sha256sum --check architecture/FROZEN_SHA256SUMS
git diff --check
git status --short
git diff --stat
git diff --name-only
```

---

## Non-goals

- FastAPI route/endpoint/schema.
- React/Vite UI.
- Face detection / RetinaFace / SCRFD / ArcFace / TensorRT / CUDA.
- Model download veya engine build.
- Dataset import.
- Üç GPU worker / bulk enrollment runner.
- Oracle adapter / video / RTSP / GStreamer / DeepStream.
- Redis / Celery / Kafka / distributed saga framework / outbox tablosu.
- Kubernetes / production Docker Compose.
- Authentication / presigned URL endpoint.
- Recognition business decision service.
- New DB table/column/status/migration.
- Frozen architecture/requirements file change.
- Git add / commit / push.

---

## Hard stops

- Frozen ERD/schema/migration değişmez.
- MinIO/Qdrant SDK import’u application/domain katmanına sızmaz.
- Raw national ID, ad, soyad, original filename MinIO key/metadata veya Qdrant payload’a yazılmaz.
- Embedding ve image binary PostgreSQL’e yazılmaz.
- Collection recreate/delete on mismatch yapılmaz.
- Filtersiz/broad vector delete yapılmaz.
- Explicitly deactivated (`deleted_at IS NOT NULL`) sample/fotoğraf otomatik activate edilmez.
- PostgreSQL transaction açıkken uzun MinIO/Qdrant çağrısı yapılmaz.
- Secret/credential log/error/repr’da görünmez.
- Mock-only test real integration PASS iddiası olarak sunulmaz.

---

## Definition of done

`SPRINT_003_STORAGE_GATE=PASS` only if:

1. Object storage port + fake + real MinIO adapter geçer.
2. Vector index port + real Qdrant adapter geçer.
3. PostgreSQL + MinIO + Qdrant happy path cross-store integration geçer.
4. Same-command retry duplicate photo/sample/Qdrant point üretmez.
5. Qdrant mismatch collection’ı silmez/recreate etmez.
6. MinIO content conflict sessiz overwrite etmez.
7. Qdrant payload’ta ve MinIO metadata/key’de PII yoktur.
8. Qdrant `active`/`inferenceProfileId` filtreleri gerçek search ile doğrulanır.
9. Cross-store failure/compensation matrisi test edilir.
10. Staged (`inactive`, `deleted_at IS NULL`) ile explicitly deleted (`deleted_at IS NOT NULL`) ayrımı doğrulanır.
11. Reconciliation explicitly deleted kaydı yeniden activate etmez.
12. Storage unit tests, integration tests, ruff, mypy, boundary, foundation ve Sprint 002 regression geçer.
13. Frozen hashes unchanged.
14. `AGENTS.md` unchanged.
15. `IMPLEMENTATION_DETAILS.md` updated.
16. No git operations performed.

If real MinIO/Qdrant container testing cannot be run: `SPRINT_003_STORAGE_GATE=PARTIAL`.
