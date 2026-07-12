.PHONY: bootstrap-foundation check-venv test-python ruff proto-syntax configure-native build-native test-native verify-boundaries frozen-hashes verify-foundation test-db-unit test-db-integration verify-db verify-sprint-002 test-storage-unit test-storage-integration verify-storage verify-sprint-003

PYTHON := .venv/bin/python
PYTEST := $(PYTHON) -m pytest

REPO_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# ---------------------------------------------------------------------------
# Environment bootstrap (idempotent, no global system packages)
# ---------------------------------------------------------------------------

bootstrap-foundation:
	@bash scripts/bootstrap_foundation.sh

check-venv:
	@test -x $(PYTHON) || { echo "Run make bootstrap-foundation first." >&2; exit 1; }

# ---------------------------------------------------------------------------
# Python layer
# ---------------------------------------------------------------------------

test-python: check-venv
	@echo "==> Compiling Python source"
	$(PYTHON) -m compileall backend/src
	@echo "==> Running Python tests"
	PYTHONPATH=backend/src $(PYTEST) backend/tests -v

ruff: check-venv
	@echo "==> Running Ruff"
	$(PYTHON) -m ruff check backend/src backend/tests

proto-syntax:
	@echo "==> Validating proto syntax"
	@if command -v protoc >/dev/null 2>&1; then \
		mkdir -p /tmp/proto_check; \
		protoc --proto_path=contracts/face_inference/v1 face_inference.proto --python_out=/tmp/proto_check; \
		echo "Proto syntax OK"; \
	else \
		echo "SKIPPED_TOOL_UNAVAILABLE: protoc not installed"; \
	fi

# ---------------------------------------------------------------------------
# Native layer
# ---------------------------------------------------------------------------

configure-native:
	@cmake -S native -B build/native

build-native: configure-native
	@cmake --build build/native --parallel

test-native: build-native
	@ctest --test-dir build/native --output-on-failure

# ---------------------------------------------------------------------------
# Repository-level boundary checks
# ---------------------------------------------------------------------------

verify-boundaries:
	@bash scripts/verify_repository_boundaries.sh

frozen-hashes:
	@echo "==> Verifying frozen file hashes"
	@sha256sum --check architecture/FROZEN_SHA256SUMS

# ---------------------------------------------------------------------------
# Database sprint targets (Sprint 002 - real PostgreSQL)
# ---------------------------------------------------------------------------

test-db-unit: check-venv
	@echo "==> Running DB/security/domain unit tests"
	PYTHONPATH=backend/src $(PYTEST) backend/tests/unit -v

test-db-integration:
	@echo "==> Running real PostgreSQL integration tests"
	@bash scripts/run_postgres_integration_tests.sh

verify-db: ruff test-db-unit test-db-integration
	@echo "==> Running mypy"
	$(PYTHON) -m mypy backend/src
	@echo "==> Database verification complete"

verify-sprint-002: verify-foundation verify-db
	@echo "==> Sprint 002 verification complete"

# ---------------------------------------------------------------------------
# Storage sprint targets (Sprint 003 - MinIO + Qdrant + cross-store)
# ---------------------------------------------------------------------------

test-storage-unit: check-venv
	@echo "==> Running storage unit tests"
	PYTHONPATH=backend/src $(PYTEST) \
		backend/tests/unit/test_storage_keys.py \
		backend/tests/unit/test_object_storage_contract.py \
		backend/tests/unit/test_vector_index_contract.py \
		backend/tests/unit/test_storage_settings.py \
		backend/tests/unit/test_external_storage_test_safety.py \
		backend/tests/unit/test_enrollment_persistence.py \
		backend/tests/unit/test_storage_reconciliation.py \
		-v

test-storage-integration:
	@echo "==> Running real MinIO + Qdrant + PostgreSQL integration tests"
	@bash scripts/run_storage_integration_tests.sh

verify-storage: ruff test-storage-unit test-storage-integration
	@echo "==> Running mypy"
	$(PYTHON) -m mypy backend/src
	@echo "==> Storage verification complete"

verify-sprint-003: verify-foundation verify-db verify-storage
	@echo "==> Sprint 003 verification complete"

# ---------------------------------------------------------------------------
# Foundation gate: all of the above, in order, non-destructive
# ---------------------------------------------------------------------------

verify-foundation: test-python ruff proto-syntax configure-native build-native test-native verify-boundaries frozen-hashes
	@echo "==> Foundation verification complete"
