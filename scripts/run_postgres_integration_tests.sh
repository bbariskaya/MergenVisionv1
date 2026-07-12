#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

CONTAINER_ID=""
EXIT_CODE=0
IMAGE="postgres:16-alpine"
DEFAULT_USER="test"
DEFAULT_PASSWORD="test"
DEFAULT_DB="mergenvision"

choose_port() {
    python3 - <<'PY'
import socket
with socket.socket() as s:
    s.bind(("", 0))
    print(s.getsockname()[1])
PY
}

cleanup() {
    if [[ -n "${CONTAINER_ID}" ]]; then
        echo "==> Stopping ephemeral PostgreSQL container ${CONTAINER_ID}"
        docker stop "${CONTAINER_ID}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

run_migrations_and_tests() {
    local database_url="$1"
    echo "==> Running Alembic migrations"
    (
        cd backend
        MERGENVISION_DATABASE_URL="${database_url}" \
            "${REPO_ROOT}/.venv/bin/alembic" -c alembic.ini upgrade head
    )

    echo "==> Running integration tests"
    MERGENVISION_DATABASE_URL="${database_url}" \
        MERGENVISION_TEST_DATABASE_URL="${database_url}" \
        "${REPO_ROOT}/.venv/bin/python" -m pytest backend/tests/integration -v
}

if [[ -n "${MERGENVISION_TEST_DATABASE_URL:-}" ]]; then
    echo "==> Using provided MERGENVISION_TEST_DATABASE_URL"
    echo "==> Running test database safety check"
    PYTHONPATH="${REPO_ROOT}/backend/src" \
        "${REPO_ROOT}/.venv/bin/python" \
        "${REPO_ROOT}/scripts/check_test_database_safety.py"
    run_migrations_and_tests "${MERGENVISION_TEST_DATABASE_URL}"
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is required to start ephemeral PostgreSQL" >&2
    exit 1
fi

TEST_PORT="$(choose_port)"
CONTAINER_NAME="mergenvision-test-postgres-$$-${RANDOM}"

echo "==> Starting ephemeral PostgreSQL on port ${TEST_PORT}"
CONTAINER_ID="$(docker run --rm -d \
    --name "${CONTAINER_NAME}" \
    -e POSTGRES_USER="${DEFAULT_USER}" \
    -e POSTGRES_PASSWORD="${DEFAULT_PASSWORD}" \
    -e POSTGRES_DB="${DEFAULT_DB}" \
    -p "${TEST_PORT}:5432" \
    "${IMAGE}")"

echo "==> Waiting for PostgreSQL to be ready"
for _ in {1..60}; do
    if docker exec "${CONTAINER_ID}" pg_isready -U "${DEFAULT_USER}" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

for _ in {1..60}; do
    if docker exec "${CONTAINER_ID}" psql -U "${DEFAULT_USER}" -d "${DEFAULT_DB}" -c "SELECT 1" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! docker exec "${CONTAINER_ID}" psql -U "${DEFAULT_USER}" -d "${DEFAULT_DB}" -c "SELECT 1" >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL did not become ready" >&2
    exit 1
fi

DATABASE_URL="postgresql+asyncpg://${DEFAULT_USER}:${DEFAULT_PASSWORD}@localhost:${TEST_PORT}/${DEFAULT_DB}"
run_migrations_and_tests "${DATABASE_URL}"
