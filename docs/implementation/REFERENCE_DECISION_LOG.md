# MergenVision Phase 1 — Reference Decision Log

**Scope:** Foundation Sprint 0–1 repository skeleton and build/test harness.
**Date:** 2026-07-12
**Active repo:** `/home/user/Workspace/MergenVisionFinalVersion`

This log records which references were inspected, what decision they influenced, and why alternatives were rejected. URL-only citations are not accepted; the exact files/pages read and the resulting project decision are stated.

---

## Decision table

| Component | Requirement | Official / upstream reference | Old repo evidence | Decision | Rejected alternative | License / provenance note |
|---|---|---|---|---|---|---|
| Python project layout | Foundation `src/` layout, `pyproject.toml` metadata, pytest configuration | Python Packaging User Guide (`/websites/packaging_python_en`) — modern `pyproject.toml`, src-layout examples, setuptools package discovery | `Workspace/mergenvision/backend/pyproject.toml`: uses hatchling, `app` package, `tool.ruff`, `tool.mypy`, `tool.pytest.ini_options` | Use `pyproject.toml` with `setuptools` build backend, explicit `src/` layout, project name `mergenvision-backend`, Python >=3.12, pytest `testpaths = ["tests"]` and `pythonpath = ["src"]`. No runtime dependencies in this sprint. | Hatchling (works, but setuptools is standard and sufficient for an empty skeleton); using `requirements.txt` without metadata (loses package identity) | Setuptools PSF / MIT-compatible; no code copied |
| C++ target layout | `mergenvision_face_core` static/shared library, public include directory, CTest | CMake official docs (`/kitware/cmake`) — `add_library`, `target_include_directories(PUBLIC ...)`, `include(CTest)`, `add_test` | No prior native target in the active repo; old repos are Python-first. `MergenVisionProdReal` and `mergenvisionprod` contain ad-hoc C++/CUDA snippets but no modern CMake target. | Create modern CMake 3.28 project, C++20, `mergenvision_face_core` target with `PUBLIC include/`, warning flags, `version_smoke` test executable, CTest enabled. | Header-only or monolithic single-file native core (rejected because the baseline contract is a reusable library with a public header) | CMake BSD-3-Clause; no code copied |
| Internal RPC contract | typed, versioned protobuf boundary between Python control plane and native GPU worker | Protocol Buffers docs (`/protocolbuffers/protobuf`) — proto3 syntax, package/version naming, PascalCase messages, snake_case fields, `bytes`, `repeated`, enum conventions; `protoc` 3.21.12 installed locally | No proto contract exists in old repos. `Workspace/mergenvision` and `MergenVision` use in-process Python adapters (ONNX/TensorRT) directly from FastAPI. | Create `contracts/face_inference/v1/face_inference.proto` with package `mergenvision.face_inference.v1`, `FaceInference` service, `Health` and `InferImage` RPCs. Request carries `request_id`, `operation_mode` enum, `encoded_image` bytes, `verified_mime_type`, `inference_profile_id`. Response carries image dimensions and repeated `FaceResult` with original-image bbox, ordered five landmarks, detection confidence, quality score, normalized 512-D embedding. No PII, no storage clients, no known/unknown business decision. | gRPC full server/client implementation in this sprint (rejected — violates sprint scope); plain JSON over socket (rejected — loses typed contract and cross-language safety) | protobuf BSD-3-Clause; this sprint only creates the `.proto` schema, no generated code |
| Five-point landmark order | Alignment output contract must be unambiguous and reference-compatible | DeepWiki/InsightFace (`deepinsight/insightface`) — `arcface_dst` landmark order: left eye, right eye, nose, left mouth corner, right mouth corner; canonical crop 112×112 | Old repos use InsightFace/RetinaFace or SCRFD decoding; `mergenvisionprod/oldWorking` implements CUDA five-point alignment. Order drift would break parity. | Adopt the InsightFace/ArcFace landmark order as the canonical contract. Document it in the proto README. | Person/image orientation ambiguity (rejected — explicit viewer-coordinates contract required); arbitrary landmark order (rejected — parity impossible) | InsightFace code MIT; landmark coordinates are factual convention, not copied code |
| Native core boundary | Native runtime must not own PostgreSQL/MinIO/Qdrant clients | Architecture/01–06 frozen docs; `whatwentwrong.md` PROD-002/DRIFT-001: old Phase 2 DeepStream/native attempts leaked storage concerns into GPU code | `mergenvisionprod/oldWorking/NVDIAgstreamer` mixes inference with bounded metadata storage but still keeps PostgreSQL writes outside the C++ parser core. | Native `libmergenvision_face_core` owns decode→detect→align→embed→normalize only. Storage orchestration lives in Python application services. Documented in `native/apps/runtime_server/README.md`. | Putting SQL/MinIO/Qdrant C++ clients inside native core (rejected — couples GPU code to storage failures and PII risk) | N/A — architectural decision |
| LFW dataset role | Small deterministic correctness/oracle set | `whatwentwrong.md` §6.6–6.7; `Demo12_VGGFace2Lab` LFW 13,233 images imported for parity/quality checks | `Demo/Demo12` used LFW for 177-test fake-pipeline and real ONNX parity. `MergenVisionProdReal` used LFW B128 for GPU-only Python path accuracy claim. | LFW is for **REFERENCE_CORRECTNESS** only: alignment/embedding parity, threshold calibration start, small deterministic regression. NOT a product-scale benchmark. | Reporting LFW accuracy as product acceptance (rejected — ACC-001 shows this path drifted and is not product enrollment) | Dataset license must be reviewed before use; no images committed |
| VGGFace2 dataset role | Throughput/stability/scale evidence | `whatwentwrong.md` §6.7; `Demo12_VGGFace2Lab` imported 176,398 images; three-GPU worker sharding experiments | `Demo/Demo12_VGGFace2Lab` scripts show batch sizes, worker slot mapping, Qdrant batch upsert, duplicate handling. | VGGFace2 is for **GPU_COMPUTE_ONLY** / **END_TO_END_ENROLLMENT** / **THREE_GPU_SCALE** evidence: throughput, multi-sample person behavior, storage pressure. | Using VGGFace2 for accuracy acceptance (rejected — label noise); auto-download (rejected — datasets must be user-provided and license-checked) | Dataset license must be reviewed before use; no images committed |
| Bulk sharding | personId-based deterministic partitioning | Charter §6: `hash(personId) mod workerCount` | `ProjectFaceRecognize/facerecognition` set all workers to `CUDA_VISIBLE_DEVICES=0` (MGPU-001). `Demo12_VGGFace2Lab` did hash-based worker assignment per person. | Use `hash(personId) mod workerCount` so all photos of a person land on the same worker, reducing face_identity/person lifecycle race risk. | `hash(photoId)` sharding (rejected — splits one person across workers); random allocation (rejected — non-deterministic, harder to reproduce) | N/A — architectural decision |
| DALI forbidden | No `nvidia.dali` in production runtime | Charter §4; `whatwentwrong.md` GPU_HOT_PATH table: DALI path abandoned in newer repos | `MergenVision` `GpuDaliDecoder.decode_batch` exists but later repos moved to PyNvVideoCodec/DeepStream. | Explicitly forbid `nvidia.dali`, `DALI` strings in production source. Document rejection. | Keep DALI as optional adapter (rejected — charter says “DALI kullanılmayacaktır”) | N/A — architectural decision |
| Old mixed-runtime lesson | Avoid CPU fallback and provider-list acceptance | `whatwentwrong.md` §9, §11, TEST-001: CPU/OpenCV falls back, provider list checks, container GPU visibility used as false proof | `VideoFaceRealtimeLab` `ffmpeg_nvdec_cpu_frames`; `FaceRecognitionProject` `cv2.VideoCapture`; `MergenVisionProdReal` mode-A/LFW shortcut. | Production-native hot path must be explicitly CUDA/TensorRT with parity tests; no hidden `CPUExecutionProvider`; `cv2.VideoCapture` forbidden in production source. | Accepting provider-list or container GPU visibility as proof (rejected — TEST-001) | N/A — process decision |
| Model/alignment not locked | Detector and recognizer are candidates only | Charter §4: RetinaFace candidate, ArcFace 512-D candidate, FP16 baseline; exact artefacts not final | Old repos drifted: RetinaFace→SCRFD, 640→320, TF/DeepFace→ONNX→TensorRT, OpenCV→GPU alignment. No single artefact is authoritative. | Do not hard-code detector/recognizer in Foundation Sprint. The proto contract and benchmark spec prepare for future parity evidence before locking. | Committing to SCRFD 10G or a specific ArcFace backbone now (rejected — needs reference/parity/batch gate) | N/A — process decision |

---

## References used

| ID / tool | Reference | What was read | Decision supported |
|---|---|---|---|
| Context7 `/websites/packaging_python_en` | Python Packaging User Guide | `pyproject.toml` metadata, src-layout, setuptools package discovery | `backend/pyproject.toml` shape |
| Context7 `/kitware/cmake` | CMake official docs | `add_library`, `target_include_directories`, `include(CTest)`, `add_test` | `native/CMakeLists.txt` shape |
| Context7 `/protocolbuffers/protobuf` | Protocol Buffers docs | proto3 syntax, naming conventions, bytes/repeated/enum usage | `contracts/face_inference/v1/face_inference.proto` |
| DeepWiki `deepinsight/insightface` | InsightFace wiki | Five-point landmark order and 112×112 canonical crop | Proto README alignment contract |
| DeepWiki `serengil/deepface` | DeepFace wiki | Detection bbox/orchestration pattern (library user perspective) | Understanding of modular pipeline references; no code reused |
| codebase-memory-mcp `home-user-Workspace-mergenvision` | Clean Phase 1 backend structure | `backend/pyproject.toml`, `backend/app/{api,application,domain,infrastructure,repositories,schemas}`, `backend/tests` | Skeleton backend layer layout |
| codebase-memory-mcp `home-user-Demo-Demo12_VGGFace2Lab` | Multi-GPU batched import sandbox | `Backend/app/domain`, `Backend/scripts/vggface2_import/*`, `Backend/scripts/run_lfw_3gpu_throughput.py`, LFW/VGGFace2 reports | Benchmark spec sharding, four modes, dataset roles |
| codebase-memory-mcp `home-user-MergenVision` | ~1M-record demo | `backend/app/application`, `backend/app/infrastructure/adapters`, `backend/app/repositories` | Layer direction, separation of domain/infrastructure |
| `whatwentwrong.md` | Forensic findings | Entire active-repo forensic report | Governance rules, rejected patterns, dataset privacy, acceptance falsehoods |

---

## References explicitly rejected or deferred

| Reference | Reason |
|---|---|
| DeepFace as production runtime | Approved only as behavior/orchestration reference (REF-005). The final runtime must be native CUDA/TensorRT, not a convenience wrapper, per charter §4. |
| Ultralytics (REF-002) | Phase 2/later object/person context only; AGPL license requires explicit decision. Not used in Phase 1. |
| PaddlePaddle (REF-004) | Research comparison only; no production dependency justification. |
| Segment Anything (REF-001) | Future segmentation phase; irrelevant to Phase 1 face recognition. |
| NVIDIA Jetson Accelerated GStreamer Guide (REF-006) | Jetson-specific archived docs; current target workstation dGPU, so deferred. |
| NVIDIA DeepStream SDK (REF-007) | Primary Phase 2 reference; Phase 1 acceptance must come first. |

---

## License / provenance note (general)

No third-party code is copied into this sprint. All source files are original skeletons. Conceptual decisions are informed by upstream references and old-repo forensic findings. Where old-repo patterns are reused as concepts, the source repo and the reason for any adaptation are recorded above. Before any model weight, dataset image, or engine binary is added to the repo, a separate license/provenance row must be added to this log and approved.
