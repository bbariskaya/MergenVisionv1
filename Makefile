.PHONY: test-python configure-native build-native test-native verify-boundaries verify-foundation

# Prefer a local virtual environment when it exists; fall back to system python.
PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)
PIP ?= $(PYTHON) -m pip
PYTEST ?= $(PYTHON) -m pytest

REPO_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# ---------------------------------------------------------------------------
# Python layer
# ---------------------------------------------------------------------------

test-python:
	@echo "==> Compiling Python source"
	$(PYTHON) -m compileall backend/src
	@echo "==> Running Python tests"
	PYTHONPATH=backend/src $(PYTEST) backend/tests -v

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

# ---------------------------------------------------------------------------
# Foundation gate: all of the above, in order, non-destructive
# ---------------------------------------------------------------------------

verify-foundation: test-python configure-native build-native test-native verify-boundaries
	@echo "==> Foundation verification complete"
