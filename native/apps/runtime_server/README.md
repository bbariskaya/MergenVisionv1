# Native Face Inference Runtime Server

**Status:** Design placeholder — no implementation in Foundation Sprint 0–1.

## Purpose

Future native process boundary for the GPU hot path:

- compressed JPEG/PNG decode
- CUDA preprocess
- TensorRT detector
- CUDA postprocess / NMS / landmarks
- quality gate
- CUDA five-point alignment
- TensorRT ArcFace
- GPU L2 normalization
- compact results back to Python control plane

## Deployment boundary

- Runs on the **same host/container** as the FastAPI process.
- Communicates over a **Unix domain socket**.
- Uses the typed protobuf contract in `contracts/face_inference/v1/face_inference.proto`.
- **Not** a public microservice; not exposed to external clients.

## Ownership rules

- The native process owns the GPU context, CUDA stream(s), and model artefacts.
- The native core does **not** embed PostgreSQL, MinIO, or Qdrant clients.
- Storage orchestration and known/unknown business decisions remain in Python application services.

## Future lifecycle

1. Model/alignment parity evidence with reference oracle.
2. Native runtime server executable.
3. Unix-socket client adapter in `mergenvision.infrastructure`.
4. End-to-end hot-path integration tests.
