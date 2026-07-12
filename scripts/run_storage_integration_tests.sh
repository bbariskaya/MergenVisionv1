#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

CONTAINERS=()
EXIT_CODE=0

PG_IMAGE="postgres:16-alpine"
# Pinned to official MinIO server release (immutable tag + manifest digest).
# Digest verified via Docker Hub manifest list for RELEASE.2025-07-23T15-54-02Z.
MINIO_IMAGE="minio/minio:RELEASE.2025-07-23T15-54-02Z@sha256:d249d1fb6966de4d8ad26c04754b545205ff15a62e4fd19ebd0f26fa5baacbc0"
# Pinned to Qdrant server minor version compatible with qdrant-client ^1.14.0.
QDRANT_IMAGE="qdrant/qdrant:v1.14.1@sha256:419d72603f5346ee22ffc4606bdb7beb52fcb63077766fab678e6622ba247366"

PG_USER="test"
PG_PASSWORD="test"
PG_DB="mergenvision"
MINIO_ROOT_USER="testtest"
MINIO_ROOT_PASSWORD="testtest"

PERSON_PHOTOS_BUCKET="test-person-photos"
RECOGNITION_INPUTS_BUCKET="test-recognition-inputs"
FACE_COLLECTION="test_face_samples"

choose_port() {
    python3 - <<'PY'
import socket
with socket.socket() as s:
    s.bind(("", 0))
    print(s.getsockname()[1])
PY
}

cleanup() {
    for container_id in "${CONTAINERS[@]}"; do
        echo "==> Stopping ephemeral container ${container_id}"
        docker stop "${container_id}" >/dev/null 2>&1 || true
    done
}
trap cleanup EXIT

wait_for_postgres() {
    local container_id="$1"
    local port="$2"
    for _ in {1..60}; do
        if docker exec "${container_id}" pg_isready -U "${PG_USER}" >/dev/null 2>&1; then
            if docker exec "${container_id}" psql -U "${PG_USER}" -d "${PG_DB}" -c "SELECT 1" >/dev/null 2>&1; then
                return 0
            fi
        fi
        sleep 1
    done
    echo "ERROR: PostgreSQL did not become ready on port ${port}" >&2
    return 1
}

wait_for_minio() {
    local port="$1"
    for _ in {1..60}; do
        if curl -sf "http://localhost:${port}/minio/health/live" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    echo "ERROR: MinIO did not become ready on port ${port}" >&2
    return 1
}

wait_for_qdrant() {
    local port="$1"
    for _ in {1..120}; do
        if curl -sf "http://localhost:${port}/healthz" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    echo "ERROR: Qdrant did not become ready on port ${port}" >&2
    return 1
}

run_migrations_and_tests() {
    local database_url="$1"
    local minio_endpoint="$2"
    local minio_port="$3"
    local qdrant_url="$4"

    export MERGENVISION_DATABASE_URL="${database_url}"
    export MERGENVISION_TEST_DATABASE_URL="${database_url}"
    export MINIO_ENDPOINT="${minio_endpoint}"
    export MINIO_ACCESS_KEY="${MINIO_ROOT_USER}"
    export MINIO_SECRET_KEY="${MINIO_ROOT_PASSWORD}"
    export MINIO_PERSON_PHOTOS_BUCKET="${PERSON_PHOTOS_BUCKET}"
    export MINIO_RECOGNITION_INPUTS_BUCKET="${RECOGNITION_INPUTS_BUCKET}"
    export QDRANT_URL="${qdrant_url}"
    export QDRANT_FACE_COLLECTION="${FACE_COLLECTION}"

    echo "==> Running external storage test safety check"
    PYTHONPATH="${REPO_ROOT}/backend/src" \
        "${REPO_ROOT}/.venv/bin/python" \
        "${REPO_ROOT}/scripts/check_external_storage_test_safety.py"

    echo "==> Running Alembic migrations"
    (
        cd backend
        MERGENVISION_DATABASE_URL="${database_url}" \
            "${REPO_ROOT}/.venv/bin/alembic" -c alembic.ini upgrade head
    )

    echo "==> Running MinIO + Qdrant + PostgreSQL integration tests"
    "${REPO_ROOT}/.venv/bin/python" -m pytest backend/tests/integration -v
}

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is required to start ephemeral storage services" >&2
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl is required to wait for storage services" >&2
    exit 1
fi

PG_PORT="$(choose_port)"
MINIO_PORT="$(choose_port)"
QDRANT_PORT="$(choose_port)"

NAME_BASE="mergenvision-test-storage-$$-${RANDOM}"

echo "==> Starting ephemeral PostgreSQL on port ${PG_PORT}"
PG_CONTAINER="$(docker run --rm -d \
    --name "${NAME_BASE}-postgres" \
    -e POSTGRES_USER="${PG_USER}" \
    -e POSTGRES_PASSWORD="${PG_PASSWORD}" \
    -e POSTGRES_DB="${PG_DB}" \
    -p "${PG_PORT}:5432" \
    "${PG_IMAGE}")"
CONTAINERS+=("${PG_CONTAINER}")

echo "==> Starting ephemeral MinIO on port ${MINIO_PORT}"
MINIO_CONTAINER="$(docker run --rm -d \
    --name "${NAME_BASE}-minio" \
    -e MINIO_ROOT_USER="${MINIO_ROOT_USER}" \
    -e MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD}" \
    -p "${MINIO_PORT}:9000" \
    "${MINIO_IMAGE}" server /data)"
CONTAINERS+=("${MINIO_CONTAINER}")

echo "==> Starting ephemeral Qdrant on port ${QDRANT_PORT}"
QDRANT_CONTAINER="$(docker run --rm -d \
    --name "${NAME_BASE}-qdrant" \
    -p "${QDRANT_PORT}:6333" \
    "${QDRANT_IMAGE}")"
CONTAINERS+=("${QDRANT_CONTAINER}")

wait_for_postgres "${PG_CONTAINER}" "${PG_PORT}"
wait_for_minio "${MINIO_PORT}"
wait_for_qdrant "${QDRANT_PORT}"

DATABASE_URL="postgresql+asyncpg://${PG_USER}:${PG_PASSWORD}@localhost:${PG_PORT}/${PG_DB}"
MINIO_ENDPOINT="localhost:${MINIO_PORT}"
QDRANT_URL="http://localhost:${QDRANT_PORT}"

run_migrations_and_tests \
    "${DATABASE_URL}" \
    "${MINIO_ENDPOINT}" \
    "${MINIO_PORT}" \
    "${QDRANT_URL}"
