# MergenVision Phase 1 Execution Charter

## Active repository

`/home/user/Workspace/MergenVisionFinalVersion` is the single source of truth. All other repositories are read-only references.

## Source-of-truth inputs

- `requirements/phase1requirements.md` — senior/client Phase 1 requirements.
- `requirements/ProjectRequirements.md` — detailed agent-written Phase 1 specification.
- `requirements/phase2requirements.md` — Phase 2 future requirements; **not** implemented yet.
- `architecture/01-phase1-high-level-architecture.md`
- `architecture/02-phase1-component-diagram.md`
- `architecture/03-phase1-postgresql-erd.md`
- `architecture/04-phase1-minio-object-layout.md`
- `architecture/05-phase1-qdrant-vector-design.md`
- `architecture/06-phase1-api-contract.md`
- `opensourcereferences/references.md`
- `whatwentwrong.md`

## Architecture freeze

The following are frozen for Phase 1 until the Foundation Gate passes:

- 8-table PostgreSQL ERD (person, face_identity, process_record, inference_profile, person_photo, face_sample, recognition_result, process_event).
- MinIO owns all binary objects; PostgreSQL owns all structured metadata.
- Qdrant owns only derived 512-D face vectors; it is rebuildable from PostgreSQL + MinIO.
- UUIDv7 for primary identifiers where possible.
- National ID encrypted/HMAC’d; never in Qdrant payload, object keys, or logs.
- Model stack candidates: ONNX Runtime / TensorRT, RetinaFace-style detector, ArcFace 512-D recognizer, cosine distance. Final artefact requires acceptance gate.
- Anonymous/known decision exposed by application service; unknown faces returned as `unknown`, not persisted automatically.

## Runtime topology

- **Python control plane** — FastAPI application services, repositories, PostgreSQL/Alembic, MinIO/Qdrant clients, orchestration.
- **Native GPU data plane** (future) — decode → detect → align → embed, implemented as a same-host Unix-domain-socket worker controlled by Python.
- **Frontend** — React + TypeScript + Vite; talks only to `/api/v1`.

## Model / alignment acceptance gate

No detector, recognizer, alignment implementation may be merged into production code until:

1. A reference oracle is defined.
2. Parity evidence exists on LFW (or a comparable public benchmark).
3. Hot-path GPU code can be traced line-by-line.
4. Required licences and provenance are recorded in `REFERENCE_DECISION_LOG.md`.

## Three-GPU bulk direction

Bulk enrollment benchmark must support:

1. `REFERENCE_CORRECTNESS` — LFW quality/oracle parity.
2. `GPU_COMPUTE_ONLY` — raw detect/align/embed throughput, no persistence.
3. `END_TO_END_ENROLLMENT` — compute + bounded PostgreSQL/MinIO/Qdrant writes.
4. `THREE_GPU_SCALE` — sharded by `hash(personId) mod workerCount` across three workers.

## Phase 1 / Phase 2 boundary

Phase 1 is an image-based face recognition product with a FastAPI backend, mandatory internal React UI, PostgreSQL, MinIO, and Qdrant. Phase 2 (video, live stream, DeepStream) may not start until Phase 1 passes Foundation, DB, API, model, and Docker gates.

## Forbidden tools / dependencies

- `deepface` in production runtime.
- `FaceAnalysis`, `paddle`, `nvidia.dali` / `DALI`.
- `cv2.VideoCapture` / CPU fallback in production hot path.
- `CPUExecutionProvider` silently.
- 21st.dev / Ruflo / broad subagent swarms.
- Phase 2 entities inside Phase 1 implementation.

## Hard-stop rules

1. No production code without a failing test first.
2. No GPU claim without line-by-line hot-path evidence.
3. No 10M scale claim without measured proof.
4. No acceptance from report claims, provider lists, or test counts alone.
5. No new repository opened; all work stays in `MergenVisionFinalVersion`.
6. No commit unless explicitly requested.
