# Phase 1 Bulk Enrollment Benchmark Specification

**Status:** Specification only. No implementation, no dataset download, no execution in Foundation Sprint 0–1.

## Objectives

- Define a repeatable benchmark contract before building the benchmark harness.
- Separate correctness evidence from throughput evidence.
- Keep dataset privacy/license gate explicit.
- Provide the input contract for the future multi-GPU bulk runner.

## Benchmark modes

### 1. REFERENCE_CORRECTNESS

- **Dataset:** LFW (or an equivalent public face benchmark).
- **Purpose:** Regression/oracle parity for detector, alignment, embedding, and threshold.
- **Scope:** Single GPU or CPU reference path; no distributed sharding.
- **Metrics:**
  - detection count per image
  - false positive / false negative face counts
  - embedding vector sanity (512-D, normalized)
  - threshold calibration start (e.g. observed same/different cosine distribution)
- **Persistence:** None. PostgreSQL/MinIO/Qdrant writes are disabled.
- **Acceptance gate:** Results must lie within an approved tolerance band of the reference oracle.

### 2. GPU_COMPUTE_ONLY

- **Dataset:** VGGFace2 subset or LFW.
- **Purpose:** Maximum detect/align/embed throughput with no storage latency.
- **Scope:** One or more GPUs; batch inference; no persistence.
- **Metrics:**
  - images/second
  - faces/second
  - batch size vs. memory
  - GPU utilization and host-device copy profile
- **Persistence:** None.
- **Acceptance gate:** Sustained throughput at target batch size without OOM.

### 3. END_TO_END_ENROLLMENT

- **Dataset:** VGGFace2 subset or LFW.
- **Purpose:** Real enrollment throughput including storage orchestration.
- **Scope:** Single worker or sharded by `personId`.
- **Required bounded behavior:**
  - PostgreSQL bounded batch transaction (batch size limit, retry on deadlock).
  - MinIO bounded concurrent `PutObject` (connection limit, async producer/consumer).
  - Qdrant batch upsert (batch size limit, retry/backpressure).
  - Storage writes must never block the CUDA hot path; use separate CPU-bound queue/worker.
  - Backpressure when persistence falls behind compute.
  - Duplicate detection/reconciliation by deterministic IDs.
- **Metrics:**
  - persons/second
  - photos/second
  - faces/second
  - p95/p99 persistence latency
  - storage error rate and retry counts
- **Acceptance gate:** Throughput must be reported separately from `GPU_COMPUTE_ONLY`, and the pipeline must recover from an injected persistence failure.

### 4. THREE_GPU_SCALE

- **Dataset:** VGGFace2 subset (or full dataset if license/resources allow).
- **Purpose:** Demonstrate horizontal worker scaling without breaking identity consistency.
- **Sharding:** deterministic `hash(personId) mod workerCount`.
- **Antipattern explicitly forbidden:** `hash(photoId) mod workerCount` — it splits one person across workers and invalidates identity lifecycle assumptions.
- **Required behavior:**
  - each worker owns its GPU device deterministically
  - workers are independent Unix-domain-socket or queue consumers
  - no global lock across workers
  - final per-person state must be consistent when the same person is sent twice
- **Metrics:**
  - total persons/second across workers
  - per-worker throughput balance (max/min ratio)
  - multi-GPU worker mapping correctness
  - concurrent import stability over at least 10k persons
- **Acceptance gate:** Three-worker throughput strictly greater than one-worker throughput, and no cross-worker identity collision.

## Dataset roles

### LFW

- Use for correctness, regression, and threshold baseline only.
- Not a product-scale benchmark.
- Do not publish LFW person names or image paths in public logs/object keys.
- License/provenance gate required before any image is imported.

### VGGFace2

- Use for throughput, stability, and multi-GPU scale evidence.
- Not for accuracy acceptance (label noise).
- Do not publish VGGFace2 person names or folder names in public logs/object keys.
- License/provenance gate required before any image is imported.

## Sharding contract

```python
worker_index = hash(person_id) % worker_count
```

- `person_id` is the project-scoped UUIDv7 person identifier.
- `hash()` must be stable across Python invocations (e.g. `hashlib.sha256(...).digest()` modulo).
- All photos of the same person must land on the same worker for the duration of a batch.

## Persistence contract

- **PostgreSQL:** bounded batch `INSERT ... ON CONFLICT DO NOTHING/UPDATE`, with explicit transaction size. Person/photo/face records are inserted before Qdrant upsert.
- **MinIO:** bounded concurrent `PutObject` pool. Photo binary and optional audit crop stored with deterministic object keys containing only UUIDs.
- **Qdrant:** batch vector upsert using the default unnamed vector. Payload contains only sample UUIDs and derived metadata; no PII/national ID/name.
- **Backpressure:** when persistence queue depth exceeds a configured threshold, compute stage slows or rejects new input.
- **Duplicates:** deterministic IDs prevent duplicates; reconciliation report emitted at end of batch.
- **Retry:** `Idempotency-Key` style generic header is forbidden; deterministic IDs and `ON CONFLICT` provide retry safety.

## Privacy and license gate

1. Datasets must be user-provided or installed under a reviewed license.
2. No automatic dataset download inside production or benchmark code.
3. Person names, national IDs, dataset folder names must never appear in object keys, logs, benchmark JSON, or demo output.
4. All raw dataset content lives outside the repo; only processed vectors and metadata (with approved anonymization) may be persisted in controlled environments.

## Not in scope yet

- Actual benchmark harness code.
- Dataset import scripts.
- Model download.
- TensorRT engine build.
- Docker compose for three-GPU runner.
- Oracle bulk import.

## Future verification

When the benchmark harness is implemented, the CI target `make benchmark-foundation` must:

1. Check that LFW/VGGFace2 datasets are present under a configured path.
2. Run all four modes in order.
3. Emit a JSON report with throughput, latency, and correctness metrics.
4. Fail if any antipattern (e.g. `photoId` sharding, PII in payload, hidden CPU fallback) is detected.
