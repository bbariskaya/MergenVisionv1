# MergenVision Phase 1 — Foundation Sprint 0–1

**Sprint name:** Foundation Sprint 0–1 — Repository skeleton + build/test harness

**Objective:**
Create a controlled, architecture-faithful repository foundation that demonstrates clear Python/native/contract boundaries, enforces repository invariants through tests, and provides a working build/test harness. No production inference, database, API, or UI feature code is produced in this sprint.

**Active repository:** `/home/user/Workspace/MergenVisionFinalVersion`

**Frozen inputs (read-only):**
- `requirements/phase1requirements.md`
- `requirements/ProjectRequirements.md`
- `requirements/phase2requirements.md`
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

### Backend
- `backend/pyproject.toml`
- `backend/src/mergenvision/__init__.py`
- `backend/src/mergenvision/api/__init__.py`
- `backend/src/mergenvision/application/__init__.py`
- `backend/src/mergenvision/domain/__init__.py`
- `backend/src/mergenvision/ports/__init__.py`
- `backend/src/mergenvision/infrastructure/__init__.py`
- `backend/src/mergenvision/config/__init__.py`
- `backend/tests/test_package_smoke.py`
- `backend/tests/test_dependency_boundaries.py`
- `backend/tests/test_forbidden_runtime_dependencies.py`

### Native
- `native/CMakeLists.txt`
- `native/include/mergenvision/face_core/version.hpp`
- `native/src/version.cpp`
- `native/apps/runtime_server/README.md`
- `native/tests/version_smoke.cpp`

### Contracts
- `contracts/face_inference/v1/README.md`
- `contracts/face_inference/v1/face_inference.proto`

### Frontend boundary
- `frontend/README.md`

### Docs
- `docs/implementation/PHASE1_EXECUTION_CHARTER.md`
- `docs/implementation/CURRENT_SPRINT.md`
- `docs/implementation/REFERENCE_DECISION_LOG.md`
- `docs/benchmarks/BULK_ENROLLMENT_BENCHMARK_SPEC.md`

### Root / scripts
- `.editorconfig`
- `.gitignore`
- `Makefile`
- `scripts/verify_repository_boundaries.sh`

---

## Exact tests

1. `backend/tests/test_package_smoke.py` — import package, version check, subpackage imports.
2. `backend/tests/test_dependency_boundaries.py` — AST import scan enforcing dependency direction.
3. `backend/tests/test_forbidden_runtime_dependencies.py` — forbidden production imports scan.
4. `native/tests/version_smoke.cpp` — links to native library, checks version/ABI constants.
5. `scripts/verify_repository_boundaries.sh` — shell-level boundary and artifact checks.

---

## Exact validation commands

```bash
cd /home/user/Workspace/MergenVisionFinalVersion
make verify-foundation
```

`verify-foundation` runs, in order:

```bash
make test-python          # compileall + pytest backend/tests
make configure-native     # cmake -S native -B build/native
make build-native         # cmake --build build/native --parallel
make test-native          # ctest --test-dir build/native --output-on-failure
make verify-boundaries    # bash scripts/verify_repository_boundaries.sh
```

Manual equivalents:

```bash
python3 -m compileall backend/src
PYTHONPATH=backend/src python3 -m pytest backend/tests -v

cmake -S native -B build/native
cmake --build build/native --parallel
ctest --test-dir build/native --output-on-failure

bash scripts/verify_repository_boundaries.sh

git status --short
git diff --stat
git diff --name-only
```

---

## Non-goals

- Real face detection / ArcFace / model download / TensorRT engine build.
- CUDA kernel / nvJPEG implementation.
- PostgreSQL migration / SQLAlchemy model / Alembic.
- MinIO / Qdrant resource creation.
- REST endpoint implementation.
- React screen implementation.
- Docker / Docker Compose.
- Bulk worker implementation.
- Dataset scanning or import.
- LFW / VGGFace2 benchmark execution.
- Phase 2 video implementation.
- Oracle connection.
- `AGENTS.md`.
- Git add / commit / push.

---

## Done definition

`FOUNDATION_GATE=PASS` only if:

1. All files listed above exist with real content.
2. `python3 -m compileall backend/src` succeeds.
3. `python3 -m pytest backend/tests -v` passes (pytest installed or blocker reported).
4. `cmake configure/build` succeeds.
5. `ctest` passes.
6. `bash scripts/verify_repository_boundaries.sh` returns 0.
7. Frozen architecture/requirements files are unchanged.
8. No fake production inference classes, no ML model, no DB implementation.
9. No unrelated files created.

If pytest cannot be installed without system/global pip, report `FOUNDATION_GATE=PARTIAL` with the exact blocker.

---

## Known blockers

- (resolved) `pytest` was not available system-wide; a local `.venv` was created in the repo root and `pytest` was installed via pip.
- No other blockers.


---

## Next sprint

**PostgreSQL + Alembic implementation sprint**

After user review and `FOUNDATION_GATE` PASS/PARTIAL acceptance:
- Implement SQLAlchemy 2 domain models for the 8 frozen ERD tables.
- Create Alembic migrations with constraints and indexes.
- Add repositories and integration tests against PostgreSQL.
- Implement national ID encryption/HMAC/masking boundary.
