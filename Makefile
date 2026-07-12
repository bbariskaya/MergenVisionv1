.PHONY: bootstrap-foundation check-venv test-python ruff proto-syntax configure-native build-native test-native verify-boundaries frozen-hashes verify-foundation

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
# Foundation gate: all of the above, in order, non-destructive
# ---------------------------------------------------------------------------

verify-foundation: test-python ruff proto-syntax configure-native build-native test-native verify-boundaries frozen-hashes
	@echo "==> Foundation verification complete"
