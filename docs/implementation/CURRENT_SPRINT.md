# MergenVision Phase 1 — Sprint 002

**Sprint name:** PostgreSQL + Alembic + national-ID security + repository layer

**Objective:**
Dondurulmuş sekiz tabloluk Phase 1 ERD’yi gerçek çalışan SQLAlchemy 2 modelleri, Alembic migration, national-ID security boundary, repository port/adapter katmanı ve gerçek PostgreSQL integration testleriyle implement etmek.

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

## Exact files

### Domain/ports
- `backend/src/mergenvision/domain/enums.py`
- `backend/src/mergenvision/domain/errors.py`
- `backend/src/mergenvision/domain/ids.py`
- `backend/src/mergenvision/domain/entities.py`
- `backend/src/mergenvision/ports/national_id.py`
- `backend/src/mergenvision/ports/repositories.py`

### Infrastructure
- `backend/src/mergenvision/infrastructure/security/national_id.py`
- `backend/src/mergenvision/infrastructure/database/base.py`
- `backend/src/mergenvision/infrastructure/database/models.py`
- `backend/src/mergenvision/infrastructure/database/mappers.py`
- `backend/src/mergenvision/infrastructure/database/session.py`
- `backend/src/mergenvision/infrastructure/database/repositories.py`

### Config/migrations
- `backend/src/mergenvision/config/settings.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/0001_phase1_schema.py`

### Tests
- `backend/tests/unit/test_uuid7.py`
- `backend/tests/unit/test_national_id_protection.py`
- `backend/tests/unit/test_domain_entities.py`
- `backend/tests/unit/test_database_metadata_contract.py`
- `backend/tests/integration/conftest.py`
- `backend/tests/integration/test_alembic_postgres.py`
- `backend/tests/integration/test_postgres_constraints.py`
- `backend/tests/integration/test_postgres_repositories.py`

### Build/scripts
- `scripts/run_postgres_integration_tests.sh`
- `scripts/bootstrap_foundation.sh`
- `Makefile`
- `backend/pyproject.toml`

### Docs
- `docs/implementation/REFERENCE_DECISION_LOG.md`
- `docs/implementation/IMPLEMENTATION_DETAILS.md`

---

## Exact deliverables

1. UUIDv7 generator (`domain/ids.py`) with version verification tests.
2. `NationalIdProtector` port + `AesGcmNationalIdProtector` adapter:
   - NFKC + trim normalization.
   - AES-256-GCM authenticated encryption with random nonce.
   - Secret-keyed HMAC-SHA256 lookup hash.
   - Masking (last four digits, full mask for ≤4 chars).
   - Fail-closed key validation.
   - No raw national ID in repr/log/error/DB.
3. Domain entities + status value constants for eight tables.
4. SQLAlchemy 2 typed declarative ORM models for eight frozen tables with all constraints/indexes/checks.
5. Alembic async migration (initial, upgrade/downgrade/re-upgrade safe).
6. Settings (`MERGENVISION_DATABASE_URL`, national ID key env vars).
7. Database session factory (`AsyncSession`, `expire_on_commit=False`).
8. Eight concrete PostgreSQL repositories implementing the port contract.
9. Repository transaction ownership: caller commits/rolls back; repository only flushes.
10. Conflict/constraint errors mapped to sanitized domain errors.
11. Real PostgreSQL integration test harness (Docker if no test URL is provided).

---

## Test-first plan

1. `test_uuid7.py` — fail due to missing `new_uuid7`, then implement.
2. `test_national_id_protection.py` — fail due to missing protector, then implement.
3. `test_domain_entities.py` — fail due to missing entities/constants, then implement.
4. `test_database_metadata_contract.py` — fail due to missing models, then implement.
5. Integration tests — fail due to missing migration/session/repositories, then implement.
6. After each green step run unit tests.
7. After all code complete run full integration harness.

---

## Real PostgreSQL validation plan

- `make test-db-unit` runs unit tests.
- `make test-db-integration` runs `scripts/run_postgres_integration_tests.sh`.
- If `MERGENVISION_TEST_DATABASE_URL` is set, use it.
- Otherwise start an ephemeral `postgres:16-alpine` container on a free localhost port.
- Run Alembic `upgrade head`, execute integration tests, then `downgrade base` + `upgrade head`.
- Container is stopped/trapped at the end; only the container started by this script is touched.
- No named volume; no `docker compose down`/`prune`/volume rm.

---

## Acceptance commands

```bash
cd /home/user/Workspace/MergenVisionFinalVersion
make bootstrap-foundation
make verify-foundation
make test-db-unit
make test-db-integration
make verify-db
make verify-sprint-002
.venv/bin/python -m ruff check backend/src backend/tests
.venv/bin/python -m mypy backend/src
bash scripts/verify_repository_boundaries.sh
sha256sum --check architecture/FROZEN_SHA256SUMS
```

---

## Non-goals

- FastAPI app/endpoint/router/schema.
- MinIO or Qdrant client/adapter.
- ML model download / RetinaFace / ArcFace / TensorRT / CUDA kernel.
- Native runtime server.
- Bulk enrollment worker.
- React/Vite UI.
- Docker Compose / Dockerfile.
- Oracle adapter.
- Phase 2 video/live-stream/tracker/object-detection.
- Authentication platform.
- Generic base repository framework.
- New business table or ERD change.
- Frozen architecture/requirements file change.
- Git add / commit / push.

---

## Hard stops

- Frozen ERD değişikliği yapma.
- Raw national ID’yi log/response/MinIO key/Qdrant payload’a yazma.
- SQLite veya mock DB ile PostgreSQL integration kanıtı yerine geçirme.
- Repository kendi başına commit yapma.
- PostgreSQL native ENUM ekleme.
- Geniş cascade delete koyma.
- Image binary / embedding’i PostgreSQL’e yazma.
- Yeni tablo ekleme.

---

## Definition of done

`SPRINT_002_DB_GATE=PASS` only if:

1. Eight SQLAlchemy model files exist for the frozen tables.
2. Initial Alembic migration creates eight business tables + `alembic_version`.
3. Upgrade/downgrade/re-upgrade pass on real PostgreSQL.
4. Required constraints/indexes/checks verified by PostgreSQL introspection.
5. UUIDv7 generator produces `uuid.version == 7`.
6. National ID AES-GCM + HMAC + masking boundary works and raw ID never appears in DB/log/error.
7. Eight repository port/implementation pairs exist.
8. Repositories do not commit themselves.
9. Unit tests pass.
10. Real PostgreSQL integration tests pass.
11. Foundation regression (`make verify-foundation`) passes.
12. Ruff passes.
13. Mypy passes or exact typed blocker is reported as `PARTIAL`.
14. Frozen hashes unchanged.
15. `AGENTS.md` unchanged.
16. `IMPLEMENTATION_DETAILS.md` updated.
17. No git operations performed.

If real PostgreSQL testing is skipped: `SPRINT_002_DB_GATE=PARTIAL`.
